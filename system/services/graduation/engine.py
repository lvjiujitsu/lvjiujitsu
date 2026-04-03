from django.utils import timezone

from system.models import GraduationHistory, GraduationRule, IbjjfBelt, PhysicalAttendance, StudentProfile


BLOCKED_STATUSES = {
    StudentProfile.STATUS_PENDING_FINANCIAL: "Aluno com pendencia financeira.",
    StudentProfile.STATUS_PAUSED: "Aluno com matricula pausada.",
    StudentProfile.STATUS_BLOCKED: "Aluno bloqueado operacionalmente.",
    StudentProfile.STATUS_INACTIVE: "Aluno inativo.",
}


def ensure_current_graduation_history(student, *, actor=None):
    current_history = _get_current_history(student)
    if current_history:
        return current_history
    default_belt = _get_default_belt()
    current_history = GraduationHistory(
        student=student,
        belt_rank=default_belt,
        degree_level=0,
        started_on=student.join_date,
        is_current=True,
        event_type=GraduationHistory.EVENT_INITIAL,
        recorded_by=actor,
        notes="Historico inicial criado automaticamente pelo motor de graduacao.",
    )
    current_history.full_clean()
    current_history.save()
    return current_history


def calculate_training_summary(student, *, reference_date=None):
    reference = reference_date or timezone.localdate()
    current_history = ensure_current_graduation_history(student)
    attendances = _get_cycle_attendances(student, current_history, reference)
    attendance_count = len(attendances)
    last_attendance_on = _get_last_attendance_on(attendances)
    paused_days = _calculate_paused_days(student, current_history.started_on, reference)
    active_days = _calculate_active_days(current_history.started_on, reference, paused_days)
    return {
        "reference_date": reference,
        "current_history": current_history,
        "active_days": active_days,
        "paused_days": paused_days,
        "attendance_count": attendance_count,
        "last_attendance_on": last_attendance_on,
        "days_since_last_attendance": _calculate_days_since_last_attendance(current_history.started_on, reference, last_attendance_on),
        "age": _calculate_student_age(student, reference),
    }


def evaluate_student_for_graduation(student, *, reference_date=None, discipline=None):
    summary = calculate_training_summary(student, reference_date=reference_date)
    current_history = summary["current_history"]
    official_rule = _resolve_rule(current_history, scope=GraduationRule.SCOPE_OFFICIAL, discipline=discipline)
    internal_rule = _resolve_rule(current_history, scope=GraduationRule.SCOPE_INTERNAL, discipline=discipline)
    active_rule = internal_rule or official_rule
    reasons = _collect_blocking_reasons(student, summary, active_rule)
    return {
        "student": student,
        "summary": summary,
        "current_history": current_history,
        "official_rule": official_rule,
        "internal_rule": internal_rule,
        "active_rule": active_rule,
        "eligible": not reasons and active_rule is not None,
        "blocking_reasons": reasons,
        "next_belt": active_rule.target_belt if active_rule else None,
        "next_degree": active_rule.target_degree if active_rule else None,
    }


def build_graduation_panel_candidates(students, *, reference_date=None, discipline=None, belt_rank=None, eligible_only=False):
    candidates = []
    for student in students:
        evaluation = evaluate_student_for_graduation(student, reference_date=reference_date, discipline=discipline)
        if belt_rank and evaluation["current_history"].belt_rank_id != belt_rank.id:
            continue
        if eligible_only and not evaluation["eligible"]:
            continue
        candidates.append(evaluation)
    return candidates


def _get_current_history(student):
    prefetched = getattr(student, "prefetched_current_graduation_history", None)
    if prefetched is not None:
        return prefetched[0] if prefetched else None
    return student.graduation_histories.select_related("belt_rank").filter(is_current=True).first()


def _get_default_belt():
    default_belt = IbjjfBelt.objects.filter(is_active=True).order_by("display_order").first()
    if default_belt is None:
        raise IbjjfBelt.DoesNotExist("Nenhuma faixa ativa foi configurada para iniciar o historico tecnico.")
    return default_belt


