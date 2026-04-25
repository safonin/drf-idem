from django.test import override_settings


def test_defaults_applied_when_drf_idem_empty():
    from drf_idem.settings import get_settings

    with override_settings(DRF_IDEM={}):
        s = get_settings()
    assert s["TTL"] == 60
    assert s["HEADER"] == "HTTP_X_REQUEST_ID"
    assert s["METHODS"] == ["POST", "PUT", "PATCH", "DELETE"]
    assert s["ENDPOINTS"] == []


def test_ttl_capped_at_60():
    from drf_idem.settings import get_settings

    with override_settings(DRF_IDEM={"TTL": 300}):
        s = get_settings()
    assert s["TTL"] == 60


def test_custom_header_preserved():
    from drf_idem.settings import get_settings

    with override_settings(DRF_IDEM={"HEADER": "HTTP_IDEMPOTENCY_KEY"}):
        s = get_settings()
    assert s["HEADER"] == "HTTP_IDEMPOTENCY_KEY"


def test_custom_methods():
    from drf_idem.settings import get_settings

    with override_settings(DRF_IDEM={"METHODS": ["GET", "POST"]}):
        s = get_settings()
    assert s["METHODS"] == ["GET", "POST"]


def test_custom_endpoints():
    from drf_idem.settings import get_settings

    with override_settings(DRF_IDEM={"ENDPOINTS": ["POST /api/pay/"]}):
        s = get_settings()
    assert s["ENDPOINTS"] == ["POST /api/pay/"]
