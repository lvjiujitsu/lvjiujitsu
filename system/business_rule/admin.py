from django.contrib import admin, messages

from system.business_rule.models import (
    AdministrativeAccessRequest,
    AsaasWebhookEvent,
    BeltRank,
    ClassCatalogRequest,
    ClassCategory,
    ClassCheckin,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    ClassSession,
    Coupon,
    Graduation,
    GraduationRule,
    Holiday,
    IbjjfAgeCategory,
    Membership,
    MembershipCredit,
    MembershipInvoice,
    MembershipPauseRequest,
    MembershipTimelineEvent,
    OperationalRole,
    Person,
    PersonOperationalRole,
    PersonRelationship,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    PreRegistration,
    Product,
    ProductBackorder,
    ProductCategory,
    ProductVariant,
    RegistrationOrder,
    RegistrationOrderItem,
    SpecialClass,
    SpecialClassCheckin,
    StripeWebhookEvent,
    SubscriptionPlan,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
    TrialAccessGrant,
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


@admin.register(ProductBackorder)
class ProductBackorderAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "person",
        "variant",
        "status",
        "created_at",
        "notified_at",
        "expires_at",
    )
    list_filter = ("status", "variant__product__category")
    search_fields = (
        "person__full_name",
        "person__cpf",
        "variant__product__display_name",
    )
    autocomplete_fields = ("person", "variant", "confirmed_order")
    readonly_fields = ("notified_at", "confirmed_at", "canceled_at", "expires_at")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "code",
        "audience",
        "weekly_frequency",
        "billing_cycle",
        "payment_method",
        "price",
        "monthly_reference_price",
        "is_family_plan",
        "teacher_commission_percentage",
        "requires_special_authorization",
        "display_order",
        "is_active",
    )
    list_filter = (
        "audience",
        "weekly_frequency",
        "billing_cycle",
        "payment_method",
        "is_family_plan",
        "requires_special_authorization",
        "is_active",
    )
    search_fields = ("display_name", "code")

    def changelist_view(self, request, extra_context=None):
        self.message_user(
            request,
            "SubscriptionPlan é legado (sp:). Use PlanTier/PlanPrice (pp:) para catálogo novo.",
            level=messages.WARNING,
        )
        return super().changelist_view(request, extra_context=extra_context)


class RegistrationOrderItemInline(admin.TabularInline):
    model = RegistrationOrderItem
    extra = 0
    fields = ("product_name", "quantity", "unit_price", "subtotal")
    readonly_fields = ("product_name", "quantity", "unit_price", "subtotal")


@admin.register(RegistrationOrder)
class RegistrationOrderAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "person",
        "plan",
        "payment_status",
        "payment_provider",
        "total",
        "administrative_fee",
        "net_amount",
        "deposit_status",
        "expected_deposit_date",
        "created_at",
    )
    list_filter = ("payment_status", "payment_provider", "deposit_status", "plan")
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person", "plan")
    readonly_fields = (
        "administrative_fee",
        "net_amount",
        "financial_transaction_id",
        "created_at",
        "updated_at",
    )
    inlines = [RegistrationOrderItemInline]


@admin.register(TrialAccessGrant)
class TrialAccessGrantAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "person",
        "order",
        "granted_classes",
        "consumed_classes",
        "is_active",
        "activated_at",
    )
    list_filter = ("is_active", "activated_at")
    search_fields = ("person__full_name", "person__cpf", "order__pk")
    autocomplete_fields = ("person", "order")


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


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("person", "class_group", "status", "created_at")
    list_filter = ("status", "class_group")
    search_fields = ("person__full_name", "person__cpf", "class_group__display_name")
    autocomplete_fields = ("person", "class_group")


@admin.register(PlanTier)
class PlanTierAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "code",
        "audience",
        "weekly_frequency",
        "family_discount_percentage",
        "display_order",
        "is_active",
    )
    list_filter = ("audience", "weekly_frequency", "is_active")
    search_fields = ("display_name", "code")


