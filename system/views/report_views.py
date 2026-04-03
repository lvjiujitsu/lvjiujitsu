from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import ExportRequestForm, ReportCenterFilterForm
from system.mixins import RoleRequiredMixin
from system.selectors import (
    build_attendance_report_rows,
    build_audit_report_rows,
    build_finance_report_rows,
    build_graduation_report_rows,
    get_audit_logs_queryset,
    get_export_requests_queryset,
)
from system.services.reports import get_or_create_export_control, request_csv_export


REPORT_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class ReportCenterView(RoleRequiredMixin, TemplateView):
    template_name = "system/reports/report_center.html"
    required_roles = REPORT_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_form = kwargs.get("filter_form") or ReportCenterFilterForm(self.request.GET or None, prefix="filters")
        export_form = kwargs.get("export_form") or self._build_export_form(filter_form)
        dates = self._resolve_dates(filter_form)
        context.update(
            {
                "filter_form": filter_form,
                "export_form": export_form,
                "dates": dates,
                "attendance_rows": build_attendance_report_rows(**dates)[:20],
                "finance_rows": build_finance_report_rows(**dates)[:20],
                "graduation_rows": build_graduation_report_rows(**dates)[:20],
                "audit_rows": build_audit_report_rows(**dates)[:20],
                "audit_logs": get_audit_logs_queryset()[:20],
                "recent_exports": get_export_requests_queryset()[:10],
                "export_control": get_or_create_export_control(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        export_form = ExportRequestForm(request.POST)
        filter_form = ReportCenterFilterForm(request.POST, prefix="filters")
        if not export_form.is_valid() or not filter_form.is_valid():
            return self.render_to_response(self.get_context_data(filter_form=filter_form, export_form=export_form))
        try:
            export_request = request_csv_export(
                report_type=export_form.cleaned_data["report_type"],
                requested_by=request.user,
                start_date=filter_form.cleaned_data["start_date"],
                end_date=filter_form.cleaned_data["end_date"],
            )
        except Exception as exc:
            messages.error(request, str(exc))
            return self.render_to_response(self.get_context_data(filter_form=filter_form, export_form=export_form))
        messages.success(
            request,
            f"Exportacao concluida: {export_request.file_name}.",
        )
        return redirect("system:report-center")

    def _resolve_dates(self, filter_form):
        if not filter_form.is_valid():
            cleaned = ReportCenterFilterForm(prefix="filters").fields
            return {
                "start_date": cleaned["start_date"].initial,
                "end_date": cleaned["end_date"].initial,
            }
        return {
            "start_date": filter_form.cleaned_data["start_date"],
            "end_date": filter_form.cleaned_data["end_date"],
        }

    def _build_export_form(self, filter_form):
        dates = self._resolve_dates(filter_form)
        return ExportRequestForm(
            initial={
                "start_date": dates["start_date"],
                "end_date": dates["end_date"],
            }
        )
