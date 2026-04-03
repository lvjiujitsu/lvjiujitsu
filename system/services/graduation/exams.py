from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import AuditLog, GraduationExam, GraduationExamParticipation, GraduationHistory
from system.services.graduation.engine import ensure_current_graduation_history, evaluate_student_for_graduation
from system.services.reports.audit import record_audit_log


@transaction.atomic
def open_graduation_exam(*, title, scheduled_for, actor, students, discipline=None, class_group=None, notes=""):
    if not students:
        raise ValidationError("Selecione pelo menos um aluno elegivel para abrir a avaliacao.")
    exam = GraduationExam(
        title=title,
        scheduled_for=scheduled_for,
        discipline=discipline,
        class_group=class_group,
        created_by=actor,
        notes=notes,
    )
    exam.full_clean()
    exam.save()
    for student in students:
        evaluation = evaluate_student_for_graduation(student, reference_date=scheduled_for, discipline=discipline)
        _create_exam_participation(exam, student, evaluation)
    record_audit_log(
        category=AuditLog.CATEGORY_GRADUATION,
        action="graduation_exam_opened",
        actor_user=actor,
        target=exam,
        metadata={"participants_count": len(students)},
    )
    return exam


@transaction.atomic
def record_exam_participation_decision(
    participation,
    *,
    actor,
    status,
    target_belt=None,
    target_degree=None,
    decision_notes="",
    promotion_date=None,
):
    _validate_pending_participation(participation)
    participation.status = status
    participation.decided_by = actor
    participation.decided_at = timezone.now()
    participation.decision_notes = decision_notes
    if status == GraduationExamParticipation.STATUS_APPROVED:
        history = promote_student(
            participation.student,
            actor=actor,
            target_belt=target_belt or participation.suggested_belt,
            target_degree=target_degree if target_degree is not None else participation.suggested_degree,
            promotion_date=promotion_date or participation.exam.scheduled_for,
            notes=decision_notes,
        )
        participation.promoted_history = history
        participation.certificate_code = participation.issue_certificate_code()
        participation.certificate_issued_at = timezone.now()
    participation.save()
    _refresh_exam_status(participation.exam)
    record_audit_log(
        category=AuditLog.CATEGORY_GRADUATION,
        action="graduation_decision_recorded",
        actor_user=actor,
        target=participation,
        metadata={"status": status, "student_uuid": str(participation.student.uuid)},
    )
    return participation


@transaction.atomic
def promote_student(student, *, actor, target_belt, target_degree, promotion_date, notes="", event_type=None):
    current_history = ensure_current_graduation_history(student, actor=actor)
    _validate_promotion_stage(current_history, target_belt, target_degree)
    _close_current_history(current_history, promotion_date)
    next_history = GraduationHistory(
        student=student,
        belt_rank=target_belt,
        degree_level=target_degree,
        started_on=promotion_date,
        is_current=True,
        event_type=event_type or GraduationHistory.EVENT_PROMOTION,
        recorded_by=actor,
        notes=notes,
    )
    next_history.full_clean()
    next_history.save()
    return next_history


def _create_exam_participation(exam, student, evaluation):
    if not evaluation["eligible"]:
        raise ValidationError(f"{student.user.full_name} nao esta apto para o exame selecionado.")
    participation = GraduationExamParticipation(
        exam=exam,
        student=student,
        current_belt=evaluation["current_history"].belt_rank,
        current_degree=evaluation["current_history"].degree_level,
        suggested_belt=evaluation["next_belt"],
        suggested_degree=evaluation["next_degree"],
        eligibility_snapshot=_build_eligibility_snapshot(evaluation),
    )
    participation.full_clean()
    participation.save()
    return participation


def _build_eligibility_snapshot(evaluation):
    summary = evaluation["summary"]
    return {
        "active_days": summary["active_days"],
        "paused_days": summary["paused_days"],
        "attendance_count": summary["attendance_count"],
        "last_attendance_on": summary["last_attendance_on"].isoformat() if summary["last_attendance_on"] else None,
        "days_since_last_attendance": summary["days_since_last_attendance"],
        "internal_rule_id": evaluation["internal_rule"].id if evaluation["internal_rule"] else None,
        "official_rule_id": evaluation["official_rule"].id if evaluation["official_rule"] else None,
    }


def _validate_pending_participation(participation):
    if participation.status != GraduationExamParticipation.STATUS_PENDING:
        raise ValidationError("Esta participacao ja possui decisao registrada.")


def _validate_promotion_stage(current_history, target_belt, target_degree):
    current_stage = (current_history.belt_rank.display_order, current_history.degree_level)
    target_stage = (target_belt.display_order, target_degree)
    if target_stage <= current_stage:
        raise ValidationError("A promocao precisa avancar para uma etapa superior a atual.")


def _close_current_history(current_history, promotion_date):
    current_history.is_current = False
    current_history.ended_on = promotion_date
    current_history.save(update_fields=["is_current", "ended_on", "updated_at"])


def _refresh_exam_status(exam):
    pending_exists = exam.participations.filter(status=GraduationExamParticipation.STATUS_PENDING).exists()
    exam.status = GraduationExam.STATUS_OPEN if pending_exists else GraduationExam.STATUS_COMPLETED
    exam.save(update_fields=["status", "updated_at"])
