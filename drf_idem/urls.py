from django.urls import path

from .views import admin_stats_view

urlpatterns = [
    path("stats/", admin_stats_view, name="drf_idem_stats"),
]
