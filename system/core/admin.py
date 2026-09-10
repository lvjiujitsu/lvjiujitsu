from django.contrib import admin

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
