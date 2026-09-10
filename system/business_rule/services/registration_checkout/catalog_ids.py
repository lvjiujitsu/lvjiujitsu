import json
from system.business_rule.models.plan import PlanPrice, SubscriptionPlan


CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN = "sp"


CATALOG_ID_PREFIX_PLAN_PRICE = "pp"


def build_catalog_plan_id(prefix, pk):
    return f"{prefix}:{pk}"


def resolve_catalog_plan(catalog_id):
    if not catalog_id:
        return None, None
    prefix, _, raw_pk = str(catalog_id).partition(":")
    if not raw_pk:
        return None, None
    try:
        pk = int(raw_pk)
    except (TypeError, ValueError):
        return None, None
    if prefix == CATALOG_ID_PREFIX_PLAN_PRICE:
        plan_price = PlanPrice.objects.filter(pk=pk, is_active=True).select_related("tier").first()
        return None, plan_price
    if prefix == CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN:
        plan = SubscriptionPlan.objects.filter(pk=pk, is_active=True).first()
        return plan, None
    return None, None


def _normalize_catalog_plan_id(value):
    if not value:
        return ""
    text = str(value)
    if ":" in text:
        return text
    try:
        return build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, int(text))
    except (TypeError, ValueError):
        return ""


def parse_selected_plan_payload(snapshot):
    raw = snapshot.get("selected_plans_payload") or ""
    result = []
    if raw:
        if isinstance(raw, list):
            payload = raw
        else:
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                payload = []
        if isinstance(payload, list):
            for item in payload:
                plan_id = _normalize_catalog_plan_id(item.get("plan_id"))
                if plan_id:
                    result.append({"plan_id": plan_id, "label": item.get("label", "")})
    if result:
        return result
    plan_id = _normalize_catalog_plan_id(snapshot.get("selected_plan"))
    return [{"plan_id": plan_id, "label": ""}] if plan_id else []
