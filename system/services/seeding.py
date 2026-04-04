from datetime import date
from itertools import combinations

from django.db import transaction

from system.models import Person, PersonRelationship, PersonRelationshipKind, PortalAccount
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


def seed_person_types():
    return ensure_default_person_types()


@transaction.atomic
def seed_person_student(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    seed_person_types()
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
    )
    return {"student": student}


@transaction.atomic
def seed_person_student_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    seed_person_types()
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
    )
    _upsert_relationship(holder, dependent, "Titular responsavel pelo dependente.")
    return {"holder": holder, "dependent": dependent}


@transaction.atomic
def seed_person_guardian(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    seed_person_types()
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
    )
    return {"guardian": guardian}


@transaction.atomic
def seed_person_guardian_with_dependent(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    seed_person_types()
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
    )
    _upsert_relationship(guardian, dependent, "Responsavel financeiro do dependente.")
    return {"guardian": guardian, "dependent": dependent}


@transaction.atomic
def seed_person_matrix(password: str = DEFAULT_TEST_PORTAL_PASSWORD):
    person_types = seed_person_types()
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
    )

    matrix_people = []
    for index, type_codes in enumerate(_build_type_code_combinations(), start=1):
        person = _upsert_person_with_account(
            full_name=_build_matrix_full_name(index, type_codes, person_types),
            cpf=_build_matrix_cpf(index),
            email=f"seed.matrix.{index:02d}@example.com",
            phone=f"(62) 99999-{index:04d}",
            birth_date=_build_matrix_birth_date(type_codes, index),
            blood_type="O+" if "dependent" in type_codes else "A+",
            allergies="",
            previous_injuries="",
            emergency_contact=f"Contato Seed {(index):02d} - (62) 99988-{index:04d}",
            password=password,
            type_codes=type_codes,
        )
        if "dependent" in type_codes:
            _upsert_relationship(
                dependent_support_guardian,
                person,
                f"Relacionamento tecnico de seed para combinacao {', '.join(type_codes)}.",
            )
        matrix_people.append({"index": index, "type_codes": type_codes, "person": person})

    return {
        "dependent_support_guardian": dependent_support_guardian,
        "matrix_people": matrix_people,
    }


def _upsert_person_with_account(
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
    password: str,
    type_codes: tuple[str, ...],
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
    )
    _upsert_portal_account(person, password)
    return person


def _upsert_person_without_account(
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


def _upsert_relationship(source_person: Person, target_person: Person, notes: str):
    PersonRelationship.objects.update_or_create(
        source_person=source_person,
        target_person=target_person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        defaults={"notes": notes},
    )


def _build_type_code_combinations():
    combinations_list = []
    for size in range(1, len(TEST_MATRIX_TYPE_CODE_ORDER) + 1):
        combinations_list.extend(combinations(TEST_MATRIX_TYPE_CODE_ORDER, size))
    return combinations_list


def _build_matrix_cpf(index: int):
    return f"910000{index:05d}"


def _build_matrix_full_name(index: int, type_codes: tuple[str, ...], person_types):
    type_labels = [person_types[code].display_name for code in type_codes]
    return f"Seed Matriz {index:02d} - {' / '.join(type_labels)}"


def _build_matrix_birth_date(type_codes: tuple[str, ...], index: int):
    if "dependent" in type_codes:
        return date(2011, (index % 12) + 1, (index % 27) + 1)
    return date(1990, (index % 12) + 1, (index % 27) + 1)
