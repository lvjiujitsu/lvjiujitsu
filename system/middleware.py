from django.conf import settings
from django.utils import timezone


class RequestTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_timezone = request.session.get("active_timezone", settings.TIME_ZONE)
        timezone.activate(active_timezone)
        response = self.get_response(request)
        timezone.deactivate()
        return response
