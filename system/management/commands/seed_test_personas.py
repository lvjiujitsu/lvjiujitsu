from django.core.management.base import BaseCommand

from system.services.seeding import seed_test_personas


class Command(BaseCommand):
    help = "Cria personas de teste cobrindo PIX/cartão/pendente, gênero e responsáveis com dependentes."

    def handle(self, *args, **options):
        results = seed_test_personas()
        self.stdout.write(f"- Personas de teste criadas: {len(results)}")
        for entry in results:
            person = entry["person"]
            self.stdout.write(
                f"  · {person.full_name} | login {person.cpf} | tipo {entry['role']} | "
                f"estado {entry['payment_state']}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de personas de teste concluída."))
