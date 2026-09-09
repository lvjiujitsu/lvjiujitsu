from system.core.access.registry import refresh_identity


class IdentityMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        refresh_identity(request)
        return self.get_response(request)
