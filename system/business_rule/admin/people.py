from django.contrib import admin

from system.business_rule.models import (
    OperationalRole,
    Person,
    PersonOperationalRole,
    PersonRelationship,
    PersonType,
    PortalAccount,
)


class OutgoingRelationshipInline(admin.TabularInline):
    model = PersonRelationship
    fk_name = "source_person"
    extra = 0
    autocomplete_fields = ("target_person",)
    fields = ("target_person", "relationship_kind", "kinship_type", "kinship_other_label", "notes")


class IncomingRelationshipInline(admin.TabularInline):
    model = PersonRelationship
    fk_name = "target_person"
    extra = 0
    autocomplete_fields = ("source_person",)
    fields = ("source_person", "relationship_kind", "kinship_type", "kinship_other_label", "notes")


class PersonOperationalRoleInline(admin.TabularInline):
    model = PersonOperationalRole
    extra = 0
    autocomplete_fields = ("role", "class_group")
    fields = ("role", "class_group", "is_active", "notes")


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


@admin.register(OperationalRole)
class OperationalRoleAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code", "description")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "cpf",
        "person_type",
        "email",
        "phone",
        "is_active",
        "has_portal_access_flag",
    )
    list_filter = ("is_active", "person_type", "blood_type", "biological_sex")
    search_fields = ("full_name", "cpf", "email", "phone")
    autocomplete_fields = ("person_type", "class_category", "class_group", "class_schedule")
    inlines = [
        PersonOperationalRoleInline,
        OutgoingRelationshipInline,
        IncomingRelationshipInline,
    ]

    @admin.display(boolean=True, description="Acesso portal")
    def has_portal_access_flag(self, obj):
        return obj.has_portal_access


@admin.register(PortalAccount)
class PortalAccountAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "is_active",
        "failed_login_attempts",
        "last_login_at",
        "password_updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("person__full_name", "person__cpf", "person__email")
    autocomplete_fields = ("person",)
    readonly_fields = ("created_at", "updated_at", "last_login_at", "password_updated_at")


@admin.register(PersonRelationship)
class PersonRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "source_person",
        "relationship_kind",
        "target_person",
        "kinship_type",
        "created_at",
    )
    list_filter = ("relationship_kind", "kinship_type")
    search_fields = (
        "source_person__full_name",
        "target_person__full_name",
        "source_person__cpf",
        "target_person__cpf",
        "notes",
    )
    autocomplete_fields = ("source_person", "target_person")
