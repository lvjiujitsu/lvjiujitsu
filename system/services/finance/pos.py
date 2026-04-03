import secrets
import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from system.models import AuditLog, CashMovement, CashSession, PdvProduct, PdvSale, PdvSaleItem
from system.services.reports.audit import record_audit_log

logger = logging.getLogger(__name__)


@transaction.atomic
def open_cash_session(*, operator_user, actor_user, opening_balance, notes=""):
    if CashSession.objects.select_for_update().filter(operator_user=operator_user, status=CashSession.STATUS_OPEN).exists():
        raise ValidationError("Ja existe um caixa aberto para este operador.")
    session = CashSession(
        operator_user=operator_user,
        opened_by=actor_user,
        opening_balance=opening_balance,
        expected_cash_total=opening_balance,
        notes=notes,
    )
    session.full_clean()
    session.save()
    if opening_balance > Decimal("0.00"):
        _create_cash_movement(
            cash_session=session,
            sale=None,
            created_by=actor_user,
            movement_type=CashMovement.TYPE_OPENING,
            direction=CashMovement.DIRECTION_IN,
            payment_method=PdvSale.PAYMENT_CASH,
            amount=opening_balance,
            description="Abertura do caixa.",
        )
    record_audit_log(
        category=AuditLog.CATEGORY_PDV,
        action="cash_session_opened",
        actor_user=actor_user,
        target=session,
        metadata={"opening_balance": str(opening_balance)},
    )
    return session


@transaction.atomic
def create_pdv_sale(
    *,
    operator_user,
    payment_method,
    items,
    customer_student=None,
    amount_received=None,
    notes="",
):
    session = _get_open_cash_session_for_update(operator_user)
    if not items:
        raise ValidationError("Adicione ao menos um item para concluir a venda.")
    subtotal_amount = _calculate_subtotal(items)
    total_amount = subtotal_amount
    resolved_received = _resolve_amount_received(payment_method, total_amount, amount_received)
    change_amount = _calculate_change_amount(payment_method, total_amount, resolved_received)
    sale = PdvSale(
        cash_session=session,
        operator_user=operator_user,
        customer_student=customer_student,
        customer_name_snapshot=customer_student.user.full_name if customer_student else "",
        receipt_code=_build_receipt_code(),
        payment_method=payment_method,
        subtotal_amount=subtotal_amount,
        discount_amount=Decimal("0.00"),
        total_amount=total_amount,
        amount_received=resolved_received,
        change_amount=change_amount,
        notes=notes,
    )
    sale.full_clean()
    sale.save()
    for item in items:
        _create_sale_item(sale=sale, product=item["product"], quantity=item["quantity"])
    _create_cash_movement(
        cash_session=session,
        sale=sale,
        created_by=operator_user,
        movement_type=CashMovement.TYPE_SALE_IN,
        direction=CashMovement.DIRECTION_IN,
        payment_method=payment_method,
        amount=total_amount,
        description="Entrada de venda PDV.",
    )
    if change_amount > Decimal("0.00"):
        _create_cash_movement(
            cash_session=session,
            sale=sale,
            created_by=operator_user,
            movement_type=CashMovement.TYPE_CHANGE_OUT,
            direction=CashMovement.DIRECTION_OUT,
            payment_method=PdvSale.PAYMENT_CASH,
            amount=change_amount,
            description="Troco de venda PDV.",
        )
    session.expected_cash_total = calculate_expected_cash_total(session)
    session.save(update_fields=["expected_cash_total", "updated_at"])
    record_audit_log(
        category=AuditLog.CATEGORY_PDV,
        action="pdv_sale_completed",
        actor_user=operator_user,
        target=sale,
        metadata={"payment_method": payment_method, "total_amount": str(total_amount)},
    )
    return sale


