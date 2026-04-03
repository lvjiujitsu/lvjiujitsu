from .attendance_views import (
    AttendanceCheckInView,
    PreCheckEligibilityAPIView,
    ProfessorDashboardView,
    ProfessorGenerateQrView,
    ProfessorManualAttendanceView,
    ProfessorSessionOpenView,
    SessionReservationCreateView,
)
from .auth_views import CpfLoginView, PasswordActionConfirmView, PasswordActionRequestView, SystemLogoutView
from .class_views import (
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
from .communications_views import CommunicationCenterView, NoticeBoardView
from .dashboard_views import AdminDashboardView, PortalDashboardRedirectView, StudentDashboardView
from .document_views import CertificateLookupView, LgpdRequestManagementView, LgpdRequestProcessView
from .emergency_views import EmergencyQuickAccessView
from .finance_views import (
    EnrollmentPauseResumeView,
    FinanceManagementView,
    InvoiceMarkOverdueView,
    InvoiceMarkPaidView,
    MyInvoicesView,
    PaymentProofReviewView,
)
from .graduation_views import GraduationPanelView, GraduationParticipationDecisionView
from .payments_views import (
    CustomerPortalStartView,
    PaymentManagementView,
    StripeWebhookView,
    SubscriptionCheckoutStartView,
)
from .pdv_views import CashClosureView, PdvDashboardView, PdvProductToggleStatusView
from .public_views import HomeView, LeadCaptureView, TrialClassRequestView
from .report_views import ReportCenterView
from .student_views import (
    GuardianRelationshipDeactivateView,
    MyProfileView,
    OnboardingConfirmStepView,
    OnboardingDependentsStepView,
    OnboardingHolderStepView,
    StudentManagementListView,
    StudentManagementToggleStatusView,
    StudentManagementUpdateView,
)


__all__ = (
    "AttendanceCheckInView",
    "AdminDashboardView",
    "CertificateLookupView",
    "ClassGroupManagementView",
    "ClassGroupUpdateView",
    "ClassSessionCloseView",
    "ClassSessionManagementView",
    "ClassSessionOpenView",
    "CommunicationCenterView",
    "CpfLoginView",
    "EmergencyQuickAccessView",
    "DisciplineManagementView",
    "DisciplineUpdateView",
    "CustomerPortalStartView",
    "EnrollmentPauseResumeView",
    "FinanceManagementView",
    "GraduationPanelView",
    "GraduationParticipationDecisionView",
    "GuardianRelationshipDeactivateView",
    "HomeView",
    "InstructorManagementView",
    "InstructorUpdateView",
    "InvoiceMarkOverdueView",
    "InvoiceMarkPaidView",
    "LeadCaptureView",
    "LgpdRequestManagementView",
    "LgpdRequestProcessView",
    "MyInvoicesView",
    "PreCheckEligibilityAPIView",
    "ProfessorDashboardView",
    "ProfessorGenerateQrView",
    "ProfessorManualAttendanceView",
    "ProfessorSessionOpenView",
    "PaymentProofReviewView",
    "NoticeBoardView",
    "MyProfileView",
    "OnboardingConfirmStepView",
    "OnboardingDependentsStepView",
    "OnboardingHolderStepView",
    "PasswordActionConfirmView",
    "PasswordActionRequestView",
    "PaymentManagementView",
    "PortalDashboardRedirectView",
    "PdvDashboardView",
    "PdvProductToggleStatusView",
    "ReportCenterView",
    "StudentManagementListView",
    "StudentDashboardView",
    "StudentManagementToggleStatusView",
    "StudentManagementUpdateView",
    "StripeWebhookView",
    "SubscriptionCheckoutStartView",
    "SystemLogoutView",
    "SessionReservationCreateView",
    "CashClosureView",
    "TrialClassRequestView",
)
