from django.urls import path
from django.views.generic import RedirectView

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
from system.views.access_request_views import (
    AdministrativeAccessRequestDetailView,
    AdministrativeAccessRequestQueueView,
    AdministrativeAccessRequestSelfCancelView,
    PortalAdministrativeAccessRequestCreateView,
    PublicAdministrativeAccessRequestCreateView,
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
from system.views.admin_views import AdminHubView, AuditLogListView
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
from system.views.class_request_views import (
    ClassCatalogRequestDetailView,
    ClassCatalogRequestQueueView,
    ClassCatalogRequestSelfCancelView,
    ExistingTeacherClassCatalogRequestCreateView,
    PublicNewTeacherClassCatalogRequestCreateView,
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
    ClientProfileDeactivateView,
    ClientProfileUpdateView,
    DashboardRedirectView,
    HomeView,
)
from system.views.dependent_views import (
    DependentRegistrationView,
    DependentRemoveView,
    DependentUpdateView,
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
    VeteranPlanDecisionView,
)
from system.views.plan_views import (
    PlanCreateView,
    PlanDeleteView,
    PlanDetailView,
    PlanListView,
    PlanUpdateView,
)
from system.views.plan_change_views import PlanChangeSelectView
from system.views.calendar_views import (
    CalendarView,
    InstructorApproveCheckinView,
    InstructorApproveSpecialCheckinView,
    InstructorSelfCheckinView,
    InstructorSelfCheckinCancelView,
    InstructorSelfSpecialCheckinView,
    InstructorSelfSpecialCheckinCancelView,
    InstructorCancelClassTodayView,
    InstructorSessionSubstituteView,
    InstructorSpecialClassCreateView,
    InstructorSpecialClassDeleteView,
    InstructorToggleSessionView,
    StudentCheckinCancelView,
    StudentCheckinView,
    StudentSpecialClassCheckinCancelView,
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
    ProductCategoryCreateView,
    ProductCategoryDeleteView,
    ProductCategoryDetailView,
    ProductCategoryListView,
    ProductCategoryUpdateView,
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
    path("register/admin-access/", PublicAdministrativeAccessRequestCreateView.as_view(), name="administrative-access-public-create"),
    path("register/teacher-proposal/", PublicNewTeacherClassCatalogRequestCreateView.as_view(), name="class-catalog-request-public-teacher-create"),
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
    path("minha-mensalidade/trocar-plano/", PlanChangeSelectView.as_view(), name="plan-change-select"),
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
    path("account/profile/update/", ClientProfileUpdateView.as_view(), name="client-profile-update"),
    path("account/profile/deactivate/", ClientProfileDeactivateView.as_view(), name="client-profile-deactivate"),
    path("dependents/add/", DependentRegistrationView.as_view(), name="dependent-add"),
    path("dependents/<int:pk>/edit/", DependentUpdateView.as_view(), name="dependent-edit"),
    path("dependents/<int:pk>/remove/", DependentRemoveView.as_view(), name="dependent-remove"),
    path("requests/admin-access/create/", PortalAdministrativeAccessRequestCreateView.as_view(), name="administrative-access-request-create"),
    path("requests/admin-access/", AdministrativeAccessRequestQueueView.as_view(), name="administrative-access-request-list"),
    path("requests/admin-access/<int:pk>/", AdministrativeAccessRequestDetailView.as_view(), name="administrative-access-request-detail"),
    path("requests/admin-access/<int:pk>/cancel/", AdministrativeAccessRequestSelfCancelView.as_view(), name="administrative-access-request-self-cancel"),
    path("requests/classes/create/", ExistingTeacherClassCatalogRequestCreateView.as_view(), name="class-catalog-request-create"),
    path("requests/classes/", ClassCatalogRequestQueueView.as_view(), name="class-catalog-request-list"),
    path("requests/classes/<int:pk>/", ClassCatalogRequestDetailView.as_view(), name="class-catalog-request-detail"),
    path("requests/classes/<int:pk>/cancel/", ClassCatalogRequestSelfCancelView.as_view(), name="class-catalog-request-self-cancel"),

    # People (PRD-075: rotas canonicas em ingles, CRUD curto em modal)
    path("people/", PersonListView.as_view(), name="person-list"),
    path("people/create/", PersonCreateView.as_view(), name="person-create"),
    path("people/<int:pk>/view/", PersonDetailView.as_view(), name="person-detail"),
    path("people/<int:pk>/edit/", PersonUpdateView.as_view(), name="person-update"),
    path("people/<int:pk>/delete/", PersonDeleteView.as_view(), name="person-delete"),
    path(
        "people/<int:pk>/veteran-plan/",
        VeteranPlanDecisionView.as_view(),
        name="person-veteran-plan-decision",
    ),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-075)
    path("pessoas/", RedirectView.as_view(pattern_name="system:person-list", permanent=False)),
    path("pessoas/nova/", RedirectView.as_view(pattern_name="system:person-create", permanent=False)),
    path("pessoas/<int:pk>/", RedirectView.as_view(pattern_name="system:person-detail", permanent=False)),
    path("pessoas/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:person-update", permanent=False)),
    path("pessoas/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:person-delete", permanent=False)),

    # Plans (PRD-077: rotas canonicas em ingles, CRUD curto em modal)
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("plans/create/", PlanCreateView.as_view(), name="plan-create"),
    path("plans/<int:pk>/view/", PlanDetailView.as_view(), name="plan-detail"),
    path("plans/<int:pk>/edit/", PlanUpdateView.as_view(), name="plan-update"),
    path("plans/<int:pk>/delete/", PlanDeleteView.as_view(), name="plan-delete"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-077)
    path("planos/", RedirectView.as_view(pattern_name="system:plan-list", permanent=False)),
    path("planos/novo/", RedirectView.as_view(pattern_name="system:plan-create", permanent=False)),
    path("planos/<int:pk>/", RedirectView.as_view(pattern_name="system:plan-detail", permanent=False)),
    path("planos/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:plan-update", permanent=False)),
    path("planos/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:plan-delete", permanent=False)),

    # Administração
    path("administration/", AdminHubView.as_view(), name="admin-hub"),
    path("administration/audit/", AuditLogListView.as_view(), name="audit-log-list"),
    path("administration/person-types/", PersonTypeListView.as_view(), name="person-type-list"),
    path("administration/person-types/create/", PersonTypeCreateView.as_view(), name="person-type-create"),
    path("administration/person-types/<int:pk>/view/", PersonTypeDetailView.as_view(), name="person-type-detail"),
    path("administration/person-types/<int:pk>/edit/", PersonTypeUpdateView.as_view(), name="person-type-update"),
    path("administration/person-types/<int:pk>/delete/", PersonTypeDeleteView.as_view(), name="person-type-delete"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-078)
    path("administracao/", RedirectView.as_view(pattern_name="system:admin-hub", permanent=False)),
    path("administracao/perfis/", RedirectView.as_view(pattern_name="system:person-type-list", permanent=False)),
    path("administracao/perfis/novo/", RedirectView.as_view(pattern_name="system:person-type-create", permanent=False)),
    path("administracao/perfis/<int:pk>/", RedirectView.as_view(pattern_name="system:person-type-detail", permanent=False)),
    path("administracao/perfis/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:person-type-update", permanent=False)),
    path("administracao/perfis/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:person-type-delete", permanent=False)),

    # Classes, categories and schedules (PRD-077: rotas canonicas em ingles, CRUD curto em modal)
    path("classes/", ClassGroupListView.as_view(), name="class-group-list"),
    path("classes/create/", ClassGroupCreateView.as_view(), name="class-group-create"),
    path("classes/<int:pk>/view/", ClassGroupDetailView.as_view(), name="class-group-detail"),
    path("classes/<int:pk>/edit/", ClassGroupUpdateView.as_view(), name="class-group-update"),
    path("classes/<int:pk>/delete/", ClassGroupDeleteView.as_view(), name="class-group-delete"),
    path("classes/categories/", ClassCategoryListView.as_view(), name="class-category-list"),
    path("classes/categories/create/", ClassCategoryCreateView.as_view(), name="class-category-create"),
    path("classes/categories/<int:pk>/view/", ClassCategoryDetailView.as_view(), name="class-category-detail"),
    path("classes/categories/<int:pk>/edit/", ClassCategoryUpdateView.as_view(), name="class-category-update"),
    path("classes/categories/<int:pk>/delete/", ClassCategoryDeleteView.as_view(), name="class-category-delete"),
    path("classes/schedules/", ClassScheduleListView.as_view(), name="class-schedule-list"),
    path("classes/schedules/create/", ClassScheduleCreateView.as_view(), name="class-schedule-create"),
    path("classes/schedules/<int:pk>/view/", ClassScheduleDetailView.as_view(), name="class-schedule-detail"),
    path("classes/schedules/<int:pk>/edit/", ClassScheduleUpdateView.as_view(), name="class-schedule-update"),
    path("classes/schedules/<int:pk>/delete/", ClassScheduleDeleteView.as_view(), name="class-schedule-delete"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-077)
    path("turmas/", RedirectView.as_view(pattern_name="system:class-group-list", permanent=False)),
    path("turmas/nova/", RedirectView.as_view(pattern_name="system:class-group-create", permanent=False)),
    path("turmas/<int:pk>/", RedirectView.as_view(pattern_name="system:class-group-detail", permanent=False)),
    path("turmas/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:class-group-update", permanent=False)),
    path("turmas/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:class-group-delete", permanent=False)),
    path("turmas/categorias/", RedirectView.as_view(pattern_name="system:class-category-list", permanent=False)),
    path("turmas/categorias/nova/", RedirectView.as_view(pattern_name="system:class-category-create", permanent=False)),
    path("turmas/categorias/<int:pk>/", RedirectView.as_view(pattern_name="system:class-category-detail", permanent=False)),
    path("turmas/categorias/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:class-category-update", permanent=False)),
    path("turmas/categorias/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:class-category-delete", permanent=False)),
    path("turmas/horarios/", RedirectView.as_view(pattern_name="system:class-schedule-list", permanent=False)),
    path("turmas/horarios/novo/", RedirectView.as_view(pattern_name="system:class-schedule-create", permanent=False)),
    path("turmas/horarios/<int:pk>/", RedirectView.as_view(pattern_name="system:class-schedule-detail", permanent=False)),
    path("turmas/horarios/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:class-schedule-update", permanent=False)),
    path("turmas/horarios/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:class-schedule-delete", permanent=False)),

    # Financial (PRD-077: rotas canonicas em ingles)
    path("financial/", FinancialControlView.as_view(), name="financial-control"),
    path("financial/approvals/", ApprovalQueueView.as_view(), name="approval-queue"),
    path("financial/pending/", PendingPaymentListView.as_view(), name="pending-payments"),
    path("financial/payroll/", PayrollListView.as_view(), name="payroll-list"),
    path("financial/payouts/", PayoutQueueView.as_view(), name="payout-queue"),
    path("financial/orders/<int:order_id>/exempt/", ExemptOrderActionView.as_view(), name="exempt-order"),
    path("financial/orders/<int:order_id>/mark-paid/", MarkOrderPaidActionView.as_view(), name="mark-order-paid"),
    path("financial/orders/<int:order_id>/refund/", RefundOrderActionView.as_view(), name="refund-order"),
    path("financial/memberships/<int:membership_id>/cancel/", CancelMembershipActionView.as_view(), name="cancel-membership"),
    path("financial/memberships/<int:membership_id>/change-plan/", ChangeMembershipPlanActionView.as_view(), name="change-membership-plan"),
    path("financial/payouts/<int:payout_id>/approve/", PayoutApproveView.as_view(), name="payout-approve"),
    path("financial/payouts/<int:payout_id>/refuse/", PayoutRefuseView.as_view(), name="payout-refuse"),
    path("financial/payouts/<int:payout_id>/dispatch/", PayoutDispatchView.as_view(), name="payout-dispatch"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-077)
    path("financeiro/", RedirectView.as_view(pattern_name="system:financial-control", permanent=False)),
    path("financeiro/aprovacoes/", RedirectView.as_view(pattern_name="system:approval-queue", permanent=False)),
    path("financeiro/pendentes/", RedirectView.as_view(pattern_name="system:pending-payments", permanent=False)),
    path("financeiro/folha/", RedirectView.as_view(pattern_name="system:payroll-list", permanent=False)),
    path("financeiro/repasses/", RedirectView.as_view(pattern_name="system:payout-queue", permanent=False)),

    # Graduation (PRD-077: rotas canonicas em ingles, CRUD curto em modal)
    path("graduation/", GraduationOverviewView.as_view(), name="graduation-overview"),
    path("graduation/belt-ranks/", BeltRankListView.as_view(), name="belt-rank-list"),
    path("graduation/belt-ranks/create/", BeltRankCreateView.as_view(), name="belt-rank-create"),
    path("graduation/belt-ranks/<int:pk>/view/", BeltRankDetailView.as_view(), name="belt-rank-detail"),
    path("graduation/belt-ranks/<int:pk>/edit/", BeltRankUpdateView.as_view(), name="belt-rank-update"),
    path("graduation/belt-ranks/<int:pk>/delete/", BeltRankDeleteView.as_view(), name="belt-rank-delete"),
    path("graduation/rules/", GraduationRuleListView.as_view(), name="graduation-rule-list"),
    path("graduation/rules/create/", GraduationRuleCreateView.as_view(), name="graduation-rule-create"),
    path("graduation/rules/<int:pk>/edit/", GraduationRuleUpdateView.as_view(), name="graduation-rule-update"),
    path("graduation/rules/<int:pk>/delete/", GraduationRuleDeleteView.as_view(), name="graduation-rule-delete"),
    path("graduation/history/", GraduationListView.as_view(), name="graduation-list"),
    path("graduation/history/create/", GraduationCreateView.as_view(), name="graduation-create"),
    path("graduation/history/<int:pk>/delete/", GraduationDeleteView.as_view(), name="graduation-delete"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-077)
    path("graduacao/", RedirectView.as_view(pattern_name="system:graduation-overview", permanent=False)),
    path("graduacao/faixas/", RedirectView.as_view(pattern_name="system:belt-rank-list", permanent=False)),
    path("graduacao/faixas/nova/", RedirectView.as_view(pattern_name="system:belt-rank-create", permanent=False)),
    path("graduacao/faixas/<int:pk>/", RedirectView.as_view(pattern_name="system:belt-rank-detail", permanent=False)),
    path("graduacao/faixas/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:belt-rank-update", permanent=False)),
    path("graduacao/faixas/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:belt-rank-delete", permanent=False)),
    path("graduacao/regras/", RedirectView.as_view(pattern_name="system:graduation-rule-list", permanent=False)),
    path("graduacao/regras/nova/", RedirectView.as_view(pattern_name="system:graduation-rule-create", permanent=False)),
    path("graduacao/regras/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:graduation-rule-update", permanent=False)),
    path("graduacao/regras/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:graduation-rule-delete", permanent=False)),
    path("graduacao/historico/", RedirectView.as_view(pattern_name="system:graduation-list", permanent=False)),
    path("graduacao/historico/novo/", RedirectView.as_view(pattern_name="system:graduation-create", permanent=False)),
    path("graduacao/historico/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:graduation-delete", permanent=False)),

    # Materials, store and backorders (PRD-077: rotas canonicas em ingles, CRUD curto em modal)
    path("materials/", ProductListView.as_view(), name="product-list"),
    path("materials/create/", ProductCreateView.as_view(), name="product-create"),
    path("materials/<int:pk>/view/", ProductDetailView.as_view(), name="product-detail"),
    path("materials/<int:pk>/edit/", ProductUpdateView.as_view(), name="product-update"),
    path("materials/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    path("materials/backorders/", AdminBackorderQueueView.as_view(), name="admin-backorder-queue"),
    path("materials/categories/", ProductCategoryListView.as_view(), name="product-category-list"),
    path("materials/categories/create/", ProductCategoryCreateView.as_view(), name="product-category-create"),
    path("materials/categories/<int:pk>/view/", ProductCategoryDetailView.as_view(), name="product-category-detail"),
    path("materials/categories/<int:pk>/edit/", ProductCategoryUpdateView.as_view(), name="product-category-update"),
    path("materials/categories/<int:pk>/delete/", ProductCategoryDeleteView.as_view(), name="product-category-delete"),
    path("store/", ProductStoreView.as_view(), name="product-store"),
    path("store/buy/", CreateProductOrderView.as_view(), name="product-order-create"),
    path("store/backorder/", ProductBackorderCreateView.as_view(), name="product-backorder-create"),
    path("my-materials/backorders/", StudentBackorderListView.as_view(), name="student-backorders"),
    path("my-materials/backorders/<int:pk>/confirm/", StudentBackorderConfirmView.as_view(), name="student-backorder-confirm"),
    path("my-materials/backorders/<int:pk>/cancel/", StudentBackorderCancelView.as_view(), name="student-backorder-cancel"),
    path("my-materials/orders/", StudentOrderHistoryView.as_view(), name="student-order-history"),

    # Compatibilidade temporaria com rotas antigas em portugues (PRD-077)
    path("materiais/", RedirectView.as_view(pattern_name="system:product-list", permanent=False)),
    path("materiais/novo/", RedirectView.as_view(pattern_name="system:product-create", permanent=False)),
    path("materiais/<int:pk>/", RedirectView.as_view(pattern_name="system:product-detail", permanent=False)),
    path("materiais/<int:pk>/editar/", RedirectView.as_view(pattern_name="system:product-update", permanent=False)),
    path("materiais/<int:pk>/excluir/", RedirectView.as_view(pattern_name="system:product-delete", permanent=False)),
    path("materiais/pre-pedidos/", RedirectView.as_view(pattern_name="system:admin-backorder-queue", permanent=False)),
    path("loja/", RedirectView.as_view(pattern_name="system:product-store", permanent=False)),
    path("loja/comprar/", RedirectView.as_view(pattern_name="system:product-order-create", permanent=False)),
    path("loja/pre-pedido/", RedirectView.as_view(pattern_name="system:product-backorder-create", permanent=False)),
    path("meus-materiais/pre-pedidos/", RedirectView.as_view(pattern_name="system:student-backorders", permanent=False)),
    path("meus-materiais/pedidos/", RedirectView.as_view(pattern_name="system:student-order-history", permanent=False)),

    path("aulas/checkin/", StudentCheckinView.as_view(), name="student-checkin"),
    path("aulas/checkin/cancelar/", StudentCheckinCancelView.as_view(), name="student-checkin-cancel"),
    path("aulas/aulao/checkin/", StudentSpecialClassCheckinView.as_view(), name="student-special-checkin"),
    path("aulas/aulao/checkin/cancelar/", StudentSpecialClassCheckinCancelView.as_view(), name="student-special-checkin-cancel"),

    # Ações do professor (check-in, aulão, sessão)
    path("aulas/professor/presenca/", InstructorSelfCheckinView.as_view(), name="instructor-self-checkin"),
    path("aulas/professor/presenca/cancelar/", InstructorSelfCheckinCancelView.as_view(), name="instructor-self-checkin-cancel"),
    path("aulas/professor/substituto/", InstructorSessionSubstituteView.as_view(), name="instructor-session-substitute"),
    path("aulas/professor/aula/cancelar/", InstructorCancelClassTodayView.as_view(), name="instructor-cancel-class-today"),
    path("aulas/professor/presenca-aulao/", InstructorSelfSpecialCheckinView.as_view(), name="instructor-self-special-checkin"),
    path("aulas/professor/presenca-aulao/cancelar/", InstructorSelfSpecialCheckinCancelView.as_view(), name="instructor-self-special-checkin-cancel"),
    path("aulas/professor/aprovar/", InstructorApproveCheckinView.as_view(), name="instructor-approve-checkin"),
    path("aulas/professor/aprovar-aulao/", InstructorApproveSpecialCheckinView.as_view(), name="instructor-approve-special-checkin"),
    path("aulas/professor/cancelar/", InstructorToggleSessionView.as_view(), name="instructor-toggle-session"),
    path("aulas/aulao/criar/", InstructorSpecialClassCreateView.as_view(), name="instructor-special-class-create"),
    path("aulas/aulao/excluir/", InstructorSpecialClassDeleteView.as_view(), name="instructor-special-class-delete"),

    # Calendário — view única para todos os perfis
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("calendar/<int:year>/<int:month>/", CalendarView.as_view(), name="calendar-month"),

    # Compatibilidade temporaria com rota antiga em portugues (PRD-077)
    path("cronograma/", RedirectView.as_view(pattern_name="system:calendar", permanent=False)),
]
