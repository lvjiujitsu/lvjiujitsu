from django.apps import AppConfig


class BusinessRuleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "system.business_rule"
    label = "business_rule"
    verbose_name = "Portal da academia"

    def ready(self):
        from system.business_rule import signals
        from system.business_rule.access import (
            PortalAccountAdapter,
            resolve_identity,
        )
        from system.core.access import register_identity_resolver
        from system.core.password_reset import register_resettable_kind

        register_identity_resolver(resolve_identity)
        register_resettable_kind("portal", PortalAccountAdapter())
