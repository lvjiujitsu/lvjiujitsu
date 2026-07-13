import json
import re
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from system.constants import CheckoutAction, DependentCardStrategy
from system.models.plan import PlanPaymentMethod, PlanPrice, SubscriptionPlan
from system.utils.plan_commercial import COMMERCIAL_TIER_LABELS, resolve_commercial_tier
from system.models.product import Product, ProductVariant
from system.models.registration_order import RegistrationOrder, RegistrationOrderItem, PaymentProvider
from system.services import asaas_client
from system.services.coupon import CouponError, apply_coupon, mark_coupon_used, validate_coupon
from system.services.financial_transactions import (
    apply_order_financials,
    calculate_gross_for_net,
    resolve_payment_provider_for_plan,
)
from system.services.pricing import catalog_unit_charges_for_display


ORDER_STOCK_APPLIED_MARKER = "[stock_applied]"
ORDER_ITEM_COLOR_PREFIX = "Cor: "
ORDER_ITEM_SIZE_PREFIX = "Tamanho: "

SIZE_SORT_ORDER = {
    "A0": 10,
    "A1": 11,
    "A2": 12,
    "A3": 13,
    "A4": 14,
    "A5": 15,
    "A6": 16,
    "F1": 21,
    "F2": 22,
    "F3": 23,
    "F4": 24,
    "M0": 31,
    "M1": 32,
    "M2": 33,
    "M3": 34,
    "M4": 35,
}

COLOR_SORT_ORDER = {
    "Branca": 10,
    "Branco": 10,
    "Cinza": 20,
    "Amarelo": 30,
    "Amarela": 30,
    "Laranja": 40,
    "Verde": 50,
    "Azul": 60,
    "Roxa": 70,
    "Marrom": 80,
    "Preto": 90,
}


_CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}


def _build_installment_label(plan):
    if plan.payment_method != "credit_card":
        return ""
    n = _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan.monthly_reference_price:
        price_str = f"R$ {plan.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def _plan_charge_group_key(plan):
    tier = resolve_commercial_tier(
        is_family_plan=plan.is_family_plan, is_loyalty_plan=plan.is_loyalty_plan
    )
    return (plan.audience, tier, plan.weekly_frequency, plan.is_family_plan, plan.billing_cycle)


CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN = "sp"
CATALOG_ID_PREFIX_PLAN_PRICE = "pp"


def build_catalog_plan_id(prefix, pk):
    return f"{prefix}:{pk}"


def resolve_catalog_plan(catalog_id):
    """Resolve um id de catálogo ('sp:<pk>' ou 'pp:<pk>') para o objeto real.

    Retorna uma tupla (plan, plan_price) — exatamente um dos dois é não-nulo,
    ou (None, None) se o id for inválido/não encontrado.
    """
    if not catalog_id:
        return None, None
    prefix, _, raw_pk = str(catalog_id).partition(":")
    if not raw_pk:
        return None, None
    try:
        pk = int(raw_pk)
    except (TypeError, ValueError):
        return None, None
    if prefix == CATALOG_ID_PREFIX_PLAN_PRICE:
        plan_price = PlanPrice.objects.filter(pk=pk, is_active=True).select_related("tier").first()
        return None, plan_price
    if prefix == CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN:
        plan = SubscriptionPlan.objects.filter(pk=pk, is_active=True).first()
        return plan, None
    return None, None


