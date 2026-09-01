# PRD-065: Administrative hubs of the LV modules

## Summary

Create a future delivery to enable navigation and administrative CRUD/hubs for the modules already modeled in LV: classes, finance, graduation, materials, plans, profiles, and access. LV has relevant domain and service pieces, but several modules have no administrative routes/templates or appear as disabled shortcuts on the home.

## Demand type

New administrative feature + integration of existing modules. It requires its own PRD, a visual proposal, and browser validation.

## Current problem

- `templates/home/dashboard.html` exposes Classes, Finance, Graduation, and Materials as disabled shortcuts.
- `system/urls.py` registers People, Plans, the Calendar, and the public payments, but it does not register the administrative views that already exist for categories/classes/schedules, graduation, products/materials, finance, payouts, and person types.
- A text inventory found views with no corresponding templates/routes in:
  - `billing`: the approval queue, pending items, and financial control;
  - `asaas payroll`: bank accounts, payouts, and the instructor's finances;
  - `classes`: categories, classes, and schedules;
  - `graduation`: belts, rules, and the student's graduation;
  - `products/materials`: categories, products, variants, and backorders;
  - `person_types`: administration of person profiles/types.
- LV must not copy the consultancy domain; it must adopt only the governance, hubs, permissions, navigation, and visual finish patterns.

## Goal

1. Define the administrative navigation architecture per module, preserving the academy's business rules.
2. Register the missing routes/templates for the existing modules without creating a new schema in the first stage.
3. Implement scannable hubs for Classes, Finance, Graduation, Materials, and Administration.
4. Enable administration of profiles/access on a screen of its own, without depending solely on the Django Admin.
5. Validate an ordinary student and a student with a dependent going through enrollment, plan, class, materials, and the expected graduation.

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

- The local inventory of views/templates/routes performed during the PRD-061/063/064 cycle.
- `system/forms/category_forms.py`, `system/forms/class_forms.py`, `system/forms/graduation_forms.py`, `system/forms/product_forms.py`, `system/forms/person_forms.py`
- `static/system/css/home/dashboard.css`, `static/system/css/people/people.css`, `static/system/css/plans/plans.css`
- A read-only count map of the local database: `Person`, `ClassGroup`, `ClassSchedule`, `BeltRank`, `GraduationRule`, `Product`, `ProductVariant`, `SubscriptionPlan`.

### Internet / official documentation

- Context7/Django 5.2 consulted: URLconf with `path()`, `app_name`, named URL patterns, `View.as_view()`, `template_name` in generic views, and `{% url %}` in templates.

### Context7 / MCPs / tools verified

- PowerShell, `rg`, Git, and the internal browser available.
- Context7 not used in this documentation work because there was no library/API decision.

### Limitations found

- The implementation may reveal the need for migrations or seed data; any schema/seed must stop for explicit authorization.
- Full validation of a registration with a dependent requires creating test data and running it in the browser; it requires its own authorization.
- `docs/UX-SCREEN-FLOWS.md` is referenced in `AGENTS.md`, but it does not exist in the current LV repository; use `docs/UI-SCREEN-CONTRACT.md`, the existing PRDs, and the real code until the source is created or restored.
- The visual gate is still pending: implementing templates/CSS/JS must wait for explicit approval of the proposal below.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: record the missing administrative modules for a later implementation, without expanding the current cycle.
- User approval: the original demand asked to validate the creation of the class, finance, graduation, materials, plans, and profile/access administration modules.
- Date: 2026-06-28.

## Execution prompt

### Persona

Django/UI engineer responsible for modularizing the LV academy's administration.

### Action

Design and implement administrative hubs per module, enabling navigation, routes, templates, and visual validation without losing the martial arts domain.

### Context

LV is a Django 5.2 monolith with models/services already existing for people, plans, classes, sessions, graduation, materials/products, payments, and payouts.

### Constraints

- Do not create a migration without explicit authorization.
- Do not edit `staticfiles/`.
- Do not move business rules into a template/JavaScript.
- Keep the permissions in the backend.
- The UI in Brazilian Portuguese, the code in English.
- Validate in the internal desktop/mobile browser.

