from django.shortcuts import render


class ModalCrudMixin:
    modal_template_name = None
    modal_name = ""

    def is_modal(self):
        return self.request.GET.get("modal") == "1"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.is_modal():
            response["X-Frame-Options"] = "SAMEORIGIN"
        return response

    def get_template_names(self):
        if self.is_modal() and self.modal_template_name:
            return [self.modal_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_modal():
            context["is_modal"] = True
            context["crud_modal_name"] = self.modal_name
        return context


class ModalFormMixin(ModalCrudMixin):
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.is_modal():
            return render(
                self.request,
                "business_rule/lv/modal_done.html",
                {"crud_modal_name": self.modal_name},
            )
        return response
