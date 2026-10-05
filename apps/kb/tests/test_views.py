import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.kb.models import ArticleTag, KnowledgeArticle


@pytest.mark.django_db
def test_employee_sees_only_published():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    emp = User.objects.create_user(username="emp", password="x")
    KnowledgeArticle.objects.create(title="Public", body="...", author=tech, status="PUBLISHED")
    KnowledgeArticle.objects.create(title="Draft", body="...", author=tech, status="DRAFT")

    c = Client()
    c.force_login(emp)
    r = c.get(reverse("kb:list"))
    assert r.status_code == 200
    assert b"Public" in r.content
    assert b"Draft" not in r.content


@pytest.mark.django_db
def test_technician_sees_drafts_too():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    KnowledgeArticle.objects.create(title="Draft", body="...", author=tech, status="DRAFT")
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("kb:list"))
    assert b"Draft" in r.content


@pytest.mark.django_db
def test_article_views_counter_increments():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    a = KnowledgeArticle.objects.create(
        title="X", body="...", author=tech, status="PUBLISHED", slug="x"
    )
    c = Client()
    c.force_login(tech)
    c.get(reverse("kb:detail", args=["x"]))
    c.get(reverse("kb:detail", args=["x"]))
    a.refresh_from_db()
    assert a.views == 2


@pytest.mark.django_db
def test_employee_cannot_create_article():
    emp = User.objects.create_user(username="emp", password="x")
    c = Client()
    c.force_login(emp)
    r = c.get(reverse("kb:create"))
    assert r.status_code == 403


@pytest.mark.django_db
def test_search_finds_article_by_title():
    tech = User.objects.create_user(username="tech", password="x", role=User.Role.TECHNICIAN)
    KnowledgeArticle.objects.create(
        title="Drukarka HP nie drukuje",
        body="Sprawdź toner",
        author=tech,
        status="PUBLISHED",
    )
    c = Client()
    c.force_login(tech)
    r = c.get(reverse("kb:list"), {"q": "drukarka"})
    assert b"Drukarka HP" in r.content