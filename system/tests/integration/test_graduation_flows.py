from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from system.constants import ROLE_PROFESSOR
from system.models import GraduationExamParticipation, GraduationRule, IbjjfBelt, SystemRole
from system.services.graduation import open_graduation_exam
from system.tests.factories.attendance_factories import PhysicalAttendanceFactory
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.class_factories import ClassGroupFactory, ClassSessionFactory, InstructorProfileFactory
from system.tests.factories.graduation_factories import GraduationHistoryFactory
from system.tests.factories.student_factories import StudentProfileFactory


def _default_belts():
    return IbjjfBelt.objects.get(code="white"), IbjjfBelt.objects.get(code="blue")


def _attendance(student, class_group, reference_date):
    starts_at = timezone.make_aware(datetime.combine(reference_date, datetime.min.time())) + timedelta(hours=19)
    return PhysicalAttendanceFactory(
        student=student,
        checked_in_at=starts_at,
        session=ClassSessionFactory(class_group=class_group, starts_at=starts_at, ends_at=starts_at + timedelta(hours=1)),
    )


def _prepare_eligible_student(*, class_group, join_offset_days=180):
    today = timezone.localdate()
    white, blue = _default_belts()
    student = StudentProfileFactory(join_date=today - timedelta(days=join_offset_days), operational_status="ACTIVE")
    GraduationHistoryFactory(student=student, belt_rank=white, started_on=today - timedelta(days=120))
    GraduationRule.objects.get_or_create(
        discipline=None,
        scope=GraduationRule.SCOPE_INTERNAL,
        current_belt=white,
        current_degree=0,
        defaults={
            "target_belt": blue,
            "target_degree": 0,
            "minimum_active_days": 90,
            "minimum_attendances": 5,
            "maximum_inactivity_days": 45,
            "requires_exam": True,
            "is_active": True,
        },
    )
    for offset in range(5):
        _attendance(student, class_group, today - timedelta(days=offset * 5))
    return student, white, blue


@pytest.mark.django_db
def test_professor_graduation_panel_lists_only_students_from_own_class_groups(client):
    professor_user = SystemUserFactory(password="StrongPassword123")
    professor_role, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    professor_user.assign_role(professor_role)
    own_instructor = InstructorProfileFactory(user=professor_user)
    own_group = ClassGroupFactory(instructor=own_instructor)
    other_group = ClassGroupFactory()
    own_student, _, _ = _prepare_eligible_student(class_group=own_group)
    other_student, _, _ = _prepare_eligible_student(class_group=other_group)
    client.force_login(professor_user)

    response = client.get(reverse("system:graduation-panel"), {"filters-eligible_only": "on"})
    content = response.content.decode()

    assert response.status_code == 200
    assert own_student.user.full_name in content
    assert other_student.user.full_name not in content
    assert "Apto para avaliacao" in content


@pytest.mark.django_db
def test_admin_graduation_panel_opens_exam_and_registers_approval(client):
    admin_user = AdminUserFactory(password="StrongPassword123")
    class_group = ClassGroupFactory()
    student, _, blue_belt = _prepare_eligible_student(class_group=class_group)
    client.force_login(admin_user)

    response = client.post(
        reverse("system:graduation-panel"),
        data={
            "selected_students": [str(student.uuid)],
            "exam-title": "Graduacao de Abril",
            "exam-scheduled_for": timezone.localdate().isoformat(),
            "exam-notes": "Turma principal",
        },
    )
    participation = GraduationExamParticipation.objects.get(student=student)
    decision_response = client.post(
        reverse("system:graduation-participation-decision", kwargs={"uuid": participation.uuid}),
        data={
            f"decision-{participation.uuid}-status": GraduationExamParticipation.STATUS_APPROVED,
            f"decision-{participation.uuid}-target_belt": blue_belt.id,
            f"decision-{participation.uuid}-target_degree": 0,
            f"decision-{participation.uuid}-promotion_date": timezone.localdate().isoformat(),
            f"decision-{participation.uuid}-decision_notes": "Promovido por desempenho tecnico.",
        },
    )
    participation.refresh_from_db()
    current_history = student.graduation_histories.get(is_current=True)

    assert response.status_code == 302
    assert decision_response.status_code == 302
    assert participation.status == GraduationExamParticipation.STATUS_APPROVED
    assert participation.certificate_code is not None
    assert current_history.belt_rank == blue_belt


@pytest.mark.django_db
def test_graduation_panel_rejects_invalid_regressive_promotion(client):
    admin_user = AdminUserFactory(password="StrongPassword123")
    class_group = ClassGroupFactory()
    student, white_belt, _ = _prepare_eligible_student(class_group=class_group)
    exam = open_graduation_exam(
        title="Exame invalido",
        scheduled_for=timezone.localdate(),
        actor=admin_user,
        students=[student],
    )
    participation = exam.participations.get(student=student)
    client.force_login(admin_user)

    response = client.post(
        reverse("system:graduation-participation-decision", kwargs={"uuid": participation.uuid}),
        data={
            f"decision-{participation.uuid}-status": GraduationExamParticipation.STATUS_APPROVED,
            f"decision-{participation.uuid}-target_belt": white_belt.id,
            f"decision-{participation.uuid}-target_degree": participation.current_degree,
            f"decision-{participation.uuid}-promotion_date": timezone.localdate().isoformat(),
            f"decision-{participation.uuid}-decision_notes": "Tentativa regressiva",
        },
    )
    participation.refresh_from_db()

    assert response.status_code == 302
    assert participation.status == GraduationExamParticipation.STATUS_PENDING
    assert student.graduation_histories.filter(is_current=True, belt_rank=white_belt).count() == 1
