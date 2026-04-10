from django.core.management.base import BaseCommand

from system.services.seeding import seed_products


class Command(BaseCommand):
    help = "Cria o catálogo base de produtos e variantes do sistema."

    def handle(self, *args, **options):
        result = seed_products()

        self.stdout.write(f"- Categorias: {len(result['categories'])}")
        self.stdout.write(f"- Produtos: {len(result['products'])}")
        self.stdout.write(self.style.SUCCESS("Seed de produtos concluída com sucesso."))
