from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "system.core"
    label = "core"
    verbose_name = "Base técnica"

    def ready(self):
        from system.core import admin
