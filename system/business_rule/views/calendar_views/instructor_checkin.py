import json
from django.http import JsonResponse
from django.views import View
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES, Capability
from system.business_rule.models import ClassSchedule, SpecialClass
from system.business_rule.services.class_calendar import (
    cancel_instructor_self_checkin,
    cancel_instructor_self_special_checkin,
    register_instructor_self_checkin,
    register_instructor_self_special_checkin,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_person
from system.business_rule.models import ClassSchedule


class InstructorSelfCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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


class InstructorSelfSpecialCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
