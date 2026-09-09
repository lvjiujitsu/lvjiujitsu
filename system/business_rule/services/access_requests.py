from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.business_rule.constants import PersonTypeCode, Capability
from system.business_rule.models import (
    AdministrativeAccessRequest,
    AdministrativeAccessRequestStatus,
    OperationalRole,
    Person,
    PersonOperationalRole,
    PortalAccount,
)
from system.business_rule.services.portal_capabilities import ensure_default_operational_roles
from system.business_rule.services.registration import ensure_default_person_types
from system.core.documents import ensure_formatted_cpf


def create_administrative_access_request(
    *,
    origin,
    full_name,
    cpf,
    email,
    phone,
    requested_role_codes,
    justification,
    requester=None,
    grant_full_administrative=False,
    password="",
    request_payload=None,
):
    formatted_cpf = ensure_formatted_cpf(cpf)
    existing_person = requester or Person.objects.filter(cpf=formatted_cpf).first()
    if _has_pending_request(formatted_cpf):
        raise ValidationError("Já existe uma solicitação administrativa pendente para este CPF.")

    requested_codes = _normalize_requested_role_codes(requested_role_codes)
    if not requested_codes and not grant_full_administrative:
        raise ValidationError("Selecione ao menos uma área administrativa solicitada.")

    password_hash = make_password(password) if password else ""
    return AdministrativeAccessRequest.objects.create(
        origin=origin,
        person=existing_person,
        full_name=(full_name or "").strip(),
        cpf=formatted_cpf,
        email=(email or "").strip(),
        phone=(phone or "").strip(),
        requested_role_codes=requested_codes,
        grant_full_administrative=bool(grant_full_administrative),
        justification=(justification or "").strip(),
        request_payload=_normalize_request_payload(request_payload),
        password_hash=password_hash,
    )


@transaction.atomic
def approve_administrative_access_request(
    request_id,
    *,
    approved_by,
    approved_role_ids,
    grant_full_administrative,
    decision_notes="",
):
    access_request = (
        AdministrativeAccessRequest.objects.select_for_update()
        .select_related("person", "approved_person")
        .get(pk=request_id)
    )
    _require_pending(access_request)

    roles = list(OperationalRole.objects.filter(pk__in=approved_role_ids, is_active=True))
    if not roles and not grant_full_administrative:
        raise ValidationError("A aprovação precisa conceder ao menos um papel ou acesso pleno.")

    person = _resolve_or_create_person_for_request(
        access_request,
        grant_full_administrative=grant_full_administrative,
    )
    if grant_full_administrative:
        admin_type = ensure_default_person_types()[PersonTypeCode.ADMINISTRATIVE_ASSISTANT]
        person.person_type = admin_type
        person.is_active = True
        person.save(update_fields=("person_type", "is_active", "updated_at"))

    for role in roles:
        PersonOperationalRole.objects.update_or_create(
            person=person,
            role=role,
            class_group=None,
            defaults={
                "is_active": True,
                "notes": "Aprovado por solicitação administrativa.",
            },
        )

    access_request.status = AdministrativeAccessRequestStatus.APPROVED
    access_request.approved_person = person
    access_request.decided_by = approved_by
    access_request.decided_at = timezone.now()
    access_request.approved_role_codes = [role.code for role in roles]
    access_request.grant_full_administrative = bool(grant_full_administrative)
    access_request.decision_notes = (decision_notes or "").strip()
    access_request.save(
        update_fields=(
            "status",
            "approved_person",
            "decided_by",
            "decided_at",
            "approved_role_codes",
            "grant_full_administrative",
            "decision_notes",
            "updated_at",
        )
    )
    return access_request


@transaction.atomic
def reject_administrative_access_request(request_id, *, rejected_by, decision_notes):
    access_request = AdministrativeAccessRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(access_request)
    if not (decision_notes or "").strip():
        raise ValidationError("Informe o motivo da recusa.")
    access_request.status = AdministrativeAccessRequestStatus.REJECTED
    access_request.decided_by = rejected_by
    access_request.decided_at = timezone.now()
    access_request.decision_notes = decision_notes.strip()
    access_request.save(
        update_fields=(
            "status",
            "decided_by",
            "decided_at",
            "decision_notes",
            "updated_at",
        )
    )
    return access_request


