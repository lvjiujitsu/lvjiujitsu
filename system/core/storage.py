from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


def object_storage_url(value, *, variable, scheme, required_in=""):
    value = (value or "").strip()
    if not value:
        if required_in:
            raise ImproperlyConfigured(
                f"{variable} deve ser definida no ambiente {required_in} "
                "para o armazenamento de arquivo enviado."
            )
        return ""
    parsed = urlparse(value)
    if (
        parsed.scheme != scheme
        or not parsed.username
        or not parsed.password
        or not parsed.hostname
    ):
        raise ImproperlyConfigured(
            f"{variable} inválida. Use {scheme}://API_KEY:API_SECRET@CLOUD_NAME."
        )
    return value
