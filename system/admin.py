from django.contrib import admin

from system.models import (
    Person,
    PersonRelationship,
    PersonType,
    PersonTypeAssignment,
    PortalAccount,
    PortalPasswordResetToken,
)


class PersonTypeAssignmentInline(admin.TabularInline):
    model = PersonTypeAssignment
    extra = 0


class OutgoingRelationshipInline(admin.TabularInline):
    model = PersonRelationship
    fk_name = "source_person"
    extra = 0
    autocomplete_fields = ("target_person",)


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cpf", "email", "phone", "blood_type", "is_active")
    list_filter = ("is_active", "person_types", "blood_type")
    search_fields = ("full_name", "cpf", "email")
    inlines = [PersonTypeAssignmentInline, OutgoingRelationshipInline]


@admin.register(PortalAccount)
class PortalAccountAdmin(admin.ModelAdmin):
    list_display = ("person", "is_active", "failed_login_attempts", "last_login_at")
    list_filter = ("is_active",)
    search_fields = ("person__full_name", "person__cpf", "person__email")
    autocomplete_fields = ("person",)


@admin.register(PersonTypeAssignment)
class PersonTypeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("person", "person_type", "created_at")
    search_fields = ("person__full_name", "person_type__display_name")


@admin.register(PersonRelationship)
class PersonRelationshipAdmin(admin.ModelAdmin):
    list_display = ("source_person", "relationship_kind", "target_person", "created_at")
    list_filter = ("relationship_kind",)
    search_fields = ("source_person__full_name", "target_person__full_name", "notes")
    autocomplete_fields = ("source_person", "target_person")


@admin.register(PortalPasswordResetToken)
class PortalPasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("access_account", "token", "expires_at", "used_at", "created_at")
    list_filter = ("used_at",)
    search_fields = ("access_account__person__full_name", "access_account__person__cpf", "token")
    autocomplete_fields = ("access_account",)
