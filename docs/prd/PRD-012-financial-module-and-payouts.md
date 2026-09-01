# PRD-012: Financial module and payouts

## Summary of the implementation
Implement an administrative financial view with ASAAS and Stripe KPIs side by side, a unified history of inflows and outflows, payout rules per staff member, and an individual payout view for the instructor or back-office staff.

## Demand type
New feature + external integration + internal architectural change.

## Current problem
The system already records orders, fees, gateways, webhooks, and a simple instructor payroll with a fixed monthly amount. The current financial screen lists only order inflows. There is no ASAAS/Stripe consolidation, no unified inflow/outflow history, no proportional rule per student/class, and no payout configuration in the person record.

## Goal
Allow the back office to track receivable amounts in ASAAS and Stripe, see separate and consolidated KPIs, view inflows and outflows linked to people, configure payouts for instructors and back-office staff, and generate monthly closings with a history visible to the instructor or back-office staff.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `requirements.txt`
- `lvjiujitsu/settings.py`
- `system/constants.py`
- `system/models/__init__.py`
- `system/models/asaas.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/models/registration_order.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/calendar.py`
- `system/models/class_schedule.py`
- `system/forms/person_forms.py`
- `system/forms/payroll_forms.py`
- `system/views/__init__.py`
- `system/views/asaas_views.py`
- `system/views/billing_admin_views.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/urls.py`
- `templates/base.html`
- `templates/billing/financial_entries.html`
- `templates/billing/payroll_list.html`
- `templates/billing/payout_queue.html`
- `templates/home/instructor/financial.html`
- `templates/people/person_form.html`
- `static/system/css/billing/billing.css`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/services/asaas_payroll.py`
- `system/services/asaas_webhooks.py`
- `system/services/financial_transactions.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_sync.py`
- `system/services/stripe_webhooks.py`
- `system/services/class_calendar.py`
- `system/services/seeding.py`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/test_models.py`
- `system/tests/test_commands.py`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/schedule_monthly_payouts.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_test_personas.py`

### Adjacent files consulted
- `system/admin.py`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`

### Internet / official documentation
- Stripe API Reference: `GET /v1/balance` and `Balance.retrieve()`.
- Stripe API Reference: `GET /v1/balance_transactions` and the balance transaction history.
- Asaas API Reference: `GET /v3/finance/balance`.
- Asaas API Reference: `GET /v3/finance/payment/statistics?status=PENDING`.

### MCPs / tools verified
- PowerShell + `.venv` — OK — `.\.venv\Scripts\python.exe --version`
- Django check — OK — `.\.venv\Scripts\python.exe manage.py check`
- Context7 — OK — Django ModelForm/CBV lookup
- Stripe skill — OK — `stripe-best-practices` consulted
- Browser Use — OK — opened `http://localhost:8000/home/administrative/` in the in-app browser and confirmed the administrative panel.
- Playwright `.venv` — OK — desktop/mobile visual validation in an isolated browser.

### Limitations found
- `rg` failed with `Access denied`; file reading was done through PowerShell.
- Local policy forbids new migrations by default. The implementation must reuse existing tables.
- The current schema has no dedicated table for payout rules by category; the variable rules will be stored as versioned JSON in `TeacherPayrollConfig.notes`, validated by a service/form.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT with services/selectors.

### Action
Implement the financial module, payout configuration, and financial seeds following the spec below.

### Context
The `system` app concentrates the domain. The current administrative screen `billing/financial_entries.html` will be expanded. The existing payroll uses `TeacherPayrollConfig`, `TeacherBankAccount`, and `TeacherPayout`; those models will be preserved with no new migration.

### Constraints
- no hardcoding outside seeds and explicit technical constants
- no error masking: ASAAS/Stripe failures must appear as an unavailable state with a short technical message
- no new migrations
- mandatory full reading
- mandatory validation
- Brazilian Portuguese UI
- technical identifiers in English

### Acceptance criteria
- [x] The back office sees ASAAS and Stripe side by side with available, receivable, and total per gateway.
- [x] The back office sees a consolidated KPI summing ASAAS + Stripe and the total of outflows/payouts.
- [x] The financial history shows order inflows and payout outflows linked to a person, gateway/status, and date.
- [x] Creating/editing a person allows configuring a payout when the type is Instructor or Back office.
- [x] An instructor or back-office member with no mandatory payout can have an inactive rule or a zero amount without breaking the closing.
- [x] The rules accept a fixed monthly amount, an amount per student, a percentage per student, and an amount per class.
- [x] The monthly closing computes the expected amount based on paid inflows, linked students, and approved classes.
- [x] The individual history shows what came in linked to the person, what is expected, and when it will land.
- [x] The initial seed creates the configs: Layon adult fixed R$ 400, Layon juvenile 50%, Andre R$ 0, Vinicius R$ 400, Vanessa Ferro R$ 0.
- [x] The test seed creates a visible past financial history.

### Expected evidence
- passing automated tests
- `manage.py check` with no issues
- `collectstatic --noinput` when a versioned CSS/template is changed
- desktop and mobile visual validation
- browser console with no critical errors
- terminal with no stack traces

