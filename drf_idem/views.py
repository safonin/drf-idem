from datetime import datetime, timezone

from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from .cache import IdempotencyCache


@user_passes_test(lambda u: u.is_active and u.is_superuser)
def admin_stats_view(request):
    cache = IdempotencyCache()
    stats = cache.get_top_stats(limit=50)
    for row in stats:
        if row.get("last_seen"):
            dt = datetime.fromtimestamp(row["last_seen"], tz=timezone.utc)
            row["last_seen_iso"] = dt.isoformat(timespec="seconds").replace(
                "+00:00", "Z"
            )
    memory_bytes = cache.get_memory_bytes()
    memory_kb = memory_bytes / 1024
    memory_mb = memory_kb / 1024
    warn_threshold_mb = 10

    context = {
        "title": "drf-idem: Duplicate Requests Statistics",
        "stats": stats,
        "memory_bytes": memory_bytes,
        "memory_kb": round(memory_kb, 2),
        "memory_mb": round(memory_mb, 4),
        "memory_warning": memory_mb > warn_threshold_mb,
        "warn_threshold_mb": warn_threshold_mb,
        **(admin.site.each_context(request)),
    }
    return render(request, "drf_idem/admin_stats.html", context)
