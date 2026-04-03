import json

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import StripePlanPriceMapForm
from system.mixins import RoleRequiredMixin
from system.selectors import (
    get_checkout_allowed_subscriptions,
    get_checkout_requests_queryset,
    get_stripe_price_maps_queryset,
    get_stripe_subscription_links_queryset,
    get_webhook_processing_queryset,
)
from system.services.payments import create_customer_portal, is_stripe_configured, process_stripe_webhook, start_subscription_checkout


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class PaymentManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/payments/payment_dashboard.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_is_configured"] = is_stripe_configured()
        context["price_maps"] = get_stripe_price_maps_queryset()
        context["checkout_requests"] = get_checkout_requests_queryset()[:30]
        context["subscription_links"] = get_stripe_subscription_links_queryset()[:30]
        context["webhook_events"] = get_webhook_processing_queryset()[:30]
        context["price_map_form"] = kwargs.get("price_map_form") or StripePlanPriceMapForm(prefix="price_map")
        return context

    def post(self, request, *args, **kwargs):
        form = StripePlanPriceMapForm(request.POST, prefix="price_map")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(price_map_form=form))
        form.save()
        messages.success(request, "Mapeamento Stripe salvo.")
        return redirect("system:payment-dashboard")


class SubscriptionCheckoutStartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not is_stripe_configured():
            messages.error(request, "A integracao Stripe ainda nao esta configurada neste ambiente.")
            return redirect(self._get_redirect_target())
        local_subscription = self._get_subscription()
        try:
            checkout_request = start_subscription_checkout(
                actor_user=request.user,
                local_subscription=local_subscription,
                success_url=_resolve_absolute_url(
                    request,
                    configured_value=settings.STRIPE_CHECKOUT_SUCCESS_PATH,
                    fallback_name="system:my-invoices",
                ),
                cancel_url=_resolve_absolute_url(
                    request,
                    configured_value=settings.STRIPE_CHECKOUT_CANCEL_PATH,
                    fallback_name="system:my-invoices",
                ),
            )
        except ValidationError as exc:
            messages.error(request, _normalize_validation_error(exc))
            return redirect(self._get_redirect_target())
        except ImproperlyConfigured as exc:
            messages.error(request, str(exc))
            return redirect(self._get_redirect_target())
        except Exception:
            messages.error(request, "Nao foi possivel iniciar o checkout Stripe neste momento.")
            return redirect(self._get_redirect_target())
        return redirect(checkout_request.checkout_url)

    def _get_subscription(self):
        queryset = get_checkout_allowed_subscriptions(self.request.user)
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])

    def _get_redirect_target(self):
        return _resolve_safe_redirect_target(self.request, self.request.POST.get("next"), "system:my-invoices")


class CustomerPortalStartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not is_stripe_configured():
            messages.error(request, "A integracao Stripe ainda nao esta configurada neste ambiente.")
            return redirect(self._get_redirect_target())
        local_subscription = self._get_subscription()
        try:
            session = create_customer_portal(
                local_subscription=local_subscription,
                return_url=_resolve_absolute_url(
                    request,
                    configured_value=settings.STRIPE_CUSTOMER_PORTAL_RETURN_PATH,
                    fallback_name="system:my-invoices",
                ),
            )
        except ValidationError as exc:
            messages.error(request, _normalize_validation_error(exc))
            return redirect(self._get_redirect_target())
        except ImproperlyConfigured as exc:
            messages.error(request, str(exc))
            return redirect(self._get_redirect_target())
        except Exception:
            messages.error(request, "Nao foi possivel abrir o portal Stripe neste momento.")
            return redirect(self._get_redirect_target())
        return redirect(session["url"])

    def _get_subscription(self):
        queryset = get_checkout_allowed_subscriptions(self.request.user)
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])

    def _get_redirect_target(self):
        return _resolve_safe_redirect_target(self.request, self.request.POST.get("next"), "system:my-invoices")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        signature = request.headers.get("Stripe-Signature", "")
        try:
            processing, duplicate = process_stripe_webhook(payload=request.body, signature=signature)
        except (json.JSONDecodeError, ValueError, stripe.error.SignatureVerificationError):
            return JsonResponse({"status": "invalid"}, status=400)
        except Exception:
            return JsonResponse({"status": "error"}, status=500)
        return JsonResponse(
            {
                "status": "ok",
                "duplicate": duplicate,
                "event_id": processing.stripe_event_id,
                "event_type": processing.event_type,
            }
        )


def _resolve_absolute_url(request, *, configured_value, fallback_name):
    if configured_value.startswith("http://") or configured_value.startswith("https://"):
        return configured_value
    relative_path = configured_value or reverse(fallback_name)
    return request.build_absolute_uri(relative_path)


def _normalize_validation_error(error):
    if hasattr(error, "message_dict"):
        messages_list = []
        for values in error.message_dict.values():
            messages_list.extend(values)
        return " ".join(messages_list)
    if hasattr(error, "messages"):
        return " ".join(error.messages)
    return str(error)


def _resolve_safe_redirect_target(request, target, default_name):
    if target and url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return reverse(default_name)
