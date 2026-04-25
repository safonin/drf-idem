SECRET_KEY = "test-secret-key"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "drf_idem",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "drf_idem": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}
DRF_IDEM = {
    "TTL": 60,
    "HEADER": "HTTP_X_REQUEST_ID",
    "CACHE_BACKEND": "drf_idem",
    # Endpoint filtering. Empty list means apply to all paths.
    # Supported formats: "METHOD /path", "/path" (applies to METHODS), "* /path"
    "ENDPOINTS": [],
    # Methods to protect when ENDPOINTS is empty or when a pattern has no explicit method
    "METHODS": ["POST", "PUT", "PATCH", "DELETE"],
}
ROOT_URLCONF = "tests.urls"
MIDDLEWARE = [
    "drf_idem.middleware.IdempotencyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
