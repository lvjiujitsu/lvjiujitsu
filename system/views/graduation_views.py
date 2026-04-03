from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.forms import GraduationExamCreateForm, GraduationPanelFilterForm, GraduationParticipationDecisionForm
from system.mixins import RoleRequiredMixin
from system.models import GraduationExamParticipation
from system.selectors import (
    get_graduation_exams_queryset,
    get_graduation_panel_class_groups_queryset,
    get_graduation_panel_students_queryset,
)
from system.services.graduation import build_graduation_panel_candidates, open_graduation_exam, record_exam_participation_decision


GRADUATION_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO, ROLE_PROFESSOR)


class GraduationPanelView(RoleRequiredMixin, TemplateView):
    template_name = "system/graduation/graduation_panel.html"
    required_roles = GRADUATION_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_form = kwargs.get("filter_form") or self._build_filter_form()
        exam_form = kwargs.get("exam_form") or GraduationExamCreateForm(prefix="exam")
        filter_data = self._resolve_filter_data(filter_form)
        candidates = self._build_candidates(filter_data)
        context.update(
            {
                "filter_form": filter_form,
                "exam_form": exam_form,
                "candidates": candidates,
                "recent_exams": get_graduation_exams_queryset()[:5],
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        filter_form = self._build_filter_form()
        exam_form = GraduationExamCreateForm(request.POST, prefix="exam")
        if not exam_form.is_valid():
            return self.render_to_response(self.get_context_data(filter_form=filter_form, exam_form=exam_form))
        filter_data = self._resolve_filter_data(filter_form)
        selected_students = self._resolve_selected_students(filter_data)
        try:
            open_graduation_exam(
                title=exam_form.cleaned_data["title"],
                scheduled_for=exam_form.cleaned_data["scheduled_for"],
                actor=request.user,
                students=selected_students,
                discipline=filter_data["discipline"],
                class_group=filter_data["class_group"],
                notes=exam_form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            exam_form.add_error(None, exc)
            return self.render_to_response(self.get_context_data(filter_form=filter_form, exam_form=exam_form))
        messages.success(request, "Avaliacao de graduacao aberta.")
        return redirect("system:graduation-panel")

    def _build_filter_form(self):
        return GraduationPanelFilterForm(
            self.request.GET or None,
            prefix="filters",
            class_group_queryset=get_graduation_panel_class_groups_queryset(self.request.user),
        )

    def _resolve_filter_data(self, filter_form):
        if not filter_form.is_valid():
            return {"class_group": None, "discipline": None, "belt_rank": None, "eligible_only": True}
        class_group = filter_form.cleaned_data["class_group"]
        return {
            "class_group": class_group,
            "discipline": class_group.modality if class_group else None,
            "belt_rank": filter_form.cleaned_data["belt_rank"],
            "eligible_only": filter_form.cleaned_data["eligible_only"],
        }

    def _build_candidates(self, filter_data):
        students = get_graduation_panel_students_queryset(self.request.user, class_group=filter_data["class_group"])
        return build_graduation_panel_candidates(
            students,
            discipline=filter_data["discipline"],
            belt_rank=filter_data["belt_rank"],
            eligible_only=filter_data["eligible_only"],
        )

    def _resolve_selected_students(self, filter_data):
        selected_uuids = set(self.request.POST.getlist("selected_students"))
        selected_students = []
        for candidate in self._build_candidates({**filter_data, "eligible_only": False}):
            if str(candidate["student"].uuid) not in selected_uuids or not candidate["eligible"]:
                continue
            selected_students.append(candidate["student"])
        return selected_students


class GraduationParticipationDecisionView(RoleRequiredMixin, View):
    required_roles = GRADUATION_ROLE_CODES

    def post(self, request, *args, **kwargs):
        participation = self._get_participation()
        form = GraduationParticipationDecisionForm(request.POST, prefix=f"decision-{participation.uuid}")
        if not form.is_valid():
            for field_name, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field_name}: {error}")
            return redirect("system:graduation-panel")
        try:
            record_exam_participation_decision(
                participation,
                actor=request.user,
                status=form.cleaned_data["status"],
                target_belt=form.cleaned_data["target_belt"],
                target_degree=form.cleaned_data["target_degree"],
                decision_notes=form.cleaned_data["decision_notes"],
                promotion_date=form.cleaned_data["promotion_date"],
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("system:graduation-panel")
        messages.success(request, "Decisao de graduacao registrada.")
        return redirect("system:graduation-panel")

    def _get_participation(self):
        queryset = get_graduation_exams_queryset()
        if self.request.user.has_role(ROLE_PROFESSOR) and not self.request.user.has_any_role(
            ROLE_ADMIN_MASTER,
            ROLE_ADMIN_UNIDADE,
            ROLE_RECEPCAO,
        ):
            queryset = queryset.filter(class_group__in=get_graduation_panel_class_groups_queryset(self.request.user))
        participations = GraduationExamParticipation.objects.select_related(
            "exam__class_group",
            "student__user",
            "suggested_belt",
        ).filter(exam__in=queryset)
        return get_object_or_404(participations, uuid=self.kwargs["uuid"])
