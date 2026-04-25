import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def admin_client(db):
    user = User.objects.create_superuser("admin", "admin@example.com", "password")
    c = Client()
    c.force_login(user)
    return c


@pytest.fixture
def stats_in_cache():
    from drf_idem.cache import IdempotencyCache

    cache = IdempotencyCache()
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("PUT", "/api/orders/")


def test_stats_page_accessible(admin_client):
    resp = admin_client.get("/admin/drf-idem/stats/")
    assert resp.status_code == 200


def test_stats_page_shows_endpoints(admin_client, stats_in_cache):
    resp = admin_client.get("/admin/drf-idem/stats/")
    content = resp.content.decode()
    assert "/api/payments/" in content
    assert "/api/orders/" in content


def test_stats_page_shows_counts(admin_client, stats_in_cache):
    resp = admin_client.get("/admin/drf-idem/stats/")
    content = resp.content.decode()
    assert "2" in content


def test_stats_page_shows_memory_section(admin_client):
    resp = admin_client.get("/admin/drf-idem/stats/")
    assert resp.status_code == 200
    content = resp.content.decode().lower()
    assert "memory" in content or "памят" in content


def test_stats_page_requires_login():
    c = Client()
    resp = c.get("/admin/drf-idem/stats/")
    assert resp.status_code in (302, 403)


def test_stats_page_requires_superuser(db):
    user = User.objects.create_user(
        "staff", "staff@example.com", "password", is_staff=True, is_superuser=False
    )
    c = Client()
    c.force_login(user)
    resp = c.get("/admin/drf-idem/stats/")
    assert resp.status_code in (302, 403)
