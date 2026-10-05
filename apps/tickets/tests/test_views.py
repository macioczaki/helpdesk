import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.tickets.models import Ticket


@pytest.mark.django_db
def test_employee_sees_only_own_tickets():
    emp = User.objects.create_user(username="emp", password="x", role=User.Role.EMPLOYEE)
    other = User.objects.create_user(username="other", password="x", role=User.Role.EMPLOYEE)
    Ticket.objects.create(title="Moje", description="...", created_by=emp)
    Ticket.objects.create(title="Cudze", description="...", created_by=other)

    c = Client()
    c.force_login(emp)
    r = c.get(reverse("tickets:list"))
    assert r.status_code == 200
    assert b"Moje" in r.content
    assert b"Cudze" not in r.content


@pytest.mark.django_db
def test_technician_sees_all_tickets():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    emp = User.objects.create_user(username="emp", password="x", role=User.Role.EMPLOYEE)
    Ticket.objects.create(title="Emp", description="...", created_by=emp)
    Ticket.objects.create(title="Tech", description="...", created_by=tech)

    c = Client()
    c.force_login(tech)
    r = c.get(reverse("tickets:list"))
    assert b"Emp" in r.content
    assert b"Tech" in r.content


@pytest.mark.django_db
def test_create_ticket_sets_author():
    emp = User.objects.create_user(username="emp", password="x", role=User.Role.EMPLOYEE)
    c = Client()
    c.force_login(emp)
    r = c.post(reverse("tickets:create"), {
        "title": "Drukarka nie działa",
        "description": "Brak odpowiedzi",
        "priority": Ticket.Priority.HIGH,
        "category": "",
    })
    assert r.status_code == 302
    t = Ticket.objects.get()
    assert t.created_by == emp
    assert t.status == Ticket.Status.NEW
    assert t.number.startswith("TICK-")