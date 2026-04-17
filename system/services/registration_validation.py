from datetime import datetime

from system.models import MartialArt, Person
from system.models.class_membership import get_class_group_eligibility_error
from system.services.registration import resolve_class_groups
from system.utils import ensure_formatted_cpf


STEP_REQUIRED_FIELDS = {
    "holder": (
        "holder_name",
        "holder_cpf",
        "holder_birthdate",
        "holder_biological_sex",
        "holder_password",
        "holder_password_confirm",
    ),
    "holder_titular": (
        "holder_name",
        "holder_cpf",
        "holder_birthdate",
        "holder_biological_sex",
        "holder_password",
        "holder_password_confirm",
    ),
    "guardian": (
        "guardian_name",
        "guardian_cpf",
        "guardian_password",
        "guardian_password_confirm",
    ),
    "dependent": (
        "dependent_name",
        "dependent_cpf",
        "dependent_birthdate",
        "dependent_biological_sex",
        "dependent_kinship_type",
        "dependent_password",
        "dependent_password_confirm",
    ),
    "student": (
        "student_name",
        "student_cpf",
        "student_birthdate",
        "student_biological_sex",
        "student_kinship_type",
        "student_password",
        "student_password_confirm",
    ),
    "other": (
        "other_name",
        "other_cpf",
        "other_birthdate",
        "other_password",
        "other_password_confirm",
    ),
}

PASSWORD_PAIRS = {
    "holder": ("holder_password", "holder_password_confirm", "As senhas de aluno titular não coincidem."),
    "holder_titular": ("holder_password", "holder_password_confirm", "As senhas de aluno titular não coincidem."),
    "guardian": ("guardian_password", "guardian_password_confirm", "As senhas de responsável não coincidem."),
    "dependent": ("dependent_password", "dependent_password_confirm", "As senhas de dependente não coincidem."),
    "student": ("student_password", "student_password_confirm", "As senhas de dependente não coincidem."),
    "other": ("other_password", "other_password_confirm", "As senhas de cadastro não coincidem."),
}

STEP_PREFIX = {
    "holder": "holder",
    "holder_titular": "holder",
    "holder_medical": "holder",
    "holder_classes": "holder",
    "guardian": "guardian",
    "dependent": "dependent",
    "dependent_medical": "dependent",
    "dependent_classes": "dependent",
    "student": "student",
    "student_medical": "student",
    "student_classes": "student",
    "other": "other",
}


def validate_registration_step(data):
    step_key = _get(data, "step_key")
    errors = {}
    _validate_required_fields(data, step_key, errors)
    _validate_password_pair(data, step_key, errors)
    _validate_cpf(data, step_key, errors)
    _validate_kinship(data, step_key, errors)
    _validate_martial_background(data, step_key, errors)
    _validate_class_groups(data, step_key, errors)
    return errors


def _validate_required_fields(data, step_key, errors):
    for field_name in STEP_REQUIRED_FIELDS.get(step_key, ()):
        if not _get(data, field_name):
            errors.setdefault(field_name, "Campo obrigatório.")


def _validate_password_pair(data, step_key, errors):
    pair = PASSWORD_PAIRS.get(step_key)
    if not pair:
        return
    password_field, confirm_field, message = pair
    password = _get(data, password_field)
    confirm_password = _get(data, confirm_field)
    if password and confirm_password and password != confirm_password:
        errors.setdefault(confirm_field, message)


def _validate_cpf(data, step_key, errors):
    prefix = STEP_PREFIX.get(step_key)
    if not prefix:
        return
    field_name = f"{prefix}_cpf"
    value = _get(data, field_name)
    if not value:
        return
    try:
        formatted = ensure_formatted_cpf(value)
    except ValueError as exc:
        errors.setdefault(field_name, str(exc))
        return
    if Person.objects.filter(cpf=formatted).exists():
        errors.setdefault(field_name, "CPF já cadastrado no sistema.")


def _validate_kinship(data, step_key, errors):
    prefix = STEP_PREFIX.get(step_key)
    if prefix not in ("dependent", "student"):
        return
    kinship_type = _get(data, f"{prefix}_kinship_type")
    other_label = _get(data, f"{prefix}_kinship_other_label")
    if kinship_type == "other" and not other_label:
        errors.setdefault(f"{prefix}_kinship_other_label", "Informe o grau de parentesco.")


def _validate_martial_background(data, step_key, errors):
    prefix = STEP_PREFIX.get(step_key)
    if step_key not in ("holder_medical", "dependent_medical", "student_medical"):
        return
    martial_art = _get(data, f"{prefix}_martial_art")
    graduation = _get(data, f"{prefix}_martial_art_graduation")
    belt = _get(data, f"{prefix}_jiu_jitsu_belt")
    if martial_art and martial_art != MartialArt.JIU_JITSU and not graduation:
        errors.setdefault(
            f"{prefix}_martial_art_graduation",
            "Informe a graduação/nível na arte marcial.",
        )
    if martial_art == MartialArt.JIU_JITSU and not belt:
        errors.setdefault(f"{prefix}_jiu_jitsu_belt", "Informe a faixa de Jiu Jitsu.")


def _validate_class_groups(data, step_key, errors):
    prefix = STEP_PREFIX.get(step_key)
    if step_key not in ("holder_classes", "dependent_classes", "student_classes"):
        return
    field_name = f"{prefix}_class_groups"
    raw_group_ids = _getlist(data, field_name)
    class_groups = resolve_class_groups(raw_group_ids)
    if not class_groups:
        errors.setdefault(field_name, "Selecione ao menos uma turma.")
        return

    birth_date = _parse_birthdate(_get(data, f"{prefix}_birthdate"))
    biological_sex = _get(data, f"{prefix}_biological_sex")
    for class_group in class_groups:
        error = get_class_group_eligibility_error(
            birth_date=birth_date,
            biological_sex=biological_sex,
            class_group=class_group,
        )
        if error:
            errors.setdefault(field_name, error)
            return


def _parse_birthdate(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


def _get(data, key):
    value = data.get(key, "")
    return value.strip() if isinstance(value, str) else value


def _getlist(data, key):
    if hasattr(data, "getlist"):
        return data.getlist(key)
    value = data.get(key, [])
    return value if isinstance(value, list) else [value]
