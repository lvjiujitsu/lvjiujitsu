import json
from django.db import transaction
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES
from system.business_rule.models.asaas import TeacherPayrollConfig
from system.business_rule.services.payroll_rules.constants import PAYROLL_METHOD_FIXED_MONTHLY, PAYROLL_METHOD_LABELS, PAYROLL_METHOD_PER_CLASS_ATTENDANCE, PAYROLL_METHOD_PER_STUDENT_FIXED, PAYROLL_METHOD_STUDENT_PERCENTAGE, PAYROLL_RULES_VERSION, PAYROLL_SCOPE_ALL, PAYROLL_SCOPE_CLASS_GROUP, PayrollRuleError, ZERO
from system.business_rule.services.payroll_rules.helpers import money, percentage


def encode_payroll_rules(rules):
    payload = {
        "version": PAYROLL_RULES_VERSION,
        "rules": [_normalize_rule(rule) for rule in rules],
    }
    return json.dumps(payload, sort_keys=True)


def decode_payroll_rules(raw_notes, *, strict=False):
    if not raw_notes:
        return {"version": PAYROLL_RULES_VERSION, "rules": []}
    try:
        payload = json.loads(raw_notes)
    except json.JSONDecodeError as exc:
        if strict:
            raise PayrollRuleError("JSON de repasse inválido.") from exc
        return {"version": PAYROLL_RULES_VERSION, "rules": [], "legacy_notes": raw_notes}
    if not isinstance(payload, dict) or "rules" not in payload:
        if strict:
            raise PayrollRuleError("Informe um objeto JSON com a chave rules.")
        return {"version": PAYROLL_RULES_VERSION, "rules": [], "legacy_notes": raw_notes}
    rules = payload.get("rules")
    if not isinstance(rules, list):
        if strict:
            raise PayrollRuleError("A chave rules deve ser uma lista.")
        rules = []
    return {
        "version": int(payload.get("version") or PAYROLL_RULES_VERSION),
        "rules": [_normalize_rule(rule) for rule in rules],
    }


def build_payroll_payload_from_form(cleaned_data):
    raw_rules = (cleaned_data.get("payroll_rules_json") or "").strip()
    if raw_rules:
        return decode_payroll_rules(raw_rules, strict=True)

    rules = []
    fixed = money(cleaned_data.get("payroll_fixed_monthly"))
    per_student = money(cleaned_data.get("payroll_per_student_amount"))
    percentage = percentage(cleaned_data.get("payroll_student_percentage"))
    per_class = money(cleaned_data.get("payroll_per_class_amount"))

    if fixed > ZERO:
        rules.append({"method": PAYROLL_METHOD_FIXED_MONTHLY, "amount": str(fixed)})
    if per_student > ZERO:
        rules.append({"method": PAYROLL_METHOD_PER_STUDENT_FIXED, "amount": str(per_student)})
    if percentage > ZERO:
        rules.append(
            {"method": PAYROLL_METHOD_STUDENT_PERCENTAGE, "percentage": str(percentage)}
        )
    if per_class > ZERO:
        rules.append(
            {"method": PAYROLL_METHOD_PER_CLASS_ATTENDANCE, "amount": str(per_class)}
        )
    return {"version": PAYROLL_RULES_VERSION, "rules": rules}


@transaction.atomic
def save_person_payroll_config(person, cleaned_data):
    enabled = bool(cleaned_data.get("payroll_enabled"))
    is_staff = person.has_type_code(*CLASS_STAFF_PERSON_TYPE_CODES)
    existing = _get_existing_config(person)

    if not is_staff:
        if existing is not None and existing.is_active:
            existing.is_active = False
            existing.save(update_fields=["is_active", "updated_at"])
        if enabled:
            raise PayrollRuleError("Repasse permitido apenas para Professor ou Administrativo.")
        return existing

    if not enabled:
        if existing is not None and existing.is_active:
            existing.is_active = False
            existing.save(update_fields=["is_active", "updated_at"])
        return existing

    payload = build_payroll_payload_from_form(cleaned_data)
    monthly_salary = money(cleaned_data.get("payroll_fixed_monthly"))
    if monthly_salary == ZERO:
        monthly_salary = _first_fixed_monthly_amount(payload["rules"])
    payment_day = int(cleaned_data.get("payroll_payment_day") or 28)
    payment_day = min(max(payment_day, 1), 28)

    config, _ = TeacherPayrollConfig.objects.update_or_create(
        person=person,
        defaults={
            "monthly_salary": monthly_salary,
            "payment_day": payment_day,
            "is_active": True,
            "notes": encode_payroll_rules(payload["rules"]),
        },
    )
    return config


def _get_existing_config(person):
    try:
        return person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return None


