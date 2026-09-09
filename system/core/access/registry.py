from system.core.access.contracts import ANONYMOUS

_resolvers = []


def register_identity_resolver(resolver):
    if resolver not in _resolvers:
        _resolvers.append(resolver)


def refresh_identity(request):
    request.identity = resolve_identity(request)
    return request.identity


def resolve_identity(request):
    for resolver in _resolvers:
        identity = resolver(request)
        if identity is not None:
            return identity
    return ANONYMOUS
