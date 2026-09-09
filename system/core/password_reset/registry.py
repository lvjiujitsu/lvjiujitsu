_adapters = {}


def register_resettable_kind(kind, adapter):
    _adapters[kind] = adapter


def adapter_for(kind):
    return _adapters.get(kind)


def registered_kinds():
    return tuple(_adapters.items())
