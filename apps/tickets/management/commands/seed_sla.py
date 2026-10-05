from django.core.management.base import BaseCommand

from apps.tickets.models import SLA, Ticket


class Command(BaseCommand):
    help = "Tworzy domyślne wpisy SLA dla wszystkich priorytetów."

    DEFAULTS = {
        Ticket.Priority.LOW: (480, 4320),  # 8h / 3 dni
        Ticket.Priority.NORMAL: (240, 1440),  # 4h / 1 dzień
        Ticket.Priority.HIGH: (60, 480),  # 1h / 8h
        Ticket.Priority.CRITICAL: (30, 240),  # 30min / 4h
    }

    def handle(self, *args, **options):
        for priority, (resp, res) in self.DEFAULTS.items():
            obj, created = SLA.objects.update_or_create(
                priority=priority,
                defaults={"response_minutes": resp, "resolve_minutes": res},
            )
            verb = "utworzono" if created else "zaktualizowano"
            self.stdout.write(f"{verb}: {obj}")
