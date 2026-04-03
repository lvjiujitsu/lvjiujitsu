from django.db.models.signals import post_migrate
from django.dispatch import receiver

from system.constants import ROLE_CHOICES
from system.models import ConsentTerm, CsvExportControl, IbjjfBelt, SystemRole
from system.services.public.configuration import get_or_create_default_academy_configuration


@receiver(post_migrate)
def ensure_initial_roles(sender, **kwargs):
    if sender.name != "system":
        return
    for role_code in ROLE_CHOICES:
        SystemRole.objects.get_or_create(
            code=role_code,
            defaults={"name": role_code.replace("_", " ").title()},
        )
    get_or_create_default_academy_configuration()
    _ensure_default_consent_terms()
    _ensure_default_belts()
    _ensure_default_export_control()


def _ensure_default_consent_terms():
    default_terms = (
        {
            "code": "service_agreement",
            "title": "Termo de matricula e convivencia",
            "version": 1,
            "content": "Autorizo o cadastro e concordo com as regras operacionais da academia.",
        },
        {
            "code": "privacy_policy",
            "title": "Termo de privacidade e dados pessoais",
            "version": 1,
            "content": "Autorizo o tratamento dos dados pessoais conforme a politica vigente.",
        },
    )
    for payload in default_terms:
        ConsentTerm.objects.get_or_create(
            code=payload["code"],
            version=payload["version"],
            defaults={
                "title": payload["title"],
                "content": payload["content"],
                "required_for_onboarding": True,
                "is_active": True,
            },
        )


def _ensure_default_belts():
    belts = (
        ("white", "Branca", 1),
        ("blue", "Azul", 2),
        ("purple", "Roxa", 3),
        ("brown", "Marrom", 4),
        ("black", "Preta", 5),
    )
    for code, name, order in belts:
        IbjjfBelt.objects.get_or_create(
            code=code,
            defaults={"name": name, "display_order": order},
        )


def _ensure_default_export_control():
    from django.conf import settings

    CsvExportControl.objects.get_or_create(
        name="critical_csv_exports",
        defaults={"control_file_path": str(settings.CRITICAL_EXPORT_CONTROL_FILE)},
    )
