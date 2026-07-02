COMMERCIAL_TIER_INDIVIDUAL = "individual"
COMMERCIAL_TIER_FIDELITY = "fidelity"
COMMERCIAL_TIER_FAMILY = "family"

COMMERCIAL_TIER_LABELS = {
    COMMERCIAL_TIER_INDIVIDUAL: "Individual",
    COMMERCIAL_TIER_FIDELITY: "Veterano",
    COMMERCIAL_TIER_FAMILY: "Família",
}

COMMERCIAL_TIER_ORDER = {
    COMMERCIAL_TIER_INDIVIDUAL: 0,
    COMMERCIAL_TIER_FIDELITY: 5,
    COMMERCIAL_TIER_FAMILY: 10,
}


def resolve_commercial_tier(*, is_family_plan: bool, is_loyalty_plan: bool) -> str:
    if is_family_plan:
        return COMMERCIAL_TIER_FAMILY
    if is_loyalty_plan:
        return COMMERCIAL_TIER_FIDELITY
    return COMMERCIAL_TIER_INDIVIDUAL
