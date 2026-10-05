from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.assets.models import Asset, AssetAssignment, License, Location


@pytest.mark.django_db
def test_asset_tag_generated():
    a1 = Asset.objects.create(name="Laptop")
    a2 = Asset.objects.create(name="Monitor")
    assert a1.tag.startswith("AST-")
    assert a1.tag != a2.tag
    assert a1.tag.endswith("00001")
    assert a2.tag.endswith("00002")


@pytest.mark.django_db
def test_warranty_expired_flag():
    a = Asset.objects.create(
        name="Dell",
        warranty_until=timezone.now().date() - timedelta(days=1),
    )
    assert a.warranty_expired is True


@pytest.mark.django_db
def test_location_str():
    loc = Location.objects.create(building="A", floor="1", room="101")
    assert str(loc) == "A / 1 / 101"


@pytest.mark.django_db
def test_assignment_active():
    u = User.objects.create_user(username="u", password="x")
    a = Asset.objects.create(name="Laptop", assigned_to=u)
    asg = AssetAssignment.objects.create(asset=a, user=u)
    assert asg.is_active is True
    asg.to_date = timezone.now().date()
    asg.save()
    assert asg.is_active is False


@pytest.mark.django_db
def test_license_seats_free():
    lic = License.objects.create(name="Office", seats_total=10, seats_used=3)
    assert lic.seats_free == 7
