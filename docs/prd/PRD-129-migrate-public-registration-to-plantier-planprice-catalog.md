# PRD-129: Migrating the public registration (`register.js`) to the PlanTier/PlanPrice catalog

## Summary
This fixes a critical regression discovered during PRD-128's end-to-end validation: after the complete `clear_migrations` + reseed cycle, the public registration (`/register/`, `register.js`/`registration_forms.py`/`auth_views.py`) shows **no plan at all** to a new student (Adult or Kids/Juvenile, non-Veteran), because PRD-127 migrated the Individual/Family plans to `PlanTier`/`PlanPrice` and the new seed no longer recreates priced SKUs in `SubscriptionPlan` for non-Veterans. The public registration kept reading exclusively from `SubscriptionPlan` (a deliberate PRD-127 decision to contain the blast radius), and that decision stopped being sustainable once the legacy catalog of sellable plans went empty.

## Demand type
A critical regression fix (it blocks the system's highest-traffic flow — a new student's registration), payment-sensitive.

## Current problem
- The `SubscriptionPlan` records with `code in ("individual", "family")` are `is_active=False` after the reseed (PRD-127); only the `loyalty-*` (Veteran) variants remain active.
- `system/views/auth_views.py::PortalRegisterView.get_context_data` calls `get_plan_catalog_payload()` without `include_plan_prices=True`, so the catalog JSON sent to `register.js` contains only the Veteran variants.
- A new student, not eligible for Veteran, sees the message "Nenhum plano disponível para esta pessoa." ("No plan available for this person.") in the plan step and cannot proceed to the payment — the public registration is effectively broken for the majority audience (new students).
- Confirmed through the internal browser (the Chrome preview): the complete public wizard flow up to step 6/8 ("Escolha seu plano" — "Choose your plan"), with an empty catalog of sellable plans.

## Goal
Migrate the public registration to the same dual-source catalog (the legacy `SubscriptionPlan` with a `sp:<pk>` prefixed id + the new `PlanPrice` with a `pp:<pk>` prefixed id) already used successfully by the add-a-dependent wizard (PRD-127 Phase 4), preserving 100% of the behavior currently covered by tests (the audience eligibility, the family plan, Veteran, the special authorization, the per-order people multiplier).

## Context Ledger
### Files read in full
- `system/forms/registration_forms.py` (the `selected_plan` field, `_clean_plan_selection`, `_build_plan_ineligible_message`)
- `system/services/registration_checkout.py` (`resolve_catalog_plan`, `build_catalog_plan_id`, `parse_selected_plan_payload`, `create_registration_order`, `_count_group_members`, `_count_training_persons`, `get_plan_catalog_payload`, `_build_legacy_plan_catalog_payload`, `_build_plan_price_catalog_payload`)
- `system/services/pre_registration.py` (`save_pre_registration_from_form`, `create_or_update_pre_registration` — with no callers, dead code —, `finalize_pre_registration`, `normalize_snapshot_for_form`, `build_wizard_form_snapshot`)
- `system/services/financial_transactions.py` (`resolve_checkout_action_for_plan`, `resolve_payment_provider_for_plan`)
- `system/selectors/plan_eligibility.py` (`is_plan_eligible`, `build_eligibility_context_for_registration`, `PlanEligibilityContext`)
- `system/views/auth_views.py` (`PortalRegisterView`, `FinalizeRegistrationView`)
- `static/system/js/auth/register.js` (`renderPlanCards`, `selectPlan`, `syncSelectedPlansPayload`)
- `system/models/plan.py` (`PlanPrice` — it confirms that `payment_method`/`gateway_code` exist natively, compatible with `resolve_checkout_action_for_plan`/`resolve_payment_provider_for_plan` with no adaptation)

