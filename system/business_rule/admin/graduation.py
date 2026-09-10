from django.contrib import admin

from system.business_rule.models import (
    BeltRank,
    Graduation,
    GraduationRule,
)


@admin.register(BeltRank)
class BeltRankAdmin(admin.ModelAdmin):
    list_display = ("display_name", "audience", "max_grades", "min_age", "max_age", "next_rank", "is_active", "display_order")
    list_filter = ("audience", "is_active")
    search_fields = ("display_name", "code")
    autocomplete_fields = ("next_rank",)


@admin.register(GraduationRule)
class GraduationRuleAdmin(admin.ModelAdmin):
    list_display = ("belt_rank", "from_grade", "to_grade", "min_months_in_current_grade", "min_classes_required", "min_classes_window_months", "is_active")
    list_filter = ("is_active", "belt_rank")
    autocomplete_fields = ("belt_rank",)


@admin.register(Graduation)
class GraduationAdmin(admin.ModelAdmin):
    list_display = ("person", "belt_rank", "grade_number", "awarded_at", "awarded_by")
    list_filter = ("belt_rank",)
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person", "belt_rank", "awarded_by")