### Output format
Implemented code + tests + validation evidence.

## Scope
- A financial dashboard service.
- An ASAAS client with charge statistics.
- A Stripe client for balance and balance transaction history.
- A payout rules and closings service.
- A person form with non-model payout fields.
- Views/templates for the administrative financial screen, payroll, queue, and the individual financial screen.
- Base and test seeds.

## Out of scope
- Executing real transfers without existing approval.
- Creating new tables or migrations.
- Full accounting reconciliation by invoice, split, or advance payment.
- New webhooks beyond the existing ones.

## Impacted files
- `system/services/financial_dashboard.py` new
- `system/services/payroll_rules.py` new
- `system/services/asaas_client.py`
- `system/services/asaas_payroll.py`
- `system/forms/person_forms.py`
- `system/forms/payroll_forms.py`
- `system/views/billing_admin_views.py`
- `system/views/asaas_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/views/__init__.py`
- `templates/billing/financial_entries.html`
- `templates/billing/payroll_list.html`
- `templates/billing/payout_queue.html`
- `templates/home/instructor/financial.html`
- `templates/home/administrative/dashboard.html`
- `templates/people/person_form.html`
- `static/system/css/billing/billing.css`
- `system/services/seeding.py`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`

## Risks and edge cases
- A dependent paid by the guardian needs to be linked to the instructor through the dependent's class.
- Family plans with more than one dependent must not duplicate the full amount for each student; the amount must be split across the linked students.
- Missing keys/API must not bring down the administrative screen.
- Rules with a zero amount must be displayed without generating an automatic payout.
- Back-office people may receive a payout even without a linked class.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding outside the seed
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling without a migration
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
OK — Playwright validated `/billing/financial/`, `/billing/payroll/`, `/billing/payouts/`, and `/me/financeiro/` at 1366x900.
### Mobile
OK — Playwright validated `/billing/financial/` at 390x844 with `financial-mobile-overflow=False`.
### Browser console
OK — Playwright returned `console_errors=0`.
### Terminal
OK for the final round — the financial routes rendered with no stack trace during the Playwright validation.

## ORM validation
### Database
OK — `inicial_seed_test` ran and created 8 test personas, a test back-office user, payout configs, and a payout history.
### Shell checks
OK — configs confirmed:
- Andre Oliveira: base `0.00`, current total `0.00`, 0 rules.
- Lauro Viana: base `0.00`, current total `0.00`, 0 rules.
- Layon Quirino: base `400.00`, current total `400.00`, 2 rules.
- Vanessa Ferro: base `0.00`, current total `0.00`, 0 rules.
- Vinicius Antonio: base `400.00`, current total `400.00`, 1 rule.
- `TeacherPayout.objects.count() == 6`.
- Local dashboard with `history_rows=12`, `local_net_inflows=904.00`, `local_outflows=1798.00`.
### Flow integrity
OK — creating a person saves the payout config for an instructor; a zero payout does not generate an automatic payment; payroll and the individual screen use the dynamic monthly calculation.

## Quality validation
### No hardcoding
OK — the requested fixed amounts were restricted to seeds; operational rules live in the versioned JSON of `TeacherPayrollConfig.notes`.
### No brittle conditional structures
OK — calculations concentrated in `system/services/payroll_rules.py` and the dashboard in `system/services/financial_dashboard.py`.
### No `except: pass`
OK — no `except: pass` introduced.
### No error masking
OK — an unavailable ASAAS/Stripe returns a provider-unavailable state with an on-screen message, without bringing down the view.
### No unnecessary comments or docstrings
OK — comments/docstrings were not added without need.

## Evidence
Commands executed:
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 305 tests, OK.
- `.\.venv\Scripts\python.exe manage.py check` — no issues.
- `.\.venv\Scripts\python.exe manage.py showmigrations` — `system [X] 0001_initial`, no new migration.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 0 copied, 164 unchanged.
- `.\.venv\Scripts\python.exe manage.py inicial_seed_test` — test seed completed.
- Playwright `.venv` — `checks=financial-desktop,payroll-desktop,payouts-desktop,own-financial-desktop,financial-mobile-overflow=False`, `console_errors=0`.

## Implemented
- An administrative financial dashboard with ASAAS and Stripe side by side, separate KPIs, a consolidated total, and a local receivable total.
- A unified financial history with order inflows and payout outflows.
- Payout rules for a fixed monthly amount, an amount per student, a percentage per student, and an amount per student/class.
- A dynamic monthly closing used in payroll, the payment queue, and the individual screen.
- Payout configuration in person creation/editing for Instructor and Back office.
- Support for an individual financial view for the instructor and back-office staff.
- An initial seed and a test seed with configs and a visible financial history.

## Deviations from plan
- No migrations were created, per project policy.
- The variable rules were persisted as versioned JSON inside `TeacherPayrollConfig.notes` to respect the existing schema.
- Playwright MCP could not open a new instance because the Chromium profile was busy; the visual validation was run with the `.venv` Playwright in an isolated browser.

## Pending
No functional pending items identified.
