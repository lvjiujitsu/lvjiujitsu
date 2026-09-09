def snapshot_scalar(snapshot, key, default=""):
    value = snapshot.get(key, default)
    if isinstance(value, list):
        value = value[0] if value else default
    return value or default
