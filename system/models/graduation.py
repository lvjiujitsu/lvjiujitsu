from django.db import models

from .category import CategoryAudience
from .common import TimeStampedModel


class BeltRank(TimeStampedModel):
    code = models.SlugField("Código", max_length=60, unique=True)
    display_name = models.CharField("Nome da faixa", max_length=80, unique=True)
    audience = models.CharField(
        "Público",
        max_length=16,
        choices=CategoryAudience.choices,
        default=CategoryAudience.ADULT,
    )
    color_hex = models.CharField(
        "Cor do corpo (hex)",
        max_length=7,
        default="#000000",
        help_text="Cor principal da faixa (corpo), no formato #rrggbb.",
    )
    tip_color_hex = models.CharField(
        "Cor da ponteira (hex)",
        max_length=7,
        default="#000000",
        help_text="Cor da barra final da faixa, onde os graus são exibidos. Use vermelho para faixa preta.",
    )
    stripe_color_hex = models.CharField(
        "Cor das listras (hex)",
        max_length=7,
        default="#ffffff",
        help_text="Cor das listras de grau aplicadas sobre a ponteira.",
    )
    max_grades = models.PositiveSmallIntegerField(
        "Graus máximos",
        default=4,
        help_text="Quantidade de graus disponíveis nesta faixa antes de promover para a próxima.",
    )
    min_age = models.PositiveSmallIntegerField("Idade mínima", null=True, blank=True)
    max_age = models.PositiveSmallIntegerField("Idade máxima", null=True, blank=True)
    next_rank = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="previous_ranks",
        verbose_name="Próxima faixa",
        null=True,
        blank=True,
    )
    display_order = models.PositiveIntegerField("Ordem de exibição", default=0)
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        ordering = ("display_order", "display_name")
        verbose_name = "Faixa"
        verbose_name_plural = "Faixas"

    def __str__(self):
        return self.display_name

    def get_grade_slots(self, current_grade=0):
        total = self.max_grades or 0
        if total <= 0:
            return []
        filled = max(0, min(current_grade or 0, total))
        return [index < filled for index in range(total)]


class GraduationRule(TimeStampedModel):
    belt_rank = models.ForeignKey(
        BeltRank,
        on_delete=models.CASCADE,
        related_name="graduation_rules",
        verbose_name="Faixa de origem",
    )
    from_grade = models.PositiveSmallIntegerField(
        "Grau de origem",
        default=0,
        help_text="Grau atual na faixa (0 a max_grades).",
    )
    to_grade = models.PositiveSmallIntegerField(
        "Grau de destino",
        null=True,
        blank=True,
        help_text="Grau resultante na mesma faixa. Deixe em branco para promover para a próxima faixa.",
    )
    min_months_in_current_grade = models.PositiveSmallIntegerField(
        "Meses mínimos no grau atual",
        default=0,
    )
    min_classes_required = models.PositiveIntegerField(
        "Mínimo de aulas aprovadas",
        default=0,
        help_text="Quantidade mínima de check-ins aprovados na janela considerada.",
    )
    min_classes_window_months = models.PositiveSmallIntegerField(
        "Janela de aulas (meses)",
        default=12,
        help_text="Janela de tempo para contagem de aulas. Use 0 para considerar desde a última graduação.",
    )
    notes = models.CharField("Observações", max_length=255, blank=True, default="")
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        ordering = ("belt_rank__display_order", "from_grade")
        verbose_name = "Regra de graduação"
        verbose_name_plural = "Regras de graduação"
        constraints = [
            models.UniqueConstraint(
                fields=("belt_rank", "from_grade"),
                name="unique_graduation_rule_per_belt_grade",
            ),
        ]

    def __str__(self):
        target = (
            f"grau {self.to_grade}"
            if self.to_grade is not None
            else "próxima faixa"
        )
        return f"{self.belt_rank.display_name} grau {self.from_grade} → {target}"

    @property
    def promotes_to_next_rank(self):
        return self.to_grade is None


class Graduation(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="graduations",
        verbose_name="Pessoa",
    )
    belt_rank = models.ForeignKey(
        BeltRank,
        on_delete=models.PROTECT,
        related_name="graduations",
        verbose_name="Faixa",
    )
    grade_number = models.PositiveSmallIntegerField("Grau", default=0)
    awarded_at = models.DateField("Concedida em")
    awarded_by = models.ForeignKey(
        "system.Person",
        on_delete=models.SET_NULL,
        related_name="awarded_graduations",
        verbose_name="Concedida por",
        null=True,
        blank=True,
    )
    notes = models.CharField("Observações", max_length=255, blank=True, default="")

    class Meta:
        ordering = ("-awarded_at", "-created_at")
        verbose_name = "Graduação"
        verbose_name_plural = "Graduações"

    def __str__(self):
        return (
            f"{self.person.full_name} — {self.belt_rank.display_name} grau {self.grade_number}"
        )
