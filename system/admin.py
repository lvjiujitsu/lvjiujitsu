from django.contrib import admin

from system.models import (
    AcademyConfiguration,
    BulkCommunication,
    CommunicationDelivery,
    DocumentRecord,
    AttendanceAttempt,
    AttendanceQrToken,
    AuthenticationEvent,
    AuditLog,
    ClassDiscipline,
    ClassGroup,
    ClassSession,
    ClassReservation,
    ConsentAcceptance,
    ConsentTerm,
    DashboardDailySnapshot,
    EmergencyRecord,
    EnrollmentPause,
    ExportRequest,
    FinancialBenefit,
    FinancialPlan,
    CashMovement,
    CashSession,
    GraduationExam,
    GraduationExamParticipation,
    GraduationHistory,
    GraduationRule,
    GuardianRelationship,
    IbjjfBelt,
    InstructorProfile,
    Lead,
    LocalSubscription,
    LgpdRequest,
    MonthlyInvoice,
    PasswordActionToken,
    PaymentProof,
    PdvProduct,
    PdvSale,
    PdvSaleItem,
    PhysicalAttendance,
    PublicClassSchedule,
    PublicPlan,
    NoticeBoardMessage,
    StripeCustomerLink,
    StripePlanPriceMap,
    StripeSubscriptionLink,
    CsvExportControl,
    SensitiveAccessLog,
    StudentProfile,
    SubscriptionStudent,
    SystemRole,
    SystemUser,
    SystemUserRole,
    TrialClassRequest,
    WebhookProcessing,
    CheckoutRequest,
)


@admin.register(SystemUser)
class SystemUserAdmin(admin.ModelAdmin):
    list_display = ("cpf", "full_name", "email", "is_active", "is_staff")
    search_fields = ("cpf", "full_name", "email")
    list_filter = ("is_active", "is_staff", "is_superuser")


@admin.register(SystemRole)
class SystemRoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(SystemUserRole)
class SystemUserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    search_fields = ("user__cpf", "role__code")


@admin.register(AuthenticationEvent)
class AuthenticationEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "identifier", "actor_user", "created_at")
    search_fields = ("identifier", "actor_user__cpf")
    list_filter = ("event_type",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("category", "action", "status", "actor_user", "target_model", "created_at")
    list_filter = ("category", "status")
    search_fields = ("action", "actor_user__cpf", "target_model")


@admin.register(CsvExportControl)
class CsvExportControlAdmin(admin.ModelAdmin):
    list_display = ("name", "control_file_path", "is_active", "last_validation_status", "last_validated_at")
    list_filter = ("is_active", "last_validation_status")
    search_fields = ("name", "control_file_path")


@admin.register(ExportRequest)
class ExportRequestAdmin(admin.ModelAdmin):
    list_display = ("report_type", "status", "requested_by", "file_name", "row_count", "started_at", "finished_at")
    list_filter = ("report_type", "status")
    search_fields = ("requested_by__cpf", "file_name", "error_message")


@admin.register(PasswordActionToken)
class PasswordActionTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "expires_at", "used_at")
    search_fields = ("user__cpf", "token")


@admin.register(AcademyConfiguration)
class AcademyConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "academy_name",
        "dependent_credential_min_age",
        "qr_code_ttl_seconds",
        "trial_class_minimum_notice_hours",
    )

    def has_add_permission(self, request):
        return not AcademyConfiguration.objects.exists()


@admin.register(PublicPlan)
class PublicPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "billing_cycle", "is_active", "is_featured", "display_order")
    list_filter = ("is_active", "is_featured", "billing_cycle")
    search_fields = ("name", "summary")


@admin.register(PublicClassSchedule)
class PublicClassScheduleAdmin(admin.ModelAdmin):
    list_display = ("class_level", "weekday", "start_time", "end_time", "instructor_name", "is_active")
    list_filter = ("weekday", "is_active")
    search_fields = ("class_level", "instructor_name")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "source", "status", "email", "phone", "created_at")
    list_filter = ("source", "status")
    search_fields = ("full_name", "email", "phone")


@admin.register(TrialClassRequest)
class TrialClassRequestAdmin(admin.ModelAdmin):
    list_display = ("lead", "preferred_date", "preferred_period", "status", "created_at")
    list_filter = ("preferred_period", "status")
    search_fields = ("lead__full_name", "lead__email", "lead__phone")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_type", "operational_status", "self_service_access", "is_active")
    list_filter = ("student_type", "operational_status", "self_service_access", "is_active")
    search_fields = ("user__cpf", "user__full_name", "contact_phone")


@admin.register(GuardianRelationship)
class GuardianRelationshipAdmin(admin.ModelAdmin):
    list_display = ("responsible_user", "student", "relationship_type", "is_primary", "end_date")
    list_filter = ("relationship_type", "is_primary", "is_financial_responsible")
    search_fields = ("responsible_user__cpf", "responsible_user__full_name", "student__user__cpf")


