from django.core.exceptions import ValidationError
from django.utils import timezone

from system.constants import (
    ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL,
    ROLE_ALUNO_TITULAR,
    ROLE_RESPONSAVEL_FINANCEIRO,
)
from system.models import EmergencyRecord, GuardianRelationship, StudentProfile, SystemRole, SystemUser
from system.services.auth.cpf import normalize_cpf


def create_or_update_identity(*, cpf, full_name, email="", timezone_name="America/Sao_Paulo"):
    normalized_cpf = normalize_cpf(cpf)
    user = SystemUser.objects.filter(cpf=normalized_cpf).first()
    if user is None:
        return _create_identity(normalized_cpf, full_name, email, timezone_name), True
    _update_identity(user, full_name, email, timezone_name)
    return user, False


def _create_identity(cpf, full_name, email, timezone_name):
    return SystemUser.objects.create_user(
        cpf=cpf,
        password=None,
        full_name=full_name,
        email=email or None,
        timezone=timezone_name,
    )


def _update_identity(user, full_name, email, timezone_name):
    user.full_name = full_name
    user.timezone = timezone_name or user.timezone
    if email:
        user.email = email
    user.save()


def ensure_student_profile(*, user, student_type, birth_date=None, contact_phone="", self_service_access=True):
    profile = StudentProfile.objects.filter(user=user).first()
    if profile and profile.student_type != student_type:
        raise ValidationError({"cpf": "Esta identidade ja possui perfil de aluno incompativel."})
    if profile is None:
        profile = StudentProfile(user=user, student_type=student_type)
    profile.birth_date = birth_date
    profile.contact_phone = contact_phone
    profile.self_service_access = self_service_access
    profile.full_clean()
    profile.save()
    return profile


def ensure_emergency_record(student, payload):
    if not payload.get("emergency_contact_name"):
        return None
    record, _ = EmergencyRecord.objects.get_or_create(student=student)
    _populate_emergency_record(record, payload)
    record.full_clean()
    record.save()
    return record


def _populate_emergency_record(record, payload):
    record.emergency_contact_name = payload["emergency_contact_name"]
    record.emergency_contact_phone = payload["emergency_contact_phone"]
    record.emergency_contact_relationship = payload["emergency_contact_relationship"]
    record.blood_type = payload.get("blood_type", "")
    record.allergies = payload.get("allergies", "")
    record.medications = payload.get("medications", "")
    record.medical_notes = payload.get("medical_notes", "")


def ensure_role(user, role_code):
    role, _ = SystemRole.objects.get_or_create(code=role_code, defaults={"name": role_code.title()})
    user.assign_role(role)
    return role


def ensure_student_roles(student, *, is_holder, self_service_access):
    if is_holder:
        ensure_role(student.user, ROLE_ALUNO_TITULAR)
        return
    if self_service_access:
        ensure_role(student.user, ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL)


def ensure_financial_responsible_role(user):
    ensure_role(user, ROLE_RESPONSAVEL_FINANCEIRO)


def create_guardian_relationship(
    *,
    student,
    responsible_user,
    relationship_type,
    is_primary=True,
    is_financial_responsible=True,
    notes="",
    replace_existing_primary=False,
):
    if replace_existing_primary:
        _close_existing_primary_relationships(student)
    link = GuardianRelationship(
        student=student,
        responsible_user=responsible_user,
        relationship_type=relationship_type,
        is_primary=is_primary,
        is_financial_responsible=is_financial_responsible,
        notes=notes,
    )
    link.full_clean()
    link.save()
    return link


def _close_existing_primary_relationships(student):
    queryset = student.guardian_links.filter(end_date__isnull=True, is_primary=True)
    for link in queryset:
        link.end_date = timezone.localdate()
        link.save(update_fields=["end_date", "updated_at"])
