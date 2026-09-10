
from django import forms

from system.business_rule.models import ClassGroup
from system.business_rule.constants import CheckoutAction, RegistrationProfile
from system.business_rule.forms.registration_operational_forms import OperationalRegistrationFieldsMixin
from system.business_rule.forms.registration_person_fields import person_fields_mixin
from system.business_rule.forms.registration_class_links import RegistrationClassLinksMixin
from system.business_rule.forms.registration_cpf_validation import RegistrationCpfMixin
from system.business_rule.forms.registration_extra_dependents import RegistrationExtraDependentsMixin
from system.business_rule.forms.registration_kinship import RegistrationKinshipMixin
from system.business_rule.forms.registration_martial_background import RegistrationMartialBackgroundMixin
from system.business_rule.forms.registration_password_validation import RegistrationPasswordMixin
from system.business_rule.forms.registration_person_type import RegistrationPersonTypeMixin
from system.business_rule.forms.registration_plan_selection import RegistrationPlanSelectionMixin
from system.business_rule.forms.registration_required_fields import RegistrationRequiredFieldsMixin


HolderFields = person_fields_mixin("holder", class_groups=True, address=True)
DependentFields = person_fields_mixin("dependent", class_groups=True, kinship=True)
GuardianFields = person_fields_mixin("guardian", birthdate=False, address=True)
StudentFields = person_fields_mixin("student", class_groups=True, kinship=True)
OtherFields = person_fields_mixin("other")


class PortalRegistrationForm(
    OperationalRegistrationFieldsMixin,
    RegistrationClassLinksMixin,
    RegistrationCpfMixin,
    RegistrationExtraDependentsMixin,
    RegistrationKinshipMixin,
    RegistrationMartialBackgroundMixin,
    RegistrationPasswordMixin,
    RegistrationPersonTypeMixin,
    RegistrationPlanSelectionMixin,
    RegistrationRequiredFieldsMixin,
    HolderFields,
    DependentFields,
    GuardianFields,
    StudentFields,
    OtherFields,
    forms.Form,
):
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





    selected_plan = forms.CharField(required=False)
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
        raise NotImplementedError(
            "PortalRegistrationForm não materializa domínio. A finalização do "
            "cadastro chama system.business_rule.services.registration.create_portal_registration "
            "diretamente a partir de system.business_rule.services.registration_finalize.finalize_pre_registration."
        )

