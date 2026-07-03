from django import forms

from system.constants import CheckoutAction
from system.forms.registration_forms import (
    MARTIAL_ART_EXPERIENCE_CHOICES,
    MARTIAL_ART_EXPERIENCE_YES,
    MARTIAL_ART_MODALITY_CHOICES,
)
from system.models import (
    BiologicalSex,
    BloodType,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PreRegistration,
    PreRegistrationStatus,
    ProductVariant,
    SubscriptionPlan,
)
from system.models.class_membership import get_class_group_eligibility_error
from system.services.class_overview import get_public_class_group_choice_options
from system.services.membership import get_active_membership
from system.services.registration import get_kinship_choices, resolve_class_groups
from system.services.registration_checkout import resolve_selected_product_items
from system.utils import ensure_formatted_cpf


DEPENDENT_FLOW_KIND = "dependent_addition"
MATERIAL_FIELD_PREFIX = "material_variant_"


class DependentRegistrationForm(forms.Form):
    dependent_name = forms.CharField(max_length=255, label="Nome completo")
    dependent_cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(
            attrs={"inputmode": "numeric", "maxlength": "14", "placeholder": "000.000.000-00", "autocomplete": "off"}
        ),
    )
    dependent_birthdate = forms.DateField(
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
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
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Início no treino",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    dependent_martial_art_last_graduation_at = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Última graduação",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    dependent_previous_academy = forms.CharField(
        required=False,
        max_length=200,
        label="Academia anterior",
    )
    use_family_plan = forms.BooleanField(required=False, label="Usar plano familiar")
    selected_plan = forms.ChoiceField(required=False, label="Plano")
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
        self.family_plan_available = _owner_has_family_plan(owner)
        self.fields["dependent_class_groups"].choices = (
            get_public_class_group_choice_options()
        )
        self.fields["dependent_class_groups"].valid_value = lambda value: True
        self.fields["selected_plan"].choices = [("", "Selecione")] + [
            (plan.pk, plan.display_name)
            for plan in SubscriptionPlan.objects.filter(
                is_active=True, requires_special_authorization=False,
            ).order_by("display_order", "price")
        ]
        self.material_variants = _get_material_variants()
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

    def clean_dependent_cpf(self):
        value = self.cleaned_data.get("dependent_cpf")
        try:
            formatted = ensure_formatted_cpf(value)
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error
        active_person = Person.objects.filter(cpf=formatted, is_active=True).first()
        if active_person is not None:
            if self._is_owned_dependent(active_person):
                self.existing_owned_dependent = active_person
                return formatted
            raise forms.ValidationError("Já existe uma pessoa ativa com este CPF.")
        if self._has_pending_pre_registration_for_cpf(formatted):
            raise forms.ValidationError(
                "Já existe um pré-cadastro pendente para este CPF."
            )
        return formatted

    def clean(self):
        cleaned_data = super().clean()
        self._clean_passwords(cleaned_data)
        self._clean_classes(cleaned_data)
        self._clean_martial_art(cleaned_data)
        self._clean_financial_choice(cleaned_data)
        self._clean_materials(cleaned_data)
        return cleaned_data

    def _is_owned_dependent(self, person):
        if self.owner is None:
            return False
        return PersonRelationship.objects.filter(
            source_person=self.owner,
            target_person=person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        ).exists()

    def _has_pending_pre_registration_for_cpf(self, cpf):
        if self.owner is None:
            return False
        queryset = PreRegistration.objects.filter(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            status__in=(
                PreRegistrationStatus.DRAFT,
                PreRegistrationStatus.AWAITING_PAYMENT,
                PreRegistrationStatus.PAYMENT_CONFIRMED,
            ),
        )
        if self.pending is not None:
            queryset = queryset.exclude(pk=self.pending.pk)
        for pre_registration in queryset.only("pk", "form_snapshot"):
            snapshot = pre_registration.form_snapshot or {}
            if snapshot.get("flow_kind") != DEPENDENT_FLOW_KIND:
                continue
            if snapshot.get("owner_person_id") != self.owner.pk:
                continue
            if snapshot.get("dependent_cpf") == cpf:
                return True
        return False

    def _clean_passwords(self, cleaned_data):
        password = cleaned_data.get("dependent_password")
        confirmation = cleaned_data.get("dependent_password_confirm")
        if password and len(password) < 8:
            self.add_error("dependent_password", "Use no mínimo 8 caracteres.")
        if password and confirmation and password != confirmation:
            self.add_error("dependent_password_confirm", "As senhas não conferem.")

    def _clean_classes(self, cleaned_data):
        values = cleaned_data.get("dependent_class_groups") or []
        class_groups = resolve_class_groups(values)
        if not class_groups:
            self.add_error("dependent_class_groups", "Selecione pelo menos uma turma.")
            cleaned_data["resolved_class_groups"] = []
            return
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=cleaned_data.get("dependent_birthdate"),
                biological_sex=cleaned_data.get("dependent_biological_sex") or "",
                class_group=class_group,
            )
            if error:
                self.add_error("dependent_class_groups", error)
                break
        cleaned_data["resolved_class_groups"] = class_groups

    def _clean_martial_art(self, cleaned_data):
        has_martial_art = cleaned_data.get("dependent_has_martial_art") or ""
        martial_art = cleaned_data.get("dependent_martial_art") or ""
        if martial_art and not has_martial_art:
            has_martial_art = MARTIAL_ART_EXPERIENCE_YES
        cleaned_data["dependent_has_martial_art"] = has_martial_art
        if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
            cleaned_data["dependent_martial_art"] = ""
            cleaned_data["dependent_martial_art_graduation"] = ""
            cleaned_data["dependent_jiu_jitsu_belt"] = ""
            cleaned_data["dependent_jiu_jitsu_stripes"] = None
            return
        if not martial_art:
            self.add_error("dependent_martial_art", "Informe a arte marcial.")
            return
        if martial_art == MartialArt.JIU_JITSU:
            if not cleaned_data.get("dependent_jiu_jitsu_belt"):
                self.add_error(
                    "dependent_jiu_jitsu_belt",
                    "Informe a faixa de Jiu Jitsu.",
                )
            cleaned_data["dependent_martial_art_graduation"] = ""
        elif not cleaned_data.get("dependent_martial_art_graduation"):
            self.add_error(
                "dependent_martial_art_graduation",
                "Informe a graduação atual.",
            )
            cleaned_data["dependent_jiu_jitsu_belt"] = ""
            cleaned_data["dependent_jiu_jitsu_stripes"] = None

    def _clean_financial_choice(self, cleaned_data):
        if cleaned_data.get("use_family_plan"):
            if not self.family_plan_available:
                self.add_error(
                    "use_family_plan",
                    "Não há plano familiar ativo para cobrir este dependente.",
                )
            return
        plan_id = cleaned_data.get("selected_plan")
        if not plan_id:
            self.add_error("selected_plan", "Selecione um plano para o dependente.")
            return
        plan = SubscriptionPlan.objects.filter(pk=plan_id, is_active=True).first()
        if plan is None:
            self.add_error("selected_plan", "Selecione um plano válido.")
            return
        cleaned_data["selected_plan_obj"] = plan
        if not cleaned_data.get("checkout_action"):
            cleaned_data["checkout_action"] = CheckoutAction.PAY_LATER

    def _clean_materials(self, cleaned_data):
        selected = []
        for variant in self.material_variants:
            quantity = cleaned_data.get(build_material_variant_field_name(variant.pk)) or 0
            if quantity > 0:
                selected.append({"variant_id": variant.pk, "quantity": quantity})
        cleaned_data["selected_products_payload"] = selected
        cleaned_data["selected_product_items"] = []
        if not selected:
            cleaned_data["materials_checkout_action"] = CheckoutAction.PAY_LATER
            return
        try:
            cleaned_data["selected_product_items"] = resolve_selected_product_items(selected)
        except ValueError as error:
            self.add_error("materials_checkout_action", str(error))
            return
        if cleaned_data.get("materials_checkout_action") not in {
            CheckoutAction.PIX,
            CheckoutAction.ASAAS_CARD,
        }:
            self.add_error(
                "materials_checkout_action",
                "Escolha PIX ou cartão para comprar os materiais agora.",
            )


class DependentProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Data de nascimento",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_started_at = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Início no treino",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_last_graduation_at = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
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


def _owner_has_family_plan(owner):
    membership = get_active_membership(owner)
    return bool(membership and membership.plan and membership.plan.is_family_plan)


def build_material_variant_field_name(variant_id):
    return f"{MATERIAL_FIELD_PREFIX}{variant_id}"


def _get_material_variants():
    return list(
        ProductVariant.objects.select_related("product", "product__category")
        .filter(
            is_active=True,
            stock_quantity__gt=0,
            product__is_active=True,
            product__category__is_active=True,
        )
        .order_by(
            "product__category__display_order",
            "product__category__display_name",
            "product__display_name",
            "color",
            "size",
            "pk",
        )
    )
