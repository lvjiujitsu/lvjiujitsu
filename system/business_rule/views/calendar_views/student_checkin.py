import json
from django.http import JsonResponse
from django.views import View
from system.business_rule.models import ClassSchedule, SpecialClass
from system.business_rule.models.person import Person
from system.business_rule.services.class_calendar import (
    cancel_student_checkin,
    cancel_student_special_class_checkin,
    perform_checkin,
    perform_special_class_checkin,
)
from system.business_rule.access import PortalLoginRequiredMixin, portal_person
from system.business_rule.models import ClassSchedule
from system.business_rule.views.calendar_views.shared import resolve_checkin_actor


class StudentCheckinView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        actor = portal_person(request)
        if not actor:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            schedule_id = int(body["schedule_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            person = resolve_checkin_actor(actor, body)
        except (ValueError, Person.DoesNotExist):
            return JsonResponse({"error": "Pessoa inválida para este check-in."}, status=403)

        try:
            checkin, created = perform_checkin(person, schedule_id)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception:
            return JsonResponse({"error": "Erro ao registrar check-in."}, status=500)

        return JsonResponse({
            "success": True,
            "created": created,
            "message": "Check-in realizado!" if created else "Você já fez check-in nesta aula.",
        })


class StudentCheckinCancelView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        actor = portal_person(request)
        if not actor:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            schedule_id = int(body["schedule_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            person = resolve_checkin_actor(actor, body)
        except (ValueError, Person.DoesNotExist):
            return JsonResponse({"error": "Pessoa inválida para este check-in."}, status=403)

        try:
            _, changed = cancel_student_checkin(person, schedule_id)
        except ClassSchedule.DoesNotExist:
            return JsonResponse({"error": "Aula não encontrada."}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "changed": changed,
            "message": "Check-in desfeito." if changed else "Nenhum check-in pendente encontrado.",
        })


class StudentSpecialClassCheckinView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        actor = portal_person(request)
        if not actor:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            person = resolve_checkin_actor(actor, body)
        except (ValueError, Person.DoesNotExist):
            return JsonResponse({"error": "Pessoa inválida para este check-in."}, status=403)

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


class StudentSpecialClassCheckinCancelView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        actor = portal_person(request)
        if not actor:
            return JsonResponse({"error": "Não autenticado."}, status=403)

        try:
            body = json.loads(request.body)
            special_id = int(body["special_id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        try:
            person = resolve_checkin_actor(actor, body)
        except (ValueError, Person.DoesNotExist):
            return JsonResponse({"error": "Pessoa inválida para este check-in."}, status=403)

        try:
            _, changed = cancel_student_special_class_checkin(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "success": True,
            "changed": changed,
            "message": "Check-in desfeito." if changed else "Nenhum check-in pendente encontrado.",
        })
