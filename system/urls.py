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
    PayrollListView,
    PayoutApproveView,
    PayoutDispatchView,
    PayoutQueueView,
    PayoutRefuseView,
)
from system.views.admin_views import AdminHubView
from system.views.billing_admin_views import (
    ApprovalQueueView,
    CancelMembershipActionView,
    ChangeMembershipPlanActionView,
    ExemptOrderActionView,
    FinancialControlView,
    MarkOrderPaidActionView,
    PendingPaymentListView,
    RefundOrderActionView,
)
from system.views.category_views import (
    ClassCategoryCreateView,
    ClassCategoryDeleteView,
    ClassCategoryDetailView,
    ClassCategoryListView,
    ClassCategoryUpdateView,
)
from system.views.class_views import (
    ClassGroupCreateView,
    ClassGroupDeleteView,
    ClassGroupDetailView,
    ClassGroupListView,
    ClassGroupUpdateView,
    ClassScheduleCreateView,
    ClassScheduleDeleteView,
    ClassScheduleDetailView,
    ClassScheduleListView,
    ClassScheduleUpdateView,
)
from system.views.graduation_views import (
    BeltRankCreateView,
    BeltRankDeleteView,
    BeltRankDetailView,
    BeltRankListView,
    BeltRankUpdateView,
    GraduationCreateView,
    GraduationDeleteView,
    GraduationListView,
    GraduationOverviewView,
    GraduationRuleCreateView,
    GraduationRuleDeleteView,
    GraduationRuleListView,
    GraduationRuleUpdateView,
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
    PersonTypeCreateView,
    PersonTypeDeleteView,
    PersonTypeDetailView,
    PersonTypeListView,
    PersonTypeUpdateView,
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
from system.views.product_views import (
    AdminBackorderQueueView,
    CreateProductOrderView,
    ProductBackorderCreateView,
    ProductCreateView,
    ProductDeleteView,
    ProductDetailView,
    ProductListView,
    ProductStoreView,
    ProductUpdateView,
    StudentBackorderCancelView,
    StudentBackorderConfirmView,
    StudentBackorderListView,
    StudentOrderHistoryView,
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

    # Administração
    path("administracao/", AdminHubView.as_view(), name="admin-hub"),
    path("administracao/perfis/", PersonTypeListView.as_view(), name="person-type-list"),
    path("administracao/perfis/novo/", PersonTypeCreateView.as_view(), name="person-type-create"),
    path("administracao/perfis/<int:pk>/", PersonTypeDetailView.as_view(), name="person-type-detail"),
    path("administracao/perfis/<int:pk>/editar/", PersonTypeUpdateView.as_view(), name="person-type-update"),
    path("administracao/perfis/<int:pk>/excluir/", PersonTypeDeleteView.as_view(), name="person-type-delete"),

    # Turmas
    path("turmas/", ClassGroupListView.as_view(), name="class-group-list"),
    path("turmas/nova/", ClassGroupCreateView.as_view(), name="class-group-create"),
    path("turmas/<int:pk>/", ClassGroupDetailView.as_view(), name="class-group-detail"),
    path("turmas/<int:pk>/editar/", ClassGroupUpdateView.as_view(), name="class-group-update"),
    path("turmas/<int:pk>/excluir/", ClassGroupDeleteView.as_view(), name="class-group-delete"),
    path("turmas/categorias/", ClassCategoryListView.as_view(), name="class-category-list"),
    path("turmas/categorias/nova/", ClassCategoryCreateView.as_view(), name="class-category-create"),
    path("turmas/categorias/<int:pk>/", ClassCategoryDetailView.as_view(), name="class-category-detail"),
    path("turmas/categorias/<int:pk>/editar/", ClassCategoryUpdateView.as_view(), name="class-category-update"),
    path("turmas/categorias/<int:pk>/excluir/", ClassCategoryDeleteView.as_view(), name="class-category-delete"),
    path("turmas/horarios/", ClassScheduleListView.as_view(), name="class-schedule-list"),
    path("turmas/horarios/novo/", ClassScheduleCreateView.as_view(), name="class-schedule-create"),
    path("turmas/horarios/<int:pk>/", ClassScheduleDetailView.as_view(), name="class-schedule-detail"),
    path("turmas/horarios/<int:pk>/editar/", ClassScheduleUpdateView.as_view(), name="class-schedule-update"),
    path("turmas/horarios/<int:pk>/excluir/", ClassScheduleDeleteView.as_view(), name="class-schedule-delete"),

    # Financeiro
    path("financeiro/", FinancialControlView.as_view(), name="financial-control"),
    path("financeiro/aprovacoes/", ApprovalQueueView.as_view(), name="approval-queue"),
    path("financeiro/pendentes/", PendingPaymentListView.as_view(), name="pending-payments"),
    path("financeiro/folha/", PayrollListView.as_view(), name="payroll-list"),
    path("financeiro/repasses/", PayoutQueueView.as_view(), name="payout-queue"),
    path("financeiro/pedidos/<int:order_id>/isentar/", ExemptOrderActionView.as_view(), name="exempt-order"),
    path("financeiro/pedidos/<int:order_id>/marcar-pago/", MarkOrderPaidActionView.as_view(), name="mark-order-paid"),
    path("financeiro/pedidos/<int:order_id>/estornar/", RefundOrderActionView.as_view(), name="refund-order"),
    path("financeiro/assinaturas/<int:membership_id>/cancelar/", CancelMembershipActionView.as_view(), name="cancel-membership"),
    path("financeiro/assinaturas/<int:membership_id>/trocar-plano/", ChangeMembershipPlanActionView.as_view(), name="change-membership-plan"),
    path("financeiro/repasses/<int:payout_id>/aprovar/", PayoutApproveView.as_view(), name="payout-approve"),
    path("financeiro/repasses/<int:payout_id>/recusar/", PayoutRefuseView.as_view(), name="payout-refuse"),
    path("financeiro/repasses/<int:payout_id>/enviar/", PayoutDispatchView.as_view(), name="payout-dispatch"),

    # Graduação
    path("graduacao/", GraduationOverviewView.as_view(), name="graduation-overview"),
    path("graduacao/faixas/", BeltRankListView.as_view(), name="belt-rank-list"),
    path("graduacao/faixas/nova/", BeltRankCreateView.as_view(), name="belt-rank-create"),
    path("graduacao/faixas/<int:pk>/", BeltRankDetailView.as_view(), name="belt-rank-detail"),
    path("graduacao/faixas/<int:pk>/editar/", BeltRankUpdateView.as_view(), name="belt-rank-update"),
    path("graduacao/faixas/<int:pk>/excluir/", BeltRankDeleteView.as_view(), name="belt-rank-delete"),
    path("graduacao/regras/", GraduationRuleListView.as_view(), name="graduation-rule-list"),
    path("graduacao/regras/nova/", GraduationRuleCreateView.as_view(), name="graduation-rule-create"),
    path("graduacao/regras/<int:pk>/editar/", GraduationRuleUpdateView.as_view(), name="graduation-rule-update"),
    path("graduacao/regras/<int:pk>/excluir/", GraduationRuleDeleteView.as_view(), name="graduation-rule-delete"),
    path("graduacao/historico/", GraduationListView.as_view(), name="graduation-list"),
    path("graduacao/historico/novo/", GraduationCreateView.as_view(), name="graduation-create"),
    path("graduacao/historico/<int:pk>/excluir/", GraduationDeleteView.as_view(), name="graduation-delete"),

    # Materiais
    path("materiais/", ProductListView.as_view(), name="product-list"),
    path("materiais/novo/", ProductCreateView.as_view(), name="product-create"),
    path("materiais/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("materiais/<int:pk>/editar/", ProductUpdateView.as_view(), name="product-update"),
    path("materiais/<int:pk>/excluir/", ProductDeleteView.as_view(), name="product-delete"),
    path("materiais/pre-pedidos/", AdminBackorderQueueView.as_view(), name="admin-backorder-queue"),
    path("loja/", ProductStoreView.as_view(), name="product-store"),
    path("loja/comprar/", CreateProductOrderView.as_view(), name="product-order-create"),
    path("loja/pre-pedido/", ProductBackorderCreateView.as_view(), name="product-backorder-create"),
    path("meus-materiais/pre-pedidos/", StudentBackorderListView.as_view(), name="student-backorders"),
    path("meus-materiais/pre-pedidos/<int:pk>/confirmar/", StudentBackorderConfirmView.as_view(), name="student-backorder-confirm"),
    path("meus-materiais/pre-pedidos/<int:pk>/cancelar/", StudentBackorderCancelView.as_view(), name="student-backorder-cancel"),
    path("meus-materiais/pedidos/", StudentOrderHistoryView.as_view(), name="student-order-history"),

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
