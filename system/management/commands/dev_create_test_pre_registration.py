import os

from django.core.management.base import BaseCommand, CommandError

from system.models import SubscriptionPlan
from system.models.class_group import ClassGroup
from system.models.pre_registration import PreRegistration, PreRegistrationStatus


_CPF_BY_PROFILE = {
    "holder": "529.982.247-25",
    "guardian": "153.509.460-56",
}

_EMAIL_BY_PROFILE = {
    "holder": "teste.aluno@dev.local",
    "guardian": "teste.responsavel@dev.local",
}

_GATEWAY_BY_CHECKOUT = {
    "pix": "asaas_pix",
    "card": "asaas_card",
    "stripe": "stripe_card",
}


def _build_snapshot(profile, checkout, class_group_id, plan):
    prefix = "guardian" if profile == "guardian" else "holder"
    snapshot = {
        "registration_profile": profile,
        f"{prefix}_name": "Teste Dev Aluno" if profile == "holder" else "Teste Dev Responsável",
        f"{prefix}_cpf": _CPF_BY_PROFILE[profile],
        f"{prefix}_birthdate": "15/03/1990",
        f"{prefix}_sex": "male",
        f"{prefix}_phone": "(62) 99999-0001",
        f"{prefix}_email": _EMAIL_BY_PROFILE[profile],
        f"{prefix}_password": "Teste@1234",
        f"{prefix}_class_groups": [str(class_group_id)],
        "selected_plan": str(plan.pk),
        "selected_plans_payload": f'[{{"plan_id": {plan.pk}, "label": "Aluno Titular"}}]',
        "checkout_action": checkout,
        "plan_paid": True,
        "plan_payment": {
            "asaas_payment_id": f"dev_test_{checkout}_000",
            "total": str(plan.price),
            "items": [
                {
                    "plan_id": plan.pk,
                    "plan_name": plan.display_name,
                    "price": str(plan.price),
                    "label": "Aluno Titular",
                }
            ],
        },
    }
    if profile == "guardian":
        snapshot.update({
            "student_name": "Filho Teste Dev",
            "student_cpf": "871.464.850-07",
            "student_birthdate": "20/07/2015",
            "student_sex": "male",
            "student_class_groups": [str(class_group_id)],
        })
    return snapshot


class Command(BaseCommand):
    help = (
        "Cria um PreRegistration de teste com payment_confirmed. "
        "Somente para ambiente local/DEBUG. "
        "Configurar via DEV_TEST_CHECKOUT (pix|card|stripe) e DEV_TEST_PROFILE (holder|guardian)."
    )

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.DEBUG:
            raise CommandError(
                "Este comando só pode ser executado com DEBUG=True. "
                "Nunca rode em produção ou homologação."
            )

        checkout = (os.environ.get("DEV_TEST_CHECKOUT") or "pix").lower().strip()
        profile = (os.environ.get("DEV_TEST_PROFILE") or "holder").lower().strip()

        if checkout not in _GATEWAY_BY_CHECKOUT:
            raise CommandError(f"DEV_TEST_CHECKOUT inválido: '{checkout}'. Use: pix, card, stripe.")
        if profile not in _CPF_BY_PROFILE:
            raise CommandError(f"DEV_TEST_PROFILE inválido: '{profile}'. Use: holder, guardian.")

        gateway_code = _GATEWAY_BY_CHECKOUT[checkout]
        plan = SubscriptionPlan.objects.filter(
            gateway_code=gateway_code, is_active=True
        ).order_by("price").first()
        if plan is None:
            raise CommandError(
                f"Nenhum plano ativo com gateway_code='{gateway_code}' encontrado. "
                f"Execute seed_system_initial_subscription_plans_values primeiro."
            )

        class_group = ClassGroup.objects.filter(is_active=True).first()
        if class_group is None:
            raise CommandError(
                "Nenhuma turma ativa encontrada. "
                "Execute seed_system_initial_class_catalog primeiro."
            )

        snapshot = _build_snapshot(profile, checkout, class_group.pk, plan)
        pre_reg = PreRegistration.objects.create(
            registration_profile=profile,
            holder_cpf=_CPF_BY_PROFILE[profile],
            holder_email=_EMAIL_BY_PROFILE[profile],
            form_snapshot=snapshot,
            selected_plan=plan,
            checkout_action=checkout,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
        )

        load_url = f"/dev/carregar-pre-cadastro/{pre_reg.pk}/"
        self.stdout.write(self.style.SUCCESS(
            f"PreRegistration #{pre_reg.pk} criado com sucesso."
        ))
        self.stdout.write(f"  Perfil : {profile}")
        self.stdout.write(f"  Checkout: {checkout} (gateway: {gateway_code})")
        self.stdout.write(f"  Plano  : {plan.display_name} — R$ {plan.price}")
        self.stdout.write(f"  Turma  : {class_group}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(
            f"  Acesse no navegador: http://127.0.0.1:8000{load_url}"
        ))
        self.stdout.write("  Isso carregará a sessão e abrirá o wizard no passo de materiais.")
