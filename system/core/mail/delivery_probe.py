import json
import re
import secrets
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import CommandError
from django.test import Client

MAILBOX_API = "https://api.mail.tm"
RESET_LINK = re.compile(r"https?://[^/\s]+(/password-reset/[^\s]+)")
POLL_SECONDS = 3


def site_client():
    parsed = urlparse(settings.SITE_BASE_URL)
    return (
        Client(SERVER_NAME=parsed.hostname or "localhost"),
        parsed.scheme == "https",
    )


def call_mailbox(path, payload=None, token=""):
    headers = {"Accept": "application/json", "User-Agent": settings.SITE_NAME}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        MAILBOX_API + path,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise CommandError(
            f"A caixa descartável recusou {path}: HTTP {exc.code}. {detail}"
        )
    except urllib.error.URLError as exc:
        raise CommandError(f"A caixa descartável está inalcançável: {exc.reason}.")


def collect(payload):
    if isinstance(payload, list):
        return payload
    return payload.get("hydra:member") or payload.get("member") or []


def mailbox_prefix():
    return re.sub(r"[^a-z0-9]+", "-", settings.SITE_NAME.lower()).strip("-")


def open_mailbox():
    domains = collect(call_mailbox("/domains"))
    available = next(
        (item["domain"] for item in domains if item.get("isActive", True)), ""
    )
    if not available:
        raise CommandError("A caixa descartável não ofereceu nenhum domínio ativo.")
    address = f"{mailbox_prefix()}-{secrets.token_hex(4)}@{available}"
    password = secrets.token_urlsafe(16)
    call_mailbox("/accounts", {"address": address, "password": password})
    token = call_mailbox("/token", {"address": address, "password": password})
    return address, token["token"]


def request_reset(address):
    client, secure = site_client()
    response = client.post("/password-reset/", {"email": address}, secure=secure)
    if response.status_code != 302:
        raise CommandError(
            f"A tela de recuperação respondeu {response.status_code}, não 302."
        )


def wait_for_link(token, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for message in collect(call_mailbox("/messages", token=token)):
            body = call_mailbox(f"/messages/{message['id']}", token=token)
            found = RESET_LINK.search(body.get("text") or "")
            if found:
                return found.group(1)
        time.sleep(POLL_SECONDS)
    raise CommandError(
        f"Nenhuma mensagem com link de recuperação chegou em {seconds}s. "
        "Confira o log do provedor: o Django esconde falha de envio."
    )


def set_new_password(path):
    client, secure = site_client()
    opened = client.get(path, follow=True, secure=secure)
    if opened.status_code != 200:
        raise CommandError(f"O link devolveu {opened.status_code}, não 200.")
    password = f"{secrets.token_urlsafe(12)}Aa1"
    saved = client.post(
        opened.request["PATH_INFO"],
        {"new_password1": password, "new_password2": password},
        secure=secure,
    )
    if saved.status_code != 302:
        raise CommandError("A troca de senha foi recusada pelo formulário.")
    return password