def get_payroll_form_initial(person):
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return {
            "payroll_enabled": False,
            "payroll_payment_day": 28,
            "payroll_fixed_monthly": ZERO,
            "payroll_per_student_amount": ZERO,
            "payroll_student_percentage": ZERO,
            "payroll_per_class_amount": ZERO,
            "payroll_rules_json": "",
        }

    payload = decode_payroll_rules(config.notes)
    initial = {
        "payroll_enabled": config.is_active,
        "payroll_payment_day": config.payment_day,
        "payroll_fixed_monthly": config.monthly_salary,
        "payroll_per_student_amount": ZERO,
        "payroll_student_percentage": ZERO,
        "payroll_per_class_amount": ZERO,
        "payroll_rules_json": config.notes if payload["rules"] else "",
    }
    for rule in payload["rules"]:
        if rule["scope"] != PAYROLL_SCOPE_ALL:
            continue
        if rule["method"] == PAYROLL_METHOD_PER_STUDENT_FIXED:
            initial["payroll_per_student_amount"] = money(rule["amount"])
        elif rule["method"] == PAYROLL_METHOD_STUDENT_PERCENTAGE:
            initial["payroll_student_percentage"] = percentage(rule["percentage"])
        elif rule["method"] == PAYROLL_METHOD_PER_CLASS_ATTENDANCE:
            initial["payroll_per_class_amount"] = money(rule["amount"])
    return initial


def format_payroll_rules(config):
    rules = get_effective_rules(config)
    summaries = []
    for rule in rules:
        method_label = PAYROLL_METHOD_LABELS.get(rule["method"], rule["method"])
        value = _rule_value_label(rule)
        scope = rule.get("class_group_id") or "todas as turmas"
        summaries.append(
            {
                "method": rule["method"],
                "method_label": method_label,
                "value": value,
                "scope": scope,
            }
        )
    if not summaries and config.monthly_salary == ZERO:
        summaries.append(
            {
                "method": PAYROLL_METHOD_FIXED_MONTHLY,
                "method_label": "Sem repasse",
                "value": "R$ 0,00",
                "scope": "todas as turmas",
            }
        )
    return summaries


def render_payroll_summary(calculation):
    return (
        f"Fechamento {calculation['reference_month'].strftime('%m/%Y')}: "
        f"fixo R$ {calculation['fixed_total']}, "
        f"alunos R$ {calculation['student_total']} "
        f"({calculation['student_count']} aluno(s)), "
        f"aulas R$ {calculation['class_total']} "
        f"({calculation['class_attendance_count']} presenca(s)), "
        f"retido R$ {calculation['held_total']}, "
        f"abatimentos R$ {calculation['refund_adjustment_total']}, "
        f"total R$ {calculation['total']}."
    )


def _normalize_rule(rule):
    if not isinstance(rule, dict):
        raise PayrollRuleError("Regra de repasse deve ser um objeto.")
    method = rule.get("method")
    if method not in PAYROLL_METHOD_LABELS:
        raise PayrollRuleError(f"Método de repasse inválido: {method}")
    normalized = {
        "method": method,
        "scope": rule.get("scope") or PAYROLL_SCOPE_ALL,
    }
    if normalized["scope"] not in (PAYROLL_SCOPE_ALL, PAYROLL_SCOPE_CLASS_GROUP):
        raise PayrollRuleError("Escopo de repasse inválido.")
    if normalized["scope"] == PAYROLL_SCOPE_CLASS_GROUP:
        class_group_id = rule.get("class_group_id")
        if not class_group_id:
            raise PayrollRuleError("Regra por turma exige class_group_id.")
        try:
            normalized["class_group_id"] = int(class_group_id)
        except (TypeError, ValueError):
            raise PayrollRuleError("class_group_id deve ser um número inteiro.")
    if method in (
        PAYROLL_METHOD_FIXED_MONTHLY,
        PAYROLL_METHOD_PER_STUDENT_FIXED,
        PAYROLL_METHOD_PER_CLASS_ATTENDANCE,
    ):
        normalized["amount"] = str(money(rule.get("amount")))
    if method == PAYROLL_METHOD_STUDENT_PERCENTAGE:
        normalized["percentage"] = str(percentage(rule.get("percentage")))
    return normalized


def get_effective_rules(config):
    payload = decode_payroll_rules(config.notes)
    rules = payload["rules"]
    if rules:
        return rules
    if config.monthly_salary != ZERO:
        return [
            {
                "method": PAYROLL_METHOD_FIXED_MONTHLY,
                "scope": PAYROLL_SCOPE_ALL,
                "amount": str(money(config.monthly_salary)),
            }
        ]
    return []


def _first_fixed_monthly_amount(rules):
    for rule in rules:
        if rule["method"] == PAYROLL_METHOD_FIXED_MONTHLY:
            return money(rule.get("amount"))
    return ZERO


def _rule_value_label(rule):
    if rule["method"] == PAYROLL_METHOD_STUDENT_PERCENTAGE:
        return f"{percentage(rule['percentage'])}%"
    return f"R$ {money(rule.get('amount'))}"
