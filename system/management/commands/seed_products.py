from django.core.management.base import BaseCommand, CommandError

from system.services.seeding import SeedDependencyError, seed_products


class Command(BaseCommand):
    help = "Cria ou atualiza apenas os produtos e variantes do sistema."

    def handle(self, *args, **options):
        try:
            result = seed_products()
        except SeedDependencyError as exc:
            raise CommandError(str(exc)) from exc

        products = result["products"]
        self.stdout.write(f"Produtos cadastrados: {len(products)}")
        for product in products.values():
            variants = product.variants.filter(is_active=True)
            stock = sum(variant.stock_quantity for variant in variants)
            self.stdout.write(
                f"- {product.sku}: {product.display_name} | categoria {product.category.display_name} | "
                f"variantes {variants.count()} | estoque {stock}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de produtos concluída."))
