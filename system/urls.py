from django.urls import path

from system.views import (
    AdminHomeView,
    AdministrativeHomeView,
    DashboardRedirectView,
    InstructorHomeView,
    PersonCreateView,
    PersonDeleteView,
    PersonListView,
    PersonTypeCreateView,
    PersonTypeDeleteView,
    PersonTypeListView,
    PersonTypeUpdateView,
    PortalHomeView,
    PortalInfoView,
    PersonUpdateView,
    PortalLoginView,
    PortalLogoutView,
    PortalRegisterView,
    StudentHomeView,
)


app_name = "system"


urlpatterns = [
    path("", PortalHomeView.as_view(), name="root"),
    path("login/", PortalLoginView.as_view(), name="login"),
    path("register/", PortalRegisterView.as_view(), name="register"),
    path("info/", PortalInfoView.as_view(), name="info"),
    path("templates/login/login.html", PortalHomeView.as_view(), name="legacy-home"),
    path("templates/login/login-form.html", PortalLoginView.as_view(), name="legacy-login-form"),
    path("templates/login/cadastro.html", PortalRegisterView.as_view(), name="legacy-register"),
    path("templates/login/informacoes.html", PortalInfoView.as_view(), name="legacy-info"),
    path("logout/", PortalLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard-redirect"),
    path("home/admin/", AdminHomeView.as_view(), name="admin-home"),
    path("home/administrative/", AdministrativeHomeView.as_view(), name="administrative-home"),
    path("home/instructor/", InstructorHomeView.as_view(), name="instructor-home"),
    path("home/student/", StudentHomeView.as_view(), name="student-home"),
    path("people/", PersonListView.as_view(), name="person-list"),
    path("people/create/", PersonCreateView.as_view(), name="person-create"),
    path("people/<int:pk>/edit/", PersonUpdateView.as_view(), name="person-update"),
    path("people/<int:pk>/delete/", PersonDeleteView.as_view(), name="person-delete"),
    path("person-types/", PersonTypeListView.as_view(), name="person-type-list"),
    path("person-types/create/", PersonTypeCreateView.as_view(), name="person-type-create"),
    path("person-types/<int:pk>/edit/", PersonTypeUpdateView.as_view(), name="person-type-update"),
    path("person-types/<int:pk>/delete/", PersonTypeDeleteView.as_view(), name="person-type-delete"),
]
