import json
from django.http import JsonResponse
from django.views import View
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES, Capability
from system.business_rule.models import ClassSchedule, SpecialClass
from system.business_rule.services.class_calendar import (
    assign_session_substitute,
    assign_special_substitute,
    assert_instructor_owns_schedule,
    cancel_class_without_instructor,
    cancel_special_without_instructor,
    toggle_session_cancel,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_person
from system.business_rule.models import ClassSchedule


class InstructorToggleSessionView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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


class InstructorSessionSubstituteView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
