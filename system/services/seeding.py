from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.models import (
    BeltRank,
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassGroup,
    ClassSchedule,
    Graduation,
    GraduationRule,
    IbjjfAgeCategory,
    Membership,
    MembershipCreatedVia,
    MembershipStatus,
    PaymentProvider,
    PaymentStatus,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PixKeyType,
    PortalAccount,
    RegistrationOrder,
    SubscriptionPlan,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
    PayoutKind,
    PayoutStatus,
    TrainingStyle,
    WeekdayCode,
)
from system.models.plan import (
    CYCLE_MONTHS,
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.models.product import Product, ProductCategory, ProductVariant
from system.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES, PersonTypeCode
from system.services.graduation import ensure_initial_graduation_for_beginner
from system.services.registration import ensure_default_person_types, sync_person_class_enrollments
from system.services.payroll_rules import (
    PAYROLL_METHOD_FIXED_MONTHLY,
    PAYROLL_METHOD_STUDENT_PERCENTAGE,
    encode_payroll_rules,
)
from system.utils import ensure_formatted_cpf


class SeedDependencyError(ValueError):
    pass


DEFAULT_TEST_PORTAL_PASSWORD = settings.SEED_TEST_PORTAL_PASSWORD
OFFICIAL_INSTRUCTOR_PASSWORD = DEFAULT_TEST_PORTAL_PASSWORD

CLASS_CATEGORY_DEFINITIONS = (
    {
        "code": "adult",
        "display_name": "Adulto",
        "audience": CategoryAudience.ADULT,
        "description": "Categoria local para alunos adultos.",
        "display_order": 1,
    },
    {
        "code": "juvenile",
        "display_name": "Juvenil",
        "audience": CategoryAudience.JUVENILE,
        "description": "Categoria local para alunos juvenis.",
        "display_order": 2,
    },
    {
        "code": "kids",
        "display_name": "Kids",
        "audience": CategoryAudience.KIDS,
        "description": "Categoria local para alunos kids.",
        "display_order": 3,
    },
    {
        "code": "women",
        "display_name": "Feminino",
        "audience": CategoryAudience.WOMEN,
        "description": "Categoria local para turma feminina.",
        "display_order": 4,
    },
)

IBJJF_AGE_CATEGORY_DEFINITIONS = (
    ("pre-mirim-1", "Pré-Mirim 1", CategoryAudience.KIDS, 4, 4, 1),
    ("pre-mirim-2", "Pré-Mirim 2", CategoryAudience.KIDS, 5, 5, 2),
    ("pre-mirim-3", "Pré-Mirim 3", CategoryAudience.KIDS, 6, 6, 3),
    ("mirim-1", "Mirim 1", CategoryAudience.KIDS, 7, 7, 4),
    ("mirim-2", "Mirim 2", CategoryAudience.KIDS, 8, 8, 5),
    ("mirim-3", "Mirim 3", CategoryAudience.KIDS, 9, 9, 6),
    ("infantil-1", "Infantil 1", CategoryAudience.KIDS, 10, 10, 7),
    ("infantil-2", "Infantil 2", CategoryAudience.KIDS, 11, 11, 8),
    ("infantil-3", "Infantil 3", CategoryAudience.KIDS, 12, 12, 9),
    ("infanto-juvenil-1", "Infanto-Juvenil 1", CategoryAudience.KIDS, 13, 13, 10),
    ("infanto-juvenil-2", "Infanto-Juvenil 2", CategoryAudience.KIDS, 14, 14, 11),
    ("infanto-juvenil-3", "Infanto-Juvenil 3", CategoryAudience.KIDS, 15, 15, 12),
    ("juvenile-1", "Juvenil 1", CategoryAudience.JUVENILE, 16, 16, 13),
    ("juvenile-2", "Juvenil 2", CategoryAudience.JUVENILE, 17, 17, 14),
    ("adult", "Adulto", CategoryAudience.ADULT, 18, 29, 15),
    ("master-1", "Master 1", CategoryAudience.ADULT, 30, 35, 16),
    ("master-2", "Master 2", CategoryAudience.ADULT, 36, 40, 17),
    ("master-3", "Master 3", CategoryAudience.ADULT, 41, 45, 18),
    ("master-4", "Master 4", CategoryAudience.ADULT, 46, 50, 19),
    ("master-5", "Master 5", CategoryAudience.ADULT, 51, 55, 20),
    ("master-6", "Master 6", CategoryAudience.ADULT, 56, 60, 21),
    ("master-7", "Master 7", CategoryAudience.ADULT, 61, None, 22),
)

OFFICIAL_CLASS_CATALOG_DEFINITIONS = (
    {
        "code": "adult-layon",
        "display_name": "Jiu Jitsu",
        "class_category": "adult",
        "description": "Turma adulta com o professor Layon Quirino.",
        "teacher": {
            "full_name": "Layon Quirino",
            "cpf": "92000000001",
            "email": "layon.quirino@lvjiujitsu.test",
            "phone": "(62) 98888-1001",
        },
        "schedules": (
            (WeekdayCode.MONDAY, TrainingStyle.GI, time(6, 30), 1),
            (WeekdayCode.TUESDAY, TrainingStyle.GI, time(6, 30), 2),
            (WeekdayCode.WEDNESDAY, TrainingStyle.NO_GI, time(6, 30), 3),
            (WeekdayCode.THURSDAY, TrainingStyle.GI, time(6, 30), 4),
            (WeekdayCode.FRIDAY, TrainingStyle.GI, time(6, 30), 5),
        ),
    },
    {
        "code": "adult-vinicius",
        "display_name": "Jiu Jitsu",
        "class_category": "adult",
        "description": "Turma adulta com o professor Vinicius Antonio.",
        "teacher": {
            "full_name": "Vinicius Antonio",
            "cpf": "92000000002",
            "email": "vinicius.antonio@lvjiujitsu.test",
            "phone": "(62) 98888-1002",
        },
        "schedules": (
            (WeekdayCode.MONDAY, TrainingStyle.GI, time(11, 0), 1),
            (WeekdayCode.WEDNESDAY, TrainingStyle.GI, time(11, 0), 2),
            (WeekdayCode.FRIDAY, TrainingStyle.NO_GI, time(11, 0), 3),
        ),
    },
    {
        "code": "adult-lauro",
        "display_name": "Jiu Jitsu",
        "class_category": "adult",
        "description": "Turma adulta com o professor Lauro Viana.",
        "teacher": {
            "full_name": "Lauro Viana",
            "cpf": "92000000003",
            "email": "lauro.viana@lvjiujitsu.test",
            "phone": "(62) 98888-1003",
        },
        "schedules": (
            (WeekdayCode.MONDAY, TrainingStyle.GI, time(19, 0), 1),
            (WeekdayCode.TUESDAY, TrainingStyle.GI, time(19, 0), 2),
            (WeekdayCode.WEDNESDAY, TrainingStyle.NO_GI, time(19, 0), 3),
            (WeekdayCode.THURSDAY, TrainingStyle.GI, time(19, 0), 4),
            (WeekdayCode.FRIDAY, TrainingStyle.GI, time(19, 0), 5),
        ),
    },
    {
        "code": "kids-andre",
        "display_name": "Jiu Jitsu",
        "class_category": "kids",
        "description": "Turma kids com o professor Andre Oliveira.",
        "teacher": {
            "full_name": "Andre Oliveira",
            "cpf": "92000000004",
            "email": "andre.oliveira@lvjiujitsu.test",
            "phone": "(62) 98888-1004",
        },
        "schedules": (
            (WeekdayCode.TUESDAY, TrainingStyle.GI, time(18, 0), 1),
            (WeekdayCode.THURSDAY, TrainingStyle.GI, time(18, 0), 2),
        ),
    },
    {
        "code": "juvenile-layon",
        "display_name": "Jiu Jitsu",
        "class_category": "juvenile",
        "description": "Turma juvenil com o professor Layon Quirino.",
        "teacher": {
            "full_name": "Layon Quirino",
            "cpf": "92000000001",
            "email": "layon.quirino@lvjiujitsu.test",
            "phone": "(62) 98888-1001",
        },
        "schedules": (
            (WeekdayCode.MONDAY, TrainingStyle.GI, time(18, 0), 1),
            (WeekdayCode.WEDNESDAY, TrainingStyle.GI, time(18, 0), 2),
            (WeekdayCode.FRIDAY, TrainingStyle.GI, time(18, 0), 3),
        ),
    },
    {
        "code": "women-vannessa",
        "display_name": "Jiu Jitsu",
        "class_category": "women",
        "description": "Turma feminina com a professora Vanessa Ferro.",
        "teacher": {
            "full_name": "Vanessa Ferro",
            "cpf": "92000000005",
            "email": "vanessa.ferro@lvjiujitsu.test",
            "phone": "(62) 98888-1005",
        },
        "schedules": (
            (WeekdayCode.SATURDAY, TrainingStyle.GI, time(10, 30), 1),
        ),
    },
)


def seed_person_types():
    return ensure_default_person_types()


@transaction.atomic
def seed_class_categories():
    categories = {}
    for definition in CLASS_CATEGORY_DEFINITIONS:
        category, _ = ClassCategory.objects.update_or_create(
            code=definition["code"],
            defaults=definition,
        )
        categories[category.code] = category
    return categories


BELT_RANK_DEFINITIONS = (
    {
        "code": "kids-white",
        "display_name": "Branca (Infantil)",
        "audience": CategoryAudience.KIDS,
        "color_hex": "#f5f5f5",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 4,
        "max_age": 15,
        "display_order": 10,
        "next_code": "kids-grey",
    },
    {
        "code": "kids-grey",
        "display_name": "Cinza",
        "audience": CategoryAudience.KIDS,
        "color_hex": "#9ca3af",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 4,
        "max_age": 15,
        "display_order": 20,
        "next_code": "kids-yellow",
    },
    {
        "code": "kids-yellow",
        "display_name": "Amarela",
        "audience": CategoryAudience.KIDS,
        "color_hex": "#facc15",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 7,
        "max_age": 15,
        "display_order": 30,
        "next_code": "kids-orange",
    },
    {
        "code": "kids-orange",
        "display_name": "Laranja",
        "audience": CategoryAudience.KIDS,
        "color_hex": "#fb923c",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 10,
        "max_age": 15,
        "display_order": 40,
        "next_code": "kids-green",
    },
    {
        "code": "kids-green",
        "display_name": "Verde",
        "audience": CategoryAudience.KIDS,
        "color_hex": "#22c55e",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 13,
        "max_age": 15,
        "display_order": 50,
        "next_code": "adult-white",
    },
    {
        "code": "adult-white",
        "display_name": "Branca",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#f5f5f5",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 16,
        "max_age": None,
        "display_order": 100,
        "next_code": "adult-blue",
    },
    {
        "code": "adult-blue",
        "display_name": "Azul",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#1e3a8a",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 16,
        "max_age": None,
        "display_order": 110,
        "next_code": "adult-purple",
    },
    {
        "code": "adult-purple",
        "display_name": "Roxa",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#5b21b6",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 16,
        "max_age": None,
        "display_order": 120,
        "next_code": "adult-brown",
    },
    {
        "code": "adult-brown",
        "display_name": "Marrom",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#78350f",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 4,
        "min_age": 18,
        "max_age": None,
        "display_order": 130,
        "next_code": "adult-black",
    },
    {
        "code": "adult-black",
        "display_name": "Preta",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#111827",
        "tip_color_hex": "#dc2626",
        "stripe_color_hex": "#ffffff",
        "max_grades": 6,
        "min_age": 19,
        "max_age": None,
        "display_order": 140,
        "next_code": "adult-coral-redblack",
    },
    {
        "code": "adult-coral-redblack",
        "display_name": "Coral (Vermelha e Preta)",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#b91c1c",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 0,
        "min_age": 50,
        "max_age": None,
        "display_order": 150,
        "next_code": "adult-coral-redwhite",
    },
    {
        "code": "adult-coral-redwhite",
        "display_name": "Coral (Vermelha e Branca)",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#dc2626",
        "tip_color_hex": "#ffffff",
        "stripe_color_hex": "#000000",
        "max_grades": 0,
        "min_age": 67,
        "max_age": None,
        "display_order": 160,
        "next_code": "adult-red",
    },
    {
        "code": "adult-red",
        "display_name": "Vermelha",
        "audience": CategoryAudience.ADULT,
        "color_hex": "#991b1b",
        "tip_color_hex": "#000000",
        "stripe_color_hex": "#ffffff",
        "max_grades": 0,
        "min_age": 67,
        "max_age": None,
        "display_order": 170,
        "next_code": None,
    },
)


GRADUATION_RULE_DEFINITIONS = (
    # Adulto: 4 graus dentro de cada faixa
    {"belt_code": "adult-white", "from_grade": 0, "to_grade": 1, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "adult-white", "from_grade": 1, "to_grade": 2, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "adult-white", "from_grade": 2, "to_grade": 3, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "adult-white", "from_grade": 3, "to_grade": 4, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "adult-white", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-blue", "from_grade": 0, "to_grade": 1, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-blue", "from_grade": 1, "to_grade": 2, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-blue", "from_grade": 2, "to_grade": 3, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-blue", "from_grade": 3, "to_grade": 4, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-blue", "from_grade": 4, "to_grade": None, "min_months": 24, "min_classes": 120, "window_months": 24},
    {"belt_code": "adult-purple", "from_grade": 0, "to_grade": 1, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-purple", "from_grade": 1, "to_grade": 2, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-purple", "from_grade": 2, "to_grade": 3, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-purple", "from_grade": 3, "to_grade": 4, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-purple", "from_grade": 4, "to_grade": None, "min_months": 18, "min_classes": 96, "window_months": 18},
    {"belt_code": "adult-brown", "from_grade": 0, "to_grade": 1, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-brown", "from_grade": 1, "to_grade": 2, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-brown", "from_grade": 2, "to_grade": 3, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-brown", "from_grade": 3, "to_grade": 4, "min_months": 6, "min_classes": 48, "window_months": 12},
    {"belt_code": "adult-brown", "from_grade": 4, "to_grade": None, "min_months": 12, "min_classes": 80, "window_months": 12},
    # Preta: graus
    {"belt_code": "adult-black", "from_grade": 0, "to_grade": 1, "min_months": 36, "min_classes": 192, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 1, "to_grade": 2, "min_months": 36, "min_classes": 192, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 2, "to_grade": 3, "min_months": 36, "min_classes": 192, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 3, "to_grade": 4, "min_months": 60, "min_classes": 240, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 4, "to_grade": 5, "min_months": 60, "min_classes": 240, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 5, "to_grade": 6, "min_months": 60, "min_classes": 240, "window_months": 36},
    {"belt_code": "adult-black", "from_grade": 6, "to_grade": None, "min_months": 84, "min_classes": 288, "window_months": 36},
    # Infantil: 4 graus em cada faixa
    {"belt_code": "kids-white", "from_grade": 0, "to_grade": 1, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-white", "from_grade": 1, "to_grade": 2, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-white", "from_grade": 2, "to_grade": 3, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-white", "from_grade": 3, "to_grade": 4, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-white", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-grey", "from_grade": 0, "to_grade": 1, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-grey", "from_grade": 1, "to_grade": 2, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-grey", "from_grade": 2, "to_grade": 3, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-grey", "from_grade": 3, "to_grade": 4, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-grey", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-yellow", "from_grade": 0, "to_grade": 1, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-yellow", "from_grade": 1, "to_grade": 2, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-yellow", "from_grade": 2, "to_grade": 3, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-yellow", "from_grade": 3, "to_grade": 4, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-yellow", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-orange", "from_grade": 0, "to_grade": 1, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-orange", "from_grade": 1, "to_grade": 2, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-orange", "from_grade": 2, "to_grade": 3, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-orange", "from_grade": 3, "to_grade": 4, "min_months": 3, "min_classes": 24, "window_months": 6},
    {"belt_code": "kids-orange", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-green", "from_grade": 0, "to_grade": 1, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-green", "from_grade": 1, "to_grade": 2, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-green", "from_grade": 2, "to_grade": 3, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-green", "from_grade": 3, "to_grade": 4, "min_months": 4, "min_classes": 32, "window_months": 12},
    {"belt_code": "kids-green", "from_grade": 4, "to_grade": None, "min_months": 6, "min_classes": 32, "window_months": 12},
)


@transaction.atomic
def seed_belts():
    ranks = {}
    for definition in BELT_RANK_DEFINITIONS:
        rank, _ = BeltRank.objects.update_or_create(
            code=definition["code"],
            defaults={
                "display_name": definition["display_name"],
                "audience": definition["audience"],
                "color_hex": definition["color_hex"],
                "tip_color_hex": definition.get("tip_color_hex", "#000000"),
                "stripe_color_hex": definition.get("stripe_color_hex", "#ffffff"),
                "max_grades": definition["max_grades"],
                "min_age": definition["min_age"],
                "max_age": definition["max_age"],
                "display_order": definition["display_order"],
                "is_active": True,
            },
        )
        ranks[rank.code] = rank
    for definition in BELT_RANK_DEFINITIONS:
        rank = ranks[definition["code"]]
        next_code = definition.get("next_code")
        rank.next_rank = ranks.get(next_code) if next_code else None
        rank.save(update_fields=["next_rank", "updated_at"])

    return {"belts": ranks}


@transaction.atomic
def seed_graduation_rules():
    belt_codes = tuple(dict.fromkeys(definition["belt_code"] for definition in GRADUATION_RULE_DEFINITIONS))
    ranks = _get_required_by_code(
        BeltRank,
        belt_codes,
        command_name="seed_graduation_rules",
        dependency_command="seed_belts",
    )
    rules = {}
    for definition in GRADUATION_RULE_DEFINITIONS:
        belt = ranks[definition["belt_code"]]
        rule, _ = GraduationRule.objects.update_or_create(
            belt_rank=belt,
            from_grade=definition["from_grade"],
            defaults={
                "to_grade": definition["to_grade"],
                "min_months_in_current_grade": definition["min_months"],
                "min_classes_required": definition["min_classes"],
                "min_classes_window_months": definition["window_months"],
                "is_active": True,
            },
        )
        rules[(belt.code, rule.from_grade)] = rule

    return {"rules": rules}


@transaction.atomic
def seed_ibjjf_age_categories():
    categories = {}
    for code, display_name, audience, minimum_age, maximum_age, display_order in IBJJF_AGE_CATEGORY_DEFINITIONS:
        category, _ = IbjjfAgeCategory.objects.update_or_create(
            code=code,
            defaults={
                "display_name": display_name,
                "audience": audience,
                "minimum_age": minimum_age,
                "maximum_age": maximum_age,
                "display_order": display_order,
                "is_active": True,
            },
        )
        categories[category.code] = category
    return categories


DEFAULT_INSTRUCTOR_BELT_CODE = "adult-black"
DEFAULT_INSTRUCTOR_BELT_GRADE = 1


@transaction.atomic
def seed_class_catalog(password: str = OFFICIAL_INSTRUCTOR_PASSWORD):
    class_category_codes = tuple(
        dict.fromkeys(definition["class_category"] for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS)
    )
    class_categories = _get_required_by_code(
        ClassCategory,
        class_category_codes,
        command_name="seed_class_catalog",
        dependency_command="seed_class_categories",
    )
    teacher_cpfs = tuple(
        dict.fromkeys(definition["teacher"]["cpf"] for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS)
    )
    teacher_people = _get_required_people_by_cpf(
        teacher_cpfs,
        command_name="seed_class_catalog",
        dependency_command="seed_official_instructors",
    )
    class_groups = {}

    for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS:
        teacher = teacher_people[ensure_formatted_cpf(definition["teacher"]["cpf"])]
        class_group = _upsert_class_group(
            definition=definition,
            class_category=class_categories[definition["class_category"]],
            teacher=teacher,
        )
        for weekday, training_style, start_time, display_order in definition["schedules"]:
            _upsert_class_schedule(
                class_group=class_group,
                weekday=weekday,
                training_style=training_style,
                start_time=start_time,
                display_order=display_order,
            )

        class_groups[class_group.code] = class_group

    return {
        "class_groups": class_groups,
        "teachers": teacher_people,
        "class_categories": class_categories,
    }


@transaction.atomic
def seed_official_instructors(password: str = OFFICIAL_INSTRUCTOR_PASSWORD):
    person_types = _get_required_by_code(
        PersonType,
        (PersonTypeCode.INSTRUCTOR,),
        command_name="seed_official_instructors",
        dependency_command="seed_person_type",
    )
    class_category_codes = tuple(
        dict.fromkeys(definition["class_category"] for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS)
    )
    class_categories = _get_required_by_code(
        ClassCategory,
        class_category_codes,
        command_name="seed_official_instructors",
        dependency_command="seed_class_categories",
    )
    instructor_belt_codes = tuple(
        dict.fromkeys(
            definition["teacher"].get("belt_code", DEFAULT_INSTRUCTOR_BELT_CODE)
            for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS
        )
    )
    belts = _get_required_by_code(
        BeltRank,
        instructor_belt_codes,
        command_name="seed_official_instructors",
        dependency_command="seed_belts",
    )

    teachers = {}
    for definition in _unique_official_teacher_definitions():
        teacher_definition = definition["teacher"]
        teacher = _upsert_person_with_account(
            full_name=teacher_definition["full_name"],
            cpf=teacher_definition["cpf"],
            email=teacher_definition["email"],
            phone=teacher_definition["phone"],
            birth_date=date(1988, 1, 1),
            blood_type="O+",
            allergies="",
            previous_injuries="",
            emergency_contact="Operação LV - (62) 98888-0000",
            password=password,
            person_type=person_types[PersonTypeCode.INSTRUCTOR],
            class_category=class_categories[definition["class_category"]],
        )
        _ensure_instructor_graduation(
            teacher=teacher,
            belts=belts,
            belt_code=teacher_definition.get("belt_code", DEFAULT_INSTRUCTOR_BELT_CODE),
            grade_number=teacher_definition.get("belt_grade", DEFAULT_INSTRUCTOR_BELT_GRADE),
        )
        teachers[teacher.cpf] = teacher

    return {"teachers": teachers}


@transaction.atomic
def seed_teacher_payroll_configs():
    class_group_codes = tuple(definition["code"] for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS)
    class_groups = _get_required_by_code(
        ClassGroup,
        class_group_codes,
        command_name="seed_teacher_payroll_configs",
        dependency_command="seed_class_catalog",
    )
    return _seed_default_payroll_configs(class_groups)


def _unique_official_teacher_definitions():
    seen = set()
    for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS:
        cpf = ensure_formatted_cpf(definition["teacher"]["cpf"])
        if cpf in seen:
            continue
        seen.add(cpf)
        yield definition


def _ensure_instructor_graduation(*, teacher, belts, belt_code, grade_number):
    if Graduation.objects.filter(person=teacher).exists():
        return None
    belt = belts.get(belt_code)
    if belt is None:
        return None
    awarded_at = timezone.localdate() - timedelta(days=730)
    return Graduation.objects.create(
        person=teacher,
        belt_rank=belt,
        grade_number=grade_number,
        awarded_at=awarded_at,
        notes="Graduação inicial cadastrada pelo seed.",
    )


def _seed_default_payroll_configs(class_groups):
    definitions = (
        {
            "person": class_groups["adult-layon"].main_teacher,
            "monthly_salary": "400.00",
            "payment_day": 28,
            "rules": (
                {
                    "method": PAYROLL_METHOD_FIXED_MONTHLY,
                    "amount": "400.00",
                    "scope": "class_group",
                    "class_group_code": "adult-layon",
                },
                {
                    "method": PAYROLL_METHOD_STUDENT_PERCENTAGE,
                    "percentage": "50.00",
                    "scope": "class_group",
                    "class_group_code": "juvenile-layon",
                },
            ),
        },
        {
            "person": class_groups["adult-vinicius"].main_teacher,
            "monthly_salary": "400.00",
            "payment_day": 28,
            "rules": (
                {
                    "method": PAYROLL_METHOD_FIXED_MONTHLY,
                    "amount": "400.00",
                    "scope": "class_group",
                    "class_group_code": "adult-vinicius",
                },
            ),
        },
        {
            "person": class_groups["adult-lauro"].main_teacher,
            "monthly_salary": "0.00",
            "payment_day": 28,
            "rules": (),
        },
        {
            "person": class_groups["kids-andre"].main_teacher,
            "monthly_salary": "0.00",
            "payment_day": 28,
            "rules": (),
        },
        {
            "person": class_groups["women-vannessa"].main_teacher,
            "monthly_salary": "0.00",
            "payment_day": 28,
            "rules": (),
        },
    )
    configs = {}
    bank_accounts = {}
    entries = []
    for definition in definitions:
        person = definition["person"]
        config, _ = TeacherPayrollConfig.objects.update_or_create(
            person=person,
            defaults={
                "monthly_salary": Decimal(definition["monthly_salary"]),
                "payment_day": definition["payment_day"],
                "is_active": True,
                "notes": encode_payroll_rules(definition["rules"]),
            },
        )
        bank_account, _ = TeacherBankAccount.objects.update_or_create(
            person=person,
            defaults={
                "pix_key": person.cpf,
                "pix_key_type": PixKeyType.CPF,
                "holder_name": person.full_name,
                "holder_document": person.cpf,
                "is_active": True,
            },
        )
        configs[person.cpf] = config
        bank_accounts[person.cpf] = bank_account
        entries.append(
            {
                "person": person,
                "config": config,
                "bank_account": bank_account,
                "rules_count": len(definition["rules"]),
            }
        )
    return {
        "payroll_configs": configs,
        "bank_accounts": bank_accounts,
        "entries": entries,
    }


def _seed_manual_person_catalog(password: str):
    seed_ibjjf_age_categories()
    seed_belts()
    seed_graduation_rules()
    seed_official_instructors(password=password)
    catalog = seed_class_catalog(password=password)
    seed_teacher_payroll_configs()
    return catalog


@transaction.atomic
def seed_person_student(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    catalog = _seed_manual_person_catalog(password=password)
    student = _upsert_person_with_account(
        full_name="Aluno Teste Individual",
        cpf="90000000001",
        email="aluno.individual@example.com",
        phone="(62) 99999-0001",
        birth_date=date(1998, 1, 10),
        biological_sex=BiologicalSex.MALE,
        blood_type="O+",
        allergies="",
        previous_injuries="",
        emergency_contact="Mãe - (62) 99999-1001",
        password=password,
        person_type=person_types[PersonTypeCode.STUDENT],
        class_category=categories["adult"],
        class_groups=[catalog["class_groups"]["adult-lauro"]],
    )
    return {"student": student}


@transaction.atomic
def seed_person_student_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    catalog = _seed_manual_person_catalog(password=password)
    holder_group = catalog["class_groups"]["adult-vinicius"]
    dependent_group = catalog["class_groups"]["kids-andre"]
    holder = _upsert_person_with_account(
        full_name="Aluno Titular com Dependente",
        cpf="90000000002",
        email="titular.dependente@example.com",
        phone="(62) 99999-0002",
        birth_date=date(1992, 4, 5),
        biological_sex=BiologicalSex.MALE,
        blood_type="A+",
        allergies="",
        previous_injuries="Lesão antiga no joelho esquerdo.",
        emergency_contact="Irmão - (62) 99999-1002",
        password=password,
        person_type=person_types[PersonTypeCode.STUDENT],
        class_category=categories["adult"],
        class_groups=[holder_group],
    )
    dependent = _upsert_person_with_account(
        full_name="Dependente do Aluno Titular",
        cpf="90000000003",
        email="dependente.titular@example.com",
        phone="(62) 99999-0003",
        birth_date=date(2014, 9, 18),
        biological_sex=BiologicalSex.MALE,
        blood_type="O+",
        allergies="",
        previous_injuries="",
        emergency_contact="Pai - (62) 99999-1003",
        password=password,
        person_type=person_types[PersonTypeCode.DEPENDENT],
        class_category=categories["kids"],
        class_groups=[dependent_group],
    )
    _upsert_relationship(
        holder,
        dependent,
        "Titular responsável pelo dependente.",
        kinship_type="father",
    )
    return {"holder": holder, "dependent": dependent}


@transaction.atomic
def seed_person_guardian(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    guardian = _upsert_person_with_account(
        full_name="Responsável Teste Individual",
        cpf="90000000004",
        email="responsavel.individual@example.com",
        phone="(62) 99999-0004",
        birth_date=date(1987, 7, 20),
        biological_sex=BiologicalSex.FEMALE,
        blood_type="B+",
        allergies="",
        previous_injuries="",
        emergency_contact="Cônjuge - (62) 99999-1004",
        password=password,
        person_type=person_types[PersonTypeCode.GUARDIAN],
        class_category=categories["adult"],
    )
    return {"guardian": guardian}


@transaction.atomic
def seed_person_guardian_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    catalog = _seed_manual_person_catalog(password=password)
    dependent_group = catalog["class_groups"]["kids-andre"]
    guardian = _upsert_person_with_account(
        full_name="Responsável com Dependente",
        cpf="90000000005",
        email="responsavel.dependente@example.com",
        phone="(62) 99999-0005",
        birth_date=date(1985, 12, 12),
        biological_sex=BiologicalSex.FEMALE,
        blood_type="AB+",
        allergies="",
        previous_injuries="",
        emergency_contact="Avó - (62) 99999-1005",
        password=password,
        person_type=person_types[PersonTypeCode.GUARDIAN],
        class_category=categories["kids"],
    )
    dependent = _upsert_person_with_account(
        full_name="Aluno Dependente do Responsável",
        cpf="90000000006",
        email="aluno.dependente@example.com",
        phone="(62) 99999-0006",
        birth_date=date(2012, 6, 1),
        biological_sex=BiologicalSex.FEMALE,
        blood_type="A-",
        allergies="Lactose.",
        previous_injuries="",
        emergency_contact="Responsável - (62) 99999-1006",
        password=password,
        person_type=person_types[PersonTypeCode.DEPENDENT],
        class_category=categories["kids"],
        class_groups=[dependent_group],
    )
    _upsert_relationship(
        guardian,
        dependent,
        "Responsável financeiro do dependente.",
        kinship_type="mother",
    )
    return {"guardian": guardian, "dependent": dependent}


@transaction.atomic
def seed_person_administrative(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    administrative = _upsert_person_with_account(
        full_name="Administrativo Teste",
        cpf="90000000007",
        email="administrativo@example.com",
        phone="(62) 99999-0007",
        birth_date=date(1991, 8, 15),
        biological_sex=BiologicalSex.MALE,
        blood_type="O-",
        allergies="",
        previous_injuries="",
        emergency_contact="Operação - (62) 99999-1007",
        password=password,
        person_type=person_types[PersonTypeCode.ADMINISTRATIVE_ASSISTANT],
        class_category=categories["adult"],
    )
    return {"administrative": administrative}


TEST_PERSONA_DEFINITIONS = (
    {
        "kind": "student",
        "full_name": "Aluno PIX Pago Masculino",
        "cpf": "95000000001",
        "email": "aluno.pix.pago@example.com",
        "phone": "(62) 95000-0001",
        "birth_date": date(1995, 3, 12),
        "biological_sex": BiologicalSex.MALE,
        "class_group_code": "adult-lauro",
        "plan_code": "adult-2x-individual-monthly-pix",
        "payment_state": "paid_pix",
    },
    {
        "kind": "student",
        "full_name": "Aluno Cartão Pago Masculino",
        "cpf": "95000000002",
        "email": "aluno.cartao.pago@example.com",
        "phone": "(62) 95000-0002",
        "birth_date": date(1993, 6, 5),
        "biological_sex": BiologicalSex.MALE,
        "class_group_code": "adult-vinicius",
        "plan_code": "adult-2x-individual-monthly-credit-card",
        "payment_state": "paid_card",
    },
    {
        "kind": "student",
        "full_name": "Aluno Sem Pagamento Masculino",
        "cpf": "95000000003",
        "email": "aluno.sem.pagamento@example.com",
        "phone": "(62) 95000-0003",
        "birth_date": date(1996, 11, 20),
        "biological_sex": BiologicalSex.MALE,
        "class_group_code": "adult-layon",
        "plan_code": "adult-2x-individual-monthly-pix",
        "payment_state": "pending",
    },
    {
        "kind": "student",
        "full_name": "Aluna PIX Paga Feminina",
        "cpf": "95000000004",
        "email": "aluna.pix.paga@example.com",
        "phone": "(62) 95000-0004",
        "birth_date": date(1994, 4, 8),
        "biological_sex": BiologicalSex.FEMALE,
        "class_group_code": "women-vannessa",
        "plan_code": "adult-2x-individual-monthly-pix",
        "payment_state": "paid_pix",
    },
    {
        "kind": "student",
        "full_name": "Aluna Cartão Paga Feminina",
        "cpf": "95000000005",
        "email": "aluna.cartao.paga@example.com",
        "phone": "(62) 95000-0005",
        "birth_date": date(1991, 7, 14),
        "biological_sex": BiologicalSex.FEMALE,
        "class_group_code": "women-vannessa",
        "plan_code": "adult-2x-individual-monthly-credit-card",
        "payment_state": "paid_card",
    },
    {
        "kind": "student",
        "full_name": "Aluna Sem Pagamento Feminina",
        "cpf": "95000000006",
        "email": "aluna.sem.pagamento@example.com",
        "phone": "(62) 95000-0006",
        "birth_date": date(1997, 1, 28),
        "biological_sex": BiologicalSex.FEMALE,
        "class_group_code": "women-vannessa",
        "plan_code": "adult-2x-individual-monthly-pix",
        "payment_state": "pending",
    },
    {
        "kind": "guardian_with_dependents",
        "full_name": "Responsável PIX Pago com 1 Dependente",
        "cpf": "95000000007",
        "email": "responsavel.pix.1dep@example.com",
        "phone": "(62) 95000-0007",
        "birth_date": date(1985, 5, 22),
        "biological_sex": BiologicalSex.FEMALE,
        "class_group_code": None,
        "plan_code": "kids-juvenile-2x-family-monthly-pix",
        "payment_state": "paid_pix",
        "dependents": (
            {
                "full_name": "Dependente do Responsável 1 Dep",
                "cpf": "95000000008",
                "email": "dependente.1dep@example.com",
                "phone": "(62) 95000-0008",
                "birth_date": date(2014, 9, 10),
                "biological_sex": BiologicalSex.MALE,
                "class_group_code": "kids-andre",
                "kinship_type": "son",
            },
        ),
    },
    {
        "kind": "guardian_with_dependents",
        "full_name": "Responsável Cartão Pago com 2 Dependentes",
        "cpf": "95000000009",
        "email": "responsavel.cartao.2dep@example.com",
        "phone": "(62) 95000-0009",
        "birth_date": date(1982, 8, 30),
        "biological_sex": BiologicalSex.MALE,
        "class_group_code": None,
        "plan_code": "kids-juvenile-2x-family-monthly-credit-card",
        "payment_state": "paid_card",
        "dependents": (
            {
                "full_name": "Dependente A do Responsável 2 Dep",
                "cpf": "95000000010",
                "email": "dependente.a.2dep@example.com",
                "phone": "(62) 95000-0010",
                "birth_date": date(2013, 2, 18),
                "biological_sex": BiologicalSex.MALE,
                "class_group_code": "kids-andre",
                "kinship_type": "son",
            },
            {
                "full_name": "Dependente B do Responsável 2 Dep",
                "cpf": "95000000011",
                "email": "dependente.b.2dep@example.com",
                "phone": "(62) 95000-0011",
                "birth_date": date(2015, 12, 3),
                "biological_sex": BiologicalSex.FEMALE,
                "class_group_code": "kids-andre",
                "kinship_type": "daughter",
            },
        ),
    },
)


@transaction.atomic
def seed_test_personas(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    seed_ibjjf_age_categories()
    seed_belts()
    seed_graduation_rules()
    seed_official_instructors(password=password)
    catalog = seed_class_catalog(password=password)
    seed_teacher_payroll_configs()
    plans = seed_plans()

    created = []
    for definition in TEST_PERSONA_DEFINITIONS:
        result = _build_test_persona(
            definition=definition,
            person_types=person_types,
            categories=categories,
            class_groups=catalog["class_groups"],
            plans=plans,
            password=password,
        )
        created.append(result)
    _seed_test_payout_history()
    return created


def _build_test_persona(*, definition, person_types, categories, class_groups, plans, password):
    kind = definition["kind"]
    if kind == "student":
        return _build_test_student(definition, person_types, categories, class_groups, plans, password)
    if kind == "guardian_with_dependents":
        return _build_test_guardian(definition, person_types, categories, class_groups, plans, password)
    raise ValueError(f"Tipo de persona de teste desconhecido: {kind}")


def _seed_test_payout_history():
    today = timezone.localdate()
    current_month = today.replace(day=1)
    previous_month = _add_months(current_month, -1)
    two_months_ago = _add_months(current_month, -2)
    payout_definitions = (
        ("920.000.000-01", previous_month, "499.00", PayoutStatus.PAID, "Repasse Layon: adulto fixo e juvenil proporcional."),
        ("920.000.000-01", current_month, "499.00", PayoutStatus.PENDING, "Fechamento atual Layon aguardando aprovação."),
        ("920.000.000-02", previous_month, "400.00", PayoutStatus.PAID, "Repasse Vinicius: adulto fixo."),
        ("920.000.000-02", current_month, "400.00", PayoutStatus.PENDING, "Fechamento atual Vinicius aguardando aprovação."),
        ("920.000.000-04", two_months_ago, "0.00", PayoutStatus.CANCELED, "Andre sem repasse configurado para o mês."),
        ("920.000.000-05", two_months_ago, "0.00", PayoutStatus.CANCELED, "Vanessa sem repasse configurado para o mês."),
    )
    for cpf, reference_month, amount, status, notes in payout_definitions:
        person = Person.objects.filter(cpf=cpf).first()
        if person is None:
            continue
        try:
            bank = person.teacher_bank_account
        except TeacherBankAccount.DoesNotExist:
            continue
        paid_at = None
        sent_at = None
        if status == PayoutStatus.PAID:
            sent_at = timezone.now() - timedelta(days=7)
            paid_at = timezone.now() - timedelta(days=6)
        TeacherPayout.objects.update_or_create(
            person=person,
            reference_month=reference_month,
            kind=PayoutKind.PAYROLL,
            defaults={
                "bank_account": bank,
                "amount": Decimal(amount),
                "status": status,
                "scheduled_for": reference_month.replace(day=28),
                "approval_notes": notes,
                "sent_at": sent_at,
                "paid_at": paid_at,
            },
        )


def _add_months(reference_date, months):
    month_index = reference_date.month - 1 + months
    year = reference_date.year + month_index // 12
    month = month_index % 12 + 1
    return reference_date.replace(year=year, month=month, day=1)


def _build_test_student(definition, person_types, categories, class_groups, plans, password):
    class_group = class_groups.get(definition["class_group_code"]) if definition["class_group_code"] else None
    person = _upsert_person_with_account(
        full_name=definition["full_name"],
        cpf=definition["cpf"],
        email=definition["email"],
        phone=definition["phone"],
        birth_date=definition["birth_date"],
        biological_sex=definition["biological_sex"],
        blood_type="",
        allergies="",
        previous_injuries="",
        emergency_contact="Contato de teste",
        password=password,
        person_type=person_types[PersonTypeCode.STUDENT],
        class_category=class_group.class_category if class_group else categories["adult"],
        class_groups=[class_group] if class_group else None,
    )
    plan = plans.get(definition["plan_code"])
    _ensure_payment_state(
        person=person,
        plan=plan,
        payment_state=definition["payment_state"],
    )
    return {
        "person": person,
        "role": "Aluno",
        "payment_state": definition["payment_state"],
    }


def _build_test_guardian(definition, person_types, categories, class_groups, plans, password):
    guardian = _upsert_person_with_account(
        full_name=definition["full_name"],
        cpf=definition["cpf"],
        email=definition["email"],
        phone=definition["phone"],
        birth_date=definition["birth_date"],
        biological_sex=definition["biological_sex"],
        blood_type="",
        allergies="",
        previous_injuries="",
        emergency_contact="Contato de teste",
        password=password,
        person_type=person_types[PersonTypeCode.GUARDIAN],
        class_category=categories["kids"],
    )
    dependents = []
    for dep_definition in definition.get("dependents", ()):  # type: ignore[arg-type]
        dep_group = class_groups.get(dep_definition["class_group_code"]) if dep_definition["class_group_code"] else None
        dependent = _upsert_person_with_account(
            full_name=dep_definition["full_name"],
            cpf=dep_definition["cpf"],
            email=dep_definition["email"],
            phone=dep_definition["phone"],
            birth_date=dep_definition["birth_date"],
            biological_sex=dep_definition["biological_sex"],
            blood_type="",
            allergies="",
            previous_injuries="",
            emergency_contact=guardian.full_name,
            password=password,
            person_type=person_types[PersonTypeCode.DEPENDENT],
            class_category=dep_group.class_category if dep_group else categories["kids"],
            class_groups=[dep_group] if dep_group else None,
        )
        _upsert_relationship(
            guardian,
            dependent,
            f"Responsável de teste — {dep_definition.get('kinship_type', 'son')}.",
            kinship_type=dep_definition.get("kinship_type", ""),
        )
        dependents.append(dependent)

    plan = plans.get(definition["plan_code"])
    _ensure_payment_state(
        person=guardian,
        plan=plan,
        payment_state=definition["payment_state"],
    )
    return {
        "person": guardian,
        "role": f"Responsável ({len(dependents)} dependente(s))",
        "payment_state": definition["payment_state"],
        "dependents": dependents,
    }


def _ensure_payment_state(*, person, plan, payment_state):
    if plan is None:
        return None
    if RegistrationOrder.objects.filter(person=person).exists():
        return None

    now = timezone.now()
    if payment_state == "paid_pix":
        order = RegistrationOrder.objects.create(
            person=person,
            plan=plan,
            plan_price=plan.price,
            total=plan.price,
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.ASAAS,
            paid_at=now,
            asaas_payment_id=f"seed-pix-{person.pk}",
            notes="Pedido criado pelo seed de teste — pagamento via PIX.",
        )
        Membership.objects.create(
            person=person,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            created_via=MembershipCreatedVia.MANUAL_PAID,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            activated_at=now,
            notes="Assinatura criada pelo seed de teste — PIX.",
        )
        return order
    if payment_state == "paid_card":
        order = RegistrationOrder.objects.create(
            person=person,
            plan=plan,
            plan_price=plan.price,
            total=plan.price,
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.STRIPE,
            paid_at=now,
            stripe_payment_intent_id=f"seed-pi-{person.pk}",
            notes="Pedido criado pelo seed de teste — pagamento via cartão.",
        )
        Membership.objects.create(
            person=person,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            created_via=MembershipCreatedVia.CHECKOUT,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            activated_at=now,
            notes="Assinatura criada pelo seed de teste — cartão.",
        )
        return order
    if payment_state == "pending":
        order = RegistrationOrder.objects.create(
            person=person,
            plan=plan,
            plan_price=plan.price,
            total=plan.price,
            payment_status=PaymentStatus.PENDING,
            notes="Pedido criado pelo seed de teste — aguardando pagamento.",
        )
        return order
    raise ValueError(f"payment_state desconhecido: {payment_state}")


def _get_required_by_code(model, codes, *, command_name, dependency_command):
    ordered_codes = tuple(dict.fromkeys(codes))
    records = model.objects.filter(code__in=ordered_codes)
    by_code = {record.code: record for record in records}
    missing = [code for code in ordered_codes if code not in by_code]
    if missing:
        raise SeedDependencyError(
            f"Execute {dependency_command} antes de {command_name}. "
            f"Registros ausentes: {', '.join(missing)}"
        )
    return {code: by_code[code] for code in ordered_codes}


def _get_required_people_by_cpf(cpfs, *, command_name, dependency_command):
    ordered_cpfs = tuple(dict.fromkeys(ensure_formatted_cpf(cpf) for cpf in cpfs))
    records = Person.objects.filter(cpf__in=ordered_cpfs)
    by_cpf = {record.cpf: record for record in records}
    missing = [cpf for cpf in ordered_cpfs if cpf not in by_cpf]
    if missing:
        raise SeedDependencyError(
            f"Execute {dependency_command} antes de {command_name}. "
            f"CPFs ausentes: {', '.join(missing)}"
        )
    return {cpf: by_cpf[cpf] for cpf in ordered_cpfs}


def _upsert_person_with_account(
    *,
    full_name: str,
    cpf: str,
    email: str = "",
    phone: str = "",
    birth_date=None,
    biological_sex: str = "",
    blood_type: str = "",
    allergies: str = "",
    previous_injuries: str = "",
    emergency_contact: str = "",
    password: str,
    person_type,
    class_category=None,
    class_groups=None,
    class_group=None,
    class_schedule=None,
):
    primary_group = class_group or ((class_groups or [None])[0])
    person = _upsert_person_record(
        full_name=full_name,
        cpf=cpf,
        email=email,
        phone=phone,
        birth_date=birth_date,
        biological_sex=biological_sex,
        blood_type=blood_type,
        allergies=allergies,
        previous_injuries=previous_injuries,
        emergency_contact=emergency_contact,
        person_type=person_type,
        class_category=primary_group.class_category if primary_group else class_category,
        class_group=primary_group,
        class_schedule=class_schedule if class_group else None,
    )
    sync_person_class_enrollments(person, class_groups or ([class_group] if class_group else []))
    portal_account, _ = PortalAccount.objects.get_or_create(person=person)
    portal_account.is_active = True
    portal_account.set_password(password)
    portal_account.save()
    if person.has_type_code(*CLASS_ENROLLMENT_PERSON_TYPE_CODES):
        ensure_initial_graduation_for_beginner(person)
    return person


def _upsert_person_record(
    *,
    full_name: str,
    cpf: str,
    email: str,
    phone: str,
    birth_date,
    biological_sex: str,
    blood_type: str,
    allergies: str,
    previous_injuries: str,
    emergency_contact: str,
    person_type,
    class_category=None,
    class_group=None,
    class_schedule=None,
):
    formatted_cpf = ensure_formatted_cpf(cpf)
    person, _ = Person.objects.update_or_create(
        cpf=formatted_cpf,
        defaults={
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "birth_date": birth_date,
            "biological_sex": biological_sex,
            "blood_type": blood_type,
            "allergies": allergies,
            "previous_injuries": previous_injuries,
            "emergency_contact": emergency_contact,
            "person_type": person_type,
            "class_category": class_category,
            "class_group": class_group,
            "class_schedule": class_schedule,
            "is_active": True,
        },
    )
    return person


def _upsert_relationship(
    source_person: Person,
    target_person: Person,
    notes: str,
    kinship_type: str = "",
    kinship_other_label: str = "",
):
    PersonRelationship.objects.update_or_create(
        source_person=source_person,
        target_person=target_person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        defaults={
            "notes": notes,
            "kinship_type": kinship_type,
            "kinship_other_label": kinship_other_label,
        },
    )


def _upsert_class_group(*, definition, class_category, teacher):
    class_group, _ = ClassGroup.objects.update_or_create(
        code=definition["code"],
        defaults={
            "display_name": definition["display_name"],
            "class_category": class_category,
            "main_teacher": teacher,
            "description": definition["description"],
            "is_active": True,
            "default_capacity": 0,
        },
    )
    return class_group


def _upsert_class_schedule(
    *,
    class_group: ClassGroup,
    weekday: str,
    training_style: str,
    start_time: time,
    display_order: int,
):
    schedule, _ = ClassSchedule.objects.update_or_create(
        class_group=class_group,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
        defaults={
            "duration_minutes": settings.CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES,
            "display_order": display_order,
            "is_active": True,
        },
    )
    return schedule


# ---------------------------------------------------------------------------
# Seed de Produtos (dados reais da loja SumUp lvjiujitsu.sumupstore.com)
# ---------------------------------------------------------------------------

PRODUCT_CATEGORY_DEFINITIONS = (
    {"code": "belts", "display_name": "Faixas", "display_order": 1},
    {"code": "kimonos", "display_name": "Kimonos", "display_order": 2},
    {"code": "rashguards", "display_name": "Rash Guard", "display_order": 3},
    {"code": "patches", "display_name": "Patches", "display_order": 4},
)

BELT_COLORS_ADULT = (
    "Branca",
    "Azul",
    "Roxa",
    "Marrom",
    "Preta",
)
BELT_COLORS_KIDS = (
    "Branca",
    "Cinza",
    "Amarela",
    "Laranja",
    "Verde",
)
GI_COLORS = ("Branco", "Azul", "Preto")

SIZES_BELT_ADULT = ("A1", "A2", "A3", "A4")
SIZES_BELT_KIDS = ("M1", "M2", "M3")
SIZES_GI_ADULT = ("A1", "A2", "A3", "A4")
SIZES_GI_KIDS = ("M1", "M2", "M3")
SIZES_RASHGUARD = ("PP", "P", "M", "G", "GG")

LEGACY_SEED_PRODUCT_SKUS = {
    "gi-trad-white-fem",
    "gi-trad-black-fem",
    "gi-comp-black-red",
    "gi-comp-black-red-fem",
    "gi-comp-black-red-kids",
}


def _variant_matrix(colors, sizes, stock=2):
    return [
        {"color": color, "size": size, "stock": stock}
        for color in colors
        for size in sizes
    ]


def _rash_variants(color, stock=2):
    return [{"color": color, "size": s, "stock": stock} for s in SIZES_RASHGUARD]


PRODUCT_DEFINITIONS = (
    {
        "sku": "belt-lv",
        "display_name": "Faixa LV",
        "category": "belts",
        "unit_price": "75.00",
        "description": "Faixa oficial LV Jiu Jitsu com graduação IBJJF: adulto A1-A4 e infantil M1-M3.",
        "variants": (
            _variant_matrix(BELT_COLORS_ADULT, SIZES_BELT_ADULT)
            + _variant_matrix(BELT_COLORS_KIDS, SIZES_BELT_KIDS)
        ),
    },
    {
        "sku": "gi-lv-adulto",
        "display_name": "Kimono LV Tradicional Adulto",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono LV adulto nas cores tradicionais Branco, Azul e Preto, com tamanhos A1 a A4.",
        "variants": _variant_matrix(GI_COLORS, SIZES_GI_ADULT),
    },
    {
        "sku": "gi-lv-infantil",
        "display_name": "Kimono LV Tradicional Infantil",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono LV infantil nas cores tradicionais Branco, Azul e Preto, com tamanhos M1 a M3.",
        "variants": _variant_matrix(GI_COLORS, SIZES_GI_KIDS),
    },
    {
        "sku": "rash-lv",
        "display_name": "Rash Guard LV",
        "category": "rashguards",
        "unit_price": "150.00",
        "description": "Rash guard oficial LV Jiu Jitsu. Tamanhos PP ao GG.",
        "variants": _rash_variants("Preto"),
    },
    {
        "sku": "patch-kit-3",
        "display_name": "Kit 3 Patch's Kimono",
        "category": "patches",
        "unit_price": "45.00",
        "description": "Kit com 3 patches oficiais LV para kimono.",
        "variants": [{"color": "", "size": "", "stock": 2}],
    },
)


@transaction.atomic
def seed_product_categories():
    categories = {}
    for definition in PRODUCT_CATEGORY_DEFINITIONS:
        cat, _ = ProductCategory.objects.update_or_create(
            code=definition["code"],
            defaults={
                "display_name": definition["display_name"],
                "display_order": definition["display_order"],
                "is_active": True,
            },
        )
        categories[cat.code] = cat
    return categories


@transaction.atomic
def seed_products():
    product_category_codes = tuple(definition["code"] for definition in PRODUCT_CATEGORY_DEFINITIONS)
    categories = _get_required_by_code(
        ProductCategory,
        product_category_codes,
        command_name="seed_products",
        dependency_command="seed_product_categories",
    )
    Product.objects.filter(sku__in=LEGACY_SEED_PRODUCT_SKUS).update(is_active=False)
    ProductVariant.objects.filter(product__sku__in=LEGACY_SEED_PRODUCT_SKUS).update(
        is_active=False
    )

    products = {}
    for definition in PRODUCT_DEFINITIONS:
        product, _ = Product.objects.update_or_create(
            sku=definition["sku"],
            defaults={
                "display_name": definition["display_name"],
                "category": categories[definition["category"]],
                "unit_price": definition["unit_price"],
                "description": definition["description"],
                "is_active": True,
            },
        )
        active_variant_ids = []
        for v in definition["variants"]:
            variant, _ = ProductVariant.objects.update_or_create(
                product=product,
                color=v["color"],
                size=v["size"],
                defaults={
                    "stock_quantity": v["stock"],
                    "is_active": True,
                },
            )
            active_variant_ids.append(variant.pk)
        ProductVariant.objects.filter(product=product).exclude(
            pk__in=active_variant_ids
        ).update(is_active=False)
        products[product.sku] = product

    return {"categories": categories, "products": products}


PLAN_BASE_MONTHLY_PRICES = {
    (PlanAudience.ADULT, PlanWeeklyFrequency.TWICE, True, PlanPaymentMethod.PIX): "212.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.TWICE, True, PlanPaymentMethod.CREDIT_CARD): "220.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.TWICE, False, PlanPaymentMethod.PIX): "222.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.TWICE, False, PlanPaymentMethod.CREDIT_CARD): "230.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.FIVE_TIMES, True, PlanPaymentMethod.PIX): "237.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.FIVE_TIMES, True, PlanPaymentMethod.CREDIT_CARD): "246.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.FIVE_TIMES, False, PlanPaymentMethod.PIX): "257.00",
    (PlanAudience.ADULT, PlanWeeklyFrequency.FIVE_TIMES, False, PlanPaymentMethod.CREDIT_CARD): "267.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.TWICE, True, PlanPaymentMethod.PIX): "404.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.TWICE, True, PlanPaymentMethod.CREDIT_CARD): "436.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.TWICE, False, PlanPaymentMethod.PIX): "424.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.TWICE, False, PlanPaymentMethod.CREDIT_CARD): "458.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.FIVE_TIMES, True, PlanPaymentMethod.PIX): "454.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.FIVE_TIMES, True, PlanPaymentMethod.CREDIT_CARD): "490.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.FIVE_TIMES, False, PlanPaymentMethod.PIX): "484.00",
    (PlanAudience.KIDS_JUVENILE, PlanWeeklyFrequency.FIVE_TIMES, False, PlanPaymentMethod.CREDIT_CARD): "523.00",
}

PLAN_TEACHER_COMMISSION = {
    PlanAudience.ADULT: Decimal("0.00"),
    PlanAudience.KIDS_JUVENILE: Decimal("50.00"),
}

AUDIENCE_LABELS = {
    PlanAudience.ADULT: "Adulto",
    PlanAudience.KIDS_JUVENILE: "Kids/Juvenil",
}

PLAN_TYPE_LABELS = {True: "Família", False: "Individual"}

PAYMENT_METHOD_LABELS = {
    PlanPaymentMethod.PIX: "PIX",
    PlanPaymentMethod.CREDIT_CARD: "Cartão",
}

CYCLE_LABELS = {
    BillingCycle.MONTHLY: "Mensal",
    BillingCycle.QUARTERLY: "Trimestral",
    BillingCycle.SEMIANNUAL: "Semestral",
    BillingCycle.ANNUAL: "Anual",
}

AUDIENCE_DISPLAY_ORDER = {PlanAudience.ADULT: 0, PlanAudience.KIDS_JUVENILE: 100}
FREQUENCY_DISPLAY_ORDER = {
    PlanWeeklyFrequency.FIVE_TIMES: 0,
    PlanWeeklyFrequency.TWICE: 25,
}
PLAN_TYPE_DISPLAY_ORDER = {False: 0, True: 10}
CYCLE_DISPLAY_ORDER = {
    BillingCycle.MONTHLY: 0,
    BillingCycle.QUARTERLY: 1,
    BillingCycle.SEMIANNUAL: 2,
    BillingCycle.ANNUAL: 3,
}
PAYMENT_DISPLAY_ORDER = {PlanPaymentMethod.PIX: 0, PlanPaymentMethod.CREDIT_CARD: 5}


def _build_plan_code(audience, frequency, is_family, billing_cycle, payment_method):
    plan_type = "family" if is_family else "individual"
    method = "credit-card" if payment_method == PlanPaymentMethod.CREDIT_CARD else payment_method
    return f"{audience}-{int(frequency)}x-{plan_type}-{billing_cycle}-{method}"


def _build_plan_display_name(audience, frequency, is_family, billing_cycle, payment_method):
    return (
        f"Plano {AUDIENCE_LABELS[audience]} {int(frequency)}x "
        f"{PLAN_TYPE_LABELS[is_family]} {CYCLE_LABELS[billing_cycle]} "
        f"{PAYMENT_METHOD_LABELS[payment_method]}"
    )


def _build_plan_description(audience, frequency, is_family, billing_cycle, payment_method, monthly_price):
    method_label = PAYMENT_METHOD_LABELS[payment_method]
    cycle_label = CYCLE_LABELS[billing_cycle].lower()
    audience_label = AUDIENCE_LABELS[audience]
    plan_type_label = PLAN_TYPE_LABELS[is_family].lower()
    return (
        f"Plano {audience_label} {int(frequency)}x semanal "
        f"({plan_type_label}) {cycle_label} via {method_label}, "
        f"equivalente a R$ {monthly_price} por mês."
    )


def _build_plan_display_order(audience, frequency, is_family, billing_cycle, payment_method):
    return (
        AUDIENCE_DISPLAY_ORDER[audience]
        + FREQUENCY_DISPLAY_ORDER[frequency]
        + PLAN_TYPE_DISPLAY_ORDER[is_family]
        + CYCLE_DISPLAY_ORDER[billing_cycle]
        + PAYMENT_DISPLAY_ORDER[payment_method]
    )


def _generate_plan_definitions():
    definitions = []
    for (audience, frequency, is_family, payment_method), monthly_price_str in PLAN_BASE_MONTHLY_PRICES.items():
        monthly_price = Decimal(monthly_price_str)
        for billing_cycle, months in CYCLE_MONTHS.items():
            cycle_price = (monthly_price * months).quantize(Decimal("0.01"))
            definitions.append(
                {
                    "code": _build_plan_code(audience, frequency, is_family, billing_cycle, payment_method),
                    "display_name": _build_plan_display_name(
                        audience, frequency, is_family, billing_cycle, payment_method
                    ),
                    "audience": audience,
                    "weekly_frequency": int(frequency),
                    "billing_cycle": billing_cycle,
                    "payment_method": payment_method,
                    "price": cycle_price,
                    "monthly_reference_price": monthly_price,
                    "is_family_plan": is_family,
                    "teacher_commission_percentage": PLAN_TEACHER_COMMISSION[audience],
                    "requires_special_authorization": (
                        audience == PlanAudience.KIDS_JUVENILE
                        and frequency == PlanWeeklyFrequency.FIVE_TIMES
                    ),
                    "description": _build_plan_description(
                        audience, frequency, is_family, billing_cycle, payment_method, monthly_price
                    ),
                    "display_order": _build_plan_display_order(
                        audience, frequency, is_family, billing_cycle, payment_method
                    ),
                }
            )
    return tuple(definitions)


SUBSCRIPTION_PLAN_DEFINITIONS = _generate_plan_definitions()


@transaction.atomic
def seed_plans():
    plans = {}
    seeded_codes = []
    for definition in SUBSCRIPTION_PLAN_DEFINITIONS:
        plan, _ = SubscriptionPlan.objects.update_or_create(
            code=definition["code"],
            defaults={
                "display_name": definition["display_name"],
                "audience": definition["audience"],
                "weekly_frequency": definition["weekly_frequency"],
                "billing_cycle": definition["billing_cycle"],
                "payment_method": definition["payment_method"],
                "price": definition["price"],
                "monthly_reference_price": definition["monthly_reference_price"],
                "is_family_plan": definition["is_family_plan"],
                "teacher_commission_percentage": definition["teacher_commission_percentage"],
                "requires_special_authorization": definition["requires_special_authorization"],
                "description": definition["description"],
                "display_order": definition["display_order"],
                "is_active": True,
            },
        )
        plans[plan.code] = plan
        seeded_codes.append(plan.code)
    SubscriptionPlan.objects.exclude(code__in=seeded_codes).update(is_active=False)
    return plans
