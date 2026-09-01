# PRD-007: Reformulate plans, pricing, eligibility, and Adult vs Kids/Juvenile targeting

## Summary of the implementation

Full reformulation of the academy's commercial plan structure, separating audience (Adult vs Kids/Juvenile), frequency (2x or 5x per week), type (Individual vs Family), and cycle (monthly/quarterly/biannual/annual), with new pricing that guarantees R$ 200 net per student/month and internalizes the 50% payout to the Kids/Juvenile instructor. Includes eligibility rules (who sees which plans) applied during registration, in the shop, and in the plan change flow.

## Demand type

Architectural change with a new commercial feature. Includes a schema change, a seed rewrite, new business rules (eligibility), a UI update, and adjustments to the plan change flows.

## Current problem

The current structure has 12 simple plans (Standard/Family × Monthly/Quarterly/Annual × PIX/Card), with no distinction of audience or weekly frequency. This creates three problems:

1. **The company can fall below the financial minimum** when the student is Kids/Juvenile (the instructor receives 50% per student, and the current price does not absorb that payout).
2. **There is no 2x/5x commercial anchoring**, which is the main desired upsell lever.
3. **The family plan is shown to everyone** indiscriminately, even to a solo adult (with no family group) or a guardian with only 1 dependent.

## Goal

- Ensure the company never receives less than R$ 200.00 net per student/month.
- Introduce 2x and 5x frequency as commercial anchoring (2x = entry offer, 5x = flagship).
- Separate Adult and Kids/Juvenile into their own tables, embedding the instructor payout into Kids.
- Apply clear eligibility rules for the Family plan and for Kids/Juvenile 5x.
- Keep PIX (Asaas) with a commercial discount and Card (Stripe) at full, installable price.

## Context Ledger

### Files read in full

- [system/models/plan.py](system/models/plan.py) — the current `SubscriptionPlan` model
- [system/models/membership.py](system/models/membership.py) — `Membership` with a `PROTECT` FK to the plan (prevents deletion)
- [system/models/person.py](system/models/person.py) — `Person`, `PersonRelationship`, `PersonRelationshipKind.RESPONSIBLE_FOR`
- [system/models/category.py](system/models/category.py) — `CategoryAudience` (ADULT/JUVENILE/KIDS/WOMEN), `IbjjfAgeCategory`
- [system/services/seeding.py](system/services/seeding.py) — the current `seed_plans()` and `SUBSCRIPTION_PLAN_DEFINITIONS`
- [system/services/membership.py](system/services/membership.py) — subscription orchestration, `get_active_membership`, cycles
- [system/services/plan_change.py](system/services/plan_change.py) — prorated upgrade/downgrade calculation
- [system/services/registration_checkout.py](system/services/registration_checkout.py) — `get_plan_catalog_payload()`, `get_registration_plan_multiplier()`, order creation
- [system/services/financial_transactions.py](system/services/financial_transactions.py) — provider/checkout action by plan, fee calculation
- [system/services/plan_management.py](system/services/plan_management.py) — simple plan reads
- [system/forms/registration_forms.py](system/forms/registration_forms.py) — `_clean_plan_selection`, `_is_family_plan_allowed`
- [system/forms/plan_forms.py](system/forms/plan_forms.py) — the `PlanForm` admin form
- [system/services/registration_validation.py](system/services/registration_validation.py) — per-step validation of the wizard
- [system/views/plan_change_views.py](system/views/plan_change_views.py) — `PlanChangeSelectView` groups by `is_family_plan`
- [system/views/product_views.py](system/views/product_views.py) — authenticated shop and catalog
- [system/views/plan_views.py](system/views/plan_views.py) — public catalog and admin CRUD
- [system/admin.py](system/admin.py) — `SubscriptionPlanAdmin`
- [system/constants.py](system/constants.py) — `PersonTypeCode`, `RegistrationProfile`, `CheckoutAction`
- [system/tests/test_plan_models.py](system/tests/test_plan_models.py) — tests of the model and the current seed
- [system/tests/test_plan_views.py](system/tests/test_plan_views.py) — tests of the plan views
- [templates/billing/plan_change_select.html](templates/billing/plan_change_select.html) — plan change UI
- [system/migrations/0001_initial.py](system/migrations/0001_initial.py) — initial `SubscriptionPlan` schema
- The relevant section of [static/system/js/auth/registration-wizard-clean.js](static/system/js/auth/registration-wizard-clean.js) (wizard plan filtering, `groupPlansForDropdown`, `getVisiblePlanCatalog`, `isFamilyPlanEligible`)

