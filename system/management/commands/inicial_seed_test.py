from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Executa as seeds base e cria as personas de validação manual cobrindo "
        "PIX, cartão, pendente, masculino, feminino, responsável com 1 e com 2 dependentes."
    )

    def handle(self, *args, **options):
        call_command("seed_person_type", stdout=self.stdout)
        call_command("seed_class_categories", stdout=self.stdout)
        call_command("seed_ibjjf_age_categories", stdout=self.stdout)
        call_command("seed_belts", stdout=self.stdout)
        call_command("seed_graduation_rules", stdout=self.stdout)
        call_command("seed_official_instructors", stdout=self.stdout)
        call_command("seed_class_catalog", stdout=self.stdout)
        call_command("seed_teacher_payroll_configs", stdout=self.stdout)
        call_command("seed_product_categories", stdout=self.stdout)
        call_command("seed_products", stdout=self.stdout)
        call_command("seed_plans", stdout=self.stdout)
        call_command("seed_holidays", stdout=self.stdout)
        call_command("seed_test_personas", stdout=self.stdout)
        call_command("seed_person_administrative", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Seed inicial de teste concluida com sucesso."))
