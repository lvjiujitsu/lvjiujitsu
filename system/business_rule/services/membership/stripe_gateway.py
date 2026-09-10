from system.business_rule.services.membership.cycles import from_unix


def stripe_get(obj, key, default=None):
    if obj is None:
        return default
    try:
        if key in obj:
            value = obj[key]
            return value if value is not None else default
    except (TypeError, KeyError):
        return default
    return default


def extract_stripe_subscription_period(stripe_subscription):
    if stripe_subscription is None:
        return None, None
    start = stripe_get(stripe_subscription, "current_period_start")
    end = stripe_get(stripe_subscription, "current_period_end")
    if start is None or end is None:
        items = stripe_get(stripe_subscription, "items")
        data = stripe_get(items, "data") if items is not None else None
        if data:
            first_item = data[0]
            if start is None:
                start = stripe_get(first_item, "current_period_start")
            if end is None:
                end = stripe_get(first_item, "current_period_end")
    return from_unix(start), from_unix(end)
