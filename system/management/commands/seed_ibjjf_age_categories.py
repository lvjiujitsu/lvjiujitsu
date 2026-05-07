from django.core.management.base import BaseCommand

from system.services.seeding import seed_ibjjf_age_categories


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as categorias etárias IBJJF."

    def handle(self, *args, **options):
        categories = seed_ibjjf_age_categories()
        self.stdout.write(f"Categorias etárias IBJJF cadastradas: {len(categories)}")
        for category in categories.values():
            self.stdout.write(
                f"- {category.code}: {category.display_name} | público {category.get_audience_display()} | "
                f"idade {_format_age_range(category)}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de categorias etárias IBJJF concluída."))


def _format_age_range(category):
    if category.maximum_age is None:
        return f"{category.minimum_age}+"
    if category.minimum_age == category.maximum_age:
        return str(category.minimum_age)
    return f"{category.minimum_age}-{category.maximum_age}"
