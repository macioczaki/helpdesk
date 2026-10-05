from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone


@shared_task
def send_ticket_assigned_email(ticket_id):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related("assigned_to", "created_by").get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    if not ticket.assigned_to or not ticket.assigned_to.email:
        return
    subject = f"[Helpdesk] Przypisano Ci zgłoszenie {ticket.number}"
    body = render_to_string("emails/ticket_assigned.txt", {"ticket": ticket})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [ticket.assigned_to.email], fail_silently=True)


@shared_task
def send_ticket_status_changed_email(ticket_id, old_status, new_status):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related("created_by").get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    if not ticket.created_by.email:
        return
    subject = f"[Helpdesk] Zmiana statusu {ticket.number}"
    body = render_to_string("emails/ticket_status_changed.txt", {
        "ticket": ticket,
        "old_status": old_status,
        "new_status": new_status,
    })
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [ticket.created_by.email], fail_silently=True)


@shared_task
def send_new_comment_email(comment_id):
    from .models import TicketComment
    try:
        comment = TicketComment.objects.select_related("ticket", "author").get(pk=comment_id)
    except TicketComment.DoesNotExist:
        return
    if comment.is_internal:
        return
    ticket = comment.ticket
    if not ticket.created_by.email or comment.author_id == ticket.created_by_id:
        return
    subject = f"[Helpdesk] Nowy komentarz w {ticket.number}"
    body = render_to_string("emails/ticket_new_comment.txt", {
        "ticket": ticket,
        "comment": comment,
    })
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [ticket.created_by.email], fail_silently=True)


@shared_task
def send_daily_digest():
    """Dzienny digest: zgłoszenia z przekroczonym SLA."""
    from apps.accounts.models import User
    from .models import Ticket

    open_tickets = Ticket.objects.filter(
        status__in=[Ticket.Status.NEW, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]
    ).select_related("assigned_to", "category")
    breached = [t for t in open_tickets if t.sla_breached]
    if not breached:
        return

    recipients = list(
        User.objects.filter(role__in=[User.Role.TECHNICIAN, User.Role.ADMIN])
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not recipients:
        return

    subject = f"[Helpdesk] Dzienny raport — {len(breached)} zgłoszeń po terminie"
    body = render_to_string("emails/daily_digest.txt", {
        "breached": breached,
        "today": timezone.now(),
    })
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)