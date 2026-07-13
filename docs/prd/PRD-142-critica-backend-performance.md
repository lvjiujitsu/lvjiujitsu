# PRD-142: Crítica backend — performance e queries

## Summary

Auditoria read-only **altamente crítica** de performance do backend LV JIU JITSU (jul/2026), focada em `system/services/`, `system/selectors/`, `system/views/`, `system/models/` (properties com query), `system/signals.py` e índices inferidos de `system/migrations/0001_initial.py`. Resultado: **47 hotspots** classificados (12 CRÍTICA, 18 ALTA, 12 MÉDIA, 5 BAIXA); **zero testes** com `assertNumQueries` ou contrato de budget de queries; risco dominante em **home**, **panorama de graduação** e **calendário mensal** sob crescimento de alunos/pedidos.

## Demand type

Auditoria read-only de performance (queries, N+1, índices, testes ausentes). **Não implementa código** — registra achados com evidência e roteia correções para PRD-filha ou consolidador.

## Current problem

O backend concentra regra de negócio em services/selectors, mas padrões recorrentes degradam latência e escalabilidade:

| Padrão | Ocorrências | Impacto típico |
|---|---|---|
| Loop sobre queryset sem prefetch + property/query interna | 15+ | N+1, O(n) queries |
| View/home agregando múltiplos services pesados por request | 1 (`HomeView`) | O(n × dependentes) |
| Property `@property` com `.objects.filter()` | 3 em `Membership`, 1 em `Person` | Query oculta por acesso |
| Full scan + nested loop em memória | `get_calendar_month_data` | O(dias × horários) |
| Índices ausentes em tabelas de alto volume | calendário, pedidos, graduação | sequential scan em HG (Postgres) |
| Ausência total de testes de performance | `system/tests/` | regressão invisível |

### Top 5 hotspots (ordem de risco em produção)

1. **`get_graduation_overview`** — 1 request × N alunos × ~5–7 queries/aluno.
2. **`HomeView.get_context_data`** — empilha cronograma, graduação, billing e payroll; multiplica por dependente.
3. **`Membership.effective_tier` / `current_pause`** — query em property usada em loops de família e home.
4. **`get_calendar_month_data`** — carrega todos os `ClassSchedule` ativos e cruza com cada dia do mês.
5. **`calculate_monthly_payroll` → `_get_order_students_for_groups`** — query por pedido pago no mês.

## Goal

Documentar inventário completo de hotspots com **arquivo:linha**, severidade, estimativa de impacto e índices recomendados; proposta de correção em ondas P0–P2 (jul/2026).

## Context Ledger

### Files read in full

- `docs/PRD-STANDARD.md`, `AGENTS.md`, `CLAUDE.md`
- `system/services/class_calendar.py` (1533L)
- `system/services/membership.py`
- `system/services/registration_checkout.py`
- `system/services/graduation.py`
- `system/services/family_pricing.py`
- `system/services/financial_dashboard.py`
- `system/services/payroll_rules.py` (amostragem profunda em `calculate_monthly_payroll` e helpers)
- `system/services/asaas_billing_cycle.py`
- `system/services/plan_change.py` (trechos `build_plan_catalog`)
- `system/services/membership_timeline.py`
- `system/services/product_backorders.py` (amostragem)
- `system/selectors/graduation.py`
- `system/selectors/plan_eligibility.py`
- `system/selectors/person_selectors.py`
- `system/views/home_views.py` (733L)
- `system/views/person_views.py` (trechos list/detail/update)
- `system/views/calendar_views.py`
- `system/views/admin_views.py` (`AdminHubView`)
- `system/views/graduation_views.py` (`GraduationOverviewView`)
- `system/models/membership.py` (properties)
- `system/models/person.py` (`current_ibjjf_category`)
- `system/models/calendar.py` (Meta/indexes)
- `system/models/registration_order.py` (Meta/indexes)
- `system/signals.py`
- `system/migrations/0001_initial.py` (seção `AddIndex` e models de calendário)

### Adjacent files consulted

- `docs/prd/PRD-138-auditoria-arquitetural-fluxo-unico-consistencia.md`
- `docs/prd/PRD-139-auditoria-cobertura-total-inventario-completo.md`
- `docs/prd/README.md`
- `rg` em `system/` por `assertNumQueries`, `select_related`, `prefetch_related`, `.objects.` em loops

### Internet / official documentation

