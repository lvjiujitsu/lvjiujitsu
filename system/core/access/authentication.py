_authenticators = []


def register_authenticator(authenticator):
    if authenticator not in _authenticators:
        _authenticators.append(authenticator)


def registered_authenticators():
    return tuple(_authenticators)


def authenticate_identity(request, credentials):
    for authenticator in _authenticators:
        outcome = authenticator(request, credentials)
        if outcome is not None:
            return outcome
    return None
