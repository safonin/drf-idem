import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_request_without_header_passes_through(client):
    resp = client.post("/api/test/", data={}, format="json")
    assert resp.status_code == 200
    assert resp.json()["method"] == "POST"


def test_first_request_with_header_passes_through(client):
    resp = client.post(
        "/api/test/",
        data={},
        format="json",
        HTTP_X_REQUEST_ID="abc-123",
    )
    assert resp.status_code == 200
    assert resp.json()["method"] == "POST"


def test_duplicate_request_returns_duplicate_status(client):
    client.post("/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="dup-456")
    resp = client.post(
        "/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="dup-456"
    )
    assert resp.status_code == 200
    assert resp.json() == {"method": "POST", "path": "/api/test/"}


def test_duplicate_get_not_blocked_by_default(client):
    """GET не входит в METHODS по умолчанию."""
    client.get("/api/test/", HTTP_X_REQUEST_ID="get-789")
    resp = client.get("/api/test/", HTTP_X_REQUEST_ID="get-789")
    assert resp.json()["method"] == "GET"


@override_settings(
    DRF_IDEM={
        "METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "ENDPOINTS": [],
        "TTL": 60,
        "HEADER": "HTTP_X_REQUEST_ID",
        "CACHE_BACKEND": "drf_idem",
    }
)
def test_duplicate_get_blocked_when_method_included(client):
    client.get("/api/test/", HTTP_X_REQUEST_ID="get-dup")
    resp = client.get("/api/test/", HTTP_X_REQUEST_ID="get-dup")
    assert resp.json() == {"method": "GET", "path": "/api/test/"}


@override_settings(
    DRF_IDEM={
        "ENDPOINTS": ["POST /api/payments/"],
        "METHODS": ["POST"],
        "TTL": 60,
        "HEADER": "HTTP_X_REQUEST_ID",
        "CACHE_BACKEND": "drf_idem",
    }
)
def test_endpoint_filter_blocks_matching(client):
    client.post("/api/payments/", data={}, format="json", HTTP_X_REQUEST_ID="pay-001")
    resp = client.post(
        "/api/payments/", data={}, format="json", HTTP_X_REQUEST_ID="pay-001"
    )
    assert resp.json() == {"method": "POST", "path": "/api/payments/"}


@override_settings(
    DRF_IDEM={
        "ENDPOINTS": ["POST /api/payments/"],
        "METHODS": ["POST"],
        "TTL": 60,
        "HEADER": "HTTP_X_REQUEST_ID",
        "CACHE_BACKEND": "drf_idem",
    }
)
def test_endpoint_filter_skips_non_matching(client):
    """Запрос к /api/test/ не в ENDPOINTS — не фильтруется."""
    client.post("/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="test-skip")
    resp = client.post(
        "/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="test-skip"
    )
    assert resp.json()["method"] == "POST"


def test_different_paths_same_request_id_not_blocked(client):
    """Один request_id на разные пути — не должен блокироваться."""
    client.post("/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="same-id")
    resp = client.post(
        "/api/payments/", data={}, format="json", HTTP_X_REQUEST_ID="same-id"
    )
    assert resp.json()["method"] == "POST"


def test_different_methods_same_request_id_not_blocked(client):
    """Один request_id, разные методы — не должен блокироваться."""
    client.post("/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="method-id")
    resp = client.put(
        "/api/test/", data={}, format="json", HTTP_X_REQUEST_ID="method-id"
    )
    assert resp.json()["method"] == "PUT"


def test_endpoint_wildcard_matching():
    from drf_idem.middleware import _endpoint_matches

    # Wildcard path matching
    endpoints = ["POST /api/v5/order/*/pay/"]
    assert (
        _endpoint_matches("POST", "/api/v5/order/123/pay/", endpoints, ["POST"]) is True
    )
    assert (
        _endpoint_matches("POST", "/api/v5/order/123/pay/details", endpoints, ["POST"])
        is True
    )
    assert _endpoint_matches("POST", "/api/v5/order/pay/", endpoints, ["POST"]) is False

    # Implicit prefix matching for regular strings
    endpoints_prefix = ["/api/payments/"]
    assert (
        _endpoint_matches("POST", "/api/payments/123/", endpoints_prefix, ["POST"])
        is True
    )
    assert (
        _endpoint_matches("POST", "/api/payments/", endpoints_prefix, ["POST"]) is True
    )
