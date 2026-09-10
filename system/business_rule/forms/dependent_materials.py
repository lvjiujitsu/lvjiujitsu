from system.business_rule.constants import CheckoutAction
from system.business_rule.services.registration_checkout import resolve_selected_product_items
from system.business_rule.forms.dependent_form_helpers import build_material_variant_field_name


class DependentMaterialsMixin:
    def _clean_materials(self, cleaned_data):
        selected = []
        for variant in self.material_variants:
            quantity = cleaned_data.get(build_material_variant_field_name(variant.pk)) or 0
            if quantity > 0:
                selected.append({"variant_id": variant.pk, "quantity": quantity})
        cleaned_data["selected_products_payload"] = selected
        cleaned_data["selected_product_items"] = []
        if not selected:
            cleaned_data["materials_checkout_action"] = CheckoutAction.PAY_LATER
            return
        try:
            cleaned_data["selected_product_items"] = resolve_selected_product_items(selected)
        except ValueError as error:
            self.add_error("materials_checkout_action", str(error))
            return
        if cleaned_data.get("materials_checkout_action") not in {
            CheckoutAction.PIX,
            CheckoutAction.ASAAS_CARD,
        }:
            self.add_error(
                "materials_checkout_action",
                "Escolha PIX ou cartão para comprar os materiais agora.",
            )
