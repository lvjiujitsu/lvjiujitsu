from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import AcademyConfiguration, AttendanceAttempt, AttendanceQrToken, ClassReservation, PhysicalAttendance, StudentProfile


@transaction.atomic
def create_class_reservation(*, student, session):
    _validate_reservation_eligibility(student, session)
    _validate_capacity(session)
    reservation = ClassReservation(student=student, session=session)
    reservation.full_clean()
    reservation.save()
    return reservation


def build_precheck_result(*, student, session):
    validators = (
        _validate_student_status,
        _validate_session_window,
        _validate_reservation_requirement,
    )
    for validator in validators:
        result = validator(student, session)
        if result["allowed"]:
            continue
        return result
    return {"allowed": True, "reason": "ok", "message": "Aluno elegivel para abrir a camera."}


def generate_session_qr_token(*, session, actor):
    window_result = _validate_session_window(None, session)
    if not window_result["allowed"]:
        raise ValidationError(window_result["message"])
    configuration = AcademyConfiguration.objects.get()
    return AttendanceQrToken.issue(
        session=session,
        generated_by=actor,
        ttl_seconds=configuration.qr_code_ttl_seconds,
    )


def register_qr_attendance(*, student, session, token_value, actor):
    if PhysicalAttendance.objects.filter(student=student, session=session).exists():
        _record_attempt(student, session, AttendanceAttempt.STATUS_DUPLICATE, "Presenca ja registrada.", token_value)
        raise ValidationError("Presenca ja registrada.")
    precheck = build_precheck_result(student=student, session=session)
    if not precheck["allowed"]:
        _record_attempt(student, session, AttendanceAttempt.STATUS_DENIED, precheck["message"], token_value)
        raise ValidationError(precheck["message"])
    try:
        qr_token = _get_valid_qr_token(session, token_value)
    except ValidationError as exc:
        _record_attempt(student, session, AttendanceAttempt.STATUS_DENIED, str(exc), token_value)
        raise
    reservation = _get_active_reservation(student, session)
    with transaction.atomic():
        attendance = PhysicalAttendance.objects.create(
            student=student,
            session=session,
            reservation=reservation,
            checkin_method=PhysicalAttendance.METHOD_QR,
            recorded_by=actor,
        )
        _consume_reservation(reservation)
    _record_attempt(student, session, AttendanceAttempt.STATUS_ALLOWED, "Check-in realizado.", qr_token.token)
    return attendance


def register_manual_attendance(*, student, session, actor, reason):
    if PhysicalAttendance.objects.filter(student=student, session=session).exists():
        _record_attempt(student, session, AttendanceAttempt.STATUS_DUPLICATE, "Presenca manual duplicada.", "")
        raise ValidationError("Presenca ja registrada.")
    with transaction.atomic():
        attendance = PhysicalAttendance.objects.create(
            student=student,
            session=session,
            reservation=_get_active_reservation(student, session),
            checkin_method=PhysicalAttendance.METHOD_MANUAL,
            recorded_by=actor,
            notes=reason,
        )
        _consume_reservation(attendance.reservation)
    _record_attempt(student, session, AttendanceAttempt.STATUS_ALLOWED, reason, "")
    return attendance


def _validate_reservation_eligibility(student, session):
    if ClassReservation.objects.filter(student=student, session=session).exists():
        raise ValidationError("Aluno ja possui reserva para esta sessao.")
    status_result = _validate_student_status(student, session)
    if not status_result["allowed"]:
        raise ValidationError(status_result["message"])


def _validate_capacity(session):
    active_count = session.reservations.filter(status=ClassReservation.STATUS_ACTIVE).count()
    if active_count >= session.class_group.capacity:
        raise ValidationError("Nao ha vagas disponiveis para esta sessao.")


def _validate_student_status(student, session):
    from system.services.finance.contracts import sync_student_operational_status

    sync_student_operational_status(student)
    blocked_statuses = {
        StudentProfile.STATUS_PENDING_FINANCIAL: "Aluno inadimplente ou com pendencia financeira.",
        StudentProfile.STATUS_PAUSED: "Aluno com matricula pausada.",
        StudentProfile.STATUS_BLOCKED: "Aluno bloqueado operacionalmente.",
        StudentProfile.STATUS_INACTIVE: "Aluno inativo.",
    }
    if student.operational_status not in blocked_statuses:
        return {"allowed": True}
    message = blocked_statuses[student.operational_status]
    return {"allowed": False, "reason": student.operational_status.lower(), "message": message}


def _validate_session_window(student, session):
    now = timezone.now()
    if session.status != session.STATUS_OPEN:
        return {"allowed": False, "reason": "session_closed", "message": "Sessao ainda nao esta aberta."}
    if not (session.starts_at <= now <= session.ends_at):
        return {"allowed": False, "reason": "outside_window", "message": "Sessao fora da janela de check-in."}
    return {"allowed": True}


def _validate_reservation_requirement(student, session):
    if not session.class_group.reservation_required:
        return {"allowed": True}
    reservation = _get_active_reservation(student, session)
    if reservation:
        return {"allowed": True}
    return {"allowed": False, "reason": "missing_reservation", "message": "Reserva previa obrigatoria para esta turma."}


def _get_active_reservation(student, session):
    queryset = ClassReservation.objects.filter(
        student=student,
        session=session,
        status=ClassReservation.STATUS_ACTIVE,
    )
    return queryset.first()


def _get_valid_qr_token(session, token_value):
    qr_token = AttendanceQrToken.objects.filter(session=session, token=token_value).first()
    if qr_token is None or qr_token.is_expired:
        raise ValidationError("QR invalido ou expirado.")
    return qr_token


def _consume_reservation(reservation):
    if reservation is None:
        return
    reservation.status = ClassReservation.STATUS_CONSUMED
    reservation.save(update_fields=["status", "updated_at"])


def _record_attempt(student, session, status, reason, token_value):
    AttendanceAttempt.objects.create(
        student=student,
        session=session,
        status=status,
        reason=reason,
        token_value=token_value,
    )
