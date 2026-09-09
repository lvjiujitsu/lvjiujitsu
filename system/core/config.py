from decimal import Decimal

from django.conf import settings


def decimal_setting(name):
    return Decimal(str(getattr(settings, name)))
