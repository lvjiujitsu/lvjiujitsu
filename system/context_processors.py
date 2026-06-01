from django.conf import settings
from django.core.cache import cache

from system.selectors.product_backorders import count_ready_backorders_for_person

_BACKORDER_CACHE_TTL = 120  # segundos — aceitável perder 2 min de precisão


def portal_navigation(request):
    person = getattr(request, "portal_person", None)

    pending_count = 0
    if person is not None:
        cache_key = f"backorder_count_{person.pk}"
        pending_count = cache.get(cache_key)
        if pending_count is None:
            pending_count = count_ready_backorders_for_person(person)
            cache.set(cache_key, pending_count, timeout=_BACKORDER_CACHE_TTL)

    return {
        "pending_backorder_count": pending_count,
        "site_base_url": settings.SITE_BASE_URL.rstrip("/"),
    }