def _build_installment_label_for_price(plan_price):
    if plan_price.payment_method != "credit_card":
        return ""
    n = _CYCLE_INSTALLMENTS.get(plan_price.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan_price.monthly_reference_price:
        price_str = f"R$ {plan_price.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def get_plan_catalog_payload(*, include_plan_prices=False):
    """Catálogo de planos para o wizard público (padrão) ou para o wizard de
    dependente (include_plan_prices=True), que também passa a receber os
    planos do novo modelo PlanTier/PlanPrice (PRD-127) com ids prefixados
    ('sp:<pk>' para SubscriptionPlan legado, 'pp:<pk>' para PlanPrice) para não
    colidir com o catálogo legado, que mantém ids numéricos crus por
    compatibilidade com o wizard público (`selected_plan` é IntegerField lá).
    """
    payload = []
    payload.extend(_build_legacy_plan_catalog_payload(prefixed=include_plan_prices))
    if include_plan_prices:
        payload.extend(_build_plan_price_catalog_payload())
    return payload


def get_public_registration_plan_catalog_payload():
    """Catálogo de planos para cadastro novo (wizard público e dependente).

    Só `PlanTier`/`PlanPrice` (PRD-127/144 C-01) — o catálogo legado
    (`SubscriptionPlan`) hoje só contém o plano Veterano (fidelidade), que
    exige tempo de matrícula e nunca é elegível para quem está se
    cadastrando agora (`is_plan_eligible` já rejeitaria no `clean()` do
    form). Expor esses ids ao cliente é ruído sem propósito de negócio.
    """
    return _build_plan_price_catalog_payload()


def _build_legacy_plan_catalog_payload(*, prefixed=False):
    plans = list(
        SubscriptionPlan.objects.filter(is_active=True)
        .exclude(requires_special_authorization=True)
        .order_by("display_order", "price")
    )
    groups = {}
    for plan in plans:
        slot = groups.setdefault(_plan_charge_group_key(plan), {})
        slot[plan.payment_method] = plan
    cent = Decimal("0.01")
    payload = []
    for plan in plans:
        slot = groups[_plan_charge_group_key(plan)]
        pix_plan = slot.get(PlanPaymentMethod.PIX)
        card_plan = slot.get(PlanPaymentMethod.CREDIT_CARD)
        charge_pix = str(pix_plan.price.quantize(cent)) if pix_plan else "0.00"
        charge_card = str(card_plan.price.quantize(cent)) if card_plan else "0.00"
        tier = resolve_commercial_tier(
            is_family_plan=plan.is_family_plan, is_loyalty_plan=plan.is_loyalty_plan
        )
        payload.append(
            {
                "id": (
                    build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan.pk)
                    if prefixed
                    else plan.pk
                ),
                "code": plan.code,
                "name": plan.display_name,
                "commercial_tier": tier,
                "commercial_tier_label": COMMERCIAL_TIER_LABELS.get(tier, tier),
                "price": str(plan.price),
                "charge_pix": charge_pix,
                "charge_card": charge_card,
                "monthly_reference_price": (
                    str(plan.monthly_reference_price)
                    if plan.monthly_reference_price is not None
                    else ""
                ),
                "cycle": plan.get_billing_cycle_display(),
                "billing_cycle": plan.billing_cycle,
                "payment_method": plan.payment_method,
                "payment_method_label": plan.get_payment_method_display(),
                "is_family_plan": plan.is_family_plan,
                "is_loyalty_plan": plan.is_loyalty_plan,
                "audience": plan.audience,
                "audience_label": plan.get_audience_display(),
                "weekly_frequency": plan.weekly_frequency,
                "weekly_frequency_label": plan.get_weekly_frequency_display(),
                "teacher_commission_percentage": str(plan.teacher_commission_percentage),
                "requires_special_authorization": plan.requires_special_authorization,
                "installment_label": _build_installment_label(plan),
                "installment_count": (
                    _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
                    if plan.payment_method == "credit_card"
                    else 0
                ),
                "gateway_code": plan.gateway_code or "",
                "family_discount_percentage": "0",
            }
        )
    return payload


