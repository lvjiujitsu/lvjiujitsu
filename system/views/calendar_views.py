import json

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from system.forms.class_forms import SpecialClassForm
from system.constants import (
    CLASS_STAFF_PERSON_TYPE_CODES,
    INSTRUCTOR_PERSON_TYPE_CODES,
    PersonTypeCode,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.models import ClassSchedule, Person, SpecialClass
from system.models.calendar import ClassCheckin, SpecialClassCheckin
from system.services.class_calendar import (
    assign_session_substitute,
    assign_special_substitute,
    approve_class_checkin,
    approve_special_checkin,
    assert_instructor_owns_schedule,
    assert_instructor_owns_special,
    cancel_class_without_instructor,
    cancel_instructor_self_checkin,
    cancel_instructor_self_special_checkin,
    cancel_special_without_instructor,
    create_special_class,
    delete_special_class,
    get_calendar_month_data,
    get_today_classes_for_person,
    perform_checkin,
    perform_special_class_checkin,
    register_instructor_self_checkin,
    register_instructor_self_special_checkin,
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
        context["instructors"] = _get_instructor_choices()
        return context


def _get_instructor_choices():
    return list(
        Person.objects.filter(
            person_type__code=PersonTypeCode.INSTRUCTOR,
            is_active=True,
        )
        .order_by("full_name")
        .values("pk", "full_name")
    )


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


class CalendarView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES + CLASS_STAFF_PERSON_TYPE_CODES
    template_name = "calendar/calendar.html"

    def _resolve_month(self):
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
        return year, month

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self._resolve_month()
        context["calendar"] = get_calendar_month_data(year, month)

        person = getattr(self.request, "portal_person", None)
        is_instructor = (
            person is not None
            and person.person_type
            and person.person_type.code in CLASS_STAFF_PERSON_TYPE_CODES
        )
        context["show_instructor_area"] = is_instructor

        owned_schedule_ids = []
        owned_special_ids = []
        if is_instructor:
            from system.services.class_calendar import _get_instructor_class_group_ids
            from system.models import ClassSchedule
            class_group_ids = _get_instructor_class_group_ids(person)
            owned_schedule_ids = list(
                ClassSchedule.objects.filter(class_group_id__in=class_group_ids)
                .values_list("pk", flat=True)
            )
            owned_special_ids = list(
                SpecialClass.objects.filter(teacher=person).values_list("pk", flat=True)
            )
        context["instructor_owned_schedule_ids"] = owned_schedule_ids
        context["instructor_owned_special_ids"] = owned_special_ids
        return context


# Kept for backward compatibility — both views now delegate to CalendarView
StudentScheduleView = CalendarView


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


class AdminSpecialClassCreateView(AdministrativeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        form = SpecialClassForm(data=body)
        if not form.is_valid():
            return JsonResponse({"error": "Dados inválidos.", "fields": form.errors}, status=400)

        special = create_special_class(
            title=form.cleaned_data["title"],
            date=form.cleaned_data["date"],
            start_time=form.cleaned_data["start_time"],
            duration_minutes=(
                form.cleaned_data.get("duration_minutes")
                or settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES
            ),
            teacher=form.cleaned_data.get("teacher"),
            notes=form.cleaned_data.get("notes") or "",
        )
        return JsonResponse({
            "success": True,
            "special": {
                "id": special.pk,
                "title": special.title,
                "date": special.date.strftime("%Y-%m-%d"),
                "start_time": special.start_time.strftime("%H:%M"),
                "teacher_name": special.teacher.full_name if special.teacher else "",
            },
        })


class AdminSpecialClassDeleteView(AdministrativeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        delete_special_class(special_id)
        return JsonResponse({"success": True})


class StudentSpecialClassCheckinView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            checkin, created = perform_special_class_checkin(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "created": created,
            "message": "Check-in no aulão realizado!" if created else "Você já fez check-in neste aulão.",
        })


# Alias mantido para imports existentes em urls.py
InstructorCalendarView = CalendarView


class InstructorToggleSessionView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

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

        try:
            assert_instructor_owns_schedule(person, schedule_id)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)

        session = toggle_session_cancel(schedule_id, session_date, reason)
        return JsonResponse({
            "status": session.status,
            "is_cancelled": session.is_cancelled,
        })


class InstructorCancelClassTodayView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        special_id = body.get("special_id")
        if special_id is not None:
            try:
                special_id = int(special_id)
            except (TypeError, ValueError):
                return JsonResponse({"error": "Dados inválidos."}, status=400)
            try:
                special = cancel_special_without_instructor(person, special_id)
            except SpecialClass.DoesNotExist:
                return JsonResponse({"error": "Aulão não encontrado."}, status=404)
            except PermissionError as e:
                return JsonResponse({"error": str(e)}, status=403)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)
            return JsonResponse({
                "success": True,
                "is_cancelled": special.is_cancelled,
            })

        try:
            schedule_id = int(body["schedule_id"])
        except (KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            session = cancel_class_without_instructor(person, schedule_id)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "is_cancelled": session.is_cancelled,
        })


