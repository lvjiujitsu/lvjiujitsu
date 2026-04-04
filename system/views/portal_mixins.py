from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
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

    def dispatch(self, request, *args, **kwargs):
        if not self.has_allowed_role():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def has_allowed_role(self) -> bool:
        if getattr(self.request, "portal_is_technical_admin", False):
            return True
        person = getattr(self.request, "portal_person", None)
        if person is None:
            return False
        return person.person_types.filter(code__in=self.allowed_codes).exists()
