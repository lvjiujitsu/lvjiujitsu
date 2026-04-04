from .auth_views import (
    PortalHomeView,
    PortalInfoView,
    PortalLoginView,
    PortalLogoutView,
    PortalRegisterView,
)
from .home_views import (
    AdminHomeView,
    AdministrativeHomeView,
    DashboardRedirectView,
    InstructorHomeView,
    RootRedirectView,
    StudentHomeView,
)
from .person_views import (
    PersonCreateView,
    PersonDeleteView,
    PersonListView,
    PersonTypeCreateView,
    PersonTypeDeleteView,
    PersonTypeListView,
    PersonTypeUpdateView,
    PersonUpdateView,
)

__all__ = [
    "AdminHomeView",
    "AdministrativeHomeView",
    "DashboardRedirectView",
    "InstructorHomeView",
    "PersonCreateView",
    "PersonDeleteView",
    "PersonListView",
    "PersonTypeCreateView",
    "PersonTypeDeleteView",
    "PersonTypeListView",
    "PersonTypeUpdateView",
    "PortalHomeView",
    "PortalInfoView",
    "PersonUpdateView",
    "PortalLoginView",
    "PortalLogoutView",
    "PortalRegisterView",
    "RootRedirectView",
    "StudentHomeView",
]
