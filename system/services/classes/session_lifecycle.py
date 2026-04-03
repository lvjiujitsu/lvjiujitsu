def open_class_session(session, actor):
    session.open(actor)
    session.full_clean()
    session.save()
    return session


def close_class_session(session, actor):
    session.close(actor)
    session.full_clean()
    session.save()
    return session


def save_class_session(session):
    session.full_clean()
    session.save()
    return session
