from system.core.audit import AuditAction, record_event
from system.core.password_reset import (
    PasswordResetConfirmView as CorePasswordResetConfirmView,
    PasswordResetDoneView as CorePasswordResetDoneView,
    PasswordResetRequestView as CorePasswordResetRequestView,
    PasswordResetSentView as CorePasswordResetSentView,
)

from system.business_rule.constants import AuditModule
from system.business_rule.forms.password_reset_forms import (
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
)


class PasswordResetRequestView(CorePasswordResetRequestView):
    form_class = PasswordResetRequestForm
    template_name = "core/auth/password_reset_request.html"


class PasswordResetSentView(CorePasswordResetSentView):
    template_name = "core/auth/password_reset_sent.html"


class PasswordResetConfirmView(CorePasswordResetConfirmView):
    form_class = PasswordResetConfirmForm
    template_name = "core/auth/password_reset_confirm.html"

    def record_reset(self, kind, account):
        record_event(
            account.person.full_name,
            AuditAction.UPDATED,
            AuditModule.PERSON,
            account.person.full_name,
            "Senha redefinida pelo próprio usuário por e-mail.",
        )


class PasswordResetDoneView(CorePasswordResetDoneView):
    template_name = "core/auth/password_reset_done.html"
