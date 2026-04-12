import json

from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from system.services.class_calendar import (
    get_calendar_month_data,
    get_today_classes_for_person,
    perform_checkin,
    toggle_session_cancel,
)
from system.views.person_views import AdministrativeRequiredMixin
from system.views.portal_mixins import PortalLoginRequiredMixin, PortalRoleRequiredMixin


class AdminCalendarView(AdministrativeRequiredMixin, TemplateView):
    template_name = "calendar/admin_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year") or timezone.localdate().year
        month = self.kwargs.get("month") or timezone.localdate().month
        try:
            year = int(year)
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError
        except (ValueError, TypeError):
            today = timezone.localdate()
            year, month = today.year, today.month
        context["calendar"] = get_calendar_month_data(year, month)
        return context


class AdminToggleSessionView(AdministrativeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            schedule_id = int(body["schedule_id"])
            date_str = body["date"]
            reason = body.get("reason", "")
            parts = date_str.split("-")
            from datetime import date
            session_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (json.JSONDecodeError, KeyError, ValueError, IndexError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        session = toggle_session_cancel(schedule_id, session_date, reason)
        return JsonResponse({
            "status": session.status,
            "is_cancelled": session.is_cancelled,
        })


class StudentScheduleView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("student", "guardian", "dependent")
    template_name = "calendar/student_schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year") or timezone.localdate().year
        month = self.kwargs.get("month") or timezone.localdate().month
        try:
            year = int(year)
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError
        except (ValueError, TypeError):
            today = timezone.localdate()
            year, month = today.year, today.month
        context["calendar"] = get_calendar_month_data(year, month)
        return context


class StudentCheckinView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            schedule_id = int(body["schedule_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            checkin, created = perform_checkin(person, schedule_id)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception:
            return JsonResponse({"error": "Erro ao registrar check-in."}, status=500)

        return JsonResponse({
            "success": True,
            "created": created,
            "message": "Check-in realizado!" if created else "Você já fez check-in nesta aula.",
        })
