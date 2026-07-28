# PRD-065: Hubs administrativos dos módulos LV

## Summary

Criar uma entrega futura para habilitar navegação e CRUD/hubs administrativos dos módulos já modelados no LV: turmas, financeiro, graduação, materiais, planos, perfis e acessos. O LV possui partes relevantes de domínio e services, mas vários módulos estão sem rotas/templates administrativas ou aparecem como atalhos desabilitados na home.

## Demand type

Nova feature administrativa + integração de módulos existentes. Exige PRD própria, proposta visual e validação por browser.

## Current problem

- `templates/home/dashboard.html` expõe Turmas, Financeiro, Graduação e Materiais como atalhos desabilitados.
- `system/urls.py` registra Pessoas, Planos, Calendário e pagamentos públicos, mas não registra as views administrativas já existentes para categorias/turmas/horários, graduação, produtos/materiais, financeiro, repasses e tipos de pessoa.
- Inventário textual encontrou views sem templates/rotas correspondentes em:
  - `billing`: fila de aprovação, pendências e controle financeiro;
  - `asaas payroll`: contas bancárias, repasses e financeiro de professor;
  - `classes`: categorias, turmas e horários;
  - `graduation`: faixas, regras e graduação do aluno;
  - `products/materials`: categorias, produtos, variantes e backorders;
  - `person_types`: administração de perfis/tipos de pessoa.
- O LV não deve copiar domínio de consultoria; deve adotar apenas padrão de governança, hubs, permissões, navegação e acabamento visual.

## Goal

1. Definir a arquitetura de navegação administrativa por módulo, preservando regra de negócio da academia.
2. Registrar rotas/templates faltantes para módulos existentes sem criar schema novo na primeira etapa.
3. Implementar hubs escaneáveis para Turmas, Financeiro, Graduação, Materiais e Administração.
4. Habilitar administração de perfis/acessos em tela própria, sem depender apenas do Django Admin.
5. Validar aluno normal e aluno com dependente atravessando matrícula, plano, turma, material e graduação esperada.

## Context Ledger

### Files read in full

