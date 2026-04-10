# PRD-008: CRUD de Planos de Assinatura e Checkout no Cadastro

## Resumo
Criar CRUD administrativo para planos de assinatura (mensalidades), integrar seleção de plano e materiais ao final do wizard de cadastro, e exibir resumo com somatória de valores.

## Problema atual
Não existe cadastro de planos de assinatura. O wizard de cadastro não oferece etapa para escolha de plano ou aquisição de materiais, dificultando a visualização do custo total de ingresso.

## Objetivo
1. CRUD completo de planos (admin)
2. Etapa "Plano e Materiais" no wizard de cadastro (holder e guardian)
3. Etapa "Resumo" com somatória de valores antes do submit

## Dependências adicionadas
Nenhuma.

## Escopo
- Model `SubscriptionPlan` (code, display_name, price, billing_cycle, description, is_active)
- CRUD views/templates/URLs seguindo padrão de Product
- Seed de planos SumUp (Mensal R$250, Irmãos R$225, Trimestral R$675, Desconto R$450)
- Link "Planos" na navegação (drawer, dashboards, login page, info page)
- Página pública de catálogo de planos
- Wizard: etapa plan_materials (seleção de plano + materiais com quantidades)
- Wizard: etapa summary (resumo com somatória)
- Campos no form: `selected_plan`, `selected_products_payload` (JSON)
- Service: `create_registration_order()` — persiste seleções
- Model `RegistrationOrder` + `RegistrationOrderItem` — rastreia plano e materiais escolhidos

## Fora do escopo
- Processamento de pagamento real (apenas resumo informativo)
- Integração com gateway (SumUp API)
- Gestão de cobranças recorrentes
- Desconto automático de estoque no cadastro

## Arquivos impactados

### Novos
- `system/models/plan.py` — SubscriptionPlan
- `system/models/registration_order.py` — RegistrationOrder, RegistrationOrderItem
- `system/forms/plan_forms.py` — PlanForm
- `system/services/plan_management.py` — CRUD service
- `system/views/plan_views.py` — CRUD views + PlanCatalogView
- `templates/plans/plan_list.html`
- `templates/plans/plan_detail.html`
- `templates/plans/plan_form.html`
- `templates/plans/plan_confirm_delete.html`
- `templates/plans/plan_catalog.html`
- `system/tests/test_plan_models.py`
- `system/tests/test_plan_views.py`
- `system/management/commands/seed_plans.py`

### Modificados
- `system/models/__init__.py` — exports
- `system/admin.py` — admin registration
- `system/forms/__init__.py` — exports
- `system/views/__init__.py` — exports
- `system/urls.py` — rotas
- `system/services/seeding.py` — seed definitions
- `system/management/commands/inicial_seed.py` — call seed_plans
- `system/forms/registration_forms.py` — campos de plano/materiais
- `system/services/registration.py` — criar RegistrationOrder
- `templates/login/register.html` — painéis plan-materials e summary
- `static/system/js/auth/registration-wizard-clean.js` — steps + lógica de preços
- `templates/base.html` — link Planos no drawer
- `templates/home/*/dashboard.html` — card Planos
- `templates/login/login.html` — botão Planos
- `templates/login/info.html` — seção planos

## Plano (ordenado por dependência)

1. Models (SubscriptionPlan, RegistrationOrder, RegistrationOrderItem)
2. Forms (PlanForm)
3. Services (plan_management.py, seed)
4. Views (CRUD + catalog)
5. URLs
6. Templates (CRUD + catalog)
7. Admin
8. Navigation (drawer, dashboards, login, info)
9. Wizard integration (form fields, JS steps, template panels, service)
10. Tests
11. Reset cycle

## Comandos de validação
```powershell
.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_models system.tests.test_plan_views
.\.venv\Scripts\python.exe manage.py test
```
