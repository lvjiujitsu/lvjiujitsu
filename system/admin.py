from django.contrib import admin

from system.models import Person, PersonType, PersonTypeAssignment


class PersonTypeAssignmentInline(admin.TabularInline):
    model = PersonTypeAssignment
    extra = 0


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cpf", "email", "phone", "is_active")
    list_filter = ("is_active", "person_types")
    search_fields = ("full_name", "cpf", "email")
    autocomplete_fields = ("user",)
    inlines = [PersonTypeAssignmentInline]


@admin.register(PersonTypeAssignment)
class PersonTypeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("person", "person_type", "created_at")
    search_fields = ("person__full_name", "person_type__display_name")
