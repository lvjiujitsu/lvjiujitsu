from django.urls import path

from system.views.attendance_views import (
    AttendanceCheckInView,
    PreCheckEligibilityAPIView,
    ProfessorDashboardView,
    ProfessorGenerateQrView,
    ProfessorManualAttendanceView,
    ProfessorSessionOpenView,
    SessionReservationCreateView,
)
from system.views.communications_views import CommunicationCenterView, NoticeBoardView
from system.views.document_views import CertificateLookupView, LgpdRequestManagementView, LgpdRequestProcessView
from system.views.emergency_views import EmergencyQuickAccessView
from system.views.auth_views import (
    CpfLoginView,
    PasswordActionConfirmView,
    PasswordActionRequestView,
    SystemLogoutView,
)
from system.views.class_views import (
    ClassGroupManagementView,
    ClassGroupUpdateView,
    ClassSessionCloseView,
    ClassSessionManagementView,
    ClassSessionOpenView,
    DisciplineManagementView,
    DisciplineUpdateView,
    InstructorManagementView,
    InstructorUpdateView,
)
from system.views.dashboard_views import AdminDashboardView, PortalDashboardRedirectView, StudentDashboardView
from system.views.finance_views import (
    EnrollmentPauseResumeView,
    FinanceManagementView,
    InvoiceMarkOverdueView,
    InvoiceMarkPaidView,
    MyInvoicesView,
    PaymentProofReviewView,
)
from system.views.graduation_views import GraduationPanelView, GraduationParticipationDecisionView
from system.views.payments_views import (
    CustomerPortalStartView,
    PaymentManagementView,
    StripeWebhookView,
    SubscriptionCheckoutStartView,
)
from system.views.pdv_views import CashClosureView, PdvDashboardView, PdvProductToggleStatusView
from system.views.public_views import HomeView, LeadCaptureView, TrialClassRequestView
from system.views.report_views import ReportCenterView
from system.views.student_views import (
    GuardianRelationshipDeactivateView,
    MyProfileView,
    OnboardingConfirmStepView,
    OnboardingDependentsStepView,
    OnboardingHolderStepView,
    StudentManagementListView,
    StudentManagementToggleStatusView,
    StudentManagementUpdateView,
)


