from decimal import Decimal

from django.db import models
from django.utils import timezone
from system.business_rule.models.coupon import Coupon


class CouponError(Exception):
    pass


def validate_coupon(code):

    normalized = (code or "").upper().strip()
    if not normalized:
        raise CouponError("Informe o código do cupom.")

    try:
        coupon = Coupon.objects.get(code=normalized)
    except Coupon.DoesNotExist:
        raise CouponError("Cupom inválido.")

    if not coupon.is_active:
        raise CouponError("Cupom inativo.")

    today = timezone.localdate()
    if coupon.valid_from and coupon.valid_from > today:
        raise CouponError("Cupom ainda não está vigente.")
    if coupon.valid_until and coupon.valid_until < today:
        raise CouponError("Cupom expirado.")

    if coupon.max_uses is not None and coupon.uses_count >= coupon.max_uses:
        raise CouponError("Cupom esgotado.")

    return coupon


def apply_coupon(coupon, total):
    return coupon.apply_to(Decimal(str(total)))


def mark_coupon_used(coupon):

    Coupon.objects.filter(pk=coupon.pk).update(uses_count=models.F("uses_count") + 1)