class InstructorSpecialClassCreateView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        body["teacher"] = person.pk

        form = SpecialClassForm(data=body)
        if not form.is_valid():
            return JsonResponse({"error": "Dados inválidos.", "fields": form.errors}, status=400)

        special = create_special_class(
            title=form.cleaned_data["title"],
            date=form.cleaned_data["date"],
            start_time=form.cleaned_data["start_time"],
            duration_minutes=(
                form.cleaned_data.get("duration_minutes")
                or settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES
            ),
            teacher=person,
            notes=form.cleaned_data.get("notes") or "",
        )
        return JsonResponse({
            "success": True,
            "special": {
                "id": special.pk,
                "title": special.title,
                "date": special.date.strftime("%Y-%m-%d"),
                "start_time": special.start_time.strftime("%H:%M"),
                "teacher_name": special.teacher.full_name if special.teacher else "",
            },
        })


class InstructorSpecialClassDeleteView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            assert_instructor_owns_special(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)

        delete_special_class(special_id)
        return JsonResponse({"success": True})


class InstructorSelfCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

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
            session, created = register_instructor_self_checkin(person, schedule_id)
        except ClassSchedule.DoesNotExist:
            return JsonResponse({"error": "Horário não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        checked_in_at = None
        if session.instructor_checked_in_at:
            from django.utils import timezone as tz
            checked_in_at = tz.localtime(session.instructor_checked_in_at).strftime("%H:%M")

        return JsonResponse({
            "success": True,
            "created": created,
            "checked_in_at": checked_in_at,
        })


class InstructorSelfCheckinCancelView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

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
            _, changed = cancel_instructor_self_checkin(person, schedule_id)
        except ClassSchedule.DoesNotExist:
            return JsonResponse({"error": "Horário não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "changed": changed,
        })


class InstructorSessionSubstituteView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            substitute_teacher_id = int(body["substitute_teacher_id"])
            special_id = body.get("special_id")
            schedule_id = body.get("schedule_id")
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        if special_id is not None and schedule_id is not None:
            return JsonResponse({"error": "Informe apenas turma ou aulão."}, status=400)
        if special_id is None and schedule_id is None:
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            if special_id is not None:
                special = assign_special_substitute(
                    person,
                    int(special_id),
                    substitute_teacher_id,
                )
            else:
                session = assign_session_substitute(
                    person,
                    int(schedule_id),
                    substitute_teacher_id,
                )
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except ClassSchedule.DoesNotExist:
            return JsonResponse({"error": "Horário não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        if special_id is not None:
            return JsonResponse({
                "success": True,
                "substitute_teacher_id": special.substitute_teacher_id,
                "substitute_teacher_name": special.substitute_teacher.full_name,
            })

        return JsonResponse({
            "success": True,
            "substitute_teacher_id": session.substitute_teacher_id,
            "substitute_teacher_name": session.substitute_teacher.full_name,
        })


class InstructorSelfSpecialCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            special, created = register_instructor_self_special_checkin(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        checked_in_at = None
        if special.instructor_checked_in_at:
            from django.utils import timezone as tz
            checked_in_at = tz.localtime(special.instructor_checked_in_at).strftime("%H:%M")

        return JsonResponse({
            "success": True,
            "created": created,
            "checked_in_at": checked_in_at,
        })


class InstructorSelfSpecialCheckinCancelView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            _, changed = cancel_instructor_self_special_checkin(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "changed": changed,
        })


class InstructorApproveCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            checkin_id = int(body["checkin_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            checkin = approve_class_checkin(instructor=person, checkin_id=checkin_id)
        except ClassCheckin.DoesNotExist:
            return JsonResponse({"error": "Check-in não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)

        return JsonResponse({
            "success": True,
            "status": checkin.status,
            "status_label": checkin.get_status_display(),
        })


class InstructorApproveSpecialCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES

    def post(self, request, *args, **kwargs):
        person = getattr(request, "portal_person", None)
        if not person:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            checkin_id = int(body["checkin_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            checkin = approve_special_checkin(instructor=person, checkin_id=checkin_id)
        except SpecialClassCheckin.DoesNotExist:
            return JsonResponse({"error": "Check-in não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)

        return JsonResponse({
            "success": True,
            "status": checkin.status,
            "status_label": checkin.get_status_display(),
        })
