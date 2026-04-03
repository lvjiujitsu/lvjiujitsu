from django.apps import AppConfig


class SystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "system"
    verbose_name = "LV Jiu Jitsu System"

    def ready(self):
        from system.sqlite_compat import register_sqlite_type_handlers

        register_sqlite_type_handlers()
        try:
            import system.signals  # noqa: F401
        except ImportError:
            return
