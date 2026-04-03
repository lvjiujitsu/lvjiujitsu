from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from system.models import GraduationExamParticipation, GraduationRule, IbjjfBelt
from system.services.graduation import (
    calculate_training_summary,
    evaluate_student_for_graduation,
    open_graduation_exam,
    record_exam_participation_decision,
)
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.attendance_factories import PhysicalAttendanceFactory
from system.tests.factories.class_factories import ClassDisciplineFactory, ClassSessionFactory
from system.tests.factories.finance_factories import EnrollmentPauseFactory
from system.tests.factories.graduation_factories import GraduationHistoryFactory, GraduationRuleFactory
from system.tests.factories.student_factories import StudentProfileFactory


def _default_belts():
    return IbjjfBelt.objects.get(code="white"), IbjjfBelt.objects.get(code="blue")


def _attendance_at(student, discipline, reference_date):
    starts_at = timezone.make_aware(datetime.combine(reference_date, datetime.min.time())) + timedelta(hours=19)
    return PhysicalAttendanceFactory(
        student=student,
        checked_in_at=starts_at,
        session=ClassSessionFactory(
            class_group__modality=discipline,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
        ),
    )


@pytest.mark.django_db
def test_evaluate_student_uses_internal_rule_and_keeps_official_reference():
    today = timezone.localdate()
    discipline = ClassDisciplineFactory()
    white, blue = _default_belts()
    student = StudentProfileFactory(join_date=today - timedelta(days=120), operational_status="ACTIVE")
    GraduationHistoryFactory(student=student, belt_rank=white, started_on=today - timedelta(days=90))
    GraduationRuleFactory(
        scope=GraduationRule.SCOPE_OFFICIAL,
        discipline=discipline,
        current_belt=white,
        target_belt=blue,
        minimum_active_days=90,
        minimum_attendances=10,
    )
    internal_rule = GraduationRuleFactory(
        scope=GraduationRule.SCOPE_INTERNAL,
        discipline=discipline,
        current_belt=white,
        target_belt=blue,
        minimum_active_days=60,
        minimum_attendances=8,
    )
    for offset in range(8):
        _attendance_at(student, discipline, today - timedelta(days=offset * 3))

    evaluation = evaluate_student_for_graduation(student, discipline=discipline)

    assert evaluation["eligible"] is True
    assert evaluation["active_rule"] == internal_rule
    assert evaluation["official_rule"].scope == GraduationRule.SCOPE_OFFICIAL
    assert evaluation["next_belt"] == blue


@pytest.mark.django_db
def test_calculate_training_summary_subtracts_pause_days_from_active_time():
    today = timezone.localdate()
    student = StudentProfileFactory(join_date=today - timedelta(days=100), operational_status="ACTIVE")
    GraduationHistoryFactory(student=student, started_on=today - timedelta(days=100))
    EnrollmentPauseFactory(
        student=student,
        subscription=None,
        start_date=today - timedelta(days=29),
        expected_return_date=today - timedelta(days=20),
        end_date=today - timedelta(days=20),
        is_active=False,
    )

    summary = calculate_training_summary(student, reference_date=today)

    assert summary["paused_days"] == 10
    assert summary["active_days"] == 91


@pytest.mark.django_db
def test_evaluate_student_blocks_prolonged_inactivity():
    today = timezone.localdate()
    discipline = ClassDisciplineFactory()
    white, blue = _default_belts()
    student = StudentProfileFactory(join_date=today - timedelta(days=120), operational_status="ACTIVE")
    GraduationHistoryFactory(student=student, belt_rank=white, started_on=today - timedelta(days=100))
    GraduationRuleFactory(
        scope=GraduationRule.SCOPE_INTERNAL,
        discipline=discipline,
        current_belt=white,
        target_belt=blue,
        minimum_active_days=60,
        minimum_attendances=1,
        maximum_inactivity_days=7,
    )
    _attendance_at(student, discipline, today - timedelta(days=20))

    evaluation = evaluate_student_for_graduation(student, discipline=discipline)

    assert evaluation["eligible"] is False
    assert "Inatividade prolongada" in " ".join(evaluation["blocking_reasons"])


@pytest.mark.django_db
def test_record_exam_approval_promotes_student_and_closes_previous_cycle():
    today = timezone.localdate()
    actor = SystemUserFactory()
    discipline = ClassDisciplineFactory()
    white, blue = _default_belts()
    student = StudentProfileFactory(join_date=today - timedelta(days=200), operational_status="ACTIVE")
    previous_history = GraduationHistoryFactory(student=student, belt_rank=white, started_on=today - timedelta(days=180))
    GraduationRuleFactory(
        scope=GraduationRule.SCOPE_INTERNAL,
        discipline=discipline,
        current_belt=white,
        target_belt=blue,
        minimum_active_days=90,
        minimum_attendances=6,
    )
    for offset in range(6):
        _attendance_at(student, discipline, today - timedelta(days=offset * 5))

    exam = open_graduation_exam(
        title="Exame tecnico",
        scheduled_for=today,
        actor=actor,
        students=[student],
        discipline=discipline,
    )
    participation = exam.participations.get(student=student)
    record_exam_participation_decision(participation, actor=actor, status=GraduationExamParticipation.STATUS_APPROVED)

    participation.refresh_from_db()
    previous_history.refresh_from_db()
    current_history = student.graduation_histories.get(is_current=True)

    assert participation.certificate_code is not None
    assert previous_history.is_current is False
    assert previous_history.ended_on == today
    assert current_history.belt_rank == blue
    assert current_history.degree_level == 0
    assert student.graduation_histories.count() == 2


@pytest.mark.django_db
def test_record_exam_postponement_keeps_current_history_untouched():
    today = timezone.localdate()
    actor = SystemUserFactory()
    discipline = ClassDisciplineFactory()
    white, blue = _default_belts()
    student = StudentProfileFactory(join_date=today - timedelta(days=120), operational_status="ACTIVE")
    current_history = GraduationHistoryFactory(student=student, belt_rank=white, started_on=today - timedelta(days=100))
    GraduationRuleFactory(
        scope=GraduationRule.SCOPE_INTERNAL,
        discipline=discipline,
        current_belt=white,
        target_belt=blue,
        minimum_active_days=90,
        minimum_attendances=4,
    )
    for offset in range(4):
        _attendance_at(student, discipline, today - timedelta(days=offset * 4))

    exam = open_graduation_exam(
        title="Exame adiado",
        scheduled_for=today,
        actor=actor,
        students=[student],
        discipline=discipline,
    )
    participation = exam.participations.get(student=student)
    record_exam_participation_decision(participation, actor=actor, status=GraduationExamParticipation.STATUS_POSTPONED)

    participation.refresh_from_db()
    current_history.refresh_from_db()

    assert participation.status == GraduationExamParticipation.STATUS_POSTPONED
    assert current_history.is_current is True
    assert student.graduation_histories.count() == 1
