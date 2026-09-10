from system.business_rule.constants import PEOPLE_SUPPORT_PERSON_TYPE_CODES, Capability
from system.business_rule.access import (
    PortalRoleRequiredMixin,
    is_technical_admin,
    portal_capabilities,
)


class PeopleSupportRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = PEOPLE_SUPPORT_PERSON_TYPE_CODES
    required_capabilities = (Capability.SUPPORT_PEOPLE,)


def can_manage_people(request):
    return bool(
        Capability.MANAGE_PEOPLE
        in portal_capabilities(request)
        or is_technical_admin(request)
    )
