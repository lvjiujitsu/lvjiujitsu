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
)
from system.views.asaas_views import (
    AsaasWebhookView,
    CreateCreditCardChargeView,
    CreatePixChargeView,
)
from system.views.home_views import (
    AdminHomeView,
    AdministrativeHomeView,
    DashboardRedirectView,
    InstructorHomeView,
    StudentHomeView,
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
    path("register/materiais/", MaterialsCheckoutView.as_view(), name="register-materials-checkout"),
    path("register/finalizar/", FinalizeRegistrationView.as_view(), name="register-finalize"),

    # Pagamentos Asaas
    path("pagamentos/<int:order_id>/", PaymentMethodChoiceView.as_view(), name="payment-checkout"),
    path("pagamentos/<int:order_id>/asaas-pix/", CreatePixChargeView.as_view(), name="asaas-pix-create"),
    path("pagamentos/<int:order_id>/asaas-cartao/", CreateCreditCardChargeView.as_view(), name="asaas-card-create"),
    path("pagamentos/<int:order_id>/pagar-depois/", DeferPaymentView.as_view(), name="payment-defer"),
    path("pagamentos/pendente/", RetryPendingOrderView.as_view(), name="payment-retry"),
    path("pagamentos/sucesso/", PaymentSuccessView.as_view(), name="payment-success"),
    path("pagamentos/cancelado/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("pagamentos/webhook/asaas/", AsaasWebhookView.as_view(), name="asaas-webhook"),

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