@admin.register(EmergencyRecord)
class EmergencyRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "emergency_contact_name", "emergency_contact_phone")
    search_fields = ("student__user__cpf", "student__user__full_name", "emergency_contact_name")


@admin.register(ConsentTerm)
class ConsentTermAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "version", "audience", "is_active", "required_for_onboarding")
    list_filter = ("audience", "is_active", "required_for_onboarding")
    search_fields = ("code", "title")


@admin.register(ConsentAcceptance)
class ConsentAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("user", "term", "context", "accepted_at")
    list_filter = ("context", "term__code")
    search_fields = ("user__cpf", "user__full_name", "term__title")


@admin.register(DocumentRecord)
class DocumentRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "owner_user", "student", "subscription", "issued_at", "is_visible_to_owner")
    list_filter = ("document_type", "is_visible_to_owner")
    search_fields = ("title", "owner_user__cpf", "owner_user__full_name", "student__user__cpf")


@admin.register(LgpdRequest)
class LgpdRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "request_type", "status", "confirmed_at", "created_at", "resolved_at")
    list_filter = ("request_type", "status")
    search_fields = ("user__cpf", "user__full_name")


@admin.register(SensitiveAccessLog)
class SensitiveAccessLogAdmin(admin.ModelAdmin):
    list_display = ("actor_user", "student", "access_type", "created_at")
    list_filter = ("access_type",)
    search_fields = ("actor_user__cpf", "student__user__cpf", "student__user__full_name")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "belt_rank", "is_active")
    list_filter = ("is_active", "belt_rank")
    search_fields = ("user__cpf", "user__full_name")


@admin.register(IbjjfBelt)
class IbjjfBeltAdmin(admin.ModelAdmin):
    list_display = ("display_order", "name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(ClassDiscipline)
class ClassDisciplineAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "modality", "instructor", "weekday", "start_time", "capacity", "is_active")
    list_filter = ("weekday", "reservation_required", "is_active")
    search_fields = ("name", "modality__name", "instructor__user__full_name")


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("class_group", "starts_at", "ends_at", "status", "opened_by", "closed_by")
    list_filter = ("status", "class_group__modality")
    search_fields = ("class_group__name", "class_group__modality__name")


@admin.register(ClassReservation)
class ClassReservationAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "created_at")
    list_filter = ("status", "session__class_group")
    search_fields = ("student__user__cpf", "student__user__full_name")


@admin.register(AttendanceQrToken)
class AttendanceQrTokenAdmin(admin.ModelAdmin):
    list_display = ("session", "expires_at", "generated_by", "created_at")
    search_fields = ("session__class_group__name", "token")


@admin.register(PhysicalAttendance)
class PhysicalAttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "checkin_method", "checked_in_at", "recorded_by")
    list_filter = ("checkin_method", "session__class_group")
    search_fields = ("student__user__cpf", "student__user__full_name")


@admin.register(AttendanceAttempt)
class AttendanceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "reason", "created_at")
    list_filter = ("status",)
    search_fields = ("student__user__cpf", "reason", "token_value")


@admin.register(FinancialPlan)
class FinancialPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "billing_cycle", "base_price", "is_active", "active_from", "active_until")
    list_filter = ("billing_cycle", "is_active")
    search_fields = ("name", "slug")


@admin.register(FinancialBenefit)
class FinancialBenefitAdmin(admin.ModelAdmin):
    list_display = ("name", "benefit_type", "value_type", "value", "is_active")
    list_filter = ("benefit_type", "value_type", "is_active")
    search_fields = ("name",)


class SubscriptionStudentInline(admin.TabularInline):
    model = SubscriptionStudent
    extra = 0


@admin.register(LocalSubscription)
class LocalSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("plan", "responsible_user", "status", "start_date", "end_date")
    list_filter = ("status", "plan")
    search_fields = ("responsible_user__cpf", "responsible_user__full_name", "plan__name")
    inlines = [SubscriptionStudentInline]


@admin.register(MonthlyInvoice)
class MonthlyInvoiceAdmin(admin.ModelAdmin):
    list_display = ("subscription", "reference_month", "due_date", "amount_net", "status", "paid_at")
    list_filter = ("status",)
    search_fields = ("subscription__responsible_user__cpf", "stripe_invoice_id")


