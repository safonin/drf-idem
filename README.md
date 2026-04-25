# drf-idem

*[Читать на русском (Read in Russian)](README_RU.md)*

Idempotency middleware for Django REST Framework. Prevents duplicate request processing using Redis.

When a client sends the same request twice (network retry, double-click, bug), `drf-idem` detects the duplicate and returns an immediate response — without running your business logic a second time.

## Installation

```bash
# In a uv-managed project
uv add drf-idem

# Or via pip
pip install drf-idem
```

## Quick Start

**1. Add to `INSTALLED_APPS`:**

```python
INSTALLED_APPS = [
    ...
    "drf_idem",
]
```

**2. Add middleware first in the list:**

```python
MIDDLEWARE = [
    "drf_idem.middleware.IdempotencyMiddleware",
    ...
]
```

**3. Configure a dedicated Redis cache backend:**

```python
CACHES = {
    "default": { ... },
    "drf_idem": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
    },
}
```

**4. Add settings:**

```python
DRF_IDEM = {
    "HEADER": "HTTP_X_REQUEST_ID",   # reads X-Request-ID header
    "TTL": 60,                        # seconds, max 60
    "CACHE_BACKEND": "drf_idem",
    "ENDPOINTS": [],                  # empty = check all endpoints
                                      # formats: "POST /path", "/path" (all METHODS), "* /path" (absolutely all)
    "METHODS": ["POST", "PUT", "PATCH", "DELETE"],
}
```

**5. Mount admin stats page in `urls.py`:**

```python
# IMPORTANT: place before path("admin/", admin.site.urls)
urlpatterns = [
    path("admin/drf-idem/", include("drf_idem.urls")),
    path("admin/", admin.site.urls),
    ...
]
```

Open `/admin/drf-idem/stats/` to see duplicate request statistics.

## How It Works

The client attaches a unique `X-Request-ID` header to each request:

```http
POST /api/payments/ HTTP/1.1
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{"amount": 100}
```

**First request** — processed normally, key stored in Redis with TTL.

**Duplicate request** (same `X-Request-ID` + same method + same path, within TTL):

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"amount": 100}
```

Business logic is not executed. The exact same HTTP status and body from the original response are returned transparently to the client.

## Settings Reference

| Key | Default | Description |
|-----|---------|-------------|
| `HEADER` | `HTTP_X_REQUEST_ID` | Django META key for the idempotency header (`X-Request-ID` → `HTTP_X_REQUEST_ID`) |
| `TTL` | `60` | Seconds to remember a request. Capped at 60. |
| `CACHE_BACKEND` | `"drf_idem"` | Django CACHES alias to use |
| `ENDPOINTS` | `[]` | Endpoint filter (empty = apply to all). Formats: `"METHOD /path"`, `"/path"`, `"* /path"` |
| `METHODS` | `["POST", "PUT", "PATCH", "DELETE"]` | HTTP methods to check when `ENDPOINTS` is empty |
| `STATS_TTL` | `604800` (7 days) | TTL for statistics data in Redis |

## Endpoint Filtering

Use `ENDPOINTS` to restrict which endpoints are protected:

```python
DRF_IDEM = {
    "ENDPOINTS": [
        "POST /api/payments/",   # only POST to /api/payments/*
        "/api/orders/",          # any method from METHODS to /api/orders/*
        "* /api/critical/",      # all methods to /api/critical/*
    ],
}
```

Pattern formats:
- `"METHOD /path/prefix"` — specific method + path prefix
- `"/path/prefix"` — any method from `METHODS` + path prefix
- `"* /path/prefix"` — all methods + path prefix

When `ENDPOINTS` is empty, all endpoints matching `METHODS` are checked.

## Security

- **Key isolation:** Cache keys use SHA-256 of `(method, path, request_id)` — no injection via separator characters.
- **Input validation:** `request_id` must be ≤ 128 chars and match `[A-Za-z0-9\-_./]+`. Invalid values return HTTP 400.
- **Atomic writes:** Uses `cache.add()` (Redis SETNX) to eliminate TOCTOU race conditions.
- **Admin protection:** Stats page requires `is_staff=True`.

## Admin Statistics

The stats page at `/admin/drf-idem/stats/` shows:

- Top endpoints by duplicate count
- Timestamp of last duplicate
- Total Redis memory used by `drf_idem:*` keys (with warning if > 10 MB)

## Development

```bash
git clone https://github.com/example/drf-idem
cd drf-idem
uv sync --extra dev
uv run pytest -v
```

## License

MIT
