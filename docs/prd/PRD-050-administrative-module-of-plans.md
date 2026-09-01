# PRD-050: Administrative plans module

## Summary of the implementation
Open the plans module for administrative viewing and management, connecting the home's `Planos` (`Plans`) shortcut to server-rendered screens for listing, detail, creation, editing, and controlled deletion of subscription plans.

## Demand type
New feature.

## Current problem
The `Planos` (`Plans`) shortcut appears on the home as a disabled link, even though the project already has the model, a partial form, services, and initial views for `SubscriptionPlan`. There are no registered routes, no module templates, no dedicated CSS, and no access tests for the administrative flow.

## Goal
Provide an administrative module consistent with the existing visual standard in `templates/people/`, respecting `docs/UI-SCREEN-CONTRACT.md`, with no schema change and no migrations.

## Context Ledger

### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/models/plan.py`
- `system/forms/plan_forms.py`
- `system/services/plan_management.py`
- `system/views/plan_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/dashboard.js`
- `system/tests/test_home_dashboard.py`
- `system/views/person_views.py`
- `system/views/home_views.py`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/people/people.css`
- `docs/prd/PRD-045-people-list-and-detail.md`
- `docs/prd/PRD-089-crud-of-plans-with-dynamic-pricing.md`
- `docs/prd/PRD-007-reformulate-plans-pricing-eligibility-and-targeting-adult-vs-kids-juvenile.md`
- `docs/prd/PRD-006-standardize-plan-change-screen-with-portal-design-system.md`
- `docs/prd/PRD-019-plan-change-plan-selector-standard.md`
- `docs/prd/PRD-020-plan-change-balance-future-credit-and-auto-refund.md`
- `docs/prd/PRD-035-subscription-plan-value-seed.md`
- `docs/prd/PRD-041-stripe-recurring-plans.md`
- `system/tests/test_plan_models.py`
- `system/tests/test_plan_eligibility.py`
- `system/tests/test_plan_change.py`
- `system/tests/test_forms.py`
- `system/admin.py`
- `system/models/__init__.py`
- `system/selectors/plan_eligibility.py`
- `system/services/registration_checkout.py`
- `system/signals.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/models/membership.py`
- `system/models/registration_order.py`
- `system/views/portal_mixins.py`

### Adjacent files consulted
- `docs/prd/`
- `templates/`
- `static/system/css/`
- `system/tests/`
- `system/migrations/`

### Internet / official documentation
- Django 4.1 — generic display views: `https://docs.djangoproject.com/en/4.1/ref/class-based-views/generic-display/`
- Django 4.1 — generic editing views: `https://docs.djangoproject.com/en/4.1/ref/class-based-views/generic-editing/`

### MCPs / tools verified
- PowerShell — OK — `Get-Location`
- The project's Python — OK — `.\.venv\Scripts\python.exe --version`
- Django test runner — OK — `.\.venv\Scripts\python.exe manage.py help test`
- Django checks — OK — `.\.venv\Scripts\python.exe manage.py check`
- Existing migrations — OK — `.\.venv\Scripts\python.exe manage.py showmigrations`
- Context7 — limited — the attempt to resolve the Django documentation returned an invalid OAuth token

### Limitations found
- The project has a dirty worktree before this change; unrelated changes must not be reverted.
- `CLAUDE.md` restricts creating new folders, but `PRD-045` already sets a precedent for creating template/static folders when existing views point to a module that has no files yet.
- There will be no schema change; therefore there will be no migration, `makemigrations`, or `migrate`.

## Execution prompt

### Persona
Development agent specializing in Django MVT, following SDD, TDD, and server-rendered UI.

### Action
Implement the administrative plans module according to the spec below.

### Context
The system already has `SubscriptionPlan` as the central entity for tuition, plan changes, public registration, recurring payments, and value seeds. The administrative module must expose that record to the authorized team without breaking the existing flows.

### Constraints
- no hardcoded secrets, domains, tokens, or variable rules
- no error masking
- no migrations
- no `makemigrations`
- no `migrate`
- mandatory full reading
- mandatory validation
- visible text in Brazilian Portuguese
- technical identifiers in English
- CSS/JS separated per module
- do not edit `staticfiles/`