@admin.register(EnrollmentPause)
class EnrollmentPauseAdmin(admin.ModelAdmin):
    list_display = ("student", "subscription", "start_date", "expected_return_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("student__user__cpf", "student__user__full_name", "reason")


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ("invoice", "uploaded_by", "status", "submitted_at", "reviewed_by")
    list_filter = ("status",)
    search_fields = ("invoice__subscription__responsible_user__cpf", "original_filename")


@admin.register(PdvProduct)
class PdvProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit_price", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("sku", "name")


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ("operator_user", "status", "opening_balance", "expected_cash_total", "counted_cash_total", "opened_at", "closed_at")
    list_filter = ("status",)
    search_fields = ("operator_user__cpf", "operator_user__full_name")


@admin.register(PdvSale)
class PdvSaleAdmin(admin.ModelAdmin):
    list_display = ("receipt_code", "cash_session", "operator_user", "payment_method", "total_amount", "completed_at")
    list_filter = ("payment_method", "status")
    search_fields = ("receipt_code", "operator_user__cpf", "customer_name_snapshot")


@admin.register(PdvSaleItem)
class PdvSaleItemAdmin(admin.ModelAdmin):
    list_display = ("sale", "product_name_snapshot", "quantity", "line_total")
    search_fields = ("sale__receipt_code", "product_name_snapshot")


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ("cash_session", "movement_type", "direction", "payment_method", "amount", "created_at")
    list_filter = ("movement_type", "direction", "payment_method")
    search_fields = ("cash_session__operator_user__cpf", "description", "sale__receipt_code")


@admin.register(DashboardDailySnapshot)
class DashboardDailySnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot_date",
        "paid_revenue_total",
        "attendances_count",
        "pending_financial_students_count",
        "overdue_invoices_count",
        "requested_trial_classes_count",
    )
    search_fields = ("snapshot_date",)


@admin.register(NoticeBoardMessage)
class NoticeBoardMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "starts_at", "ends_at", "is_active", "created_by")
    list_filter = ("audience", "is_active")
    search_fields = ("title", "body", "created_by__full_name")


@admin.register(BulkCommunication)
class BulkCommunicationAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "channel", "status", "queued_at", "dispatched_at", "created_by")
    list_filter = ("audience", "channel", "status")
    search_fields = ("title", "message", "created_by__full_name")


@admin.register(CommunicationDelivery)
class CommunicationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("communication", "recipient_user", "channel", "status", "delivered_at")
    list_filter = ("channel", "status")
    search_fields = ("communication__title", "recipient_user__cpf", "recipient_user__full_name")


@admin.register(GraduationRule)
class GraduationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "scope",
        "discipline",
        "current_belt",
        "current_degree",
        "target_belt",
        "target_degree",
        "minimum_active_days",
        "minimum_attendances",
        "is_active",
    )
    list_filter = ("scope", "discipline", "is_active")
    search_fields = ("current_belt__name", "target_belt__name", "criteria_notes")


@admin.register(GraduationHistory)
class GraduationHistoryAdmin(admin.ModelAdmin):
    list_display = ("student", "belt_rank", "degree_level", "started_on", "ended_on", "is_current", "event_type")
    list_filter = ("belt_rank", "degree_level", "is_current", "event_type")
    search_fields = ("student__user__cpf", "student__user__full_name")


@admin.register(GraduationExam)
class GraduationExamAdmin(admin.ModelAdmin):
    list_display = ("title", "scheduled_for", "status", "discipline", "class_group", "created_by")
    list_filter = ("status", "discipline")
    search_fields = ("title", "class_group__name", "created_by__full_name")


@admin.register(GraduationExamParticipation)
class GraduationExamParticipationAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "current_belt", "suggested_belt", "status", "certificate_code")
    list_filter = ("status", "current_belt", "suggested_belt")
    search_fields = ("student__user__cpf", "student__user__full_name", "certificate_code")


@admin.register(StripeCustomerLink)
class StripeCustomerLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_customer_id", "livemode", "last_synced_at")
    list_filter = ("livemode",)
    search_fields = ("user__cpf", "user__full_name", "stripe_customer_id")


@admin.register(StripePlanPriceMap)
class StripePlanPriceMapAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "stripe_price_id",
        "currency",
        "amount",
        "recurring_interval",
        "is_current",
        "is_legacy",
        "is_active",
    )
    list_filter = ("currency", "recurring_interval", "is_current", "is_legacy", "is_active", "livemode")
    search_fields = ("plan__name", "stripe_price_id", "stripe_product_id", "product_name", "lookup_key")


@admin.register(StripeSubscriptionLink)
class StripeSubscriptionLinkAdmin(admin.ModelAdmin):
    list_display = ("local_subscription", "stripe_subscription_id", "stripe_status", "livemode", "current_period_end")
    list_filter = ("stripe_status", "livemode")
    search_fields = ("local_subscription__responsible_user__cpf", "stripe_subscription_id")


@admin.register(CheckoutRequest)
class CheckoutRequestAdmin(admin.ModelAdmin):
    list_display = ("local_subscription", "requester", "status", "stripe_checkout_session_id", "completed_at")
    list_filter = ("status",)
    search_fields = ("local_subscription__responsible_user__cpf", "stripe_checkout_session_id", "stripe_subscription_id")


@admin.register(WebhookProcessing)
class WebhookProcessingAdmin(admin.ModelAdmin):
    list_display = ("stripe_event_id", "event_type", "status", "signature_verified", "processing_attempts", "processed_at")
    list_filter = ("status", "signature_verified", "livemode")
    search_fields = ("stripe_event_id", "event_type")
