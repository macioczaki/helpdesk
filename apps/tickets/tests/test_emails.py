import pytest
from django.core import mail

from apps.accounts.models import User
from apps.tickets.models import Ticket
from apps.tickets.tasks import (
    send_ticket_assigned_email,
    send_ticket_status_changed_email,
)


@pytest.mark.django_db
def test_assigned_email_sent():
    tech = User.objects.create_user(
        username="tech",
        password="x",
        email="tech@example.com",
        role=User.Role.TECHNICIAN,
    )
    emp = User.objects.create_user(username="emp", password="x")
    t = Ticket.objects.create(
        title="A", description="...", created_by=emp, assigned_to=tech
    )

    send_ticket_assigned_email(t.pk)
    assert len(mail.outbox) == 1
    assert t.number in mail.outbox[0].subject
    assert "tech@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_status_change_email_sent():
    emp = User.objects.create_user(
        username="emp", password="x", email="emp@example.com"
    )
    t = Ticket.objects.create(title="A", description="...", created_by=emp)

    send_ticket_status_changed_email(t.pk, "NEW", "IN_PROGRESS")
    assert len(mail.outbox) == 1
    assert "emp@example.com" in mail.outbox[0].to