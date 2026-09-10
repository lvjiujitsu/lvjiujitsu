from django.contrib import admin

from system.business_rule.models import (
    AsaasWebhookEvent,
    Coupon,
    RegistrationOrder,
    RegistrationOrderItem,
    StripeWebhookEvent,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
    TrialAccessGrant,
)


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
