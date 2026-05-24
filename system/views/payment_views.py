from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from system.models.person import PersonRelationship, PersonRelationshipKind, PortalAccount
from system.models import PreRegistration, PreRegistrationStatus
from system.models.registration_order import (
    PaymentStatus,
    RegistrationOrder,
)
from system.services import login_portal_identity
from system.services.membership import get_latest_open_order
from system.services.trial_access import grant_trial_for_order


def _redirect_missing_order(request):
    messages.error(request, "Pedido não encontrado.")
    return redirect("system:root")


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
    """Direciona o pedido pendente para o checkout Asaas adequado."""

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
        if order.plan and order.plan.payment_method == "credit_card":
            return redirect("system:asaas-card-create", order_id=order.pk)
        return redirect("system:asaas-pix-create", order_id=order.pk)


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
        request.session["post_plan_payment_complete"] = True
        request.session["plan_order_id"] = order.pk
        request.session.pop("post_materials_payment_complete", None)
        request.session.pop("materials_order_id", None)
        if not order.person.is_active:
            request.session["pending_registration_person_id"] = order.person.pk
        messages.info(
            request,
            f"Você tem {settings.TRIAL_ACCESS_DEFAULT_CLASSES} aula(s) experimental(is) "
            "liberada. Finalize seu cadastro para ativar a mensalidade.",
        )
        return redirect("system:register")


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
        pre_registration_response = self._handle_pre_registration_success(request)
        if pre_registration_response is not None:
            return pre_registration_response

        order_id = request.session.pop("pending_checkout_order_id", None)
        order = None

        if order_id:
            try:
                order = RegistrationOrder.objects.select_related("person").get(pk=order_id)
            except RegistrationOrder.DoesNotExist:
                order = None

        # Fallback: Asaas passes ?id=pay_xxx on successUrl redirect — recover order from it
        if order is None:
            asaas_payment_id = request.GET.get("id")
            if asaas_payment_id:
                order = (
                    RegistrationOrder.objects
                    .select_related("person")
                    .filter(asaas_payment_id=asaas_payment_id)
                    .first()
                )

        if order is not None:
            person = order.person

            if not person.is_active:
                if order.plan_id is None:
                    request.session["post_materials_payment_complete"] = True
                    request.session["materials_order_id"] = order.pk
                else:
                    request.session["post_plan_payment_complete"] = True
                    request.session["plan_order_id"] = order.pk
                    request.session["pending_registration_person_id"] = person.pk
                    request.session.pop("post_materials_payment_complete", None)
                    request.session.pop("materials_order_id", None)
                messages.success(request, "Pagamento confirmado!")
                return redirect("system:register")

            portal_account = PortalAccount.objects.filter(
                person=person, is_active=True
            ).first()
            if portal_account:
                login_portal_identity(request, portal_account=portal_account)
                messages.success(request, "Pagamento confirmado!")
                return redirect("system:dashboard-redirect")

        messages.success(request, "Pagamento confirmado!")
        return redirect("system:login")

    def _handle_pre_registration_success(self, request):
        pre_registration_id = request.GET.get("pre_registration_id") or request.session.get(
            "pending_pre_registration_id"
        )
        stage = request.GET.get("stage") or ""

        pre_registration = None
        if pre_registration_id and stage in ("plan", "materials"):
            pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()

        # Fallback: Asaas pode perder os query params originais e só enviar ?id=pay_xxx
        if pre_registration is None:
            asaas_payment_id = request.GET.get("id") or ""
            if asaas_payment_id:
                pr = PreRegistration.objects.filter(
                    form_snapshot__plan_payment__asaas_payment_id=asaas_payment_id
                ).first()
                if pr:
                    pre_registration = pr
                    stage = "plan"
                else:
                    pr = PreRegistration.objects.filter(
                        form_snapshot__materials_payment__asaas_payment_id=asaas_payment_id
                    ).first()
                    if pr:
                        pre_registration = pr
                        stage = "materials"

        # Fallback: Stripe redirects with session_id → match via plan_payment snapshot
        if pre_registration is None:
            stripe_session_id = request.GET.get("session_id") or ""
            if stripe_session_id:
                pr = PreRegistration.objects.filter(
                    form_snapshot__plan_payment__stripe_session_id=stripe_session_id
                ).first()
                if pr:
                    pre_registration = pr
                    stage = "plan"

        if pre_registration is None:
            return None

        request.session["pending_pre_registration_id"] = pre_registration.pk
        snapshot = pre_registration.form_snapshot or {}
        if stage == "plan":
            snapshot["plan_paid"] = True
            pre_registration.form_snapshot = snapshot
            pre_registration.status = PreRegistrationStatus.PAYMENT_CONFIRMED
            pre_registration.save(update_fields=["form_snapshot", "status", "updated_at"])
            request.session["post_plan_payment_complete"] = True
            request.session.pop("post_materials_payment_complete", None)
            request.session.pop("post_materials_skipped", None)
        else:
            snapshot["materials_paid"] = True
            pre_registration.form_snapshot = snapshot
            pre_registration.save(update_fields=["form_snapshot", "updated_at"])
            request.session["post_materials_payment_complete"] = True
            request.session.pop("post_materials_skipped", None)
        messages.success(request, "Pagamento confirmado!")
        return redirect("system:register")


class PaymentCancelView(View):
    def get(self, request, *args, **kwargs):
        messages.warning(
            request,
            "Pagamento cancelado. Retorne ao cadastro e tente novamente.",
        )
        return redirect("system:register")

