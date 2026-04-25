import hashlib
import time
from typing import Any

from django.core.cache import caches
from django.http import HttpResponse

from .settings import get_settings

PREFIX = "drf_idem:req"

# Maximum allowed length of request_id (in characters).
# Values longer than this threshold are rejected as invalid.
MAX_REQUEST_ID_LENGTH = 128


class IdempotencyCache:
    def __init__(self):
        cfg = get_settings()
        self._backend = cfg["CACHE_BACKEND"]
        self._ttl = cfg["TTL"]

    @property
    def _cache(self):
        return caches[self._backend]

    def _make_key(self, method: str, path: str, request_id: str) -> str:
        # Hash the composite key to prevent collisions via
        # separator manipulation in the path or request_id.
        raw = f"{method.upper()}:{path}:{request_id}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{PREFIX}:{digest}"

    def exists(self, method: str, path: str, request_id: str) -> bool:
        return self._cache.get(self._make_key(method, path, request_id)) is not None

    def store(self, method: str, path: str, request_id: str) -> None:
        self._cache.set(self._make_key(method, path, request_id), 1, timeout=self._ttl)

    def store_if_new(self, method: str, path: str, request_id: str, response) -> bool:
        """Atomically writes the key if it does not already exist.

        Returns True if the key was written (new request),
        and False if the key already existed (duplicate request).

        Uses cache.add(), which is an atomic SET-IF-NOT-EXISTS
        operation (SETNX in Redis), eliminating the TOCTOU window
        between exists() and store().
        """
        key = self._make_key(method, path, request_id)
        cache_data = {
            "content": response.content,
            "status": response.status_code,
            "content_type": response.get("Content-Type", "application/json"),
        }
        return self._cache.add(key, cache_data, timeout=self._ttl)

    def get_response(self, method: str, path: str, request_id: str):
        key = self._make_key(method, path, request_id)
        cached_data = self._cache.get(key)
        if cached_data is None:
            return HttpResponse(
                content=b'{"detail": "Idempotency cache eviction error"}',
                status=500,
                content_type="application/json",
            )
        return HttpResponse(
            content=cached_data["content"],
            status=cached_data["status"],
            content_type=cached_data["content_type"],
        )

    def increment_stats(self, method: str, path: str) -> None:
        member = f"{method.upper()}:{path}"
        counts_key = "drf_idem:stats:counts"
        timestamps_key = "drf_idem:stats:ts"
        cfg = get_settings()
        stats_ttl = cfg.get("STATS_TTL", 60 * 60 * 24 * 7)
        current = self._cache.get(counts_key) or {}
        current[member] = current.get(member, 0) + 1
        self._cache.set(counts_key, current, timeout=stats_ttl)
        timestamps = self._cache.get(timestamps_key) or {}
        timestamps[member] = time.time()
        self._cache.set(timestamps_key, timestamps, timeout=stats_ttl)

    def get_top_stats(self, limit: int = 20) -> list[dict[str, Any]]:
        counts = self._cache.get("drf_idem:stats:counts") or {}
        timestamps = self._cache.get("drf_idem:stats:ts") or {}
        result = []
        for member, count in counts.items():
            try:
                method, path = member.split(":", 1)
            except ValueError:
                continue
            result.append(
                {
                    "endpoint": path,
                    "method": method,
                    "count": count,
                    "last_seen": timestamps.get(member),
                }
            )
        result.sort(key=lambda x: x["count"], reverse=True)
        return result[:limit]

    def get_memory_bytes(self) -> int:
        """
        Returns the approximate amount of memory occupied by drf_idem:* keys.
        Works only if the backend is Redis (redis-py).
        Returns 0 for other backends.
        """
        try:
            backend = self._cache
            if hasattr(backend, "client"):
                # django-redis
                client = backend.client.get_client()
            elif hasattr(backend, "_cache"):
                client = backend._cache.get_client()
            else:
                return 0
            cursor = 0
            total = 0
            while True:
                cursor, keys = client.scan(cursor, match="*drf_idem*", count=200)
                for key in keys:
                    usage = client.memory_usage(key)
                    if usage:
                        total += usage
                if cursor == 0:
                    break
            return total
        except Exception:
            return 0
