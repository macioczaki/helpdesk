import pytest

from apps.accounts.models import User
from apps.tickets.models import Ticket, TicketHistory


@pytest.mark.django_db
def test_status_change_logged():
    u = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    t = Ticket.objects.create(title="A", description="...", created_by=u)
    t._changed_by = u
    t.status = Ticket.Status.IN_PROGRESS
    t.save()
    h = TicketHistory.objects.filter(ticket=t, field="status").first()
    assert h is not None
    assert h.old_value == "NEW"
    assert h.new_value == "IN_PROGRESS"