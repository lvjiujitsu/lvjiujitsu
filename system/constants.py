class PersonTypeCode:
    STUDENT = "student"
    GUARDIAN = "guardian"
    DEPENDENT = "dependent"
    INSTRUCTOR = "instructor"
    ADMINISTRATIVE_ASSISTANT = "administrative-assistant"


class OperationalRoleCode:
    ACADEMY_MANAGER = "academy-manager"
    CLASS_ASSISTANT = "class-assistant"
    PEOPLE_SUPPORT = "people-support"
    FINANCIAL_OPERATOR = "financial-operator"
    STOCK_OPERATOR = "stock-operator"
    GRADUATION_OPERATOR = "graduation-operator"


class PortalCapability:
    ACCESS_STUDENT_AREA = "access-student-area"
    ACCESS_INSTRUCTOR_AREA = "access-instructor-area"
    SUPPORT_CLASSES = "support-classes"
    SUPPORT_PEOPLE = "support-people"
    MANAGE_ACADEMY = "manage-academy"
    MANAGE_PEOPLE = "manage-people"
    MANAGE_CLASSES = "manage-classes"
    MANAGE_FINANCE = "manage-finance"
    MANAGE_STOCK = "manage-stock"
    MANAGE_GRADUATION = "manage-graduation"
    REQUEST_MATERIAL = "request-material"


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

DEFAULT_OPERATIONAL_ROLE_DEFINITIONS = {
    OperationalRoleCode.ACADEMY_MANAGER: {
        "display_name": "Gestor da academia",
        "description": "Acesso operacional amplo aos módulos administrativos.",
        "capabilities": [
            PortalCapability.MANAGE_ACADEMY,
            PortalCapability.MANAGE_PEOPLE,
            PortalCapability.MANAGE_CLASSES,
            PortalCapability.MANAGE_FINANCE,
            PortalCapability.MANAGE_STOCK,
            PortalCapability.MANAGE_GRADUATION,
            PortalCapability.SUPPORT_PEOPLE,
            PortalCapability.SUPPORT_CLASSES,
            PortalCapability.REQUEST_MATERIAL,
        ],
    },
    OperationalRoleCode.CLASS_ASSISTANT: {
        "display_name": "Apoio de turma",
        "description": "Apoia presença, aulas e rotina de uma turma sem acesso administrativo amplo.",
        "capabilities": [
            PortalCapability.ACCESS_INSTRUCTOR_AREA,
            PortalCapability.SUPPORT_CLASSES,
            PortalCapability.REQUEST_MATERIAL,
        ],
    },
    OperationalRoleCode.PEOPLE_SUPPORT: {
        "display_name": "Apoio de pessoas",
        "description": "Consulta e cadastro operacional limitado de alunos.",
        "capabilities": [
            PortalCapability.SUPPORT_PEOPLE,
        ],
    },
    OperationalRoleCode.FINANCIAL_OPERATOR: {
        "display_name": "Operador financeiro",
        "description": "Opera rotinas financeiras sem alterar perfis globais.",
        "capabilities": [
            PortalCapability.MANAGE_FINANCE,
        ],
    },
    OperationalRoleCode.STOCK_OPERATOR: {
        "display_name": "Operador de estoque",
        "description": "Opera materiais, estoque e pedidos.",
        "capabilities": [
            PortalCapability.MANAGE_STOCK,
            PortalCapability.REQUEST_MATERIAL,
        ],
    },
    OperationalRoleCode.GRADUATION_OPERATOR: {
        "display_name": "Operador de graduação",
        "description": "Opera histórico e regras de graduação.",
        "capabilities": [
            PortalCapability.MANAGE_GRADUATION,
        ],
    },
}

PERSON_TYPE_CAPABILITIES = {
    PersonTypeCode.STUDENT: (
        PortalCapability.ACCESS_STUDENT_AREA,
        PortalCapability.REQUEST_MATERIAL,
    ),
    PersonTypeCode.GUARDIAN: (
        PortalCapability.ACCESS_STUDENT_AREA,
        PortalCapability.REQUEST_MATERIAL,
    ),
    PersonTypeCode.DEPENDENT: (
        PortalCapability.ACCESS_STUDENT_AREA,
        PortalCapability.REQUEST_MATERIAL,
    ),
    PersonTypeCode.INSTRUCTOR: (
        PortalCapability.ACCESS_INSTRUCTOR_AREA,
        PortalCapability.SUPPORT_CLASSES,
        PortalCapability.SUPPORT_PEOPLE,
        PortalCapability.REQUEST_MATERIAL,
    ),
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT: (
        PortalCapability.MANAGE_ACADEMY,
        PortalCapability.MANAGE_PEOPLE,
        PortalCapability.MANAGE_CLASSES,
        PortalCapability.MANAGE_FINANCE,
        PortalCapability.MANAGE_STOCK,
        PortalCapability.MANAGE_GRADUATION,
        PortalCapability.SUPPORT_PEOPLE,
        PortalCapability.SUPPORT_CLASSES,
        PortalCapability.REQUEST_MATERIAL,
    ),
}

TECHNICAL_ADMIN_CAPABILITIES = tuple(
    sorted(
        {
            capability
            for capabilities in PERSON_TYPE_CAPABILITIES.values()
            for capability in capabilities
        }
        | {
            PortalCapability.MANAGE_ACADEMY,
            PortalCapability.MANAGE_PEOPLE,
            PortalCapability.MANAGE_CLASSES,
            PortalCapability.MANAGE_FINANCE,
            PortalCapability.MANAGE_STOCK,
            PortalCapability.MANAGE_GRADUATION,
            PortalCapability.SUPPORT_PEOPLE,
            PortalCapability.SUPPORT_CLASSES,
            PortalCapability.ACCESS_INSTRUCTOR_AREA,
            PortalCapability.ACCESS_STUDENT_AREA,
            PortalCapability.REQUEST_MATERIAL,
        }
    )
)

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
    PersonTypeCode.GUARDIAN,
)
TECHNICAL_ADMIN_PERSON_TYPE_CODES = (
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
    PersonTypeCode.INSTRUCTOR,
    PersonTypeCode.STUDENT,
    PersonTypeCode.GUARDIAN,
)
MATERIAL_REQUEST_PERSON_TYPE_CODES = (
    *STUDENT_PORTAL_PERSON_TYPE_CODES,
    *CLASS_STAFF_PERSON_TYPE_CODES,
)
PEOPLE_SUPPORT_PERSON_TYPE_CODES = (
    PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
    PersonTypeCode.INSTRUCTOR,
)


class CheckoutAction:
    ASAAS_CARD = "asaas_card"
    PIX = "pix"
    PAY_LATER = "pay_later"
    STRIPE_CARD = "stripe_card"


class DependentFinancialMode:
    DEPENDENT_OWN = "dependent_own"
    FAMILY_EXISTING = "family_existing"
    FAMILY_UPGRADE = "family_upgrade"


class DependentCardStrategy:
    NEW_CARD = "new_card"
    SAME_CARD_MERGED = "same_card_merged"
    SAME_CARD_STAGGERED = "same_card_staggered"
