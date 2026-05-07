from system.services.seeding import (
    seed_belts,
    seed_class_catalog,
    seed_class_categories,
    seed_graduation_rules,
    seed_ibjjf_age_categories,
    seed_official_instructors,
    seed_person_types,
    seed_product_categories,
    seed_products,
    seed_teacher_payroll_configs,
)


def seed_class_catalog_dependencies():
    seed_person_types()
    seed_class_categories()
    seed_ibjjf_age_categories()
    seed_belts()
    seed_graduation_rules()
    seed_official_instructors()


def seed_full_class_catalog():
    seed_class_catalog_dependencies()
    return seed_class_catalog()


def seed_full_class_catalog_with_payroll():
    catalog = seed_full_class_catalog()
    seed_teacher_payroll_configs()
    return catalog


def seed_full_product_catalog():
    seed_product_categories()
    return seed_products()
