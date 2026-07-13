from decimal import Decimal

from django.conf import settings


def decimal_setting(name):
    return Decimal(str(getattr(settings, name)))


def payment_currency():
    return str(getattr(settings, "PAYMENT_CURRENCY", "brl")).lower()


def site_name():
    return str(getattr(settings, "SITE_NAME", "LV Jiu Jitsu"))


def site_name_upper():
    return str(getattr(settings, "SITE_NAME_UPPER", site_name().upper()))
