from datetime import date, time
from itertools import combinations

from django.db import transaction

from system.models import (
    CategoryAudience,
    ClassAudience,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PortalAccount,
    TrainingStyle,
    WeekdayCode,
)
from system.services.registration import ensure_default_person_types
from system.utils import ensure_formatted_cpf


DEFAULT_TEST_PORTAL_PASSWORD = "123456"
TEST_MATRIX_TYPE_CODE_ORDER = (
    "student",
    "guardian",
    "dependent",
    "instructor",
    "administrative-assistant",
)
DEPENDENT_SUPPORT_GUARDIAN_CPF = "90999999999"
MATRIX_PERSON_CPF_PREFIX = "910."
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
        "audience": ClassAudience.ADULT,
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
        "audience": ClassAudience.ADULT,
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
        "audience": ClassAudience.ADULT,
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
        "audience": ClassAudience.KIDS,
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
        "audience": ClassAudience.JUVENILE,
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
        "audience": ClassAudience.WOMEN,
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
    for code, display_name, audience, minimum_age, maximum_age, display_order in (
        IBJJF_AGE_CATEGORY_DEFINITIONS
    ):
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
    seed_person_types()
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
            emergency_contact="Operacao LV - (62) 98888-0000",
            password=password,
            type_codes=("instructor",),
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
    categories = seed_class_categories()
    catalog = seed_class_catalog(password=password)
    student = _upsert_person_with_account(
        full_name="Aluno Teste Individual",
        cpf="90000000001",
        email="aluno.individual@example.com",
        phone="(62) 99999-0001",
        birth_date=date(1998, 1, 10),
        blood_type="O+",
        allergies="",
        previous_injuries="",
        emergency_contact="Mae - (62) 99999-1001",
        password=password,
        type_codes=("student",),
        class_category=categories["adult"],
        class_group=catalog["class_groups"]["adult-lauro"],
    )
    return {"student": student}


@transaction.atomic
def seed_person_student_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    categories = seed_class_categories()
    catalog = seed_class_catalog(password=password)
    holder = _upsert_person_with_account(
        full_name="Aluno Titular com Dependente",
        cpf="90000000002",
        email="titular.dependente@example.com",
        phone="(62) 99999-0002",
        birth_date=date(1992, 4, 5),
        blood_type="A+",
        allergies="",
        previous_injuries="Lesao antiga no joelho esquerdo.",
        emergency_contact="Irmao - (62) 99999-1002",
        password=password,
        type_codes=("student", "guardian"),
        class_category=categories["adult"],
        class_group=catalog["class_groups"]["adult-vinicius"],
    )
    dependent = _upsert_person_with_account(
        full_name="Dependente do Aluno Titular",
        cpf="90000000003",
        email="dependente.titular@example.com",
        phone="(62) 99999-0003",
        birth_date=date(2014, 9, 18),
        blood_type="O+",
        allergies="",
        previous_injuries="",
        emergency_contact="Pai - (62) 99999-1003",
        password=password,
        type_codes=("student", "dependent"),
        class_category=categories["kids"],
        class_group=catalog["class_groups"]["kids-andre"],
    )
    _upsert_relationship(
        holder,
        dependent,
        "Titular responsavel pelo dependente.",
        kinship_type="father",
    )
    return {"holder": holder, "dependent": dependent}


