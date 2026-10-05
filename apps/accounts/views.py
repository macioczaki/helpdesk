from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from apps.assets.alerts import collect_alerts
from apps.tickets.models import Ticket


@login_required
def home(request):
    user = request.user
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    base = Ticket.objects.all()
    if not user.is_technician:
        base = base.filter(created_by=user)

    open_statuses = [Ticket.Status.NEW, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]

    my_open = (
        base.filter(assigned_to=user, status__in=open_statuses).count()
        if user.is_technician
        else None
    )
    all_open = base.filter(status__in=open_statuses).count()

    breached_qs = base.filter(status__in=open_statuses, due_at__lt=now)
    sla_breached = breached_qs.count()

    resolved_week = base.filter(
        status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED],
        resolved_at__gte=week_ago,
    ).count()

    recent = base.select_related("category", "created_by", "assigned_to")[:8]

    per_category = base.values("category__name").annotate(total=Count("id")).order_by("-total")[:8]
    chart_labels = [row["category__name"] or "Bez kategorii" for row in per_category]
    chart_values = [row["total"] for row in per_category]

    context = {
        "my_open": my_open,
        "all_open": all_open,
        "sla_breached": sla_breached,
        "resolved_week": resolved_week,
        "recent": recent,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }

    if user.is_technician:
        alerts = collect_alerts()
        context["asset_alerts_count"] = alerts["count"]
    else:
        context["my_assets"] = list(user.assets_assigned.all()[:5])
    return render(request, "accounts/home.html", context)


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
