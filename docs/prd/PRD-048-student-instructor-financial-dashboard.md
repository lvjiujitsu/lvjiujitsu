# PRD-048: Finances on the dashboard — the instructor's payout and the student's tuition

## Summary of the implementation

Two improvements to the `/home/` screen (the unified dashboard):

1. **Payout section (instructor)**: show the current month's payout data on the instructor's dashboard — the available balance, a breakdown by method, the registered bank details, and a history of the most recent payments received.
2. **Enhanced tuition section (student)**: extend the existing tuition card with the plan's amount, the coverage period (start/end), a history of paid invoices, and a stub link for a plan upgrade/downgrade.

## Demand type

Addition of a read-only feature (no writes) displaying data that already exists in the backend.

## Current problem

- **Instructor**: sees no payout information on the home. `TeacherFinancialView` already has all the logic implemented, but with no registered URL, no template, and no link to the dashboard.
- **Student**: the `Mensalidade` (`Tuition`) section exists but shows only the status + due date. The plan's amount, the coverage period, and the invoice history (`recent_invoices`) are in the context but not rendered.

## Goal

Give each profile financial visibility directly on the home, with no extra navigation.

## Context Ledger

### Files read in full

- `templates/home/dashboard.html`
- `system/views/home_views.py`
- `system/views/asaas_views.py` (TeacherFinancialView, StaffFinancialRequiredMixin)
- `system/services/payroll_rules.py` (calculate_monthly_payroll, get_staff_financial_context)
- `system/services/asaas_payroll.py` (compute_available_balance)
- `system/urls.py`
- `static/system/css/home/dashboard.css`

### Adjacent files consulted

- `system/models/asaas.py` (TeacherPayout, TeacherPayrollConfig, TeacherBankAccount, PayoutStatus)
- `system/models/membership.py` (Membership, MembershipInvoice)
- `system/models/plan.py` (SubscriptionPlan)

### Limitations found

- `TeacherFinancialView` has the `StaffFinancialRequiredMixin` mixin requiring the instructor or back-office role — it will not be used directly; the data will be loaded in `HomeView`
- A plan upgrade/downgrade is a future feature (a visual stub only)

## Execution prompt

### Persona

Django development agent following SDD + the AGENTS.md/CLAUDE.md protocol.

### Action

Add the payout context to `HomeView` for instructors and render the two new sections in `dashboard.html`.

### Context

The dashboard already separates the context per profile (`is_instructor`, `is_student`). `calculate_monthly_payroll` and `compute_available_balance` already exist and can be called directly. The student's `billing_tabs` data already reaches the template, but the fields are not rendered.

### Constraints

- No new route, no separate new template — everything on the existing home
- No write logic — reads only
- No migrations
- Mandatory full reading before editing
- Mandatory visual validation

### Acceptance criteria

- [ ] A logged-in instructor sees a `Repasse` (`Payout`) section on the home with: the amount receivable for the month, a breakdown by method, the next payment, and the payout history (verifiable: visual)
- [ ] An instructor with no payout config sees the section with an appropriate empty state (verifiable: visual)
- [ ] An instructor with registered bank details sees the PIX key and its type (verifiable: visual)
- [ ] A logged-in student sees in the `Mensalidade` (`Tuition`) section: the plan name, amount, cycle, and the start/end period (verifiable: visual)
- [ ] A student with paid invoices sees a list of recent invoices with the date and amount (verifiable: visual)
- [ ] An overdue student sees a `Pagar agora` (`Pay now`) button (already existing — confirm it works)
- [ ] The `Trocar plano` (`Change plan`) button appears disabled as a stub (verifiable: visual)
- [ ] `manage.py test --verbosity 2` passes with no failures (verifiable: terminal)
- [ ] `manage.py check` passes (verifiable: terminal)
- [ ] The browser console has no critical JavaScript errors (verifiable: DevTools)

### Expected evidence

- A screenshot of the instructor's payout section
- A screenshot of the student's tuition section with invoices
- A terminal with passing tests

## Scope

1. `system/views/home_views.py` — add the imports and the instructor context block
2. `templates/home/dashboard.html` — add the Payout section (instructor) and extend the Tuition section (student)
3. `static/system/css/home/dashboard.css` — add the visual tokens for the new sections
4. Update `?v=` in the template and the CSS

## Out of scope

- The real implementation of a plan upgrade/downgrade
- A dedicated instructor finance screen
- An invoice history with pagination
- Editing the bank details

## Impacted files

| File | Change |
|---|---|
| `system/views/home_views.py` | a new `if is_instructor` block with the payout data |
| `templates/home/dashboard.html` | a new `#section-repasse` section (instructor) + extra fields in `#section-billing` |
| `static/system/css/home/dashboard.css` | tokens and classes for the new components |

## Risks and edge cases

- An instructor with no `TeacherPayrollConfig`: `calculate_monthly_payroll` returns `_empty_calculation` — handle it in the template
- An instructor with no `TeacherBankAccount`: handle the absence with an empty state
- A student with dependents' `billing_tabs`: the extra fields must appear in each tab
- `recent_invoices` may be empty even with an active membership — show an empty state