app_name = "system"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("certificados/consulta/", CertificateLookupView.as_view(), name="certificate-lookup"),
    path("quero-me-cadastrar/", LeadCaptureView.as_view(), name="lead-capture"),
    path("aula-experimental/", TrialClassRequestView.as_view(), name="trial-class-request"),
    path("onboarding/", OnboardingHolderStepView.as_view(), name="onboarding-holder"),
    path("onboarding/dependentes/", OnboardingDependentsStepView.as_view(), name="onboarding-dependents"),
    path("onboarding/confirmacao/", OnboardingConfirmStepView.as_view(), name="onboarding-confirm"),
    path("auth/login/", CpfLoginView.as_view(), name="login"),
    path("auth/logout/", SystemLogoutView.as_view(), name="logout"),
    path("auth/password-reset/", PasswordActionRequestView.as_view(), name="password-reset"),
    path("auth/first-access/", PasswordActionRequestView.as_view(), {"purpose": "first_access"}, name="first-access"),
    path(
        "auth/token/<str:purpose>/<str:token>/",
        PasswordActionConfirmView.as_view(),
        name="password-action-confirm",
    ),
    path("portal/", PortalDashboardRedirectView.as_view(), name="portal-dashboard"),
    path("portal/avisos/", NoticeBoardView.as_view(), name="notice-board"),
    path("portal/comunicacoes/", CommunicationCenterView.as_view(), name="communication-center"),
    path("portal/dashboard/aluno/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("portal/dashboard/admin/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("portal/relatorios/", ReportCenterView.as_view(), name="report-center"),
    path("portal/emergencia/", EmergencyQuickAccessView.as_view(), name="emergency-quick-access"),
    path("portal/graduacao/", GraduationPanelView.as_view(), name="graduation-panel"),
    path(
        "portal/graduacao/participacoes/<uuid:uuid>/decisao/",
        GraduationParticipationDecisionView.as_view(),
        name="graduation-participation-decision",
    ),
    path("portal/meu-perfil/", MyProfileView.as_view(), name="my-profile"),
    path("portal/lgpd/", LgpdRequestManagementView.as_view(), name="lgpd-request-list"),
    path(
        "portal/lgpd/<uuid:uuid>/processar/",
        LgpdRequestProcessView.as_view(),
        name="lgpd-request-process",
    ),
    path("portal/alunos/", StudentManagementListView.as_view(), name="student-list"),
    path("portal/alunos/<uuid:uuid>/", StudentManagementUpdateView.as_view(), name="student-update"),
    path("portal/professores/", InstructorManagementView.as_view(), name="instructor-list"),
    path("portal/professores/<uuid:uuid>/", InstructorUpdateView.as_view(), name="instructor-update"),
    path("portal/modalidades/", DisciplineManagementView.as_view(), name="discipline-list"),
    path("portal/modalidades/<uuid:uuid>/", DisciplineUpdateView.as_view(), name="discipline-update"),
    path("portal/financeiro/", FinanceManagementView.as_view(), name="finance-dashboard"),
    path("portal/financeiro/minhas-faturas/", MyInvoicesView.as_view(), name="my-invoices"),
    path("portal/financeiro/pdv/", PdvDashboardView.as_view(), name="pdv-dashboard"),
    path(
        "portal/financeiro/pdv/produtos/<uuid:uuid>/toggle/",
        PdvProductToggleStatusView.as_view(),
        name="pdv-product-toggle",
    ),
    path("portal/financeiro/caixas/<uuid:uuid>/fechamento/", CashClosureView.as_view(), name="cash-closure"),
    path("portal/pagamentos/", PaymentManagementView.as_view(), name="payment-dashboard"),
    path(
        "portal/pagamentos/contratos/<uuid:uuid>/checkout/",
        SubscriptionCheckoutStartView.as_view(),
        name="subscription-checkout-start",
    ),
    path(
        "portal/pagamentos/contratos/<uuid:uuid>/portal/",
        CustomerPortalStartView.as_view(),
        name="customer-portal-start",
    ),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("portal/financeiro/faturas/<uuid:uuid>/pagar/", InvoiceMarkPaidView.as_view(), name="invoice-mark-paid"),
    path(
        "portal/financeiro/faturas/<uuid:uuid>/vencer/",
        InvoiceMarkOverdueView.as_view(),
        name="invoice-mark-overdue",
    ),
    path(
        "portal/financeiro/pausas/<uuid:uuid>/retomar/",
        EnrollmentPauseResumeView.as_view(),
        name="pause-resume",
    ),
    path(
        "portal/financeiro/comprovantes/<uuid:uuid>/revisar/",
        PaymentProofReviewView.as_view(),
        name="payment-proof-review",
    ),
    path("portal/turmas/", ClassGroupManagementView.as_view(), name="class-group-list"),
    path("portal/turmas/<uuid:uuid>/", ClassGroupUpdateView.as_view(), name="class-group-update"),
    path("portal/professor/dashboard/", ProfessorDashboardView.as_view(), name="professor-dashboard"),
    path("portal/professor/sessoes/<uuid:uuid>/abrir/", ProfessorSessionOpenView.as_view(), name="professor-session-open"),
    path("portal/professor/sessoes/<uuid:uuid>/qr/", ProfessorGenerateQrView.as_view(), name="professor-session-qr"),
    path(
        "portal/professor/sessoes/<uuid:uuid>/presenca-manual/",
        ProfessorManualAttendanceView.as_view(),
        name="professor-manual-attendance",
    ),
    path("portal/sessoes/", ClassSessionManagementView.as_view(), name="session-list"),
    path("portal/sessoes/<uuid:uuid>/abrir/", ClassSessionOpenView.as_view(), name="session-open"),
    path("portal/sessoes/<uuid:uuid>/encerrar/", ClassSessionCloseView.as_view(), name="session-close"),
    path("portal/tatame/sessoes/<uuid:uuid>/reservar/", SessionReservationCreateView.as_view(), name="session-reserve"),
    path("portal/tatame/sessoes/<uuid:uuid>/check-in/", AttendanceCheckInView.as_view(), name="attendance-check-in"),
    path("api/presenca/pre-check/<uuid:uuid>/", PreCheckEligibilityAPIView.as_view(), name="attendance-precheck"),
    path(
        "portal/alunos/<uuid:uuid>/status/",
        StudentManagementToggleStatusView.as_view(),
        name="student-toggle-status",
    ),
    path(
        "portal/vinculos/<uuid:uuid>/encerrar/",
        GuardianRelationshipDeactivateView.as_view(),
        name="guardian-link-deactivate",
    ),
]
