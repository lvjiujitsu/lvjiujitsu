from django.db import transaction

from system.constants import ROLE_ALUNO_TITULAR
from system.models import ConsentTerm, StudentProfile
from system.services.lgpd.records import record_term_acceptances
from system.services.students.registry import (
    create_guardian_relationship,
    create_or_update_identity,
    ensure_emergency_record,
    ensure_financial_responsible_role,
    ensure_role,
    ensure_student_profile,
    ensure_student_roles,
)


@transaction.atomic
def submit_household_onboarding(*, holder_data, dependents_data, accepted_term_ids, request):
    holder_user, _ = _create_holder_identity(holder_data)
    responsible_user = _resolve_financial_responsible(holder_data, holder_user)
    holder_student = _create_holder_student(holder_data, holder_user, responsible_user)
    dependents = _create_dependents(dependents_data, responsible_user)
    accepted_terms = _load_accepted_terms(accepted_term_ids)
    _register_terms(request, responsible_user, accepted_terms)
    return {
        "holder_user": holder_user,
        "responsible_user": responsible_user,
        "holder_student": holder_student,
        "dependents": dependents,
    }


def _create_holder_identity(holder_data):
    return create_or_update_identity(
        cpf=holder_data["holder_cpf"],
        full_name=holder_data["holder_full_name"],
        email=holder_data.get("holder_email", ""),
        timezone_name=holder_data.get("holder_timezone", "America/Sao_Paulo"),
    )


def _resolve_financial_responsible(holder_data, holder_user):
    if holder_data["responsible_same_as_holder"]:
        ensure_financial_responsible_role(holder_user)
        return holder_user
    responsible_user, _ = create_or_update_identity(
        cpf=holder_data["responsible_cpf"],
        full_name=holder_data["responsible_full_name"],
        email=holder_data.get("responsible_email", ""),
        timezone_name=holder_data.get("holder_timezone", "America/Sao_Paulo"),
    )
    ensure_financial_responsible_role(responsible_user)
    return responsible_user


def _create_holder_student(holder_data, holder_user, responsible_user):
    student = ensure_student_profile(
        user=holder_user,
        student_type=StudentProfile.TYPE_HOLDER,
        birth_date=holder_data.get("holder_birth_date"),
        contact_phone=holder_data.get("holder_contact_phone", ""),
        self_service_access=True,
    )
    ensure_role(holder_user, ROLE_ALUNO_TITULAR)
    create_guardian_relationship(
        student=student,
        responsible_user=responsible_user,
        relationship_type=_holder_relationship_type(holder_user, responsible_user),
        replace_existing_primary=True,
    )
    ensure_emergency_record(student, holder_data)
    return student


def _holder_relationship_type(holder_user, responsible_user):
    if holder_user.pk == responsible_user.pk:
        return "self"
    return "guardian"


def _create_dependents(dependents_data, responsible_user):
    dependents = []
    for payload in dependents_data:
        if not payload.get("cpf"):
            continue
        dependents.append(_create_single_dependent(payload, responsible_user))
    return dependents


def _create_single_dependent(payload, responsible_user):
    dependent_user, _ = create_or_update_identity(
        cpf=payload["cpf"],
        full_name=payload["full_name"],
        email=payload.get("email", ""),
        timezone_name=payload.get("timezone", "America/Sao_Paulo"),
    )
    student = ensure_student_profile(
        user=dependent_user,
        student_type=StudentProfile.TYPE_DEPENDENT,
        birth_date=payload.get("birth_date"),
        contact_phone=payload.get("contact_phone", ""),
        self_service_access=payload.get("has_own_credential", False),
    )
    ensure_student_roles(
        student,
        is_holder=False,
        self_service_access=payload.get("has_own_credential", False),
    )
    create_guardian_relationship(
        student=student,
        responsible_user=responsible_user,
        relationship_type=payload["relationship_type"],
        replace_existing_primary=True,
    )
    ensure_emergency_record(student, payload)
    return student


def _load_accepted_terms(accepted_term_ids):
    return list(ConsentTerm.objects.filter(pk__in=accepted_term_ids, is_active=True))


def _register_terms(request, user, accepted_terms):
    record_term_acceptances(
        request=request,
        user=user,
        terms=accepted_terms,
        context="onboarding",
    )
