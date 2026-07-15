# PRD-143: Crítica MVT — views, models e forms

## Summary

Auditoria read-only altamente crítica da camada MVT Django (`system/views/`, `system/models/`, `system/forms/`) em jul/2026. O escopo cobre 57 arquivos Python (22 views, 21 models, 14 forms). Conclusão: **violações sistemáticas de separação MVT** — god-modules, regra de negócio em views/forms/models, catálogo dual de planos, caminhos paralelos de cadastro incompatíveis com PRD-040, validação triplicada e barrel exports incompletos. **Nenhum código é alterado nesta PRD**; consolidação fica para PRD consolidadora.

## Demand type

Revisão arquitetural read-only (crítica MVT) + roteamento de dívida. Complementa PRD-138 e PRD-139 com foco exclusivo em views, models e forms.

## Current problem

A camada HTTP e de entrada de dados concentra orquestração que deveria viver em `services/`. Forms com 600–1100+ linhas misturam validação, elegibilidade de plano e materialização de domínio. Models expõem dezenas de `@property` com queries e regras de precificação. Views como `home_views.py` e `dependent_views.py` montam contexto e executam checkout sem delegação fina.

### Métricas do escopo

| Camada | Arquivos | Linhas (aprox.) | God-modules (≥400L) |
|---|---|---|---|
| `system/views/` | 22 | ~5.400 | `home_views` (656), `calendar_views` (548), `person_views` (538), `auth_views` (482), `dependent_views` (401), `product_views` (364) |
| `system/forms/` | 14 | ~4.100 | `registration_forms` (1124), `person_forms` (734), `dependent_forms` (615) |
| `system/models/` | 21 | ~3.200 | `plan` (437), `membership` (413), `person` (334) |

## Goal

Registrar inventário crítico arquivo a arquivo, os 30 achados priorizados com severidade e evidência, e proposta de correção em ondas P0–P3 (jul/2026).

## Context Ledger

### Files read in full

- `system/views/` — 22 módulos (incl. `home_views.py`, `auth_views.py`, `person_views.py`, `dependent_views.py`, `calendar_views.py`, `__init__.py`)
- `system/models/` — 21 módulos (incl. `plan.py`, `membership.py`, `person.py`, `class_membership.py`, `__init__.py`)
- `system/forms/` — 14 módulos (incl. `registration_forms.py`, `person_forms.py`, `dependent_forms.py`, `__init__.py`)
- `system/urls.py` (cruzamento views ↔ rotas)
- `system/services/pre_registration.py` (finalize → `form.save()`)
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` (contrato)
- `docs/prd/PRD-097-views-calendario-orfas-sem-rota.md`, `PRD-138`, `PRD-139`

### Adjacent files consulted

- `system/services/registration.py`, `registration_validation.py`
- `system/views/payment_views.py`, `plan_change_views.py`
- `docs/PRD-STANDARD.md`, `docs/prd/README.md`

### Internet / official documentation

- [Django design philosophies — Loose coupling](https://docs.djangoproject.com/en/5.2/misc/design-philosophies/#loose-coupling) — camadas desacopladas; lógica de domínio não pertence a views nem a forms como orquestradores.
- [Django models — Keep models focused](https://docs.djangoproject.com/en/5.2/topics/db/models/) — models representam dados e invariantes simples; queries em loop via `@property` são anti-padrão.

### Context7 / MCPs / tools verified

- `rg`, contagem de linhas PowerShell, leitura integral dos módulos citados.

### Limitations found

- Auditoria não reexecutou suíte de testes (read-only).
- Services/selectors/JS citados apenas quando acoplam views/forms/models.
- Proposta de correção **consolidada** (jul/2026) — ver seção dedicada.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`

## Understanding approved

Solicitação explícita: auditoria read-only, persona arquiteto MVT implacável, criar PRD-143 e atualizar índice. **Não implementar código.**

## Execution prompt

### Persona

Arquiteto MVT implacável — apenas criticar violações, acochamento e god-classes.

### Action

Inventário crítico + top 30 achados + PRD template completo.

### Context

LV JIU JITSU, Django 5.2, fluxo canônico PRD-040.

### Constraints

- Read-only.
- Evidência por arquivo/linha.
- Placeholder de correção substituído por ondas P0–P3 (jul/2026).

### Acceptance criteria

- [ ] Inventário dos 57 arquivos com veredito por arquivo.
- [ ] Top 30 achados com severidade (CRÍTICA/ALTA/MÉDIA) e evidência.
- [ ] `docs/prd/README.md` atualizado com PRD-143.
- [ ] Seção `## Proposta de correção (pendente consolidador)` presente.
- [ ] Nenhum arquivo de código alterado.

### Expected evidence

- Este documento + diff em `docs/prd/`.

### Output format

PRD-STANDARD completo.

## Scope

- `system/views/**/*.py`
- `system/models/**/*.py`
- `system/forms/**/*.py`
- `docs/prd/PRD-143-*.md`, `docs/prd/README.md`

## Out of scope

