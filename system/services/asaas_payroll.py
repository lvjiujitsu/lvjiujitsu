import logging
from datetime import date
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from system.models.asaas import (
    PayoutKind,
    PayoutStatus,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
)
from system.services import asaas_client
from system.services.payroll_rules import (
    calculate_monthly_payroll,
    render_payroll_summary,
)


logger = logging.getLogger(__name__)


class PayrollError(Exception):
    pass


def _first_of_month(reference_date):
    return reference_date.replace(day=1)


def _scheduled_date(reference_month, payment_day):
    last_valid = 28
    day = min(max(int(payment_day), 1), last_valid)
    return reference_month.replace(day=day)


@transaction.atomic
def schedule_monthly_payouts(*, today=None, dry_run=False):
    if today is None:
        today = timezone.localdate()
    reference_month = _first_of_month(today)
    configs = (
        TeacherPayrollConfig.objects.filter(is_active=True, payment_day=today.day)
        .select_related("person")
    )
    created = []
    for config in configs:
        calculation = calculate_monthly_payroll(
            config.person,
            reference_month=reference_month,
        )
        if calculation["total"] <= 0:
            continue
        try:
            bank = config.person.teacher_bank_account
        except TeacherBankAccount.DoesNotExist:
            logger.warning(
                "Professor %s sem conta bancária — pulando folha.", config.person.pk
            )
            continue
        if not bank.is_active:
            continue
        existing = TeacherPayout.objects.filter(
            person=config.person,
            reference_month=reference_month,
            kind=PayoutKind.PAYROLL,
        ).first()
        if existing is not None:
            continue
        if dry_run:
            created.append(config.person.pk)
            continue
        payout = TeacherPayout.objects.create(
            person=config.person,
            bank_account=bank,
            kind=PayoutKind.PAYROLL,
            reference_month=reference_month,
            amount=calculation["total"],
            status=PayoutStatus.PENDING,
            scheduled_for=_scheduled_date(reference_month, config.payment_day),
            approval_notes=render_payroll_summary(calculation),
        )
        created.append(payout.pk)
    return created


@transaction.atomic
def approve_payout(payout: TeacherPayout, *, admin_user, notes=""):
    if payout.status != PayoutStatus.PENDING:
        raise PayrollError(
            f"Pagamento em status '{payout.get_status_display()}' não pode ser aprovado."
        )
    payout.status = PayoutStatus.APPROVED
    payout.approved_by = admin_user
    payout.approved_at = timezone.now()
    payout.approval_notes = notes or ""
    payout.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "approval_notes",
            "updated_at",
        ]
    )
    return payout


@transaction.atomic
def refuse_payout(payout: TeacherPayout, *, admin_user, notes=""):
    if payout.status != PayoutStatus.PENDING:
        raise PayrollError(
            f"Pagamento em status '{payout.get_status_display()}' não pode ser recusado."
        )
    payout.status = PayoutStatus.REFUSED
    payout.approved_by = admin_user
    payout.approved_at = timezone.now()
    payout.approval_notes = notes or ""
    payout.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "approval_notes",
            "updated_at",
        ]
    )
    return payout


def dispatch_payout(payout: TeacherPayout):
    """Dispara o Transfer PIX via Asaas. Requer payout APPROVED."""
    if payout.status != PayoutStatus.APPROVED:
        raise PayrollError(
            "Só é possível disparar pagamentos aprovados."
        )
    bank = payout.bank_account
    try:
        transfer = asaas_client.create_transfer(
            value=payout.amount,
            pix_key=bank.pix_key,
            pix_key_type=bank.pix_key_type,
            description=f"Pagamento {payout.get_kind_display()} — {payout.person.full_name}",
            external_reference=f"payout-{payout.pk}",
        )
    except asaas_client.AsaasClientError as exc:
        payout.status = PayoutStatus.FAILED
        payout.failure_reason = str(exc)[:1000]
        payout.save(update_fields=["status", "failure_reason", "updated_at"])
        raise PayrollError(str(exc)) from exc

    transfer_id = transfer.get("id") if isinstance(transfer, dict) else None
    if not transfer_id:
        payout.status = PayoutStatus.FAILED
        payout.failure_reason = "Resposta Asaas sem id do transfer"
        payout.save(update_fields=["status", "failure_reason", "updated_at"])
        raise PayrollError("Resposta Asaas sem id do transfer.")

    payout.asaas_transfer_id = transfer_id
    payout.status = PayoutStatus.SENT
    payout.sent_at = timezone.now()
    payout.save(
        update_fields=[
            "asaas_transfer_id",
            "status",
            "sent_at",
            "updated_at",
        ]
    )
    return payout


def mark_payout_paid(payout: TeacherPayout):
    payout.status = PayoutStatus.PAID
    payout.paid_at = timezone.now()
    payout.save(update_fields=["status", "paid_at", "updated_at"])
    return payout


def compute_available_balance(person, *, reference_month=None):
    if reference_month is None:
        reference_month = _first_of_month(timezone.localdate())
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return Decimal("0"), Decimal("0"), Decimal("0")
    if not config.is_active:
        return Decimal("0"), config.monthly_salary, Decimal("0")

    calculation = calculate_monthly_payroll(person, reference_month=reference_month)
    base_total = calculation["total"]

    committed_statuses = (
        PayoutStatus.PENDING,
        PayoutStatus.APPROVED,
        PayoutStatus.SENT,
        PayoutStatus.PAID,
    )
    committed = (
        TeacherPayout.objects.filter(
            person=person,
            reference_month=reference_month,
            status__in=committed_statuses,
        )
        .aggregate(total=models.Sum("amount"))
    )
    committed_total = committed["total"] or Decimal("0")
    available = base_total - committed_total
    if available < 0:
        available = Decimal("0")
    return available, base_total, committed_total


@transaction.atomic
def request_withdrawal(person, amount, *, notes=""):
    amount = Decimal(amount)
    if amount <= 0:
        raise PayrollError("Valor do saque deve ser maior que zero.")
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        raise PayrollError("Professor sem configuração de folha.")
    if not config.is_active:
        raise PayrollError("Folha inativa — solicitações bloqueadas.")
    try:
        bank = person.teacher_bank_account
    except TeacherBankAccount.DoesNotExist:
        raise PayrollError("Cadastre uma chave PIX antes de solicitar saque.")
    if not bank.is_active:
        raise PayrollError("Conta bancária inativa.")

    reference_month = _first_of_month(timezone.localdate())
    available, _, _ = compute_available_balance(person, reference_month=reference_month)
    if amount > available:
        raise PayrollError(
            f"Valor solicitado (R$ {amount}) excede o saldo disponível (R$ {available})."
        )

    payout = TeacherPayout.objects.create(
        person=person,
        bank_account=bank,
        kind=PayoutKind.WITHDRAWAL,
        reference_month=reference_month,
        amount=amount,
        status=PayoutStatus.PENDING,
        approval_notes=notes or "",
    )
    return payout


def mark_payout_failed(payout: TeacherPayout, reason=""):
    payout.status = PayoutStatus.FAILED
    payout.failure_reason = (reason or "")[:1000]
    payout.save(update_fields=["status", "failure_reason", "updated_at"])
    return payout
