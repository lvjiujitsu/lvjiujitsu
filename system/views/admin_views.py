from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from system.models import (
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
from system.views.person_views import AdministrativeRequiredMixin


class AdminHubView(AdministrativeRequiredMixin, TemplateView):
    template_name = "admin_modules/admin_hub.html"

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
                "title": "Perfis e acessos",
                "description": "Tipos de pessoa, permissões operacionais e Django Admin.",
                "url_name": "system:person-type-list",
                "primary_count": PersonType.objects.filter(is_active=True).count(),
                "primary_label": "perfis ativos",
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
