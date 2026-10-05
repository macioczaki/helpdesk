from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import SLA, Ticket, TicketComment, TicketHistory
from .tasks import (
    send_new_comment_email,
    send_ticket_assigned_email,
    send_ticket_status_changed_email,
)

TRACKED_FIELDS = ("status", "priority", "assigned_to", "category", "title")


@receiver(pre_save, sender=Ticket)
def ticket_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_values = {}
        return
    try:
        old = Ticket.objects.get(pk=instance.pk)
    except Ticket.DoesNotExist:
        instance._old_values = {}
        return
    instance._old_values = {f: getattr(old, f) for f in TRACKED_FIELDS}


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    # 1. Wylicz due_at przy tworzeniu
    if created and instance.due_at is None:
        try:
            sla = SLA.objects.get(priority=instance.priority)
            instance.due_at = instance.created_at + timezone.timedelta(minutes=sla.resolve_minutes)
            Ticket.objects.filter(pk=instance.pk).update(due_at=instance.due_at)
        except SLA.DoesNotExist:
            pass
        return

    # 2. Zapisz zmiany w historii
    old = getattr(instance, "_old_values", {})
    if not old:
        return

    user = getattr(instance, "_changed_by", None)
    for field in TRACKED_FIELDS:
        old_val = old.get(field)
        new_val = getattr(instance, field)
        if old_val == new_val:
            continue
        if field == "assigned_to":
            old_val = old_val.pk if old_val else None
            new_val = new_val.pk if new_val else None
        TicketHistory.objects.create(
            ticket=instance,
            field=field,
            old_value=str(old_val) if old_val is not None else "",
            new_value=str(new_val) if new_val is not None else "",
            changed_by=user,
        )

    # 3. Automatyczne znaczniki czasu
    updates = {}
    if instance.status == Ticket.Status.RESOLVED and not instance.resolved_at:
        updates["resolved_at"] = timezone.now()
    if instance.status == Ticket.Status.CLOSED and not instance.closed_at:
        updates["closed_at"] = timezone.now()
    if updates:
        Ticket.objects.filter(pk=instance.pk).update(**updates)
        for k, v in updates.items():
            setattr(instance, k, v)

    # 4. Powiadomienia
    old_status = old.get("status")
    new_status = instance.status
    if old_status and old_status != new_status:
        send_ticket_status_changed_email.delay(instance.pk, old_status, new_status)

    old_assigned = old.get("assigned_to")
    new_assigned = instance.assigned_to
    if new_assigned and (old_assigned is None or old_assigned.pk != new_assigned.pk):
        send_ticket_assigned_email.delay(instance.pk)


@receiver(post_save, sender=TicketComment)
def comment_post_save(sender, instance, created, **kwargs):
    if not created:
        return
    send_new_comment_email.delay(instance.pk)