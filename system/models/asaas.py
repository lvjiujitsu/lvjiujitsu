from django.conf import settings
from django.db import models

from .common import TimeStampedModel


class PixKeyType(models.TextChoices):
    CPF = "CPF", "CPF"
    CNPJ = "CNPJ", "CNPJ"
    EMAIL = "EMAIL", "E-mail"
    PHONE = "PHONE", "Telefone"
    EVP = "EVP", "Chave aleatória"


class PayoutStatus(models.TextChoices):
    PENDING = "pending", "Pendente aprovação"
    APPROVED = "approved", "Aprovado"
    SENT = "sent", "Enviado ao Asaas"
    PAID = "paid", "Pago"
    FAILED = "failed", "Falhou"
    REFUSED = "refused", "Recusado"
    CANCELED = "canceled", "Cancelado"


class PayoutKind(models.TextChoices):
    PAYROLL = "payroll", "Folha mensal"
    WITHDRAWAL = "withdrawal", "Saque parcial"


class TeacherBankAccount(TimeStampedModel):
    person = models.OneToOneField(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="teacher_bank_account",
        verbose_name="Professor",
    )
    pix_key = models.CharField("Chave PIX", max_length=140)
    pix_key_type = models.CharField(
        "Tipo da chave PIX",
        max_length=16,
        choices=PixKeyType.choices,
    )
    holder_name = models.CharField("Titular", max_length=140, blank=True, default="")
    holder_document = models.CharField("CPF/CNPJ do titular", max_length=32, blank=True, default="")
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Conta bancária de professor"
        verbose_name_plural = "Contas bancárias de professores"

    def __str__(self):
        return f"{self.person.full_name} ({self.pix_key_type})"


class TeacherPayrollConfig(TimeStampedModel):
    person = models.OneToOneField(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="payroll_config",
        verbose_name="Professor",
    )
    monthly_salary = models.DecimalField(
        "Salário mensal (R$)",
        max_digits=10,
        decimal_places=2,
    )
    payment_day = models.PositiveSmallIntegerField(
        "Dia do pagamento",
        help_text="Dia do mês (1-28) em que o pagamento é disparado automaticamente",
    )
    is_active = models.BooleanField("Ativo", default=True)
    notes = models.TextField("Observações", blank=True, default="")

    class Meta:
        verbose_name = "Folha de professor"
        verbose_name_plural = "Folha de professores"

    def __str__(self):
        return f"{self.person.full_name} — R$ {self.monthly_salary}"


class TeacherPayout(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.PROTECT,
        related_name="teacher_payouts",
        verbose_name="Professor",
    )
    bank_account = models.ForeignKey(
        TeacherBankAccount,
        on_delete=models.PROTECT,
        related_name="payouts",
        verbose_name="Conta bancária",
    )
    kind = models.CharField(
        "Tipo",
        max_length=16,
        choices=PayoutKind.choices,
        default=PayoutKind.PAYROLL,
    )
    reference_month = models.DateField(
        "Mês de referência",
        help_text="Dia 1 do mês ao qual o pagamento se refere",
    )
    amount = models.DecimalField(
        "Valor (R$)",
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
    )
    scheduled_for = models.DateField(
        "Agendado para",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_teacher_payouts",
        verbose_name="Aprovado por",
    )
    approved_at = models.DateTimeField("Aprovado em", null=True, blank=True)
    approval_notes = models.TextField("Notas da aprovação", blank=True, default="")
    sent_at = models.DateTimeField("Enviado em", null=True, blank=True)
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    failure_reason = models.TextField("Motivo da falha", blank=True, default="")
    asaas_transfer_id = models.CharField(
        "ID da Transferência Asaas",
        max_length=120,
        blank=True,
        default="",
    )

    class Meta:
        ordering = ("-reference_month", "-created_at")
        verbose_name = "Pagamento a professor"
        verbose_name_plural = "Pagamentos a professores"
        constraints = [
            models.UniqueConstraint(
                fields=("person", "reference_month", "kind"),
                condition=models.Q(kind="payroll"),
                name="unique_payroll_per_person_month",
            ),
        ]

    def __str__(self):
        return f"{self.person.full_name} — {self.reference_month} ({self.get_status_display()})"

    @property
    def is_terminal(self):
        return self.status in (
            PayoutStatus.PAID,
            PayoutStatus.FAILED,
            PayoutStatus.REFUSED,
            PayoutStatus.CANCELED,
        )


class AsaasWebhookEvent(TimeStampedModel):
    event_id = models.CharField("ID do evento Asaas", max_length=255, unique=True)
    event_type = models.CharField("Tipo do evento", max_length=128)
    order = models.ForeignKey(
        "system.RegistrationOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asaas_events",
        verbose_name="Pedido",
    )
    payout = models.ForeignKey(
        TeacherPayout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asaas_events",
        verbose_name="Pagamento",
    )
    payload = models.JSONField("Payload", default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Evento de webhook Asaas"
        verbose_name_plural = "Eventos de webhook Asaas"

    def __str__(self):
        return f"{self.event_type} — {self.event_id}"
