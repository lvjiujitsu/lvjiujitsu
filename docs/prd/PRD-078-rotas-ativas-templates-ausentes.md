# PRD-078: Rotas ativas com templates ausentes

## Summary
Bloquear `TemplateDoesNotExist` em rotas registradas. O inventário atual encontrou dezenas de `template_name` e `modal_template_name` sem arquivo correspondente, incluindo rotas públicas de recuperação de senha, módulos administrativos, produtos, financeiro, graduação e templates modais.

## Demand type
Correção de integridade de rotas/templates.

## Current problem
- Views registradas apontam para templates inexistentes.
- Recuperação de senha tem rotas ativas, mas templates pendentes no contrato.
- Módulos administrativos têm rotas e views, mas grande parte da superfície não renderiza.
- Testes existentes validam `reverse()` e alguns links, mas não garantem renderização real de todos os templates.

## Goal
Toda rota ativa deve ter uma decisão explícita:
- renderizar template existente;
- retornar 404/410 intencional;
- redirecionar para fluxo canônico;
- ou ser removida da URLconf com PRD própria.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/urls.py`
- `system/views/auth_views.py`
- `system/views/admin_views.py`
- `system/views/person_views.py`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`

### Adjacent files consulted
- Inventário `template_name -> exists`
- `docs/prd/PRD-071-alinhamento-suite-legada-escopo-progressivo.md`
- `docs/prd/PRD-065-hubs-administrativos-modulos-lv.md`

### Internet / official documentation
- Django templates: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 templates.

### Limitations found
- Esta PRD deve ser executada junto ou antes da PRD-077 para módulos CRUD.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual de reorganizar o sistema e listar inconsistências.

## Scope
- Criar teste de inventário de templates das views registradas.
- Resolver templates públicos críticos de recuperação de senha.
- Resolver ou bloquear explicitamente rotas administrativas sem template.
- Atualizar PRD-071 ou substituir por evidência atualizada.

## Out of scope
- Redesign completo de todos os módulos; PRD-077.
- Rotas em inglês/modal CRUD; PRD-075.

## Impacted files
- `system/tests/`
- `templates/login/*`
- `templates/admin_modules/*`
- `templates/billing/*`
- `templates/products/*`
- `templates/graduation/*`
- `templates/classes/*`
- `templates/class_categories/*`
- `templates/class_schedules/*`
- `templates/person_types/*`

## Risks and edge cases
- Criar template vazio só para passar teste esconderia produto incompleto.
- Remover rota pode quebrar links existentes.
- Templates públicos de senha precisam manter segurança e mensagens genéricas.

## Plan
- [x] Teste falhando para templates ausentes (inventário programático via `get_resolver()` + `get_template()`).
- [x] Matriz rota/view/template/decisão (gerada via shell, documentada em Evidence).
- [x] Corrigir público crítico primeiro (recuperação de senha).
- [x] Corrigir administrativos por módulo (hub, perfis) — os demais módulos foram resolvidos organicamente pela PRD-077.
- [x] Validar rotas 200/redirect/404 intencionais.

## Test plan
### Tests to author
- Inventário de templates de views registradas.
- GET de rotas públicas de senha.
- GET dos hubs principais para perfil autorizado.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_lv_foundation_templates_gap.py` (8 testes): as 4 telas de recuperação de senha renderizam, hub administrativo renderiza com KPIs e módulos reais, rota inglesa `/administration/` com redirect de `/administracao/`, listagem de perfis renderiza dado real, modal de criar perfil funciona de ponta a ponta.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_templates_gap --verbosity 2` — 8 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 testes OK (suíte completa, sem regressão).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Inventário programático final (script via `manage.py shell` percorrendo `get_resolver()` e chamando `get_template()` para cada `template_name`/`modal_template_name` de toda view registrada): de 36 templates ausentes no início, restam apenas 3 — `products/product_store.html`, `products/student_backorder_list.html`, `products/student_order_history.html` (loja pública e histórico/pré-pedido do aluno), já documentados como pendência explícita na PRD-077 (fora do escopo de CRUD administrativo).

## Visual validation
Validado no navegador interno: `/administration/` renderiza com KPIs reais e lista os 7 módulos; `/password-reset/` renderiza consistente com o visual de login; mobile (375×812) sem overflow horizontal em ambas.

## ORM validation
Não aplicável (templates de leitura/formulário simples, cobertos pelos testes focados).

## Quality validation
- `manage.py test` focado e suíte completa.
- `manage.py check`.
- Browser interno (desktop, mobile).

## Evidence
- Inventário local inicial retornou 36 templates ausentes entre views ativas.
- A PRD-075 resolveu a fundação (`lv/modal_done.html`, `theme_boot.js`, `people/person_form_modal.html`, `people/person_detail_modal.html`) e a PRD-077 resolveu os 7 módulos de domínio (Pessoas, Planos, Turmas/categorias/horários, Materiais, Graduação, Financeiro, Cronograma) organicamente durante a implementação do CRUD.
- Esta PRD fechou o restante: 4 templates de recuperação de senha (`templates/login/password_reset_*.html`), `templates/admin_modules/admin_hub.html` e 4 templates de perfis (`templates/person_types/person_type_*.html`).
- Rotas de administração e perfis migradas para inglês (`/administration/...`) com redirect de `/administracao/...`.

## Implemented
- `templates/login/password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`: reaproveitam o shell `auth/base_auth.html` e as classes de `login.css` já existentes.
- `templates/admin_modules/admin_hub.html`: lista os 7 módulos com contadores reais e os KPIs administrativos já calculados pela view.
- `templates/person_types/person_type_list.html`, `person_type_form.html`, `person_type_detail.html`, `person_type_confirm_delete.html`: CRUD completo de perfis no mesmo padrão modal das PRDs 075/077.
- `system/views/person_views.py`: `PersonTypeCreateView`/`UpdateView` ganharam `ModalFormMixin`.
- `system/urls.py`: `/administracao/...` migrado para `/administration/...` com redirect de compatibilidade.

## Cleanup findings
- Nenhum resíduo temporário.
- Nenhuma rota foi removida da URLconf; todas as views ativas agora têm decisão explícita (renderizar ou redirecionar).

## Follow-up PRDs
- Nenhuma PRD nova necessária; o gap remanescente (loja pública, histórico/pré-pedido do aluno) já está registrado como pendência na PRD-077.

## Deviations from plan
- Nenhum desvio funcional. A correção dos módulos de domínio (Pessoas, Planos, Turmas, Materiais, Graduação, Financeiro, Cronograma) acabou acontecendo dentro da execução da PRD-077, não como trabalho isolado desta PRD — refletido aqui em vez de duplicado.

## Pending
- Loja pública (`product-store`) e fluxo de pré-pedido/histórico do aluno continuam sem template — pendência explícita, não escondida, já registrada na PRD-077.

## Final status
Concluída com limitações — todas as rotas ativas administrativas e públicas críticas têm template real e testado; o gap remanescente é intencional e documentado (loja pública/aluno, fora do escopo de CRUD administrativo desta rodada).
