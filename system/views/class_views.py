from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import FormView, TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import ClassDisciplineForm, ClassGroupForm, ClassSessionForm, InstructorProfileForm
from system.mixins import RoleRequiredMixin
from system.selectors.class_selectors import (
    get_class_disciplines_queryset,
    get_class_groups_queryset,
    get_class_sessions_queryset,
    get_instructor_profiles_queryset,
)
from system.services.classes.session_lifecycle import close_class_session, open_class_session, save_class_session
from system.services.instructors.registry import create_or_update_instructor_profile


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class InstructorManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/instructors/instructors_list.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instructors"] = get_instructor_profiles_queryset()
        context["form"] = kwargs.get("form") or InstructorProfileForm(prefix="instructor")
        return context

    def post(self, request, *args, **kwargs):
        form = InstructorProfileForm(request.POST, prefix="instructor")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        create_or_update_instructor_profile(**form.cleaned_data)
        messages.success(request, "Professor salvo.")
        return redirect("system:instructor-list")


class InstructorUpdateView(RoleRequiredMixin, FormView):
    form_class = InstructorProfileForm
    template_name = "system/instructors/instructor_update.html"
    required_roles = ADMIN_ROLE_CODES

    def dispatch(self, request, *args, **kwargs):
        self.instructor = get_object_or_404(get_instructor_profiles_queryset(), uuid=self.kwargs["uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = "instructor"
        return kwargs

    def get_initial(self):
        return {
            "full_name": self.instructor.user.full_name,
            "cpf": self.instructor.user.cpf,
            "email": self.instructor.user.email,
            "belt_rank": self.instructor.belt_rank,
            "bio": self.instructor.bio,
            "specialties": self.instructor.specialties,
            "is_active": self.instructor.is_active,
        }

    def form_valid(self, form):
        create_or_update_instructor_profile(**form.cleaned_data)
        messages.success(self.request, "Professor atualizado.")
        return redirect("system:instructor-update", uuid=self.instructor.uuid)


class DisciplineManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/classes/disciplines_list.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["disciplines"] = get_class_disciplines_queryset()
        context["form"] = kwargs.get("form") or ClassDisciplineForm(prefix="discipline")
        return context

    def post(self, request, *args, **kwargs):
        form = ClassDisciplineForm(request.POST, prefix="discipline")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        form.save()
        messages.success(request, "Modalidade salva.")
        return redirect("system:discipline-list")


class DisciplineUpdateView(RoleRequiredMixin, FormView):
    form_class = ClassDisciplineForm
    template_name = "system/classes/discipline_update.html"
    required_roles = ADMIN_ROLE_CODES

    def dispatch(self, request, *args, **kwargs):
        self.discipline = get_object_or_404(get_class_disciplines_queryset(), uuid=self.kwargs["uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.discipline
        kwargs["prefix"] = "discipline"
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Modalidade atualizada.")
        return redirect("system:discipline-update", uuid=self.discipline.uuid)


class ClassGroupManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/classes/class_groups_list.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["class_groups"] = get_class_groups_queryset()
        context["form"] = kwargs.get("form") or ClassGroupForm(prefix="class_group")
        return context

    def post(self, request, *args, **kwargs):
        form = ClassGroupForm(request.POST, prefix="class_group")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        class_group = form.save(commit=False)
        class_group.full_clean()
        class_group.save()
        messages.success(request, "Turma salva.")
        return redirect("system:class-group-list")


class ClassGroupUpdateView(RoleRequiredMixin, FormView):
    form_class = ClassGroupForm
    template_name = "system/classes/class_group_update.html"
    required_roles = ADMIN_ROLE_CODES

    def dispatch(self, request, *args, **kwargs):
        self.class_group = get_object_or_404(get_class_groups_queryset(), uuid=self.kwargs["uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.class_group
        kwargs["prefix"] = "class_group"
        return kwargs

    def form_valid(self, form):
        class_group = form.save(commit=False)
        class_group.full_clean()
        class_group.save()
        messages.success(self.request, "Turma atualizada.")
        return redirect("system:class-group-update", uuid=self.class_group.uuid)


class ClassSessionManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/classes/sessions_list.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = get_class_sessions_queryset()
        context["form"] = kwargs.get("form") or ClassSessionForm(prefix="session")
        return context

    def post(self, request, *args, **kwargs):
        form = ClassSessionForm(request.POST, prefix="session")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        session = form.save(commit=False)
        save_class_session(session)
        messages.success(request, "Sessao salva.")
        return redirect("system:session-list")


class ClassSessionOpenView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(get_class_sessions_queryset(), uuid=self.kwargs["uuid"])
        open_class_session(session, request.user)
        messages.success(request, "Sessao aberta.")
        return redirect("system:session-list")


class ClassSessionCloseView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(get_class_sessions_queryset(), uuid=self.kwargs["uuid"])
        close_class_session(session, request.user)
        messages.success(request, "Sessao encerrada.")
        return redirect("system:session-list")
