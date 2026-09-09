import json
from decimal import Decimal, InvalidOperation

from django import forms

from system.business_rule.constants import OperationalRoleCode, PersonTypeCode, RegistrationProfile
from system.business_rule.services.class_overview import resolve_class_group_selection


TEACHER_ASSIGNMENT_EXISTING = "existing"
TEACHER_ASSIGNMENT_PROPOSE = "propose"
TEACHER_ASSIGNMENT_MODES = {TEACHER_ASSIGNMENT_EXISTING, TEACHER_ASSIGNMENT_PROPOSE}

OPERATIONAL_FINANCIAL_PAYS_MONTHLY = "pays_monthly"
OPERATIONAL_FINANCIAL_BARTER = "barter"
OPERATIONAL_FINANCIAL_VOLUNTEER = "volunteer"
OPERATIONAL_FINANCIAL_PAID_FIXED = "paid_fixed"
OPERATIONAL_FINANCIAL_PAID_PER_STUDENT = "paid_per_student"
OPERATIONAL_FINANCIAL_PAID_MIXED = "paid_mixed"
OPERATIONAL_FINANCIAL_ARRANGEMENTS = {
    OPERATIONAL_FINANCIAL_PAYS_MONTHLY,
    OPERATIONAL_FINANCIAL_BARTER,
    OPERATIONAL_FINANCIAL_VOLUNTEER,
    OPERATIONAL_FINANCIAL_PAID_FIXED,
    OPERATIONAL_FINANCIAL_PAID_PER_STUDENT,
    OPERATIONAL_FINANCIAL_PAID_MIXED,
}
PAID_OPERATIONAL_FINANCIAL_ARRANGEMENTS = {
    OPERATIONAL_FINANCIAL_PAID_FIXED,
    OPERATIONAL_FINANCIAL_PAID_PER_STUDENT,
    OPERATIONAL_FINANCIAL_PAID_MIXED,
}
PAYOUT_METHODS = {"none", "pix", "bank"}
WEEKDAY_VALUES = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
ADMINISTRATIVE_ROLE_CODES = {
    OperationalRoleCode.ACADEMY_MANAGER,
    OperationalRoleCode.CLASS_ASSISTANT,
    OperationalRoleCode.PEOPLE_SUPPORT,
    OperationalRoleCode.FINANCIAL_OPERATOR,
    OperationalRoleCode.STOCK_OPERATOR,
    OperationalRoleCode.GRADUATION_OPERATOR,
}


