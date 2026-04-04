from system.services import resolve_portal_account_from_session, resolve_technical_admin_from_session


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

        access_account = resolve_portal_account_from_session(request)
        technical_admin_user = resolve_technical_admin_from_session(request)
        if technical_admin_user is not None:
            request.technical_admin_user = technical_admin_user
            request.portal_is_technical_admin = True
            request.portal_is_administrative = True
            request.portal_is_instructor = True
            request.portal_is_student = True
            request.portal_type_codes = {
                "administrative-assistant",
                "instructor",
                "student",
                "guardian",
            }

        if access_account is not None:
            request.portal_account = access_account
            request.portal_person = access_account.person
            request.portal_type_codes = set(
                access_account.person.person_types.values_list("code", flat=True)
            )
            request.portal_is_administrative = "administrative-assistant" in request.portal_type_codes
            request.portal_is_instructor = "instructor" in request.portal_type_codes
            request.portal_is_student = bool(
                {"student", "guardian"} & request.portal_type_codes
            )

        return self.get_response(request)
