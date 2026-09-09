from django.conf import settings

from system.core.access.contracts import ANONYMOUS

_theme_provider = None


def register_theme_provider(provider):
    global _theme_provider
    _theme_provider = provider


def site_identity(request):
    context = {
        "identity": getattr(request, "identity", ANONYMOUS),
        "site_name": settings.SITE_NAME,
        "site_name_upper": settings.SITE_NAME_UPPER,
    }
    if _theme_provider is not None:
        context.update(_theme_provider(request))
    return context