class OperationalRegistrationFieldsMixin(forms.Form):

    operational_training_intent = forms.CharField(required=False, max_length=40)
    operational_payment_condition = forms.CharField(required=False, max_length=40)
    operational_financial_arrangement = forms.CharField(required=False, max_length=40)
    operational_compensation_preference = forms.CharField(required=False, max_length=40)
    operational_requested_roles_payload = forms.CharField(required=False, widget=forms.HiddenInput)
    operational_payout_method = forms.CharField(required=False, max_length=40)
    operational_pix_key_type = forms.CharField(required=False, max_length=40)
    operational_pix_key = forms.CharField(required=False, max_length=255)
    operational_bank_details = forms.CharField(required=False)
    operational_fixed_amount = forms.CharField(required=False, max_length=40)
    operational_student_percentage = forms.CharField(required=False, max_length=40)
    operational_compensation_notes = forms.CharField(required=False)
    teacher_assignment_mode = forms.CharField(required=False, max_length=40)
    teacher_existing_class_group = forms.CharField(required=False, max_length=80)
    teacher_existing_class_groups_payload = forms.CharField(required=False, widget=forms.HiddenInput)
    teacher_proposed_schedule_payload = forms.CharField(required=False, widget=forms.HiddenInput)

    def _clean_operational_registration(self, profile):
        if profile != RegistrationProfile.OTHER:
            self._clear_operational_fields()
            return

        other_type_code = self.cleaned_data.get("other_type_code") or ""
        if other_type_code == PersonTypeCode.INSTRUCTOR:
            self._clean_teacher_operational_registration()
        elif other_type_code == PersonTypeCode.ADMINISTRATIVE_ASSISTANT:
            self._clean_administrative_operational_registration()
        else:
            self._clear_operational_fields()
            return

        self._clean_operational_finance()

    def _clear_operational_fields(self):
        for field_name in (
            "operational_training_intent",
            "operational_payment_condition",
            "operational_financial_arrangement",
            "operational_compensation_preference",
            "operational_requested_roles_payload",
            "operational_payout_method",
            "operational_pix_key_type",
            "operational_pix_key",
            "operational_bank_details",
            "operational_fixed_amount",
            "operational_student_percentage",
            "operational_compensation_notes",
            "teacher_assignment_mode",
            "teacher_existing_class_group",
            "teacher_existing_class_groups_payload",
            "teacher_proposed_schedule_payload",
        ):
            self.cleaned_data[field_name] = ""

    def _clean_administrative_operational_registration(self):
        role_codes = self._parse_json_list(
            self.cleaned_data.get("operational_requested_roles_payload"),
            "operational_requested_roles_payload",
            "Selecione ao menos uma área administrativa.",
        )
        role_codes = [str(code) for code in role_codes if str(code)]
        invalid_codes = [code for code in role_codes if code not in ADMINISTRATIVE_ROLE_CODES]
        if invalid_codes:
            self.add_error(
                "operational_requested_roles_payload",
                "Selecione apenas áreas administrativas válidas.",
            )
            return
        if not role_codes:
            self.add_error(
                "operational_requested_roles_payload",
                "Selecione ao menos uma área administrativa.",
            )
            return
        self.cleaned_data["operational_requested_roles_payload"] = json.dumps(role_codes)
        self.cleaned_data["teacher_assignment_mode"] = ""
        self.cleaned_data["teacher_existing_class_group"] = ""
        self.cleaned_data["teacher_existing_class_groups_payload"] = ""
        self.cleaned_data["teacher_proposed_schedule_payload"] = ""

    def _clean_teacher_operational_registration(self):
        mode = self.cleaned_data.get("teacher_assignment_mode") or ""
        if mode not in TEACHER_ASSIGNMENT_MODES:
            self.add_error(
                "teacher_assignment_mode",
                "Selecione se vai assumir turma existente ou propor novo horário.",
            )
            return

        self.cleaned_data["operational_requested_roles_payload"] = ""
        if mode == TEACHER_ASSIGNMENT_EXISTING:
            self._clean_teacher_existing_class_groups()
            self.cleaned_data["teacher_proposed_schedule_payload"] = ""
            return
        self.cleaned_data["teacher_existing_class_group"] = ""
        self.cleaned_data["teacher_existing_class_groups_payload"] = ""
        self._clean_teacher_proposed_schedule()

    def _clean_teacher_existing_class_groups(self):
        selected_payload = self._parse_json_list(
            self.cleaned_data.get("teacher_existing_class_groups_payload"),
            "teacher_existing_class_groups_payload",
            "Selecione ao menos uma turma ativa.",
            allow_blank=True,
        )
        fallback_id = self.cleaned_data.get("teacher_existing_class_group")
        if fallback_id and not selected_payload:
            selected_payload = [{"id": fallback_id}]

        raw_values = []
        for item in selected_payload:
            if isinstance(item, dict):
                raw_values.append(
                    str(item.get("id") or item.get("class_group_id") or "")
                )
            else:
                raw_values.append(str(item))
        raw_values = [value for value in raw_values if value]


        resolved_groups = resolve_class_group_selection(raw_values)
        if not resolved_groups:
            self.add_error(
                "teacher_existing_class_groups_payload",
                "Selecione ao menos uma turma ativa.",
            )
            return

        normalized_payload = []
        for class_group in resolved_groups:
            source_item = next(
                (
                    item
                    for item in selected_payload
                    if isinstance(item, dict)
                    and str(item.get("id") or item.get("class_group_id") or "")
                    in raw_values
                ),
                {},
            )
            normalized_payload.append(
                {
                    "id": class_group.pk,
                    "class_group_id": class_group.pk,
                    "label": source_item.get("label") or str(class_group),
                    "teacher_names": source_item.get("teacher_names") or [],
                    "approval_scope": source_item.get("approval_scope")
                    or ("admin_and_current_teacher" if class_group.main_teacher_id else "admin_only"),
                }
            )

        self.cleaned_data["teacher_existing_class_group"] = str(resolved_groups[0].pk)
        self.cleaned_data["teacher_existing_class_groups_payload"] = json.dumps(
            normalized_payload,
            ensure_ascii=False,
        )

    def _clean_teacher_proposed_schedule(self):
        payload = self._parse_json_object(
            self.cleaned_data.get("teacher_proposed_schedule_payload"),
            "teacher_proposed_schedule_payload",
            "Crie o horário proposto antes de avançar.",
        )
        if not payload:
            return
        weekdays = payload.get("weekdays")
        if not weekdays and payload.get("weekday"):
            weekdays = [payload.get("weekday")]
        if not isinstance(weekdays, list):
            weekdays = []
        weekdays = [str(weekday) for weekday in weekdays if str(weekday)]
        invalid_weekdays = [weekday for weekday in weekdays if weekday not in WEEKDAY_VALUES]
        required_values = (
            payload.get("category_id"),
            payload.get("display_name"),
            payload.get("start_time"),
        )
        if not all(required_values) or not weekdays or invalid_weekdays:
            self.add_error(
                "teacher_proposed_schedule_payload",
                "Informe categoria, nome, dias da semana e horário de início.",
            )
            return
        payload["weekdays"] = weekdays
        payload.pop("weekday", None)
        self.cleaned_data["teacher_proposed_schedule_payload"] = json.dumps(
            payload,
            ensure_ascii=False,
        )

    def _clean_operational_finance(self):
        arrangement = self.cleaned_data.get("operational_financial_arrangement") or ""
        if not arrangement:
            arrangement = self._map_legacy_financial_arrangement()
        if arrangement not in OPERATIONAL_FINANCIAL_ARRANGEMENTS:
            self.add_error(
                "operational_financial_arrangement",
                "Selecione uma condição financeira válida.",
            )
            return
        self.cleaned_data["operational_financial_arrangement"] = arrangement
        self._sync_legacy_financial_fields(arrangement)

        if arrangement not in PAID_OPERATIONAL_FINANCIAL_ARRANGEMENTS:
            self._clear_operational_payout_fields()
            return

        payout_method = self.cleaned_data.get("operational_payout_method") or "none"
        if payout_method not in PAYOUT_METHODS:
            self.add_error("operational_payout_method", "Selecione um meio de recebimento válido.")
            return
        if payout_method == "none":
            self.add_error(
                "operational_payout_method",
                "Informe PIX ou conta bancária para condição com recebimento.",
            )
            return

        if arrangement in {OPERATIONAL_FINANCIAL_PAID_FIXED, OPERATIONAL_FINANCIAL_PAID_MIXED}:
            fixed_amount = self._clean_positive_decimal(
                "operational_fixed_amount",
                "Informe o valor fixo combinado.",
            )
            if fixed_amount is not None:
                self.cleaned_data["operational_fixed_amount"] = str(fixed_amount)
        else:
            self.cleaned_data["operational_fixed_amount"] = ""

        if arrangement in {OPERATIONAL_FINANCIAL_PAID_PER_STUDENT, OPERATIONAL_FINANCIAL_PAID_MIXED}:
            percentage = self._clean_positive_decimal(
                "operational_student_percentage",
                "Informe o percentual por aluno.",
            )
            if percentage is not None:
                self.cleaned_data["operational_student_percentage"] = str(percentage)
        else:
            self.cleaned_data["operational_student_percentage"] = ""

        if payout_method == "pix":
            if not self.cleaned_data.get("operational_pix_key_type") or not (
                self.cleaned_data.get("operational_pix_key") or ""
            ).strip():
                self.add_error(
                    "operational_pix_key",
                    "Informe tipo e chave PIX para recebimento.",
                )
            self.cleaned_data["operational_bank_details"] = ""
        elif payout_method == "bank":
            if not (self.cleaned_data.get("operational_bank_details") or "").strip():
                self.add_error(
                    "operational_bank_details",
                    "Informe os dados bancários para recebimento.",
                )
            self.cleaned_data["operational_pix_key_type"] = ""
            self.cleaned_data["operational_pix_key"] = ""

    def _map_legacy_financial_arrangement(self):
        payment_condition = self.cleaned_data.get("operational_payment_condition") or ""
        payout_method = self.cleaned_data.get("operational_payout_method") or "none"
        if payout_method in {"pix", "bank"}:
            return OPERATIONAL_FINANCIAL_PAID_FIXED
        if payment_condition == "barter":
            return OPERATIONAL_FINANCIAL_BARTER
        if payment_condition == "no_monthly_fee":
            return OPERATIONAL_FINANCIAL_VOLUNTEER
        return OPERATIONAL_FINANCIAL_PAYS_MONTHLY

    def _sync_legacy_financial_fields(self, arrangement):
        if arrangement == OPERATIONAL_FINANCIAL_PAYS_MONTHLY:
            self.cleaned_data["operational_payment_condition"] = "pay_monthly"
            self.cleaned_data["operational_compensation_preference"] = "none"
        elif arrangement == OPERATIONAL_FINANCIAL_BARTER:
            self.cleaned_data["operational_payment_condition"] = "barter"
            self.cleaned_data["operational_compensation_preference"] = "barter"
        elif arrangement == OPERATIONAL_FINANCIAL_VOLUNTEER:
            self.cleaned_data["operational_payment_condition"] = "no_monthly_fee"
            self.cleaned_data["operational_compensation_preference"] = "none"
        else:
            payout_method = self.cleaned_data.get("operational_payout_method") or "none"
            self.cleaned_data["operational_payment_condition"] = "no_monthly_fee"
            self.cleaned_data["operational_compensation_preference"] = payout_method

    def _clear_operational_payout_fields(self):
        self.cleaned_data["operational_payout_method"] = "none"
        self.cleaned_data["operational_pix_key_type"] = ""
        self.cleaned_data["operational_pix_key"] = ""
        self.cleaned_data["operational_bank_details"] = ""
        self.cleaned_data["operational_fixed_amount"] = ""
        self.cleaned_data["operational_student_percentage"] = ""

    def _clean_positive_decimal(self, field_name, message):
        raw_value = self.cleaned_data.get(field_name)
        if raw_value in (None, ""):
            self.add_error(field_name, message)
            return None
        try:
            value = Decimal(str(raw_value).replace(",", "."))
        except (InvalidOperation, ValueError):
            self.add_error(field_name, message)
            return None
        if value <= 0:
            self.add_error(field_name, message)
            return None
        return value.quantize(Decimal("0.01"))

    def _parse_json_list(self, raw_value, field_name, message, *, allow_blank=False):
        if raw_value in (None, ""):
            if allow_blank:
                return []
            self.add_error(field_name, message)
            return []
        if isinstance(raw_value, list):
            return raw_value
        try:
            payload = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            self.add_error(field_name, message)
            return []
        if not isinstance(payload, list):
            self.add_error(field_name, message)
            return []
        return payload

    def _parse_json_object(self, raw_value, field_name, message):
        if raw_value in (None, ""):
            self.add_error(field_name, message)
            return {}
        if isinstance(raw_value, dict):
            return raw_value
        try:
            payload = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            self.add_error(field_name, message)
            return {}
        if not isinstance(payload, dict):
            self.add_error(field_name, message)
            return {}
        return payload