- Implementação de refatoração.
- `services/`, `selectors/`, templates, static, tests (exceto citação de acoplamento).
- Execução de testes nesta entrega.

## Impacted files

- `docs/prd/PRD-143-critica-views-models-forms-mvt.md` (novo)
- `docs/prd/README.md` (índice)

## Risks and edge cases

- Remover `form.save()` → `create_portal_registration` sem substituir `finalize_pre_registration` quebra cadastro.
- Unificar catálogo `PlanTier`/`PlanPrice` exige migração de `Membership.plan` legado.
- `home_views` concentra permissões — extrair sem regressão em home split (PRD-092).

## Rules and constraints

- AGENTS.md: regra de negócio em `services/`, views finas, forms só validação.
- PRD-040: pagamento antes de `Person`; estado pré-finalização em `PreRegistration`.

## Plan

### Onda P0 — Cadastro e API elegibilidade (bloqueia PRD-141)
- [ ] #1, #10: fatiar `registration_forms.py`; validação única em `registration_validation.py`
- [ ] #2: `RegistrationFinalizeService`; remover `form.save()` do finalize
- [ ] #3, #15, #29: eliminar `pending_registration_person_id`; unificar checkout PreRegistration
- [ ] #7: `dependent_registration_service`; view fina
- [ ] API JSON elegibilidade (desbloqueia PRD-141 C-01)
- [ ] Testes HTTP contrato API vs `plan_eligibility.py`

### Onda P1 — Catálogo, home, membership
- [ ] #4, #8, #28: fluxos públicos só `pp:` (PlanPrice)
- [ ] #5, #30 + PRD-142: `effective_tier`/`current_pause` em service
- [ ] #6, #14, #26: `home_dashboard_service` + `selectors/home_context.py`
- [ ] #13: `plan_change_service` transacional
- [ ] #9, #16, #17, #18: PersonForm DTO; ibjjf selector; pricing fora do model

### Onda P2 — Forms finos e higiene
- [x] #11: ClassGroup → `services/class_management.py`. #12: avaliado, já era service-thin
- [x] #19, #20, #21: barrel `views/__init__.py` esvaziado (código morto); aliases já removidos; mixin único em `portal_mixins.py` (corrigiu divergência de capabilities)
- [x] #23, #24: `get_instructor_class_group_ids` público; `registration_common.py` criado
- [x] #22: avaliado — já era fonte única de elegibilidade de turma

### Onda P3 — Legado
- [ ] #4, #8, #28: deprecar SubscriptionPlan admin; backfill HG
- [ ] #27: reduzir barrel models

## Inventário crítico — `system/models/` (21 arquivos)

| Arquivo | L | Veredito | Crítica principal |
|---|---|---|---|
| `__init__.py` | 240 | MÉDIA | Barrel gigante reexporta domínio inteiro; favorece imports circulares (`plan` ↔ `membership`). |
| `common.py` | 6 | OK | `TimeStampedModel` — adequado. |
| `person.py` | 334 | ALTA | `@property current_ibjjf_category` faz query; `can_enroll_in_class_group` consulta `class_enrollments`; regra de papel espalhada. |
| `plan.py` | 437 | CRÍTICA | Catálogo dual (`SubscriptionPlan` + `PlanTier`/`PlanPrice`); `PlanPrice.save()` recalcula preço e `_guard_immutability()`; `@property is_referenced_by_membership` query. |
| `membership.py` | 413 | CRÍTICA | FK dual `plan` + `plan_price`; 12+ `@property effective_*`; `effective_tier` query; `current_pause` filter; `recompute_billed_price()` é regra financeira no model. |
| `registration_order.py` | 257 | MÉDIA | Properties de display; aceitável se read-only sem query. |
| `pre_registration.py` | 127 | MÉDIA | Estado wizard; properties leves — OK como persistência. |
| `class_membership.py` | 152 | ALTA | `clean()`/`save(full_clean)` com regra de tipo e elegibilidade IBJJF; função module-level com query em `get_class_group_eligibility_error`. |
| `class_group.py` | 36 | MÉDIA | `clean()` — invariante aceitável. |
| `class_schedule.py` | 49 | OK | Schema. |
| `calendar.py` | 209 | MÉDIA | Properties em sessões/check-in; verificar N+1 em listagens. |
| `graduation.py` | 145 | BAIXA | Property simples. |
| `product.py` | 85 | MÉDIA | Properties de estoque/display. |
| `product_backorder.py` | 84 | BAIXA | Properties de status. |
| `category.py` | 36 | OK | Schema + `matches_age`. |
| `coupon.py` | 35 | OK | Schema. |
| `asaas.py` | 168 | BAIXA | Property display. |
| `audit.py` | 24 | OK | Schema. |
| `trial_access.py` | 40 | BAIXA | Properties leves. |
| `request_workflows.py` | 171 | OK | Schema de solicitações. |
| `membership_timeline.py` | 55 | OK | Schema de eventos. |

## Inventário crítico — `system/forms/` (14 arquivos)

