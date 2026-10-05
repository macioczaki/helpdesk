from datetime import timedelta

from django.utils import timezone

from .models import Asset, License


def collect_alerts():
    today = timezone.now().date()
    in_30 = today + timedelta(days=30)

    warranty_soon = Asset.objects.filter(
        warranty_until__isnull=False,
        warranty_until__gte=today,
        warranty_until__lte=in_30,
    ).exclude(status=Asset.Status.RETIRED).order_by("warranty_until")

    warranty_expired = Asset.objects.filter(
        warranty_until__lt=today,
    ).exclude(status=Asset.Status.RETIRED).order_by("-warranty_until")[:20]

    licenses_soon = License.objects.filter(
        expires_at__isnull=False,
        expires_at__gte=today,
        expires_at__lte=in_30,
    ).order_by("expires_at")

    licenses_expired = License.objects.filter(
        expires_at__lt=today,
    ).order_by("-expires_at")[:20]

    in_repair = Asset.objects.filter(status=Asset.Status.REPAIR).order_by("updated_at")

    return {
        "warranty_soon": warranty_soon,
        "warranty_expired": warranty_expired,
        "licenses_soon": licenses_soon,
        "licenses_expired": licenses_expired,
        "in_repair": in_repair,
        "count": (
            warranty_soon.count()
            + warranty_expired.count()
            + licenses_soon.count()
            + licenses_expired.count()
            + in_repair.count()
        ),
    }