@transaction.atomic
def seed_person_guardian(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    categories = seed_class_categories()
    guardian = _upsert_person_with_account(
        full_name="Responsavel Teste Individual",
        cpf="90000000004",
        email="responsavel.individual@example.com",
        phone="(62) 99999-0004",
        birth_date=date(1987, 7, 20),
        blood_type="B+",
        allergies="",
        previous_injuries="",
        emergency_contact="Conjuge - (62) 99999-1004",
        password=password,
        type_codes=("guardian",),
        class_category=categories["adult"],
    )
    return {"guardian": guardian}


@transaction.atomic
def seed_person_guardian_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    categories = seed_class_categories()
    catalog = seed_class_catalog(password=password)
    guardian = _upsert_person_with_account(
        full_name="Responsavel com Dependente",
        cpf="90000000005",
        email="responsavel.dependente@example.com",
        phone="(62) 99999-0005",
        birth_date=date(1985, 12, 12),
        blood_type="AB+",
        allergies="",
        previous_injuries="",
        emergency_contact="Avo - (62) 99999-1005",
        password=password,
        type_codes=("guardian",),
        class_category=categories["kids"],
    )
    dependent = _upsert_person_with_account(
        full_name="Aluno Dependente do Responsavel",
        cpf="90000000006",
        email="aluno.dependente@example.com",
        phone="(62) 99999-0006",
        birth_date=date(2012, 6, 1),
        blood_type="A-",
        allergies="Lactose.",
        previous_injuries="",
        emergency_contact="Responsavel - (62) 99999-1006",
        password=password,
        type_codes=("student", "dependent"),
        class_category=categories["kids"],
        class_group=catalog["class_groups"]["kids-andre"],
    )
    _upsert_relationship(
        guardian,
        dependent,
        "Responsavel financeiro do dependente.",
        kinship_type="mother",
    )
    return {"guardian": guardian, "dependent": dependent}


@transaction.atomic
def seed_person_matrix(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
    class_categories = seed_class_categories()
    seed_ibjjf_age_categories()
    dependent_support_guardian = _upsert_person_without_account(
        full_name="Responsavel Tecnico Seed",
        cpf=DEPENDENT_SUPPORT_GUARDIAN_CPF,
        email="responsavel.seed@example.com",
        phone="(62) 99999-9999",
        birth_date=date(1980, 1, 1),
        blood_type="O+",
        allergies="",
        previous_injuries="",
        emergency_contact="Operacao Seed - (62) 99999-9998",
        type_codes=("guardian",),
        class_category=class_categories["adult"],
    )

    class_category_cycle = (
        class_categories["adult"],
        class_categories["juvenile"],
        class_categories["kids"],
        class_categories["women"],
    )

    matrix_people = []
    for index, type_codes in enumerate(_build_type_code_combinations(), start=1):
        class_category = class_category_cycle[(index - 1) % len(class_category_cycle)]
        person = _upsert_person_with_account(
            full_name=_build_matrix_full_name(index, type_codes, person_types),
            cpf=_build_matrix_cpf(index),
            email=f"seed.matrix.{index:02d}@example.com",
            phone=f"(62) 99999-{index:04d}",
            birth_date=_build_matrix_birth_date(type_codes, index),
            blood_type="O+" if "dependent" in type_codes else "A+",
            allergies="",
            previous_injuries="",
            emergency_contact=f"Contato Seed {index:02d} - (62) 99988-{index:04d}",
            password=password,
            type_codes=type_codes,
            class_category=class_category,
        )
        if "dependent" in type_codes:
            _upsert_relationship(
                dependent_support_guardian,
                person,
                f"Relacionamento tecnico de seed para combinacao {', '.join(type_codes)}.",
                kinship_type="other",
                kinship_other_label="Seed tecnica",
            )
        matrix_people.append({"index": index, "type_codes": type_codes, "person": person})

    return {
        "dependent_support_guardian": dependent_support_guardian,
        "matrix_people": matrix_people,
    }


@transaction.atomic
def seed_class_matrix(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    catalog = seed_class_catalog(password=password)
    matrix_result = seed_person_matrix(password=password)
    class_groups = tuple(catalog["class_groups"].values())
    matrix_people = tuple(entry["person"] for entry in matrix_result["matrix_people"])

    instructor_assignments = []
    enrollments = []

    administrative_people = [
        person
        for person in matrix_people
        if person.has_type_code("administrative-assistant")
    ]
    student_people = [
        person
        for person in matrix_people
        if person.has_type_code("student", "dependent")
    ]

    for class_group in class_groups:
        for person in administrative_people:
            assignment = _upsert_class_instructor_assignment(
                class_group=class_group,
                person=person,
                is_primary=False,
                notes="Vinculo N:N de auxiliares administrativos para cobertura manual.",
            )
            instructor_assignments.append(assignment)
        for person in student_people:
            enrollment = _upsert_class_enrollment(
                class_group=class_group,
                person=person,
                notes="Matricula N:N de seed para cobertura manual e automatizada.",
            )
            enrollments.append(enrollment)

    return {
        "catalog": catalog,
        "matrix_people": matrix_people,
        "instructor_assignments": instructor_assignments,
        "enrollments": enrollments,
    }


def _upsert_person_with_account(
    *,
    full_name: str,
    cpf: str,
    email: str = "",
    phone: str = "",
    birth_date=None,
    blood_type: str = "",
    allergies: str = "",
    previous_injuries: str = "",
    emergency_contact: str = "",
    password: str,
    type_codes: tuple[str, ...],
    class_category=None,
    class_group=None,
    class_schedule=None,
):
    person = _upsert_person_record(
        full_name=full_name,
        cpf=cpf,
        email=email,
        phone=phone,
        birth_date=birth_date,
        blood_type=blood_type,
        allergies=allergies,
        previous_injuries=previous_injuries,
        emergency_contact=emergency_contact,
        type_codes=type_codes,
        class_category=class_category,
        class_group=class_group,
        class_schedule=class_schedule,
    )
    _upsert_portal_account(person, password)
    return person


def _upsert_person_without_account(
    *,
    full_name: str,
    cpf: str,
    email: str = "",
    phone: str = "",
    birth_date=None,
    blood_type: str = "",
    allergies: str = "",
    previous_injuries: str = "",
    emergency_contact: str = "",
    type_codes: tuple[str, ...],
    class_category=None,
    class_group=None,
    class_schedule=None,
):
    person = _upsert_person_record(
        full_name=full_name,
        cpf=cpf,
        email=email,
        phone=phone,
        birth_date=birth_date,
        blood_type=blood_type,
        allergies=allergies,
        previous_injuries=previous_injuries,
        emergency_contact=emergency_contact,
        type_codes=type_codes,
        class_category=class_category,
        class_group=class_group,
        class_schedule=class_schedule,
    )
    PortalAccount.objects.filter(person=person).delete()
    return person


def _upsert_person_record(
    *,
    full_name: str,
    cpf: str,
    email: str,
    phone: str,
    birth_date,
    blood_type: str,
    allergies: str,
    previous_injuries: str,
    emergency_contact: str,
    type_codes: tuple[str, ...],
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
            "blood_type": blood_type,
            "allergies": allergies,
            "previous_injuries": previous_injuries,
            "emergency_contact": emergency_contact,
            "class_category": class_category,
            "class_group": class_group,
            "class_schedule": class_schedule,
            "is_active": True,
        },
    )
    _assign_person_types(person, type_codes)
    return person


def _assign_person_types(person: Person, type_codes: tuple[str, ...]):
    person_types = seed_person_types()
    person.person_types.set([person_types[code] for code in type_codes])


def _upsert_portal_account(person: Person, password: str):
    portal_account, _ = PortalAccount.objects.get_or_create(person=person)
    portal_account.is_active = True
    portal_account.set_password(password)
    portal_account.save()
    return portal_account


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
            "audience": definition["audience"],
            "class_category": class_category,
            "main_teacher": teacher,
            "description": definition["description"],
            "is_public": True,
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


def _upsert_class_instructor_assignment(
    *,
    class_group: ClassGroup,
    person: Person,
    is_primary: bool,
    notes: str,
):
    assignment, _ = ClassInstructorAssignment.objects.update_or_create(
        class_group=class_group,
        person=person,
        defaults={
            "is_primary": is_primary,
            "notes": notes,
        },
    )
    return assignment


def _upsert_class_enrollment(
    *,
    class_group: ClassGroup,
    person: Person,
    notes: str,
):
    schedule = class_group.schedules.filter(is_active=True).order_by("display_order", "start_time").first()
    if person.class_group_id != class_group.id or person.class_schedule_id != getattr(schedule, "id", None):
        person.class_group = class_group
        person.class_schedule = schedule
        person.save(update_fields=("class_group", "class_schedule", "updated_at"))

    enrollment, _ = ClassEnrollment.objects.update_or_create(
        class_group=class_group,
        person=person,
        defaults={
            "status": "active",
            "notes": notes,
        },
    )
    return enrollment


def _build_type_code_combinations():
    combinations_list = []
    for size in range(1, len(TEST_MATRIX_TYPE_CODE_ORDER) + 1):
        combinations_list.extend(combinations(TEST_MATRIX_TYPE_CODE_ORDER, size))
    return combinations_list


def _build_matrix_cpf(index: int):
    return f"{MATRIX_PERSON_CPF_PREFIX.replace('.', '')}{index:08d}"


def _build_matrix_full_name(index: int, type_codes: tuple[str, ...], person_types):
    type_labels = [person_types[code].display_name for code in type_codes]
    return f"Seed Matriz {index:02d} - {' / '.join(type_labels)}"


def _build_matrix_birth_date(type_codes: tuple[str, ...], index: int):
    if "dependent" in type_codes:
        return date(2011, (index % 12) + 1, (index % 27) + 1)
    return date(1990, (index % 12) + 1, (index % 27) + 1)
