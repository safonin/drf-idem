import json
import re

from django.http import HttpResponse

from .cache import IdempotencyCache, MAX_REQUEST_ID_LENGTH
from .settings import get_settings

# Allow only safe characters: letters, digits, and -_./
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9\-_./]+$")


def _validate_request_id(value: str) -> bool:
    """Returns True if request_id is valid in length and character composition."""
    if not value or len(value) > MAX_REQUEST_ID_LENGTH:
        return False
    return bool(_REQUEST_ID_RE.match(value))


def _endpoint_matches(
    method: str, path: str, endpoints: list[str], methods: list[str]
) -> bool:
    """
    Checks whether this request should be checked for idempotency.

    Format of endpoint elements:
    - "POST /api/payments/" — specific method + path prefix
    - "/api/critical/"     — any method from `methods` + path prefix
    - "* /api/orders/"     — explicitly all methods + path prefix
    """
    if not endpoints:
        return method.upper() in [m.upper() for m in methods]

    for pattern in endpoints:
        parts = pattern.strip().split(None, 1)
        if len(parts) == 1:
            path_prefix = parts[0]
            if path.startswith(path_prefix) and method.upper() in [
                m.upper() for m in methods
            ]:
                return True
        else:
            pat_method, path_prefix = parts
            method_match = pat_method == "*" or pat_method.upper() == method.upper()
            if method_match and path.startswith(path_prefix):
                return True
    return False


class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cfg = get_settings()
        request_id = request.META.get(cfg["HEADER"])
        if not request_id:
            return self.get_response(request)

        # Reject request_id with invalid length or characters.
        # Return 400 to avoid silently ignoring a suspicious header.
        if not _validate_request_id(request_id):
            return HttpResponse(
                json.dumps({"detail": "invalid idempotency key"}),
                status=400,
                content_type="application/json",
            )

        if not _endpoint_matches(
            request.method, request.path, cfg["ENDPOINTS"], cfg["METHODS"]
        ):
            return self.get_response(request)

        cache = IdempotencyCache()

        response = self.get_response(request)
        # store_if_new is an atomic SET-IF-NOT-EXISTS operation,
        # eliminating the TOCTOU window between check and write.
        is_new = cache.store_if_new(request.method, request.path, request_id, response)

        if not is_new:
            cache.increment_stats(request.method, request.path)
            response = cache.get_response(request.method, request.path, request_id)

        return response
