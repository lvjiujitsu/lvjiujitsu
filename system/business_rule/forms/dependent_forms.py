from django import forms

from system.core.dates import PT_BR_DATE_INPUT_FORMATS
from system.business_rule.constants import CheckoutAction, DependentCardStrategy, DependentFinancialMode
from system.business_rule.forms.registration_common import (
    MARTIAL_ART_EXPERIENCE_CHOICES,
    MARTIAL_ART_MODALITY_CHOICES,
)
from system.business_rule.models import (
    BiologicalSex,
    BloodType,
    JiuJitsuBelt,
    MartialArt,
    Person,
    SubscriptionPlan,
)
from system.business_rule.models.plan import PlanPrice
from system.business_rule.services.class_overview import get_public_class_group_choice_options
from system.business_rule.services.registration import get_kinship_choices
from system.business_rule.services.registration_checkout import (
    build_catalog_plan_id,
    CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
    CATALOG_ID_PREFIX_PLAN_PRICE,
)
from system.business_rule.forms.dependent_class_selection import DependentClassesMixin
from system.business_rule.forms.dependent_cpf_validation import DependentCpfMixin
from system.business_rule.forms.dependent_financial_choice import DependentFinancialChoiceMixin
from system.business_rule.forms.dependent_martial_art import DependentMartialArtMixin
from system.business_rule.forms.dependent_materials import DependentMaterialsMixin
from system.business_rule.forms.dependent_password_validation import DependentPasswordMixin
from system.business_rule.forms.dependent_form_helpers import (
    build_material_variant_field_name,
    get_material_variants,
    owner_has_family_plan,
)


class DependentRegistrationForm(
    DependentClassesMixin,
    DependentCpfMixin,
    DependentFinancialChoiceMixin,
    DependentMartialArtMixin,
    DependentMaterialsMixin,
    DependentPasswordMixin,
    forms.Form,
):
    dependent_name = forms.CharField(max_length=255, label="Nome completo")
    dependent_cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(
            attrs={"inputmode": "numeric", "maxlength": "14", "placeholder": "000.000.000-00", "autocomplete": "off"}
        ),
    )
    dependent_birthdate = forms.DateField(
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Data de nascimento",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    dependent_biological_sex = forms.ChoiceField(
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
        label="Sexo biológico",
    )
    dependent_email = forms.EmailField(required=False, label="E-mail")
    dependent_phone = forms.CharField(
        required=False,
        max_length=20,
        label="Telefone",
        widget=forms.TextInput(
            attrs={"type": "tel", "inputmode": "tel", "maxlength": "16", "placeholder": "(00) 00000-0000", "autocomplete": "tel"}
        ),
    )
    dependent_password = forms.CharField(
        strip=False,
        label="Senha",
        widget=forms.PasswordInput(render_value=True),
    )
    dependent_password_confirm = forms.CharField(
        strip=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(render_value=True),
    )
    dependent_kinship_type = forms.ChoiceField(
        choices=[("", "Selecione")] + list(get_kinship_choices()),
        label="Parentesco",
    )
    dependent_kinship_other_label = forms.CharField(
        required=False,
        max_length=80,
        label="Parentesco",
    )
    dependent_class_groups = forms.MultipleChoiceField(
        required=True,
        label="Turmas",
    )
    dependent_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
        label="Tipo sanguíneo",
    )
    dependent_allergies = forms.CharField(
        required=False,
        label="Alergias",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    dependent_injuries = forms.CharField(
        required=False,
        label="Lesões",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    dependent_emergency_contact = forms.CharField(
        required=False,
        max_length=255,
        label="Contato de emergência",
    )
    dependent_has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
        label="Já treinou artes marciais?",
    )
    dependent_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_MODALITY_CHOICES,
        label="Arte marcial",
    )
    dependent_martial_art_graduation = forms.CharField(
        required=False,
        max_length=120,
        label="Graduação",
    )
    dependent_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
        label="Faixa de Jiu Jitsu",
    )
    dependent_jiu_jitsu_stripes = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        label="Graus",
    )
    dependent_martial_art_started_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Início no treino",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    dependent_martial_art_last_graduation_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Última graduação",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    dependent_previous_academy = forms.CharField(
        required=False,
        max_length=200,
        label="Academia anterior",
    )
    use_family_plan = forms.BooleanField(required=False, label="Usar plano familiar")
    financial_mode = forms.ChoiceField(
        required=False,
        choices=(
            (DependentFinancialMode.DEPENDENT_OWN, "Mensalidade própria"),
            (DependentFinancialMode.FAMILY_EXISTING, "Usar plano familiar ativo"),
            (DependentFinancialMode.FAMILY_UPGRADE, "Migrar para plano familiar"),
        ),
        initial=DependentFinancialMode.DEPENDENT_OWN,
    )
    selected_plan = forms.ChoiceField(required=False, label="Plano")
    card_strategy = forms.ChoiceField(
        required=False,
        choices=(
            (DependentCardStrategy.NEW_CARD, "Novo cartão"),
            (DependentCardStrategy.SAME_CARD_MERGED, "Mesmo cartão — fundir em 1 cobrança"),
            (DependentCardStrategy.SAME_CARD_STAGGERED, "Mesmo cartão — manter separado, escalonar horário"),
        ),
        initial=DependentCardStrategy.NEW_CARD,
    )
    checkout_action = forms.ChoiceField(
        required=False,
        choices=(
            (CheckoutAction.STRIPE_CARD, "Cartão Stripe"),
            (CheckoutAction.ASAAS_CARD, "Cartão"),
            (CheckoutAction.PIX, "PIX"),
            (CheckoutAction.PAY_LATER, "Pagar depois"),
        ),
        initial=CheckoutAction.PAY_LATER,
    )
    materials_checkout_action = forms.ChoiceField(
        required=False,
        choices=(
            (CheckoutAction.PAY_LATER, "Comprar depois"),
            (CheckoutAction.PIX, "PIX"),
            (CheckoutAction.ASAAS_CARD, "Cartão"),
        ),
        initial=CheckoutAction.PAY_LATER,
        label="Pagamento dos materiais",
    )

    def __init__(self, *args, owner=None, pending=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.pending = pending
        self.existing_owned_dependent = None
        self.family_plan_available = owner_has_family_plan(owner)
        self.fields["dependent_class_groups"].choices = (
            get_public_class_group_choice_options()
        )
        self.fields["dependent_class_groups"].valid_value = lambda value: True
        self.fields["selected_plan"].choices = [("", "Selecione")] + [
            (build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan.pk), plan.display_name)
            for plan in SubscriptionPlan.objects.filter(
                is_active=True, requires_special_authorization=False,
            ).order_by("display_order", "price")
        ] + [
            (build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, price.pk), price.tier.display_name)
            for price in PlanPrice.objects.filter(
                is_active=True, tier__is_active=True,
            ).select_related("tier").order_by("tier__display_order", "price")
        ]
        self.material_variants = get_material_variants()
        for variant in self.material_variants:
            field_name = build_material_variant_field_name(variant.pk)
            self.fields[field_name] = forms.IntegerField(
                required=False,
                min_value=0,
                max_value=variant.stock_quantity,
                initial=0,
                label=str(variant),
            )
        self._apply_wizard_widget_classes()

    def _apply_wizard_widget_classes(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                continue
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-input form-textarea")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-input form-select")
            else:
                widget.attrs.setdefault("class", "form-input")

    def clean(self):
        cleaned_data = super().clean()
        self._clean_passwords(cleaned_data)
        self._clean_classes(cleaned_data)
        self._clean_martial_art(cleaned_data)
        self._clean_financial_choice(cleaned_data)
        self._clean_card_strategy(cleaned_data)
        self._clean_materials(cleaned_data)
        return cleaned_data

class DependentProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Data de nascimento",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_started_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Início no treino",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_last_graduation_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Última graduação",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    jiu_jitsu_stripes = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        label="Graus",
    )

    class Meta:
        model = Person
        fields = (
            "full_name",
            "birth_date",
            "biological_sex",
            "email",
            "phone",
            "blood_type",
            "allergies",
            "previous_injuries",
            "emergency_contact",
            "martial_art",
            "martial_art_graduation",
            "jiu_jitsu_belt",
            "jiu_jitsu_stripes",
            "martial_art_started_at",
            "martial_art_last_graduation_at",
            "previous_academy",
        )
        labels = {
            "full_name": "Nome completo",
            "biological_sex": "Sexo biológico",
            "email": "E-mail",
            "phone": "Telefone",
            "blood_type": "Tipo sanguíneo",
            "allergies": "Alergias",
            "previous_injuries": "Lesões",
            "emergency_contact": "Contato de emergência",
            "martial_art": "Arte marcial",
            "martial_art_graduation": "Graduação",
            "jiu_jitsu_belt": "Faixa de Jiu Jitsu",
            "previous_academy": "Academia anterior",
        }
        widgets = {
            "allergies": forms.Textarea(attrs={"rows": 3}),
            "previous_injuries": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                continue
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-input form-textarea")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-input form-select")
            else:
                widget.attrs.setdefault("class", "form-input")

    def clean(self):
        cleaned_data = super().clean()
        martial_art = cleaned_data.get("martial_art") or ""
        if martial_art == MartialArt.JIU_JITSU:
            cleaned_data["martial_art_graduation"] = ""
        elif martial_art:
            cleaned_data["jiu_jitsu_belt"] = ""
            cleaned_data["jiu_jitsu_stripes"] = None
        return cleaned_data


