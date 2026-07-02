from system.constants import (
    INSTRUCTOR_PERSON_TYPE_CODES,
    PortalCapability,
    TECHNICAL_ADMIN_PERSON_TYPE_CODES,
    TECHNICAL_ADMIN_CAPABILITIES,
)
from system.services import (
    get_person_capabilities,
    get_person_operational_role_codes,
    resolve_portal_account_from_session,
    resolve_technical_admin_from_session,
)


class PortalSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.portal_account = None
        request.portal_person = None
        request.technical_admin_user = None
        request.portal_is_technical_admin = False
        request.portal_is_administrative = False
        request.portal_is_instructor = False
        request.portal_is_student = False
        request.portal_type_codes = set()
        request.portal_role_codes = set()
        request.portal_capabilities = set()
        request.portal_supports_classes = False

        access_account = resolve_portal_account_from_session(request)
        technical_admin_user = resolve_technical_admin_from_session(request)
        if technical_admin_user is not None:
            request.technical_admin_user = technical_admin_user
            request.portal_is_technical_admin = True
            request.portal_is_administrative = True
            request.portal_is_instructor = True
            request.portal_is_student = True
            request.portal_type_codes = set(TECHNICAL_ADMIN_PERSON_TYPE_CODES)
            request.portal_role_codes = set()
            request.portal_capabilities = set(TECHNICAL_ADMIN_CAPABILITIES)
            request.portal_supports_classes = True

        if access_account is not None:
            request.portal_account = access_account
            request.portal_person = access_account.person
            person = access_account.person
            person_type_code = (
                person.person_type.code
                if person.person_type_id
                else ""
            )
            request.portal_type_codes = {person_type_code} if person_type_code else set()
            request.portal_role_codes = get_person_operational_role_codes(person)
            request.portal_capabilities = get_person_capabilities(person)
            request.portal_is_administrative = (
                PortalCapability.MANAGE_ACADEMY in request.portal_capabilities
            )
            request.portal_is_instructor = bool(
                set(INSTRUCTOR_PERSON_TYPE_CODES) & request.portal_type_codes
            )
            request.portal_is_student = (
                PortalCapability.ACCESS_STUDENT_AREA in request.portal_capabilities
            )
            request.portal_supports_classes = (
                PortalCapability.SUPPORT_CLASSES in request.portal_capabilities
            )

        return self.get_response(request)
