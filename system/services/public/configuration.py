from system.models import AcademyConfiguration


def get_or_create_default_academy_configuration():
    configuration, _ = AcademyConfiguration.objects.get_or_create(
        singleton_key="default",
        defaults={
            "academy_name": "LV JIU JITSU",
        },
    )
    return configuration