### Acceptance criteria
- [ ] The home's `Planos` (`Plans`) shortcut must open the module at `/planos/` for a technical administrator (verifiable by test and in the browser).
- [ ] An unauthenticated user must be redirected to login when reaching `/planos/` (verifiable by test).
- [ ] The list must show the existing plans with their name, code, audience, frequency, cycle, payment method, status, and price (verifiable by test and visual inspection).
- [ ] The list must allow filtering by text search, audience, frequency, cycle, gateway, and status (verifiable by test).
- [ ] The detail must show the commercial data, pricing, gateway, Stripe, and the plan's usage (verifiable by test and visual inspection).
- [ ] The form must expose the administrative fields needed to create/edit a plan with no schema change (verifiable by test).
- [ ] Deleting a plan linked to a `Membership` must fail explicitly, preserve the plan, and advise deactivation (verifiable by test).
- [ ] Visual hierarchy: the title at weight 700, labels at 500, hints in `--muted` (verifiable: visual inspection).
- [ ] Proximity: fields of the same group with a gap <= 12px; groups separated by a divider or a gap >= 20px (verifiable: visual inspection).
- [ ] Affordance: the primary action with a `--brand-red` background; filters and badges with distinct states (verifiable: visual inspection).
- [ ] The disabled state with opacity 0.45 and a `not-allowed` cursor when an action is unavailable (verifiable: visual inspection).
- [ ] Per-field error feedback below the field in `--danger` (verifiable: an invalid submission).
- [ ] State machine: an empty list, a list with data, an invalid form, and a blocked deletion have distinct visual representations (verifiable: test + inspection).

### Expected evidence
- focused tests passing
- `manage.py test --verbosity 2` passing
- `manage.py check` passing
- `manage.py collectstatic --noinput` passing when there is a new static file
- the browser console with no critical JavaScript error
- the server terminal with no stack trace
- desktop and mobile visual inspection

### Output format
Implemented code + tests + validation evidence.

## Scope
- Register the administrative plan routes in the `system` namespace.
- Enable the home's `Planos` (`Plans`) quick-link.
- Expand the plans form with the commercial, pricing, and gateway fields already present in the model.
- Create a server-side filter for the list.
- Create the `plans/` templates following the visual standard of `people/`.
- Create the module's own CSS/JS in `static/system/css/plans/` and `static/system/js/plans/`.
- Add view, form, and home tests.
- Validate the UI in the browser.

## Out of scope
- Changing the `SubscriptionPlan` model.
- Creating or regenerating migrations.
- Creating a new gateway integration.
- Synchronizing products/prices in Stripe.
- Changing the public registration wizard.
- Changing the plan eligibility rules.
- Implementing new granular permissions.