### Adjacent files consulted
- `system/services/dependent_registration.py`/`dependent_forms.py` — the reference pattern already validated in the local production (PRD-127's Phase 4) for the same ID migration.
- `system/tests/test_pre_registration_service.py`, `system/tests/test_register_wizard_contract.py` — the existing coverage of the public flow.

### Internet / official documentation
No new lookup — it reuses the Django pattern (`forms.CharField`, `ModelForm` cleaning) already used in PRDs 126/127/128.

### Context7 / MCPs / tools verified
N/A — no new library.

### Limitations found
- `create_or_update_pre_registration` (`pre_registration.py`) is dead code (with no caller in the repository) — it will not be migrated in this PRD; it is recorded as possible future cleanup (`lv-cleanup-audit`).
- The "family plan" flow through `SubscriptionPlan.is_family_plan` becomes, in practice, unreachable for new clients because there is no active `is_family_plan=True` row any more — the group multiplier (`_count_group_members`) stays in the code for historical compatibility (it breaks nothing), but no test depends on it being reachable.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user explicitly confirmed (an objective question with 3 alternatives) the "Migrate the public wizard to the new catalog" option, rather than reverting the seed or merely recording the pending item.

## Execution prompt
### Persona
A senior Django agent working on financial business rules, attentive to not regressing the public registration flow (the system's highest traffic volume).

### Action
Migrate the public registration's `selected_plan` from an `IntegerField`/`SubscriptionPlan.pk` to a `CharField` accepting prefixed ids (`sp:<pk>`/`pp:<pk>`), resolved through the already-existing `resolve_catalog_plan`.

### Context
The dependent wizard already solves exactly this problem (`dependent_forms.py::_clean_financial_choice`, `dependent_registration.py::_legacy_selected_plan`) — this PRD replicates the same pattern for `registration_forms.py`/`pre_registration.py`/`registration_checkout.py`/`register.js`.

### Constraints
- No schema migration (no new field is necessary — `RegistrationOrder.plan_price_ref` already exists from PRD-127).
- Preserve 100% of the behavior currently covered by `test_pre_registration_service.py`/`test_register_wizard_contract.py`.
- A `PlanPrice` never has `is_family_plan`/`is_loyalty_plan`/`requires_special_authorization` — the eligibility for a `pp:<pk>` selection uses a simplified check (audience only), without reusing `is_plan_eligible` (which presumes attributes exclusive to `SubscriptionPlan`).
- No real Asaas/Stripe call in an automated test.
- Do not change `create_or_update_pre_registration` (dead code, out of scope).

### Acceptance criteria
- [x] `selected_plan` (the public form) accepts and resolves the `sp:`/`pp:` prefixed ids through `resolve_catalog_plan`.
- [x] `get_plan_catalog_payload(include_plan_prices=True)` used in `auth_views.py`, and the public catalog now includes the active `PlanTier`/`PlanPrice` tiers.
- [x] `create_registration_order` creates the `RegistrationOrder` correctly for both cases (`plan=`/`plan_price_ref=`), preserving the order's per-people multiplier.
- [x] `save_pre_registration_from_form` does not try to assign a prefixed string to `selected_plan_id` (an integer FK) — it writes `None` when the selection is a `PlanPrice`, preserving the raw snapshot for a later reconstruction.
- [x] `register.js`: `data-plan-id` is no longer converted through `parseInt`; any static contract test (`test_register_wizard_contract.py`) that today checks the absence of `parseInt` stays valid, and no new `parseInt` over a plan is introduced.
- [x] A manual test in the internal browser confirms that a new Adult student and a new Kids/Juvenile student see real sellable plans in the "Escolha seu plano" ("Choose your plan") step after the complete reseed.
- [x] The full suite with no regression; `manage.py check` with no issues.

### Expected evidence
- The real test command and result (Red before the production code where applicable, Green after).
- Visual validation in the internal browser showing the populated catalog for Adult and Kids/Juvenile.
- The real Asaas/Stripe validation: out of this PRD's scope (the same limitation already recorded in PRD-128 — it depends on an external browser and human intervention).

### Output format
The implementation + the real evidence + the unvalidated limitations.

## Scope
- `system/forms/registration_forms.py`: `selected_plan` becomes a `CharField`; `_clean_plan_selection` resolves through `resolve_catalog_plan`, with a simplified branch for `PlanPrice` (with no family/Veteran/special authorization).
- `system/services/registration_checkout.py`: `create_registration_order` resolves `plan_id` through `resolve_catalog_plan`, populating `RegistrationOrder.plan` OR `RegistrationOrder.plan_price_ref` according to the resolved type.
- `system/services/pre_registration.py`: `save_pre_registration_from_form` only assigns `selected_plan_id` when the selection resolves to a legacy `SubscriptionPlan` (through a local helper), avoiding a `ValueError` when saving a prefixed string into an `IntegerField`/FK.
- `system/views/auth_views.py`: `get_plan_catalog_payload(include_plan_prices=True)`.
- `static/system/js/auth/register.js`: remove the `parseInt` from the plan selection (`selectPlan`/the `.plan-card` click handler); bump the asset's version.
- `templates/login/register.html`: bump the script's `?v=`.
- The tests: extend `system/tests/test_pre_registration_service.py` (the end-to-end PlanPrice flow) and `system/tests/test_register_wizard_contract.py` (if necessary); a new dedicated test for `create_registration_order`/`_clean_plan_selection` with a `PlanPrice`.

## Out of scope
- Reopening the "family plan" model as an SKU (`SubscriptionPlan.is_family_plan`) — it stays as it was, only unreachable in practice for lack of active data.
- `create_or_update_pre_registration` (dead code).
- The real Asaas/Stripe sandbox validation — the same limitation as PRD-128.
- Any change to the dependent wizard (already migrated in PRD-127).

## Impacted files
`system/forms/registration_forms.py`, `system/services/registration_checkout.py`, `system/services/pre_registration.py`, `system/views/auth_views.py`, `static/system/js/auth/register.js`, `templates/login/register.html`, `templates/login/installment_select.html` (if it references the same asset version), `system/tests/test_pre_registration_service.py`, `system/tests/test_register_wizard_contract.py`.

## Risks and edge cases
- A draft `PreRegistration` created BEFORE this change, with a legacy (integer) `selected_plan_id`, must keep being read correctly — `resolve_catalog_plan` receives prefixed strings; old snapshots with a plain "15" (no prefix) do not exist in the local production (a single development environment, with no real legacy data to preserve), but the resolution code must degrade with no unhandled exception.
- `RegistrationOrder.plan` is `on_delete=PROTECT`; when creating an order from a `PlanPrice`, `plan` must stay `None` (do not use an arbitrary `SubscriptionPlan`) and `plan_price_ref` must point at the correct `PlanPrice`.
- The per-people multiplier (`_count_training_persons`/`_count_group_members`) must keep being applied over the correct unit price (`plan.price` or `plan_price.price`), without duplicating or zeroing the total.
- The eligibility error messages for a `PlanPrice` need to be clear even without `SubscriptionPlan`'s attributes (they cannot call `_build_plan_ineligible_message` blindly).

## Rules and constraints
- No schema migration.
- No real gateway call in an automated test.
- Follow exactly the pattern already established in `dependent_forms.py`/`dependent_registration.py` (reuse `resolve_catalog_plan`/`build_catalog_plan_id`, do not reinvent).

## Plan
1. `registration_checkout.py::create_registration_order` — rewrite it to use `resolve_catalog_plan` (the test first).
2. `registration_forms.py::_clean_plan_selection` — switch `IntegerField`→`CharField`, with a simplified `PlanPrice` branch (the test first).
3. `pre_registration.py::save_pre_registration_from_form` — fix the `selected_plan_id` assignment (the test first).
4. `auth_views.py` — `include_plan_prices=True`.
5. `register.js` — remove the `parseInt` from the plan selection; bump the version.
6. The full suite + `manage.py check` + visual validation in the internal browser (a new Adult and a new Kids/Juvenile seeing real plans).

## Test plan
### Tests to author
- `create_registration_order` with a `pp:<pk>` selection creates a `RegistrationOrder` with `plan=None`, `plan_price_ref=<PlanPrice>`, and the correct total multiplied by the order's people.
- `create_registration_order` with an `sp:<pk>` selection (Veteran) keeps working with no regression (an explicit non-regression).
- `_clean_plan_selection`/the form: a `pp:<pk>` selection of an incompatible audience (e.g. Kids/Juvenile for an adult person) is rejected with a clear message.
- `save_pre_registration_from_form` with a `pp:<pk>` selection does not raise an exception and persists `selected_plan_id=None`.
- The complete flow (`finalize_pre_registration`) with a `PlanPrice`: the snapshot → the form revalidated → the `Person`/`Membership`(`plan_price_ref`) created correctly.

### Execution authorization
Authorized by the user (an objective answer choosing the complete migration).

### Execution evidence
- `./.venv/Scripts/python.exe manage.py test system.tests.test_registration_public_plan_price --verbosity 2` → 7 new tests, all `ok` (the form accepts `pp:<pk>` for a compatible audience, rejects an incompatible audience, and rejects a non-existent catalog id; `create_registration_order` creates a `RegistrationOrder` with `plan_price_ref` and multiplies correctly by the order's people; `finalize_pre_registration` with a `PlanPrice` creates the correct `Membership.plan_price_id` and a `RegistrationOrder` with `plan_price_ref`/`plan=None`/`payment_status=PAID`).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_pre_registration_service system.tests.test_register_wizard_contract system.tests.test_plan_commercial --verbosity 2` → 17 existing tests, all `ok` (the non-regression confirmed, including the static contract of `register.html`/`register.js` with the updated asset version).
- `./.venv/Scripts/python.exe manage.py test --verbosity 1` → the full suite, 544 tests, `OK`.
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced)`.

## Visual validation
Run in the internal browser (the Chrome preview), after `clear_migrations` + a complete reseed:
- A new Adult student (CPF `529.982.247-25`, born 15/03/1998): the complete public wizard flow up to step 6/8 ("Escolha seu plano" — "Choose your plan") shows the card "Individual — R$ 221,99/Mensal — 2x por semana" ("Individual — R$ 221.99/Monthly — 2x per week"), with a working selection (`id_selected_plan` = `pp:1`, `aria-pressed="true"` after the click). Before the fix: "Nenhum plano disponível para esta pessoa." ("No plan available for this person.")
- A new Kids/Juvenile student (CPF `153.509.460-56`, born 10/05/2015, a Kids class): the card "Individual — R$ 208,31/mês — 2x por semana — Recorrente" ("Individual — R$ 208.31/month — 2x per week — Recurring") (Stripe), with a working selection (`id_selected_plan` = `pp:19`).
- An additional regression found and fixed during this validation: `register.js::onEnterPlan()` had the same "payment-method filter never revalidated" bug already fixed in this session in `dependent_registration.js` — fixed with the same defensive logic (resetting the filter when the current value no longer belongs to the current audience's set of valid options).
- A physical reload of the preview server was confirmed as necessary (the known stale-content bug of `runserver --noreload`, documented in memory) for the asset's new version (`?v=49`) to be served.

## ORM validation
`Membership.objects.get(person=person).plan_price_id` and `RegistrationOrder.objects.get(person=person).plan_price_ref_id` verified through the automated test (see Execution evidence) and through `manage.py shell` during the investigation of the original regression (counting the active `PlanTier`/`PlanPrice`/`SubscriptionPlan` records after the reseed).

## Quality validation
`manage.py check` clean; the full suite (544 tests) with no regression; no real Asaas/Stripe call in an automated test (the already-existing `family_pricing`/`stripe_discounts` mocks were not touched by this PRD).

## Evidence
See Execution evidence and Visual validation above.

## Implemented
- `system/services/registration_checkout.py::create_registration_order` rewritten to resolve `selected_plan` through `resolve_catalog_plan`, populating `RegistrationOrder.plan` (legacy) OR `RegistrationOrder.plan_price_ref` (new), preserving the order's per-people multiplier (`_count_group_members`/`_count_training_persons`).
- `system/forms/registration_forms.py`: the `selected_plan` field migrated from an `IntegerField` to a `CharField`; `_clean_plan_selection` resolves through `resolve_catalog_plan`, with a simplified audience-eligibility branch for `PlanPrice` selections (with no family/Veteran/special authorization, which do not exist in that model); the `SubscriptionPlan` import removed (no longer used directly in the file).
- `system/services/pre_registration.py`: a new `_legacy_plan_pk_from_catalog_id` helper used in `save_pre_registration_from_form` to assign `selected_plan_id` (the legacy FK) only when the selection resolves to a `SubscriptionPlan`; `PlanPrice` selections write `selected_plan_id=None`, preserving the catalog string in the raw snapshot for the reconstruction in `finalize_pre_registration`.
- `system/views/auth_views.py`: `get_plan_catalog_payload(include_plan_prices=True)` — the public catalog now includes the active `PlanTier`/`PlanPrice` records (with `sp:`/`pp:` prefixed IDs), along with the legacy Veteran variants (also prefixed in that mode, with no ID collision).
- `static/system/js/auth/register.js`: the single `parseInt` applied to `data-plan-id` removed (it is now an opaque string, like in the dependent wizard); `onEnterPlan()` fixed to revalidate `planFilter.cycle`/`frequency`/`method` against the current audience's set of valid options before applying the default value, fixing a real regression that froze the payment method with a value from a previous/non-existent audience; the asset version `?v=49`.
- `templates/login/register.html`: the script's version bumped.
- New tests: `system/tests/test_registration_public_plan_price.py` (7 tests: the form, `create_registration_order`, the complete completion).
- The contract test updated: `system/tests/test_register_wizard_contract.py` (the `register.js` asset version).

## Cleanup findings
- `create_or_update_pre_registration` (pre_registration.py) is dead code — a candidate for removal in a future audit, outside this PRD.
- The "family plan" model through `SubscriptionPlan.is_family_plan` remains in the code (`_count_group_members`, a branch in `create_registration_order`) but is unreachable in practice — no `is_family_plan=True` row is active in the post-PRD-127 catalog. Not removed in this PRD (out of scope; the behavior preserved for safety).

## Follow-up PRDs
- Removing the dead code (`create_or_update_pre_registration`) if confirmed unused after this PRD.
- Evaluate whether the legacy "family plan" branch (`is_family_plan`) should be removed or whether it will one day have active SKUs again.

## Deviations from plan
- An additional regression not foreseen in the original plan was found and fixed: `register.js::onEnterPlan()` had the same "never revalidated" payment-method filter bug that had been fixed in `dependent_registration.js` in this same session (PRD-128). Fixed with the same technique, within this PRD's scope because it blocked the same "a new student sees plans" validation.

## Pending
- None. The real Asaas validation was carried out successfully on 2026-07-06 (see the section below).

## The real Asaas validation (run on 2026-07-06)
Carried out with the user's assistance through an external browser (`claude-in-chrome`), as recorded as a pending item in this PRD and in PRD-128:

1. The public registration filled in through the internal browser up to Step 6 (the student "Carlos Teste PIX", CPF 529.982.247-25, the plan `pp:1` — Adult 2x per week, PIX).
2. The first real attempt blocked by Asaas: `400 invalid_object` — the local `SITE_BASE_URL` (`http://127.0.0.1:8000`) is neither HTTPS nor a domain registered under "Minha Conta → Informações" ("My Account → Information") of the Asaas sandbox.
3. The user brought up an `ngrok` tunnel (`https://dealmaker-deserve-afford.ngrok-free.dev` → `localhost:8000`), registered that domain as the "Site" in the Asaas sandbox account (temporarily, replacing `lvjiujitsu-hg.onrender.com` — to be reverted by the user after the test), and configured a webhook pointing at the tunnel.
4. After adjusting the local `.env` (`SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`, `ASAAS_WEBHOOK_TOKEN`) with the user's confirmation and restarting the server, the real PIX payment was created successfully through `create_pre_registration_plan_payment` (`asaas_payment_id=pay_jfokildk7gfohu6a`, `asaas_customer=cus_000008338873`).
5. The payment confirmed through the Asaas sandbox's official simulation endpoint (`POST /v3/sandbox/payment/{id}/confirm`, documented at `docs.asaas.com/reference/confirm-payment`) — the status changed to `RECEIVED` with a real `paymentDate`/`transactionReceiptUrl`, with no need for manual approval in the dashboard.
6. **Asaas's real redirect to the `successUrl` worked on its own** (through the tunnel), with no need for the manual `/pagamentos/sucesso/?id=<pay_id>` simulation documented in the guide as a fallback — confirming that the documented limitation (the lack of an HTTPS tunnel + a registered domain) was exactly the only barrier.
7. The wizard advanced correctly into the post-payment mode ("Pagamento confirmado" — "Payment confirmed", "Adulto 2x por semana" — "Adult 2x per week", "Total: R$ 221,99"), the materials skipped, the registration completed.
8. The final check in the database: the `Person` "Carlos Teste PIX" created and active; the `PreRegistration` `finalized`; the `Membership` `active` referencing `plan_price_id=1` (PRD-127/129's new catalog) — confirming that the real PIX → Membership-with-a-`PlanPrice` pipeline works end to end.
9. The environment reverted after the test: the `ngrok` tunnel terminated; the local `.env` (`SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`) reverted to the original values; the server restarted. The user will revert the Asaas sandbox account's "Site" field back to `lvjiujitsu-hg.onrender.com`.
10. **An incidental finding (not blocking)**: `Membership.billed_price` stays `None` for a new subscription with no family group (it is only populated through `recompute_family_discounts_for_person`, never called in the solo public flow). It is not a visible bug — the template already uses `billed_price|default:effective_full_price` — but it is recorded as a possible follow-up to populate `billed_price` on the activation of any new `Membership`, not only when there is a family discount.

## Final status
Completed and fully validated — the automated tests, the internal browser, AND the real Asaas sandbox (PIX) validation with the user through an external browser. No remaining pending item in this PRD.
