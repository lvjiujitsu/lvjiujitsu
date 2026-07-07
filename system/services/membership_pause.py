import logging
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.constants import PortalCapability
from system.models.membership import (
    MembershipPauseRequest,
    MembershipPauseRequestKind,
    MembershipPauseRequestStatus,
)
from system.services.plan_change import is_plan_change_locked

logger = logging.getLogger(__name__)

SELF_SERVICE_ANNUAL_QUOTA_DAYS = 30

PAUSE_DECISION_CAPABILITIES = (
    PortalCapability.MANAGE_PEOPLE,
    PortalCapability.MANAGE_ACADEMY,
)


def _duration_days(start_date, end_date):
    return (end_date - start_date).days + 1


def _membership_year_window(membership, reference_date):
    anchor_dt = membership.activated_at or membership.created_at
    anchor = timezone.localtime(anchor_dt).date()

    def _safe_replace(base_date, year):
        try:
            return base_date.replace(year=year)
        except ValueError:
            return base_date.replace(year=year, day=28)

    anniversary = _safe_replace(anchor, reference_date.year)
    if anniversary > reference_date:
        anniversary = _safe_replace(anchor, reference_date.year - 1)
    next_anniversary = _safe_replace(anchor, anniversary.year + 1)
    return anniversary, next_anniversary


def _self_service_days_used(membership, reference_date, *, exclude_pk=None):
    window_start, window_end = _membership_year_window(membership, reference_date)
    requests = membership.pause_requests.filter(
        kind=MembershipPauseRequestKind.SELF_SERVICE,
        status__in=(MembershipPauseRequestStatus.PENDING, MembershipPauseRequestStatus.APPROVED),
        requested_start_date__gte=window_start,
        requested_start_date__lt=window_end,
    )
    if exclude_pk is not None:
        requests = requests.exclude(pk=exclude_pk)
    return sum(_duration_days(r.requested_start_date, r.requested_end_date) for r in requests)


def _has_overlapping_request(membership, start_date, end_date):
    return membership.pause_requests.filter(
        status__in=(MembershipPauseRequestStatus.PENDING, MembershipPauseRequestStatus.APPROVED),
        requested_start_date__lte=end_date,
        requested_end_date__gte=start_date,
    ).exists()


def create_pause_request(membership, *, kind, start_date, end_date, reason_note=""):
    if kind not in MembershipPauseRequestKind.values:
        raise ValidationError("Tipo de pausa inválido.")
    if end_date < start_date:
        raise ValidationError("A data final não pode ser anterior à data inicial.")
    if _has_overlapping_request(membership, start_date, end_date):
        raise ValidationError("Já existe uma pausa pendente ou aprovada nesse período.")

    if kind == MembershipPauseRequestKind.SELF_SERVICE:
        if is_plan_change_locked(membership):
            raise ValidationError(
                "Trancamento sem atestado só é permitido fora do período de carência do plano."
            )
        duration = _duration_days(start_date, end_date)
        used = _self_service_days_used(membership, start_date)
        if used + duration > SELF_SERVICE_ANNUAL_QUOTA_DAYS:
            remaining = max(SELF_SERVICE_ANNUAL_QUOTA_DAYS - used, 0)
            raise ValidationError(
                "Cota de trancamento excedida — restam "
                f"{remaining} dia(s) disponíveis neste ano de matrícula."
            )

    return MembershipPauseRequest.objects.create(
        membership=membership,
        kind=kind,
        requested_start_date=start_date,
        requested_end_date=end_date,
        reason_note=(reason_note or "").strip(),
    )


def _pause_stripe_collection(membership, pause_request):
    from system.services.stripe_admin_actions import StripeAdminActionError, _get_client

    client = _get_client()
    resumes_at_date = pause_request.requested_end_date + timedelta(days=1)
    resumes_at_dt = timezone.make_aware(datetime.combine(resumes_at_date, datetime.min.time()))
    try:
        client.Subscription.modify(
            membership.stripe_subscription_id,
            pause_collection={
                "behavior": "void",
                "resumes_at": int(resumes_at_dt.timestamp()),
            },
        )
    except Exception as exc:
        logger.exception("Falha ao pausar cobrança Stripe da assinatura %s", membership.pk)
        raise StripeAdminActionError(str(exc)) from exc


@transaction.atomic
def approve_pause_request(request_id, *, approved_by, decision_notes=""):
    pause_request = (
        MembershipPauseRequest.objects.select_for_update()
        .select_related("membership")
        .get(pk=request_id)
    )
    _require_pending(pause_request)

    membership = pause_request.membership
    duration = pause_request.duration_days

    if membership.stripe_subscription_id:
        _pause_stripe_collection(membership, pause_request)

    update_fields = ["updated_at"]
    if membership.current_period_end:
        membership.current_period_end = membership.current_period_end + timedelta(days=duration)
        update_fields.append("current_period_end")

    if pause_request.kind == MembershipPauseRequestKind.MEDICAL:
        membership.fidelity_extension_days = (membership.fidelity_extension_days or 0) + duration
        update_fields.append("fidelity_extension_days")

    if len(update_fields) > 1:
        membership.save(update_fields=update_fields)

    pause_request.status = MembershipPauseRequestStatus.APPROVED
    pause_request.decided_by = approved_by
    pause_request.decided_at = timezone.now()
    pause_request.decision_notes = (decision_notes or "").strip()
    pause_request.save(
        update_fields=["status", "decided_by", "decided_at", "decision_notes", "updated_at"]
    )
    return pause_request


@transaction.atomic
def reject_pause_request(request_id, *, rejected_by, decision_notes):
    pause_request = MembershipPauseRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(pause_request)
    if not (decision_notes or "").strip():
        raise ValidationError("Informe o motivo da recusa.")
    pause_request.status = MembershipPauseRequestStatus.REJECTED
    pause_request.decided_by = rejected_by
    pause_request.decided_at = timezone.now()
    pause_request.decision_notes = decision_notes.strip()
    pause_request.save(
        update_fields=["status", "decided_by", "decided_at", "decision_notes", "updated_at"]
    )
    return pause_request


@transaction.atomic
def cancel_pause_request(request_id, *, canceled_by, decision_notes=""):
    pause_request = MembershipPauseRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(pause_request)
    pause_request.status = MembershipPauseRequestStatus.CANCELED
    pause_request.decided_by = canceled_by
    pause_request.decided_at = timezone.now()
    pause_request.decision_notes = (decision_notes or "Cancelada pelo solicitante.").strip()
    pause_request.save(
        update_fields=["status", "decided_by", "decided_at", "decision_notes", "updated_at"]
    )
    return pause_request


def get_self_service_quota_summary(membership, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    used = _self_service_days_used(membership, reference_date)
    window_start, window_end = _membership_year_window(membership, reference_date)
    return {
        "used_days": used,
        "remaining_days": max(SELF_SERVICE_ANNUAL_QUOTA_DAYS - used, 0),
        "quota_days": SELF_SERVICE_ANNUAL_QUOTA_DAYS,
        "window_start": window_start,
        "window_end": window_end,
    }


def can_decide_pause_request(request_capabilities):
    return bool(set(PAUSE_DECISION_CAPABILITIES) & set(request_capabilities))


def _require_pending(pause_request):
    if pause_request.status != MembershipPauseRequestStatus.PENDING:
        raise ValidationError("A solicitação já foi decidida.")
