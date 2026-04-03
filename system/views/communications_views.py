from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import BulkCommunicationForm, NoticeBoardMessageForm
from system.mixins import RoleRequiredMixin
from system.selectors import get_active_notice_board_messages_for_user, get_communication_center_context
from system.services.communications import create_bulk_communication, create_notice_board_message


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class NoticeBoardView(LoginRequiredMixin, TemplateView):
    template_name = "system/communications/notice_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notices"] = get_active_notice_board_messages_for_user(self.request.user)
        return context


class CommunicationCenterView(RoleRequiredMixin, TemplateView):
    template_name = "system/communications/communication_center.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_communication_center_context())
        context["notice_form"] = kwargs.get("notice_form") or NoticeBoardMessageForm(prefix="notice")
        context["bulk_form"] = kwargs.get("bulk_form") or BulkCommunicationForm(prefix="bulk")
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "notice":
            return self._handle_notice()
        if action == "bulk":
            return self._handle_bulk()
        messages.error(request, "Acao invalida.")
        return self.render_to_response(self.get_context_data())

    def _handle_notice(self):
        form = NoticeBoardMessageForm(self.request.POST, prefix="notice")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(notice_form=form))
        create_notice_board_message(actor_user=self.request.user, **form.cleaned_data)
        messages.success(self.request, "Aviso publicado no mural.")
        return self.render_to_response(self.get_context_data())

    def _handle_bulk(self):
        form = BulkCommunicationForm(self.request.POST, prefix="bulk")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(bulk_form=form))
        create_bulk_communication(actor_user=self.request.user, **form.cleaned_data)
        messages.success(self.request, "Comunicado enfileirado para envio.")
        return self.render_to_response(self.get_context_data())
