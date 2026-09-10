from django.contrib import admin

from system.business_rule.models import (
    Product,
    ProductBackorder,
    ProductCategory,
    ProductVariant,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("color", "size", "stock_quantity", "is_active")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("display_name", "code")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("display_name", "sku", "category", "unit_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("display_name", "sku")
    autocomplete_fields = ("category",)
    inlines = [ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "size", "stock_quantity", "is_active")
    list_filter = ("is_active", "product__category")
    search_fields = ("product__display_name", "color", "size")
    autocomplete_fields = ("product",)


@admin.register(ProductBackorder)
class ProductBackorderAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "person",
        "variant",
        "status",
        "created_at",
        "notified_at",
        "expires_at",
    )
    list_filter = ("status", "variant__product__category")
    search_fields = (
        "person__full_name",
        "person__cpf",
        "variant__product__display_name",
    )
    autocomplete_fields = ("person", "variant", "confirmed_order")
    readonly_fields = ("notified_at", "confirmed_at", "canceled_at", "expires_at")
