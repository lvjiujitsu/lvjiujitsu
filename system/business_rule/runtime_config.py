from django.conf import settings


def payment_currency():
    return str(settings.PAYMENT_CURRENCY).lower()