def _build_plan_price_catalog_payload():
    prices = list(
        PlanPrice.objects.filter(is_active=True, tier__is_active=True)
        .select_related("tier")
        .order_by("tier__display_order", "price")
    )
    cent = Decimal("0.01")
    payload = []
    for price in prices:
        # Cada PlanPrice já representa um gateway/forma de pagamento específico
        # (ex.: asaas_card e stripe_card podem coexistir no mesmo tier/ciclo com
        # preços diferentes) — charge_pix/charge_card devem refletir só o preço
        # desta própria linha, nunca o de uma linha "irmã" de outro gateway.
        own_price = str(price.price.quantize(cent))
        charge_pix = own_price if price.payment_method == PlanPaymentMethod.PIX else "0.00"
        charge_card = own_price if price.payment_method == PlanPaymentMethod.CREDIT_CARD else "0.00"
        payload.append(
            {
                "id": build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, price.pk),
                "code": f"{price.tier.code}-{price.gateway_code}-{price.billing_cycle}",
                "name": price.tier.display_name,
                "commercial_tier": "individual",
                "commercial_tier_label": COMMERCIAL_TIER_LABELS.get("individual", "Individual"),
                "price": str(price.price),
                "charge_pix": charge_pix,
                "charge_card": charge_card,
                "monthly_reference_price": (
                    str(price.monthly_reference_price)
                    if price.monthly_reference_price is not None
                    else ""
                ),
                "cycle": price.get_billing_cycle_display(),
                "billing_cycle": price.billing_cycle,
                "payment_method": price.payment_method,
                "payment_method_label": price.get_payment_method_display(),
                "is_family_plan": False,
                "is_loyalty_plan": False,
                "audience": price.tier.audience,
                "audience_label": price.tier.get_audience_display(),
                "weekly_frequency": price.tier.weekly_frequency,
                "weekly_frequency_label": price.tier.get_weekly_frequency_display(),
                "teacher_commission_percentage": str(price.teacher_commission_percentage),
                "requires_special_authorization": False,
                "installment_label": _build_installment_label_for_price(price),
                "installment_count": (
                    _CYCLE_INSTALLMENTS.get(price.billing_cycle, 1)
                    if price.payment_method == "credit_card"
                    else 0
                ),
                "gateway_code": price.gateway_code or "",
                "family_discount_percentage": str(price.tier.family_discount_percentage),
            }
        )
    return payload


def get_product_catalog_payload():
    products = (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        .select_related("category")
        .prefetch_related("variants")
    )
    payload = []
    for product in products:
        variants = [
            _build_product_variant_payload(product, variant)
            for variant in _get_active_variants(product)
        ]
        charges = catalog_unit_charges_for_display(product.unit_price)
        payload.append(
            {
                "id": product.pk,
                "sku": product.sku,
                "name": product.display_name,
                "price": str(product.unit_price),
                "charge_pix": charges["charge_pix"],
                "charge_card": charges["charge_card"],
                "category": str(product.category),
                "category_code": product.category.code,
                "category_order": product.category.display_order,
                "description": product.description or "",
                "variant_count": len(variants),
                "total_stock": sum(variant["stock_quantity"] for variant in variants),
                "variants": variants,
            }
        )
    return payload


def _build_product_variant_payload(product, variant):
    return {
        "id": variant.pk,
        "product_id": product.pk,
        "product_name": product.display_name,
        "label": _build_variant_option_label(variant),
        "snapshot_name": build_order_item_product_name(product, variant),
        "color": variant.color,
        "size": variant.size,
        "stock_quantity": variant.stock_quantity,
        "is_in_stock": variant.stock_quantity > 0,
    }


def _build_variant_option_label(variant):
    parts = []
    if variant.color:
        parts.append(variant.color)
    if variant.size:
        parts.append(variant.size)
    if not parts:
        parts.append("Padrão")
    if variant.stock_quantity > 0:
        parts.append(f"{variant.stock_quantity} un.")
    else:
        parts.append("Esgotado")
    return " · ".join(parts)


def _get_active_variants(product):
    variants = [variant for variant in product.variants.all() if variant.is_active]
    return sorted(
        variants,
        key=lambda variant: (
            COLOR_SORT_ORDER.get(variant.color, 999),
            variant.color or "",
            SIZE_SORT_ORDER.get(variant.size, 999),
            variant.size or "",
            variant.pk,
        ),
    )


