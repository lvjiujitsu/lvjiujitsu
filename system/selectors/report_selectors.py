from system.models import AuditLog, ExportRequest, GraduationHistory, MonthlyInvoice, PhysicalAttendance


def get_audit_logs_queryset():
    return AuditLog.objects.select_related("actor_user").order_by("-created_at")


def get_export_requests_queryset():
    return ExportRequest.objects.select_related("requested_by").order_by("-started_at")


def build_attendance_report_rows(*, start_date, end_date):
    queryset = PhysicalAttendance.objects.select_related(
        "student__user",
        "session__class_group",
    ).filter(checked_in_at__date__gte=start_date, checked_in_at__date__lte=end_date)
    return [
        {
            "student_name": attendance.student.user.full_name,
            "student_cpf": attendance.student.user.cpf,
            "class_group": attendance.session.class_group.name,
            "checked_in_at": attendance.checked_in_at.isoformat(),
            "method": attendance.get_checkin_method_display(),
        }
        for attendance in queryset
    ]


def build_finance_report_rows(*, start_date, end_date):
    queryset = MonthlyInvoice.objects.select_related(
        "subscription__responsible_user",
        "subscription__plan",
    ).filter(reference_month__gte=start_date.replace(day=1), reference_month__lte=end_date.replace(day=1))
    return [
        {
            "responsible_name": invoice.subscription.responsible_user.full_name,
            "responsible_cpf": invoice.subscription.responsible_user.cpf,
            "plan_name": invoice.subscription.plan.name,
            "reference_month": invoice.reference_month.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "amount_net": str(invoice.amount_net),
            "status": invoice.get_status_display(),
        }
        for invoice in queryset
    ]


def build_graduation_report_rows(*, start_date, end_date):
    queryset = GraduationHistory.objects.select_related(
        "student__user",
        "belt_rank",
    ).filter(started_on__gte=start_date, started_on__lte=end_date)
    return [
        {
            "student_name": history.student.user.full_name,
            "student_cpf": history.student.user.cpf,
            "belt": history.belt_rank.name,
            "degree": history.degree_level,
            "started_on": history.started_on.isoformat(),
            "event_type": history.get_event_type_display(),
        }
        for history in queryset
    ]


def build_audit_report_rows(*, start_date, end_date):
    queryset = get_audit_logs_queryset().filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    return [
        {
            "created_at": log.created_at.isoformat(),
            "actor": log.actor_user.full_name if log.actor_user else "",
            "category": log.get_category_display(),
            "action": log.action,
            "status": log.get_status_display(),
            "target_model": log.target_model,
            "target_uuid": str(log.target_uuid or ""),
        }
        for log in queryset
    ]
