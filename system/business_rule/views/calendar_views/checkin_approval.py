import json
from django.http import JsonResponse
from django.views import View
from system.core.audit import AuditAction
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES, Capability
from system.business_rule.constants import AuditModule
from system.business_rule.models.calendar import ClassCheckin, SpecialClassCheckin
from system.core.audit import record_event
from system.business_rule.services.class_calendar import (
    approve_class_checkin,
    approve_special_checkin,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_person


class InstructorApproveCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        record_event(
            person.full_name,
            AuditAction.APPROVED,
            AuditModule.CHECKIN,
            checkin.person.full_name,
            f"Presença aprovada na sessão de {checkin.session.date}.",
        )
        return JsonResponse({
            "success": True,
            "status": checkin.status,
            "status_label": checkin.get_status_display(),
        })


class InstructorApproveSpecialCheckinView(PortalRoleRequiredMixin, View):
    allowed_codes = CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_CLASSES,)

    def post(self, request, *args, **kwargs):
        person = portal_person(request)
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
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "status": checkin.status,
            "status_label": checkin.get_status_display(),
        })
