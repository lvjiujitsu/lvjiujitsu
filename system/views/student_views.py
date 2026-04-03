from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import (
    AccountPasswordChangeForm,
    CertificateLookupForm,
    DependentOnboardingFormSet,
    DocumentRecordUploadForm,
    EmergencyRecordForm,
    GuardianLinkForm,
    HolderOnboardingForm,
    LgpdRequestForm,
    OnboardingTermsForm,
    ProfileUpdateForm,
    StudentRecordForm,
)
from system.forms.student_forms import deserialize_step_payload, get_onboarding_terms, serialize_step_payload
from system.mixins import RoleRequiredMixin
from system.models import AuthenticationEvent, LgpdRequest, LocalSubscription, SensitiveAccessLog
from system.models.student_models import GuardianRelationship
from system.selectors import get_student_document_history, get_user_document_history
from system.selectors.student_selectors import get_student_management_queryset, get_visible_students_for_user
from system.services.auth.audit import record_authentication_event
from system.services.lgpd import confirm_lgpd_request, create_lgpd_request, record_sensitive_access, register_document_record
from system.services.onboarding.workflow import submit_household_onboarding
from system.services.students.registry import (
    create_guardian_relationship,
    create_or_update_identity,
    ensure_emergency_record,
)


ONBOARDING_HOLDER_SESSION_KEY = "onboarding_holder"
ONBOARDING_DEPENDENTS_SESSION_KEY = "onboarding_dependents"
ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class OnboardingHolderStepView(FormView):
    form_class = HolderOnboardingForm
    template_name = "system/students/onboarding_holder.html"
    success_url = reverse_lazy("system:onboarding-dependents")

    def get_initial(self):
        return self.request.session.get(ONBOARDING_HOLDER_SESSION_KEY, {})

    def form_valid(self, form):
        self.request.session[ONBOARDING_HOLDER_SESSION_KEY] = serialize_step_payload(form.cleaned_data)
        return super().form_valid(form)


class OnboardingDependentsStepView(TemplateView):
    template_name = "system/students/onboarding_dependents.html"

    def get(self, request, *args, **kwargs):
        holder_data = self._get_holder_data()
        if holder_data is None:
            return redirect("system:onboarding-holder")
        context = self.get_context_data(formset=self._build_formset(holder_data["holder_cpf"]))
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        holder_data = self._get_holder_data()
        if holder_data is None:
            return redirect("system:onboarding-holder")
        formset = self._build_formset(holder_data["holder_cpf"], data=request.POST)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        self._store_dependents(formset)
        return redirect("system:onboarding-confirm")

    def _build_formset(self, holder_cpf, data=None):
        return DependentOnboardingFormSet(data=data, prefix="dependents", holder_cpf=holder_cpf)

    def _get_holder_data(self):
        return self.request.session.get(ONBOARDING_HOLDER_SESSION_KEY)

    def _store_dependents(self, formset):
        dependents = []
        for form in formset.forms:
            if self._should_skip_form(form):
                continue
            dependents.append(serialize_step_payload(form.cleaned_data))
        self.request.session[ONBOARDING_DEPENDENTS_SESSION_KEY] = dependents

    def _should_skip_form(self, form):
        if not form.cleaned_data:
            return True
        return form.cleaned_data.get("skip_form") or not form.cleaned_data.get("cpf")


