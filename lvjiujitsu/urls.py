from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from system.core.staticfiles import FaviconRedirectView

urlpatterns = [
    path("favicon.ico", FaviconRedirectView.as_view()),
    path("django-admin/", admin.site.urls),
    path("", include("system.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