@transaction.atomic
def close_cash_session(*, cash_session, closed_by, counted_cash_total, notes=""):
    session = CashSession.objects.select_for_update().get(id=cash_session.id)
    if session.status != CashSession.STATUS_OPEN:
        raise ValidationError("Este caixa ja foi encerrado.")
    expected_cash_total = calculate_expected_cash_total(session)
    difference_amount = counted_cash_total - expected_cash_total
    requires_manager_review = _requires_manager_review(difference_amount)
    session.expected_cash_total = expected_cash_total
    session.counted_cash_total = counted_cash_total
    session.difference_amount = difference_amount
    session.requires_manager_review = requires_manager_review
    session.manager_alert_reason = _build_manager_alert_reason(difference_amount, requires_manager_review)
    session.status = CashSession.STATUS_CLOSED
    session.closed_by = closed_by
    session.closed_at = timezone.now()
    session.notes = _merge_notes(session.notes, notes)
    session.full_clean()
    session.save(
        update_fields=[
            "expected_cash_total",
            "counted_cash_total",
            "difference_amount",
            "requires_manager_review",
            "manager_alert_reason",
            "status",
            "closed_by",
            "closed_at",
            "notes",
            "updated_at",
        ]
    )
    record_audit_log(
        category=AuditLog.CATEGORY_PDV,
        action="cash_session_closed",
        actor_user=closed_by,
        target=session,
        metadata={
            "counted_cash_total": str(counted_cash_total),
            "difference_amount": str(difference_amount),
            "requires_manager_review": requires_manager_review,
        },
    )
    if requires_manager_review:
        logger.warning(
            "cash_session_requires_manager_review",
            extra={"cash_session_uuid": str(session.uuid), "difference_amount": str(difference_amount)},
        )
    return session


def calculate_expected_cash_total(cash_session):
    totals = cash_session.movements.filter(payment_method=PdvSale.PAYMENT_CASH).values("direction").annotate(
        total=Sum("amount")
    )
    total_in = Decimal("0.00")
    total_out = Decimal("0.00")
    for row in totals:
        if row["direction"] == CashMovement.DIRECTION_IN:
            total_in += row["total"] or Decimal("0.00")
        else:
            total_out += row["total"] or Decimal("0.00")
    return total_in - total_out


def _get_open_cash_session_for_update(operator_user):
    session = CashSession.objects.select_for_update().filter(
        operator_user=operator_user,
        status=CashSession.STATUS_OPEN,
    ).first()
    if session is None:
        raise ValidationError("Abra um caixa antes de registrar vendas no PDV.")
    return session


def _calculate_subtotal(items):
    subtotal = Decimal("0.00")
    for item in items:
        product = item["product"]
        quantity = item["quantity"]
        subtotal += product.unit_price * quantity
    return subtotal


def _resolve_amount_received(payment_method, total_amount, amount_received):
    if payment_method == PdvSale.PAYMENT_CASH:
        if amount_received is None:
            raise ValidationError("Informe o valor recebido para vendas em dinheiro.")
        if amount_received < total_amount:
            raise ValidationError("O valor recebido precisa cobrir o total da venda.")
        return amount_received
    return amount_received or total_amount


def _calculate_change_amount(payment_method, total_amount, amount_received):
    if payment_method != PdvSale.PAYMENT_CASH:
        return Decimal("0.00")
    return amount_received - total_amount


def _create_sale_item(*, sale, product, quantity):
    item = PdvSaleItem(
        sale=sale,
        product=product,
        product_name_snapshot=product.name,
        unit_price=product.unit_price,
        quantity=quantity,
        line_total=product.unit_price * quantity,
    )
    item.full_clean()
    item.save()
    return item


def _create_cash_movement(
    *,
    cash_session,
    sale,
    created_by,
    movement_type,
    direction,
    payment_method,
    amount,
    description,
):
    movement = CashMovement(
        cash_session=cash_session,
        sale=sale,
        created_by=created_by,
        movement_type=movement_type,
        direction=direction,
        payment_method=payment_method,
        amount=amount,
        description=description,
    )
    movement.full_clean()
    movement.save()
    return movement


def _build_receipt_code():
    return f"PDV-{timezone.localdate():%Y%m%d}-{secrets.token_hex(3).upper()}"


def _merge_notes(current_notes, incoming_notes):
    if not incoming_notes:
        return current_notes
    if not current_notes:
        return incoming_notes
    return f"{current_notes}\n{incoming_notes}"


def _requires_manager_review(difference_amount):
    threshold = Decimal(str(settings.CASH_CLOSURE_ALERT_THRESHOLD))
    return abs(difference_amount) >= threshold


def _build_manager_alert_reason(difference_amount, requires_manager_review):
    if not requires_manager_review:
        return ""
    if difference_amount > Decimal("0.00"):
        return "Sobra de caixa acima do limite gerencial."
    if difference_amount < Decimal("0.00"):
        return "Quebra de caixa acima do limite gerencial."
    return "Divergencia de caixa acima do limite gerencial."