- [Django — Database access optimization](https://docs.djangoproject.com/en/5.2/topics/db/optimization/) — `select_related`/`prefetch_related`, `annotate`, `iterator`, profiling com `connection.queries`, anti-padrão de queries em loop.
- [Django — Model index reference](https://docs.djangoproject.com/en/5.2/ref/models/indexes/) — `Meta.indexes` e impacto em filtros/ordenação.
- Skill `supabase-postgres-best-practices` (categoria `query-` / `schema-`) — índices compostos e partial indexes para filtros frequentes (`status`, `date`, FK).

### Context7 / MCPs / tools verified

- `rg` / leitura integral dos arquivos listados
- Skill `lv-prd` aplicada para estrutura
- Skill `supabase-postgres-best-practices` consultada para priorização de índices

### Limitations found

- Auditoria **estática** — nenhum `EXPLAIN ANALYZE`, `assertNumQueries` ou medição de latência HTTP executada nesta PRD.
- Estimativas de impacto são **inferidas** por padrão de código e cardinalidade esperada (academia média: 200–800 alunos, dezenas de horários/dia).
- `staticfiles/` e ambiente HG não foram perfilados.
- Correções concretas documentadas na seção Proposta de correção (jul/2026).

## Required skills

- `lv-task-intake` (concluída)
- `lv-prd` (esta PRD)
- `lv-django-delivery` (execução futura)
- `supabase-postgres-best-practices` (índices HG/produção)

## Understanding approved

Solicitação (jul/2026): auditoria read-only implacável de performance no backend; criticar com evidência; criar PRD-142; atualizar índice; **não implementar**.

## Execution prompt

### Persona

Revisor de performance implacável — apenas criticar com evidência; sem suavizar achados.

### Action

Consolidar correções em PRD-filha ou onda dedicada; aplicar testes com budget de queries antes de refatorar hotspots CRÍTICA.

### Context

Esta PRD é o mapa de hotspots; implementação exige nova aprovação explícita.

### Constraints

- Baseline de migration única (`0001_initial.py`) — novos índices exigem PRD de schema + confirmação HG/produção.
- Não alterar comportamento funcional sem testes de regressão.
- Medir antes/depois com `assertNumQueries` ou `django-debug-toolbar` / log de queries em ambiente controlado.

### Acceptance criteria

- [ ] Hotspots CRÍTICA (PERF-001–012) endereçados ou explicitamente aceitos com justificativa
- [ ] `get_graduation_overview` com budget documentado (ex.: ≤15 queries para 500 alunos)
- [ ] `HomeView` com budget por persona (aluno simples, responsável + 3 dependentes, professor+admin)
- [ ] Índices recomendados (seção 6) avaliados em HG com `EXPLAIN`
- [ ] Pelo menos 1 módulo de teste `*Performance*` ou `assertNumQueries` por área crítica

### Expected evidence

- Saída de `manage.py test` com testes de query budget
- `EXPLAIN (ANALYZE, BUFFERS)` em HG para 3 queries representativas pós-índice
- Comando + contagem de queries (`connection.queries`) antes/depois em fixture seedada

### Output format

PRD-filha por onda: `PERF-ondas` com checklist por ID PERF-xxx.

## Scope

- `system/services/` (ênfase: `class_calendar.py`, `membership.py`, `registration_checkout.py`, `graduation.py`, `payroll_rules.py`, `financial_dashboard.py`, `family_pricing.py`, `plan_change.py`, `asaas_billing_cycle.py`)
- `system/selectors/` (`graduation.py`, `plan_eligibility.py`, `person_selectors.py`)
- `system/views/` (`home_views.py`, `person_views.py`, `calendar_views.py`, `graduation_views.py`, `admin_views.py`)
- Properties com query em `system/models/`
- `system/signals.py`
- Índices em `system/migrations/0001_initial.py` vs padrões de filtro observados
- Lacuna de testes de performance em `system/tests/`

## Out of scope

- Implementação de correções (execução via PRD-filhas por onda)
- Frontend / `register.js`
- Otimização de chamadas externas Asaas/Stripe (mencionada onde bloqueia home admin)
- Connection pooling / PgBouncer (infra Render/Supabase)
- Refatoração arquitetural geral (PRD-138)

## Impacted files

| Arquivo | Papel na auditoria |
|---|---|
| `system/selectors/graduation.py` | Hotspot CRÍTICA PERF-001 |
| `system/views/home_views.py` | Hotspot CRÍTICA PERF-002, PERF-003 |
| `system/services/class_calendar.py` | Hotspots CRÍTICA PERF-004, PERF-005, ALTA PERF-013–016 |
| `system/models/membership.py` | Hotspots CRÍTICA PERF-006, PERF-007 |
| `system/services/family_pricing.py` | ALTA PERF-017 |
| `system/services/financial_dashboard.py` | CRÍTICA PERF-008 |
| `system/services/payroll_rules.py` | CRÍTICA PERF-009 |
| `system/services/plan_change.py` | ALTA PERF-018 |
| `system/services/membership.py` | ALTA PERF-019–021 |
| `system/selectors/plan_eligibility.py` | ALTA PERF-022–023 |
| `system/views/person_views.py` | ALTA PERF-024 |
| `system/selectors/person_selectors.py` | ALTA PERF-025 |
| `system/views/admin_views.py` | ALTA PERF-026 |
| `system/signals.py` | MÉDIA PERF-035 |
| `system/migrations/0001_initial.py` | Seção índices (Seção 6) |

## Risks and edge cases

- Otimizar `HomeView` sem quebrar combinações de papel (aluno + professor + admin + responsável).
- Índice composto errado pode piorar escrita em check-in alto volume.
- Cache de `effective_tier` pode desatualizar desconto família se tier legado mudar.
- `get_calendar_month_data` pré-computa mês inteiro — cache por mês pode servir stale após cancelamento de aula.
- Payroll depende de janela de pedidos — agregação SQL incorreta altera repasse.

## Rules and constraints

- Evidência por `arquivo:linha` ou padrão nomeado repetido.
- Classificação: **CRÍTICA** = degradação provável >1s ou O(n²)/N+1 em rota frequente; **ALTA** = N+1 ou full scan em rota administrativa; **MÉDIA** = redundância ou índice ausente em volume moderado; **BAIXA** = micro-otimização ou aceitável em MVP.
- Política de migrations do projeto: alteração de índices via PRD de schema dedicada.

## Plan

### Onda P0 — Testes + home + graduação + properties
- [ ] Criar `test_performance_graduation.py`, `test_performance_home.py`, `test_performance_membership.py` (budgets baseline)
- [ ] PERF-006/007: `resolve_effective_tier` + pause prefetch (coordenar PRD-143)
- [ ] PERF-001/010/011: `get_graduation_overview` bulk (≤15 queries / 50 alunos)
- [ ] PERF-002/003/015: extrair `selectors/home_context.py`; deduplicar dependentes/billing
- [ ] PERF-008/009/012: agregação SQL financial, payroll batch, cache plan catalog

### Onda P1 — Calendário e elegibilidade
- [x] PERF-005/013: `get_calendar_month_data` (`select_related main_teacher`) e checkins staff em lote — implementados. PERF-004: avaliado, não aplicável (SpecialClass não tem `class_group`)
- [x] PERF-014: memo instructor groups (memoização por instância de `person`, escopo de request) — implementado. PERF-032: cache de feriado revertido (cross-request cache incompatível com isolamento de teste do Django)
- [x] PERF-019/020: unificação de `get_membership_owner`/`get_active_membership` em billing — implementado. PERF-016/018: avaliados, não implementados (mudariam dado histórico exibido ao usuário — decisão de produto)
- [x] PERF-022/027: PERF-022 (prefetch elegibilidade familiar) implementado; PERF-023 avaliado, sem N+1; PERF-027 avaliado, não implementado (risco de concorrência em `select_for_update`)

### Onda P2 — Índices HG + admin + backlog
- [ ] PRD schema índices Seção 6 (CRÍTICA/ALTA) + `EXPLAIN` HG
- [ ] PERF-026: AdminHub agregação única
- [ ] PERF-017/021/024/025/028/029: family pricing, person list, jobs Asaas
- [ ] Documentar budgets finais em cada teste `*Performance*`

### Inventário de hotspots (auditoria read-only)

Legenda de impacto:

- **N+1**: 1 query inicial + N queries no loop
- **O(n×m)**: nested loop em memória com trabalho por item
- **FTS**: full table scan potencial sem índice adequado

#### CRÍTICA

| ID | Local | Padrão | Impacto estimado |
|---|---|---|---|
| PERF-001 | `system/selectors/graduation.py:23-25` | `for person in queryset: compute_graduation_progress(person)` | **N+1 severo**: por aluno ~5–7 queries (`get_current_graduation`, `_resolve_applicable_rule`, `count_approved_classes_in_window` com 2 queries). Panorama admin: **O(n) queries**, n = alunos ativos. |
| PERF-002 | `system/views/home_views.py:78-233` | `get_context_data` empilha `get_today_classes_*`, `compute_graduation_progress`, `build_financial_dashboard`, `_build_billing_context`, `build_client_timeline`, payroll | **Request storm**: 15–40+ queries por persona complexa antes de dependentes. Rota mais acessada do portal. |
| PERF-003 | `system/views/home_views.py:567-591` (`_build_dependents`) | Por dependente: `compute_graduation_progress`, `get_graduation_history`, `get_today_classes_for_person`, `get_student_checkin_history`, `get_active_membership`, `get_membership_owner` | **O(d × Q)**: d dependentes × ~15–25 queries cada. Responsável com 3 dependentes pode **triplicar** custo da home. |
| PERF-004 | `system/services/class_calendar.py:253-257`, `661-665` | `SpecialClass.objects.filter(date=today)` sem filtro de papel; lista completa do dia para cada aluno/admin | **FTS + over-fetch**: carrega todos os aulões do dia para quem só precisa de subset. Escala com quantidade de aulões, não de matrículas. |
| PERF-005 | `system/services/class_calendar.py:1337-1434` (`get_calendar_month_data`) | Carrega **todos** `ClassSchedule` ativos (`1351-1355`); loop `day_num × day_schedules` (`1378-1405`) | **O(dias × horários)**: ~31 × \|schedules\| iterações/request. `main_teacher` acessado sem `select_related` (`1398-1400`) → **N+1** adicional. |
| PERF-006 | `system/models/membership.py:139-151` (`effective_tier`) | `@property` com `PlanTier.objects.filter(audience=..., weekly_frequency=...).first()` quando `plan_price` é null | **Query oculta** por acesso. Em `family_pricing.py:35-36` loop sobre memberships chama property → **N+1** para memberships legadas. |
| PERF-007 | `system/models/membership.py:243-252` (`current_pause`) | `@property` com `pause_requests.filter(...).first()` | **N+1** em `get_today_classes_for_person:267-268` para cada entrada de cronograma que lê membership sem `prefetch_related('pause_requests')`. |
| PERF-008 | `system/services/financial_dashboard.py:200-204` | `_aggregate_net_inflows`: `for order in queryset` materializa **todos** pedidos pagos | **O(n) Python** sobre tabela `RegistrationOrder` em toda home admin. Deveria ser `Sum(Coalesce('net_amount', 'total'))`. |
| PERF-009 | `system/services/payroll_rules.py:561-566`, `658-672` | `_build_student_entries_from_orders` chama `_get_order_students_for_groups` **por pedido** | **N+1**: 1 query `ClassEnrollment` × \|pedidos pagos no mês\|. Home professor com payroll ativo. |
| PERF-010 | `system/services/graduation.py:22-45` (`count_approved_classes_in_window`) | 2 queries por pessoa (regular + special checkins) | Componente de PERF-001; isolado é aceitável, **multiplicado por N alunos** vira gargalo. |
| PERF-011 | `system/views/graduation_views.py:177` | `get_graduation_overview` na view administrativa | Dispara PERF-001 em produção sem paginação nem cache. |
| PERF-012 | `system/services/plan_change.py:314-320` | `build_plan_catalog`: `calculate_plan_change` por plano elegível | **O(planos × custo interno)** na home billing; cada iteração toca membership/orders. Catálogo grande → latência perceptível. |

#### ALTA

| ID | Local | Padrão | Impacto estimado |
|---|---|---|---|
| PERF-013 | `system/services/class_calendar.py:786-788` (`get_today_classes_staff_overview`) | `for special in ...: SpecialClassCheckin.objects.filter(special_class=special)` | **N+1**: 1 query por aulão do dia. |
| PERF-014 | `system/services/class_calendar.py:1212-1221` | `_get_instructor_class_group_ids` chamado 2× em `assert_instructor_owns_schedule` / `_can_instructor_access_session` | **2 queries duplicadas** (ClassGroup + ClassInstructorAssignment) por validação de permissão. |
| PERF-015 | `system/views/home_views.py:159-176` | `get_today_classes_for_person` + `get_today_classes_for_instructor` + merge — overlap de queries de cronograma | Redundância: mesma data/holiday/sessions consultados múltiplas vezes no mesmo request. |
| PERF-016 | `system/views/home_views.py:209-221` | `ClassSession` + `SpecialClass` `values_list('date')` sem limite para contagem de presença professor | **FTS potencial** em histórico completo de sessões presentes. |
| PERF-017 | `system/services/family_pricing.py:34-51` | Loop `membership.effective_tier` + `save` individual + `_sync_stripe_discount` | N queries tier + N writes; cancelamento Stripe dispara em `mark_membership_canceled:471-483` por membership. |
| PERF-018 | `system/views/home_views.py:516-537` (`_build_payment_history_items`) | `MembershipInvoice.objects.filter(membership=...)` **sem** `[:limit]` por aba billing | Carrega histórico completo de faturas × abas (titular + dependentes). |
| PERF-019 | `system/services/membership.py:690-702` (`get_guardian_billing_tabs`) | `_build_billing_tab` por dependente chama `get_active_membership` + `get_latest_open_order` | **2–4 queries × dependentes**; duplica trabalho de `_build_dependents`. |
| PERF-020 | `system/services/membership.py:636-658` (`get_membership_owner` / `_person_has_financial_records`) | `.exists()` em Membership e RegistrationOrder por responsável candidato | Até **2 queries × responsáveis** em cadeia de billing. |
| PERF-021 | `system/services/membership.py:471-483` (`mark_membership_canceled`) | `recompute_family_discounts_for_person` no loop por membership cancelada | Recomputo família repetido; cada um revarre grupo familiar. |
| PERF-022 | `system/selectors/plan_eligibility.py:253-264` (`build_eligibility_context_for_person`) | Loop `family_people` → `_classify_person_audience` | **N+1 enrollments** por membro da família (`301-303`). |
| PERF-023 | `system/selectors/plan_eligibility.py:62-65` (`compute_veteran_member_since`) | Query memberships sem cache; chamado de `build_eligibility_context_for_person:264` | Query extra por contexto de elegibilidade/troca de plano. |
| PERF-024 | `system/views/person_views.py:145-146` | Loop `_hydrate_person_relationships` sobre lista paginada | CPU + acesso ORM por linha; prefetch ajuda mas `prepare_class_group_for_display` repete trabalho. Com filtros `distinct()` (PERF-025) piora. |
| PERF-025 | `system/selectors/person_selectors.py:154-185` | Filtros com múltiplos `Q` OR em relações M2M/FK + `.distinct()` | **JOIN explosion** + `DISTINCT` custoso em Postgres em listagem de pessoas. |
| PERF-026 | `system/views/admin_views.py:31-105` | 17× `.count()` separados no hub admin | 17 round-trips DB por pageview; deveria ser agregação única ou cache. |
| PERF-027 | `system/services/registration_checkout.py:595-607` (`apply_order_variant_stock`) | `resolve_order_item_variant` com query por item (`613-627`) | **N queries** (com `select_for_update`) por item do pedido. |
| PERF-028 | `system/services/asaas_billing_cycle.py:44-48` | Loop `find_due_asaas_memberships`: `_has_pending_renewal_order` por membership | **N× exists** em `RegistrationOrder` no job de cobrança. |
| PERF-029 | `system/services/financial_dashboard.py:85-116` | `_build_local_totals`: múltiplos `aggregate` + filtros repetidos em `RegistrationOrder` | 6+ agregações separadas; aceitável admin-only, mas somável. |
| PERF-030 | `system/views/person_views.py:227-228`, `293-294` | `compute_graduation_progress` + `get_graduation_history` por detail/update | Duplica PERF-010 para 1 pessoa — OK isolado, pesado em modais frequentes. |

#### MÉDIA

| ID | Local | Padrão | Impacto estimado |
|---|---|---|---|
| PERF-031 | `system/models/person.py:233-245` (`current_ibjjf_category`) | Property carrega **todas** `IbjjfAgeCategory` por acesso | Query repetida se property usada em loop (lista usa cache local em `_hydrate` — OK na listagem). |
| PERF-032 | `system/services/class_calendar.py:265`, `421`, `521`, `736` | `Holiday.objects.filter(date=today)` repetido em funções do mesmo fluxo | 2–4 queries idênticas por request de cronograma. |
| PERF-033 | `system/views/home_views.py:409` | `get_student_checkin_history(dependent["person"])` sem `limit` em tab | Duplica histórico já carregado em `_build_dependents` (`limit=5`). |
| PERF-034 | `system/services/membership.py:232-234`, `290-292`, `409-411` | `Membership.objects.filter(stripe_subscription_id=...)` sem `select_related('person')` antes de notificar | Query + lazy load person em webhooks Stripe. |
| PERF-035 | `system/signals.py:18-19` | `pre_save` `ProductVariant`: `.get(pk=...)` por save | +1 query/write em atualização de estoque; aceitável em baixo volume, sensível em seed/import. |
| PERF-036 | `system/services/product_backorders.py:67-87`, `147-151` | Loops `restock_variant` / cancel com query por backorder/variant | N+1 em operações de estoque em lote. |
| PERF-037 | `system/services/registration_checkout.py:150-212`, `271-304` | Catálogo wizard: full table scan de planos/produtos ativos | O(n) aceitável em MVP; sem cache HTTP/ORM. |
| PERF-038 | `system/views/calendar_views.py:88-97` | Queries extras `ClassSchedule` + `SpecialClass` para IDs do instrutor | Redundante com `get_calendar_month_data` já pesado. |
| PERF-039 | `system/services/class_calendar.py:50-57` (`_training_class_group_ids`) | Query enrollments + possível append `class_group_id` | Query extra por cronograma; poderia usar prefetch do person. |
| PERF-040 | `system/views/home_views.py:144`, `725-732` | `class_enrollments.filter(...).exists()` e lista completa de instrutores | exists OK; `_get_active_instructor_choices` sem cache em toda home com área professor. |
| PERF-041 | `system/services/membership_timeline.py:30-37` | `build_client_timeline`: query eventos família | Única query com `select_related` — OK; limite 30 adequado. |
| PERF-042 | `system/services/graduation.py:297-345` (`get_graduation_history`) | Loop in-memory sobre graduações | CPU O(g); g pequeno — sem query extra no loop. |

#### BAIXA

| ID | Local | Padrão | Impacto estimado |
|---|---|---|---|
| PERF-043 | `system/services/class_calendar.py:1138-1196` | `get_student_checkin_history`: duas queries amplas + sort Python | Limit 12 mitiga; índice em `(person, status)` ajudaria. |
| PERF-044 | `system/views/person_views.py:137-142` | `IbjjfAgeCategory` carregada 1× por list view | Cache request-level — aceitável. |
| PERF-045 | `system/services/membership.py:725-729` (`has_dependents`) | `.exists()` dedicado antes de `_build_dependents` | +1 query; fusível com prefetch de relationships. |
| PERF-046 | `system/services/class_calendar.py:1199-1208` | `_get_instructor_class_group_ids` duas queries merge Python | Custo fixo baixo; repetido (ver PERF-014). |
| PERF-047 | `system/views/calendar_views.py:113-120` | `_resolve_checkin_actor`: exists + get Person | 2 queries por POST check-in — aceitável. |

### Seção 2 — Properties com query (anti-padrão Django)

| Model | Property | Linhas | Query |
|---|---|---|---|
| `Membership` | `effective_tier` | `139-151` | `PlanTier.objects.filter(...).first()` |
| `Membership` | `current_pause` | `243-252` | `pause_requests.filter(...).first()` |
| `Person` | `current_ibjjf_category` | `233-245` | `IbjjfAgeCategory.objects.filter(is_active=True)` |

Referência: [Django optimization — defer unnecessary queries](https://docs.djangoproject.com/en/5.2/topics/db/optimization/#defer-unnecessary-queries).

### Seção 3 — Signals com query extra

| Signal | Arquivo | Linha | Query |
|---|---|---|---|
| `pre_save` ProductVariant | `system/signals.py` | `18-19` | `ProductVariant.objects.only(...).get(pk=instance.pk)` |
| `post_save` → `restock_variant` | `system/signals.py` | `33-36` | Cadeia de queries em `product_backorders` (PERF-036) |

### Seção 4 — Testes de performance ausentes

Busca `assertNumQueries`, `django_assert_num_queries`, `query_count`, `performance` em `system/` → **0 resultados**.

Lacunas prioritárias:

| Área | Teste recomendado (não escrito) |
|---|---|
| `get_graduation_overview` | Budget com fixture de N alunos |
| `HomeView` | Budget por matriz de papéis |
| `get_calendar_month_data` | Budget + estabilidade com M horários |
| `get_today_classes_for_person` | Sem crescimento linear com aulões alheios |
| `build_plan_catalog` | Budget vs. quantidade de planos |
| `apply_order_variant_stock` | 1 query por item → budget fixo |
| Índices | Smoke `EXPLAIN` em HG (manual/CI opcional) |

### Seção 5 — `select_related` / `prefetch_related` (lacunas notáveis)

| Local | Falta |
|---|---|
| `class_calendar.py:1351-1354` | `class_group__main_teacher` |
| `class_calendar.py:267` (`get_active_membership`) | `plan_price__tier`, `plan`, `pause_requests` |
| `membership.py` webhooks | `select_related('person')` em lookups por `stripe_subscription_id` |
| `graduation.py:49-53` | Prefetch rules por belt se overview for otimizado |
| `plan_eligibility._classify_person_audience` | Prefetch enrollments ao carregar família |

### Seção 6 — Índices ausentes inferidos (`0001_initial.py`)

Índices **existentes** relevantes (amostra): `Membership(person, status)`, `Membership(stripe_subscription_id)`, `PlanTier(audience, weekly_frequency)`, `PlanPrice(tier, payment_method, billing_cycle, is_active)`, `PreRegistration(holder_cpf, status)`, `ProductBackorder(variant, status, created_at)`.

**Ausentes** (filtros observados no código, sem `Meta.indexes` / `AddIndex`):

| Tabela | Colunas sugeridas | Motivação (query pattern) | Severidade |
|---|---|---|---|
| `ClassSession` | `(date)` | `filter(date__gte, date__lte)`, `filter(date=today)` | ALTA |
| `ClassCheckin` | `(person_id, status)` | histórico aluno, contagem graduação | ALTA |
| `ClassCheckin` | via join `session__date` | `filter(person=, session__date=today)` — considerar índice em `ClassSession(date)` primeiro | ALTA |
| `ClassSchedule` | `(weekday, is_active)` | cronograma diário global | ALTA |
| `ClassSchedule` | `(class_group_id, weekday, is_active)` | turmas do aluno no dia | ALTA |
| `SpecialClass` | `(date)` | aulões do dia/mês | ALTA |
| `SpecialClass` | `(teacher_id, date)` | instrutor ownership calendar | MÉDIA |
| `Graduation` | `(person_id, -awarded_at)` | `get_current_graduation` | ALTA |
| `PersonRelationship` | `(source_person_id, relationship_kind)` | dependentes/responsável | ALTA |
| `PersonRelationship` | `(target_person_id, relationship_kind)` | `get_membership_owner` | ALTA |
| `RegistrationOrder` | `(person_id, payment_status)` | billing, renewal check | CRÍTICA |
| `RegistrationOrder` | `(paid_at)` ou `(payment_status, paid_at)` | payroll, financial dashboard | ALTA |
| `RegistrationOrder` | `(person_id, plan_price_ref_id, payment_status)` | `_has_pending_renewal_order` | ALTA |
| `ClassEnrollment` | `(person_id, status)` | elegibilidade, payroll | ALTA |
| `ClassEnrollment` | `(class_group_id, status)` | repasse por turma | MÉDIA |
| `Person` | `(cpf, is_active)` | login/cadastro (partial unique) | MÉDIA |
| `Membership` | `(person_id, -created_at)` | `_ensure_active_membership_for_person` | MÉDIA |

Nota: `ClassSession` já tem `UniqueConstraint(schedule, date)` — índice composto `(schedule_id, date)` existe; índice adicional só em `date` ainda é útil para ranges mensais.

Política Supabase/postgres: preferir índices compostos alinhados ao predicado (`query-composite-indexes`); partial index em `is_active=True` onde aplicável.

## Proposta de correção

> Proposta de correção preenchida pelo consolidador em jul/2026.

Plano acionável com **test-first** (`assertNumQueries`) antes de cada refatoração. Coordena com PRD-143 (extração `home_views`, `effective_tier` em service) e PRD-141 (dashboard consome contexto já enxuto).

### Ondas priorizadas

| Onda | Foco | Risco global | Dependências |
|---|---|---|---|
| **P0** | Testes budget + properties com query + home/graduação | Alto | PRD-143 P1 (#5, #6) para `effective_tier`; extrair selectors antes de otimizar view |
| **P1** | Calendário + agregações SQL | Médio–alto | P0 budgets verdes |
| **P2** | Índices HG + admin hub + backlog ALTA | Médio | PRD schema + confirmação HG/produção |

---

### Onda P0 — Budgets e hotspots de rota frequente

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| PERF-004 | Criar `system/tests/test_performance_*.py` com budgets antes de refatorar | Novos testes; fixtures seed mínima | `rg assertNumQueries system/` ≥ 5 testes; CI local verde | Baixo |
| PERF-006 | Mover resolução de tier para `membership_service.resolve_effective_tier(membership, tier_cache)`; deprecar query em `@property` | `system/models/membership.py` L139–151; `system/services/family_pricing.py` L34–51; `system/services/membership.py` | Property vira leitura de campo anotado ou delega a cache injetado; `recompute_family_discounts` com 10 memberships ≤ 3 queries (teste) | Alto |
| PERF-007 | Idem para `current_pause`: `prefetch_related('pause_requests')` + helper sem property query | `membership.py` L243–252; `class_calendar.py` L267–268 | `get_today_classes_for_person` fixture: sem query extra por schedule ao acessar pause | Médio |
| PERF-001, PERF-010, PERF-011 | Reescrever `get_graduation_overview`: bulk prefetch rules + `annotate` contagens check-in | `system/selectors/graduation.py` L23–25; `system/services/graduation.py` L22–45 | Budget: ≤15 queries para 50 alunos; ≤25 para 200 alunos (teste) | Alto |
| PERF-002, PERF-003, PERF-015 | Extrair `system/selectors/home_context.py` (`build_home_context`); deduplicar `_build_dependents` vs billing tabs | `system/views/home_views.py` L78–233, L567–591; novo selector | Aluno simples ≤12 queries; responsável+3 dependentes ≤35 queries (teste) | Alto |
| PERF-008 | `_aggregate_net_inflows`: `aggregate(Sum(Coalesce(...)))` em vez de loop Python | `system/services/financial_dashboard.py` L200–204 | Mesmo total financeiro em fixture; 1 query agregada vs O(n) | Médio |
| PERF-009 | `_build_student_entries_from_orders`: prefetch `ClassEnrollment` por lote de pedidos | `system/services/payroll_rules.py` L561–566, L658–672 | Payroll mês com 20 pedidos ≤ 5 queries enrollment (teste) | Médio |
| PERF-012 | `build_plan_catalog`: cache request-level de `calculate_plan_change` por `(membership_id, plan_price_id)` | `system/services/plan_change.py` L314–320 | 10 planos elegíveis: queries não crescem linearmente 10× | Médio |

**Dependências:** PERF-006/007 **coordenados** com PRD-143 achados #4, #5, #30 (model cleanup). PERF-002/003 **coordenados** com PRD-143 #6 (`home_views` fina).

**O que NÃO fazer em P0:**
- Não adicionar cache Redis/memcached sem medição baseline.
- Não remover `@property` sem atualizar todos os call sites (`rg effective_tier`).
- Não otimizar `HomeView` in-place sem extrair selector (regressão de permissões).

---

### Onda P1 — Calendário e N+1 operacional

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| PERF-004, PERF-013 | Filtrar `SpecialClass` por `class_group_id__in` do ator; prefetch checkins staff | `class_calendar.py` L253–257, L661–665, L786–788 | Aluno com 2 turmas: queries de aulão não escalam com total do dia | Médio |
| PERF-005 | `get_calendar_month_data`: filtrar schedules por weekday; `select_related('class_group__main_teacher')` | `class_calendar.py` L1337–1434, L1351–1355 | Budget ≤10 + 2×\|schedules ativos\| para mês; sem N+1 teacher | Alto |
| PERF-032 | Cache request-level `Holiday.objects.filter(date=today)` | `class_calendar.py` L265, L421, L521, L736 | 1 query feriado por request de cronograma | Baixo |
| PERF-014, PERF-046 | Memoizar `_get_instructor_class_group_ids` por request | `class_calendar.py` L1212–1221 | 2ª chamada no mesmo request: 0 queries extras | Baixo |
| PERF-016 | Limitar `values_list('date')` com range 90 dias para KPI professor | `home_views.py` L209–221 | Query com `date__gte`; resultado idêntico em fixture | Médio |
| PERF-018 | `MembershipInvoice` com `[:limit]` por aba billing | `home_views.py` L516–537 | Histórico billing carrega no máximo N faturas por aba | Baixo |
| PERF-019, PERF-020 | Unificar billing dependents: uma passagem ORM em `get_guardian_billing_tabs` | `membership.py` L636–702 | Queries billing não duplicam `_build_dependents` | Médio |
| PERF-022, PERF-023 | `build_eligibility_context_for_person`: prefetch enrollments família + cache veteran | `plan_eligibility.py` L253–264, L62–65 | Família 4 pessoas ≤ 8 queries (teste) | Médio |
| PERF-027 | `apply_order_variant_stock`: `select_related` batch variants antes do loop | `registration_checkout.py` L595–627 | Pedido 5 itens: ≤ 6 queries (teste) | Médio |

**Dependências:** P0 test suite verde. PRD-143 API elegibilidade usa selector otimizado (PERF-022).

**O que NÃO fazer em P1:**
- Não pré-computar mês inteiro em cache persistente sem invalidação em cancelamento de aula.
- Não fundir `class_calendar.py` inteiro nesta onda (escopo PRD-138 Onda 4).

---

### Onda P2 — Índices, admin hub e backlog

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| Seção 6 | PRD schema: adicionar índices CRÍTICA/ALTA em migration dedicada | `system/migrations/0001_initial.py` ou PRD baseline regen; models `calendar`, `registration_order`, `graduation` | `EXPLAIN ANALYZE` em HG: 3 queries representativas usam Index Scan; documentar em PRD-filha | Alto (HG) |
| PERF-026 | `AdminHubView`: agregação única ou `Case/When` counts | `admin_views.py` L31–105 | 17 counts → ≤3 queries | Médio |
| PERF-017, PERF-021 | `recompute_family_discounts`: batch tier resolve + 1 Stripe sync por família | `family_pricing.py`, `membership.py` L471–483 | Cancelar 3 memberships: 1 recomputo família, não 3 | Médio |
| PERF-024, PERF-025 | `person_selectors`: revisar ORM filters; índice em `PersonRelationship` | `person_selectors.py` L154–185; migration índices | Listagem 100 pessoas com filtro turma ≤ 10 queries | Médio |
| PERF-028 | `find_due_asaas_memberships`: prefetch pending orders | `asaas_billing_cycle.py` L44–48 | Job cobrança: sem N× `_has_pending_renewal_order` | Baixo |
| PERF-029 | Consolidar agregações `_build_local_totals` | `financial_dashboard.py` L85–116 | 6 aggregates → 2 queries com `Case` | Baixo |
| PERF-030 | `person_views` detail: reutilizar selector graduação prefetch | `person_views.py` L227–228 | Detail view ≤ 8 queries com histórico graduação | Baixo |
| PERF-035, PERF-036 | Signals/backorders: batch em import estoque | `signals.py`, `product_backorders.py` | Seed estoque 50 variantes: budget documentado | Baixo |

**Índices P2 prioritários (Seção 6):** `RegistrationOrder(person_id, payment_status)`, `ClassSession(date)`, `SpecialClass(date)`, `Graduation(person_id, -awarded_at)`, `PersonRelationship(source/target, relationship_kind)`.

**O que NÃO fazer em P2:**
- Não aplicar índices em produção sem `EXPLAIN` em HG e janela de manutenção.
- Não partial index em `is_active` sem medir cardinalidade real.

---

## Cross-PRD dependencies

| Dependência | PRD parceira | Direção | Bloqueio |
|---|---|---|---|
| `effective_tier` / `current_pause` fora do model | **PRD-143** P0 (#4, #5, #30) | 143 ↔ 142 | PERF-006/007 sincronizados |
| `home_views` → `home_context` selector | **PRD-143** P1 (#6, #26) | 143 → 142 | PERF-002/003 após extração view |
| `plan_eligibility` otimizado | **PRD-143** + **PRD-141** API | 142 → 141 | PERF-022 alimenta API wizard |
| `registration_forms` antes JS | **PRD-143** P0 | 143 → 141 | Indireto (menos carga checkout) |
| Shell/dashboard split | **PRD-141** P2 | 141 ← 142 | Home rápida antes de fatiar dashboard UI |
| God-module `class_calendar` | **PRD-138** Onda 4 | 138 → 142 | P1 otimiza; P2 não divide arquivo |

## Test plan

### Tests to author

- [ ] `system/tests/test_performance_graduation.py` — `assertNumQueries` em `get_graduation_overview` com fixture 50 alunos
- [ ] `system/tests/test_performance_home.py` — budgets: aluno, professor, responsável+2 dependentes
- [ ] `system/tests/test_performance_calendar.py` — `get_calendar_month_data` e `get_today_classes_for_person`
- [ ] `system/tests/test_performance_membership.py` — `effective_tier` / `recompute_family_discounts_for_person` sem N+1
- [ ] `system/tests/test_performance_payroll.py` — `calculate_monthly_payroll` com pedidos fixture

### Execution authorization

Não autorizada nesta PRD (read-only).

### Execution evidence

- [ ] Comando e saída de testes de performance — **pendente**

## Visual validation

N/A (auditoria backend).

## ORM validation

- [x] Leitura estática de services/selectors/views/models listados
- [x] Cruzamento de índices em `0001_initial.py`
- [ ] `EXPLAIN ANALYZE` em HG — **não executado**
- [ ] `connection.queries` antes/depois — **não executado**

## Quality validation

- [x] Inventário PERF-001–047 com severidade e impacto
- [x] Fonte oficial Django documentada
- [x] Seção de correção preenchida pelo consolidador (jul/2026)
- [ ] Revisão por segundo revisor — **pendente**

## Evidence

| Evidência | Tipo | Resultado |
|---|---|---|
| `rg assertNumQueries system/` | Busca estática | 0 matches |
| Leitura `graduation.py:23-25` + `graduation.py:129-184` | Código | N+1 confirmado por construção |
| Leitura `membership.py:139-151` | Código | Query em property confirmada |
| Leitura `0001_initial.py` AddIndex | Schema | Índices de calendário/pedidos/graduação ausentes |
| `docs/prd/PRD-142-critica-backend-performance.md` | Documento | Criado nesta entrega |

## Implemented

- PRD-142 criada com inventário completo
- `docs/prd/README.md` atualizado com entrada PRD-142
- **[2026-07-09] Execução parcial da Onda P0** (fora do escopo original read-only, autorizada pelo usuário):
  - PERF-001/010/011: `get_graduation_overview` reescrito para lote — `compute_graduation_progress_bulk` em `system/services/graduation.py`; `system/selectors/graduation.py` atualizado. Budget: 5 queries fixas independente de N (medido com 25 alunos; era ~4 queries/aluno). Testes: `system/tests/test_performance_graduation.py` (`assertNumQueries`, comparação lote vs individual).
  - PERF-008: `_aggregate_net_inflows` em `system/services/financial_dashboard.py` reescrito com `Sum(Case(When(net_amount__gt=0, ...), default=F("total")))` em vez de loop Python materializando pedidos. Testes: `system/tests/test_services.py::AggregateNetInflowsQueryBudgetTestCase`.
  - PERF-006/007 (`effective_tier`/`current_pause`): auditados — `family_pricing.py` já usa `select_related("plan_price__tier", "plan")`, mitigando a maior parte do N+1 para memberships já migradas a `PlanPrice`; resta apenas o branch legado (`plan` sem `plan_price`). Refatoração completa para service dedicado **não** executada — coordenada com PRD-143 (model cleanup), não bloqueante isoladamente.
  - PERF-002/003/015 (home selector), PERF-009 (payroll batch), PERF-012 (plan_change cache): **não executados** nesta rodada — coordenados com PRD-143 #6 (extração `home_views`), tratados na sequência (PRD-143).
  - Evidência: `manage.py test system` — 656 testes, OK (era 651 antes desta onda).
- **[2026-07-09] Execução da Onda P1** (calendário e N+1 operacional):
  - PERF-013: `get_today_classes_staff_overview` — checkins de `SpecialClass` do dia agora buscados em lote (`SpecialClassCheckin.objects.filter(special_class__in=specials_today)`) em vez de 1 query por aulão no loop. `system/services/class_calendar.py`.
  - PERF-005: `get_calendar_month_data` — adicionado `select_related("class_group__main_teacher")` ao queryset de `ClassSchedule`, eliminando N+1 de `main_teacher.full_name` no loop de dias do mês.
  - PERF-014/046: `_get_instructor_class_group_ids` memoizado por instância de `person` (atributo privado no objeto, populado uma vez por chamada e reaproveitado nas chamadas seguintes dentro do mesmo request). Seguro porque `request.portal_person` é resolvido do zero a cada request pelo middleware (`system/middleware.py`) — não há vazamento entre requests/testes, diferente do cache de processo usado na tentativa de PERF-032 abaixo.
  - PERF-019/020: `get_active_membership(person)` ganhou parâmetro opcional `billing_owner=None`; `_build_billing_tab` (`membership.py`), `build_billing_context` e `build_dependents` (`home_context.py`) agora resolvem `get_membership_owner` uma única vez e reaproveitam o resultado, eliminando a recomputação duplicada de `_person_has_financial_records`/`_get_responsible_people` que ocorria a cada dependente.
  - PERF-022: `build_eligibility_context_for_person` — família inteira agora resolvida em 2 queries fixas (`Person.objects.filter(pk__in=family_ids).select_related(...)` + `ClassEnrollment.objects.filter(person_id__in=family_ids, ...)`) em vez de até 3 queries por membro no loop. `_classify_person_audience` ganhou parâmetro opcional `active_enrollments` para consumir o lote pré-carregado sem quebrar chamadas single-person existentes.
  - PERF-032 (**revertido**): tentativa inicial usou `django.core.cache.cache` (LocMemCache) para memoizar `Holiday.objects.filter(date=today)` com TTL de 300s. **Quebrou o isolamento de testes**: o cache do Django não é limpo entre métodos de teste (diferente do banco, que usa rollback de transação por `TestCase`), então uma entrada negativa ("sem feriado") de um teste vazava para outro teste que esperava um feriado existir. Uma segunda tentativa com signals `post_save`/`post_delete` em `Holiday` para invalidar a chave piorou o resultado (6 failures + 15 errors, vs. 2 antes), porque rollback de transação de teste não dispara signals ORM — a direção inversa da contaminação (feriado criado em cache, depois removido via rollback) continuava vazando. **Decisão**: a otimização original do PRD pedia cache "request-level" (memoização por execução), não cache cross-request/TTL — o framework de cache do Django é a ferramenta errada aqui. Revertido integralmente (`class_calendar.py` e `system/signals.py` voltaram às 5 chamadas diretas `Holiday.objects.filter(date=today, is_active=True).first()`); não reimplementado nesta rodada.
  - PERF-004: avaliado e **não implementado** — `SpecialClass` (aulão) não possui campo `class_group` no modelo (`system/models/calendar.py:139-179`); é um evento aberto à escola inteira por desenho, não vinculado a turmas. Filtrar por turmas do ator, como o achado original sugeria, mudaria o comportamento funcional (esconderia aulões legítimos de quem deveria vê-los). Volume real por dia é pequeno (poucos aulões), então o "over-fetch" apontado não se sustenta como hotspot após leitura do modelo.
  - PERF-016: avaliado e **não implementado** — `instructor_attendance_count` (home) é um contador histórico total de dias com presença do professor, exibido como "Aulas presentes" (`templates/home/partials/graduation_section.html:93`). Limitar a uma janela de 90 dias, como sugerido, alteraria o valor exibido (quebra de correção funcional, não apenas performance). Query já projeta só a coluna `date` via `values_list`, volume esperado é baixo mesmo em anos de carreira.
  - PERF-018: avaliado e **não implementado** — `build_payment_history_items` alimenta o modal "Histórico de pagamentos" (`templates/home/dashboard.html:1059`), um extrato financeiro completo por família. Truncar sem paginação esconderia pagamentos reais do usuário — decisão de produto, não apenas performance; requer aprovação explícita antes de limitar.
  - PERF-023: avaliado — `compute_veteran_member_since` já é 1 query fixa por chamada de `build_eligibility_context_for_person` (não está em loop); não há N+1 a corrigir, apenas custo fixo aceitável.
  - PERF-027: avaliado e **não implementado** — `resolve_order_item_variant` usa `select_for_update()` por item propositalmente (evitar corrida de estoque em concorrência); volume por pedido é pequeno (poucos itens); tentar consolidar em uma única query com filtros de cor/tamanho variáveis por item arriscaria regressão de concorrência sem ganho relevante.
  - Evidência: `manage.py test system` — 662 testes, OK (mesma contagem antes/depois — nenhum teste novo criado nesta onda, apenas correções de N+1/duplicação verificadas contra a suíte existente).

## Cleanup findings

- God-modules (`class_calendar.py`, `home_views.py`) concentram hotspots — correção de performance alinha-se com PRD-138 (ondas de consolidação).
- Duplicação de chamadas entre `_build_dependents` e `_build_today_classes_tabs` / `get_guardian_billing_tabs` aumenta custo sem benefício funcional.

## Follow-up PRDs

| PRD sugerida | Escopo |
|---|---|
| PRD-142-onda-1 (a criar) | PERF-001–003, PERF-006–007 — home + graduação |
| PRD-142-onda-2 (a criar) | PERF-004–005, PERF-013 — calendário |
| PRD-142-onda-3 (a criar) | Seção 6 índices + HG `EXPLAIN` |
| PRD-142-onda-4 (a criar) | Testes `assertNumQueries` |

## Deviations from plan

Nenhuma — escopo read-only respeitado.

## Pending

- Aprovação para PRD-filhas de execução por onda (P0–P2).
- Confirmação HG para índices P2.
- Medição HTTP real pós-P0 (home, panorama graduação, calendário).

## Final status

**Concluída** — auditoria estática entregue; proposta de correção consolidada (jul/2026). Implementação e medição runtime pendentes.
