import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assets.models import Asset


@pytest.mark.django_db
def test_employee_can_list_assets():
    emp = User.objects.create_user(username="emp", password="x")
    Asset.objects.create(name="Laptop")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("assets:list"))
    assert r.status_code == 200
    assert b"Laptop" in r.content


@pytest.mark.django_db
def test_employee_cannot_create_asset():
    emp = User.objects.create_user(username="emp", password="x")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("assets:create"))
    assert r.status_code == 403


@pytest.mark.django_db
def test_technician_can_create_asset():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("assets:create"))
    assert r.status_code == 200


@pytest.mark.django_db
def test_scan_resolves_tag():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    a = Asset.objects.create(name="Laptop")
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("assets:scan_resolve", args=[a.tag]))
    assert r.status_code == 302
    assert r.url == reverse("assets:detail", args=[a.pk])


@pytest.mark.django_db
def test_alerts_requires_technician():
    emp = User.objects.create_user(username="emp", password="x")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("assets:alerts"))
    assert r.status_code == 403