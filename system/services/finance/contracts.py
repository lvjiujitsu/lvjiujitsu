from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import (
    AuditLog,
    CheckoutRequest,
    EnrollmentPause,
    FinancialBenefit,
    LocalSubscription,
    MonthlyInvoice,
    PaymentProof,
    StripeSubscriptionLink,
    StudentProfile,
    SubscriptionStudent,
)
from system.services.reports.audit import record_audit_log
from system.services.students.registry import create_or_update_identity, ensure_financial_responsible_role


@transaction.atomic
def create_local_subscription(
    *,
    plan,
    responsible_cpf,
    responsible_full_name,
    responsible_email,
    student_profiles,
    benefit=None,
    primary_student=None,
    status=LocalSubscription.STATUS_ACTIVE,
    notes="",
):
    if not student_profiles:
        raise ValidationError("Selecione ao menos um aluno para a assinatura.")
    responsible_user, _ = create_or_update_identity(
        cpf=responsible_cpf,
        full_name=responsible_full_name,
        email=responsible_email,
    )
    ensure_financial_responsible_role(responsible_user)
    subscription = LocalSubscription(
        plan=plan,
        responsible_user=responsible_user,
        benefit=benefit,
        status=status,
        notes=notes,
    )
    subscription.full_clean()
    subscription.save()
    for student in student_profiles:
        link = SubscriptionStudent(
            subscription=subscription,
            student=student,
            is_primary_student=bool(primary_student and student.id == primary_student.id),
        )
        link.full_clean()
        link.save()
        sync_student_operational_status(student)
    sync_subscription_status(subscription)
    return subscription


def calculate_subscription_discount(subscription, base_amount):
    if subscription.benefit is None:
        return Decimal("0.00")
    return subscription.benefit.calculate_discount(base_amount)


@transaction.atomic
def issue_monthly_invoice(*, subscription, reference_month, due_date, amount_gross=None):
    gross = amount_gross if amount_gross is not None else subscription.plan.base_price
    discount = calculate_subscription_discount(subscription, gross)
    invoice = MonthlyInvoice(
        subscription=subscription,
        reference_month=reference_month,
        due_date=due_date,
        amount_gross=gross,
        amount_discount=discount,
        amount_net=gross - discount,
    )
    invoice.full_clean()
    invoice.save()
    sync_subscription_status(subscription)
    return invoice


@transaction.atomic
def mark_invoice_paid(invoice, *, notes="", actor_user=None):
    invoice.status = MonthlyInvoice.STATUS_PAID
    invoice.paid_at = timezone.now()
    if notes:
        invoice.notes = notes
    invoice.save(update_fields=["status", "paid_at", "notes", "updated_at"])
    sync_subscription_status(invoice.subscription)
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="invoice_paid",
        actor_user=actor_user,
        target=invoice,
        metadata={"subscription_uuid": str(invoice.subscription.uuid), "notes": notes},
    )
    return invoice


@transaction.atomic
def mark_invoice_overdue(invoice, *, notes="", actor_user=None):
    invoice.status = MonthlyInvoice.STATUS_OVERDUE
    if notes:
        invoice.notes = notes
    invoice.save(update_fields=["status", "notes", "updated_at"])
    sync_subscription_status(invoice.subscription)
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="invoice_overdue",
        actor_user=actor_user,
        target=invoice,
        metadata={"subscription_uuid": str(invoice.subscription.uuid), "notes": notes},
    )
    return invoice


@transaction.atomic
def create_enrollment_pause(*, student, subscription, reason, start_date, expected_return_date, notes="", actor_user=None):
    pause = EnrollmentPause(
        student=student,
        subscription=subscription,
        reason=reason,
        start_date=start_date,
        expected_return_date=expected_return_date,
        notes=notes,
        is_active=True,
    )
    pause.full_clean()
    pause.save()
    sync_student_operational_status(student)
    if subscription:
        sync_subscription_status(subscription)
        transaction.on_commit(
            lambda: _sync_pause_collection_after_commit(subscription=subscription, pause=pause)
        )
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="enrollment_paused",
        actor_user=actor_user,
        target=pause,
        metadata={"student_uuid": str(student.uuid), "subscription_uuid": str(subscription.uuid) if subscription else ""},
    )
    return pause


@transaction.atomic
def resume_enrollment_pause(pause, *, end_date=None, notes="", actor_user=None):
    pause.end_date = end_date or timezone.localdate()
    pause.is_active = False
    if notes:
        pause.notes = notes
    pause.full_clean()
    pause.save()
    sync_student_operational_status(pause.student)
    if pause.subscription:
        sync_subscription_status(pause.subscription)
        transaction.on_commit(
            lambda: _resume_pause_collection_after_commit(subscription=pause.subscription)
        )
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="enrollment_resumed",
        actor_user=actor_user,
        target=pause,
        metadata={"student_uuid": str(pause.student.uuid), "subscription_uuid": str(pause.subscription.uuid) if pause.subscription else ""},
    )
    return pause


@transaction.atomic
def upload_payment_proof(*, invoice, uploaded_by, uploaded_file):
    if invoice.status in {MonthlyInvoice.STATUS_PAID, MonthlyInvoice.STATUS_CANCELLED}:
        raise ValidationError("Nao e permitido enviar comprovante para uma fatura encerrada.")
    proof = PaymentProof(
        invoice=invoice,
        uploaded_by=uploaded_by,
        file=uploaded_file,
        original_filename=uploaded_file.name,
    )
    proof.full_clean()
    proof.save()
    invoice.status = MonthlyInvoice.STATUS_UNDER_REVIEW
    invoice.save(update_fields=["status", "updated_at"])
    sync_subscription_status(invoice.subscription)
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="payment_proof_uploaded",
        actor_user=uploaded_by,
        target=proof,
        metadata={"invoice_uuid": str(invoice.uuid), "original_filename": uploaded_file.name},
    )
    return proof


