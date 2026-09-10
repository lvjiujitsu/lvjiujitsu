from django import forms

from system.core.dates import PT_BR_DATE_INPUT_FORMATS
from system.business_rule.models import BiologicalSex, BloodType, JiuJitsuBelt
from system.business_rule.forms.registration_common import (
    MARTIAL_ART_EXPERIENCE_CHOICES,
    MARTIAL_ART_MODALITY_CHOICES,
)
from system.business_rule.services.registration import get_kinship_choices

SELECT_PLACEHOLDER = [("", "Selecione")]


def identity_fields(*, birthdate=True):
    fields = {
        "name": forms.CharField(required=False, max_length=255),
        "cpf": forms.CharField(required=False, max_length=14),
        "biological_sex": forms.ChoiceField(
            required=False,
            choices=SELECT_PLACEHOLDER + list(BiologicalSex.choices),
        ),
        "phone": forms.CharField(required=False, max_length=20),
        "email": forms.EmailField(required=False),
        "password": forms.CharField(required=False, strip=False),
        "password_confirm": forms.CharField(required=False, strip=False),
    }
    if birthdate:
        fields["birthdate"] = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    return fields


def health_fields():
    return {
        "blood_type": forms.ChoiceField(
            required=False,
            choices=SELECT_PLACEHOLDER + list(BloodType.choices),
        ),
        "allergies": forms.CharField(required=False),
        "injuries": forms.CharField(required=False),
        "emergency_contact": forms.CharField(required=False, max_length=255),
    }


def martial_background_fields():
    return {
        "has_martial_art": forms.ChoiceField(
            required=False,
            choices=MARTIAL_ART_EXPERIENCE_CHOICES,
        ),
        "martial_art": forms.ChoiceField(
            required=False,
            choices=MARTIAL_ART_MODALITY_CHOICES,
        ),
        "martial_art_graduation": forms.CharField(required=False, max_length=120),
        "jiu_jitsu_belt": forms.ChoiceField(
            required=False,
            choices=SELECT_PLACEHOLDER + list(JiuJitsuBelt.choices),
        ),
        "jiu_jitsu_stripes": forms.IntegerField(required=False, min_value=0, max_value=4),
        "martial_art_started_at": forms.DateField(
            required=False, input_formats=PT_BR_DATE_INPUT_FORMATS
        ),
        "martial_art_last_graduation_at": forms.DateField(
            required=False, input_formats=PT_BR_DATE_INPUT_FORMATS
        ),
        "previous_academy": forms.CharField(required=False, max_length=200),
    }


def address_fields():
    return {
        "postal_code": forms.CharField(required=False, max_length=9),
        "address": forms.CharField(required=False, max_length=255),
        "address_number": forms.CharField(required=False, max_length=20),
        "address_complement": forms.CharField(required=False, max_length=100),
        "address_neighborhood": forms.CharField(required=False, max_length=100),
        "city": forms.CharField(required=False, max_length=100),
    }


def kinship_fields():
    return {
        "kinship_type": forms.ChoiceField(
            required=False,
            choices=SELECT_PLACEHOLDER + list(get_kinship_choices()),
        ),
        "kinship_other_label": forms.CharField(required=False, max_length=80),
    }


def person_fields_mixin(
    prefix,
    *,
    birthdate=True,
    class_groups=False,
    address=False,
    kinship=False,
):
    fields = identity_fields(birthdate=birthdate)
    if class_groups:
        fields["class_groups"] = forms.MultipleChoiceField(required=False)
    fields.update(health_fields())
    if kinship:
        fields.update(kinship_fields())
    fields.update(martial_background_fields())
    if address:
        fields.update(address_fields())
    attrs = {f"{prefix}_{name}": field for name, field in fields.items()}
    return type(f"{prefix.title()}FieldsMixin", (forms.Form,), attrs)
