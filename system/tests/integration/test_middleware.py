import pytest
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

from system.middleware import RequestTimezoneMiddleware


@pytest.mark.django_db
def test_timezone_middleware_activates_session_timezone(rf):
    request = rf.get("/")
    request.session = {"active_timezone": settings.TIME_ZONE}

    middleware = RequestTimezoneMiddleware(lambda req: HttpResponse(timezone.get_current_timezone_name()))
    response = middleware(request)

    assert response.content.decode() == settings.TIME_ZONE