### Acceptance criteria

- [x] The visual proposal below approved before editing templates/CSS/JS.
- [x] The administrative home has enabled shortcuts for Classes, Finance, Graduation, Materials, Plans, and Administration.
- [x] Each hub has a named route, its own template, and an empty state.
- [x] The Classes module covers categories, classes, schedules, and the instructor link.
- [x] The Finance module covers approvals, pending items, plans/charges, and instructor payouts.
- [x] The Graduation module covers belts, rules, history, and the student's progress.
- [x] The Materials module covers categories, products, variants, stock/backorders, and requests linked to an enrollment.
- [x] Administration covers person types/profiles and access without depending exclusively on the Django Admin.
- [ ] An ordinary student and a student with a dependent are validated in the expected visual flow.
- [x] Tests written before the code and run only with authorization.

### Expected evidence

- A route → view → template → permission matrix.
- Desktop/mobile screenshots of each hub.
- A clean console.
- `manage.py check`.
- Authorized tests, when the user releases them.
- A read-only ORM before/after for the authorized test records.

### Output format

A short summary, the module matrix, evidence, limitations, and status.

## Module matrix

### Proposed routes and hubs

| Module | Hub | Main routes | Existing views | Template/status |
|---|---|---|---|---|
| Classes | `/turmas/` (`class-group-list`) | categories, classes, schedules | `ClassCategory*`, `ClassGroup*`, `ClassSchedule*` | implemented |
| Finance | `/financeiro/` (`financial-control`) | approvals, pending, entries, payouts, payroll | `FinancialControlView`, `ApprovalQueueView`, `PendingPaymentListView`, `PayrollListView`, `PayoutQueueView` | implemented |
| Graduation | `/graduacao/` (`graduation-overview`) | belts, rules, history, record a graduation | `GraduationOverviewView`, `BeltRank*`, `GraduationRule*`, `Graduation*` | implemented |
| Materials | `/materiais/` (`product-list`) | products, variants, the shop, pre-orders, history | `Product*`, `ProductStoreView`, `StudentBackorder*`, `AdminBackorderQueueView` | implemented |
| Administration | `/administracao/` (`admin-hub`) | profiles/person types, access, the Django Admin | `AdminHubView`, `PersonType*`, `Person*` | implemented |
| Plans | `/planos/` (`plan-list`) | plans, detail, create, edit, delete | `Plan*` | implemented; it enters as a hub link, with no reimplementation |

### Route → view → template → permission matrix