@transaction.atomic
def review_payment_proof(*, proof, reviewer, approve, review_notes=""):
    if proof.status != PaymentProof.STATUS_UNDER_REVIEW:
        raise ValidationError("Este comprovante ja foi revisado.")
    proof.reviewed_by = reviewer
    proof.reviewed_at = timezone.now()
    proof.review_notes = review_notes
    proof.status = PaymentProof.STATUS_APPROVED if approve else PaymentProof.STATUS_REJECTED
    proof.save(update_fields=["reviewed_by", "reviewed_at", "review_notes", "status", "updated_at"])
    if approve:
        mark_invoice_paid(proof.invoice, notes=review_notes, actor_user=reviewer)
    else:
        proof.invoice.status = _resolve_open_invoice_status(proof.invoice)
        proof.invoice.notes = review_notes
        proof.invoice.save(update_fields=["status", "notes", "updated_at"])
        sync_subscription_status(proof.invoice.subscription)
    record_audit_log(
        category=AuditLog.CATEGORY_FINANCE,
        action="payment_proof_reviewed",
        actor_user=reviewer,
        target=proof,
        metadata={"approve": approve, "invoice_uuid": str(proof.invoice.uuid)},
    )
    return proof


def sync_subscription_status(subscription):
    if subscription.status == LocalSubscription.STATUS_CANCELLED:
        _sync_covered_students(subscription)
        return subscription
    new_status = _resolve_subscription_status(subscription)
    if subscription.status != new_status:
        subscription.status = new_status
        subscription.save(update_fields=["status", "updated_at"])
    _sync_covered_students(subscription)
    return subscription


def sync_student_operational_status(student):
    active_pauses = student.enrollment_pauses.filter(is_active=True).exists()
    active_links = student.subscription_links.filter(is_active=True).select_related("subscription", "subscription__plan")
    if active_pauses:
        student.operational_status = StudentProfile.STATUS_PAUSED
    elif any(link.subscription.status == LocalSubscription.STATUS_BLOCKED for link in active_links):
        student.operational_status = StudentProfile.STATUS_BLOCKED
    elif any(link.subscription.status == LocalSubscription.STATUS_PENDING_FINANCIAL for link in active_links):
        student.operational_status = StudentProfile.STATUS_PENDING_FINANCIAL
    elif any(link.subscription.status == LocalSubscription.STATUS_ACTIVE for link in active_links):
        student.operational_status = StudentProfile.STATUS_ACTIVE
    elif student.is_active:
        student.operational_status = StudentProfile.STATUS_PENDING
    else:
        student.operational_status = StudentProfile.STATUS_INACTIVE
    student.save(update_fields=["operational_status", "updated_at"])
    return student


def _sync_covered_students(subscription):
    for link in subscription.covered_students.select_related("student"):
        sync_student_operational_status(link.student)


def _resolve_open_invoice_status(invoice):
    if invoice.due_date < timezone.localdate():
        return MonthlyInvoice.STATUS_OVERDUE
    return MonthlyInvoice.STATUS_OPEN


def _resolve_subscription_status(subscription):
    if subscription.pauses.filter(is_active=True).exists():
        return LocalSubscription.STATUS_PAUSED
    if _has_local_financial_pending(subscription):
        return LocalSubscription.STATUS_PENDING_FINANCIAL
    if _has_checkout_in_progress(subscription):
        return LocalSubscription.STATUS_PENDING_FINANCIAL
    if _has_external_financial_pending(subscription):
        return LocalSubscription.STATUS_PENDING_FINANCIAL
    return LocalSubscription.STATUS_ACTIVE


def _has_local_financial_pending(subscription):
    pending_statuses = (
        MonthlyInvoice.STATUS_OVERDUE,
        MonthlyInvoice.STATUS_UNDER_REVIEW,
    )
    if not subscription.plan.blocks_checkin_on_overdue:
        return False
    return subscription.invoices.filter(status__in=pending_statuses).exists()


def _has_checkout_in_progress(subscription):
    pending_statuses = (
        CheckoutRequest.STATUS_CREATED,
        CheckoutRequest.STATUS_SESSION_CREATED,
    )
    return subscription.checkout_requests.filter(status__in=pending_statuses).exists()


def _has_external_financial_pending(subscription):
    external_link = getattr(subscription, "stripe_subscription_link", None)
    if external_link is None:
        return False
    return external_link.stripe_status in {
        StripeSubscriptionLink.STATUS_PENDING,
        StripeSubscriptionLink.STATUS_PAST_DUE,
    }


def _sync_pause_collection_after_commit(*, subscription, pause):
    try:
        from system.services.payments import pause_linked_subscription_collection

        pause_linked_subscription_collection(local_subscription=subscription, pause=pause)
    except Exception as exc:
        _store_subscription_sync_error(subscription=subscription, action="pause_collection", error=exc)


def _resume_pause_collection_after_commit(*, subscription):
    try:
        from system.services.payments import resume_linked_subscription_collection

        resume_linked_subscription_collection(local_subscription=subscription)
    except Exception as exc:
        _store_subscription_sync_error(subscription=subscription, action="resume_collection", error=exc)


def _store_subscription_sync_error(*, subscription, action, error):
    external_link = getattr(subscription, "stripe_subscription_link", None)
    if external_link is None:
        return
    payload = dict(external_link.latest_payload or {})
    payload["sync_error"] = {
        "action": action,
        "message": str(error),
        "recorded_at": timezone.now().isoformat(),
    }
    external_link.latest_payload = payload
    external_link.save(update_fields=["latest_payload", "updated_at"])
