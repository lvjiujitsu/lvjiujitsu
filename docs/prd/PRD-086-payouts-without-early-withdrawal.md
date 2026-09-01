# PRD-086: Payouts without early withdrawal

## Summary of the implementation
Completely remove the early withdrawal feature and adjust the closing so payouts are only released after the 7-day refund coverage window, with a proportional deduction of refunds from future payouts.

## Demand type
Targeted fix + a financial rule.

## Current problem
The individual screen displays `Solicitar saque antecipado` (`Request an early withdrawal`) and the backend allows `request_withdrawal()`. That flow is not part of the intended product. A correct payout must come from the money that came in and was linked to the instructor/back-office member, respecting a 7-day window before releasing the balance. If there is a full or partial refund after the amount was already considered in an earlier closing, the proportional amount must be deducted from the next payouts.

## Goal
Eliminate early withdrawal from the UI, forms, views, services, and tests; keep only payouts through automatic closings. The calculation must:
- consider paid inflows only once the payment date has passed the configured 7-day window;
- record and apply proportional refund deductions;
- show the instructor/back-office member the history, the forecast, and proof of the linked inflows.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `docs/prd/PRD-012-financial-module-and-payouts.md`
- `lvjiujitsu/settings.py`
- `system/models/asaas.py`
- `system/models/registration_order.py`
- `system/forms/payroll_forms.py`
- `system/forms/__init__.py`
- `system/services/asaas_payroll.py`
- `system/services/payroll_rules.py`
- `system/services/financial_transactions.py`
- `system/services/stripe_admin_actions.py`
- `system/services/asaas_webhooks.py`
- `system/services/stripe_webhooks.py`
- `system/services/membership.py`
- `system/views/asaas_views.py`
- `templates/home/instructor/financial.html`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`

### Adjacent files consulted
- `system/views/billing_admin_views.py`
- `system/tests/test_views.py`
- `templates/billing/payout_queue.html`
- `templates/billing/payroll_list.html`

### Internet / official documentation
- Procon-SP, the 2025 Consumer Protection Code, Law 8,078/1990, art. 49 — the seven-day cooling-off period for contracts signed away from the business premises.

### MCPs / tools verified
- PowerShell + the `.venv` — OK.
- The web/official documentation — OK.
- Browser Use `iab` + Playwright — OK.

### Limitations found
- No new migration, per project policy. The proportional refund amount will be recorded in `RegistrationOrder.notes` with a versioned JSON marker.
- The current schema has no dedicated deductions ledger table. The solution preserves structured textual auditing without changing the database.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT with services.

### Action
Remove early withdrawal and implement a payout eligible after 7 days, with refund deductions.

### Context
The payout calculation lives in `system/services/payroll_rules.py`. Creating/triggering payments lives in `system/services/asaas_payroll.py`. The individual screen uses `TeacherFinancialView` and `templates/home/instructor/financial.html`.

### Constraints
- no new migration
- no early withdrawal in the UI or the backend
- do not mask refunds
- a 7-day window configurable through a setting
- the final text in Brazilian Portuguese

### Acceptance criteria
- [x] The `Meu financeiro` (`My finances`) screen must not display `Solicitar saque antecipado` (`Request an early withdrawal`).
- [x] A POST to `/me/financeiro/` must not create a `TeacherPayout`.
- [x] `request_withdrawal` and `WithdrawalRequestForm` must be removed.
- [x] An inflow paid less than 7 days ago does not enter the per-student/percentage balance.
- [x] An inflow paid more than 7 days ago enters the balance and shows the payout release date.
- [x] A full refund of an already-credited inflow generates a proportional deduction in the next closing.
- [x] A partial refund generates a proportional partial deduction.
- [x] The closing never produces a negative amount; an excess deduction is made evident in the month's summary.
- [x] Automated tests cover the withdrawal removal, the 7-day window, and the refund deduction.

### Expected evidence
- focused tests passing
- the full suite passing
- `manage.py check`
- `collectstatic --noinput` when a template/CSS changes
- visual validation of the individual screen with no early withdrawal

### Output format
Implemented code + tests + validation evidence.

## Scope
- Removing the withdrawal form and flow.
- The eligibility calculation through the 7-day window.
- Recording/parsing a refund in `RegistrationOrder.notes`.
- A proportional deduction in a future closing.
- Updating the individual screen.

## Out of scope
- A new financial ledger table.
- Automated legal research.
- A real bank transfer in the production environment.

## Impacted files
- `lvjiujitsu/settings.py`
- `system/models/asaas.py`
- `system/forms/__init__.py`
- `system/forms/payroll_forms.py`
- `system/services/asaas_payroll.py`
- `system/services/payroll_rules.py`
- `system/services/stripe_admin_actions.py`
- `system/services/membership.py`
- `system/views/asaas_views.py`
- `templates/home/instructor/financial.html`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`

