from datetime import date, time

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
from system.models.plan import SubscriptionPlan
from system.models.product import Product, ProductCategory, ProductVariant
from system.services.registration import ensure_default_person_types, sync_person_class_enrollments
from system.utils import ensure_formatted_cpf


DEFAULT_TEST_PORTAL_PASSWORD = "123456"
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
            person_type=person_types["instructor"],
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
        person_type=person_types["student"],
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
        person_type=person_types["student"],
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
        person_type=person_types["dependent"],
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
        person_type=person_types["guardian"],
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
        person_type=person_types["guardian"],
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
        person_type=person_types["dependent"],
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
        person_type=person_types["administrative-assistant"],
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
            "duration_minutes": 60,
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

BELT_COLORS = (
    "Branca", "Cinza", "Amarela", "Laranja", "Verde",
    "Azul", "Roxa", "Marrom", "Preta",
)

PRODUCT_DEFINITIONS = (
    {
        "sku": "belt-lv",
        "display_name": "Faixa LV",
        "category": "belts",
        "unit_price": "75.00",
        "description": "Faixa oficial LV Jiu Jitsu. Disponível em todas as cores de graduação.",
        "variants": [{"color": c, "size": "", "stock": 1} for c in BELT_COLORS],
    },
    {
        "sku": "gi-premium-comp",
        "display_name": "Kimono Premium Competition LV",
        "category": "kimonos",
        "unit_price": "520.00",
        "description": "Kimono premium de competição LV. Tecido leve e resistente.",
        "variants": [{"color": "Preto", "size": "A1", "stock": 1}],
    },
    {
        "sku": "gi-trad-white",
        "display_name": "Kimono Tradicional Trançado LV Branco",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono tradicional trançado branco masculino.",
        "variants": [{"color": "Branco", "size": "A2", "stock": 1}],
    },
    {
        "sku": "gi-trad-white-fem",
        "display_name": "Kimono Tradicional Trançado LV Branco Feminino",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono tradicional trançado branco feminino.",
        "variants": [{"color": "Branco", "size": "F3", "stock": 1}],
    },
    {
        "sku": "gi-trad-black-fem",
        "display_name": "Kimono Tradicional Trançado LV Preto Feminino",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono tradicional trançado preto feminino.",
        "variants": [{"color": "Preto", "size": "F3", "stock": 1}],
    },
    {
        "sku": "gi-comp-black-red",
        "display_name": "Kimono Trançado Competition LV Preto c/ Vermelho",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono trançado de competição preto com detalhes em vermelho.",
        "variants": [{"color": "Preto c/ Vermelho", "size": "A2", "stock": 1}],
    },
    {
        "sku": "gi-comp-black-red-fem",
        "display_name": "Kimono Trançado Competition LV Preto c/ Vermelho Feminino",
        "category": "kimonos",
        "unit_price": "480.00",
        "description": "Kimono trançado de competição preto com vermelho feminino.",
        "variants": [{"color": "Preto c/ Vermelho", "size": "F3", "stock": 1}],
    },
    {
        "sku": "gi-comp-black-red-kids",
        "display_name": "Kimono Trançado Competition LV Preto c/ Vermelho Infantil",
        "category": "kimonos",
        "unit_price": "450.00",
        "description": "Kimono trançado de competição infantil preto com vermelho.",
        "variants": [{"color": "Preto c/ Vermelho", "size": "M1", "stock": 1}],
    },
    {
        "sku": "rash-lv",
        "display_name": "Rash Guard LV",
        "category": "rashguards",
        "unit_price": "150.00",
        "description": "Rash guard oficial LV Jiu Jitsu.",
        "variants": [{"color": "Preto", "size": "M", "stock": 1}],
    },
    {
        "sku": "patch-kit-3",
        "display_name": "Kit 3 Patch's Kimono",
        "category": "patches",
        "unit_price": "45.00",
        "description": "Kit com 3 patches oficiais LV para kimono.",
        "variants": [{"color": "", "size": "", "stock": 1}],
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
        for v in definition["variants"]:
            ProductVariant.objects.update_or_create(
                product=product,
                color=v["color"],
                size=v["size"],
                defaults={
                    "stock_quantity": v["stock"],
                    "is_active": True,
                },
            )
        products[product.sku] = product

    return {"categories": categories, "products": products}


SUBSCRIPTION_PLAN_DEFINITIONS = (
    {
        "code": "mensal",
        "display_name": "Plano Mensal",
        "billing_cycle": "monthly",
        "price": "250.00",
        "description": "Acesso mensal a todas as turmas disponíveis.",
        "display_order": 1,
    },
    {
        "code": "mensal-irmaos",
        "display_name": "Plano Mensal Irmãos / Pais e Filhos",
        "billing_cycle": "monthly",
        "price": "225.00",
        "description": "Desconto para familiares que treinam juntos.",
        "display_order": 2,
    },
    {
        "code": "trimestral",
        "display_name": "Plano Trimestral",
        "billing_cycle": "quarterly",
        "price": "675.00",
        "description": "Pagamento trimestral com desconto sobre o mensal.",
        "display_order": 3,
    },
)


@transaction.atomic
def seed_plans():
    plans = {}
    for definition in SUBSCRIPTION_PLAN_DEFINITIONS:
        plan, _ = SubscriptionPlan.objects.update_or_create(
            code=definition["code"],
            defaults={
                "display_name": definition["display_name"],
                "billing_cycle": definition["billing_cycle"],
                "price": definition["price"],
                "description": definition["description"],
                "display_order": definition["display_order"],
                "is_active": True,
            },
        )
        plans[plan.code] = plan
    return plans
