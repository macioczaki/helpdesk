import pytest
from apps.accounts.models import Department, User


@pytest.mark.django_db
def test_user_default_role_is_employee():
    u = User.objects.create_user(username="jkowalski", password="x")
    assert u.role == User.Role.EMPLOYEE
    assert u.is_technician is False
    assert u.is_admin_role is False


@pytest.mark.django_db
def test_technician_flag():
    u = User.objects.create_user(username="tnowak", password="x", role=User.Role.TECHNICIAN)
    assert u.is_technician is True
    assert u.is_admin_role is False


@pytest.mark.django_db
def test_admin_flag():
    u = User.objects.create_user(username="admin2", password="x", role=User.Role.ADMIN)
    assert u.is_technician is True
    assert u.is_admin_role is True


@pytest.mark.django_db
def test_department_str():
    d = Department.objects.create(name="IT", building="A", floor="1")
    assert str(d) == "IT"
    assert d.users.count() == 0