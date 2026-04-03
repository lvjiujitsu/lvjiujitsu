import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from system.models import AttendanceAttempt, AttendanceQrToken, ClassReservation, ClassSession, PhysicalAttendance, StudentProfile
from system.services.attendance.workflow import (
    build_precheck_result,
    create_class_reservation,
    generate_session_qr_token,
    register_qr_attendance,
)
from system.tests.factories.attendance_factories import AttendanceQrTokenFactory
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.class_factories import ClassGroupFactory, ClassSessionFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_reservation_blocks_duplicate_and_full_capacity():
    session = _build_open_session(capacity=1, reservation_required=True)
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    other_student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)

    create_class_reservation(student=student, session=session)

    with pytest.raises(ValidationError):
        create_class_reservation(student=student, session=session)
    with pytest.raises(ValidationError):
        create_class_reservation(student=other_student, session=session)


@pytest.mark.django_db
def test_precheck_blocks_paused_student_and_missing_reservation():
    session = _build_open_session(capacity=5, reservation_required=True)
    paused_student = StudentProfileFactory(operational_status=StudentProfile.STATUS_PAUSED)
    active_student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)

    paused_result = build_precheck_result(student=paused_student, session=session)
    missing_reservation_result = build_precheck_result(student=active_student, session=session)

    assert paused_result["allowed"] is False
    assert missing_reservation_result["reason"] == "missing_reservation"


@pytest.mark.django_db
def test_qr_checkin_registers_first_attendance_and_blocks_duplicate():
    actor = SystemUserFactory()
    session = _build_open_session(capacity=5, reservation_required=True)
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    create_class_reservation(student=student, session=session)
    qr_token = generate_session_qr_token(session=session, actor=actor)

    attendance = register_qr_attendance(student=student, session=session, token_value=qr_token.token, actor=actor)

    with pytest.raises(ValidationError):
        register_qr_attendance(student=student, session=session, token_value=qr_token.token, actor=actor)

    assert attendance.checkin_method == PhysicalAttendance.METHOD_QR
    assert AttendanceAttempt.objects.filter(student=student, status=AttendanceAttempt.STATUS_DUPLICATE).exists() is True


@pytest.mark.django_db
def test_expired_qr_is_rejected():
    actor = SystemUserFactory()
    session = _build_open_session(capacity=5, reservation_required=False)
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    qr_token = AttendanceQrTokenFactory(
        session=session,
        generated_by=actor,
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    with pytest.raises(ValidationError):
        register_qr_attendance(student=student, session=session, token_value=qr_token.token, actor=actor)


def _build_open_session(*, capacity, reservation_required):
    class_group = ClassGroupFactory(capacity=capacity, reservation_required=reservation_required)
    session = ClassSessionFactory(
        class_group=class_group,
        starts_at=timezone.now() - timedelta(minutes=5),
        ends_at=timezone.now() + timedelta(minutes=55),
        status=ClassSession.STATUS_OPEN,
    )
    return session
