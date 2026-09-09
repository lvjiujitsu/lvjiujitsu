from system.business_rule.models import MartialArt


MARTIAL_ART_EXPERIENCE_YES = "yes"
MARTIAL_ART_EXPERIENCE_NO = "no"
MARTIAL_ART_EXPERIENCE_CHOICES = [
    ("", "Selecione"),
    (MARTIAL_ART_EXPERIENCE_YES, "Sim"),
    (MARTIAL_ART_EXPERIENCE_NO, "Não"),
]
MARTIAL_ART_MODALITY_CHOICES = [("", "Selecione")] + list(MartialArt.choices)