| Arquivo | L | Veredito | Crítica principal |
|---|---|---|---|
| `__init__.py` | 50 | OK | Barrel forms — incompleto vs módulos (sem `plan_tier_forms`). |
| `registration_forms.py` | 1124 | CRÍTICA | God-form: validação de 7 perfis, plano, turmas, materiais, operacional; `save()` → `create_portal_registration()`; duplica `registration_validation.py`. |
| `person_forms.py` | 734 | CRÍTICA | God-form admin; `PersonForm.save()` orquestra enrollments, payroll, papéis operacionais; validação martial art duplicada com registration. |
| `dependent_forms.py` | 615 | CRÍTICA | God-form; importa constantes de `registration_forms`; elegibilidade de plano reimplementada; sem `save()` mas view orquestra tudo. |
| `class_forms.py` | 300 | ALTA | `ClassGroupForm.save()` sincroniza `ClassInstructorAssignment` — domínio no form. |
| `class_request_forms.py` | 329 | MÉDIA | Validação pesada; decisão deve estar em service. |
| `access_request_forms.py` | 163 | ALTA | `AdministrativeAccessRequestForm.save()` → `create_administrative_access_request()`. |
| `plan_forms.py` | 227 | MÉDIA | CRUD legado `SubscriptionPlan`. |
| `plan_tier_forms.py` | 168 | MÉDIA | CRUD novo catálogo — paralelo a `plan_forms`. |
| `graduation_forms.py` | 144 | OK | CRUD enxuto. |
| `product_forms.py` | 103 | OK | CRUD + carrinho. |
| `auth_forms.py` | 80 | OK | Autenticação. |
| `membership_pause_forms.py` | 13 | OK | Delegação mínima. |
| `category_forms.py` | 24 | OK | CRUD. |

## Inventário crítico — `system/views/` (22 módulos)

| Arquivo | L | Veredito | Crítica principal |
|---|---|---|---|
| `__init__.py` | 240 | ALTA | Barrel parcial: omite `dependent_views`, `admin_views`, `plan_tier_views`, `membership_pause_views`, `access_request_views`, `class_request_views`, `stripe_views`; exporta aliases mortos `InstructorCalendarView`/`StudentScheduleView`. |
| `portal_mixins.py` | 34 | OK | Mixins de auth — adequado. |
| `home_views.py` | 656 | CRÍTICA | God-module: `HomeView.get_context_data` ~160L, 18 helpers, ORM direto (`ClassSession`, `SpecialClass`), billing, payroll, dependentes, permissões. |
| `auth_views.py` | 482 | CRÍTICA | Wizard + materiais + finalização; caminho legado `pending_registration_person_id`; `MaterialsCheckoutView` cria pedidos na view; `FinalizeRegistrationView` ativa Person na view. |
| `person_views.py` | 538 | ALTA | God-module CRUD; mixins duplicados (`AdministrativeRequiredMixin`); `VeteranPlanDecisionView` com regra na view. |
| `dependent_views.py` | 401 | CRÍTICA | `DependentRegistrationView.post` ~120L orquestra pagamento, materiais, finalize — paralelo ao wizard PRD-040. |
| `calendar_views.py` | 548 | ALTA | 16 classes; aliases órfãos no barrel; import de `_get_instructor_class_group_ids` (privado); queries na view. |
| `payment_views.py` | 258 | ALTA | `DeferPaymentView` reintroduz `pending_registration_person_id` (Person antes do fluxo PreRegistration); lógica de sessão na view. |
| `product_views.py` | 364 | ALTA | Loja + backorder + pedidos; mistura admin e portal. |
| `plan_change_views.py` | 152 | ALTA | `PlanChangeSelectView.post` cancela Stripe e `membership.save()` na view; deveria ser service transacional. |
| `asaas_views.py` | 272 | MÉDIA | Webhook fino; `AdministrativeRequiredMixin` **duplicado** (cópia de `person_views`). |
| `billing_admin_views.py` | 168 | MÉDIA | Actions delegam parcialmente a services — aceitável. |
| `graduation_views.py` | 138 | MÉDIA | `_AdministrativeRequiredMixin` triplicado. |
| `class_views.py` | 172 | MÉDIA | Usa services — padrão melhor. |
| `category_views.py` | 98 | OK | CRUD fino. |
| `plan_views.py` | 97 | MÉDIA | CRUD legado planos. |
| `plan_tier_views.py` | 185 | MÉDIA | CRUD paralelo PlanTier — fora do barrel. |
| `admin_views.py` | 136 | MÉDIA | Hub admin — fora do barrel. |
| `access_request_views.py` | 182 | MÉDIA | `form.save()` na view — fora do barrel. |
| `class_request_views.py` | 210 | MÉDIA | Fila de solicitações — fora do barrel. |
| `membership_pause_views.py` | 180 | MÉDIA | Pausa — fora do barrel. |
| `stripe_views.py` | 39 | OK | Webhook fino. |

## Top 30 achados (severidade + evidência)

