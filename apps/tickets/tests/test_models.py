import pytest

from apps.accounts.models import User
from apps.tickets.models import Category, Ticket


@pytest.mark.django_db
def test_ticket_number_generated():
    u = User.objects.create_user(username="a", password="x")
    t1 = Ticket.objects.create(title="A", description="...", created_by=u)
    t2 = Ticket.objects.create(title="B", description="...", created_by=u)
    assert t1.number.startswith("TICK-")
    assert t1.number != t2.number
    assert t1.number.endswith("0001")
    assert t2.number.endswith("0002")


@pytest.mark.django_db
def test_category_str_nested():
    parent = Category.objects.create(name="Sprzęt")
    child = Category.objects.create(name="Drukarki", parent=parent)
    assert str(child) == "Sprzęt / Drukarki"
    assert str(parent) == "Sprzęt"