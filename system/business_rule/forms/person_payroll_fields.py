from system.business_rule.services.payroll_rules import PayrollRuleError
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES
from system.business_rule.services.payroll_rules import build_payroll_payload_from_form


class PersonPayrollMixin:
    @property
    def payroll_fields(self):
        if not self.show_payroll_fields:
            return []
        return self._bound_fields(self.payroll_field_names)

    def _clean_payroll_config(self, cleaned_data):
        person_type = cleaned_data.get("person_type")
        payroll_enabled = bool(cleaned_data.get("payroll_enabled"))
        has_payroll_values = any(
            cleaned_data.get(field_name)
            for field_name in (
                "payroll_fixed_monthly",
                "payroll_per_student_amount",
                "payroll_student_percentage",
                "payroll_per_class_amount",
                "payroll_rules_json",
            )
        )
        is_staff = bool(
            person_type and person_type.code in CLASS_STAFF_PERSON_TYPE_CODES
        )
        if (payroll_enabled or has_payroll_values) and not is_staff:
            self.add_error(
                "payroll_enabled",
                "Repasse permitido apenas para Professor ou Administrativo.",
            )
            return
        if not payroll_enabled:
            return
        if not cleaned_data.get("payroll_payment_day"):
            cleaned_data["payroll_payment_day"] = 28
        try:

            build_payroll_payload_from_form(cleaned_data)
        except PayrollRuleError as exc:
            self.add_error("payroll_rules_json", str(exc))