### Adjacent files consulted

- [system/forms/product_forms.py](system/forms/product_forms.py)
- [system/services/plan_management.py](system/services/plan_management.py)
- [system/models/registration_order.py](system/models/registration_order.py) (FKs/PROTECT)

### Internet / official documentation

- Brazilian Law 13,455/2017 (price differentiation by payment instrument) — the legal basis used in the PIX/Card messaging
- Asaas (PIX fee R$ 1.99) and Stripe Brazil (3.99% + R$ 0.39, R$ 55 chargeback) — references from the demand document

### MCPs / tools verified

- `Read`, `Grep`, `Glob`, `Bash` — working in the Windows environment
- `manage.py test` — available through `.venv`

### Limitations found

- A schema change is **required** (fields `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization`). `CLAUDE.md` §8 and §24 and `AGENTS.md` §15 forbid hand-writing a migration file — in this project a schema change is made through the destructive cycle `clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds, which regenerates `0001_initial.py` from scratch. All model, service, seed, and test work must be ready **before** requesting authorization to run the cycle.
- Stripe Sync will not be re-triggered in this delivery — the old Stripe Price IDs disappear along with `0001_initial.py` during the reset; re-synchronization belongs to a later PRD.
- Cancellation policy, refunds, and the complete N:N upgrade/downgrade matrix are out of this delivery — they go into PRD-008.
- The single-day pass does not yet have a dedicated product/service entity and is out of this delivery (PRD-009).

## Execution prompt

### Persona

Senior Django development agent working in control-first mode with SDD + TDD.

### Action

Reformulate the plan domain of the `system` app according to the specification below, keeping backward compatibility with legacy `Membership` records by deactivating (not deleting) the old plans.

### Context

The academy operates with Stripe (card) + Asaas (PIX), has registration with HOLDER/GUARDIAN/OTHER profiles, and Adult/Juvenile/Kids/Women classes. The demand splits the commercial domain into two tables (Adult and Kids/Juvenile) based on who trains and what payout the instructor receives.

### Constraints

- no hardcoded secrets
- no error masking
- hand-writing a migration file is **forbidden**; schema changes happen through the destructive cycle (only `0001_initial.py` may exist after the cycle)
- mandatory full reading (completed above)
- tests must keep passing
- since the destructive cycle wipes the database, legacy plans do not need to be preserved — it is enough to rewrite the seed so it already generates the new matrix
- PIX/Card messaging follows the document (full price on card, commercial discount on PIX)

### Acceptance criteria

- [ ] `SubscriptionPlan` gains the fields `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization` (verifiable: reading the model + `showmigrations` showing only `0001_initial`)
- [ ] `seed_plans()` produces 64 new plans with the matrix Adult/Kids × 2x/5x × Individual/Family × 4 cycles × 2 methods (verifiable: unit test over counts and samples)
- [ ] Each plan's price respects the table in the document (verifiable: sample tests for each combination)
- [ ] After the destructive cycle, only `0001_initial.py` exists in `system/migrations/` (verifiable: `ls`)
- [ ] A solo adult (no dependents) only sees Adult Individual plans during registration (verifiable: form test)
- [ ] An adult with a dependent sees Adult + Kids/Juvenile; Family is only unlocked when the group has 2+ active students (verifiable: form test)
- [ ] A guardian with 1 Kids dependent only sees Kids Individual (verifiable: form test)
- [ ] A guardian with 2+ Kids dependents sees Kids Individual + Family (verifiable: form test)
- [ ] The Kids 5x plan is not displayed without authorization (verifiable: the `requires_special_authorization=True` field filtered by default)
- [ ] `plan_change_select.html` groups plans by audience and frequency (verifiable: reading the template)
- [ ] The wizard JavaScript filters plans by the correct audience (verifiable: manual navigation + reading the payload)
- [ ] `manage.py test --verbosity 2` passes with 0 failures
- [ ] `manage.py check` passes with no new warnings

### Expected evidence

- passing tests
- `manage.py showmigrations` showing only `system.0001_initial` (regenerated)
- clean browser console on the registration and plan change screens
- terminal with no stack traces
- an ORM shell check showing the 64 new active plans

### Output format

Code + tests + evidence report.

## Scope

1. The `SubscriptionPlan` model gains 4 new fields (changing `code`'s `max_length` if necessary).
2. Rewrite `SUBSCRIPTION_PLAN_DEFINITIONS` in `seeding.py`, generated programmatically from a base-price matrix and cycle multipliers (64 plans).
3. A new selector `system/selectors/plan_eligibility.py` with a pure function to filter plans by registration/portal context.
4. Update `_clean_plan_selection` in `registration_forms.py` to use the new selector and respect `audience`/`requires_special_authorization`.
5. Update `PlanChangeSelectView` to use the selector and group by `audience` + `weekly_frequency`.
6. Update `get_plan_catalog_payload()` to enrich the payload with `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization`.
7. Update the wizard JavaScript to filter by audience/frequency according to the profile + selected dependents.
8. Update the `plan_change_select.html` template for the new anchoring (5x first, 2x after; Family visible only when eligible).
9. Update `SubscriptionPlanAdmin` with the new fields.
10. Update the `PlanForm` admin form with the new fields.
11. Adjust `get_registration_plan_multiplier` (remove the doubling for Kids+Juvenile — the payout is already in the new price).
12. Test coverage for the model, seed, eligibility, form, view, and wizard payload.
13. Destructive cycle: request authorization and run `clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds.