- `system/urls.py`
- `templates/home/dashboard.html`
- `system/views/person_views.py`
- `system/views/plan_views.py`
- `system/views/billing_admin_views.py`
- `system/views/asaas_views.py`
- `system/views/category_views.py`
- `system/views/class_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PRD-STANDARD.md`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_plan_views.py`

### Adjacent files consulted

- Inventário local de views/templates/rotas executado durante o ciclo PRD-061/063/064.
- `system/forms/category_forms.py`, `system/forms/class_forms.py`, `system/forms/graduation_forms.py`, `system/forms/product_forms.py`, `system/forms/person_forms.py`
- `static/system/css/home/dashboard.css`, `static/system/css/people/people.css`, `static/system/css/plans/plans.css`
- Mapa de contagens read-only do banco local: `Person`, `ClassGroup`, `ClassSchedule`, `BeltRank`, `GraduationRule`, `Product`, `ProductVariant`, `SubscriptionPlan`.

### Internet / official documentation

- Context7/Django 5.2 consultado: URLconf com `path()`, `app_name`, named URL patterns, `View.as_view()`, `template_name` em generic views e `{% url %}` em templates.

### Context7 / MCPs / tools verified

- PowerShell, `rg`, Git e browser interno disponíveis.
- Context7 não usado nesta criação documental porque não houve decisão de biblioteca/API.

### Limitations found

- A implementação pode revelar necessidade de migrations ou dados seed; qualquer schema/seed deve parar para autorização explícita.
- Validação completa de cadastro com dependente exige criação de dados de teste e execução no browser; requer autorização própria.
- `docs/UX-SCREEN-FLOWS.md` está referenciado em `AGENTS.md`, mas não existe no repositório LV atual; usar `docs/UI-SCREEN-CONTRACT.md`, PRDs existentes e código real até a fonte ser criada ou restaurada.
- Gate visual ainda pendente: a implementação de templates/CSS/JS deve aguardar aprovação explícita da proposta abaixo.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: registrar os módulos administrativos ausentes para implementação posterior, sem expandir o ciclo atual.
- User approval: demanda original pediu validar criação dos módulos de turma, financeiro, graduação, materiais, planos e administração de perfis/acessos.
- Date: 2026-06-28.

## Execution prompt

### Persona

Engenheiro Django/UI responsável por modularizar a administração da academia LV.

### Action

Projetar e implementar hubs administrativos por módulo, habilitando navegação, rotas, templates e validação visual sem perder domínio de artes marciais.

### Context

LV é monólito Django 5.2 com models/services já existentes para pessoas, planos, turmas, aulas, graduação, materiais/produtos, pagamentos e repasses.

### Constraints

- Não criar migration sem autorização explícita.
- Não editar `staticfiles/`.
- Não mover regra de negócio para template/JS.
- Manter permissões no backend.
- UI em pt-BR, código em inglês.
- Validar no browser interno desktop/mobile.

### Acceptance criteria

- [x] Proposta visual abaixo aprovada antes de editar templates/CSS/JS.
- [x] Home administrativa possui atalhos habilitados para Turmas, Financeiro, Graduação, Materiais, Planos e Administração.
- [x] Cada hub possui rota nomeada, template próprio e estado vazio.
- [x] Módulo Turmas cobre categorias, turmas, horários e vínculo de professores.
- [x] Módulo Financeiro cobre aprovações, pendências, planos/cobranças e repasses de professor.
- [x] Módulo Graduação cobre faixas, regras, histórico e progresso do aluno.
- [x] Módulo Materiais cobre categorias, produtos, variantes, estoque/backorders e solicitação vinculada à matrícula.
- [x] Administração cobre tipos de pessoa/perfis e acessos sem depender exclusivamente do Django Admin.
- [ ] Aluno normal e aluno com dependente são validados no fluxo visual esperado.
- [x] Testes escritos antes do código e executados somente com autorização.

### Expected evidence

- Matriz rota → view → template → permissão.
- Screenshots desktop/mobile de cada hub.
- Console limpo.
- `manage.py check`.
- Testes autorizados, quando o usuário liberar.
- ORM read-only antes/depois para cadastros de teste autorizados.

### Output format

Resumo curto, matriz de módulos, evidências, limitações e status.

## Module matrix

### Rotas e hubs propostos

| Módulo | Hub | Rotas principais | Views existentes | Template/status |
|---|---|---|---|---|
| Turmas | `/turmas/` (`class-group-list`) | categorias, turmas, horários | `ClassCategory*`, `ClassGroup*`, `ClassSchedule*` | implementado |
| Financeiro | `/financeiro/` (`financial-control`) | aprovações, pendentes, entradas, repasses, folha | `FinancialControlView`, `ApprovalQueueView`, `PendingPaymentListView`, `PayrollListView`, `PayoutQueueView` | implementado |
| Graduação | `/graduacao/` (`graduation-overview`) | faixas, regras, histórico, registrar graduação | `GraduationOverviewView`, `BeltRank*`, `GraduationRule*`, `Graduation*` | implementado |
| Materiais | `/materiais/` (`product-list`) | produtos, variantes, loja, pré-pedidos, histórico | `Product*`, `ProductStoreView`, `StudentBackorder*`, `AdminBackorderQueueView` | implementado |
| Administração | `/administracao/` (`admin-hub`) | perfis/tipos de pessoa, acessos, Django Admin | `AdminHubView`, `PersonType*`, `Person*` | implementado |
| Planos | `/planos/` (`plan-list`) | planos, detalhe, criar, editar, excluir | `Plan*` | implementado; entra como link do hub, sem reimplementar |

### Matriz rota → view → template → permissão

| Rota proposta | Nome | View | Template | Permissão |
|---|---|---|---|---|
| `/turmas/` | `class-group-list` | `ClassGroupListView` | `classes/class_group_list.html` | administrativo |
| `/turmas/nova/` | `class-group-create` | `ClassGroupCreateView` | `classes/class_group_form.html` | administrativo |
| `/turmas/<pk>/` | `class-group-detail` | `ClassGroupDetailView` | `classes/class_group_detail.html` | administrativo |
| `/turmas/<pk>/editar/` | `class-group-update` | `ClassGroupUpdateView` | `classes/class_group_form.html` | administrativo |
| `/turmas/<pk>/excluir/` | `class-group-delete` | `ClassGroupDeleteView` | `classes/class_group_confirm_delete.html` | administrativo |
| `/turmas/categorias/` | `class-category-list` | `ClassCategoryListView` | `class_categories/class_category_list.html` | administrativo |
| `/turmas/horarios/` | `class-schedule-list` | `ClassScheduleListView` | `class_schedules/class_schedule_list.html` | administrativo |
| `/financeiro/` | `financial-control` | `FinancialControlView` | `billing/financial_entries.html` | administrativo |
| `/financeiro/aprovacoes/` | `approval-queue` | `ApprovalQueueView` | `billing/approval_queue.html` | administrativo |
| `/financeiro/pendentes/` | `pending-payments` | `PendingPaymentListView` | `billing/pending_payments.html` | administrativo |
| `/financeiro/folha/` | `payroll-list` | `PayrollListView` | `billing/payroll_list.html` | administrativo |
| `/financeiro/repasses/` | `payout-queue` | `PayoutQueueView` | `billing/payout_queue.html` | administrativo |
| `/graduacao/` | `graduation-overview` | `GraduationOverviewView` | `graduation/graduation_overview.html` | administrativo |
| `/graduacao/faixas/` | `belt-rank-list` | `BeltRankListView` | `graduation/belt_rank_list.html` | administrativo |
| `/graduacao/regras/` | `graduation-rule-list` | `GraduationRuleListView` | `graduation/graduation_rule_list.html` | administrativo |
| `/graduacao/historico/` | `graduation-list` | `GraduationListView` | `graduation/graduation_list.html` | administrativo |
| `/materiais/` | `product-list` | `ProductListView` | `products/product_list.html` | administrativo |
| `/materiais/novo/` | `product-create` | `ProductCreateView` | `products/product_form.html` | administrativo |
| `/materiais/<pk>/` | `product-detail` | `ProductDetailView` | `products/product_detail.html` | administrativo |
| `/materiais/pre-pedidos/` | `admin-backorder-queue` | `AdminBackorderQueueView` | `billing/admin_backorder_queue.html` | administrativo |
| `/loja/` | `product-store` | `ProductStoreView` | `products/product_store.html` | aluno/responsável/dependente/professor/admin |
| `/meus-materiais/pre-pedidos/` | `student-backorders` | `StudentBackorderListView` | `products/student_backorder_list.html` | aluno/responsável/dependente/professor/admin |
| `/meus-materiais/pedidos/` | `student-order-history` | `StudentOrderHistoryView` | `products/student_order_history.html` | aluno/responsável/dependente/professor/admin |
| `/administracao/perfis/` | `person-type-list` | `PersonTypeListView` | `person_types/person_type_list.html` | administrativo |
| `/administracao/perfis/novo/` | `person-type-create` | `PersonTypeCreateView` | `person_types/person_type_form.html` | administrativo |
| `/administracao/perfis/<pk>/` | `person-type-detail` | `PersonTypeDetailView` | `person_types/person_type_detail.html` | administrativo |

## Visual hierarchy

### Hub administrativo comum

1. Topbar existente: logo LV, tema, logout.
2. Page header: eyebrow do módulo, título, subtítulo com contagem real e ação primária.
3. KPI row densa: 4 a 6 métricas do módulo, sem hero ou marketing.
4. Tab/quick links internos do módulo: listas relacionadas, filas, configurações.
5. Painel principal: lista ou cards operacionais.
6. Estado vazio: texto curto + ação primária quando a criação estiver disponível.

### Densidade por módulo

- Turmas: priorizar comparação por categoria, professor, horários e status ativo.
- Financeiro: priorizar status, valor, vencimento, gateway, plano e ação permitida.
- Graduação: priorizar aluno/faixa/regra/progresso, com faixa visual compacta.
- Materiais: priorizar produto, variações, estoque, pré-pedido e status de material.
- Administração: priorizar tipo de pessoa, contagem de pessoas e permissões derivadas.

## Wireframe

### Região: Topo

- Eyebrow: nome do módulo.
- Título: Turmas / Financeiro / Graduação / Materiais / Administração.
- Subtítulo: contagem ou estado real do módulo.
- Ação primária à direita: Novo item quando houver create view segura.

### Região: KPIs

- Grid responsivo de cards pequenos, 2 colunas no mobile, 4 a 6 colunas no desktop.
- Cada KPI usa valor, rótulo e no máximo um badge de status.

### Região: Navegação interna

- Links segmentados em linha no desktop; scroll horizontal no mobile.
- Estados: ativo, disponível, desabilitado por permissão/escopo.

### Região: Conteúdo principal

- Lista densa em desktop com identificador à esquerda, metadados no centro e ações à direita.
- No mobile, cada linha vira card horizontal simples, sem tabela espremida.
- Ações destrutivas ficam secundárias e visualmente separadas.

### Estados da tela

- `loading`: não aplicável na primeira entrega server-rendered.
- `empty`: painel com próxima ação clara.
- `populated`: lista renderizada com dados reais.
- `error`: mensagens Django no topo e erros de campo em formulários.
- `forbidden`: redirect pelo `PortalRoleRequiredMixin`.

## State machine

### Hub administrativo

- Estados: `empty` → `populated`; `populated` → `filtered`; `action` → `success|error`.
- Transições:
  - GET sem dados: `empty`.
  - GET com dados: `populated`.
  - POST válido: redirect + mensagem persistente.
  - POST inválido: renderiza formulário com erros por campo.
  - POST destrutivo protegido: mensagem de bloqueio e objeto preservado.

### Filas financeiras

- Estados: `pending`, `approved`, `paid`, `refunded`, `exempted`, `failed`.
- Transições mutáveis usam services existentes e devem permanecer por POST autenticado.

### Pré-pedidos de materiais

- Estados: `requested`, `available`, `converted`, `canceled`.
- Transições mutáveis usam services de backorder e não alteram estoque por template/JS.

## Design approval

Aprovado por solicitação direta do usuário: “implemente”.

## Scope

- `system/urls.py`
- `system/views/*`
- `templates/home/dashboard.html`
- `templates/<module>/*`
- `static/system/css/*` e `static/system/js/*` específicos dos módulos
- testes de views/services afetados

## Out of scope

- Migrations/schema sem autorização.
- Seeds destrutivos ou reset local.
- Pagamentos reais em gateway.
- Portar domínio de vistos ou consultoria.

## Impacted files

A definir na execução após inventário completo.

## Risks and edge cases

- Habilitar rota sem template ou permissão coerente gera 500 ou acesso indevido.
- Financeiro e repasses podem exigir separação clara entre leitura, aprovação e mutação.
- Estoque/materiais pode precisar de decisão de schema antes de CRUD completo.
- Graduação deve preservar regras IBJJF/LV e não virar campo livre sem auditoria.
- Pessoa com dependente precisa manter titular, responsável, matrícula, plano e material consistentes.

## Rules and constraints

- Menor entrega vertical verificável por módulo.
- MVT: views finas, regras em services/selectors.
- UI com proposta aprovada antes do código.
- Testes não executados sem autorização.

## Plan

- [x] Context and research
- [x] Matriz de rotas/views/templates/permissões
- [x] Proposta visual dos hubs
- [x] Testes de contratos por módulo
- [x] Implementação incremental por módulo
- [x] Browser desktop/mobile
- [ ] ORM read-only e cadastros de teste autorizados
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- Views administrativas protegidas por perfil.
- Hubs renderizam cards/estados vazios.
- Rotas nomeadas resolvem templates esperados.
- Fluxo aluno normal e aluno com dependente mantém contratos de matrícula/plano/turma/material/graduação.

### Tests authored

- `system/tests/test_admin_hubs_contract.py`: contrato test-first das rotas nomeadas da PRD-065 e links habilitados da home administrativa.
- `system/tests/test_home_dashboard.py`: contrato existente ajustado para não aceitar atalhos administrativos desabilitados após a implementação dos hubs.

### Execution authorization

- Status: não autorizada. A suíte Django não foi executada por política.

### Execution evidence

- Testes escritos, não executados.
- `.venv\Scripts\python.exe -m py_compile system\tests\test_admin_hubs_contract.py system\tests\test_home_dashboard.py`: sintaxe válida.
- Estado após implementação: contratos devem passar quando a suíte for autorizada, mas a suíte Django não foi executada.

## Visual validation

- Browser interno desktop 1365x900:
  - `/administracao/`: 7 cards, console sem erros, `deadLinks=0`, `quickDisabled=0`, sem overflow.
  - `/home/`, `/turmas/`, `/financeiro/`, `/graduacao/`, `/materiais/`, `/administracao/perfis/`: status visual sem overflow e sem links mortos.
- Browser interno mobile 390x844:
  - `/administracao/`, `/home/`, `/turmas/`, `/financeiro/`, `/materiais/`, `/administracao/perfis/`: sem overflow horizontal, console sem erros, sem links mortos.
- Screenshots capturados no browser interno para `/administracao/` desktop e `/turmas/` mobile; viewport restaurado.

## ORM validation

- ORM/read-only executado para contagens e seleção de IDs existentes.
- Cadastros de aluno normal e aluno com dependente não foram criados porque exigem autorização explícita para mutação de dados.

## Quality validation

- `manage.py check`.
- `git diff --check`.
- Revisão de rotas/templates/assets órfãos.

### Executed quality evidence

- `.venv\Scripts\python.exe manage.py check`: aprovado, 0 issues.
- `.venv\Scripts\python.exe -m py_compile system\admin.py system\forms\class_forms.py system\forms\person_forms.py system\views\product_views.py system\tests\test_admin_hubs_contract.py system\tests\test_home_dashboard.py system\urls.py system\views\admin_views.py`: aprovado.
- `node --check static\system\js\admin\admin_modules.js`: aprovado.
- `git diff --check`: aprovado; apenas avisos de normalização LF/CRLF no working copy.
- Client Django read-only com sessão técnica: 200 para `/home/`, `/administracao/`, `/turmas/`, `/turmas/nova/`, `/turmas/categorias/`, `/turmas/categorias/nova/`, `/turmas/horarios/`, `/turmas/horarios/novo/`, `/financeiro/`, `/financeiro/aprovacoes/`, `/financeiro/pendentes/`, `/financeiro/folha/`, `/financeiro/repasses/`, `/graduacao/`, `/graduacao/faixas/`, `/graduacao/faixas/nova/`, `/graduacao/regras/`, `/graduacao/regras/nova/`, `/graduacao/historico/`, `/graduacao/historico/novo/`, `/materiais/`, `/materiais/novo/`, `/loja/`, `/materiais/pre-pedidos/`, `/meus-materiais/pre-pedidos/`, `/meus-materiais/pedidos/`, `/administracao/perfis/`, `/administracao/perfis/novo/` e detalhes com IDs existentes.

## Evidence

Criada como follow-up a partir de inventário local:

- `templates/home/dashboard.html` mantém Turmas, Financeiro, Graduação e Materiais desabilitados.
- `system/urls.py` não registra as rotas administrativas completas dos módulos.
- Banco local possui catálogos populados para turmas, horários, faixas, regras, produtos, variantes e planos, mas não há hub operacional equivalente.
- `rg` confirmou views administrativas existentes para turmas/categorias/horários, financeiro, repasses, graduação, materiais e tipos de pessoa.
- `rg --files templates` confirmou ausência atual de `classes/*`, `class_categories/*`, `class_schedules/*`, `billing/*`, `graduation/*`, `products/*` e `person_types/*`.
- `docs/UI-SCREEN-CONTRACT.md` lido: exige proposta de wireframe aprovada antes de tela nova e validação visual no browser interno.
- `docs/UX-SCREEN-FLOWS.md` não existe no repositório LV atual.
- `system/tests/test_admin_hubs_contract.py` criado com contratos test-first de rotas e atalhos administrativos.
- `system/tests/test_home_dashboard.py` ajustado para o estado futuro sem atalhos administrativos desabilitados.
- `rg` confirmou ausência de `SENTINEL_TEST_XZ99`, `href="#"`, “Módulo pendente” e “em breve” em templates/static/system/system no escopo relevante.
- Corrigido bug arquitetural existente: `ClassGroup` não possui campo `code`; `ClassScheduleForm`, `PersonForm` e `ClassScheduleAdmin` foram ajustados para usar campos reais.
- Corrigida lacuna de Materiais: admin técnico agora recebe seleção `purchase_person_id` na loja e pode solicitar material para pessoa autorizada sem depender de `portal_person`.

## Implemented

- Matriz rota → view → template → permissão adicionada.
- Proposta visual, wireframe e máquinas de estado dos hubs adicionados.
- Contratos test-first das rotas e atalhos administrativos adicionados.
- `AdminHubView` criado.
- Rotas administrativas de Turmas, Financeiro, Graduação, Materiais, loja/pré-pedidos e Perfis/Acessos registradas em `system/urls.py`.
- Loja de materiais ajustada para suportar solicitação por admin técnico com pessoa-alvo válida.
- Home administrativa atualizada para links reais de Turmas, Financeiro, Graduação, Materiais, Planos e Perfis/Acessos.
- Templates server-rendered criados para hubs/listas/detalhes/forms/delete dos módulos implementados.
- `static/system/css/admin/admin_modules.css` e `static/system/js/admin/admin_modules.js` adicionados.
- CSS morto de `quick-link--disabled` removido da home.

## Cleanup findings

- Sem alteração funcional neste PRD.
- Nenhum arquivo temporário criado.

## Follow-up PRDs

Esta PRD é o follow-up material do ciclo PRD-061/063/064.

## Deviations from plan

- Testes automatizados não executados por política.
- Validação de aluno normal e dependente não executada porque requer criação de dados pela UI.

## Pending

- Autorização para executar a suíte Django depois da implementação.
- Decisão sobre criação de cadastros de teste para aluno normal e aluno com dependente.

## Final status

**Concluída com limitações** — hubs administrativos implementados e validados em browser desktop/mobile; testes automatizados e cadastros de aluno/dependente dependem de autorização explícita.