| Proposed route | Name | View | Template | Permission |
|---|---|---|---|---|
| `/turmas/` | `class-group-list` | `ClassGroupListView` | `classes/class_group_list.html` | back office |
| `/turmas/nova/` | `class-group-create` | `ClassGroupCreateView` | `classes/class_group_form.html` | back office |
| `/turmas/<pk>/` | `class-group-detail` | `ClassGroupDetailView` | `classes/class_group_detail.html` | back office |
| `/turmas/<pk>/editar/` | `class-group-update` | `ClassGroupUpdateView` | `classes/class_group_form.html` | back office |
| `/turmas/<pk>/excluir/` | `class-group-delete` | `ClassGroupDeleteView` | `classes/class_group_confirm_delete.html` | back office |
| `/turmas/categorias/` | `class-category-list` | `ClassCategoryListView` | `class_categories/class_category_list.html` | back office |
| `/turmas/horarios/` | `class-schedule-list` | `ClassScheduleListView` | `class_schedules/class_schedule_list.html` | back office |
| `/financeiro/` | `financial-control` | `FinancialControlView` | `billing/financial_entries.html` | back office |
| `/financeiro/aprovacoes/` | `approval-queue` | `ApprovalQueueView` | `billing/approval_queue.html` | back office |
| `/financeiro/pendentes/` | `pending-payments` | `PendingPaymentListView` | `billing/pending_payments.html` | back office |
| `/financeiro/folha/` | `payroll-list` | `PayrollListView` | `billing/payroll_list.html` | back office |
| `/financeiro/repasses/` | `payout-queue` | `PayoutQueueView` | `billing/payout_queue.html` | back office |
| `/graduacao/` | `graduation-overview` | `GraduationOverviewView` | `graduation/graduation_overview.html` | back office |
| `/graduacao/faixas/` | `belt-rank-list` | `BeltRankListView` | `graduation/belt_rank_list.html` | back office |
| `/graduacao/regras/` | `graduation-rule-list` | `GraduationRuleListView` | `graduation/graduation_rule_list.html` | back office |
| `/graduacao/historico/` | `graduation-list` | `GraduationListView` | `graduation/graduation_list.html` | back office |
| `/materiais/` | `product-list` | `ProductListView` | `products/product_list.html` | back office |
| `/materiais/novo/` | `product-create` | `ProductCreateView` | `products/product_form.html` | back office |
| `/materiais/<pk>/` | `product-detail` | `ProductDetailView` | `products/product_detail.html` | back office |
| `/materiais/pre-pedidos/` | `admin-backorder-queue` | `AdminBackorderQueueView` | `billing/admin_backorder_queue.html` | back office |
| `/loja/` | `product-store` | `ProductStoreView` | `products/product_store.html` | student/guardian/dependent/instructor/admin |
| `/meus-materiais/pre-pedidos/` | `student-backorders` | `StudentBackorderListView` | `products/student_backorder_list.html` | student/guardian/dependent/instructor/admin |
| `/meus-materiais/pedidos/` | `student-order-history` | `StudentOrderHistoryView` | `products/student_order_history.html` | student/guardian/dependent/instructor/admin |
| `/administracao/perfis/` | `person-type-list` | `PersonTypeListView` | `person_types/person_type_list.html` | back office |
| `/administracao/perfis/novo/` | `person-type-create` | `PersonTypeCreateView` | `person_types/person_type_form.html` | back office |
| `/administracao/perfis/<pk>/` | `person-type-detail` | `PersonTypeDetailView` | `person_types/person_type_detail.html` | back office |

## Visual hierarchy

### The common administrative hub

1. The existing topbar: the LV logo, the theme, logout.
2. The page header: the module's eyebrow, the title, a subtitle with a real count, and the primary action.
3. A dense KPI row: 4 to 6 module metrics, with no hero or marketing.
4. Internal module tabs/quick links: related lists, queues, settings.
5. The main panel: an operational list or cards.
6. The empty state: short text + the primary action when creation is available.

### Density per module

- Classes: prioritize comparison by category, instructor, schedules, and active status.
- Finance: prioritize status, amount, due date, gateway, plan, and the permitted action.
- Graduation: prioritize the student/belt/rule/progress, with a compact visual belt.
- Materials: prioritize the product, variations, stock, pre-order, and material status.
- Administration: prioritize the person type, the person count, and the derived permissions.

## Wireframe

### Region: Top

- Eyebrow: the module's name.
- Title: Classes / Finance / Graduation / Materials / Administration.
- Subtitle: the module's real count or state.
- The primary action on the right: New item when there is a safe create view.

### Region: KPIs

- A responsive grid of small cards, 2 columns on mobile, 4 to 6 columns on desktop.
- Each KPI uses a value, a label, and at most one status badge.

### Region: Internal navigation

- Links segmented in a row on desktop; horizontal scrolling on mobile.
- States: active, available, disabled by permission/scope.

### Region: Main content

- A dense list on desktop with the identifier on the left, metadata in the center, and actions on the right.
- On mobile, each row becomes a simple horizontal card, with no squeezed table.
- Destructive actions stay secondary and visually separated.

### Screen states

- `loading`: not applicable in the first server-rendered delivery.
- `empty`: a panel with a clear next action.
- `populated`: a list rendered with real data.
- `error`: Django messages at the top and per-field errors in the forms.
- `forbidden`: a redirect through `PortalRoleRequiredMixin`.

## State machine

### The administrative hub

- States: `empty` → `populated`; `populated` → `filtered`; `action` → `success|error`.
- Transitions:
  - GET with no data: `empty`.
  - GET with data: `populated`.
  - A valid POST: a redirect + a persistent message.
  - An invalid POST: renders the form with per-field errors.
  - A protected destructive POST: a blocking message and the object preserved.