## Out of scope

- The complete cancellation, refund, and chargeback policy (PRD-008).
- The N:N upgrade/downgrade matrix across all 64 plans (PRD-008).
- The single-day pass as a product (PRD-009).
- Stripe re-synchronization (Price archival, new Prices) — deferred to PRD-010.
- An administrative screen to view "student X's eligibility".

## Impacted files

- [system/models/plan.py](system/models/plan.py)
- [system/models/__init__.py](system/models/__init__.py) (exports the new enums)
- [system/migrations/0001_initial.py](system/migrations/0001_initial.py) — regenerated by the destructive cycle
- [system/services/seeding.py](system/services/seeding.py)
- [system/services/registration_checkout.py](system/services/registration_checkout.py) (`get_plan_catalog_payload`, `get_registration_plan_multiplier`)
- [system/selectors/plan_eligibility.py](system/selectors/plan_eligibility.py) (new)
- [system/forms/registration_forms.py](system/forms/registration_forms.py)
- [system/forms/plan_forms.py](system/forms/plan_forms.py)
- [system/views/plan_change_views.py](system/views/plan_change_views.py)
- [system/views/plan_views.py](system/views/plan_views.py) (the public catalog may need new grouping)
- [system/admin.py](system/admin.py)
- [static/system/js/auth/registration-wizard-clean.js](static/system/js/auth/registration-wizard-clean.js)
- [templates/billing/plan_change_select.html](templates/billing/plan_change_select.html)
- [system/tests/test_plan_models.py](system/tests/test_plan_models.py)
- [system/tests/test_plan_eligibility.py](system/tests/test_plan_eligibility.py) (new)
- [system/tests/test_forms.py](system/tests/test_forms.py)
- [system/tests/test_services.py](system/tests/test_services.py) (if necessary)

## Risks and edge cases

