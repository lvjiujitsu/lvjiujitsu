from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from system.forms import PortalAuthenticationForm


class PortalHomeView(TemplateView):
    template_name = "login/login.html"


class PortalRegisterView(TemplateView):
    template_name = "login/register.html"


class PortalInfoView(TemplateView):
    template_name = "login/info.html"


class PortalLoginView(LoginView):
    authentication_form = PortalAuthenticationForm
    template_name = "login/login_form.html"
    redirect_authenticated_user = True


class PortalLogoutView(LogoutView):
    next_page = reverse_lazy("system:root")
