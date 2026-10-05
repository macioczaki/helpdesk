import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.tickets.models import Ticket, TicketComment


@pytest.mark.django_db
def test_comment_added_by_author():
    emp = User.objects.create_user(username="emp", password="x")
    t = Ticket.objects.create(title="A", description="...", created_by=emp)
    c = Client()
    c.force_login(emp)
    r = c.post(reverse("tickets:add_comment", args=[t.pk]), {"body": "Dzięki!"})
    assert r.status_code == 302
    assert TicketComment.objects.filter(ticket=t).count() == 1


@pytest.mark.django_db
def test_internal_comment_hidden_from_employee():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    emp = User.objects.create_user(username="emp", password="x")
    t = Ticket.objects.create(title="A", description="...", created_by=emp)
    TicketComment.objects.create(ticket=t, author=tech, body="tajne", is_internal=True)

    c = Client()
    c.force_login(emp)
    r = c.get(reverse("tickets:detail", args=[t.pk]))
    assert b"tajne" not in r.content