from django.contrib import admin
from django.utils import timezone

from system.models import (
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonRelationship,
    PersonType,
    PortalAccount,
    PortalPasswordResetToken,
    Product,
    ProductCategory,
    ProductVariant,
    RegistrationOrder,
    RegistrationOrderItem,
    SubscriptionPlan,
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


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


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
    inlines = [OutgoingRelationshipInline, IncomingRelationshipInline]

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


@admin.register(PortalPasswordResetToken)
class PortalPasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("access_account", "token_preview", "expires_at", "used_at", "is_currently_valid")
    list_filter = ("used_at",)
    search_fields = ("access_account__person__full_name", "access_account__person__cpf")
    autocomplete_fields = ("access_account",)
    readonly_fields = ("access_account", "token", "created_at", "expires_at", "used_at")
    fields = ("access_account", "token", "created_at", "expires_at", "used_at")

    @admin.display(description="Token")
    def token_preview(self, obj):
        if not obj.token:
            return "-"
        return f"{obj.token[:8]}..."

    @admin.display(boolean=True, description="Válido")
    def is_currently_valid(self, obj):
        return obj.used_at is None and timezone.now() <= obj.expires_at

    def has_add_permission(self, request):
        return False


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
        "code",
        "class_category",
        "main_teacher",
        "default_capacity",
        "is_active",
    )
    list_filter = ("class_category", "is_active")
    search_fields = ("display_name", "code", "class_category__display_name")
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
    search_fields = ("class_group__display_name", "class_group__code")
    autocomplete_fields = ("class_group",)


@admin.register(ClassInstructorAssignment)
class ClassInstructorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("class_group", "person", "created_at")
    list_filter = ("class_group",)
    search_fields = ("class_group__display_name", "person__full_name", "person__cpf")
    autocomplete_fields = ("class_group", "person")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("color", "size", "stock_quantity", "is_active")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("display_name", "sku", "category", "unit_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("display_name", "sku")
    autocomplete_fields = ("category",)
    inlines = [ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "size", "stock_quantity", "is_active")
    list_filter = ("is_active", "product__category")
    search_fields = ("product__display_name", "color", "size")
    autocomplete_fields = ("product",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "billing_cycle", "price", "display_order", "is_active")
    list_filter = ("billing_cycle", "is_active")
    search_fields = ("display_name", "code")


class RegistrationOrderItemInline(admin.TabularInline):
    model = RegistrationOrderItem
    extra = 0
    fields = ("product_name", "quantity", "unit_price", "subtotal")
    readonly_fields = ("product_name", "quantity", "unit_price", "subtotal")


@admin.register(RegistrationOrder)
class RegistrationOrderAdmin(admin.ModelAdmin):
    list_display = ("pk", "person", "plan", "plan_price", "total", "created_at")
    list_filter = ("plan",)
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person", "plan")
    inlines = [RegistrationOrderItemInline]


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("person", "class_group", "status", "created_at")
    list_filter = ("status", "class_group")
    search_fields = ("person__full_name", "person__cpf", "class_group__display_name")
    autocomplete_fields = ("person", "class_group")
