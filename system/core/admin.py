from django.contrib import admin
from django.contrib.auth import get_user_model

from system.core.audit.models import AuditEntry


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "module", "action", "actor_label", "entity_label")
    list_filter = ("module", "action")
    search_fields = ("actor_label", "entity_label", "summary")
    readonly_fields = (
        "module",
        "action",
        "actor_label",
        "entity_label",
        "summary",
        "created_at",
    )


@admin.register(get_user_model())
class TechnicalUserAdmin(admin.ModelAdmin):
    list_display = ("username", "name", "email", "is_active", "is_staff", "is_superuser")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "name", "email")
    ordering = ("username",)
    readonly_fields = ("last_login", "created_at", "updated_at")
