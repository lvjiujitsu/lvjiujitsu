from datetime import date, time
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassGroup,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PortalAccount,
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
from system.constants import PersonTypeCode
from system.services.registration import ensure_default_person_types, sync_person_class_enrollments
from system.utils import ensure_formatted_cpf


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
        "description": "Turma feminina com a professora Vannessa Ferro.",
        "teacher": {
            "full_name": "Vannessa Ferro",
            "cpf": "92000000005",
            "email": "vannessa.ferro@lvjiujitsu.test",
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


@transaction.atomic
def seed_class_catalog(password: str = OFFICIAL_INSTRUCTOR_PASSWORD):
    person_types = seed_person_types()
    class_categories = seed_class_categories()
    seed_ibjjf_age_categories()
    class_groups = {}
    teacher_people = {}

    for definition in OFFICIAL_CLASS_CATALOG_DEFINITIONS:
        teacher = _upsert_person_with_account(
            full_name=definition["teacher"]["full_name"],
            cpf=definition["teacher"]["cpf"],
            email=definition["teacher"]["email"],
            phone=definition["teacher"]["phone"],
            birth_date=date(1988, 1, 1),
            blood_type="O+",
            allergies="",
            previous_injuries="",
            emergency_contact="Operação LV - (62) 98888-0000",
            password=password,
            person_type=person_types[PersonTypeCode.INSTRUCTOR],
            class_category=class_categories[definition["class_category"]],
        )
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
        teacher_people[teacher.cpf] = teacher

    return {
        "class_groups": class_groups,
        "teachers": teacher_people,
        "class_categories": class_categories,
    }


@transaction.atomic
def seed_person_student(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    categories = seed_class_categories()
    catalog = seed_class_catalog(password=password)
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
    catalog = seed_class_catalog(password=password)
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
    catalog = seed_class_catalog(password=password)
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
def seed_products():
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
