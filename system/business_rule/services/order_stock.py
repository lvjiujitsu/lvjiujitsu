import re

from django.db import transaction

from system.business_rule.models.product import ProductVariant


ORDER_STOCK_APPLIED_MARKER = "[stock_applied]"
ORDER_ITEM_COLOR_PREFIX = "Cor: "
ORDER_ITEM_SIZE_PREFIX = "Tamanho: "


def build_order_item_product_name(product, variant):
    details = []
    if variant.color:
        details.append(f"{ORDER_ITEM_COLOR_PREFIX}{variant.color}")
    if variant.size:
        details.append(f"{ORDER_ITEM_SIZE_PREFIX}{variant.size}")
    if not details:
        return product.display_name
    return f"{product.display_name} ({', '.join(details)})"


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
