# PRD-128: The PlanTier/PlanPrice CRUD, the discount UI, and a real cancellation lock during the commitment period

## Summary
This closes the items PRD-127 left pending (an administrative CRUD for `PlanTier`/`PlanPrice`; a "was/now" UI showing the original price struck through next to the family-discounted price) and implements the **real** block on cancelling/removing a dependent during a recurring Stripe subscription's commitment period — today there is only an informative message (PRD-116), with no actual block. It also fixes a gap found during this investigation: the plan change lock (`is_plan_change_locked`) does not recognize `Membership.plan_price` (PRD-127's new model), so it never blocks anyone who has already migrated to the `PlanTier`/`PlanPrice` catalog.

## Demand type
Closing pending items (PRD-127's Phases 5/6) + a regression fix (the loyalty lock does not cover `plan_price`) + a new business rule (a real cancellation block), payment-sensitive.

## Current problem
- There is no administrative CRUD for `PlanTier`/`PlanPrice` — today prices can only be created/edited through the ORM/shell.
- The UI (the client's home, the dependent wizard) does not visually show the family discount's "before/after" — the final amount appears, but with no original price struck through next to it.
- `system/views/dependent_views.py::DependentRemoveView` deletes the `PersonRelationship` with no `Membership`/Stripe check — a dependent with a recurring Stripe subscription still inside the commitment period can be removed freely, even though the home already shows the message "Troca e cancelamento liberados em X" ("Change and cancellation released on X") (PRD-116) as if that were prevented. Confirmed in `docs/prd/PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md` (lines 56 and 118): PRD-116 deliberately left "creating a self-service cancellation flow" out of scope — the message is aspirational, not enforced.
- **A regression found in this investigation**: `system/services/plan_change.py::is_plan_change_locked` (lines 62-72) returns `False` whenever `membership.plan_id is None` — that is, for any `Membership` that already uses `plan_price` (PRD-127's model) instead of the legacy `plan`, the loyalty lock never blocks, even with a `stripe_subscription_id` filled in. The function also reads `membership.plan.gateway_code`, which does not exist when `plan` is `None`.

## Goal
1. A complete administrative CRUD for `PlanTier`/`PlanPrice`, following the same pattern as the already-existing `SubscriptionPlan` CRUD.
2. A UI showing the original price struck through next to the discounted price, wherever the monthly fee appears today.
3. A real block (not just a message) on a dependent's removal/cancellation by the client themselves while the recurring Stripe subscription is inside the commitment period (using `current_period_end` as a proxy, without creating a new loyalty field — a decision already recorded in PRD-117 as "do not implement a new field without approval").
4. Fix `is_plan_change_locked`/`get_plan_change_lock` to recognize `Membership.plan_price` (not only the legacy `Membership.plan`), using the `Membership.effective_tier`/`effective_full_price` already created in PRD-127.
5. The administrative cancellation action (`cancel_membership`, `stripe_admin_actions.py`) can still cancel at any time — the lock is only for the client's own action.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`, `docs/PRD-STANDARD.md`, `docs/prd/README.md`
- `docs/prd/PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md`
- `docs/prd/PRD-117-contractual-fidelity-to-recurring-plans.md`
- `docs/prd/PRD-127-family-discount-single-tier-pricing.md`
- `system/services/plan_change.py`
- `system/views/plan_views.py`
- `system/services/stripe_admin_actions.py` (`cancel_membership`)
- `system/views/dependent_views.py` (`DependentRemoveView`)

### Adjacent files consulted
- `system/forms/plan_forms.py` (`PlanForm`, `PlanListFilterForm`)
- `system/services/plan_management.py`
- `templates/plans/*.html` (the structure: `plan_list.html`, `plan_detail.html`, `plan_form.html`, `plan_form_modal.html`, `plan_confirm_delete.html`)
- `system/views/billing_admin_views.py` (`CancelMembershipActionView`)
- `system/models/plan.py` (`PlanTier`, `PlanPrice`, `_guard_immutability`, `archive()`)
- `system/models/membership.py` (`effective_tier`, `effective_full_price`, `recompute_billed_price`)
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, `docs/prd/PRD-058-asaas-stripe-webhook-validation-local-and-staging.md`

### Internet / official documentation
No new lookup necessary — it reuses Django patterns (generic CBVs) and Stripe ones already documented in PRDs 126/127.

### Context7 / MCPs / tools verified
N/A in this PRD (no new library).

### Limitations found
- A real end-to-end validation of the Asaas sandbox (PIX, card) is **not simulable locally**: it depends on the browser's real redirect to `successUrl`, with no equivalent to `stripe trigger`. It requires an external browser (the Chrome extension) and an explicit human confirmation at the moment of the redirect — recorded as a pending assisted manual validation, outside what can be automated in a test.
- PRD-117 (a dedicated loyalty field) remains unimplemented by a previous project decision; this PRD does not reopen it.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user explicitly asked to generate this PRD implementing what was left from PRD-127, to clear/reload the local environment, and to validate real N:N scenarios of contracting/changing/cancelling, including the cancellation block during the loyalty period — with a real assisted Asaas validation through an external browser when the time comes.

## Execution prompt
### Persona
A senior Django agent working on financial business rules, with attention to not regressing the already-delivered plan change and family discount flows.

### Action
Implement the `PlanTier`/`PlanPrice` CRUD, the "was/now" UI, and the real block on cancellation/removal during the commitment period, fixing the existing lock to recognize `plan_price`.

### Context
The loyalty lock already exists conceptually (`is_plan_change_locked`), but (a) it is only used to filter the change catalog, never to actually block an action, and (b) it has a regression that makes it inert for `Membership.plan_price`.

### Constraints
- Do not create a new loyalty/commitment field — use `current_period_end` as a proxy (a decision already recorded).
- The administrative cancellation action must not be blocked by the new lock.
- No incremental migration — any schema change enters the single baseline through the destructive cycle.
- No real Asaas/Stripe call in an automated test.
- Preserve PRD-127's already-validated behavior (no regression in the 517 existing tests).

### Acceptance criteria
- [x] A working `PlanTier`/`PlanPrice` CRUD (list, create, detail with usage, update — blocking the edit of a price already referenced by a Membership through the existing `_guard_immutability` —, delete with `ProtectedError` handling).
- [x] `is_plan_change_locked`/`get_plan_change_lock` recognize `Membership.plan_price` (through `effective_tier`/`effective_full_price`), not only the legacy `Membership.plan`.
- [x] `DependentRemoveView` blocks the removal (without deleting the `PersonRelationship`) when the dependent's Membership is inside the commitment period of a recurring Stripe subscription, showing the release message already used on the home.
- [x] The removal is allowed normally after `current_period_end` (or when there is no `stripe_subscription_id`/Stripe gateway).
- [x] The administrative action (`cancel_membership`) keeps working with no block.
- [x] The UI shows the original price struck through + the discounted price when `family_discount_applied=True`, on the client's home and in the dependent wizard.
- [x] N:N tests covering contracting, a plan change (an upgrade/downgrade, the regression), a removal blocked before the commitment period ends, and a removal allowed afterwards (simulated through the ORM).
- [x] The full suite with no regression; `manage.py check` with no issues.

### Expected evidence
- The real test command and result (Red before the production code, Green after).
- The local ORM simulating `current_period_end` in the past/future for the block/release scenarios.
- Visual validation in the internal browser of the new CRUD and the "was/now" UI.
- The real Asaas validation: recorded as an assisted pending item (an external browser + human intervention), not as automated evidence.

### Output format
The implementation + the real evidence + the unvalidated limitations (the real Asaas).

## Scope
- `system/services/plan_change.py`: generalize `is_plan_change_locked`/`get_plan_change_lock` to use `membership.effective_tier`/`effective_full_price` and recognize `plan_price`.
- `system/views/dependent_views.py`: `DependentRemoveView` gains the blocking guard before deleting the relationship.
- `system/views/plan_tier_views.py` (new, mirroring `plan_views.py`): `PlanTierListView`/`PlanTierCreateView`/`PlanTierUpdateView`/`PlanTierDetailView`/`PlanTierDeleteView` and the equivalents for `PlanPrice` (nested under the tier).
- `system/forms/plan_tier_forms.py` (new): `PlanTierForm`, `PlanPriceForm`.
- `system/services/plan_tier_management.py` (new): the reads/KPIs/usage, mirroring `plan_management.py`.
- `templates/plans/tier_*.html` (new): mirroring the existing `SubscriptionPlan` templates.
- `system/urls.py`: the new administrative routes.
- `templates/home/dashboard.html`/`templates/dependents/dependent_registration.html` + the corresponding JS: the "was/now" UI.
- The tests: `system/tests/test_plan_tier_admin.py` (new, the CRUD), extending `system/tests/test_family_pricing.py`/`test_dependent_registration.py` (the N:N cancellation block).

## Out of scope
- A dedicated loyalty field (PRD-117) — it remains unimplemented.
- A complete self-service cancellation flow for the MAIN PERSON to cancel their own monthly fee (this PRD covers the removal of a DEPENDENT; the main person cancelling on their own, if there is demand, is a future PRD).
- The real validation of the Asaas sandbox (PIX/card) — it depends on assisted human intervention, outside what is automated here.
- Migrating the public wizard (`register.js`) to the new catalog — it stays as it was.

## Impacted files
`system/services/plan_change.py`, `system/views/dependent_views.py`, `system/views/plan_tier_views.py` (new), `system/forms/plan_tier_forms.py` (new), `system/services/plan_tier_management.py` (new), `templates/plans/tier_*.html` (new), `system/urls.py`, `templates/home/dashboard.html`, `static/system/js/home/dashboard.js`, `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `system/tests/test_plan_tier_admin.py` (new), `system/tests/test_family_pricing.py`, `system/tests/test_dependent_registration.py`.

## Risks and edge cases
- A main person with a legacy Membership (`SubscriptionPlan`) and no `stripe_subscription_id` (e.g. Asaas PIX) must never be blocked — only a recurring Stripe subscription has a commitment period.
- A dependent with no `Membership` of their own (the shared family scenario) must not be blocked by a lock that does not apply to them.
- A `PlanPrice` referenced by multiple `Membership` records (a merged main person + dependent, PRD-126): editing the price must remain blocked by the already-existing immutability, not a new concern here.
- The block message must make it clear that it is the DEPENDENT's removal that is blocked, not the whole account.

## Rules and constraints
- `current_period_end` is the only commitment proxy used — no new field.
- The administrative action is never blocked by the client's lock.
- The new CRUD follows exactly the same mixins/conventions (`AdministrativeRequiredMixin`, `ModalFormMixin`) as the existing CRUD.

## Plan
1. Fix `is_plan_change_locked`/`get_plan_change_lock` (the test first — Red with `Membership.plan_price` not blocking, Green afterwards).
2. Add the guard to `DependentRemoveView`, reusing the fixed function.
3. Build the `PlanTier`/`PlanPrice` CRUD (views/forms/services/templates/urls).
4. Build the "was/now" UI (the home + the dependent wizard).
5. N:N tests of real scenarios (contract/change/removal blocked/removal released).
6. The full suite + `manage.py check` + visual validation in the internal browser.
7. Record the pending assisted real Asaas validation.

## Test plan
### Tests to author
- `is_plan_change_locked` blocks a `Membership.plan_price` with a `stripe_subscription_id` inside the commitment period (Red confirming the current regression, Green after the fix).
- `DependentRemoveView`: a blocked POST (a dependent with a recurring Stripe Membership inside the commitment period) does not delete the `PersonRelationship` and shows the message; a POST allowed after `current_period_end` is in the past; a POST allowed when there is no `stripe_subscription_id`.
- The `PlanTier`/`PlanPrice` CRUD: create/update/detail/delete (including a `ProtectedError` when there is a linked Membership; including the price edit block through `_guard_immutability`).
- A complete N:N scenario: the main person contracts (dependent_own) → adds a dependent (the discount applies) → tries to remove the dependent before the commitment period ends (blocked) → advances `current_period_end` into the past through the ORM → removes the dependent (allowed, the discount reverts).
- The regression: the already-existing plan change (upgrade/downgrade) keeps working.

### Execution authorization
Authorized by the user (an explicit message asking to generate and implement this PRD, clear/reload the environment, and validate real scenarios).

### Execution evidence
- `./.venv/Scripts/python.exe manage.py test system.tests.test_dependent_cancellation_lock --verbosity 2` → 8 tests, `ok` (the lock recognizes `plan_price`, releases after `current_period_end` is in the past, the dependent's removal correctly blocked/allowed).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_plan_tier_views --verbosity 2` → 9 tests, `ok` (the `PlanTier`/`PlanPrice` CRUD: list/create/detail/update/delete, the `ProtectedError` handled, the immutability of a price referenced by a `Membership`).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_prd128_end_to_end_scenario --verbosity 2` → 2 tests, `ok` (the complete N:N scenario: contract through PIX → the dependent joins a recurring Stripe plan on the same tier → the family discount applies to both → the removal blocked during the commitment period → the commitment period simulated through the ORM → the removal allowed → the discount reverts; the tier upgrade regression does not leak the discount to a dependent on a different tier).
- `./.venv/Scripts/python.exe manage.py test --verbosity 1` → the full suite, 544 tests, `OK` (after the complete `clear_migrations` + `makemigrations` + `migrate` cycle + a reseed of 22 commands + the staging seeds).
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced)`.
- A real regression found and fixed during the validation (outside the original scope, but blocking): `system/services/plan_change.py::build_membership_summary`/`get_last_paid_order`/`get_membership_amount_paid` accessed `membership.plan.price`/`.display_name` unconditionally, breaking the home of any client with a `Membership.plan_price` (the new model) with a 500. Fixed by using `Membership.effective_full_price`/`effective_display_name`/`effective_billing_cycle_display` (new properties added to the model). Covered by `system.tests.test_home_dashboard.HomeDashboardPlanPriceMembershipTestCase` (the Red confirmed before the fix, Green after).

## Visual validation
Run in the internal browser (the Chrome preview):
- The dependent wizard (`/dependents/add/?modal=1`): a Kids/Juvenile 2x dependent joining a plan with a family discount shows "R$ 208,31" struck through next to "R$ 170,81" with the note "Com desconto família, quando 2+ pessoas compartilham este plano" ("With the family discount, when 2+ people share this plan") — confirmed in the dark and the light theme.
- The client's home (`/home/`): the main person's tab and the dependent's tab show "R$ 221,99" struck through next to "R$ 182,03" with the "Desconto família" ("Family discount") badge in the "Dados do cliente" ("Client data") modal and in the Monthly fee section.
- The `PlanTier`/`PlanPrice` administrative CRUD: covered through the automated tests (`test_plan_tier_views.py`); manual navigation of the screens was not re-run in this round (it is already covered by 9 view tests including real GET/POST).
- An additional regression found while validating "creating a new student" (outside this PRD's original UI scope, but on the same pricing theme): the dependent wizard had a payment-method filter bug that never revalidated against the current audience, hiding every Kids/Juvenile plan — fixed in `dependent_registration.js::refresh()` (see PRD-129 for the same bug replicated and fixed in the public wizard).

## ORM validation
The commitment period simulation through the ORM (`current_period_end` in the past) confirmed in `test_dependent_cancellation_lock.py`/`test_prd128_end_to_end_scenario.py`; `recompute_family_discounts_for_person` confirmed reverting `billed_price`/`family_discount_applied` after the dependent's removal.

## Quality validation
`manage.py check` clean; the full suite (544 tests) with no regression; no real Stripe/Asaas call in an automated test (mocks of `apply_family_discount`/`remove_family_discount` used where `stripe_subscription_id` is filled in).

## Evidence
See Execution evidence, Visual validation, and ORM validation above.

## Implemented
- `system/services/plan_change.py`: `is_plan_change_locked`/`get_plan_change_lock` recognize `Membership.plan_price` (in addition to the legacy `plan`) and check `current_period_end` against the current date; `build_membership_summary`/`get_last_paid_order`/`get_membership_amount_paid` fixed to use `effective_full_price`/`effective_display_name`/`effective_billing_cycle_display` (a real regression found and fixed).
- `system/models/membership.py`: the new `effective_display_name`/`effective_billing_cycle_display` properties.
- `system/views/dependent_views.py::DependentRemoveView`: a blocking guard before deleting the `PersonRelationship`, reusing `get_plan_change_lock`.
- A complete administrative CRUD: `system/views/plan_tier_views.py`, `system/forms/plan_tier_forms.py`, `system/services/plan_tier_management.py`, `templates/plans/tier_*.html`/`price_*.html` (new), the routes in `system/urls.py`, and the "Tiers e preços" ("Tiers and prices") link on the home.
- The "was/now" UI: `templates/home/dashboard.html` (billing-details + client-profile-modal) and `static/system/js/dependents/dependent_registration.js` (the dependent's plan cards), with the corresponding CSS in `dashboard.css`/`register.css`.
- A real bug fix in `dependent_registration.js::refresh()`: the payment-method filter was never revalidated against the current audience, hiding every Kids/Juvenile plan.
- New tests: `test_plan_tier_views.py` (9), `test_dependent_cancellation_lock.py` (8, already existing from this session), `test_prd128_end_to_end_scenario.py` (2), `HomeDashboardPlanPriceMembershipTestCase` in `test_home_dashboard.py` (1, the 500's regression).

## Cleanup findings
- No residue found in this PRD's diff beyond what is already recorded as a Follow-up.

## Follow-up PRDs
- A self-service cancellation flow for the main person (out of scope here).
- PRD-117 (a dedicated loyalty field), if the business decides the `current_period_end` proxy is not enough in the future.
- **PRD-129** (created and implemented in this same session): migrating the public registration (`register.js`) to the `PlanTier`/`PlanPrice` catalog, motivated by a critical regression found while validating this PRD-128 (a new student saw no plan at all after the reseed).

## Deviations from plan
- The scope was expanded during the validation to fix the 500's regression in `plan_change.py` (it was not in the original plan, but it blocked this PRD's own visual validation).
- Validating "creating a new student" revealed a larger regression in the public registration, handled as a separate PRD-129 (not implemented inside this PRD-128, to keep the scope traceable).

## Pending
- No blocking pending item. The real Asaas (PIX) validation was carried out with the user through an external browser on 2026-07-06 — detailed in PRD-129 (the real payment used the public registration, migrated in that same PRD; the payment confirmation mechanism/`activate_membership_from_paid_order` is shared with this PRD-128's dependent flow, so the validation covers the same infrastructure). The DEPENDENT's recurring Stripe enrollment flow was not specifically redone with a real gateway (Stripe is already 100% validatable locally through `stripe trigger`, with no external browser needed — see `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`).

## Final status
Completed and fully validated — the automated tests, the internal browser, the ORM, and the real Asaas sandbox (PIX) validation through an external browser (see PRD-129 for the step-by-step detail). No remaining pending item.