## Impacted files
- `docs/prd/PRD-050-administrative-module-of-plans.md`
- `system/forms/plan_forms.py`
- `system/services/plan_management.py`
- `system/views/plan_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `templates/plans/plan_list.html`
- `templates/plans/plan_detail.html`
- `templates/plans/plan_form.html`
- `templates/plans/plan_confirm_delete.html`
- `static/system/css/plans/plans.css`
- `static/system/js/plans/plans.js`
- `system/tests/test_plan_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_home_dashboard.py`

## Risks and edge cases
- Plans linked to subscriptions cannot be deleted because of `PROTECT`.
- The gateway and Stripe fields are used by the payment flows; the UI must expose the data without inventing synchronization.
- The price calculation in the model uses `base_monthly_net_price`; the form must not hide the manual price when that field is empty.
- The list may contain many plans; the first delivery uses server-side filters and predictable ordering, with no pagination because the expected catalog is small.
- The current template pattern has inline theme scripts; this implementation must prefer module JavaScript for new interactions.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Visual hierarchy

- Reading pattern: F Pattern
- Screen title: weight 700-800, the `--text` token
- Sections/groups: weight 600, the `--text` token
- Fields/labels: weight 500, the `--text` token
- Help text/hints: weight 400, the `--muted` token
- Primary action: `--brand-red`, weight 600
- Secondary action: `--border` border, weight 500

## Wireframe

### Region: Top
- Eyebrow: Administration
- Title: Plans
- Primary action: New plan, aligned right
- Secondary action: Back to Home

### Region: Main content
- Group A: Indicators — total, active, inactive, family, special, and gateways
- Group B: Filters — search, audience, frequency, cycle, gateway, and status
- Group C: List — a responsive card/table with the main data and a `Detalhe` (`Detail`) action

### Region: Detail
- A header with the name, code, status, and actions
- Group A: Commercial
- Group B: Pricing
- Group C: Gateway and Stripe
- Group D: Plan usage

### Region: Form
- Group A: Identification
- Group B: Segmentation
- Group C: Pricing
- Group D: Gateway
- Group E: Display
- Actions: Cancel (secondary), Save plan (primary)

### Screen states
- Loading: server-side rendering with no specific intermediate visual state
- Empty: a panel with the message `Nenhum plano encontrado` (`No plan found`)
- With data: a list of plans grouped into responsive cards
- Error: global messages and per-field errors in `--danger`

## State machines

### Plan list
- States: empty, with data, filtered with no result
- Transitions: the initial request -> queryset -> render empty | render with data
- Visual representation: an empty panel with an icon/text, or a list with cards and counters

### Plan form
- States: initial, invalid, saving, saved
- Transitions: GET -> filling in -> an invalid POST | a valid POST -> redirect
- Visual representation: grouped fields; per-field errors; a success message after the redirect

### Plan deletion
- States: available, blocked by links, completed
- Transitions: a confirmation GET -> POST -> delete | ProtectedError
- Visual representation: a risk alert; a block with guidance to deactivate when there is usage

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation

### Desktop
Validate `/home/`, `/planos/`, the detail, the form, and deletion in a desktop viewport.

### Mobile
Validate the same flows in a mobile viewport, focusing on the filters, cards, buttons, and the absence of overlap.

### Browser console
Check for the absence of critical JavaScript errors.

### Terminal
Check for the absence of a stack trace on the Django server.

## ORM validation

### Database
Use data created in tests; do not run migrations.

### Shell checks
Not planned for this change with no schema.

### Flow integrity
Confirm that plans linked to a `Membership` are not removed.

## Quality validation

### No hardcoding
Filters, routes, and URLs must use Django forms, `reverse`/`url`, and the model's choices.

### No brittle conditional structures
The views must delegate filters and statistics to helper services.

### No `except: pass`
Protected deletion errors must be handled explicitly.

### No error masking
`ProtectedError` must produce a clear message and keep the object.

### No unnecessary comments or docstrings
Comments will only be added when there is an architectural decision that cannot be inferred.

## Evidence
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_views system.tests.test_forms.PlanFormLayoutContractTestCase system.tests.test_home_dashboard.HomeDashboardTestCase.test_technical_admin_home_does_not_render_dead_staff_links --verbosity 2 --keepdb` initially failed due to non-existent `plan-*` routes and the absence of groupings in `PlanForm`.
- Focused Green: the same command passed with 8 tests.
- Technical validation: `.\.venv\Scripts\python.exe manage.py check` passed with no issues.
- Final validation after the style adjustment: `.\.venv\Scripts\python.exe manage.py check` and the focused plan/form tests passed.
- Migrations, read-only: `.\.venv\Scripts\python.exe manage.py showmigrations system` showed only `[X] 0001_initial`.
- Static files: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` processed the new plan assets.
- Full suite: `.\.venv\Scripts\python.exe manage.py test --verbosity 2 --keepdb` passed with 207 tests.
- Browser DOM: the technical login, the Home, and the `Planos` (`Plans`) link validated at `http://127.0.0.1:8000/home/`; `/planos/` validated with the KPIs, filters, list, and the detail link.
- Playwright visual validation: desktop and mobile captured in `C:\Users\whsf\AppData\Local\Temp\lvj-plans-validation\`.
- The browser console: no critical errors (`console_errors: []`, `page_errors: []`).
- Cleanup: the temporary `codex_plan_validation` user and its associated sessions removed.

## Implemented
- Administrative plan routes at `/planos/`, `/planos/novo/`, `/planos/<pk>/`, `/planos/<pk>/editar/`, and `/planos/<pk>/excluir/`.
- The `Planos` (`Plans`) shortcut enabled on the home.
- `PlanForm` expanded with identification, segmentation, pricing, and gateway fields.
- `PlanListFilterForm` created with search, audience, frequency, cycle, payment method, gateway, and status.
- A listing service with server-side filters and plan statistics.
- Explicit handling of `ProtectedError` when deleting plans linked to subscriptions.
- Administrative templates for the list, detail, form, and delete confirmation.
- The plans module's own CSS/JS.
- Tests for the views, the filter, the form, the Home, and protected deletion.

## Deviations from plan
- The embedded browser validated navigation and the DOM, but the screenshot capture through CDP exceeded the timeout. Visual validation was completed with headless Playwright on the same local server.
- The old Home test was adjusted to accept a hashed asset after `collectstatic`, validating `system/js/dashboard` instead of `system/js/dashboard.js`.

## Pending
- No functional pending items identified in this delivery.
