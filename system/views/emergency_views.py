from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.mixins import RoleRequiredMixin
from system.models import AuditLog, SensitiveAccessLog
from system.selectors import get_emergency_student, search_emergency_students
from system.services.lgpd import record_sensitive_access
from system.services.reports.audit import record_audit_log


EMERGENCY_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO, ROLE_PROFESSOR)


class EmergencyQuickAccessView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "system/emergency/quick_access.html"
    required_roles = EMERGENCY_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        selected_uuid = self.request.GET.get("student")
        selected_student = self._get_selected_student(selected_uuid)
        context["query"] = query
        context["students"] = search_emergency_students(query)
        context["selected_student"] = selected_student
        context["emergency_record"] = getattr(selected_student, "emergency_record", None) if selected_student else None
        return context

    def _get_selected_student(self, selected_uuid):
        if not selected_uuid:
            return None
        student = get_emergency_student(selected_uuid)
        if student is None:
            return None
        self._record_access(student)
        return student

    def _record_access(self, student):
        record_sensitive_access(
            actor_user=self.request.user,
            student=student,
            access_type=SensitiveAccessLog.ACCESS_EMERGENCY_VIEW,
            access_purpose="Consulta rapida de emergencia.",
        )
        record_audit_log(
            category=AuditLog.CATEGORY_EMERGENCY,
            action="emergency_record_viewed",
            actor_user=self.request.user,
            target=student,
            request=self.request,
        )
