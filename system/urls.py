from django.urls import path

from system.views.auth_views import (
    ChromeDevtoolsProbeView,
    FinalizeRegistrationView,
    MaterialsCheckoutView,
    PortalLoginView,
    RegistrationCpfAvailabilityView,
    PortalLogoutView,
    PortalPasswordResetCompleteView,
    PortalPasswordResetConfirmView,
    PortalPasswordResetDoneView,
    PortalPasswordResetView,
    PortalRegisterView,
    ResetRegistrationView,
    ValidateCouponView,
)
from system.views.asaas_views import (
    AsaasWebhookView,
    CreateCreditCardChargeView,
    CreatePixChargeView,
)
from system.views.stripe_views import StripeWebhookView
from system.views.home_views import (
    DashboardRedirectView,
    HomeView,
)
from system.views.person_views import (
    PersonCreateView,
    PersonDeleteView,
    PersonDetailView,
    PersonListView,
    PersonUpdateView,
)
from system.views.plan_views import (
    PlanCreateView,
    PlanDeleteView,
    PlanDetailView,
    PlanListView,
    PlanUpdateView,
)
from system.views.calendar_views import (
    CalendarView,
    InstructorApproveCheckinView,
    InstructorApproveSpecialCheckinView,
    InstructorSelfCheckinView,
    InstructorSelfSpecialCheckinView,
    InstructorSpecialClassCreateView,
    InstructorSpecialClassDeleteView,
    InstructorToggleSessionView,
    StudentCheckinView,
    StudentSpecialClassCheckinView,
)
from system.views.payment_views import (
    DeferPaymentView,
    PaymentCancelView,
    PaymentMethodChoiceView,
    PaymentSuccessView,
    RetryPendingOrderView,
)


app_name = "system"


urlpatterns = [
    path(".well-known/appspecific/com.chrome.devtools.json", ChromeDevtoolsProbeView.as_view(), name="chrome-devtools-probe"),

    # Autenticação
    path("", PortalLoginView.as_view(), name="root"),
    path("login/", PortalLoginView.as_view(), name="login"),
    path("logout/", PortalLogoutView.as_view(), name="logout"),
    path("register/", PortalRegisterView.as_view(), name="register"),
    path("register/check-cpf/", RegistrationCpfAvailabilityView.as_view(), name="register-check-cpf"),
    path("cadastro/validar-cupom/", ValidateCouponView.as_view(), name="validate-coupon"),
    path("register/materiais/", MaterialsCheckoutView.as_view(), name="register-materials-checkout"),
    path("register/finalizar/", FinalizeRegistrationView.as_view(), name="register-finalize"),
    path("register/recomecar/", ResetRegistrationView.as_view(), name="register-reset"),

    # Pagamentos Asaas
    path("pagamentos/<int:order_id>/", PaymentMethodChoiceView.as_view(), name="payment-checkout"),
    path("pagamentos/<int:order_id>/asaas-pix/", CreatePixChargeView.as_view(), name="asaas-pix-create"),
    path("pagamentos/<int:order_id>/asaas-cartao/", CreateCreditCardChargeView.as_view(), name="asaas-card-create"),
    path("pagamentos/<int:order_id>/pagar-depois/", DeferPaymentView.as_view(), name="payment-defer"),
    path("pagamentos/pendente/", RetryPendingOrderView.as_view(), name="payment-retry"),
    path("pagamentos/sucesso/", PaymentSuccessView.as_view(), name="payment-success"),
    path("pagamentos/cancelado/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("pagamentos/webhook/asaas/", AsaasWebhookView.as_view(), name="asaas-webhook"),
    path("pagamentos/webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),

    # Recuperação de senha
    path("password-reset/", PortalPasswordResetView.as_view(), name="password-reset"),
    path("password-reset/done/", PortalPasswordResetDoneView.as_view(), name="password-reset-done"),
    path("reset/done/", PortalPasswordResetCompleteView.as_view(), name="password-reset-complete"),
    path("reset/<str:token>/", PortalPasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    # Redirecionamento pós-login e home unificada
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard-redirect"),
    path("home/", HomeView.as_view(), name="home"),

    # Pessoas
    path("pessoas/", PersonListView.as_view(), name="person-list"),
    path("pessoas/nova/", PersonCreateView.as_view(), name="person-create"),
    path("pessoas/<int:pk>/", PersonDetailView.as_view(), name="person-detail"),
    path("pessoas/<int:pk>/editar/", PersonUpdateView.as_view(), name="person-update"),
    path("pessoas/<int:pk>/excluir/", PersonDeleteView.as_view(), name="person-delete"),

    # Planos
    path("planos/", PlanListView.as_view(), name="plan-list"),
    path("planos/novo/", PlanCreateView.as_view(), name="plan-create"),
    path("planos/<int:pk>/", PlanDetailView.as_view(), name="plan-detail"),
    path("planos/<int:pk>/editar/", PlanUpdateView.as_view(), name="plan-update"),
    path("planos/<int:pk>/excluir/", PlanDeleteView.as_view(), name="plan-delete"),

    path("aulas/checkin/", StudentCheckinView.as_view(), name="student-checkin"),
    path("aulas/aulao/checkin/", StudentSpecialClassCheckinView.as_view(), name="student-special-checkin"),

    # Ações do professor (check-in, aulão, sessão)
    path("aulas/professor/presenca/", InstructorSelfCheckinView.as_view(), name="instructor-self-checkin"),
    path("aulas/professor/presenca-aulao/", InstructorSelfSpecialCheckinView.as_view(), name="instructor-self-special-checkin"),
    path("aulas/professor/aprovar/", InstructorApproveCheckinView.as_view(), name="instructor-approve-checkin"),
    path("aulas/professor/aprovar-aulao/", InstructorApproveSpecialCheckinView.as_view(), name="instructor-approve-special-checkin"),
    path("aulas/professor/cancelar/", InstructorToggleSessionView.as_view(), name="instructor-toggle-session"),
    path("aulas/aulao/criar/", InstructorSpecialClassCreateView.as_view(), name="instructor-special-class-create"),
    path("aulas/aulao/excluir/", InstructorSpecialClassDeleteView.as_view(), name="instructor-special-class-delete"),

    # Calendário — view única para todos os perfis
    path("cronograma/", CalendarView.as_view(), name="calendar"),
    path("cronograma/<int:year>/<int:month>/", CalendarView.as_view(), name="calendar-month"),
]
