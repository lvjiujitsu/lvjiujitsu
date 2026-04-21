class PersonTypeCode:
    STUDENT = "student"
    GUARDIAN = "guardian"
    DEPENDENT = "dependent"
    INSTRUCTOR = "instructor"
    ADMINISTRATIVE_ASSISTANT = "administrative-assistant"


class RegistrationProfile:
    HOLDER = "holder"
    GUARDIAN = PersonTypeCode.GUARDIAN
    OTHER = "other"


DEFAULT_PERSON_TYPE_DEFINITIONS = {
    PersonTypeCode.STUDENT: {
        "display_name": "Aluno",
        "description": "Pessoa com matrícula ativa como aluno.",
    },
    PersonTypeCode.GUARDIAN: {
        "display_name": "Responsável",
        "description": "Pessoa responsável por um aluno ou dependente.",
    },
    PersonTypeCode.DEPENDENT: {
        "display_name": "Dependente",
        "description": "Pessoa vinculada a um titular ou responsável.",
    },
    PersonTypeCode.INSTRUCTOR: {
        "display_name": "Professor",
        "description": "Pessoa vinculada ao corpo docente.",
    },
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT: {
        "display_name": "Administrativo",
        "description": "Pessoa vinculada ao apoio administrativo.",
    },
}

ADMINISTRATIVE_PERSON_TYPE_CODES = (PersonTypeCode.ADMINISTRATIVE_ASSISTANT,)
INSTRUCTOR_PERSON_TYPE_CODES = (PersonTypeCode.INSTRUCTOR,)
STUDENT_PORTAL_PERSON_TYPE_CODES = (
    PersonTypeCode.STUDENT,
    PersonTypeCode.GUARDIAN,
    PersonTypeCode.DEPENDENT,
)
CLASS_STAFF_PERSON_TYPE_CODES = (
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
    PersonTypeCode.INSTRUCTOR,
)
CLASS_ENROLLMENT_PERSON_TYPE_CODES = (
    PersonTypeCode.STUDENT,
    PersonTypeCode.DEPENDENT,
)
TECHNICAL_ADMIN_PERSON_TYPE_CODES = (
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
    PersonTypeCode.INSTRUCTOR,
    PersonTypeCode.STUDENT,
    PersonTypeCode.GUARDIAN,
)


class CheckoutAction:
    STRIPE = "stripe"
    PIX = "pix"
    PAY_LATER = "pay_later"
