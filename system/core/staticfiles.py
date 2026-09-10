from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

FAVICON_STATIC_PATH = "logo/favicon.png"


class FaviconRedirectView(RedirectView):
    permanent = False
    static_path = FAVICON_STATIC_PATH

    def get_redirect_url(self, *args, **kwargs):
        return staticfiles_storage.url(self.static_path)
