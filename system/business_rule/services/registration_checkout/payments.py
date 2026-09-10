from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from system.business_rule.constants import CheckoutAction, DependentCardStrategy
from system.business_rule.services import asaas_client
from system.business_rule.services.coupon import CouponError, apply_coupon, mark_coupon_used, validate_coupon
from system.business_rule.services.form_snapshot import snapshot_scalar
from system.business_rule.services.membership import add_billing_cycle, get_active_membership
from system.business_rule.services.order_stock import build_order_item_product_name
from system.business_rule.services.stripe_checkout import StripeCheckoutError, create_subscription_session_for_pre_registration, merge_plan_into_existing_subscription
from system.business_rule.services.registration_checkout.catalog_ids import parse_selected_plan_payload, resolve_catalog_plan


def ensure_pre_registration_asaas_customer(pre_registration):
    snapshot = pre_registration.form_snapshot or {}
    payment_meta = snapshot.get("asaas_customer") or {}
    if payment_meta.get("id"):
        return payment_meta["id"]
    profile = snapshot.get("registration_profile") or pre_registration.registration_profile
    prefix = "guardian" if profile == "guardian" else "holder"
    customer = asaas_client.create_customer(
        name=snapshot.get(f"{prefix}_name") or pre_registration.holder_cpf,
        cpf_cnpj=snapshot.get(f"{prefix}_cpf") or pre_registration.holder_cpf,
        email=snapshot.get(f"{prefix}_email") or None,
        phone=snapshot.get(f"{prefix}_phone") or None,
        external_reference=f"pre-registration:{pre_registration.pk}",
        postal_code=snapshot.get(f"{prefix}_postal_code") or None,
        address=snapshot.get(f"{prefix}_address") or None,
        address_number=snapshot.get(f"{prefix}_address_number") or None,
        address_complement=snapshot.get(f"{prefix}_address_complement") or None,
        address_neighborhood=snapshot.get(f"{prefix}_address_neighborhood") or None,
        city=snapshot.get(f"{prefix}_city") or None,
    )
    customer_id = customer.get("id") if isinstance(customer, dict) else ""
    if not customer_id:
        raise asaas_client.AsaasClientError("Resposta Asaas sem id de cliente.")
    snapshot["asaas_customer"] = {"id": customer_id}
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return customer_id


CARD_STAGGER_OFFSET_HOURS = 4


def compute_staggered_billing_cycle_anchor(owner_membership, plan):
    now = timezone.now()
    reference = None
    if owner_membership is not None and owner_membership.current_period_end:
        if owner_membership.current_period_end > now:
            reference = owner_membership.current_period_end
    if reference is None:
        reference = add_billing_cycle(now, plan.billing_cycle)
    anchor = reference + timedelta(hours=CARD_STAGGER_OFFSET_HOURS)
    return int(anchor.timestamp())