## Rules and constraints

- SDD before code
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory visual validation

## Plan

- [x] 1. Full reading of the files in the flow
- [ ] 2. Add the instructor context to HomeView
- [ ] 3. Update the template: the Payout section (instructor)
- [ ] 4. Update the template: the extended Tuition section (student)
- [ ] 5. Update the CSS with the new components
- [ ] 6. Run the tests and the check
- [ ] 7. Visual validation
- [ ] 8. Cleanup and asset version bump

## Visual hierarchy

- Reading pattern: F Pattern (an operational information screen)
- Section title: weight 600, the `--text` token
- Value labels: weight 500, the `--text` token
- Monetary values: weight 700, the `--text` token, with the total emphasized in `--brand-red`
- Help text/dates: weight 400, the `--muted` token
- Primary action (Pay): `--brand-red`, weight 600
- Disabled action (Change plan): `--border` border, weight 500, `opacity 0.45`

## Wireframe

### Section: Payout (instructor)

```
[▼] Payout                          [reference month]
┌────────────────────────────────────────────────────┐
│  [balance card]                                    │
│   Amount receivable  R$ XXX.XX                     │
│   Expected payment   MM/DD                         │
├────────────────────────────────────────────────────┤
│  [breakdown]                                        │
│   Monthly fixed      R$ XXX.XX                     │
│   Per student        R$ XXX.XX  (N students)       │
│   Adjustments/refunds R$ -XX.XX                    │
│   ─────────────────────────────                    │
│   Total              R$ XXX.XX                     │
├────────────────────────────────────────────────────┤
│  [bank details]                                     │
│   PIX key            CPF / xxx.xxx.xxx-xx          │
├────────────────────────────────────────────────────┤
│  [payout history]                                   │
│   MM/DD/YYYY   R$ XXX.XX   ● Paid                 │
│   MM/DD/YYYY   R$ XXX.XX   ● Approved             │
└────────────────────────────────────────────────────┘
```

### Section: Tuition (student) — extended

```
[▼] Tuition
┌────────────────────────────────────────────────────┐
│  [status badge]  Plan name                         │
│  Amount: R$ XX.XX / monthly                       │
│  Coverage: 05/01/2026 → 06/01/2026              │
│  [Pay now button] (when overdue)                  │
│  [Change plan button] (disabled — stub)           │
├────────────────────────────────────────────────────┤
│  Recent invoices                                   │
│   MM/DD/YYYY   R$ XX.XX   ● Paid                  │
│   MM/DD/YYYY   R$ XX.XX   ● Paid                  │
└────────────────────────────────────────────────────┘
```

## State machines

### Payout section — the balance card

- `no_config`: no configuration on record → an empty-state `Configuração de repasse não cadastrada` (`Payout configuration not registered`)
- `config_inactive`: the config exists but is inactive → an `Inativo` (`Inactive`) badge
- `active_zero`: the config is active, total = 0 → `R$ 0,00 — sem alunos vinculados no mês` (`R$ 0.00 — no students linked this month`)
- `active_positive`: the config is active, total > 0 → the amount emphasized + the expected date

### Tuition section — the card

- `no_plan`: no membership → `Nenhum plano ativo` (`No active plan`)
- `pending`: a pending order → an `Ir para pagamento` (`Go to payment`) button
- `active`: active → the plan, amount, and coverage period
- `past_due`: overdue → a red badge + a `Pagar agora` (`Pay now`) button
- `exempted`: exempt → a green badge + no monetary amount

## Visual validation

### Desktop

- [x] The payout section visible for a logged-in instructor — the correct empty state when there is no config
- [x] The tuition section with the amount (R$ 228.80) and the period (24/05/2026 → 24/06/2026) for a logged-in student

### Mobile

- [ ] Not validated in a reduced viewport (the preview environment has no resize)

### Browser console

- [x] No critical JavaScript errors

### Terminal

- [x] `manage.py test --verbosity 2` — 171 tests, 0 failures
- [x] `manage.py check` — 0 issues

## Evidence

- The instructor (André): the `Repasse` (`Payout`) section rendered with the correct empty state (no payout config on record)
- The student (Wagner): the `Mensalidade` (`Tuition`) section with an Active badge, the plan, the amount R$ 228.80/monthly, the period 24/05–24/06/2026, and the `Trocar plano` (`Change plan`) button disabled
- Console: no JavaScript errors
- 171 tests passing

## Implemented

- `system/views/home_views.py`: the imports + the `_build_instructor_payroll_context` function + an `if is_instructor` block in `get_context_data` + the default context in `_empty_context`
- `templates/home/dashboard.html`: a new `Repasse` (`Payout`) section for the instructor + extra fields (amount, period, invoices) in the `Mensalidade` (`Tuition`) section + `?v=13`
- `static/system/css/home/dashboard.css`: the `.payroll-*` and `.billing-meta`, `.billing-invoices`, `.billing-invoice-*` classes

## Deviations from plan

- None

## Pending

- The real implementation of a plan upgrade/downgrade (out of scope)
- Mobile validation not performed (the environment has no resize in the preview)
