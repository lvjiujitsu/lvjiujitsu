from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import ClassCatalogRequest, ClassCatalogRequestStatus, TeacherPayrollConfig
from system.services.payroll_rules import PayrollRuleError, save_person_payroll_config

MONETARY_ARRANGEMENTS = {
    "paid_fixed",
    "paid_per_student",
    "paid_mixed",
}


def can_activate_payroll_from_request(catalog_request):
    if catalog_request.status != ClassCatalogRequestStatus.APPROVED:
        return False
    if catalog_request.created_teacher_id is None:
        return False
    payout = (catalog_request.payload or {}).get("payout") or {}
    if payout.get("financial_arrangement") not in MONETARY_ARRANGEMENTS:
        return False
    existing = (
        TeacherPayrollConfig.objects.filter(
            person_id=catalog_request.created_teacher_id,
            is_active=True,
        ).first()
    )
    return existing is None


def build_payroll_activation_initial(catalog_request):
    payout = (catalog_request.payload or {}).get("payout") or {}
    arrangement = payout.get("financial_arrangement") or ""
    initial = {
        "payroll_payment_day": 5,
        "payroll_activation_notes": "",
    }
    if arrangement in {"paid_fixed", "paid_mixed"}:
        initial["payroll_fixed_monthly"] = payout.get("fixed_amount") or ""
    if arrangement in {"paid_per_student", "paid_mixed"}:
        initial["payroll_student_percentage"] = payout.get("student_percentage") or ""
    return initial


@transaction.atomic
def activate_payroll_from_class_request(
    catalog_request,
    *,
    activated_by,
    payment_day,
    decision_notes="",
):
    if catalog_request.status != ClassCatalogRequestStatus.APPROVED:
        raise ValidationError("Ative o repasse somente após aprovar a solicitação.")
    teacher = catalog_request.created_teacher
    if teacher is None:
        raise ValidationError("A solicitação ainda não possui professor aprovado.")
    if not can_activate_payroll_from_request(catalog_request):
        raise ValidationError("Repasse já está ativo para este professor.")

    payout = (catalog_request.payload or {}).get("payout") or {}
    arrangement = payout.get("financial_arrangement") or ""
    if arrangement not in MONETARY_ARRANGEMENTS:
        raise ValidationError("Esta solicitação não possui condição financeira monetária.")

    cleaned_data = {
        "payroll_enabled": True,
        "payroll_payment_day": payment_day,
        "payroll_fixed_monthly": "",
        "payroll_student_percentage": "",
        "payroll_per_student_amount": "",
        "payroll_per_class_amount": "",
        "payroll_rules_json": "",
    }
    if arrangement in {"paid_fixed", "paid_mixed"}:
        cleaned_data["payroll_fixed_monthly"] = payout.get("fixed_amount") or ""
    if arrangement in {"paid_per_student", "paid_mixed"}:
        cleaned_data["payroll_student_percentage"] = payout.get("student_percentage") or ""

    try:
        payment_day_value = int(payment_day)
    except (TypeError, ValueError) as error:
        raise ValidationError("Informe um dia de pagamento válido.") from error
    if payment_day_value < 1 or payment_day_value > 28:
        raise ValidationError("O dia de pagamento deve ficar entre 1 e 28.")

    cleaned_data["payroll_payment_day"] = payment_day_value
    if not _has_monetary_value(cleaned_data):
        raise ValidationError("Informe valor fixo ou percentual para ativar o repasse.")

    try:
        config = save_person_payroll_config(teacher, cleaned_data)
    except PayrollRuleError as error:
        raise ValidationError(str(error)) from error

    payload = dict(catalog_request.payload or {})
    payload["payroll_activation"] = {
        "activated_at": timezone.now().isoformat(),
        "activated_by_id": getattr(activated_by, "pk", None),
        "payment_day": payment_day_value,
        "financial_arrangement": arrangement,
        "notes": (decision_notes or "").strip(),
    }
    catalog_request.payload = payload
    catalog_request.save(update_fields=("payload", "updated_at"))
    return config


def _has_monetary_value(cleaned_data):
    for field_name in (
        "payroll_fixed_monthly",
        "payroll_student_percentage",
        "payroll_per_student_amount",
        "payroll_per_class_amount",
    ):
        raw_value = cleaned_data.get(field_name)
        if not raw_value:
            continue
        try:
            if Decimal(str(raw_value).replace(",", ".")) > 0:
                return True
        except (InvalidOperation, ValueError):
            continue
    return False