def create_pre_registration_plan_payment(pre_registration, checkout_action, *, card_strategy=None, owner=None):
    snapshot = pre_registration.form_snapshot or {}
    selected_plans = parse_selected_plan_payload(snapshot)
    if not selected_plans:
        raise ValueError("Selecione ao menos um plano para pagar.")

    plans_by_id = {}
    for item in selected_plans:
        legacy_plan, plan_price = resolve_catalog_plan(item["plan_id"])
        resolved = legacy_plan if legacy_plan is not None else plan_price
        if resolved is not None:
            plans_by_id[item["plan_id"]] = resolved
    missing = [item["plan_id"] for item in selected_plans if item["plan_id"] not in plans_by_id]
    if missing:
        raise ValueError("Selecione apenas planos válidos.")

    total = sum((plans_by_id[item["plan_id"]].price for item in selected_plans), Decimal("0.00"))
    if total <= 0:
        raise ValueError("Plano sem valor cobrável.")

    coupon_code = snapshot_scalar(snapshot, "coupon_code")
    coupon = None
    discount_amount = Decimal("0.00")
    if coupon_code:
        try:
            coupon = validate_coupon(coupon_code)
            total, discount_amount = apply_coupon(coupon, total)
        except CouponError as exc:
            raise ValueError(str(exc))

    if checkout_action == CheckoutAction.STRIPE_CARD and card_strategy == DependentCardStrategy.SAME_CARD_MERGED:
        if owner is None or len(selected_plans) != 1:
            raise ValueError("Fusão de cobrança exige um responsável com assinatura ativa e um único plano.")
        owner_membership = get_active_membership(owner)
        plan = plans_by_id[selected_plans[0]["plan_id"]]
        try:
            merge_result = merge_plan_into_existing_subscription(owner_membership, plan)
        except StripeCheckoutError as exc:
            raise ValueError(str(exc))
        if coupon:
            mark_coupon_used(coupon)
        snapshot["plan_payment"] = {
            "total": str(total),
            "merged_into_owner_subscription": True,
            "stripe_subscription_id": merge_result["stripe_subscription_id"],
            "stripe_subscription_item_id": merge_result["stripe_subscription_item_id"],
            "items": [
                {
                    "label": selected_plans[0].get("label", ""),
                    "plan_id": plan.pk,
                    "plan_name": plan.display_name,
                    "price": str(plan.price),
                }
            ],
        }
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])
        return (
            reverse("system:payment-success")
            + f"?pre_registration_id={pre_registration.pk}&stage=plan"
        )

    if checkout_action == CheckoutAction.STRIPE_CARD:
        coupon_info = (
            {"coupon_code": coupon.code, "discount_amount": str(discount_amount)}
            if coupon else None
        )
        billing_cycle_anchor = None
        if card_strategy == DependentCardStrategy.SAME_CARD_STAGGERED and owner is not None:
            owner_membership = get_active_membership(owner)
            plan = plans_by_id[selected_plans[0]["plan_id"]] if len(selected_plans) == 1 else None
            if plan is not None:
                billing_cycle_anchor = compute_staggered_billing_cycle_anchor(
                    owner_membership, plan
                )
        try:
            session = create_subscription_session_for_pre_registration(
                pre_registration, plans_by_id, selected_plans,
                final_total=total, coupon_info=coupon_info,
                billing_cycle_anchor=billing_cycle_anchor,
            )
        except StripeCheckoutError as exc:
            raise ValueError(str(exc))
        if coupon:
            mark_coupon_used(coupon)
        return session["url"]

    customer_id = ensure_pre_registration_asaas_customer(pre_registration)
    success_url = (
        settings.SITE_BASE_URL.rstrip("/")
        + reverse("system:payment-success")
        + f"?pre_registration_id={pre_registration.pk}&stage=plan"
    )
    description = "Mensalidade {0} — pré-cadastro #{1}".format(
        settings.SITE_NAME, pre_registration.pk
    )
    due_date = timezone.localdate() + timedelta(days=settings.ASAAS_CARD_DUE_DAYS)

    if checkout_action == CheckoutAction.PIX:
        payment = asaas_client.create_pix_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=f"pre-registration:{pre_registration.pk}:plan",
            success_url=success_url,
        )
    else:
        payment = asaas_client.create_credit_card_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=f"pre-registration:{pre_registration.pk}:plan",
            installment_count=1,
            success_url=success_url,
        )

    invoice_url = payment.get("invoiceUrl") or ""
    payment_id = payment.get("id") or ""
    if not invoice_url or not payment_id:
        raise asaas_client.AsaasClientError("Resposta Asaas sem invoiceUrl ou id.")

    coupon_info = {}
    if coupon:
        coupon_info = {
            "coupon_code": coupon.code,
            "discount_amount": str(discount_amount),
        }
        mark_coupon_used(coupon)

    snapshot["plan_payment"] = {
        "asaas_payment_id": payment_id,
        "total": str(total),
        "items": [
            {
                "label": item.get("label", ""),
                "plan_id": item["plan_id"],
                "plan_name": plans_by_id[item["plan_id"]].display_name,
                "price": str(plans_by_id[item["plan_id"]].price),
            }
            for item in selected_plans
        ],
        **coupon_info,
    }
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return invoice_url


def create_pre_registration_materials_payment(pre_registration, items, checkout_action):
    total = sum(
        (selection["product"].unit_price * selection["quantity"] for selection in items),
        Decimal("0.00"),
    )
    if total <= 0:
        raise asaas_client.AsaasClientError("Pedido de materiais sem valor cobrável.")

    customer_id = ensure_pre_registration_asaas_customer(pre_registration)
    success_url = (
        settings.SITE_BASE_URL.rstrip("/")
        + reverse("system:payment-success")
        + f"?pre_registration_id={pre_registration.pk}&stage=materials"
    )
    due_date = timezone.localdate() + timedelta(days=settings.ASAAS_CARD_DUE_DAYS)
    description = "Materiais {0} — pré-cadastro #{1}".format(
        settings.SITE_NAME, pre_registration.pk
    )

    if checkout_action == CheckoutAction.PIX:
        payment = asaas_client.create_pix_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=f"pre-registration:{pre_registration.pk}:materials",
            success_url=success_url,
        )
    else:
        payment = asaas_client.create_credit_card_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=f"pre-registration:{pre_registration.pk}:materials",
            installment_count=1,
            success_url=success_url,
        )
    invoice_url = payment.get("invoiceUrl") or ""
    payment_id = payment.get("id") or ""
    if not invoice_url or not payment_id:
        raise asaas_client.AsaasClientError("Resposta Asaas sem invoiceUrl ou id.")

    snapshot = pre_registration.form_snapshot or {}
    snapshot["materials_payment"] = {
        "asaas_payment_id": payment_id,
        "total": str(total),
        "items": [
            {
                "name": build_order_item_product_name(selection["product"], selection["variant"]),
                "quantity": selection["quantity"],
                "unit_price": str(selection["product"].unit_price),
                "subtotal": str(selection["product"].unit_price * selection["quantity"]),
            }
            for selection in items
        ],
    }
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return invoice_url
