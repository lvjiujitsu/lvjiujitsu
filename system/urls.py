from django.urls import path

from system.views.auth_views import (
    ChromeDevtoolsProbeView,
    PortalLoginView,
    PortalLogoutView,
    PortalPasswordResetCompleteView,
    PortalPasswordResetConfirmView,
    PortalPasswordResetDoneView,
    PortalPasswordResetView,
    PortalRegisterView,
)
from system.views.home_views import (
    AdminHomeView,
    AdministrativeHomeView,
    DashboardRedirectView,
    InstructorHomeView,
    StudentHomeView,
)


app_name = "system"


urlpatterns = [
    path(".well-known/appspecific/com.chrome.devtools.json", ChromeDevtoolsProbeView.as_view(), name="chrome-devtools-probe"),

    # Autenticação
    path("", PortalLoginView.as_view(), name="root"),
    path("login/", PortalLoginView.as_view(), name="login"),
    path("logout/", PortalLogoutView.as_view(), name="logout"),
    path("register/", PortalRegisterView.as_view(), name="register"),

    # Recuperação de senha
    path("password-reset/", PortalPasswordResetView.as_view(), name="password-reset"),
    path("password-reset/done/", PortalPasswordResetDoneView.as_view(), name="password-reset-done"),
    path("reset/done/", PortalPasswordResetCompleteView.as_view(), name="password-reset-complete"),
    path("reset/<str:token>/", PortalPasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    # Redirecionamento pós-login e homes (templates pendentes de implementação)
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard-redirect"),
    path("home/admin/", AdminHomeView.as_view(), name="admin-home"),
    path("home/administrative/", AdministrativeHomeView.as_view(), name="administrative-home"),
    path("home/instructor/", InstructorHomeView.as_view(), name="instructor-home"),
    path("home/student/", StudentHomeView.as_view(), name="student-home"),
]