- **Regenerated database:** the destructive cycle wipes `db.sqlite3` and rewrites `0001_initial.py`. The local environment comes back clean; no production data is touched because the production database is not here.
- **An adult who is also a guardian (holder + dependent):** eligible for Adult Individual + Adult Family + Kids Individual + (Kids Family when 2+ kids).
- **A family with 1 adult + 1 Kids dependent:** eligible for Adult 2x/5x Family and Kids 2x Individual. Not eligible for Kids Family (which needs 2+ kids).
- **Kids 5x:** excluded from the payload by default. It will be shown only when marked as authorized (a field on the plan + the student's authorization; in this delivery it stays hidden always — administrative authorization goes to PRD-010, but the gating already exists in the `requires_special_authorization` field).
- **`get_registration_plan_multiplier`:** today it multiplies the price by 2 when KIDS+JUVENILE are in the same enrollment group. With the new Kids pricing embedding the 50% payout, this logic becomes **redundant and harmful** (double charging). Remove/zero it.

## Rules and constraints

- SDD before code
- TDD for the implementation (tests first for model/seed/eligibility)
- no hardcoding
- no error masking
- hand-writing a migration is **forbidden**; mandatory use of the destructive cycle described in `CLAUDE.md` §24
- mandatory full reading (completed)
- mandatory validation

## Plan

- [x] 1. Context and full reading
- [x] 2. Update the `SubscriptionPlan` model (fields + enums + exports)
- [ ] 3. Update the model tests (Red → Green)
- [ ] 4. Rewrite `seed_plans` (Red → Green)
- [ ] 5. Create the `plan_eligibility` selector (Red → Green)
- [ ] 6. Update the wizard form
- [ ] 7. Update the plan change view
- [ ] 8. Adjust `get_registration_plan_multiplier` (no Kids doubling)
- [ ] 9. Update the wizard JavaScript
- [ ] 10. Update the templates
- [ ] 11. Update the admin/PlanForm
- [ ] 12. Refactor where it makes sense (DRY in the matrix generation)
- [ ] 13. Request authorization and run the destructive cycle (`clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds)
- [ ] 14. `manage.py check` and `collectstatic` if necessary
- [ ] 15. In-browser visual validation
- [ ] 16. Final cleanup
- [ ] 17. Documentation update (this PRD + report)

## Visual validation

### Desktop

- Registration screen (`/portal/cadastro`) — plan and checkout steps, with Adult/Guardian + dependent profiles
- Plan change screen (`/portal/financeiro/trocar-plano`) — grouping by audience/frequency
- Public plan catalog (`/planos`) — display with the new anchoring

### Mobile

- The same three screens in a viewport ≤ 480px

### Browser console

- No JavaScript errors on load and on plan selection
- No asset 404s (cache-busting `?v=` updated)

### Terminal

- `runserver` with no stack traces
- No new `DeprecationWarning`

## ORM validation

### Database

- 76 plans in total: 64 active (new) + 12 inactive (legacy)

### Shell checks

```python
from system.models import SubscriptionPlan
SubscriptionPlan.objects.filter(is_active=True).count()  # 64
SubscriptionPlan.objects.filter(is_active=False).count() # 12
SubscriptionPlan.objects.filter(audience="kids_juvenile", weekly_frequency=5).count()  # 16
```

### Flow integrity

- `Membership.objects.filter(plan__is_active=False).count()` returns the expected number when old memberships exist.

## Quality validation

### No hardcoding

Prices live in a dictionary matrix in `seeding.py`; cycle multipliers are named constants. No secrets.

### No brittle conditional structures

The selector uses short guard clauses; nothing with more than 2 levels of nesting.

### No `except: pass`

Not introduced.

### No error masking

Validations raise `ValidationError` with clear messages.

### No unnecessary comments or docstrings

Self-explanatory names. Comments only for non-obvious decisions (the legal table, the 50% payout).

## Evidence

(to be filled in after implementation)

## Implemented

(to be filled in after implementation)

## Deviations from plan

(to be filled in after implementation)

## Pending

- PRD-008: cancellation, refund, and chargeback policy; the complete upgrade/downgrade matrix
- PRD-009: the single-day pass as a product
- PRD-010: administrative authorization for Kids 5x and Stripe re-synchronization
