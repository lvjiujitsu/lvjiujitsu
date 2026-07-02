from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse


class PortalLoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "portal_account", None) and not getattr(
            request, "portal_is_technical_admin", False
        ):
            return redirect_to_login(
                next=request.get_full_path(),
                login_url=reverse("system:login"),
            )
        return super().dispatch(request, *args, **kwargs)


class PortalRoleRequiredMixin(PortalLoginRequiredMixin):
    allowed_codes: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "portal_account", None) and not getattr(
            request, "portal_is_technical_admin", False
        ):
            return super().dispatch(request, *args, **kwargs)
        if not self.has_allowed_role():
            return redirect(reverse("system:dashboard-redirect"))
        return super().dispatch(request, *args, **kwargs)

    def has_allowed_role(self) -> bool:
        if getattr(self.request, "portal_is_technical_admin", False):
            return True
        if self.required_capabilities:
            capabilities = getattr(self.request, "portal_capabilities", set())
            return bool(set(self.required_capabilities) & set(capabilities))
        person = getattr(self.request, "portal_person", None)
        if person is None or not person.person_type_id:
            return False
        return person.person_type.code in self.allowed_codes