| # | Sev | Achado | Evidência |
|---|---|---|---|
| 1 | CRÍTICA | **God-form `registration_forms.py` (1124L)** concentra validação de todos os perfis, elegibilidade, turmas, materiais e checkout. | `PortalRegistrationForm.clean()` L352–375 encadeia 10+ `_clean_*`; arquivo inteiro. |
| 2 | CRÍTICA | **`PortalRegistrationForm.save()` materializa domínio** via `create_portal_registration()` — violação MVT; único caminho de `finalize_pre_registration`. | `registration_forms.py` L377–378; `pre_registration.py` L536. |
| 3 | CRÍTICA | **Caminho legado PRD-040**: `pending_registration_person_id` ainda ativo — Person existe antes da finalização canônica. | `auth_views.py` L392–399, L502–518; `payment_views.py` L129–130; `MaterialsCheckoutView` L392–428. |
| 4 | CRÍTICA | **FK dual em `Membership`**: `plan` (legado) + `plan_price` (novo) com 8 `effective_*` properties — fonte de inconsistência em billing. | `membership.py` L35–49, L139–205. |
| 5 | CRÍTICA | **`Membership.effective_tier` executa query** em `@property` — N+1 em listagens e regra no model. | `membership.py` L146–150. |
| 6 | CRÍTICA | **God-module `home_views.py`**: view monta dashboard inteiro com ORM, billing, payroll, graduação, dependentes. | `HomeView.get_context_data` L78–233; helpers L302–725. |
| 7 | CRÍTICA | **`DependentRegistrationView.post` orquestra checkout** (plan, materiais, family) — segundo wizard paralelo ao PRD-040. | `dependent_views.py` L60–181. |
| 8 | CRÍTICA | **Catálogo dual de planos** em forms e views: `resolve_catalog_plan` aceita `sp:` e `pp:` em todo fluxo. | `dependent_views.py` L98–100; `plan_change_views.py` L59–60; `plan.py` + `plan_forms` vs `plan_tier_forms`. |
| 9 | ALTA | **`PersonForm.save()` orquestra domínio**: enrollments, payroll, papéis operacionais. | `person_forms.py` L681–702. |
| 10 | ALTA | **Validação triplicada de cadastro**: `PortalRegistrationForm`, `registration_validation.py`, JS wizard. | `auth_views.py` L229–232 (`RegistrationStepValidationView`); `registration_forms.py` vs `registration_validation.py` `STEP_REQUIRED_FIELDS`. |
| 11 | ALTA | **`ClassGroupForm.save()` sincroniza instrutores** — escrita transacional no form. | `class_forms.py` L88–120. |
| 12 | ALTA | **`AdministrativeAccessRequestForm.save()` cria solicitação** — domínio no form. | `access_request_forms.py` L125–139. |
| 13 | ALTA | **`PlanChangeSelectView.post` altera membership e cancela Stripe** na view sem service único. | `plan_change_views.py` L75–101. |
| 14 | ALTA | **`ClientProfileDeactivateView` com `transaction.atomic` na view** — deveria ser `deactivate_portal_person()`. | `home_views.py` L279–292. |
| 15 | ALTA | **`MaterialsCheckoutView` cria pedidos e redireciona gateway** na view (dois caminhos: PreRegistration + Person legado). | `auth_views.py` L386–472. |
| 16 | ALTA | **`Person.current_ibjjf_category` query em property** — duplica selector/service de elegibilidade. | `person.py` L233–245. |
| 17 | ALTA | **`PlanPrice.save()` com regra de precificação e imutabilidade** — lógica financeira no model. | `plan.py` L409–458. |
| 18 | ALTA | **`Membership.recompute_billed_price()`** — desconto família no model, não em service. | `membership.py` L207–218. |
| 19 | ALTA | **Barrel `views/__init__.py` incompleto** — 7 módulos importados só em `urls.py`; risco de views “fantasma”. | Compare `urls.py` imports vs `views/__init__.py`. |
| 20 | ALTA | **Aliases órfãos no barrel**: `InstructorCalendarView`, `StudentScheduleView` = `CalendarView` sem rota dedicada. | `calendar_views.py` L104, L248; `views/__init__.py` L4, L152. |
| 21 | ALTA | **`AdministrativeRequiredMixin` duplicado** em `person_views.py` e `asaas_views.py` (e variante em `graduation_views`). | `person_views.py` L52; `asaas_views.py` L233; `graduation_views.py` L27. |
| 22 | MÉDIA | **`ClassEnrollment.clean/save(full_clean)`** — regra de matrícula no model (aceitável como invariante, mas duplica form/service). | `class_membership.py` L162–168. |
| 23 | MÉDIA | **`calendar_views` importa função privada** `_get_instructor_class_group_ids` — acoplamento a implementation detail. | `calendar_views.py` L88. |
| 24 | MÉDIA | **`dependent_forms` importa de `registration_forms`** — acoplamento entre god-forms. | `dependent_forms.py` L4–8. |
| 25 | MÉDIA | **`PortalRegisterView.form_valid` não chama `form.save()`** — `save()` do form só no finalize; API confusa e morta para wizard intermédio. | `auth_views.py` L110–150 vs `registration_forms.py` L377. |
| 26 | MÉDIA | **`home_views` ORM direto** para contagem de presença do professor — deveria ser selector. | `home_views.py` L210–222. |
| 27 | MÉDIA | **`models/__init__.py` barrel 240L** — import circular `membership` ↔ `plan` via lazy imports em properties. | `plan.py` L462; `membership.py` L144. |
| 28 | MÉDIA | **CRUD paralelo de planos**: `plan_views` + `plan_forms` (legado) vs `plan_tier_views` + `plan_tier_forms` (novo). | Dois módulos admin ativos. |
| 29 | MÉDIA | **`FinalizeRegistrationView` ativa Person/PortalAccount na view** — duplica lógica de `finalize_pre_registration`. | `auth_views.py` L494–533 vs `pre_registration.py` L501+. |
| 30 | MÉDIA | **`Membership.current_pause` property com filter** — query por acesso em templates/serialização. | `membership.py` L242–253. |

