from django.contrib import admin

from system.business_rule.models import (
    AdministrativeAccessRequest,
    ClassCatalogRequest,
)


@admin.register(AdministrativeAccessRequest)
class AdministrativeAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cpf", "status", "origin", "person", "decided_by", "created_at")
    list_filter = ("status", "origin")
    search_fields = ("full_name", "cpf", "email")
    autocomplete_fields = ("person", "approved_person", "decided_by")


@admin.register(ClassCatalogRequest)
class ClassCatalogRequestAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "full_name",
        "request_type",
        "status",
        "origin",
        "teacher_person",
        "target_class_group",
        "created_at",
    )
    list_filter = ("status", "request_type", "origin")
    search_fields = ("full_name", "cpf", "display_name")
    autocomplete_fields = (
        "requester_person",
        "teacher_person",
        "created_teacher",
        "decided_by",
        "target_class_group",
        "created_class_group",
        "class_category",
    )
