from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView
from system.core.http import safe_redirect_target
from system.business_rule.forms import PortalAuthenticationForm, PortalChangePasswordForm
from system.business_rule.models import PortalAccount
from system.business_rule.access import (
    is_technical_admin,
    login_portal_identity,
    logout_portal_identity,
    portal_account,
)
from system.business_rule.services import (
    FORCED_PASSWORD_CHANGE_SESSION_KEY,
    authenticate_portal_identity,
    change_own_password,
)


class LoginView(FormView):
    form_class = PortalAuthenticationForm
    template_name = "business_rule/login/login_form.html"

    def dispatch(self, request, *args, **kwargs):
        if portal_account(request) is not None or is_technical_admin(request):
            return redirect("system:dashboard-redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        identity = authenticate_portal_identity(
            identifier=form.cleaned_data["identifier"],
            password=form.cleaned_data["password"],
        )

        if identity is None:
            form.add_error(None, "CPF, acesso técnico ou senha inválidos.")
            return self.form_invalid(form)

        if identity.get("blocked_reason") == "must_change_password":
            self.request.session[FORCED_PASSWORD_CHANGE_SESSION_KEY] = identity["portal_account"].pk
            messages.info(
                self.request,
                "Por segurança, defina uma nova senha para continuar.",
            )
            return redirect("system:password-change")

        if identity.get("blocked_reason") == "payment_pending":
            pending_order = identity.get("pending_order")
            if pending_order is not None:
                self.request.session["pending_checkout_order_id"] = pending_order.pk
                messages.info(
                    self.request,
                    "Seu cadastro está aguardando a confirmação do pagamento. "
                    "Vamos redirecioná-lo para concluir agora.",
                )
                return redirect(
                    "system:payment-checkout", order_id=pending_order.pk
                )
            form.add_error(
                None,
                "Seu cadastro está aguardando a confirmação do pagamento. "
                "Conclua o pagamento para acessar o sistema.",
            )
            return self.form_invalid(form)

        login_portal_identity(
            self.request,
            portal_account=identity["portal_account"],
            technical_admin_user=identity["technical_admin_user"],
        )
        candidate = self.request.POST.get("next") or self.request.GET.get("next")
        return redirect(
            safe_redirect_target(
                self.request,
                candidate,
                fallback=reverse("system:dashboard-redirect"),
            )
        )


class LogoutView(View):
    redirect_target = "system:login"

    def post(self, request, *args, **kwargs):
        return self.sign_out(request)

    def sign_out(self, request):
        logout_portal_identity(request)
        return redirect(self.redirect_target)


class PortalChangePasswordView(FormView):
    form_class = PortalChangePasswordForm
    template_name = "business_rule/login/change_password_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.access_account = portal_account(request)
        self.is_mandatory = False
        if self.access_account is None:
            pending_id = request.session.get(FORCED_PASSWORD_CHANGE_SESSION_KEY)
            if pending_id:
                self.access_account = PortalAccount.objects.filter(
                    pk=pending_id, is_active=True
                ).first()
                self.is_mandatory = True
        if self.access_account is None:
            return redirect("system:login")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["access_account"] = self.access_account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_mandatory"] = self.is_mandatory
        return context

    def form_valid(self, form):
        change_own_password(self.access_account, form.cleaned_data["new_password1"])
        if self.is_mandatory:
            self.request.session.pop(FORCED_PASSWORD_CHANGE_SESSION_KEY, None)
            login_portal_identity(self.request, portal_account=self.access_account)
            messages.success(self.request, "Senha atualizada. Bem-vindo(a)!")
        else:
            messages.success(self.request, "Senha atualizada com sucesso.")
        return redirect("system:dashboard-redirect")
