import logging

from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from system.business_rule.services.stripe_checkout import verify_webhook_event, StripeCheckoutError
from system.business_rule.services.stripe_webhooks import process_stripe_event


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = verify_webhook_event(payload, sig_header)
        except StripeCheckoutError as exc:
            logger.error("Webhook Stripe — configuração inválida: %s", exc)
            return HttpResponse(status=500)
        except Exception as exc:
            logger.warning("Webhook Stripe — assinatura inválida: %s", exc)
            return HttpResponse(status=400)

        try:
            result = process_stripe_event(event)
        except Exception:
            logger.exception(
                "Webhook Stripe — falha ao processar evento %s (%s)",
                event["id"] if "id" in event else None,
                event["type"] if "type" in event else None,
            )
            return HttpResponse(status=500)

        logger.info(
            "Stripe event processed: id=%s type=%s order=%s membership=%s duplicate=%s",
            event["id"],
            event["type"],
            getattr(result.get("order"), "pk", None),
            getattr(result.get("membership"), "pk", None),
            result.get("duplicate"),
        )
        return HttpResponse(status=200)
