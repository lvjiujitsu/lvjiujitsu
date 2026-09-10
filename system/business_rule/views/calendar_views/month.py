from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView
from system.business_rule.constants import (
    CLASS_STAFF_PERSON_TYPE_CODES,
    Capability,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.business_rule.models import ClassSchedule, SpecialClass
from system.business_rule.services.class_calendar import (
    get_calendar_month_data,
    get_instructor_class_group_ids,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_capabilities, portal_person
from system.business_rule.models import ClassSchedule


@method_decorator(xframe_options_sameorigin, name="dispatch")
class CalendarView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES + CLASS_STAFF_PERSON_TYPE_CODES
    required_capabilities = (
        Capability.ACCESS_STUDENT_AREA,
        Capability.SUPPORT_CLASSES,
    )
    template_name = "business_rule/calendar/calendar.html"

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
        is_embedded = self.request.GET.get("embedded") == "1"
        context["is_embedded"] = is_embedded
        context["calendar_query_suffix"] = "?embedded=1" if is_embedded else ""

        person = portal_person(self.request)
        is_instructor = bool(
            person is not None
            and Capability.SUPPORT_CLASSES
            in portal_capabilities(self.request)
        )
        context["show_instructor_area"] = is_instructor

        owned_schedule_ids = []
        owned_special_ids = []
        if is_instructor:
            class_group_ids = get_instructor_class_group_ids(person)
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
