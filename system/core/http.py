from django.utils.http import url_has_allowed_host_and_scheme

AJAX_HEADER = "X-Requested-With"
AJAX_VALUE = "XMLHttpRequest"
MODAL_PARAM = "modal"
MODAL_VALUE = "1"


def is_ajax(request):
    return request.headers.get(AJAX_HEADER) == AJAX_VALUE


def is_modal(request):
    return request.GET.get(MODAL_PARAM) == MODAL_VALUE or is_ajax(request)


def safe_redirect_target(request, candidate, *, allowed=None, fallback):
    target = (candidate or "").strip()
    if not target:
        return fallback
    if allowed is not None:
        return target if target in allowed else fallback
    reachable = url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    return target if reachable else fallback


class ModalViewMixin:
    modal_template_name = ""

    def is_modal(self):
        return is_modal(self.request)

    def get_template_names(self):
        if self.is_modal() and self.modal_template_name:
            return [self.modal_template_name]
        return super().get_template_names()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.is_modal():
            response["X-Frame-Options"] = "SAMEORIGIN"
        return response
