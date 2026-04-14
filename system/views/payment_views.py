import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from system.models.registration_order import RegistrationOrder
from system.services.stripe_checkout import (
    StripeCheckoutError,
    create_checkout_session_for_order,
    process_stripe_event,
    verify_webhook_event,
)


logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(View):
    def post(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def get(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def _start(self, request, order_id):
        try:
            order = RegistrationOrder.objects.prefetch_related("items").get(
                pk=order_id
            )
        except RegistrationOrder.DoesNotExist:
            raise Http404("Pedido não encontrado")

        try:
            session = create_checkout_session_for_order(order, request)
        except StripeCheckoutError as exc:
            logger.error("Falha ao criar sessão Stripe: %s", exc)
            return HttpResponseBadRequest(str(exc))
        except Exception as exc:
            logger.exception("Erro inesperado na criação da sessão Stripe")
            return HttpResponseBadRequest("Erro ao iniciar pagamento")

        return redirect(session.url, permanent=False)


class PaymentSuccessView(View):
    def get(self, request, *args, **kwargs):
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
            "Stripe event processed: id=%s type=%s order=%s duplicate=%s",
            event["id"],
            event["type"],
            getattr(result["order"], "pk", None),
            result["duplicate"],
        )
        return HttpResponse(status=200)
