import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_home_requires_login():
    c = Client()
    r = c.get(reverse("home"))
    assert r.status_code == 302
    assert "/login/" in r.url


@pytest.mark.django_db
def test_home_after_login():
    User.objects.create_user(username="jkowalski", password="testpass123")
    c = Client()
    assert c.login(username="jkowalski", password="testpass123")
    r = c.get(reverse("home"))
    assert r.status_code == 200
    assert b"Pulpit" in r.content


@pytest.mark.django_db
def test_profile_shows_role():
    u = User.objects.create_user(
        username="tnowak",
        password="testpass123",
        first_name="Tomasz",
        last_name="Nowak",
        role=User.Role.TECHNICIAN,
    )
    c = Client()
    c.force_login(u)
    r = c.get(reverse("profile"))
    assert r.status_code == 200
    assert b"Technik" in r.content
    assert b"Tomasz Nowak" in r.content


@pytest.mark.django_db
def test_role_required_mixin_denies_wrong_role():
    from django.http import HttpResponse
    from django.views import View

    from apps.accounts.mixins import RoleRequiredMixin

    class OnlyAdminView(RoleRequiredMixin, View):
        allowed_roles = (User.Role.ADMIN,)

        def get(self, request):
            return HttpResponse("ok")

    from django.test import override_settings
    from django.urls import path

    urlconf = type("U", (), {"urlpatterns": [path("only-admin/", OnlyAdminView.as_view())]})
    with override_settings(ROOT_URLCONF=urlconf):
        u = User.objects.create_user(username="emp", password="x", role=User.Role.EMPLOYEE)
        c = Client()
        c.force_login(u)
        r = c.get("/only-admin/")
        assert r.status_code == 403