## Risks and edge cases
- A refund in the same month before the instructor is paid must not generate a duplicate deduction.
- A partial refund needs to be proportional to the percentage/rule that credited the instructor.
- A refund larger than the month's payout must not create a negative payment.
- Old records with no structured marker must assume a full refund only when `payment_status=REFUNDED`.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding outside a setting/default
- no new migration
- mandatory validation

## Plan
- [x] 1. Create the Red tests
- [x] 2. Remove early withdrawal
- [x] 3. Implement the 7-day window
- [x] 4. Implement recording and deducting refunds
- [x] 5. Update the individual UI
- [x] 6. Validate
- [x] 7. Update the evidence

## Visual validation
- Browser Use `iab`: `http://localhost:8000/me/financeiro/` rendered `Meu financeiro` (`My finances`), with no `Solicitar saque antecipado` (`Request an early withdrawal`), with `Retido em cobertura` (`Held in coverage`), `Abatimentos por estorno` (`Refund deductions`), and `Disponivel para repasse` (`Available for payout`); the console with no errors.
- Playwright desktop 1366x900: no `Solicitar saque antecipado` (`Request an early withdrawal`), with the held/refunds/available figures, no horizontal overflow, the console with no errors.
- Playwright mobile 390x844: no `Solicitar saque antecipado` (`Request an early withdrawal`), with the held/refunds/available figures, no horizontal overflow, the console with no errors.

## ORM validation
- The ORM shell: Layon Quirino computed with `total=400.00`, `gross_total=400.00`, `held_total=0.00`, `refund_adjustment_total=0.00`.
- The ORM shell: `hasattr(system.services.asaas_payroll, "request_withdrawal") == False`.

## Quality validation
- `manage.py test --verbosity 2`: 335 tests OK.
- `manage.py check`: no problems.
- `manage.py showmigrations`: only `system.0001_initial` applied; no new migration created.
- `collectstatic --noinput`: not run because there was no change to a source static file.

## Evidence
- Focused: `manage.py test system.tests.test_services.PayrollRulesServiceTestCase system.tests.test_asaas system.tests.test_views.PortalViewTestCase.test_administrative_portal_account_can_open_own_financial_screen system.tests.test_views.PortalViewTestCase.test_staff_financial_screen_rejects_withdrawal_post --verbosity 2` — 27 tests OK.
- The full suite: `manage.py test --verbosity 2` — 335 tests OK.
- Check: `manage.py check` — `System check identified no issues (0 silenced).`
- Migrations: `manage.py showmigrations` — `system [X] 0001_initial`.
- Desktop/mobile visuals: Playwright confirmed the absence of the withdrawal, the presence of the new KPIs, no horizontal overflow, and no console errors.

## Implemented
- `WithdrawalRequestForm`, `request_withdrawal`, the withdrawal POST, and the `WITHDRAWAL` item of the runtime enum removed.
- `TeacherFinancialView` became read-only; a POST to `/me/financeiro/` returns 405.
- A configurable `PAYROLL_REFUND_HOLD_DAYS` added to settings with a default of 7.
- The monthly calculation now separates `gross_total`, `held_total`, `refund_adjustment_total`, `carryover_adjustment`, `entries`, `held_entries`, and `refund_entries`.
- The Stripe admin, Stripe webhook, and Asaas webhook refunds record a JSON marker in `RegistrationOrder.notes`.
- The automatic closing records the absorption of deductions and creates a zeroed closing when the month's payout is fully deducted, preserving idempotency through the monthly `TeacherPayout`.
- The `Meu financeiro` (`My finances`) screen now shows the held amount, the deductions, the balance available for payout, the released inflows, the inflows in coverage, and the refund deductions.

## Deviations from plan
- No migration created; under the project's constraint, the ledger of refunds and absorptions was persisted in `RegistrationOrder.notes` with a versioned JSON marker.

## Pending
- No blocking pending items.
- Recommended in the future: create a dedicated financial ledger table once migrations are unlocked, replacing the structured marker in `notes`.
