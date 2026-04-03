from datetime import timedelta
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView

from system.constants import PASSWORD_ACTION_RESET
from system.forms import CpfLoginForm, PasswordActionConfirmForm, PasswordActionRequestForm
from system.models import AuthenticationEvent
from system.services.auth.audit import record_authentication_event
from system.services.auth.tokens import consume_password_action_token, get_usable_password_action_token, issue_password_action_token


class CpfLoginView(FormView):
    form_class = CpfLoginForm
    template_name = "system/auth/login.html"

    def form_valid(self, form):
        if self._is_locked():
            form.add_error(None, "Muitas tentativas. Aguarde alguns minutos e tente novamente.")
            return self.form_invalid(form)
        user = authenticate(
            self.request,
            cpf=form.cleaned_data["cpf"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            self._register_failure()
            record_authentication_event(
                AuthenticationEvent.EVENT_LOGIN_FAILURE,
                self.request,
                identifier=form.cleaned_data["cpf"],
                metadata={"reason": "invalid_credentials"},
            )
            form.add_error(None, "CPF ou senha invalidos.")
            return self.form_invalid(form)
        login(self.request, user)
        self.request.session["active_timezone"] = user.timezone
        self._clear_failures()
        record_authentication_event(
            AuthenticationEvent.EVENT_LOGIN_SUCCESS,
            self.request,
            actor_user=user,
            identifier=user.cpf,
        )
        return redirect("system:portal-dashboard")

    def _register_failure(self):
        failed_attempts = self.request.session.get("login_failed_attempts", 0) + 1
        self.request.session["login_failed_attempts"] = failed_attempts
        if failed_attempts >= settings.AUTH_LOGIN_MAX_FAILED_ATTEMPTS:
            lock_until = timezone.now() + timedelta(minutes=settings.AUTH_LOGIN_LOCK_MINUTES)
            self.request.session["login_locked_until"] = lock_until.isoformat()

    def _clear_failures(self):
        self.request.session.pop("login_failed_attempts", None)
        self.request.session.pop("login_locked_until", None)

    def _is_locked(self):
        locked_until = self.request.session.get("login_locked_until")
        if not locked_until:
            return False
        return timezone.now() < datetime.fromisoformat(locked_until).astimezone(timezone.get_current_timezone())


class SystemLogoutView(LogoutView):
    next_page = "system:home"
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            record_authentication_event(
                AuthenticationEvent.EVENT_LOGOUT,
                request,
                actor_user=request.user,
                identifier=request.user.cpf,
            )
        return super().dispatch(request, *args, **kwargs)


class PasswordActionRequestView(FormView):
    form_class = PasswordActionRequestForm
    template_name = "system/auth/password_action_request.html"

    def dispatch(self, request, *args, **kwargs):
        self.purpose = kwargs.get("purpose", PASSWORD_ACTION_RESET)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["purpose"] = self.purpose
        return context

    def form_valid(self, form):
        issue_password_action_token(self.request, form.cleaned_data["cpf"], self.purpose)
        messages.success(
            self.request,
            "Se existir uma conta valida para este CPF, o token de acesso foi emitido.",
        )
        return redirect("system:login")


class PasswordActionConfirmView(FormView):
    form_class = PasswordActionConfirmForm
    template_name = "system/auth/password_action_confirm.html"

    def dispatch(self, request, *args, **kwargs):
        self.purpose = kwargs["purpose"]
        self.password_action_token = get_usable_password_action_token(kwargs["token"], self.purpose)
        if self.password_action_token is None:
            raise Http404("Token invalido.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["purpose"] = self.purpose
        return context

    def form_valid(self, form):
        consume_password_action_token(
            self.request,
            self.password_action_token,
            form.cleaned_data["password"],
        )
        messages.success(self.request, "Senha definida com sucesso.")
        return redirect("system:login")
