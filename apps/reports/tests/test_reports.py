import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.tickets.models import Ticket


@pytest.mark.django_db
def test_report_requires_technician():
    emp = User.objects.create_user(username="emp", password="x")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("reports:index"))
    assert r.status_code == 403


@pytest.mark.django_db
def test_report_accessible_to_technician():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("reports:index"))
    assert r.status_code == 200
    assert "Raporty" in r.content.decode()


@pytest.mark.django_db
def test_export_returns_xlsx():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    emp = User.objects.create_user(username="emp", password="x")
    Ticket.objects.create(title="A", description="...", created_by=emp)
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("reports:export"))
    assert r.status_code == 200
    assert r["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.content[:2] == b"PK"  # ZIP magic — XLSX to ZIP
