from system.selectors.product_backorders import count_ready_backorders_for_person


def portal_navigation(request):
    person = getattr(request, "portal_person", None)
    return {
        "pending_backorder_count": count_ready_backorders_for_person(person),
    }