def parse_selected_products(raw_payload):
    if not raw_payload:
        return []
    try:
        items = json.loads(raw_payload)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            variant_id = int(item.get("variant_id") or item.get("id") or 0)
            quantity = int(item.get("qty") or item.get("quantity") or 0)
        except (ValueError, TypeError):
            continue
        if variant_id > 0 and 0 < quantity <= 99:
            result.append({"variant_id": variant_id, "quantity": quantity})
    return result


def resolve_selected_product_items(raw_items):
    if not raw_items:
        return []

    quantities_by_variant = {}
    ordered_variant_ids = []
    for item in raw_items:
        variant_id = int(item.get("variant_id") or 0)
        quantity = int(item.get("quantity") or 0)
        if variant_id <= 0 or quantity <= 0:
            continue
        if variant_id not in quantities_by_variant:
            ordered_variant_ids.append(variant_id)
            quantities_by_variant[variant_id] = 0
        quantities_by_variant[variant_id] += quantity

    if not ordered_variant_ids:
        return []

    variants_by_id = {
        variant.pk: variant
        for variant in ProductVariant.objects.select_related("product", "product__category")
        .filter(
            pk__in=ordered_variant_ids,
            is_active=True,
            product__is_active=True,
            product__category__is_active=True,
        )
    }

    selections = []
    for variant_id in ordered_variant_ids:
        variant = variants_by_id.get(variant_id)
        if variant is None:
            raise ValueError("Selecione apenas materiais válidos.")
        quantity = quantities_by_variant[variant_id]
        if quantity > variant.stock_quantity:
            raise ValueError(
                f"Estoque insuficiente para {build_order_item_product_name(variant.product, variant)}."
            )
        selections.append(
            {
                "variant_id": variant.pk,
                "variant": variant,
                "product": variant.product,
                "quantity": quantity,
            }
        )
    return selections


def build_order_item_product_name(product, variant):
    details = []
    if variant.color:
        details.append(f"{ORDER_ITEM_COLOR_PREFIX}{variant.color}")
    if variant.size:
        details.append(f"{ORDER_ITEM_SIZE_PREFIX}{variant.size}")
    if not details:
        return product.display_name
    return f"{product.display_name} ({', '.join(details)})"


def normalize_selected_product_items(selected_products):
    if not selected_products:
        return []
    if selected_products and selected_products[0].get("variant") is not None:
        return selected_products
    return resolve_selected_product_items(selected_products)


@transaction.atomic
def create_product_only_order(person, cart_items):
    selections = normalize_selected_product_items(cart_items)
    if not selections:
        return None

    from system.models.registration_order import OrderKind

    order = RegistrationOrder.objects.create(
        person=person,
        plan=None,
        plan_price=Decimal("0"),
        total=Decimal("0"),
        kind=OrderKind.ONE_TIME,
    )

    items_total = Decimal("0")
    for selection in selections:
        subtotal = _create_product_order_item(order, selection)
        items_total += subtotal

    if items_total <= 0:
        order.delete()
        return None

    order.total = items_total
    order.save(update_fields=["total", "updated_at"])
    return order


def _create_product_order_item(order, selection):
    variant = selection["variant"]
    product = selection["product"]
    quantity = selection["quantity"]
    subtotal = product.unit_price * quantity
    RegistrationOrderItem.objects.create(
        order=order,
        product=product,
        product_name=build_order_item_product_name(product, variant),
        quantity=quantity,
        unit_price=product.unit_price,
        subtotal=subtotal,
    )
    return subtotal


def _count_group_members(cleaned_data):
    count = 1
    if cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf"):
        count += 1
    extras = cleaned_data.get("extra_dependents") or []
    if isinstance(extras, list):
        count += len(extras)
    return max(count, 1)


