from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tickets.models import SLA, Ticket


class Command(BaseCommand):
    help = "Uzupełnia due_at dla zgłoszeń, które go nie mają (na podstawie SLA)."

    def handle(self, *args, **options):
        tickets = Ticket.objects.filter(due_at__isnull=True)
        slas = {sla.priority: sla for sla in SLA.objects.all()}
        updated = 0
        for t in tickets:
            sla = slas.get(t.priority)
            if not sla:
                continue
            t.due_at = t.created_at + timezone.timedelta(minutes=sla.resolve_minutes)
            t.save(update_fields=["due_at"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Zaktualizowano {updated} zgłoszeń."))