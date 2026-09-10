from system.core.access.registry import refresh_identity


def session_actor(request, session_key, queryset):
    identifier = request.session.get(session_key)
    if not identifier:
        return None
    actor = queryset.filter(pk=identifier).first()
    if actor is None:
        request.session.pop(session_key, None)
    return actor


def login_session_identity(request, *, clear=(), **identifiers):
    request.session.cycle_key()
    for session_key in clear:
        request.session.pop(session_key, None)
    for session_key, actor in identifiers.items():
        request.session.pop(session_key, None)
        if actor is not None:
            request.session[session_key] = actor.pk
    refresh_identity(request)


def logout_session_identity(request, *session_keys):
    for session_key in session_keys:
        request.session.pop(session_key, None)
    refresh_identity(request)
