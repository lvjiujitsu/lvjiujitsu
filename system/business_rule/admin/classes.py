from django.contrib import admin

from system.business_rule.models import (
    ClassCategory,
    ClassCheckin,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    ClassSession,
    Holiday,
    IbjjfAgeCategory,
    SpecialClass,
    SpecialClassCheckin,
)


class ClassScheduleInline(admin.TabularInline):
    model = ClassSchedule
    extra = 0
    fields = ("weekday", "start_time", "duration_minutes", "training_style", "display_order", "is_active")
    ordering = ("weekday", "start_time")


class ClassInstructorAssignmentInline(admin.TabularInline):
    model = ClassInstructorAssignment
    extra = 0
    autocomplete_fields = ("person",)
    fields = ("person", "notes")


@admin.register(ClassCategory)
class ClassCategoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "audience", "display_order", "is_active")
    list_filter = ("audience", "is_active")
    search_fields = ("display_name", "code")


@admin.register(IbjjfAgeCategory)
class IbjjfAgeCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "code",
        "audience",
        "minimum_age",
        "maximum_age",
        "display_order",
        "is_active",
    )
    list_filter = ("audience", "is_active")
    search_fields = ("display_name", "code")


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "class_category",
        "main_teacher",
        "default_capacity",
        "is_active",
    )
    list_filter = ("class_category", "is_active")
    search_fields = ("display_name", "class_category__display_name", "main_teacher__full_name")
    autocomplete_fields = ("class_category", "main_teacher")
    inlines = [ClassScheduleInline, ClassInstructorAssignmentInline]


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "class_group",
        "weekday",
        "start_time",
        "duration_minutes",
        "training_style",
        "is_active",
    )
    list_filter = ("weekday", "training_style", "is_active")
    search_fields = ("class_group__display_name", "class_group__class_category__display_name")
    autocomplete_fields = ("class_group",)


@admin.register(ClassInstructorAssignment)
class ClassInstructorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("class_group", "person", "created_at")
    list_filter = ("class_group",)
    search_fields = ("class_group__display_name", "person__full_name", "person__cpf")
    autocomplete_fields = ("class_group", "person")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("schedule", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("schedule__class_group__display_name",)
    autocomplete_fields = ("schedule",)


@admin.register(ClassCheckin)
class ClassCheckinAdmin(admin.ModelAdmin):
    list_display = ("person", "session", "status", "checked_in_at", "approved_at")
    list_filter = ("status", "checked_in_at")
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person", "session", "approved_by")


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("person", "class_group", "status", "created_at")
    list_filter = ("status", "class_group")
    search_fields = ("person__full_name", "person__cpf", "class_group__display_name")
    autocomplete_fields = ("person", "class_group")


@admin.register(SpecialClass)
class SpecialClassAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "start_time", "teacher", "status", "instructor_present")
    list_filter = ("status", "date")
    search_fields = ("title", "teacher__full_name")
    autocomplete_fields = ("teacher", "substitute_teacher")


@admin.register(SpecialClassCheckin)
class SpecialClassCheckinAdmin(admin.ModelAdmin):
    list_display = ("special_class", "person", "status", "checked_in_at", "approved_at")
    list_filter = ("status",)
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("special_class", "person", "approved_by")