## Proposta de correção

> Proposta de correção preenchida pelo consolidador em jul/2026.

Plano acionável alinhado a PRD-138 Ondas 2 e 4. **Bloqueia PRD-141 P1** (remoção elegibilidade JS) e **desbloqueia PRD-142 P0** (home selector + `effective_tier`).

### Ondas priorizadas

| Onda | Foco | Risco global | Dependências |
|---|---|---|---|
| **P0** | Cadastro único + validação autoritativa + API elegibilidade | Alto | PRD-040, PRD-081; **antes** de PRD-141 C-01 |
| **P1** | Catálogo único + views finas + home selector | Alto | P0 estável; coordena PRD-142 PERF-002/006 |
| **P2** | Forms sem `save()` domínio + higiene barrel/mixins | Médio | P1 |
| **P3** | Model cleanup residual + CRUD planos legado | Médio–alto | Migração memberships ativas |

---

### Onda P0 — Cadastro canônico e fonte única de validação

| # | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| 1, 10 | Fatiar `PortalRegistrationForm` em forms por etapa (`ProfileStepForm`, `PlanStepForm`, …); mover `clean()` encadeado para `registration_validation.py` único | `registration_forms.py` L352–375; `registration_validation.py`; novos `forms/registration_*_forms.py` | `registration_forms.py` < 400L; `rg STEP_REQUIRED_FIELDS` uma única definição; testes wizard etapa a etapa verdes | Alto |
| 2 | `finalize_pre_registration` chama `RegistrationFinalizeService.create_from_pre_registration()` — **não** `form.save()` | `pre_registration.py` L536; novo `services/registration_finalize.py`; `registration_forms.py` L377–378 | `PortalRegistrationForm.save()` removido ou raise `NotImplementedError`; finalize cria Person+Membership via service; `test_registration_*` verdes | Alto |
| 3, 15, 29 | Eliminar `pending_registration_person_id`; unificar `MaterialsCheckoutView` e `DeferPaymentView` só em `PreRegistration` | `auth_views.py` L392–472, L494–533; `payment_views.py` L129–130 | `rg pending_registration_person_id` → 0; fluxo sandbox pagamento→finalize sem Person prévia | Alto |
| 7 | `DependentRegistrationView.post` delega a `dependent_registration_service` espelhando PRD-040 (mesmo contrato que wizard público) | `dependent_views.py` L60–181; novo `services/dependent_registration.py` | View < 80L POST; paridade testes dependente vs wizard titular | Alto |
| — | **API read-model elegibilidade** (JSON): expor `build_eligibility_context_for_person` + catálogos filtrados | Novo `views/registration_api_views.py` ou action em `auth_views`; `selectors/plan_eligibility.py` | Contrato JSON documentado; teste HTTP = selector Python; **desbloqueia PRD-141 C-01** | Alto |
| 25 | Documentar que `form.save()` não é usado no wizard intermediário; `save_pre_registration_from_form` é o único caminho | `auth_views.py` L110–150; docstring forms | Sem ambiguidade em code review | Baixo |

**Dependências:** PRD-138 Onda 2 (PRD-081, PRD-129). PRD-141 **não** remove JS elegibilidade até API + validação P0 em produção local.

**O que NÃO fazer em P0:**
- Não remover `registration_forms.py` inteiro de uma vez (quebra finalize).
- Não expor elegibilidade no JS antes da API estar coberta por testes.
- Não apagar caminho legado sem `rg` zerado + testes pagamento.

---

### Onda P1 — Catálogo único, home fina e membership

| # | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| 4, 8, 28 | Checkout/wizard aceita só `pp:` (`PlanPrice`); `resolve_catalog_plan` rejeita `sp:` em fluxos públicos | `dependent_views.py` L98–100; `plan_change_views.py`; `registration_checkout.py` | Cadastro e dependente só `PlanTier`/`PlanPrice`; testes `LegacyPlan*` isolados ou removidos | Alto |
| 5, 30 | `Membership.effective_tier` e `current_pause`: resolver em `membership_service` com annotate/prefetch; properties delegam ou viram campos | `membership.py` L139–151, L242–253; `services/membership.py` | **Sincronizar PRD-142 PERF-006/007**; family_pricing sem N+1 | Alto |
| 6, 14, 26 | Extrair `home_dashboard_service.build_context(user)` + `selectors/home_context.py`; view só HTTP | `home_views.py` L78–233, L279–292, L302–725 | `HomeView.get_context_data` < 40L; **PRD-142 PERF-002** budgets atingidos | Alto |
| 13 | `PlanChangeSelectView.post` → `plan_change_service.apply_change()` transacional | `plan_change_views.py` L75–101; `services/plan_change.py` | Stripe cancel + membership update em atomic; teste mock Stripe | Médio |
| 17, 18 | `PlanPrice.save()` imutabilidade → `plan_management_service`; `recompute_billed_price` → `family_pricing` | `plan.py` L409–458; `membership.py` L207–218 | Models sem escrita de regra financeira; testes pricing verdes | Médio |
| 16 | `Person.current_ibjjf_category` → `plan_eligibility.get_ibjjf_category(person)` (sem query em property) | `person.py` L233–245; `selectors/plan_eligibility.py` | Property removida ou cache-only; listagem pessoas sem query extra | Médio |
| 9 | `PersonForm.save()` retorna DTO; view chama `person_admin_service.update_person()` | `person_forms.py` L681–702; `person_views.py` | Form sem `create`/`update` ORM direto | Médio |

**Dependências:** P0 API elegibilidade. PRD-142 extrai selectors em paralelo (mesmo módulo `home_context.py`).

**O que NÃO fazer em P1:**
- Não dropar FK `Membership.plan` antes de backfill `plan_price_id` em HG.
- Não fatiar `home_views` sem matriz de papéis (aluno+professor+admin+responsável).

---

### Onda P2 — Forms finos e higiene HTTP

| # | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| 11 | `ClassGroupForm.save()` → `class_group_service.sync_instructors()` | `class_forms.py` L88–120 | Form valida só; service transacional | Médio |
| 12 | `AdministrativeAccessRequestForm.save()` → service | `access_request_forms.py` L125–139 | Padrão DTO + service | Baixo |
| 19, 20 | Completar `views/__init__.py` com todos módulos de `urls.py` **ou** eliminar barrel; remover aliases `InstructorCalendarView`/`StudentScheduleView` | `views/__init__.py`; `calendar_views.py` L104, L248 | `rg InstructorCalendarView` só em testes de remoção ou 0; imports urls explícitos | Baixo |
| 21 | `AdministrativeRequiredMixin` único em `portal_mixins.py` | `person_views.py` L52; `asaas_views.py` L233; `graduation_views.py` L27 | 1 definição; 3 cópias removidas | Baixo |
| 24 | Quebrar acoplamento `dependent_forms` → `registration_forms`; shared em `forms/registration_common.py` | `dependent_forms.py` L4–8 | Sem import de god-form | Médio |
| 23 | `calendar_views` não importa `_get_instructor_class_group_ids` privado; usar selector público | `calendar_views.py` L88; `selectors/` ou `class_calendar` API pública | Import de símbolo público documentado | Baixo |
| 22 | `ClassEnrollment.clean` alinhado a service único de matrícula | `class_membership.py` L162–168 | Uma fonte elegibilidade turma | Médio |

**O que NÃO fazer em P2:**
- Não reexportar views mortas “por compatibilidade”.
- Não mover validação de volta para templates/JS.

---

### Onda P3 — Deprecação legado (pós-migração dados)

| # | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| 4, 8, 28 | Remover `SubscriptionPlan` de admin ativo; deprecar `plan_views`/`plan_forms` | `plan_views.py`, `plan_forms.py`, `plan.py` | `rg SubscriptionPlan` só em migrations/histórico; memberships 100% `plan_price` | Alto (HG) |
| 27 | Reduzir `models/__init__.py` barrel; lazy imports onde necessário | `models/__init__.py` L240 | Sem import circular membership↔plan em runtime comum | Médio |

**Dependências:** PRD-138 Onda 5; confirmação HG backfill memberships.

---

## Cross-PRD dependencies

| Dependência | PRD parceira | Direção | Bloqueio |
|---|---|---|---|
| API elegibilidade → remover JS | **PRD-141** P1 (C-01, C-07) | 143 → 141 | P0 API obrigatória |
| `registration_forms` antes regra JS | **PRD-141** P1 | 143 → 141 | P0 forms fatiados |
| `home_context` selector | **PRD-142** P0 (PERF-002/003) | 143 ↔ 142 | Mesmo módulo `selectors/home_context.py` |
| `effective_tier` service | **PRD-142** P0 (PERF-006/007) | 143 ↔ 142 | P1 sincronizado |
| `base.html` shell | **PRD-141** P0 | 141 → 143 | Templates wizard após shell |
| Fluxo único cadastro | **PRD-138** Onda 2 | 138 → 143 | P0 = Onda 2 parcial |
| Catálogo `PlanTier` only | **PRD-138** Onda 2 / PRD-129 | 138 → 143 | P1 |
| Performance elegibilidade API | **PRD-142** P1 (PERF-022) | 142 → 143 | API não pode N+1 |