def _count_training_persons(cleaned_data):
    from system.constants import RegistrationProfile
    profile = cleaned_data.get("registration_profile") or RegistrationProfile.HOLDER
    extras = cleaned_data.get("extra_dependents") or []
    extra_count = len(extras) if isinstance(extras, list) else 0
    if profile == RegistrationProfile.GUARDIAN:
        primary = 1 if (cleaned_data.get("student_name") or cleaned_data.get("student_cpf")) else 0
        return max(primary + extra_count, 1)
    # HOLDER: titular + dependente opcional
    deps = 1 if (cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf")) else 0
    return max(1 + deps + extra_count, 1)


def get_registration_plan_multiplier(cleaned_data):
    return _count_training_persons(cleaned_data)


@transaction.atomic
def create_registration_order(person, cleaned_data):
    catalog_id = cleaned_data.get("selected_plan")

    if not catalog_id:
        return None

    legacy_plan, plan_price_ref = resolve_catalog_plan(catalog_id)
    if legacy_plan is None and plan_price_ref is None:
        return None

    if legacy_plan is not None:
        resolved_plan = legacy_plan
        if getattr(legacy_plan, "is_family_plan", False):
            multiplier = _count_group_members(cleaned_data)
        else:
            multiplier = _count_training_persons(cleaned_data)
        unit_price = legacy_plan.price
    else:
        resolved_plan = plan_price_ref
        multiplier = _count_training_persons(cleaned_data)
        unit_price = plan_price_ref.price

    total = unit_price * Decimal(multiplier)
    payment_provider = resolve_payment_provider_for_plan(resolved_plan)

    order = RegistrationOrder.objects.create(
        person=person,
        plan=legacy_plan,
        plan_price_ref=plan_price_ref,
        plan_price=total,
        total=total,
    )
    apply_order_financials(order, payment_provider=payment_provider)
    return order


def _apply_fee_pass_through(base_amount, payment_provider):
    if payment_provider == PaymentProvider.ASAAS and getattr(settings, "PIX_FEE_PASS_THROUGH", True):
        return calculate_gross_for_net(base_amount, payment_provider)
    return base_amount


def gross_up_order_for_checkout(order, checkout_action):
    """Aplica gross-up de taxa ao total do pedido de acordo com o método de pagamento escolhido."""
    payment_method = None
    if checkout_action == CheckoutAction.ASAAS_CARD:
        if not getattr(settings, "CREDIT_CARD_FEE_PASS_THROUGH", True):
            return order
        provider = PaymentProvider.ASAAS
        payment_method = PlanPaymentMethod.CREDIT_CARD
    elif checkout_action == CheckoutAction.PIX:
        if not getattr(settings, "PIX_FEE_PASS_THROUGH", True):
            return order
        provider = PaymentProvider.ASAAS
        payment_method = PlanPaymentMethod.PIX
    else:
        return order
    gross = calculate_gross_for_net(
        order.total or Decimal("0"),
        provider,
        payment_method=payment_method,
    )
    if gross != order.total:
        order.total = gross
        order.save(update_fields=["total", "updated_at"])
    return order


@transaction.atomic
def apply_order_variant_stock(order):
    if order is None or _has_order_stock_applied(order):
        return order

    order_items = list(order.items.select_related("product"))
    if not order_items:
        return order

    deductions = []
    for item in order_items:
        variant = resolve_order_item_variant(item, lock=True)
        if variant is None:
            raise ValueError(f"Variante do pedido não encontrada para '{item.product_name}'.")
        if item.quantity > variant.stock_quantity:
            raise ValueError(
                f"Estoque insuficiente para {build_order_item_product_name(item.product, variant)}."
            )
        deductions.append((variant, item.quantity))

    for variant, quantity in deductions:
        variant.stock_quantity -= quantity
        variant.save(update_fields=["stock_quantity", "updated_at"])

    _mark_order_stock_applied(order)
    return order


def resolve_order_item_variant(order_item, *, lock=False):
    product = order_item.product
    if product is None:
        return None

    snapshot = _parse_order_item_variant_snapshot(order_item.product_name)
    queryset = ProductVariant.objects.filter(product=product, is_active=True)
    if lock:
        queryset = queryset.select_for_update()
    if snapshot["color"]:
        queryset = queryset.filter(color=snapshot["color"])
    if snapshot["size"]:
        queryset = queryset.filter(size=snapshot["size"])

    variants = list(queryset[:2])
    if len(variants) == 1:
        return variants[0]
    if not snapshot["color"] and not snapshot["size"] and len(variants) == 1:
        return variants[0]
    return None


def _parse_order_item_variant_snapshot(product_name):
    match = re.search(r"\((?P<details>[^()]*)\)$", product_name or "")
    if not match:
        return {"color": "", "size": ""}

    color = ""
    size = ""
    for raw_part in match.group("details").split(","):
        part = raw_part.strip()
        if part.startswith(ORDER_ITEM_COLOR_PREFIX):
            color = part[len(ORDER_ITEM_COLOR_PREFIX) :]
        elif part.startswith(ORDER_ITEM_SIZE_PREFIX):
            size = part[len(ORDER_ITEM_SIZE_PREFIX) :]
    return {"color": color, "size": size}


def _has_order_stock_applied(order):
    return ORDER_STOCK_APPLIED_MARKER in _get_order_note_lines(order)


def _mark_order_stock_applied(order):
    notes = _get_order_note_lines(order)
    if ORDER_STOCK_APPLIED_MARKER not in notes:
        notes.append(ORDER_STOCK_APPLIED_MARKER)
        order.notes = "\n".join(notes)
        order.save(update_fields=["notes", "updated_at"])


def _get_order_note_lines(order):
    return [line.strip() for line in (order.notes or "").splitlines() if line.strip()]


def ensure_pre_registration_asaas_customer(pre_registration):
    """Garante um customer Asaas para o pré-cadastro, criando-o se necessário."""
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


def _normalize_catalog_plan_id(value):
    if not value:
        return ""
    text = str(value)
    if ":" in text:
        return text
    # Compat: pré-cadastros antigos guardavam apenas o pk (int) do SubscriptionPlan.
    try:
        return build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, int(text))
    except (TypeError, ValueError):
        return ""


