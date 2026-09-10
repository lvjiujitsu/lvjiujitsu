from contextlib import contextmanager

_suspended = False


@contextmanager
def suspended_signals():
    global _suspended
    previous = _suspended
    _suspended = True
    try:
        yield
    finally:
        _suspended = previous


def is_fixture_load(kwargs):
    return _suspended or bool(kwargs.get("raw"))