## Test plan

### Tests to author

- N/A nesta entrega (read-only).

### Execution authorization

- Não autorizado — documentação apenas.

### Execution evidence

- N/A.

## Visual validation

- N/A.

## ORM validation

- N/A.

## Quality validation

- [x] Inventário 57 arquivos completo.
- [x] Top 30 com severidade e evidência.
- [x] Fonte oficial Django citada.
- [x] Proposta de correção detalhada (ondas P0–P3, jul/2026)
- [ ] Testes de regressão pós-correção (futuro, por onda)

## Evidence

| Item | Evidência |
|---|---|
| Contagem de linhas | PowerShell `Measure-Object` em jul/2026 — valores na tabela de inventário. |
| Achados 1–30 | `rg` + leitura integral dos módulos citados. |
| Rotas vs barrel | `system/urls.py` vs `system/views/__init__.py`. |
| PRD-040 | Caminho `pending_registration_person_id` ainda referenciado em 3+ views. |

## Implemented

- PRD-143 criada com inventário e top 30.
- `docs/prd/README.md` atualizado.
- **[2026-07-09] Onda P0 executada** (fora do escopo original read-only, autorizada pelo usuário):
  - **API elegibilidade**: nova `RegistrationEligibilityView` (`POST /cadastro/elegibilidade/`, rota `system:registration-eligibility`) expõe `build_eligibility_context_for_registration` + `get_eligible_plan_prices` via JSON. `system/services/registration_validation.py::build_eligibility_context_from_wizard_data` faz o parsing dos dados brutos do wizard. Contrato testado byte-a-byte contra o selector em `system/tests/test_registration_eligibility_api.py` (5 testes). Mudança 100% aditiva — desbloqueia PRD-141 C-01/C-07 sem alterar `register.js` nesta entrega.
  - **#2 (form.save() → service)**: `PortalRegistrationForm.save()` agora levanta `NotImplementedError`; `finalize_pre_registration` chama `create_portal_registration(form.cleaned_data)` diretamente. `system/tests/test_models.py::test_form_save_raises_not_implemented` guarda o novo contrato.
  - **#3, #15, #29 (eliminar `pending_registration_person_id`)**: confirmado por análise estática exaustiva que o caminho legado (Person criada antes do pagamento) é inalcançável no fluxo atual — `create_pre_registration_plan_payment` nunca vincula `RegistrationOrder` a uma Person real antes do finalize. Removidos os ramos mortos em `MaterialsCheckoutView`, `FinalizeRegistrationView`, `DeferPaymentView`, `PaymentSuccessView`, `ResetRegistrationView._SESSION_KEYS` (também morto) e o fallback em `get_pending_person_summary`. `rg pending_registration_person_id system/` → 0.
  - **#7 (dependent_registration_service)**: extraídas as funções puras `is_dependent_payment_confirmed`, `is_dependent_materials_confirmed`, `restore_confirmed_payment_post_data`, `apply_confirmed_payment_to_cleaned_data` de `DependentRegistrationView` para `system/services/dependent_registration.py`. Escopo reduzido deliberadamente: a árvore de decisão HTTP (redirects/render/modal) permanece na view — extração completa da orquestração foi avaliada como risco desproporcional sem sessão dedicada.
  - Evidência: `manage.py test system` — 662 testes OK (era 651 no início da sessão); 29/29 testes dedicados de `test_dependent_registration.py` verdes incluindo cenários de pagamento adulterado (`test_paid_resume_finalizes_with_paid_plan_even_if_post_is_tampered`); validação manual no navegador do wizard público até o step de materiais.
