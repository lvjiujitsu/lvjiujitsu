import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from system.models.person import PersonRelationship, PersonRelationshipKind
from system.models.registration_order import (
    PaymentStatus,
    RegistrationOrder,
)
from system.services.membership import get_latest_open_order
from system.services.stripe_checkout import (
    StripeCheckoutError,
    create_checkout_session_for_order,
    verify_webhook_event,
)
from system.services.stripe_webhooks import process_stripe_event
from system.services.trial_access import grant_trial_for_order


logger = logging.getLogger(__name__)


def _redirect_missing_order(request):
    messages.error(request, "Pedido não encontrado.")
    return redirect("system:root")


def _redirect_payment_unavailable(request, order, provider_label):
    messages.error(
        request,
        f"{provider_label} indisponível no momento. "
        "Você pode tentar outro método ou concluir e pagar depois.",
    )
    return redirect("system:payment-checkout", order_id=order.pk)


def _is_authorized_for_order(request, order):
    person = order.person
    portal_person = getattr(request, "portal_person", None)
    if portal_person and portal_person.pk == person.pk:
        return True
    if portal_person and PersonRelationship.objects.filter(
        source_person=person,
        target_person=portal_person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists():
        return True
    if portal_person and PersonRelationship.objects.filter(
        source_person=portal_person,
        target_person=person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists():
        return True
    if getattr(request, "portal_is_technical_admin", False):
        return True
    session_order_id = request.session.get("pending_checkout_order_id")
    if session_order_id and int(session_order_id) == order.pk:
        return True
    return False


class PaymentMethodChoiceView(View):
    """Tela intermediária onde o aluno escolhe Cartão (Stripe) ou PIX (Asaas)."""

    def get(self, request, order_id, *args, **kwargs):
        try:
            order = RegistrationOrder.objects.select_related("plan", "person").get(
                pk=order_id
            )
        except RegistrationOrder.DoesNotExist:
            return _redirect_missing_order(request)
        if not _is_authorized_for_order(request, order):
            return _redirect_missing_order(request)
        if order.payment_status in (
            PaymentStatus.PAID,
            PaymentStatus.EXEMPTED,
            PaymentStatus.REFUNDED,
        ):
            messages.info(request, "Este pedido já foi processado.")
            return redirect("system:dashboard-redirect")
        return render(
            request,
            "billing/payment_method_choice.html",
            {"order": order},
        )


class CreateCheckoutSessionView(View):
    def post(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def get(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def _start(self, request, order_id):
        try:
            order = RegistrationOrder.objects.select_related("plan", "person").get(
                pk=order_id
            )
        except RegistrationOrder.DoesNotExist:
            return _redirect_missing_order(request)

        if order.payment_status in (
            PaymentStatus.PAID,
            PaymentStatus.EXEMPTED,
            PaymentStatus.REFUNDED,
        ):
            messages.info(request, "Este pedido já foi processado.")
            return redirect("system:dashboard-redirect")

        if not _is_authorized_for_order(request, order):
            return _redirect_missing_order(request)

        try:
            session = create_checkout_session_for_order(order, request)
        except StripeCheckoutError as exc:
            logger.error("Falha ao criar sessão Stripe: %s", exc)
            return _redirect_payment_unavailable(request, order, "Pagamento com cartão")
        except Exception:
            logger.exception("Erro inesperado na criação da sessão Stripe")
            return _redirect_payment_unavailable(request, order, "Pagamento com cartão")

        return redirect(session.url, permanent=False)


class DeferPaymentView(View):
    def get(self, request, order_id, *args, **kwargs):
        return self._defer(request, order_id)

    def post(self, request, order_id, *args, **kwargs):
        return self._defer(request, order_id)

    def _defer(self, request, order_id):
        try:
            order = RegistrationOrder.objects.select_related("plan", "person").get(
                pk=order_id
            )
        except RegistrationOrder.DoesNotExist:
            return _redirect_missing_order(request)

        if not _is_authorized_for_order(request, order):
            return _redirect_missing_order(request)

        if order.payment_status in (
            PaymentStatus.PAID,
            PaymentStatus.EXEMPTED,
            PaymentStatus.REFUNDED,
        ):
            messages.info(request, "Este pedido já foi processado.")
            return redirect("system:dashboard-redirect")

        grant_trial_for_order(
            order,
            notes="Pagamento adiado pelo usuário na tela de checkout.",
        )
        request.session["pending_checkout_order_id"] = order.pk
        messages.warning(
            request,
            "Cadastro concluído sem pagamento. Você tem 1 aula experimental "
            "liberada e pode pagar depois para ativar sua mensalidade.",
        )
        return redirect("system:legacy-login-form")


class RetryPendingOrderView(View):
    def get(self, request, *args, **kwargs):
        return self._retry(request)

    def post(self, request, *args, **kwargs):
        return self._retry(request)

    def _retry(self, request):
        portal_person = getattr(request, "portal_person", None)
        if portal_person is None:
            session_order_id = request.session.get("pending_checkout_order_id")
            if not session_order_id:
                return redirect("system:login")
            return redirect("system:payment-checkout", order_id=session_order_id)
        order = get_latest_open_order(portal_person)
        if order is None:
            messages.info(request, "Não há pagamento pendente.")
            return redirect("system:dashboard-redirect")
        return redirect("system:payment-checkout", order_id=order.pk)


class PaymentSuccessView(View):
    def get(self, request, *args, **kwargs):
        request.session.pop("pending_checkout_order_id", None)
        messages.success(
            request,
            "Pagamento confirmado! Seu cadastro foi finalizado. Faça login para acessar o sistema.",
        )
        return redirect("system:legacy-login-form")


class PaymentCancelView(View):
    def get(self, request, *args, **kwargs):
        messages.warning(
            request,
            "Pagamento cancelado. Seu cadastro foi registrado mas ainda não está ativo — refaça o pagamento para concluir.",
        )
        return redirect("system:legacy-login-form")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = verify_webhook_event(payload, sig_header)
        except StripeCheckoutError as exc:
            logger.error("Webhook Stripe mal configurado: %s", exc)
            return HttpResponse(status=500)
        except ValueError:
            return HttpResponse(status=400)
        except Exception:
            logger.exception("Assinatura do webhook Stripe inválida")
            return HttpResponse(status=400)

        try:
            result = process_stripe_event(event)
        except Exception:
            logger.exception("Falha ao processar evento Stripe %s", event["id"])
            return HttpResponse(status=500)

        logger.info(
            "Stripe event processed: id=%s type=%s order=%s membership=%s duplicate=%s",
            event["id"],
            event["type"],
            getattr(result["order"], "pk", None),
            getattr(result["membership"], "pk", None),
            result["duplicate"],
        )
        return HttpResponse(status=200)
