import json
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from system.business_rule.forms.class_forms import SpecialClassForm
from system.business_rule.constants import CLASS_STAFF_PERSON_TYPE_CODES, Capability
from system.business_rule.models import SpecialClass
from system.business_rule.services.class_calendar import (
    assert_instructor_owns_special,
    create_special_class,
    delete_special_class,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_person


class InstructorSpecialClassCreateView(PortalRoleRequiredMixin, View):
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

        body["teacher"] = person.pk

        form = SpecialClassForm(data=body)
        if not form.is_valid():
            return JsonResponse({"error": "Dados inválidos.", "fields": form.errors}, status=400)

        special = create_special_class(
            title=form.cleaned_data["title"],
            session_date=form.cleaned_data["date"],
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
            assert_instructor_owns_special(person, special_id)
        except SpecialClass.DoesNotExist:
            return JsonResponse({"error": "Aulão não encontrado."}, status=404)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)

        delete_special_class(special_id)
        return JsonResponse({"success": True})
