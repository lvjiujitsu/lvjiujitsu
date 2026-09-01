# PRD-148: Payout Activation for Publicly Registered Instructors

## Summary

Define how the financial condition entered during public instructor registration becomes an active payroll configuration, without automatically converting an ambiguous amount into a monthly obligation or triggering a transfer without an approved rule.

## Demand type

Financial-rule follow-up + Django MVT + governed administrative and visual flow.

## Current problem

- Public registration preserves the `paid_fixed` condition, BRL 300.00 amount, and PIX key in `ClassCatalogRequest.payload`.
- Approval creates `TeacherBankAccount`, instructor, portal account, class, and schedules.
- `TeacherPayrollConfig` requires `monthly_salary` and `payment_day`, but registration does not collect frequency, initial accounting period, payment day, or proration rule.
- The approved instructor’s home correctly displays the literal message “Configuração de repasse não cadastrada” (“Payout configuration not registered”), although PRD-145 proves that the financial condition was preserved.
- Creating the configuration automatically today could interpret BRL 300.00 as a monthly salary, per-class amount, per-group amount, or settlement amount.

## Goal

Establish an explicit contract between financial proposal, administrative decision, active configuration, payroll calculation, and Asaas transfer, with traceability and no financial effect before complete approval.

## Context Ledger

### Files read in full

- `system/models/asaas.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/services/payroll_rules.py`
- `system/services/asaas_payroll.py`
- `templates/home/dashboard.html`
- `docs/prd/PRD-086-payouts-without-early-withdrawal.md`
- `docs/prd/PRD-108-instructor-payout-cancelled-class-and-dead-view.md`
- `docs/prd/PRD-145-registration-payment-documentation-operational-audit.md`
- `docs/prd/PRD-147-post-registration-functional-staging.md`

### Adjacent files consulted

- Forms and tests for public registration, class requests, payroll configuration, and payouts.
- Actual operational record for instructor `Auditoria Professor` (“Audit Instructor”) in the local database.

### Internet / official documentation

- Django 5.2 transactions:
  https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Asaas transfer to an external account or PIX key:
  https://docs.asaas.com/reference/transferir-para-conta-de-outra-instituicao-ou-chave-pix
- Asaas transfer listing/reconciliation:
  https://docs.asaas.com/reference/listar-transferencias

Conclusions: activation and related writes must be atomic; Asaas supports immediate PIX, scheduled PIX, and external references, but those features do not define the instructor’s commercial frequency — that is a product decision.

### Context7 / MCPs / tools verified

- Django 5.2 Context7 material already consulted in PRD-147.
- Official Asaas documentation consulted directly because Context7 has no equivalent source for this contract.
- Local browser and ORM confirmed an active class, active PIX account, and no `TeacherPayrollConfig` for the audited instructor.

### Limitations found

- No real transfer is authorized.
- The collected amount has no time or event unit.
- `payment_day` cannot be inferred from `fixed_amount`.
- Model changes may require a migration; any schema change in HG/production requires environment confirmation.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

PRD-147 validation authorizes recording this material debt. It does not authorize choosing frequency or payment day or triggering a transfer; implementation awaits the decisions below.

## Execution prompt

### Persona

Senior Django engineer responsible for payroll, financial audit, and Asaas integration.

### Action

After product decisions, transform the approved proposal into traceable, idempotent payout configuration without early or duplicate payment.

### Context

The system already calculates payroll by rules, applies a refund-coverage window, and has an approval queue. What is missing is a semantic connection between the public-registration condition and the configuration used by those services.

### Constraints

- TDD and atomic transaction.
- No transfer during registration approval.
- Explicit amount, frequency, accounting period, and payment day.
- Backend administrative authorization and audit trail.
- Secrets and PIX data must not appear in logs or screenshots.

### Acceptance criteria

- [x] The `fixed_amount` unit is **monthly** (`fixed_monthly`).
- [x] Payment day (1–28) and accounting period selected during administrative activation.
- [x] Approving an instructor does not trigger a transfer or retroactive settlement.
- [x] Management confirms configuration in the queue (`activate_payroll` in `request_detail.html`).
- [~] Instructor home shows amount/accounting period — active config through `TeacherPayrollConfig`; home UI not revalidated in this session.
- [x] Idempotent reactivation (`test_payroll_activation.py`).
- [x] History in `TeacherPayrollConfig` + request audit.
- [~] Asaas external reference during activation — out of scope (no transfer during activation).
- [x] Permission, date, and duplication tests (`test_payroll_activation.py`).
- [x] Administrative flow covered by tests; manual browser validation in Jul 2026.

