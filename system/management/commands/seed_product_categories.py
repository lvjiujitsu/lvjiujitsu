from django.core.management.base import BaseCommand

from system.services.seeding import seed_product_categories


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as categorias base de produto."

    def handle(self, *args, **options):
        categories = seed_product_categories()
        self.stdout.write(f"Categorias de produto cadastradas: {len(categories)}")
        for category in categories.values():
            self.stdout.write(f"- {category.code}: {category.display_name}")
        self.stdout.write(self.style.SUCCESS("Seed de categorias de produto concluída."))
