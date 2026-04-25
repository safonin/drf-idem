import pytest
from drf_idem.cache import IdempotencyCache


@pytest.fixture
def cache():
    return IdempotencyCache()


def test_key_not_exists_initially(cache):
    assert cache.exists("POST", "/api/test/", "req-123") is False


def test_key_stored_and_found(cache):
    cache.store("POST", "/api/test/", "req-123")
    assert cache.exists("POST", "/api/test/", "req-123") is True


def test_different_request_id_not_found(cache):
    cache.store("POST", "/api/test/", "req-123")
    assert cache.exists("POST", "/api/test/", "req-999") is False


def test_different_method_not_found(cache):
    cache.store("POST", "/api/test/", "req-123")
    assert cache.exists("GET", "/api/test/", "req-123") is False


def test_different_path_not_found(cache):
    cache.store("POST", "/api/test/", "req-123")
    assert cache.exists("POST", "/api/other/", "req-123") is False


def test_increment_stats(cache):
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("POST", "/api/payments/")
    stats = cache.get_top_stats(limit=5)
    assert stats[0]["endpoint"] == "/api/payments/"
    assert stats[0]["method"] == "POST"
    assert stats[0]["count"] >= 3


def test_stats_sorted_by_count(cache):
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("POST", "/api/payments/")
    cache.increment_stats("GET", "/api/other/")
    stats = cache.get_top_stats(limit=5)
    assert stats[0]["count"] >= stats[1]["count"]


def test_get_memory_usage_returns_int(cache):
    cache.store("POST", "/api/test/", "req-mem-test")
    usage = cache.get_memory_bytes()
    assert isinstance(usage, int)
    assert usage >= 0


def test_stats_last_seen_set(cache):
    import time

    before = time.time()
    cache.increment_stats("PUT", "/api/orders/")
    stats = cache.get_top_stats(limit=5)
    assert stats[0]["last_seen"] >= before


def test_store_if_new_and_get_response(cache):
    from django.http import HttpResponse

    response = HttpResponse(
        content=b'{"test": "ok"}', status=201, content_type="application/json"
    )
    is_new = cache.store_if_new("POST", "/api/data/", "req-new", response)
    assert is_new is True

    is_new_dup = cache.store_if_new("POST", "/api/data/", "req-new", response)
    assert is_new_dup is False

    cached_resp = cache.get_response("POST", "/api/data/", "req-new")
    assert cached_resp.status_code == 201
    assert cached_resp.content == b'{"test": "ok"}'
    assert cached_resp.get("Content-Type") == "application/json"


def test_get_response_eviction(cache):
    cached_resp = cache.get_response("POST", "/api/data/", "req-missing")
    assert cached_resp.status_code == 500
    assert cached_resp.content == b'{"detail": "Idempotency cache eviction error"}'