def _get_cycle_attendances(student, current_history, reference_date):
    prefetched = getattr(student, "prefetched_attendances", None)
    attendances = prefetched if prefetched is not None else _load_cycle_attendances(student, current_history, reference_date)
    filtered = []
    for attendance in attendances:
        checked_date = timezone.localtime(attendance.checked_in_at).date()
        if current_history.started_on <= checked_date <= reference_date:
            filtered.append(attendance)
    return filtered


def _load_cycle_attendances(student, current_history, reference_date):
    return list(
        PhysicalAttendance.objects.filter(
            student=student,
            checked_in_at__date__gte=current_history.started_on,
            checked_in_at__date__lte=reference_date,
        ).order_by("-checked_in_at")
    )


def _get_last_attendance_on(attendances):
    if not attendances:
        return None
    return timezone.localtime(attendances[0].checked_in_at).date()


def _calculate_paused_days(student, start_date, reference_date):
    pauses = getattr(student, "enrollment_pauses", None)
    if hasattr(pauses, "all"):
        pauses = list(pauses.all())
    if pauses is None:
        pauses = list(student.enrollment_pauses.all())
    total_days = 0
    for pause in pauses:
        pause_end = pause.end_date or reference_date
        overlap_start = max(pause.start_date, start_date)
        overlap_end = min(pause_end, reference_date)
        if overlap_end < overlap_start:
            continue
        total_days += (overlap_end - overlap_start).days + 1
    return total_days


def _calculate_active_days(start_date, reference_date, paused_days):
    total_days = max((reference_date - start_date).days + 1, 0)
    return max(total_days - paused_days, 0)


def _calculate_days_since_last_attendance(start_date, reference_date, last_attendance_on):
    anchor_date = last_attendance_on or start_date
    return max((reference_date - anchor_date).days, 0)


def _calculate_student_age(student, reference_date):
    if not student.birth_date:
        return None
    years = reference_date.year - student.birth_date.year
    before_birthday = (reference_date.month, reference_date.day) < (student.birth_date.month, student.birth_date.day)
    return years - int(before_birthday)


def _resolve_rule(current_history, *, scope, discipline):
    queryset = GraduationRule.objects.select_related("current_belt", "target_belt", "discipline").filter(
        scope=scope,
        is_active=True,
        current_belt=current_history.belt_rank,
        current_degree=current_history.degree_level,
    )
    discipline_rule = _find_rule_for_discipline(queryset, discipline)
    if discipline_rule:
        return discipline_rule
    return queryset.filter(discipline__isnull=True).first()


def _find_rule_for_discipline(queryset, discipline):
    if discipline is None:
        return None
    return queryset.filter(discipline=discipline).first()


def _collect_blocking_reasons(student, summary, active_rule):
    reasons = []
    status_reason = BLOCKED_STATUSES.get(student.operational_status)
    if status_reason:
        reasons.append(status_reason)
    if active_rule is None:
        reasons.append("Nao existe regra ativa configurada para esta etapa tecnica.")
        return reasons
    reasons.extend(_collect_rule_reasons(summary, active_rule))
    return reasons


def _collect_rule_reasons(summary, rule):
    reasons = []
    if summary["age"] is not None and summary["age"] < rule.minimum_age:
        reasons.append("Idade minima da regra ainda nao atingida.")
    if summary["active_days"] < rule.minimum_active_days:
        reasons.append("Tempo ativo de treino ainda insuficiente para a regra atual.")
    if summary["attendance_count"] < rule.minimum_attendances:
        reasons.append("Frequencia valida ainda insuficiente para a regra atual.")
    if summary["days_since_last_attendance"] > rule.maximum_inactivity_days:
        reasons.append("Inatividade prolongada bloqueia elegibilidade automatica.")
    return reasons
