from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from system.core.password_reset.service import (
    INTERNAL_RESET_SESSION_TOKEN,
    INTERNAL_RESET_URL_TOKEN,
    find_resettable_account,
    password_reset_done_context,
    remember_return_url,
    resolve_reset_credentials,
    send_password_reset_email,
    set_account_password,
)


class PasswordResetRequestView(FormView):
    success_url = reverse_lazy("system:password-reset-sent")

    def form_valid(self, form):
        kind, account = find_resettable_account(form.get_lookup_value())
        if account is not None:
            send_password_reset_email(
                kind, account, self.request.build_absolute_uri("/")
            )
        return super().form_valid(form)


class PasswordResetSentView(TemplateView):
    pass


class PasswordResetConfirmView(FormView):
    success_url = reverse_lazy("system:password-reset-done")

    def dispatch(self, request, *args, **kwargs):
        self.validlink = False
        self.kind = ""
        self.account = None
        identifier = kwargs["identifier"]
        token = kwargs["token"]
        if token == INTERNAL_RESET_URL_TOKEN:
            session_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN, "")
            resolved = resolve_reset_credentials(identifier, session_token)
            if resolved is not None:
                self.kind, self.account = resolved
                self.validlink = True
                return super().dispatch(request, *args, **kwargs)
        elif resolve_reset_credentials(identifier, token) is not None:
            request.session[INTERNAL_RESET_SESSION_TOKEN] = token
            return HttpResponseRedirect(
                reverse(
                    "system:password-reset-confirm",
                    args=[identifier, INTERNAL_RESET_URL_TOKEN],
                )
            )
        return self.render_to_response(self.get_context_data())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["account"] = self.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["validlink"] = self.validlink
        context["account"] = self.account
        if not self.validlink:
            context["form"] = None
        return context

    def record_reset(self, kind, account):
        return None

    def form_valid(self, form):
        set_account_password(
            self.kind, self.account, form.cleaned_data["new_password1"]
        )
        self.request.session.pop(INTERNAL_RESET_SESSION_TOKEN, None)
        remember_return_url(self.request, self.kind, self.account)
        self.record_reset(self.kind, self.account)
        return super().form_valid(form)


class PasswordResetDoneView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(password_reset_done_context(self.request))
        return context