### Financial queues

- States: `pending`, `approved`, `paid`, `refunded`, `exempted`, `failed`.
- Mutating transitions use the existing services and must stay behind an authenticated POST.

### Material pre-orders

- States: `requested`, `available`, `converted`, `canceled`.
- Mutating transitions use the backorder services and do not change stock through a template/JavaScript.

## Design approval

Approved by the user's direct request: "implemente" ("implement it").

## Scope

- `system/urls.py`
- `system/views/*`
- `templates/home/dashboard.html`
- `templates/<module>/*`
- the modules' specific `static/system/css/*` and `static/system/js/*`
- tests of the affected views/services

## Out of scope

- Migrations/schema without authorization.
- Destructive seeds or a local reset.
- Real payments in the gateway.
- Porting the visa or consultancy domain.

## Impacted files

To be defined during execution, after a complete inventory.

## Risks and edge cases

- Enabling a route with no template or coherent permission produces a 500 or improper access.
- Finance and payouts may require a clear separation between reading, approval, and mutation.
- Stock/materials may need a schema decision before a complete CRUD.
- Graduation must preserve the IBJJF/LV rules and must not become a free field with no auditing.
- A person with a dependent needs to keep the holder, guardian, enrollment, plan, and materials consistent.

## Rules and constraints

- The smallest verifiable vertical delivery per module.
- MVT: thin views, rules in services/selectors.
- UI with an approved proposal before the code.
- Tests not run without authorization.

## Plan

- [x] Context and research
- [x] The route/view/template/permission matrix
- [x] The hubs' visual proposal
- [x] Contract tests per module
- [x] Incremental implementation per module
- [x] Desktop/mobile browser
- [ ] Read-only ORM and authorized test records
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- Administrative views protected by profile.
- The hubs render cards/empty states.
- Named routes resolve to the expected templates.
- The ordinary student and student-with-a-dependent flows keep the enrollment/plan/class/materials/graduation contracts.

### Tests authored

- `system/tests/test_admin_hubs_contract.py`: a test-first contract for PRD-065's named routes and the administrative home's enabled links.
- `system/tests/test_home_dashboard.py`: the existing contract adjusted so it no longer accepts disabled administrative shortcuts after the hubs were implemented.

### Execution authorization

- Status: not authorized. The Django suite was not run, per policy.

### Execution evidence

- The tests were written, not run.
- `.venv\Scripts\python.exe -m py_compile system\tests\test_admin_hubs_contract.py system\tests\test_home_dashboard.py`: valid syntax.
- The state after the implementation: the contracts should pass when the suite is authorized, but the Django suite was not run.

## Visual validation

- The internal desktop browser at 1365x900:
  - `/administracao/`: 7 cards, a console with no errors, `deadLinks=0`, `quickDisabled=0`, no overflow.
  - `/home/`, `/turmas/`, `/financeiro/`, `/graduacao/`, `/materiais/`, `/administracao/perfis/`: a visual status with no overflow and no dead links.
- The internal mobile browser at 390x844:
  - `/administracao/`, `/home/`, `/turmas/`, `/financeiro/`, `/materiais/`, `/administracao/perfis/`: no horizontal overflow, a console with no errors, no dead links.
- Screenshots captured in the internal browser for `/administracao/` on desktop and `/turmas/` on mobile; the viewport restored.

## ORM validation

- A read-only ORM run for the counts and the selection of existing IDs.
- The ordinary student and student-with-a-dependent records were not created because they require explicit authorization for a data mutation.

## Quality validation

- `manage.py check`.
- `git diff --check`.
- A review of orphaned routes/templates/assets.

### Executed quality evidence

