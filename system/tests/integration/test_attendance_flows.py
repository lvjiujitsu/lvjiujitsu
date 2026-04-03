import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone

from system.constants import ROLE_PROFESSOR
from system.models import ClassSession, PhysicalAttendance, StudentProfile, SystemRole
from system.tests.factories.attendance_factories import ClassReservationFactory
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.class_factories import ClassSessionFactory, InstructorProfileFactory
from system.tests.factories.finance_factories import EnrollmentPauseFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_precheck_api_returns_allowed_and_denied(client):
    student_user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(
        user=student_user,
        operational_status=StudentProfile.STATUS_ACTIVE,
    )
    session = ClassSessionFactory(
        status=ClassSession.STATUS_OPEN,
        starts_at=timezone.now() - timedelta(minutes=5),
        ends_at=timezone.now() + timedelta(minutes=30),
    )
    ClassReservationFactory(student=student, session=session)
    client.force_login(student_user)

    allowed_response = client.get(reverse("system:attendance-precheck", kwargs={"uuid": session.uuid}))
    EnrollmentPauseFactory(student=student, subscription=None)
    denied_response = client.get(reverse("system:attendance-precheck", kwargs={"uuid": session.uuid}))

    assert allowed_response.json()["allowed"] is True
    assert denied_response.json()["allowed"] is False


@pytest.mark.django_db
def test_professor_dashboard_shows_own_sessions_and_manual_attendance(client):
    professor_user = SystemUserFactory(password="StrongPassword123")
    professor_role, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    professor_user.assign_role(professor_role)
    instructor = InstructorProfileFactory(user=professor_user)
    own_session = ClassSessionFactory(
        class_group__instructor=instructor,
        starts_at=timezone.now() - timedelta(minutes=5),
        ends_at=timezone.now() + timedelta(minutes=30),
    )
    other_session = ClassSessionFactory()
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    client.force_login(professor_user)

    dashboard_response = client.get(reverse("system:professor-dashboard"))
    manual_response = client.post(
        reverse("system:professor-manual-attendance", kwargs={"uuid": own_session.uuid}),
        data={
            "manual-student_uuid": str(student.uuid),
            "manual-reason": "Aluno confirmado manualmente pelo professor.",
        },
    )

    assert dashboard_response.status_code == 200
    assert own_session.class_group.name in dashboard_response.content.decode()
    assert other_session.class_group.name not in dashboard_response.content.decode()
    assert manual_response.status_code == 302
    assert PhysicalAttendance.objects.filter(student=student, session=own_session).exists() is True