class OnboardingConfirmStepView(FormView):
    form_class = OnboardingTermsForm
    template_name = "system/students/onboarding_confirm.html"
    success_url = reverse_lazy("system:login")

    def dispatch(self, request, *args, **kwargs):
        self.holder_data = request.session.get(ONBOARDING_HOLDER_SESSION_KEY)
        self.dependents_data = request.session.get(ONBOARDING_DEPENDENTS_SESSION_KEY, [])
        if self.holder_data is None:
            return redirect("system:onboarding-holder")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["terms"] = get_onboarding_terms()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["holder_data"] = self.holder_data
        context["dependents_data"] = self.dependents_data
        return context

    def form_valid(self, form):
        result = submit_household_onboarding(
            holder_data=deserialize_step_payload(self.holder_data),
            dependents_data=[deserialize_step_payload(item) for item in self.dependents_data],
            accepted_term_ids=form.get_accepted_term_ids(),
            request=self.request,
        )
        self._clear_session_steps()
        messages.success(self.request, "Cadastro concluido com sucesso.")
        messages.info(self.request, f"Titular cadastrado: {result['holder_user'].full_name}.")
        return super().form_valid(form)

    def _clear_session_steps(self):
        self.request.session.pop(ONBOARDING_HOLDER_SESSION_KEY, None)
        self.request.session.pop(ONBOARDING_DEPENDENTS_SESSION_KEY, None)


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = "system/students/my_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_forms())
        context["visible_students"] = get_visible_students_for_user(self.request.user)
        context["lgpd_requests"] = self.request.user.lgpd_requests.all()
        context.update(get_user_document_history(self.request.user))
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        handlers = {
            "confirm_lgpd": self._handle_lgpd_confirmation,
            "profile": self._handle_profile_update,
            "password": self._handle_password_change,
            "lgpd": self._handle_lgpd_request,
        }
        handler = handlers.get(action, self._invalid_action)
        return handler()

    def _build_forms(self):
        user = self.request.user
        return {
            "certificate_lookup_form": CertificateLookupForm(prefix="certificate"),
            "profile_form": ProfileUpdateForm(instance=user, prefix="profile"),
            "password_form": AccountPasswordChangeForm(user=user, prefix="password"),
            "lgpd_form": LgpdRequestForm(prefix="lgpd"),
        }

    def _handle_profile_update(self):
        form = ProfileUpdateForm(self.request.POST, instance=self.request.user, prefix="profile")
        if not form.is_valid():
            return self._render_with_forms(profile_form=form)
        form.save()
        self._record_profile_update()
        messages.success(self.request, "Perfil atualizado.")
        return redirect("system:my-profile")

    def _handle_password_change(self):
        form = AccountPasswordChangeForm(self.request.POST, user=self.request.user, prefix="password")
        if not form.is_valid():
            return self._render_with_forms(password_form=form)
        self._persist_password_change(form.cleaned_data["new_password"])
        messages.success(self.request, "Senha alterada.")
        return redirect("system:my-profile")

    def _handle_lgpd_request(self):
        form = LgpdRequestForm(self.request.POST, prefix="lgpd")
        if not form.is_valid():
            return self._render_with_forms(lgpd_form=form)
        lgpd_request = create_lgpd_request(
            user=self.request.user,
            request_type=form.cleaned_data["request_type"],
            notes=form.cleaned_data["notes"],
        )
        if lgpd_request.requires_confirmation:
            messages.warning(self.request, "Solicitacao LGPD criada. Confirme a intencao para liberar o processamento.")
        else:
            messages.success(self.request, "Solicitacao LGPD registrada.")
        return redirect("system:my-profile")

    def _invalid_action(self):
        messages.error(self.request, "Acao invalida.")
        return redirect("system:my-profile")

    def _handle_lgpd_confirmation(self):
        lgpd_request = get_object_or_404(self._get_user_lgpd_queryset(), uuid=self.request.POST.get("request_uuid"))
        confirm_lgpd_request(lgpd_request=lgpd_request, actor_user=self.request.user)
        messages.success(self.request, "Solicitacao LGPD confirmada.")
        return redirect("system:my-profile")

    def _render_with_forms(self, **overrides):
        context = self.get_context_data()
        context.update(overrides)
        return self.render_to_response(context)

    def _get_user_lgpd_queryset(self):
        queryset = self.request.user.lgpd_requests
        return queryset.filter(status__in=(LgpdRequest.STATUS_OPEN, LgpdRequest.STATUS_IN_PROGRESS))

    def _record_profile_update(self):
        record_authentication_event(
            AuthenticationEvent.EVENT_PROFILE_UPDATE,
            self.request,
            actor_user=self.request.user,
        )

    def _persist_password_change(self, new_password):
        self.request.user.set_password(new_password)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["password", "must_change_password", "updated_at"])
        update_session_auth_hash(self.request, self.request.user)
        record_authentication_event(
            AuthenticationEvent.EVENT_PASSWORD_CHANGE,
            self.request,
            actor_user=self.request.user,
        )