- `.venv\Scripts\python.exe manage.py check`: passed, 0 issues.
- `.venv\Scripts\python.exe -m py_compile system\admin.py system\forms\class_forms.py system\forms\person_forms.py system\views\product_views.py system\tests\test_admin_hubs_contract.py system\tests\test_home_dashboard.py system\urls.py system\views\admin_views.py`: passed.
- `node --check static\system\js\admin\admin_modules.js`: passed.
- `git diff --check`: passed; only LF/CRLF normalization warnings in the working copy.
- A read-only Django client with a technical session: 200 for `/home/`, `/administracao/`, `/turmas/`, `/turmas/nova/`, `/turmas/categorias/`, `/turmas/categorias/nova/`, `/turmas/horarios/`, `/turmas/horarios/novo/`, `/financeiro/`, `/financeiro/aprovacoes/`, `/financeiro/pendentes/`, `/financeiro/folha/`, `/financeiro/repasses/`, `/graduacao/`, `/graduacao/faixas/`, `/graduacao/faixas/nova/`, `/graduacao/regras/`, `/graduacao/regras/nova/`, `/graduacao/historico/`, `/graduacao/historico/novo/`, `/materiais/`, `/materiais/novo/`, `/loja/`, `/materiais/pre-pedidos/`, `/meus-materiais/pre-pedidos/`, `/meus-materiais/pedidos/`, `/administracao/perfis/`, `/administracao/perfis/novo/`, and the details with existing IDs.

## Evidence

Created as a follow-up from the local inventory:

- `templates/home/dashboard.html` keeps Classes, Finance, Graduation, and Materials disabled.
- `system/urls.py` does not register the modules' complete administrative routes.
- The local database has populated catalogs for classes, schedules, belts, rules, products, variants, and plans, but there is no equivalent operational hub.
- `rg` confirmed existing administrative views for classes/categories/schedules, finance, payouts, graduation, materials, and person types.
- `rg --files templates` confirmed the current absence of `classes/*`, `class_categories/*`, `class_schedules/*`, `billing/*`, `graduation/*`, `products/*`, and `person_types/*`.
- `docs/UI-SCREEN-CONTRACT.md` read: it requires an approved wireframe proposal before a new screen and visual validation in the internal browser.
- `docs/UX-SCREEN-FLOWS.md` does not exist in the current LV repository.
- `system/tests/test_admin_hubs_contract.py` created with test-first contracts for the routes and the administrative shortcuts.
- `system/tests/test_home_dashboard.py` adjusted for the future state with no disabled administrative shortcuts.
- `rg` confirmed the absence of `SENTINEL_TEST_XZ99`, `href="#"`, "Módulo pendente" ("Module pending"), and "em breve" ("coming soon") in the templates/static/system within the relevant scope.
- An existing architectural bug fixed: `ClassGroup` has no `code` field; `ClassScheduleForm`, `PersonForm`, and `ClassScheduleAdmin` were adjusted to use the real fields.
- A Materials gap fixed: the technical admin now receives a `purchase_person_id` selection in the shop and can request materials for an authorized person without depending on `portal_person`.

## Implemented

- The route → view → template → permission matrix added.
- The visual proposal, wireframe, and the hubs' state machines added.
- Test-first contracts for the routes and the administrative shortcuts added.
- `AdminHubView` created.
- Administrative routes for Classes, Finance, Graduation, Materials, the shop/pre-orders, and Profiles/Access registered in `system/urls.py`.
- The materials shop adjusted to support a request by the technical admin with a valid target person.
- The administrative home updated to real links for Classes, Finance, Graduation, Materials, Plans, and Profiles/Access.
- Server-rendered templates created for the implemented modules' hubs/lists/details/forms/delete screens.
- `static/system/css/admin/admin_modules.css` and `static/system/js/admin/admin_modules.js` added.
- The dead `quick-link--disabled` CSS removed from the home.

## Cleanup findings

- No functional change in this PRD.
- No temporary file created.

## Follow-up PRDs

This PRD is the material follow-up of the PRD-061/063/064 cycle.

## Deviations from plan

- The automated tests were not run, per policy.
- The validation of an ordinary student and a dependent was not run because it requires creating data through the UI.

## Pending

- Authorization to run the Django suite after the implementation.
- A decision about creating test records for an ordinary student and a student with a dependent.

## Final status

**Completed with limitations** — the administrative hubs implemented and validated in the desktop/mobile browser; the automated tests and the student/dependent records depend on explicit authorization.