def parse_selected_plan_payload(snapshot):
    raw = snapshot.get("selected_plans_payload") or ""
    result = []
    if raw:
        if isinstance(raw, list):
            payload = raw
        else:
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                payload = []
        if isinstance(payload, list):
            for item in payload:
                plan_id = _normalize_catalog_plan_id(item.get("plan_id"))
                if plan_id:
                    result.append({"plan_id": plan_id, "label": item.get("label", "")})
    if result:
        return result
    plan_id = _normalize_catalog_plan_id(snapshot.get("selected_plan"))
    return [{"plan_id": plan_id, "label": ""}] if plan_id else []


CARD_STAGGER_OFFSET_HOURS = 4


def compute_staggered_billing_cycle_anchor(owner_membership, plan):
    from system.services.membership import add_billing_cycle

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
    """
    Cria o pagamento da mensalidade do pré-cadastro (Asaas PIX/cartão ou Stripe assinatura)
    e retorna a invoice_url/checkout_url para redirecionamento.

    Levanta ValueError para erros de validação (planos inválidos, cupom inválido, etc.)
    e asaas_client.AsaasClientError para falhas do gateway Asaas.
    """
    from system.services.pre_registration import snapshot_scalar
    from system.services.stripe_checkout import (
        StripeCheckoutError,
        create_subscription_session_for_pre_registration,
        merge_plan_into_existing_subscription,
    )

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

    # Aplicar cupom de desconto — válido para todos os gateways
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
        from system.services.membership import get_active_membership

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
            from system.services.membership import get_active_membership

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
    description = "Mensalidade LV Jiu Jitsu — pré-cadastro #{0}".format(pre_registration.pk)
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
    """
    Cria o pagamento Asaas (PIX/cartão) dos materiais selecionados no pré-cadastro
    e retorna a invoice_url para redirecionamento.

    Levanta asaas_client.AsaasClientError para pedido sem valor ou falha do gateway.
    """
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
    description = "Materiais LV Jiu Jitsu — pré-cadastro #{0}".format(pre_registration.pk)

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
