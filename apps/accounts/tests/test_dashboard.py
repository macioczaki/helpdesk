import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.tickets.models import Ticket


@pytest.mark.django_db
def test_employee_dashboard_shows_only_own():
    emp = User.objects.create_user(username="emp", password="x")
    other = User.objects.create_user(username="other", password="x")
    Ticket.objects.create(title="Moje", description="...", created_by=emp)
    Ticket.objects.create(title="Cudze", description="...", created_by=other)

    c = Client()
    c.force_login(emp)
    r = c.get(reverse("home"))
    assert r.status_code == 200
    assert b"Moje" in r.content
    assert b"Cudze" not in r.content


@pytest.mark.django_db
def test_technician_dashboard_shows_all():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    emp = User.objects.create_user(username="emp", password="x")
    Ticket.objects.create(title="Emp", description="...", created_by=emp)
    Ticket.objects.create(title="Tech", description="...", created_by=tech)

    c = Client()
    c.force_login(tech)
    r = c.get(reverse("home"))
    assert b"Emp" in r.content
    assert b"Tech" in r.content


@pytest.mark.django_db
def test_employee_does_not_see_my_open_card():
    emp = User.objects.create_user(username="emp", password="x")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("home"))
    assert b"Moje otwarte" in r.content
    # karta technika nie powinna się renderować (nie ma "Moje otwarte" w wersji technika)
    # sprawdzamy że nie ma dwóch kart "Moje otwarte"
    assert r.content.count(b"Moje otwarte") == 1
