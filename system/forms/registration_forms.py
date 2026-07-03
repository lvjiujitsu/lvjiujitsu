import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django import forms

from system.models import (
    BiologicalSex,
    BloodType,
    ClassGroup,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonType,
    SubscriptionPlan,
)
from system.models.class_membership import get_class_group_eligibility_error
from system.constants import (
    CheckoutAction,
    OperationalRoleCode,
    PersonTypeCode,
    RegistrationProfile,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.services.class_overview import get_public_class_group_choice_options
from system.services.registration import (
    create_portal_registration,
    get_kinship_choices,
    parse_extra_dependents_payload,
    resolve_class_groups,
)
from system.selectors.plan_eligibility import (
    build_eligibility_context_for_registration,
    is_plan_eligible,
)
from system.services.registration_checkout import (
    parse_selected_products,
    resolve_selected_product_items,
)
from system.services.financial_transactions import resolve_checkout_action_for_plan
from system.utils import ensure_formatted_cpf


MARTIAL_ART_EXPERIENCE_YES = "yes"
MARTIAL_ART_EXPERIENCE_NO = "no"
MARTIAL_ART_EXPERIENCE_CHOICES = [
    ("", "Selecione"),
    (MARTIAL_ART_EXPERIENCE_YES, "Sim"),
    (MARTIAL_ART_EXPERIENCE_NO, "Não"),
]
MARTIAL_ART_MODALITY_CHOICES = [("", "Selecione")] + list(MartialArt.choices)

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


class PortalRegistrationForm(forms.Form):
    registration_profile = forms.ChoiceField(
        choices=(
            (RegistrationProfile.HOLDER, "Aluno titular"),
            (RegistrationProfile.GUARDIAN, "Responsável"),
            (RegistrationProfile.OTHER, "Outro"),
        ),
        required=False,
        initial='',
    )
    include_dependent = forms.BooleanField(required=False)
    other_type_code = forms.ChoiceField(required=False)
    extra_dependents_payload = forms.CharField(required=False, widget=forms.HiddenInput)

    holder_name = forms.CharField(required=False, max_length=255)
    holder_cpf = forms.CharField(required=False, max_length=14)
    holder_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    holder_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    holder_phone = forms.CharField(required=False, max_length=20)
    holder_email = forms.EmailField(required=False)
    holder_password = forms.CharField(required=False, strip=False)
    holder_password_confirm = forms.CharField(required=False, strip=False)
    holder_class_groups = forms.MultipleChoiceField(required=False)
    holder_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    holder_allergies = forms.CharField(required=False)
    holder_injuries = forms.CharField(required=False)
    holder_emergency_contact = forms.CharField(required=False, max_length=255)
    holder_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
    )
    holder_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
    )
    holder_martial_art_graduation = forms.CharField(required=False, max_length=120)
    holder_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    holder_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)
    holder_martial_art_started_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    holder_martial_art_last_graduation_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    holder_previous_academy = forms.CharField(required=False, max_length=200)
    holder_postal_code = forms.CharField(required=False, max_length=9)
    holder_address = forms.CharField(required=False, max_length=255)
    holder_address_number = forms.CharField(required=False, max_length=20)
    holder_address_complement = forms.CharField(required=False, max_length=100)
    holder_address_neighborhood = forms.CharField(required=False, max_length=100)
    holder_city = forms.CharField(required=False, max_length=100)

    dependent_name = forms.CharField(required=False, max_length=255)
    dependent_cpf = forms.CharField(required=False, max_length=14)
    dependent_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    dependent_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    dependent_email = forms.EmailField(required=False)
    dependent_phone = forms.CharField(required=False, max_length=20)
    dependent_password = forms.CharField(required=False, strip=False)
    dependent_password_confirm = forms.CharField(required=False, strip=False)
    dependent_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    dependent_kinship_other_label = forms.CharField(required=False, max_length=80)
    dependent_class_groups = forms.MultipleChoiceField(required=False)
    dependent_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    dependent_allergies = forms.CharField(required=False)
    dependent_injuries = forms.CharField(required=False)
    dependent_emergency_contact = forms.CharField(required=False, max_length=255)
    dependent_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
    )
    dependent_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
    )
    dependent_martial_art_graduation = forms.CharField(required=False, max_length=120)
    dependent_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    dependent_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)
    dependent_martial_art_started_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    dependent_martial_art_last_graduation_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    dependent_previous_academy = forms.CharField(required=False, max_length=200)

    guardian_name = forms.CharField(required=False, max_length=255)
    guardian_cpf = forms.CharField(required=False, max_length=14)
    guardian_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    guardian_phone = forms.CharField(required=False, max_length=20)
    guardian_email = forms.EmailField(required=False)
    guardian_password = forms.CharField(required=False, strip=False)
    guardian_password_confirm = forms.CharField(required=False, strip=False)
    guardian_postal_code = forms.CharField(required=False, max_length=9)
    guardian_address = forms.CharField(required=False, max_length=255)
    guardian_address_number = forms.CharField(required=False, max_length=20)
    guardian_address_complement = forms.CharField(required=False, max_length=100)
    guardian_address_neighborhood = forms.CharField(required=False, max_length=100)
    guardian_city = forms.CharField(required=False, max_length=100)
    guardian_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    guardian_allergies = forms.CharField(required=False)
    guardian_injuries = forms.CharField(required=False)
    guardian_emergency_contact = forms.CharField(required=False, max_length=255)
    guardian_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
    )
    guardian_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
    )
    guardian_martial_art_graduation = forms.CharField(required=False, max_length=120)
    guardian_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    guardian_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)
    guardian_martial_art_started_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    guardian_martial_art_last_graduation_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    guardian_previous_academy = forms.CharField(required=False, max_length=200)

    student_name = forms.CharField(required=False, max_length=255)
    student_cpf = forms.CharField(required=False, max_length=14)
    student_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    student_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    student_email = forms.EmailField(required=False)
    student_phone = forms.CharField(required=False, max_length=20)
    student_password = forms.CharField(required=False, strip=False)
    student_password_confirm = forms.CharField(required=False, strip=False)
    student_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    student_kinship_other_label = forms.CharField(required=False, max_length=80)
    student_class_groups = forms.MultipleChoiceField(required=False)
    student_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    student_allergies = forms.CharField(required=False)
    student_injuries = forms.CharField(required=False)
    student_emergency_contact = forms.CharField(required=False, max_length=255)
    student_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
    )
    student_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
    )
    student_martial_art_graduation = forms.CharField(required=False, max_length=120)
    student_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    student_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)
    student_martial_art_started_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    student_martial_art_last_graduation_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    student_previous_academy = forms.CharField(required=False, max_length=200)

    selected_plan = forms.IntegerField(required=False)
    selected_products_payload = forms.CharField(required=False, widget=forms.HiddenInput)
    coupon_code = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput)
    checkout_action = forms.ChoiceField(
        required=False,
        choices=(
            (CheckoutAction.ASAAS_CARD, "Pagar com cartão"),
            (CheckoutAction.PIX, "Pagar com PIX"),
            (CheckoutAction.STRIPE_CARD, "Pagar com cartão (Stripe)"),
            (CheckoutAction.PAY_LATER, "Concluir e pagar depois"),
        ),
        initial=CheckoutAction.PAY_LATER,
    )

    other_name = forms.CharField(required=False, max_length=255)
    other_cpf = forms.CharField(required=False, max_length=14)
    other_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    other_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    other_phone = forms.CharField(required=False, max_length=20)
    other_email = forms.EmailField(required=False)
    other_password = forms.CharField(required=False, strip=False)
    other_password_confirm = forms.CharField(required=False, strip=False)
    other_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    other_allergies = forms.CharField(required=False)
    other_injuries = forms.CharField(required=False)
    other_emergency_contact = forms.CharField(required=False, max_length=255)
    other_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
    )
    other_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
    )
    other_martial_art_graduation = forms.CharField(required=False, max_length=120)
    other_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    other_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)
    other_martial_art_started_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    other_martial_art_last_graduation_at = forms.DateField(required=False, input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    other_previous_academy = forms.CharField(required=False, max_length=200)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_is_available = ClassGroup.objects.filter(is_active=True).exists()
        self._configure_other_type_choices()
        self._configure_class_choices()
        for prefix in ("dependent", "student"):
            self.fields[f"{prefix}_class_groups"].valid_value = lambda v: True

    def clean(self):
        cleaned_data = super().clean()
        profile = cleaned_data.get("registration_profile") or RegistrationProfile.HOLDER
        include_dependent = cleaned_data.get("include_dependent", False)
        extra_dependents = self._clean_extra_dependents_payload()
        if profile == RegistrationProfile.OTHER or (
            profile == RegistrationProfile.HOLDER and not include_dependent
        ):
            extra_dependents = []
        cleaned_data["extra_dependents"] = extra_dependents

        self._clean_required_fields(profile, include_dependent)
        self._clean_cpfs(extra_dependents)
        self._clean_other_type_code(profile)
        self._clean_passwords(profile, include_dependent, extra_dependents)
        self._clean_class_links(profile, include_dependent, extra_dependents)
        self._clean_plan_selection(profile, include_dependent, extra_dependents)
        self._clean_selected_products_payload()
        self._clean_kinship(profile, include_dependent, extra_dependents)
        self._clean_martial_background(profile, include_dependent, extra_dependents)
        self._clean_operational_registration(profile)
        if not self.cleaned_data.get("checkout_action"):
            self.cleaned_data["checkout_action"] = CheckoutAction.PAY_LATER
        return cleaned_data

    def save(self):
        return create_portal_registration(self.cleaned_data)

    def _configure_other_type_choices(self):
        choices = [("", "Selecione")]
        queryset = PersonType.objects.filter(is_active=True).exclude(
            code__in=STUDENT_PORTAL_PERSON_TYPE_CODES
        )
        choices.extend((item.code, item.display_name) for item in queryset.order_by("display_name"))
        self.fields["other_type_code"].choices = choices

    def _configure_class_choices(self):
        group_choices = [("", "Selecione")] + get_public_class_group_choice_options()
        for prefix in ("holder", "dependent", "student"):
            self.fields[f"{prefix}_class_groups"].choices = group_choices

    def _clean_required_fields(self, profile, include_dependent):
        if profile == RegistrationProfile.HOLDER:
            self._require_fields(
                "holder_name",
                "holder_cpf",
                "holder_birthdate",
                "holder_biological_sex",
                "holder_password",
                "holder_password_confirm",
            )
            if include_dependent:
                self._require_fields(
                    "dependent_name",
                    "dependent_cpf",
                    "dependent_birthdate",
                    "dependent_biological_sex",
                    "dependent_password",
                    "dependent_password_confirm",
                    "dependent_kinship_type",
                )
            return

        if profile == RegistrationProfile.GUARDIAN:
            self._require_fields(
                "guardian_name",
                "guardian_cpf",
                "guardian_password",
                "guardian_password_confirm",
                "student_name",
                "student_cpf",
                "student_birthdate",
                "student_biological_sex",
                "student_password",
                "student_password_confirm",
                "student_kinship_type",
            )
            return

        self._require_fields(
            "other_name",
            "other_cpf",
            "other_birthdate",
            "other_biological_sex",
            "other_password",
            "other_password_confirm",
        )

    def _require_fields(self, *field_names):
        for field_name in field_names:
            value = self.cleaned_data.get(field_name)
            if value in (None, ""):
                self.add_error(field_name, "Campo obrigatório.")

    def _clean_cpfs(self, extra_dependents):
        seen_cpfs = set()
        for field_name in (
            "holder_cpf",
            "dependent_cpf",
            "guardian_cpf",
            "student_cpf",
            "other_cpf",
        ):
            value = self.cleaned_data.get(field_name)
            if not value:
                continue
            self.cleaned_data[field_name] = self._validate_single_cpf(value, field_name, seen_cpfs)

        for index, dependent in enumerate(extra_dependents, start=1):
            value = dependent.get("cpf")
            if not value:
                continue
            dependent["cpf"] = self._validate_single_cpf(value, None, seen_cpfs, index=index)

    def _validate_single_cpf(self, value, field_name, seen_cpfs, index=None):
        try:
            formatted = ensure_formatted_cpf(value)
        except ValueError as error:
            if field_name:
                self.add_error(field_name, str(error))
            else:
                self.add_error(None, f"Dependente adicional {index}: {error}")
            return value

        if formatted in seen_cpfs:
            message = "CPF duplicado no cadastro."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        existing = Person.objects.filter(cpf=formatted).first()
        if existing is not None and existing.is_active:
            message = "CPF já cadastrado no sistema."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        seen_cpfs.add(formatted)
        return formatted

    def _clean_other_type_code(self, profile):
        selected_code = self.cleaned_data.get("other_type_code") or ""
        available_codes = {code for code, _label in self.fields["other_type_code"].choices if code}
        if profile != RegistrationProfile.OTHER:
            self.cleaned_data["other_type_code"] = ""
            return
        if not available_codes:
            self.add_error(
                "other_type_code",
                "Nenhum tipo adicional está disponível para esse cadastro.",
            )
            return
        if available_codes and selected_code not in available_codes:
            self.add_error("other_type_code", "Selecione um tipo de cadastro válido.")
        if available_codes and not selected_code:
            self.add_error("other_type_code", "Selecione um tipo de cadastro.")

    def _clean_passwords(self, profile, include_dependent, extra_dependents):
        groups = []
        if profile == RegistrationProfile.HOLDER:
            groups.append(("holder_password", "holder_password_confirm", "aluno titular"))
            if include_dependent:
                groups.append(("dependent_password", "dependent_password_confirm", "dependente"))
        elif profile == RegistrationProfile.GUARDIAN:
            groups.append(("guardian_password", "guardian_password_confirm", "responsável"))
            groups.append(("student_password", "student_password_confirm", "dependente"))
        else:
            groups.append(("other_password", "other_password_confirm", "cadastro"))

        for password_field, confirm_field, label in groups:
            self._validate_password_pair(
                self.cleaned_data.get(password_field),
                self.cleaned_data.get(confirm_field),
                confirm_field,
                label,
            )

        for index, dependent in enumerate(extra_dependents, start=1):
            self._validate_password_pair(
                dependent.get("password"),
                dependent.get("password_confirm"),
                None,
                f"dependente adicional {index}",
            )

    def _validate_password_pair(self, password, confirm_password, error_field, label):
        if not password or not confirm_password:
            return
        if password != confirm_password:
            message = f"As senhas de {label} não coincidem."
            if error_field:
                self.add_error(error_field, message)
            else:
                self.add_error(None, message)

    def _clean_class_links(self, profile, include_dependent, extra_dependents):
        if profile == RegistrationProfile.HOLDER:
            self._resolve_class_group_collection("holder", required=self.catalog_is_available)
            if include_dependent:
                self._resolve_class_group_collection(
                    "dependent",
                    required=self.catalog_is_available,
                )
        elif profile == RegistrationProfile.GUARDIAN:
            self._resolve_class_group_collection("student", required=self.catalog_is_available)

        for index, dependent in enumerate(extra_dependents, start=1):
            if not dependent.get("biological_sex"):
                self.add_error(None, f"Dependente adicional {index}: informe o sexo biológico.")
            raw_group_ids = dependent.get("class_groups") or []
            if not self.catalog_is_available and not raw_group_ids:
                dependent["class_groups"] = []
                continue
            groups = resolve_class_groups(raw_group_ids)
            if self.catalog_is_available and not groups:
                self.add_error(None, f"Dependente adicional {index}: selecione ao menos uma turma.")
                continue
            if self._has_invalid_class_group_selection(raw_group_ids):
                self.add_error(
                    None,
                    f"Dependente adicional {index}: selecione apenas turmas válidas.",
                )
            self._add_class_group_eligibility_errors(
                None,
                groups,
                dependent.get("birth_date"),
                dependent.get("biological_sex", ""),
                f"Dependente adicional {index}",
            )
            dependent["class_groups"] = groups

    def _clean_plan_selection(self, profile, include_dependent, extra_dependents):
        plan_id = self.cleaned_data.get("selected_plan")
        if not plan_id:
            return
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            self.add_error("selected_plan", "Selecione um plano válido.")
            return

        context = build_eligibility_context_for_registration(self.cleaned_data)
        if not is_plan_eligible(plan, context):
            self.add_error(
                "selected_plan",
                self._build_plan_ineligible_message(plan, context),
            )
            return

        checkout_action = self.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
        expected_action = resolve_checkout_action_for_plan(plan)
        if checkout_action != CheckoutAction.PAY_LATER and checkout_action != expected_action:
            self.add_error(
                "checkout_action",
                "O meio de pagamento escolhido não corresponde ao plano selecionado.",
            )

    def _build_plan_ineligible_message(self, plan, context):
        if plan.requires_special_authorization:
            return "Este plano exige autorização especial da academia."
        if plan.is_family_plan:
            return (
                "Plano familiar disponível apenas quando há ao menos dois alunos "
                "ativos no grupo familiar com a mesma faixa etária do plano."
            )
        from system.models.plan import PlanAudience

        if plan.audience == PlanAudience.KIDS_JUVENILE and context.kids_juvenile_active_count < 1:
            return "Plano Kids/Juvenil exige aluno menor cadastrado."
        if plan.audience == PlanAudience.ADULT and not context.adult_active:
            return "Plano Adulto exige aluno adulto cadastrado."
        return "Plano não disponível para o perfil selecionado."

    def _clean_selected_products_payload(self):
        selected_products = parse_selected_products(
            self.cleaned_data.get("selected_products_payload")
        )
        if not selected_products:
            self.cleaned_data["selected_products"] = []
            return
        try:
            self.cleaned_data["selected_products"] = resolve_selected_product_items(
                selected_products
            )
        except ValueError as error:
            self.cleaned_data["selected_products"] = []
            self.add_error("selected_products_payload", str(error))

    def _resolve_class_group_collection(self, prefix, required):
        field_name = f"{prefix}_class_groups"
        raw_group_ids = [
            v for v in (self.cleaned_data.get(field_name) or [])
            if v and not str(v).startswith("[")
        ]

        if not raw_group_ids and not required:
            self.cleaned_data[field_name] = []
            return

        if required and not self.catalog_is_available:
            self.cleaned_data[field_name] = []
            return

        groups = resolve_class_groups(raw_group_ids)

        if required and not groups:
            self.add_error(field_name, "Selecione ao menos uma turma.")
        if self._has_invalid_class_group_selection(raw_group_ids):
            self.add_error(field_name, "Selecione apenas turmas válidas.")

        self._add_class_group_eligibility_errors(
            field_name,
            groups,
            self.cleaned_data.get(f"{prefix}_birthdate"),
            self.cleaned_data.get(f"{prefix}_biological_sex", ""),
        )
        self.cleaned_data[field_name] = groups

    def _has_invalid_class_group_selection(self, raw_group_ids):
        for raw_group_id in raw_group_ids:
            if not str(raw_group_id):
                continue
            if resolve_class_groups([raw_group_id]):
                continue
            return True
        return False

    def _add_class_group_eligibility_errors(
        self,
        field_name,
        class_groups,
        birth_date,
        biological_sex,
        label_prefix=None,
    ):
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=birth_date,
                biological_sex=biological_sex,
                class_group=class_group,
            )
            if not error:
                continue
            message = f"{class_group.class_category.display_name} · {class_group.display_name}: {error}"
            if label_prefix:
                self.add_error(None, f"{label_prefix}: {message}")
            else:
                self.add_error(field_name, message)

    def _clean_kinship(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER and include_dependent:
            prefixes.append("dependent")
        if profile == RegistrationProfile.GUARDIAN:
            prefixes.append("student")

        for prefix in prefixes:
            kinship_type = self.cleaned_data.get(f"{prefix}_kinship_type") or ""
            other_label = (self.cleaned_data.get(f"{prefix}_kinship_other_label") or "").strip()
            if kinship_type == "other" and not other_label:
                self.add_error(
                    f"{prefix}_kinship_other_label",
                    "Informe o grau de parentesco.",
                )

        for index, dependent in enumerate(extra_dependents, start=1):
            if dependent.get("kinship_type") == "other" and not (dependent.get("kinship_other_label") or "").strip():
                self.add_error(None, f"Dependente adicional {index}: informe o grau de parentesco.")

    def _clean_martial_background(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER:
            prefixes.append("holder")
            if include_dependent:
                prefixes.append("dependent")
        elif profile == RegistrationProfile.GUARDIAN:
            prefixes.append("guardian")
            prefixes.append("student")
        elif profile == RegistrationProfile.OTHER:
            prefixes.append("other")

        for prefix in prefixes:
            has_martial_art = self._normalize_martial_art_answer(
                self.cleaned_data.get(f"{prefix}_has_martial_art") or "",
                self.cleaned_data.get(f"{prefix}_martial_art") or "",
            )
            self.cleaned_data[f"{prefix}_has_martial_art"] = has_martial_art
            martial_art = self.cleaned_data.get(f"{prefix}_martial_art") or ""
            graduation = (self.cleaned_data.get(f"{prefix}_martial_art_graduation") or "").strip()
            belt = self.cleaned_data.get(f"{prefix}_jiu_jitsu_belt") or ""
            if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
                self._clear_martial_background_fields(prefix)
                continue
            if not martial_art:
                self.add_error(
                    f"{prefix}_martial_art",
                    "Selecione a arte marcial praticada.",
                )
                self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None
                continue
            if martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(
                    f"{prefix}_martial_art_graduation",
                    "Informe a graduação/nível na arte marcial.",
                )
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(
                    f"{prefix}_jiu_jitsu_belt",
                    "Informe a faixa de Jiu Jitsu.",
                )
            if martial_art != MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""

        for index, dependent in enumerate(extra_dependents, start=1):
            has_martial_art = self._normalize_martial_art_answer(
                dependent.get("has_martial_art") or "",
                dependent.get("martial_art") or "",
            )
            dependent["has_martial_art"] = has_martial_art
            martial_art = dependent.get("martial_art") or ""
            graduation = (dependent.get("martial_art_graduation") or "").strip()
            belt = dependent.get("jiu_jitsu_belt") or ""
            if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
                self._clear_extra_dependent_martial_background(dependent)
                continue
            if not martial_art:
                self.add_error(
                    None,
                    f"Dependente adicional {index}: selecione a arte marcial praticada.",
                )
                dependent["martial_art_graduation"] = ""
                dependent["jiu_jitsu_belt"] = ""
                dependent["jiu_jitsu_stripes"] = None
                continue
            if martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(None, f"Dependente adicional {index}: informe a graduação na arte marcial.")
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(None, f"Dependente adicional {index}: informe a faixa de Jiu Jitsu.")
            if martial_art != MartialArt.JIU_JITSU:
                dependent["jiu_jitsu_belt"] = ""
                dependent["jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                dependent["martial_art_graduation"] = ""

    def _clean_extra_dependents_payload(self):
        payload = parse_extra_dependents_payload(self.cleaned_data.get("extra_dependents_payload"))
        cleaned_dependents = []
        for index, dependent in enumerate(payload, start=1):
            birth_date_raw = dependent.get("birth_date") or ""
            birth_date = None
            jiu_jitsu_stripes = dependent.get("jiu_jitsu_stripes")
            if jiu_jitsu_stripes in ("", None):
                jiu_jitsu_stripes = None
            else:
                try:
                    jiu_jitsu_stripes = int(jiu_jitsu_stripes)
                except (TypeError, ValueError):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu inválidos.")
                    jiu_jitsu_stripes = None
                if jiu_jitsu_stripes is not None and not (0 <= jiu_jitsu_stripes <= 4):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu deve ser entre 0 e 4.")
                    jiu_jitsu_stripes = None
            if birth_date_raw:
                try:
                    birth_date = datetime.strptime(birth_date_raw, "%d/%m/%Y").date()
                except ValueError:
                    self.add_error(
                        None,
                        f"Dependente adicional {index}: data de nascimento inválida.",
                    )
            cleaned_dependents.append(
                {
                    "full_name": (dependent.get("full_name") or "").strip(),
                    "cpf": (dependent.get("cpf") or "").strip(),
                    "birth_date": birth_date,
                    "biological_sex": dependent.get("biological_sex") or "",
                    "email": (dependent.get("email") or "").strip(),
                    "phone": (dependent.get("phone") or "").strip(),
                    "password": dependent.get("password") or "",
                    "password_confirm": dependent.get("password_confirm") or "",
                    "kinship_type": dependent.get("kinship_type") or "",
                    "kinship_other_label": (dependent.get("kinship_other_label") or "").strip(),
                    "class_groups": dependent.get("class_groups") or [],
                    "blood_type": dependent.get("blood_type") or "",
                    "allergies": dependent.get("allergies") or "",
                    "previous_injuries": dependent.get("injuries") or dependent.get("previous_injuries") or "",
                    "emergency_contact": dependent.get("emergency_contact") or "",
                    "has_martial_art": self._normalize_martial_art_answer(
                        dependent.get("has_martial_art") or "",
                        dependent.get("martial_art") or "",
                    ),
                    "martial_art": dependent.get("martial_art") or "",
                    "martial_art_graduation": dependent.get("martial_art_graduation") or "",
                    "jiu_jitsu_belt": dependent.get("jiu_jitsu_belt") or "",
                    "jiu_jitsu_stripes": jiu_jitsu_stripes,
                }
            )
        return cleaned_dependents

    def _normalize_martial_art_answer(self, answer, martial_art):
        if answer:
            return answer
        return MARTIAL_ART_EXPERIENCE_YES if martial_art else ""

    def _clear_martial_background_fields(self, prefix):
        self.cleaned_data[f"{prefix}_martial_art"] = ""
        self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""
        self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
        self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None

    def _clear_extra_dependent_martial_background(self, dependent):
        dependent["martial_art"] = ""
        dependent["martial_art_graduation"] = ""
        dependent["jiu_jitsu_belt"] = ""
        dependent["jiu_jitsu_stripes"] = None

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

        selected_ids = []
        normalized_payload = []
        for item in selected_payload:
            if isinstance(item, dict):
                raw_id = item.get("id") or item.get("class_group_id")
            else:
                raw_id = item
            try:
                selected_id = int(raw_id)
            except (TypeError, ValueError):
                self.add_error(
                    "teacher_existing_class_groups_payload",
                    "Selecione apenas turmas ativas válidas.",
                )
                return
            if selected_id in selected_ids:
                continue
            selected_ids.append(selected_id)
            normalized_payload.append(item if isinstance(item, dict) else {"id": selected_id})

        if not selected_ids:
            self.add_error(
                "teacher_existing_class_groups_payload",
                "Selecione ao menos uma turma ativa.",
            )
            return

        active_ids = set(
            ClassGroup.objects.filter(pk__in=selected_ids, is_active=True).values_list("pk", flat=True)
        )
        if len(active_ids) != len(selected_ids):
            self.add_error(
                "teacher_existing_class_groups_payload",
                "Selecione apenas turmas ativas válidas.",
            )
            return

        for item in normalized_payload:
            if isinstance(item, dict):
                item["id"] = int(item.get("id") or item.get("class_group_id"))
        self.cleaned_data["teacher_existing_class_group"] = str(selected_ids[0])
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
