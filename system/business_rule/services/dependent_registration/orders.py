from django.utils import timezone
from system.business_rule.constants import CheckoutAction
from system.business_rule.models import (
    Membership,
    MembershipStatus,
    PaymentProvider,
    PaymentStatus,
    RegistrationOrder,
)
from system.business_rule.services.financial_transactions import apply_order_financials
from system.business_rule.services.membership import activate_membership_from_paid_order
from system.business_rule.services.order_stock import apply_order_variant_stock
from system.business_rule.services.registration_checkout import (
    create_product_only_order,
    resolve_selected_product_items,
)
from system.business_rule.services.family_pricing import recompute_family_discounts_for_person
from system.business_rule.models.plan import PlanPrice
from system.business_rule.services.dependent_registration.snapshot import material_payload_from_snapshot, materials_order_marker


def create_paid_plan_order(
    dependent, plan, *, checkout_action="",
    stripe_subscription_id="", stripe_subscription_item_id="", stripe_customer_id="",
):

    is_plan_price = isinstance(plan, PlanPrice)
    order = RegistrationOrder.objects.create(
        person=dependent,
        plan=None if is_plan_price else plan,
        plan_price_ref=plan if is_plan_price else None,
        plan_price=plan.price,
        total=plan.price,
        payment_status=PaymentStatus.PAID,
        paid_at=timezone.now(),
        payment_provider=(
            PaymentProvider.STRIPE
            if checkout_action == CheckoutAction.STRIPE_CARD
            else PaymentProvider.ASAAS
        ),
        notes="Pagamento confirmado no pré-cadastro de dependente.",
    )
    apply_order_financials(
        order,
        payment_provider=order.payment_provider,
        mark_available=True,
    )
    activate_membership_from_paid_order(
        order,
        notes="Dependente ativado após pagamento do pré-cadastro.",
        stripe_subscription_id=stripe_subscription_id,
        stripe_subscription_item_id=stripe_subscription_item_id,
        stripe_customer_id=stripe_customer_id,
    )
    recompute_family_discounts_for_person(dependent)
    return order


def create_paid_family_upgrade_order(owner, dependent, plan, *, checkout_action=""):
    order = RegistrationOrder.objects.create(
        person=owner,
        plan=plan,
        plan_price=plan.price,
        total=plan.price,
        payment_status=PaymentStatus.PAID,
        paid_at=timezone.now(),
        payment_provider=(
            PaymentProvider.STRIPE
            if checkout_action == CheckoutAction.STRIPE_CARD
            else PaymentProvider.ASAAS
        ),
        notes=(
            "Upgrade familiar confirmado no pré-cadastro de dependente: "
            f"{dependent.full_name}."
        ),
    )
    apply_order_financials(
        order,
        payment_provider=order.payment_provider,
        mark_available=True,
    )
    membership = activate_membership_from_paid_order(
        order,
        notes="Titular migrado para plano familiar após pagamento do dependente.",
    )
    _retire_previous_owner_memberships(owner, keep_membership=membership)
    return order


def _retire_previous_owner_memberships(owner, *, keep_membership):
    if keep_membership is None:
        return
    now = timezone.now()
    memberships = (
        Membership.objects.filter(
            person=owner,
            status__in=(
                MembershipStatus.PENDING,
                MembershipStatus.ACTIVE,
                MembershipStatus.PAST_DUE,
                MembershipStatus.EXEMPTED,
            ),
        )
        .exclude(pk=keep_membership.pk)
        .order_by("pk")
    )
    for membership in memberships:
        membership.status = MembershipStatus.CANCELED
        membership.canceled_at = membership.canceled_at or now
        membership.notes = (
            (membership.notes or "")
            + f"\nSubstituída pelo plano familiar #{keep_membership.pk}."
        ).strip()
        membership.save(
            update_fields=("status", "canceled_at", "notes", "updated_at")
        )


def create_paid_materials_order_if_needed(dependent, pre_registration):
    snapshot = pre_registration.form_snapshot or {}
    if not snapshot.get("materials_paid"):
        return None
    marker = materials_order_marker(pre_registration.pk)
    existing = RegistrationOrder.objects.filter(
        person=dependent,
        notes__contains=marker,
    ).first()
    if existing is not None:
        return existing

    payload = material_payload_from_snapshot(snapshot)
    if not payload:
        return None
    selections = resolve_selected_product_items(payload)
    order = create_product_only_order(dependent, selections)
    if order is None:
        return None
    order.payment_status = PaymentStatus.PAID
    order.payment_provider = PaymentProvider.ASAAS
    order.paid_at = timezone.now()
    order.notes = "\n".join(
        line for line in (order.notes, marker) if line
    )
    order.save(
        update_fields=(
            "payment_status",
            "payment_provider",
            "paid_at",
            "notes",
            "updated_at",
        )
    )
    apply_order_financials(
        order,
        payment_provider=PaymentProvider.ASAAS,
        mark_available=True,
    )
    apply_order_variant_stock(order)
    return order