@admin.register(PlanPrice)
class PlanPriceAdmin(admin.ModelAdmin):
    list_display = (
        "tier",
        "payment_method",
        "billing_cycle",
        "gateway_code",
        "price",
        "monthly_reference_price",
        "is_active",
        "effective_from",
        "effective_until",
    )
    list_filter = ("payment_method", "billing_cycle", "is_active", "tier")
    search_fields = ("tier__display_name", "gateway_code", "stripe_price_id")
    autocomplete_fields = ("tier",)
    readonly_fields = ("price", "monthly_reference_price", "stripe_synced_at")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "effective_display_name",
        "status",
        "billed_price",
        "family_discount_applied",
        "created_via",
        "current_period_end",
        "cancel_at_period_end",
    )
    list_filter = ("status", "created_via", "family_discount_applied")
    search_fields = (
        "person__full_name",
        "person__cpf",
        "stripe_subscription_id",
        "stripe_customer_id",
    )
    autocomplete_fields = ("person", "plan", "plan_price")


@admin.register(MembershipCredit)
class MembershipCreditAdmin(admin.ModelAdmin):
    list_display = ("membership", "amount", "source", "status", "applied_at", "refunded_at")
    list_filter = ("source", "status")
    search_fields = ("membership__person__full_name", "membership__person__cpf")
    autocomplete_fields = ("membership", "source_order")


@admin.register(MembershipInvoice)
class MembershipInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "membership",
        "stripe_invoice_id",
        "amount_paid",
        "amount_refunded",
        "status",
        "paid_at",
    )
    list_filter = ("status",)
    search_fields = ("membership__person__full_name", "stripe_invoice_id")
    autocomplete_fields = ("membership",)


@admin.register(MembershipPauseRequest)
class MembershipPauseRequestAdmin(admin.ModelAdmin):
    list_display = (
        "membership",
        "kind",
        "status",
        "requested_start_date",
        "requested_end_date",
        "decided_by",
        "decided_at",
    )
    list_filter = ("kind", "status")
    search_fields = ("membership__person__full_name", "membership__person__cpf")
    autocomplete_fields = ("membership", "decided_by")


@admin.register(MembershipTimelineEvent)
class MembershipTimelineEventAdmin(admin.ModelAdmin):
    list_display = ("person", "event_type", "membership", "actor", "actor_is_admin", "created_at")
    list_filter = ("event_type", "actor_is_admin")
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person", "membership", "actor")

    def has_add_permission(self, request):
        return False


@admin.register(PreRegistration)
class PreRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "registration_profile",
        "holder_cpf",
        "holder_email",
        "status",
        "selected_plan",
        "created_at",
    )
    list_filter = ("status", "registration_profile")
    search_fields = ("holder_cpf", "holder_email", "session_key")
    autocomplete_fields = ("selected_plan", "plan_order", "finalized_person")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "max_uses",
        "uses_count",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "description")


@admin.register(TeacherBankAccount)
class TeacherBankAccountAdmin(admin.ModelAdmin):
    list_display = ("person", "pix_key_type", "pix_key", "holder_name", "is_active")
    list_filter = ("pix_key_type", "is_active")
    search_fields = ("person__full_name", "person__cpf", "pix_key")
    autocomplete_fields = ("person",)


@admin.register(TeacherPayrollConfig)
class TeacherPayrollConfigAdmin(admin.ModelAdmin):
    list_display = ("person", "monthly_salary", "payment_day", "is_active")
    list_filter = ("is_active",)
    search_fields = ("person__full_name", "person__cpf")
    autocomplete_fields = ("person",)


@admin.register(TeacherPayout)
class TeacherPayoutAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "bank_account",
        "kind",
        "reference_month",
        "amount",
        "status",
        "scheduled_for",
        "paid_at",
    )
    list_filter = ("status", "kind")
    search_fields = ("person__full_name", "person__cpf", "asaas_transfer_id")
    autocomplete_fields = ("person", "bank_account", "approved_by")


@admin.register(AsaasWebhookEvent)
class AsaasWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "order", "payout", "created_at")
    list_filter = ("event_type",)
    search_fields = ("event_id", "order__person__full_name")
    autocomplete_fields = ("order", "payout")

    def has_add_permission(self, request):
        return False


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "order", "membership", "created_at")
    list_filter = ("event_type",)
    search_fields = ("event_id", "order__person__full_name")
    autocomplete_fields = ("order", "membership")

    def has_add_permission(self, request):
        return False


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
