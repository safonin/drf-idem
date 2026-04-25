from django.contrib import admin
from django.db import models
from django.urls import path
from django.apps import apps

from .views import admin_stats_view


class IdempotencyStat(models.Model):
    class Meta:
        managed = False
        app_label = "drf_idem"
        verbose_name = "Idempotency Statistics"
        verbose_name_plural = "Idempotency Statistics"


# Prevent makemigrations from creating a migration for this dummy model
if "idempotencystat" in apps.all_models.get("drf_idem", {}):
    del apps.all_models["drf_idem"]["idempotencystat"]


@admin.register(IdempotencyStat)
class IdempotencyStatAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "",
                self.admin_site.admin_view(admin_stats_view),
                name="drf_idem_idempotencystat_changelist",
            ),
        ]
        return custom_urls + urls

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
