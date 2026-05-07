from django.core.management.base import BaseCommand

from system.services.seeding import seed_class_categories


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as categorias base de turma."

    def handle(self, *args, **options):
        categories = seed_class_categories()
        self.stdout.write(f"Categorias de turma cadastradas: {len(categories)}")
        for category in categories.values():
            self.stdout.write(
                f"- {category.code}: {category.display_name} | público {category.get_audience_display()}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de categorias de turma concluída."))
