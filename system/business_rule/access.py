from dataclasses import dataclass, field

from django.shortcuts import redirect
from django.urls import reverse

from system.business_rule.constants import (
    ADMINISTRATIVE_PERSON_TYPE_CODES,
    Capability,
    INSTRUCTOR_PERSON_TYPE_CODES,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
    TECHNICAL_ADMIN_CAPABILITIES,
    TECHNICAL_ADMIN_PERSON_TYPE_CODES,
)
from system.business_rule.models import PortalAccount
from system.business_rule.services.portal_auth import (
    PORTAL_ACCOUNT_SESSION_KEY,
    TECHNICAL_ADMIN_SESSION_KEY,
    resolve_portal_account_from_session,
    resolve_technical_admin_from_session,
)
from system.business_rule.services.portal_capabilities import (
    get_person_capabilities,
    get_person_operational_role_codes,
)
from system.core.documents import ensure_formatted_cpf
from system.core.password_reset import AccountAdapter
from system.core.access import (
    CapabilityRequired,
    Identity,
    identity_of,
    refresh_identity,
)

PORTAL_KIND = "portal"
TECHNICAL_ADMIN_KIND = "technical-admin"


@dataclass(frozen=True)
class PortalActor:
    account: object = None
    person: object = None
    technical_admin: object = None
    type_codes: frozenset = field(default_factory=frozenset)
    role_codes: frozenset = field(default_factory=frozenset)
    supports_classes: bool = False


def resolve_identity(request):
    technical_admin = resolve_technical_admin_from_session(request)
    access_account = resolve_portal_account_from_session(request)

    if access_account is None and technical_admin is None:
        return None

    if access_account is not None:
        return _portal_identity(access_account, technical_admin)

    return _technical_admin_identity(technical_admin)


def _portal_identity(access_account, technical_admin):
    person = access_account.person
    person_type_code = person.person_type.code if person.person_type_id else ""
    capabilities = frozenset(get_person_capabilities(person))
    return Identity(
        kind=PORTAL_KIND,
        actor=PortalActor(
            account=access_account,
            person=person,
            technical_admin=technical_admin,
            type_codes=frozenset({person_type_code}) if person_type_code else frozenset(),
            role_codes=frozenset(get_person_operational_role_codes(person)),
            supports_classes=Capability.SUPPORT_CLASSES in capabilities,
        ),
        label=person.full_name,
        capabilities=capabilities,
    )


def _technical_admin_identity(technical_admin):
    return Identity(
        kind=TECHNICAL_ADMIN_KIND,
        actor=PortalActor(
            account=None,
            person=None,
            technical_admin=technical_admin,
            type_codes=frozenset(TECHNICAL_ADMIN_PERSON_TYPE_CODES),
            role_codes=frozenset(),
            supports_classes=True,
        ),
        label=_technical_admin_label(technical_admin),
        capabilities=frozenset(TECHNICAL_ADMIN_CAPABILITIES),
    )


def _technical_admin_label(technical_admin):
    return (
        technical_admin.get_short_name()
        or technical_admin.get_full_name()
        or technical_admin.get_username()
    )


class PortalLoginRequiredMixin(CapabilityRequired):
    def denied(self, request):
        return redirect(reverse("system:dashboard-redirect"))


class PortalRoleRequiredMixin(PortalLoginRequiredMixin):
    allowed_codes: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if identity_of(request).authenticated and not self.has_allowed_role():
            return self.denied(request)
        return super().dispatch(request, *args, **kwargs)

    def has_allowed_role(self) -> bool:
        identity = identity_of(self.request)
        if identity.kind == TECHNICAL_ADMIN_KIND:
            return True
        if self.required_capabilities:
            return identity.has_any(*self.required_capabilities)
        person = identity.actor.person if identity.actor is not None else None
        if person is None or not person.person_type_id:
            return False
        return person.person_type.code in self.allowed_codes


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES
    required_capabilities = (Capability.MANAGE_ACADEMY,)


def portal_person(request):
    actor = identity_of(request).actor
    return actor.person if actor is not None else None


def portal_account(request):
    actor = identity_of(request).actor
    return actor.account if actor is not None else None


def portal_capabilities(request):
    return identity_of(request).capabilities


def is_technical_admin(request):
    actor = identity_of(request).actor
    return bool(actor is not None and actor.technical_admin is not None)


def supports_classes(request):
    actor = identity_of(request).actor
    return bool(actor is not None and actor.supports_classes)


def has_person_type(request, codes):
    actor = identity_of(request).actor
    if actor is None:
        return False
    return bool(actor.type_codes.intersection(codes))


def is_administrative(request):
    return has_person_type(request, ADMINISTRATIVE_PERSON_TYPE_CODES)


def is_instructor(request):
    return has_person_type(request, INSTRUCTOR_PERSON_TYPE_CODES)


def is_student(request):
    return has_person_type(request, STUDENT_PORTAL_PERSON_TYPE_CODES)


def login_portal_identity(request, *, portal_account=None, technical_admin_user=None):
    request.session.cycle_key()
    request.session.pop(PORTAL_ACCOUNT_SESSION_KEY, None)
    request.session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)

    if portal_account is not None:
        request.session[PORTAL_ACCOUNT_SESSION_KEY] = portal_account.pk

    if technical_admin_user is not None:
        request.session[TECHNICAL_ADMIN_SESSION_KEY] = technical_admin_user.pk

    refresh_identity(request)


def logout_portal_identity(request):
    request.session.pop(PORTAL_ACCOUNT_SESSION_KEY, None)
    request.session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)
    refresh_identity(request)


class PortalAccountAdapter(AccountAdapter):
    model = PortalAccount

    def find(self, lookup_value):
        try:
            formatted_cpf = ensure_formatted_cpf((lookup_value or "").strip())
        except ValueError:
            return None
        return (
            PortalAccount.objects.select_related("person")
            .filter(person__cpf=formatted_cpf)
            .first()
        )

    def password_hash(self, account):
        return account.password_hash

    def email(self, account):
        return (account.person.email or "").strip()

    def display_name(self, account):
        return account.person.full_name or self.email(account)

    def is_active(self, account):
        return bool(account.is_active and account.person.is_active)

    def set_password(self, account, raw_password):
        account.set_password(raw_password)
        account.failed_login_attempts = 0
        account.save(
            update_fields=(
                "password_hash",
                "password_updated_at",
                "failed_login_attempts",
                "updated_at",
            )
        )

    def login_url(self, account):
        return reverse("system:login")
