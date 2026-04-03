from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import CashSessionCloseForm, CashSessionOpenForm, PdvProductForm, PdvSaleForm, PdvSaleItemFormSet
from system.mixins import RoleRequiredMixin
from system.models import PdvProduct
from system.selectors import (
    build_cash_closure_summary,
    get_cash_movements_queryset,
    get_cash_sessions_queryset,
    get_open_cash_session_for_user,
    get_pdv_products_queryset,
    get_recent_pdv_sales_queryset,
)
from system.services.finance import close_cash_session, create_pdv_sale, open_cash_session


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)
SALE_ITEMS_PREFIX = "sale_items"


class PdvDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "system/finance/pdv_dashboard.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_session = get_open_cash_session_for_user(self.request.user)
        context["active_cash_session"] = active_session
        context["products"] = get_pdv_products_queryset()
        context["cash_sessions"] = get_cash_sessions_queryset().filter(operator_user=self.request.user)[:10]
        context["recent_sales"] = get_recent_pdv_sales_queryset().filter(cash_session__operator_user=self.request.user)[:10]
        context["recent_movements"] = get_cash_movements_queryset().filter(cash_session__operator_user=self.request.user)[:20]
        context["product_form"] = kwargs.get("product_form") or PdvProductForm(prefix="product")
        context["open_cash_form"] = kwargs.get("open_cash_form") or CashSessionOpenForm(prefix="cash_open")
        context["sale_form"] = kwargs.get("sale_form") or PdvSaleForm(prefix="sale")
        context["sale_item_formset"] = kwargs.get("sale_item_formset") or PdvSaleItemFormSet(prefix=SALE_ITEMS_PREFIX)
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        handlers = {
            "product": self._handle_product_create,
            "open_cash": self._handle_open_cash,
            "sale": self._handle_sale_create,
        }
        return handlers.get(action, self._invalid_action)()

    def _handle_product_create(self):
        form = PdvProductForm(self.request.POST, prefix="product")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(product_form=form))
        form.save()
        messages.success(self.request, "Produto PDV salvo.")
        return redirect("system:pdv-dashboard")

    def _handle_open_cash(self):
        form = CashSessionOpenForm(self.request.POST, prefix="cash_open")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(open_cash_form=form))
        try:
            open_cash_session(
                operator_user=self.request.user,
                actor_user=self.request.user,
                opening_balance=form.cleaned_data["opening_balance"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc.message)
            return self.render_to_response(self.get_context_data(open_cash_form=form))
        messages.success(self.request, "Caixa aberto para o operador atual.")
        return redirect("system:pdv-dashboard")

    def _handle_sale_create(self):
        sale_form = PdvSaleForm(self.request.POST, prefix="sale")
        item_formset = PdvSaleItemFormSet(self.request.POST, prefix=SALE_ITEMS_PREFIX)
        if not sale_form.is_valid() or not item_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(sale_form=sale_form, sale_item_formset=item_formset)
            )
        try:
            sale = create_pdv_sale(
                operator_user=self.request.user,
                payment_method=sale_form.cleaned_data["payment_method"],
                items=self._extract_items(item_formset),
                customer_student=sale_form.get_student(),
                amount_received=sale_form.cleaned_data.get("amount_received"),
                notes=sale_form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            sale_form.add_error(None, exc.message)
            return self.render_to_response(
                self.get_context_data(sale_form=sale_form, sale_item_formset=item_formset)
            )
        messages.success(
            self.request,
            f"Venda concluida. Recibo {sale.receipt_code} no valor de {sale.total_amount}.",
        )
        return redirect("system:pdv-dashboard")

    def _extract_items(self, item_formset):
        items = []
        for form in item_formset.forms:
            if not form.cleaned_data or form.cleaned_data.get("skip_form"):
                continue
            items.append(
                {
                    "product": form.cleaned_data["product"],
                    "quantity": form.cleaned_data["quantity"],
                }
            )
        return items

    def _invalid_action(self):
        messages.error(self.request, "Acao de PDV invalida.")
        return redirect("system:pdv-dashboard")


class CashClosureView(RoleRequiredMixin, TemplateView):
    template_name = "system/finance/cash_closure.html"
    required_roles = ADMIN_ROLE_CODES

    def dispatch(self, request, *args, **kwargs):
        self.cash_session = self._get_cash_session()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cash_session"] = self.cash_session
        context["closure_summary"] = build_cash_closure_summary(self.cash_session)
        context["close_form"] = kwargs.get("close_form") or CashSessionCloseForm(prefix="cash_close")
        return context

    def post(self, request, *args, **kwargs):
        form = CashSessionCloseForm(request.POST, prefix="cash_close")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(close_form=form))
        try:
            close_cash_session(
                cash_session=self.cash_session,
                closed_by=request.user,
                counted_cash_total=form.cleaned_data["counted_cash_total"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc.message)
            return self.render_to_response(self.get_context_data(close_form=form))
        self.cash_session.refresh_from_db()
        if self.cash_session.requires_manager_review:
            messages.warning(request, self.cash_session.manager_alert_reason)
        else:
            messages.success(request, "Caixa encerrado com sucesso.")
        return redirect("system:pdv-dashboard")

    def _get_cash_session(self):
        queryset = get_cash_sessions_queryset()
        return get_object_or_404(queryset, uuid=self.kwargs["uuid"])


class PdvProductToggleStatusView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(PdvProduct.objects.all(), uuid=self.kwargs["uuid"])
        product.is_active = not product.is_active
        product.save(update_fields=["is_active", "updated_at"])
        messages.success(
            request,
            "Produto PDV ativado." if product.is_active else "Produto PDV desativado.",
        )
        return redirect("system:pdv-dashboard")