@transaction.atomic
def cancel_administrative_access_request(request_id, *, canceled_by, decision_notes=""):
    access_request = AdministrativeAccessRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(access_request)
    access_request.status = AdministrativeAccessRequestStatus.CANCELED
    access_request.decided_by = canceled_by
    access_request.decided_at = timezone.now()
    access_request.decision_notes = (decision_notes or "Cancelada pelo solicitante.").strip()
    access_request.save(
        update_fields=(
            "status",
            "decided_by",
            "decided_at",
            "decision_notes",
            "updated_at",
        )
    )
    return access_request


ADMINISTRATIVE_ACCESS_DECISION_CAPABILITIES = (
    Capability.MANAGE_PEOPLE,
    Capability.MANAGE_ACADEMY,
)


def can_decide_administrative_access_request(request_capabilities):
    return bool(set(ADMINISTRATIVE_ACCESS_DECISION_CAPABILITIES) & set(request_capabilities))


def can_cancel_administrative_access_request(access_request, *, actor, actor_capabilities):
    if can_decide_administrative_access_request(actor_capabilities):
        return True
    return bool(actor is not None and actor.cpf == access_request.cpf)


def get_administrative_access_requests_for_person(person, limit=5):
    if person is None:
        return []
    return list(
        AdministrativeAccessRequest.objects.filter(cpf=person.cpf)
        .select_related("approved_person", "decided_by")
        .order_by("-created_at")[:limit]
    )


def get_pending_administrative_access_request_count():
    return AdministrativeAccessRequest.objects.filter(
        status=AdministrativeAccessRequestStatus.PENDING,
    ).count()


def _resolve_or_create_person_for_request(access_request, *, grant_full_administrative):
    formatted_cpf = access_request.cpf
    person = access_request.person or Person.objects.filter(cpf=formatted_cpf).first()
    if person is None:
        person_type = None
        if grant_full_administrative:
            person_type = ensure_default_person_types()[PersonTypeCode.ADMINISTRATIVE_ASSISTANT]
        elif (access_request.request_payload or {}).get("training_intent") == "student":
            person_type = ensure_default_person_types()[PersonTypeCode.STUDENT]
        person = Person.objects.create(
            full_name=access_request.full_name,
            cpf=formatted_cpf,
            email=access_request.email,
            phone=access_request.phone,
            person_type=person_type,
            is_active=True,
        )
    else:
        changed_fields = []
        if not person.is_active:
            person.is_active = True
            changed_fields.append("is_active")
        for field_name in ("email", "phone"):
            if not getattr(person, field_name) and getattr(access_request, field_name):
                setattr(person, field_name, getattr(access_request, field_name))
                changed_fields.append(field_name)
        if changed_fields:
            changed_fields.append("updated_at")
            person.save(update_fields=tuple(changed_fields))

    _ensure_portal_account(person, access_request.password_hash)
    return person


def _ensure_portal_account(person, password_hash):
    account = getattr(person, "access_account", None)
    if account is not None:
        if not account.is_active:
            account.is_active = True
            account.save(update_fields=("is_active", "updated_at"))
        return account
    return PortalAccount.objects.create(
        person=person,
        password_hash=password_hash or make_password(None),
        is_active=True,
    )


def _normalize_requested_role_codes(role_codes):
    ensure_default_operational_roles()
    codes = []
    valid_codes = set(
        OperationalRole.objects.filter(is_active=True).values_list("code", flat=True)
    )
    for code in role_codes or []:
        if code in valid_codes and code not in codes:
            codes.append(code)
    return codes


def _normalize_request_payload(payload):
    payload = payload or {}
    training_intent = payload.get("training_intent") or "none"
    compensation_preference = payload.get("compensation_preference") or "none"
    allowed_training = {"none", "student"}
    allowed_compensation = {"none", "barter", "pix"}
    pix_key_type = (payload.get("pix_key_type") or "").strip()
    pix_key = (payload.get("pix_key") or "").strip()
    if compensation_preference == "pix" and (not pix_key_type or not pix_key):
        raise ValidationError("Informe tipo e chave PIX para solicitação com recebimento por PIX.")
    return {
        "training_intent": training_intent if training_intent in allowed_training else "none",
        "compensation_preference": (
            compensation_preference
            if compensation_preference in allowed_compensation
            else "none"
        ),
        "pix_key_type": pix_key_type,
        "pix_key": pix_key,
    }


def _has_pending_request(cpf):
    return AdministrativeAccessRequest.objects.filter(
        cpf=cpf,
        status=AdministrativeAccessRequestStatus.PENDING,
    ).exists()


def _require_pending(access_request):
    if access_request.status != AdministrativeAccessRequestStatus.PENDING:
        raise ValidationError("A solicitação já foi decidida.")
