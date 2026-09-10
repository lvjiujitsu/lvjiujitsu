from django.contrib import admin, messages

from system.business_rule.models import (
    Membership,
    MembershipCredit,
    MembershipInvoice,
    MembershipPauseRequest,
    MembershipTimelineEvent,
    PlanPrice,
    PlanTier,
    PreRegistration,
    SubscriptionPlan,
)


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