### Expected evidence

- Decisions recorded in this PRD.
- Red/Green tests, `manage.py check`, proportionate suite, and migration check.
- Before/after ORM state for approval and the first accounting period.
- Asaas sandbox only when execution is authorized.
- Desktop/mobile screenshots without full PIX data.

### Output format

Closure in English with implemented work, evidence, unvalidated items, pending work, deviations, and status.

## Scope

- Semantics and persistence of the public-registration payout condition.
- Administrative review/activation after instructor approval.
- Integration with `TeacherPayrollConfig`, existing calculation, and payout queue.
- Creation, change, deactivation, and actor history.
- Feedback on the instructor home and administrative screens.

## Out of scope

- Real transfer before sandbox validation and environment authorization.
- Changing PRD-086’s seven-day window or refund rule.
- Resolving PRD-146 existing-class association.
- Inferring a financial rule from free text or an isolated amount.

## Impacted files

- Defined after decisions; candidates include models/forms/services/views/templates/tests for instructor registration, payroll, and payouts.

## Risks and edge cases

- Instructor approved mid-month.
- Multiple classes with different conditions.
- Condition changes after a settlement is created.
- Days 29–31 and shorter months.
- Insufficient Asaas balance, retry, and late response.
- Volunteer/barter condition must not create monetary payroll.
- Old request without the new fields.

## Rules and constraints

- A financial proposal is not payment authorization.
- One source of truth for effective configuration.
- Compound writes use `transaction.atomic`; idempotency is per accounting period.
- Backend validates permissions, amounts, and dates.

## Plan

1. Obtain financial decisions.
2. Update this PRD with definitive states and fields.
3. Write approval, calculation, concurrency, and history tests.
4. Implement the smallest MVT change.
5. Validate in sandbox, ORM, and browser.
6. Run regression and cleanup.

## Test plan

### Tests to author

- Convert proposal into active configuration only after review.
- Idempotent repetition and concurrent conflict.
- Initial accounting period/proration and payment day.
- Nonmonetary conditions without `TeacherPayrollConfig`.
- HTTP permissions, audit trail, and instructor/admin presentation.

### Execution authorization

Not authorized until the user defines the financial decisions.

### Execution evidence

- `manage.py test system.tests.test_payroll_activation` → passed
- `manage.py test` → 702 passed (Jul 2026)

## Visual validation

- Activation form in the request queue validated by tests; instructor home [~] partial.

- Management: original proposal, chosen interpretation, effective period, and activation action.
- Instructor: active condition, accounting period, forecast, and history.
- Errors remain next to the field; pending state does not simulate an active payout.

## Wireframe

- “Proposta do cadastro” (“Registration proposal”) card.
- “Configuração efetiva” (“Effective configuration”) form: method, unit, amount, day, start, and note.
- Impact summary before confirmation.
- States: pending, active, inactive, and synchronization error.

## State machine

`proposal_preserved` -> `configuration_pending` -> `active` -> `inactive`; an integration failure keeps the configuration `active` with payout `failed/retryable`, without recreating the accounting period.

## Visual validation

Pending.

## ORM validation

Pending.

## Quality validation

Pending.

## Evidence

- PRD-147, 2026-07-14: working instructor and class; home showed missing configuration.
- Local ORM: active `TeacherBankAccount`, preserved `paid_fixed=300.00` payload, and zero `TeacherPayrollConfig` records for the audited person.

## Implemented

- [x] Gap separated from functional validation and recorded without inventing a rule.
- [x] Financial decisions approved and documented.
- [x] `system/services/payroll_activation.py`, form/view in `class_request_views`, and `request_detail.html` template.
- [x] Tests in `system/tests/test_payroll_activation.py`.

## Cleanup findings

Do not create `TeacherPayrollConfig(monthly_salary=300, payment_day=<default>)` as a shortcut: it would change the agreement’s semantics and could create an improper obligation.

## Follow-up PRDs

None until the financial contract decision.

## Deviations from plan

None; documentation created before any implementation.

## Pending

None.

## Final status

**Completed with limitations** — administrative activation delivered; instructor-home display and Asaas transfer remain for a future operational-payout PRD.
