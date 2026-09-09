from django.contrib.auth import get_user_model
from django.views.generic import ListView, TemplateView

from system.core.audit import AuditEntry
from system.business_rule.constants import AuditModule
from system.business_rule.models import (
    BeltRank,
    ClassCategory,
    ClassGroup,
    ClassSchedule,
    Graduation,
    GraduationRule,
    Person,
    PersonType,
    Product,
    ProductBackorder,
    ProductVariant,
    RegistrationOrder,
    SubscriptionPlan,
    TeacherPayout,
)
from system.business_rule.models.membership_timeline import MembershipTimelineEvent, MembershipTimelineEventType
from system.business_rule.services.membership_timeline import build_admin_timeline
from system.business_rule.access import AdministrativeRequiredMixin


class AdminHubView(AdministrativeRequiredMixin, TemplateView):
    template_name = "business_rule/admin_modules/admin_hub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["module_cards"] = [
            {
                "title": "Pessoas",
                "description": "Cadastro, responsáveis, alunos, dependentes e equipe.",
                "url_name": "system:person-list",
                "primary_count": Person.objects.count(),
                "primary_label": "pessoas",
            },
            {
                "title": "Planos",
                "description": "Catálogo de mensalidades por público, frequência e gateway.",
                "url_name": "system:plan-list",
                "primary_count": SubscriptionPlan.objects.filter(is_active=True).count(),
                "primary_label": "planos ativos",
            },
            {
                "title": "Turmas",
                "description": "Categorias, turmas, professores e horários de aula.",
                "url_name": "system:class-group-list",
                "primary_count": ClassGroup.objects.filter(is_active=True).count(),
                "primary_label": "turmas ativas",
            },
            {
                "title": "Financeiro",
                "description": "Pedidos, pendências, aprovações e repasses de professor.",
                "url_name": "system:financial-control",
                "primary_count": RegistrationOrder.objects.count(),
                "primary_label": "pedidos",
            },
            {
                "title": "Graduação",
                "description": "Faixas, regras, histórico e elegibilidade dos alunos.",
                "url_name": "system:graduation-overview",
                "primary_count": BeltRank.objects.filter(is_active=True).count(),
                "primary_label": "faixas ativas",
            },
            {
                "title": "Materiais",
                "description": "Produtos, variantes, estoque e pré-pedidos.",
                "url_name": "system:product-list",
                "primary_count": Product.objects.filter(is_active=True).count(),
                "primary_label": "produtos ativos",
            },
            {
                "title": "Tipos de vínculo",
                "description": "Catálogo global (Aluno, Professor, Administrativo). Para dar apoio de turma ou gestão a uma pessoa, edite o cadastro em Pessoas.",
                "url_name": "system:person-type-list",
                "primary_count": PersonType.objects.filter(is_active=True).count(),
                "primary_label": "tipos ativos",
            },
            {
                "title": "Auditoria",
                "description": "Trilha de ações operacionais: cadastro, presença e financeiro.",
                "url_name": "system:audit-log-list",
                "primary_count": AuditEntry.objects.count(),
                "primary_label": "entradas registradas",
            },
            {
                "title": "Histórico de assinaturas",
                "description": "Trilha técnica de dependente, plano, pausa, cobrança e cancelamento.",
                "url_name": "system:membership-timeline-admin-list",
                "primary_count": MembershipTimelineEvent.objects.count(),
                "primary_label": "eventos registrados",
            },
        ]
        context["admin_kpis"] = [
            {"label": "Categorias de turma", "value": ClassCategory.objects.count()},
            {"label": "Horários", "value": ClassSchedule.objects.filter(is_active=True).count()},
            {"label": "Regras de graduação", "value": GraduationRule.objects.filter(is_active=True).count()},
            {"label": "Graduações registradas", "value": Graduation.objects.count()},
            {"label": "Variantes de material", "value": ProductVariant.objects.filter(is_active=True).count()},
            {"label": "Pré-pedidos", "value": ProductBackorder.objects.count()},
            {"label": "Repasses", "value": TeacherPayout.objects.count()},
            {"label": "Usuários técnicos", "value": get_user_model().objects.count()},
        ]
        return context


class AuditLogListView(AdministrativeRequiredMixin, ListView):
    model = AuditEntry
    template_name = "business_rule/audit/audit_log_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditEntry.objects.all()
        module = self.request.GET.get("module") or ""
        if module:
            queryset = queryset.filter(module=module)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["module_filter"] = self.request.GET.get("module") or ""
        context["module_choices"] = AuditModule.choices
        return context


class MembershipTimelineAdminListView(AdministrativeRequiredMixin, TemplateView):
    template_name = "business_rule/audit/membership_timeline_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person_search = (self.request.GET.get("person") or "").strip()
        event_type = self.request.GET.get("event_type") or ""

        person = None
        if person_search:
            person = (
                Person.objects.filter(full_name__icontains=person_search)
                .order_by("full_name")
                .first()
            )

        context["events"] = build_admin_timeline(person=person, event_type=event_type)
        context["person_search"] = person_search
        context["event_type_filter"] = event_type
        context["event_type_choices"] = MembershipTimelineEventType.choices
        return context
