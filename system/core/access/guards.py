from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from system.core.access.contracts import ANONYMOUS


def identity_of(request):
    return getattr(request, "identity", ANONYMOUS)


def require_identity(request, capabilities, login_url=None, on_denied=None):
    identity = identity_of(request)
    if not identity.authenticated:
        return redirect_to_login(request.get_full_path(), login_url)
    if not identity.has_any(*capabilities):
        if on_denied is not None:
            return on_denied(request)
        raise PermissionDenied
    return None


def capability_required(*capabilities, login_url=None, on_denied=None):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            denial = require_identity(request, capabilities, login_url, on_denied)
            if denial is not None:
                return denial
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


class CapabilityRequired:
    required_capabilities = ()
    login_url = None

    def denied(self, request):
        raise PermissionDenied

    def dispatch(self, request, *args, **kwargs):
        denial = require_identity(
            request, self.required_capabilities, self.login_url, self.denied
        )
        if denial is not None:
            return denial
        return super().dispatch(request, *args, **kwargs)
