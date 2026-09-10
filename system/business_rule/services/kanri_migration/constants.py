from system.business_rule.models import JiuJitsuBelt


DATA_DIRNAME = "kanri_students_migration"

MIGRATION_CPF_PREFIX = "KANRI-"

PLACEHOLDER_VALUES = {"carregando", "carregando..."}

PERSON_BELT_BY_RANK_CODE = {
    "adult-white": JiuJitsuBelt.WHITE,
    "adult-blue": JiuJitsuBelt.BLUE,
    "adult-purple": JiuJitsuBelt.PURPLE,
    "adult-brown": JiuJitsuBelt.BROWN,
    "adult-black": JiuJitsuBelt.BLACK,
    "adult-coral-redblack": JiuJitsuBelt.RED_BLACK,
    "adult-coral-redwhite": JiuJitsuBelt.RED_WHITE,
    "adult-red": JiuJitsuBelt.RED,
}
