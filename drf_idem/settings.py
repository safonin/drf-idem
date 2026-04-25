from django.conf import settings

DEFAULTS = {
    # Request header that carries the idempotency key
    "HEADER": "HTTP_X_REQUEST_ID",
    # Time-to-live for idempotency cache in seconds (max 60)
    "TTL": 60,
    # Which Django cache backend to use
    "CACHE_BACKEND": "drf_idem",
    # Endpoints to protect. Empty list means apply to all paths.
    # Supported formats:
    # - "METHOD /path/prefix" (e.g. "POST /api/payments/")
    # - "/path/prefix" (applies to all methods in METHODS)
    # - "* /path/prefix" (applies to absolutely all methods)
    "ENDPOINTS": [],
    # Methods to protect when ENDPOINTS is empty, or when a path-only pattern is used
    "METHODS": ["POST", "PUT", "PATCH", "DELETE"],
    # TTL for aggregated statistics (duplicate counters per endpoint).
    # Default is 7 days; None = never expires.
    "STATS_TTL": 60 * 60 * 24 * 7,
}

MAX_TTL = 60  # Spec: maximum 60 seconds


def get_settings() -> dict:
    user_settings = getattr(settings, "DRF_IDEM", {})
    result = {**DEFAULTS, **user_settings}
    result["TTL"] = min(int(result["TTL"]), MAX_TTL)
    return result