class StudentManagementListView(RoleRequiredMixin, ListView):
    template_name = "system/students/student_list.html"
    context_object_name = "students"
    paginate_by = 20
    required_roles = ADMIN_ROLE_CODES

    def get_queryset(self):
        filters = {
            "name": self.request.GET.get("name", ""),
            "cpf": self.request.GET.get("cpf", ""),
            "status": self.request.GET.get("status", ""),
            "responsible": self.request.GET.get("responsible", ""),
        }
        return get_student_management_queryset(filters)


class StudentManagementUpdateView(RoleRequiredMixin, TemplateView):
    template_name = "system/students/student_update.html"
    required_roles = ADMIN_ROLE_CODES

    def dispatch(self, request, *args, **kwargs):
        self.student = self._get_student()
        response = super().dispatch(request, *args, **kwargs)
        if request.method == "GET":
            self._record_emergency_access()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student"] = self.student
        context.update(self._build_document_context())
        context["student_form"] = kwargs.get("student_form") or self._build_student_form()
        context["document_form"] = kwargs.get("document_form") or self._build_document_form()
        context["emergency_form"] = kwargs.get("emergency_form") or self._build_emergency_form()
        context["guardian_form"] = kwargs.get("guardian_form") or GuardianLinkForm(prefix="guardian")
        context["guardian_links"] = self.student.guardian_links.select_related("responsible_user")
        context["student_lgpd_requests"] = self.student.user.lgpd_requests.all()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        handlers = {
            "document": self._handle_document_upload,
            "student": self._handle_student_update,
            "emergency": self._handle_emergency_update,
            "guardian": self._handle_guardian_update,
        }
        return handlers.get(action, self._invalid_action)()

    def _build_student_form(self):
        initial = {
            "full_name": self.student.user.full_name,
            "email": self.student.user.email,
            "timezone": self.student.user.timezone,
            "birth_date": self.student.birth_date,
            "contact_phone": self.student.contact_phone,
            "operational_status": self.student.operational_status,
            "self_service_access": self.student.self_service_access,
        }
        return StudentRecordForm(initial=initial, prefix="student")

    def _build_emergency_form(self):
        instance = getattr(self.student, "emergency_record", None)
        return EmergencyRecordForm(instance=instance, prefix="emergency")

    def _build_document_form(self):
        form = DocumentRecordUploadForm(prefix="document")
        form.fields["subscription"].queryset = self._get_student_subscriptions()
        return form

    def _build_document_context(self):
        return get_student_document_history(self.student)

    def _handle_student_update(self):
        form = StudentRecordForm(self.request.POST, prefix="student")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(student_form=form))
        self._save_student_identity(form.cleaned_data)
        messages.success(self.request, "Aluno atualizado.")
        return redirect("system:student-update", uuid=self.student.uuid)

    def _handle_emergency_update(self):
        form = EmergencyRecordForm(self.request.POST, prefix="emergency")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(emergency_form=form))
        ensure_emergency_record(self.student, form.cleaned_data)
        self._record_emergency_update()
        messages.success(self.request, "Prontuario atualizado.")
        return redirect("system:student-update", uuid=self.student.uuid)

    def _handle_guardian_update(self):
        form = GuardianLinkForm(self.request.POST, prefix="guardian")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(guardian_form=form))
        responsible_user, _ = create_or_update_identity(
            cpf=form.cleaned_data["responsible_cpf"],
            full_name=form.cleaned_data["responsible_full_name"],
            email=form.cleaned_data["responsible_email"],
        )
        create_guardian_relationship(
            student=self.student,
            responsible_user=responsible_user,
            relationship_type=form.cleaned_data["relationship_type"],
            is_primary=form.cleaned_data["is_primary"],
            is_financial_responsible=form.cleaned_data["is_financial_responsible"],
            replace_existing_primary=form.cleaned_data["is_primary"],
        )
        messages.success(self.request, "Responsavel vinculado.")
        return redirect("system:student-update", uuid=self.student.uuid)

    def _handle_document_upload(self):
        form = DocumentRecordUploadForm(self.request.POST, self.request.FILES, prefix="document")
        form.fields["subscription"].queryset = self._get_student_subscriptions()
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(document_form=form))
        self._persist_document_record(form.cleaned_data)
        messages.success(self.request, "Documento historico registrado.")
        return redirect("system:student-update", uuid=self.student.uuid)

    def _invalid_action(self):
        messages.error(self.request, "Acao invalida.")
        return redirect("system:student-update", uuid=self.student.uuid)

    def _get_student(self):
        queryset = get_student_management_queryset()
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])

    def _record_emergency_access(self):
        if not hasattr(self.student, "emergency_record"):
            return
        record_sensitive_access(
            actor_user=self.request.user,
            student=self.student,
            access_type=SensitiveAccessLog.ACCESS_EMERGENCY_VIEW,
            access_purpose="Consulta administrativa do prontuario.",
        )

    def _save_student_identity(self, cleaned_data):
        user = self.student.user
        user.full_name = cleaned_data["full_name"]
        user.email = cleaned_data["email"]
        user.timezone = cleaned_data["timezone"]
        user.save()
        self.student.birth_date = cleaned_data["birth_date"]
        self.student.contact_phone = cleaned_data["contact_phone"]
        self.student.operational_status = cleaned_data["operational_status"]
        self.student.self_service_access = cleaned_data["self_service_access"]
        self.student.full_clean()
        self.student.save()

    def _persist_document_record(self, cleaned_data):
        register_document_record(
            owner_user=self.student.user,
            student=self.student,
            uploaded_by=self.request.user,
            uploaded_file=cleaned_data["file"],
            document_type=cleaned_data["document_type"],
            title=cleaned_data["title"],
            version_label=cleaned_data["version_label"],
            subscription=cleaned_data["subscription"],
            is_visible_to_owner=cleaned_data["is_visible_to_owner"],
            notes=cleaned_data["notes"],
        )

    def _get_student_subscriptions(self):
        queryset = LocalSubscription.objects.select_related("plan", "responsible_user")
        return queryset.filter(covered_students__student=self.student).distinct()

    def _record_emergency_update(self):
        record_sensitive_access(
            actor_user=self.request.user,
            student=self.student,
            access_type=SensitiveAccessLog.ACCESS_EMERGENCY_UPDATE,
            access_purpose="Atualizacao administrativa de prontuario.",
        )


class StudentManagementToggleStatusView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        student = self._get_student()
        self._toggle_student(student)
        messages.success(request, "Status do aluno atualizado.")
        return HttpResponseRedirect(reverse("system:student-update", kwargs={"uuid": student.uuid}))

    def _get_student(self):
        queryset = get_student_management_queryset()
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])

    def _toggle_student(self, student):
        student.is_active = not student.is_active
        student.operational_status = "INACTIVE" if not student.is_active else "ACTIVE"
        student.save(update_fields=["is_active", "operational_status", "updated_at"])


class GuardianRelationshipDeactivateView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        link = get_object_or_404(self._get_queryset(), uuid=self.kwargs["uuid"])
        link.end_date = timezone.localdate()
        link.save(update_fields=["end_date", "updated_at"])
        messages.success(request, "Vinculo encerrado.")
        return HttpResponseRedirect(reverse("system:student-update", kwargs={"uuid": link.student.uuid}))

    def _get_queryset(self):
        return GuardianRelationship.objects.select_related("student")