- **[2026-07-09] Onda P2 executada** (forms finos e higiene HTTP):
  - **#21 (`AdministrativeRequiredMixin` único)**: mixin movido para `system/views/portal_mixins.py` (fonte canônica com `allowed_codes=ADMINISTRATIVE_PERSON_TYPE_CODES` + `required_capabilities=(MANAGE_ACADEMY,)`); as 2 cópias em `asaas_views.py` e `graduation_views.py::_AdministrativeRequiredMixin` foram removidas. **Achado de segurança durante a consolidação**: as duas cópias removidas **não** definiam `required_capabilities`, então caíam no branch de `has_allowed_role()` que checa `person.person_type.code in allowed_codes` — ignorando por completo o sistema de `OperationalRole`/capabilities. Na prática, um portador do papel operacional `academy-manager` (desenhado explicitamente para "acesso operacional amplo aos módulos administrativos", `system/constants.py` `DEFAULT_OPERATIONAL_ROLE_DEFINITIONS`) ou `graduation-operator`/`financial-operator` conseguia entrar em `PersonDeleteView` (via `person_views.py`, versão correta) mas era barrado em `PayrollListView`/`PayoutQueueView`/`GraduationOverviewView` (versões incompletas) mesmo tendo a capability certa — a delegação granular de papéis para essas duas áreas estava, na prática, morta. A unificação corrige isso ao adotar a versão com `required_capabilities` em todo lugar. 9 arquivos atualizados para importar do local canônico (`person_views.py`, `asaas_views.py`, `graduation_views.py`, `category_views.py`, `class_views.py`, `admin_views.py`, `plan_views.py`, `plan_tier_views.py`, `product_views.py`).
  - **#19/#20 (barrel `views/__init__.py`)**: confirmado por `rg "from system.views import [A-Z]"` que **nada** no código consome os ~90 re-exports do barrel — `system/urls.py` (único consumidor real de views) já importa direto de cada submódulo. Barrel esvaziado (era código morto, não "incompleto"). Aliases órfãos `InstructorCalendarView`/`StudentScheduleView` (achado #20) já não existiam mais — confirmados removidos em sessão anterior (Onda 1 do PRD-138).
  - **#23 (`_get_instructor_class_group_ids` privado)**: renomeado para `get_instructor_class_group_ids` (público) em `system/services/class_calendar.py`; `calendar_views.py` e `home_views.py` passaram a importar do topo do módulo em vez de import local/símbolo privado.
  - **#24 (acoplamento `dependent_forms` → `registration_forms`)**: `MARTIAL_ART_EXPERIENCE_CHOICES`, `MARTIAL_ART_EXPERIENCE_YES`, `MARTIAL_ART_MODALITY_CHOICES` extraídas para novo `system/forms/registration_common.py`; `registration_forms.py` e `dependent_forms.py` agora importam da mesma fonte compartilhada, sem uma depender da outra.
  - **#11 (`ClassGroupForm.save()` com domínio)**: `save()`/`save_m2m()`/`save_related()`/`_save_assistant_staff()` removidos do form; lógica de sincronização de `ClassInstructorAssignment` movida para `system/services/class_management.py::sync_class_group_instructors()`, chamada diretamente por `save_class_group_catalog()`. Único consumidor (`ClassGroupCatalogMixin.form_valid`) já passava exclusivamente pelo service, então a mudança é comportamentalmente neutra.
  - **#12 (`AdministrativeAccessRequestForm.save()`)**: avaliado — já é um delegate fino que só monta kwargs e chama `create_administrative_access_request()`; nenhuma regra de negócio no form. Sem ação necessária.
  - **#22 (`ClassEnrollment.clean` — fonte de elegibilidade)**: avaliado — `get_class_group_eligibility_error` já é função pura única (não é método do model) reutilizada por `registration_forms.py`, `dependent_forms.py`, `person_forms.py`, `services/registration_validation.py` e o próprio `ClassEnrollment.clean()`. Já é fonte única; nenhuma duplicação de regra encontrada. Sem ação necessária.
  - Evidência: `manage.py check` limpo; `manage.py test system` — 662 testes OK (mesma contagem antes/depois, nenhuma regressão) em 3 execuções completas ao longo da onda (após consolidação do mixin, após class_forms/class_management, e final).

## Cleanup findings

- `PortalRegistrationForm.save()` era API enganosa — **corrigido nesta entrega** (levanta `NotImplementedError`).
- `plan_tier_forms` ausente do barrel `forms/__init__.py` — não corrigido nesta entrega (Onda P2).
- PRD-097 parcialmente obsoleta: aliases calendário persistem no barrel, não no `urls.py` — não corrigido nesta entrega (Onda P2).

## Follow-up PRDs

- Consolidador pós PRD-138 (execução ondas A–E acima).
- Atualizar PRD-097 após decisão sobre aliases.
- PRD dedicada: migração `Membership` FK única.

## Deviations from plan

- Nenhuma.

## Pending

- Aprovação para PRD-filhas de execução por onda (P0–P3).
- PRD-141 P1 aguarda P0 (API elegibilidade).
- Backfill `Membership.plan_price` em HG antes de P3.

## Final status

**Concluída** — auditoria read-only e proposta de correção consolidada (jul/2026).
Implementação parcial das ondas ocorreu via **PRD-144** (P0/P1); o fechamento
original “código não iniciado” está obsoleto (ver reconciliação PRD-145 abaixo).

## Reconciliação PRD-145 — 2026-07-13

- “Implementação de código não iniciada” corresponde ao fechamento original e ficou
  obsoleto após as ondas descritas na seção `Implemented`.
- A PRD-145 confirmou o uso de services para solicitações administrativas e de turma,
  views finas para decisão HTTP e persistência transacional testada.
- A decomposição completa dos módulos grandes e a migração `Membership` permanecem
  fora do escopo desta rodada.
- Estado reconciliado: **auditoria concluída; ondas registradas implementadas;
  refatorações estruturais restantes pendentes**.
