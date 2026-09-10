from django.apps import AppConfig


class BusinessRuleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "system.business_rule"
    label = "business_rule"
    verbose_name = "Portal da academia"

    def ready(self):
        from system.core.access import register_identity_resolver
        from system.core.audit import register_actor_label_resolver
        from system.core.password_reset import register_resettable_kind

        from system.business_rule import signals
        from system.business_rule.access import (
            PortalAccountAdapter,
            actor_label_for,
            resolve_identity,
        )

        register_identity_resolver(resolve_identity)
        register_actor_label_resolver(actor_label_for)
        register_resettable_kind("portal", PortalAccountAdapter())
