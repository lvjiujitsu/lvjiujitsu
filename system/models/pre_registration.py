from django.db import models

from .common import TimeStampedModel


def _scrub_password_fields(value):
    if isinstance(value, dict):
        return {
            key: _scrub_password_fields(child)
            for key, child in value.items()
            if "password" not in str(key).lower()
        }
    if isinstance(value, list):
        return [_scrub_password_fields(child) for child in value]
    return value


class PreRegistrationStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    AWAITING_PAYMENT = "awaiting_payment", "Aguardando pagamento"
    PAYMENT_CONFIRMED = "payment_confirmed", "Pagamento confirmado"
    FINALIZED = "finalized", "Finalizado"
    ABANDONED = "abandoned", "Abandonado"


class PreRegistration(TimeStampedModel):

    session_key = models.CharField(
        "Chave de sessão",
        max_length=40,
        blank=True,
        db_index=True,
    )

    registration_profile = models.CharField(
        "Perfil de cadastro",
        max_length=20,
        blank=True,
        db_index=True,
    )
    holder_cpf = models.CharField(
        "CPF do titular",
        max_length=14,
        blank=True,
        db_index=True,
    )
    holder_email = models.EmailField(
        "E-mail do titular",
        blank=True,
    )

    form_snapshot = models.JSONField(
        "Dados do formulário",
        default=dict,
        blank=True,
        help_text=(
            "Snapshot de todos os campos submetidos no wizard de cadastro. "
            "Usado para re-popular o formulário se o usuário voltar antes da finalização."
        ),
    )

    selected_plan = models.ForeignKey(
        "system.SubscriptionPlan",
        verbose_name="Plano selecionado",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pre_registrations",
    )
    checkout_action = models.CharField(
        "Ação de checkout",
        max_length=20,
        blank=True,
        help_text="asaas_card | pix | pay_later",
    )
    plan_order = models.OneToOneField(
        "system.RegistrationOrder",
        verbose_name="Ordem do plano",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pre_registration",
    )

    status = models.CharField(
        "Status",
        max_length=30,
        choices=PreRegistrationStatus.choices,
        default=PreRegistrationStatus.DRAFT,
        db_index=True,
    )

    finalized_person = models.OneToOneField(
        "system.Person",
        verbose_name="Pessoa finalizada",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_pre_registration",
    )

    class Meta:
        verbose_name = "Pré-cadastro"
        verbose_name_plural = "Pré-cadastros"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["holder_cpf", "status"]),
            models.Index(fields=["session_key", "status"]),
        ]

    def __str__(self) -> str:
        cpf = self.holder_cpf or "—"
        return f"PreRegistration #{self.pk} | CPF {cpf} | {self.get_status_display()}"


    @property
    def is_finalized(self) -> bool:
        return self.status == PreRegistrationStatus.FINALIZED

    @property
    def payment_confirmed(self) -> bool:
        return self.status in (
            PreRegistrationStatus.PAYMENT_CONFIRMED,
            PreRegistrationStatus.FINALIZED,
        )

    @property
    def is_awaiting_payment(self) -> bool:
        return self.status == PreRegistrationStatus.AWAITING_PAYMENT


    def mark_awaiting_payment(self) -> None:
        self.status = PreRegistrationStatus.AWAITING_PAYMENT
        self.save(update_fields=["status", "updated_at"])

    def mark_payment_confirmed(self) -> None:
        self.status = PreRegistrationStatus.PAYMENT_CONFIRMED
        self.save(update_fields=["status", "updated_at"])

    def mark_finalized(self, person) -> None:
        self.status = PreRegistrationStatus.FINALIZED
        self.finalized_person = person
        self.form_snapshot = _scrub_password_fields(self.form_snapshot or {})
        self.save(
            update_fields=[
                "status",
                "finalized_person",
                "form_snapshot",
                "updated_at",
            ]
        )

    def mark_abandoned(self) -> None:
        self.status = PreRegistrationStatus.ABANDONED
        self.form_snapshot = _scrub_password_fields(self.form_snapshot or {})
        self.save(update_fields=["status", "form_snapshot", "updated_at"])
