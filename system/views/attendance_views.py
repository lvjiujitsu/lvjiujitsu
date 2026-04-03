from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_PROFESSOR
from system.forms import AttendanceCheckInForm, ManualAttendanceForm
from system.mixins import RoleRequiredMixin
from system.models import ClassSession, StudentProfile
from system.selectors.attendance_selectors import get_professor_sessions_queryset
from system.services.attendance.workflow import (
    build_precheck_result,
    create_class_reservation,
    generate_session_qr_token,
    register_manual_attendance,
    register_qr_attendance,
)
from system.services.classes.session_lifecycle import open_class_session


class SessionReservationCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        session = self._get_session()
        student = get_object_or_404(StudentProfile, user=request.user)
        try:
            create_class_reservation(student=student, session=session)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("system:home")
        messages.success(request, "Reserva confirmada.")
        return redirect("system:home")

    def _get_session(self):
        return get_object_or_404(ClassSession.objects.select_related("class_group"), uuid=self.kwargs["uuid"])


class PreCheckEligibilityAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        session = self._get_session()
        student = get_object_or_404(StudentProfile, user=request.user)
        payload = build_precheck_result(student=student, session=session)
        return JsonResponse(payload)

    def _get_session(self):
        return get_object_or_404(ClassSession.objects.select_related("class_group"), uuid=self.kwargs["uuid"])


class AttendanceCheckInView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = AttendanceCheckInForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"allowed": False, "reason": "invalid_form"}, status=400)
        session = self._get_session()
        student = get_object_or_404(StudentProfile, user=request.user)
        try:
            attendance = register_qr_attendance(
                student=student,
                session=session,
                token_value=form.cleaned_data["token"],
                actor=request.user,
            )
        except ValidationError as exc:
            return JsonResponse({"allowed": False, "message": str(exc)}, status=400)
        return JsonResponse({"allowed": True, "attendance_uuid": str(attendance.uuid)})

    def _get_session(self):
        return get_object_or_404(ClassSession.objects.select_related("class_group"), uuid=self.kwargs["uuid"])


class ProfessorDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "system/attendance/professor_dashboard.html"
    required_roles = (ROLE_PROFESSOR,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = get_professor_sessions_queryset(self.request.user)
        context["manual_form"] = kwargs.get("manual_form") or ManualAttendanceForm(prefix="manual")
        return context


class ProfessorSessionOpenView(RoleRequiredMixin, View):
    required_roles = (ROLE_PROFESSOR,)

    def post(self, request, *args, **kwargs):
        session = self._get_session(request.user)
        try:
            open_class_session(session, request.user)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("system:professor-dashboard")
        messages.success(request, "Aula iniciada.")
        return redirect("system:professor-dashboard")

    def _get_session(self, user):
        queryset = get_professor_sessions_queryset(user)
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])


class ProfessorGenerateQrView(RoleRequiredMixin, View):
    required_roles = (ROLE_PROFESSOR,)

    def post(self, request, *args, **kwargs):
        session = self._get_session(request.user)
        try:
            qr_token = generate_session_qr_token(session=session, actor=request.user)
        except ValidationError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        payload = {"token": qr_token.token, "expires_at": qr_token.expires_at.isoformat()}
        return JsonResponse(payload)

    def _get_session(self, user):
        queryset = get_professor_sessions_queryset(user)
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])


class ProfessorManualAttendanceView(RoleRequiredMixin, View):
    required_roles = (ROLE_PROFESSOR,)

    def post(self, request, *args, **kwargs):
        form = ManualAttendanceForm(request.POST, prefix="manual")
        if not form.is_valid():
            return self._redirect_dashboard_with_error(request)
        session = self._get_session(request.user)
        student = get_object_or_404(StudentProfile, uuid=form.cleaned_data["student_uuid"])
        try:
            register_manual_attendance(
                student=student,
                session=session,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("system:professor-dashboard")
        messages.success(request, "Presenca manual registrada.")
        return redirect("system:professor-dashboard")

    def _get_session(self, user):
        queryset = get_professor_sessions_queryset(user)
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])

    def _redirect_dashboard_with_error(self, request):
        messages.error(request, "Nao foi possivel registrar a presenca manual.")
        return redirect("system:professor-dashboard")
