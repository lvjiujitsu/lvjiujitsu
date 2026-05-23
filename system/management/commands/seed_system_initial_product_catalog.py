import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import Product, ProductCategory, ProductVariant


class Command(BaseCommand):
    help = (
        "Cria produtos e variantes a partir de static/initial_data/"
        "seed_system_initial_product_catalog.json e "
        "seed_system_initial_product_catalog_inventory.json. "
        "Depende de seed_system_initial_product_categories."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_product_catalog"))
        catalog = self._load_json("seed_system_initial_product_catalog.json")
        inventory = self._load_json("seed_system_initial_product_catalog_inventory.json")

        if not catalog:
            self.stdout.write(self.style.WARNING(
                "Nenhum produto encontrado em seed_system_initial_product_catalog.json."
            ))
            return

        self._check_categories_exist()

        category_map = {c.code: c for c in ProductCategory.objects.all()}
        inventory_map = {entry["sku"]: entry["variants"] for entry in inventory}

        products_created = 0
        products_updated = 0
        variants_created = 0
        variants_updated = 0

        with transaction.atomic():
            for entry in catalog:
                sku = entry.get("sku", "").strip()
                if not sku:
                    raise CommandError(f"Entrada inválida no JSON: 'sku' é obrigatório. Entrada: {entry}")

                category_code = entry.get("category", "").strip()
                category = category_map.get(category_code)
                if category is None:
                    raise CommandError(
                        f"Categoria '{category_code}' não encontrada para o produto '{sku}'. "
                        f"Execute seed_system_initial_product_categories antes desta seed."
                    )

                product, created = Product.objects.get_or_create(
                    sku=sku,
                    defaults=self._build_product_defaults(entry, category),
                )
                if not created:
                    self._apply_product_updates(product, entry, category)
                    product.save()

                status = "criado" if created else "atualizado"
                self.stdout.write(f"  [produto {status}] {product.display_name} (sku={sku})")
                if created:
                    products_created += 1
                else:
                    products_updated += 1

                variants = inventory_map.get(sku, [])
                for variant_entry in variants:
                    color = variant_entry.get("color", "")
                    size = variant_entry.get("size", "")
                    stock = variant_entry.get("stock", 0)

                    variant, v_created = ProductVariant.objects.get_or_create(
                        product=product,
                        color=color,
                        size=size,
                        defaults={"stock_quantity": stock},
                    )
                    if not v_created:
                        variant.stock_quantity = stock
                        variant.save(update_fields=["stock_quantity", "updated_at"])

                    v_status = "criada" if v_created else "atualizada"
                    label = f"{color} {size}".strip() or "(sem variação)"
                    self.stdout.write(f"    [variante {v_status}] {label} — estoque: {stock}")
                    if v_created:
                        variants_created += 1
                    else:
                        variants_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nProdutos: {products_created} criado(s), {products_updated} atualizado(s). "
                f"Variantes: {variants_created} criada(s), {variants_updated} atualizada(s).\n"
                f"Preços unitários aplicados a partir do JSON do catálogo."
            )
        )

    def _check_categories_exist(self) -> None:
        if not ProductCategory.objects.exists():
            raise CommandError(
                "Nenhuma categoria de produto encontrada no banco. "
                "Execute seed_system_initial_product_categories antes desta seed."
            )

    def _load_json(self, filename: str) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / filename
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _build_product_defaults(self, entry: dict, category: ProductCategory) -> dict:
        return {
            "display_name": entry["display_name"],
            "category": category,
            "unit_price": entry.get("unit_price", "0.00"),
            "description": entry.get("description", ""),
        }

    def _apply_product_updates(self, product: Product, entry: dict, category: ProductCategory) -> None:
        product.display_name = entry["display_name"]
        product.category = category
        product.unit_price = entry.get("unit_price", product.unit_price)
        product.description = entry.get("description", "")
