from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone

from apps.tickets.models import Ticket


def build_report(date_from, date_to):
    """Zwraca dict z metrykami dla zakresu dat."""
    qs = Ticket.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)

    total = qs.count()
    resolved_qs = qs.filter(resolved_at__isnull=False)
    resolved = resolved_qs.count()

    # średni czas rozwiązania (w godzinach)
    avg_resolve = resolved_qs.aggregate(
        avg=Avg(
            ExpressionWrapper(
                F("resolved_at") - F("created_at"),
                output_field=DurationField(),
            )
        )
    )["avg"]

    avg_resolve_hours = round(avg_resolve.total_seconds() / 3600, 2) if avg_resolve else None

    # SLA
    open_statuses = [Ticket.Status.NEW, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]
    breached = qs.filter(
        Q(status__in=open_statuses, due_at__lt=timezone.now())
        | Q(resolved_at__gt=F("due_at"))
    ).count()

    sla_percent = round(100 * (total - breached) / total, 1) if total else 100.0

    by_category = (
        qs.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    by_priority = (
        qs.values("priority")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    by_technician = (
        qs.values("assigned_to__username", "assigned_to__first_name", "assigned_to__last_name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return {
        "date_from": date_from,
        "date_to": date_to,
        "total": total,
        "resolved": resolved,
        "avg_resolve_hours": avg_resolve_hours,
        "sla_breached": breached,
        "sla_percent": sla_percent,
        "by_category": list(by_category),
        "by_priority": list(by_priority),
        "by_technician": list(by_technician),
    }


def default_range():
    """Domyślny zakres: ostatnie 30 dni."""
    today = timezone.now().date()
    return today - timedelta(days=30), today