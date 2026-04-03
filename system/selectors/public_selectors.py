from system.models import AcademyConfiguration, PublicClassSchedule, PublicPlan


def get_active_academy_configuration():
    return AcademyConfiguration.objects.filter(is_active=True).first()


def get_public_plans():
    return PublicPlan.objects.filter(is_active=True)


def get_public_class_schedules():
    return PublicClassSchedule.objects.filter(is_active=True)


def get_public_landing_context():
    return {
        "academy_configuration": get_active_academy_configuration(),
        "public_plans": get_public_plans(),
        "public_class_schedules": get_public_class_schedules(),
    }
