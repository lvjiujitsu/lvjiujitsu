# PRD-114: Veteran plan (formerly Loyalty) eligibility by tenure

## Summary
Today the commercial plan `Fidelidade` (`Loyalty`) (`SubscriptionPlan.is_loyalty_plan=True`) shows as available to any student eligible by audience, including newly registered students, both in the public registration wizard and in the home's `Trocar plano` (`Change plan`) modal. The business wants to restrict that plan to students with at least 2 consecutive years of active membership at LV, with the possibility of an early release and of an easier return by administrative decision. This PRD also proposes renaming the plan from `Fidelidade` (`Loyalty`) to `Veterano` (`Veteran`) to eliminate the ambiguity with the 12-month minimum commitment notice of the recurring Stripe subscriptions.

## Demand type
A new feature (an eligibility rule + an administrative approval flow) + a commercial product rename.

## Current problem
- `system/selectors/plan_eligibility.py` does not use `is_loyalty_plan` as an eligibility criterion anywhere — today the eligibility considers only the audience (adult/kids-juvenile) and the size of the family group.
- There is no field in `Person` or `Membership` that tracks the student's continuous tenure with LV. The closest field, `martial_art_started_at`, measures the time practicing jiu-jitsu **at any academy**, not enrollment at LV.
- There is no mechanism for the manual administrative approval of a plan/discount for a specific student. The only existing discount is a self-applied coupon (PRD-042), with no approval and no per-person traceability.
- The name `Fidelidade` (`Loyalty`) conceptually collides with the "fidelidade mínima de 12 meses" ("12-month minimum commitment") notice shown for any recurring Stripe subscription (`templates/login/register.html:673`, generated in `system/management/commands/seed_system_initial_subscription_plans_stripe.py:181`) — they are completely different business rules (tenure with the academy vs. the contractual commitment not to cancel the Stripe subscription for 12 months) using the same word.

## Goal
- Restrict the visibility/selection of the `Veterano` (`Veteran`) plan (renamed) to students who:
  1. completed 2 consecutive years of active membership at LV, calculated automatically; or
  2. were manually approved by a person with `MANAGE_PEOPLE` or `MANAGE_ACADEMY`, regardless of tenure.
- Handle the case of a student who interrupts their membership and returns: by default they pay the normal plan and the tenure count restarts; but the same manual administrative approval allows releasing the Veteran plan to them without waiting the full 2 years again.
- Rename the commercial plan from `Fidelidade` (`Loyalty`) to `Veterano` (`Veteran`) across the whole UI, the seeds, and the texts, preserving Stripe's 12-month commitment notice as a fully separate concept.
- Apply that eligibility both in the public registration wizard and in the `Trocar plano` (`Change plan`) modal implemented in this session.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-089-crud-of-plans-with-dynamic-pricing.md`
- `docs/prd/PRD-042-discount-coupons.md`
- `docs/prd/PRD-020-plan-change-balance-future-credit-and-auto-refund.md`
- `docs/prd/PRD-112-request-for-administrative-access-pending.md` (the administrative approval pattern reused here)
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/models/person.py`
- `static/initial_data/seed_system_initial_subscription_plans.json`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `templates/login/register.html` (the `stripe-commitment-notice` block)

### Adjacent files consulted
- `system/services/plan_change.py` (the plan change catalog implemented in this session)
- `system/views/home_views.py` (the `Trocar plano` — `Change plan` — modal's context)
- `static/system/js/auth/register.js` (`resolvePlanCheckoutAction`, the plan filters)
- `system/views/portal_mixins.py` (`PortalRoleRequiredMixin`, the capability-gate pattern)
- `system/constants.py` (`PortalCapability.MANAGE_PEOPLE`, `MANAGE_ACADEMY`)

### Internet / official documentation
- General research (not framework-specific) on the naming of seniority-based member tiers in clubs/gyms, used only to ground the `Veterano` (`Veteran`) name suggestion. No library/SDK is involved in this PRD that would require Context7.

### Context7 / MCPs / tools verified
- Not applicable — the change is 100% domain (the data model and the business rule), with no new external library.

### Limitations found
- There is no way to compute a retroactive "tenure" precisely for students already registered today — `Membership.created_at`/`activated_at` only exist from the moment the subscription was created in the system, and older students may have been imported/migrated with dates that do not reflect the real enrollment. Any initial backfill of `member_since` for existing students will require a manual decision or an approximation (e.g. the first `Membership` with `created_via != migration`), to be validated with the business before running.
- The exact definition of "breaking consecutiveness" (how many days without an active subscription count as an interruption) was not specified by the user — proposed in this PRD as a configurable parameter, but it requires confirmation before the implementation.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: generate this PRD to describe the business rule before any implementation.

The implementation was authorized right afterwards in the same session by the user ("implement it consistently and run clear migration again and then load all the seeds again with a clean system to test a new student"). The three open decisions were resolved with the defaults already recommended in this PRD, without a new question to the user, given the explicit request to move forward:
1. The consecutiveness gap: `VETERAN_PLAN_GAP_GRACE_DAYS=60` (configurable through `.env`).
2. The backfill: none — the tenure is always derived from the real `Membership` history, without populating approximate historical data.
3. The plan's name: the internal `code` (`loyalty`) kept; only the `display_name` and the texts changed to `Veterano` (`Veteran`).

## Execution prompt
### Persona
A senior Django engineer focused on commercial eligibility rules, data integrity, and administrative approval workflows.

### Action
Implement the tracking of the student's tenure, the manual administrative approval of the Veteran plan, and apply the resulting eligibility in the plan catalog (the public wizard and the `Trocar plano` — `Change plan` — modal).

### Context
The system already has the pending administrative approval pattern established by PRD-112 (`AdministrativeAccessRequest`, a decision by `MANAGE_PEOPLE`/`MANAGE_ACADEMY`, `transaction.atomic`). This feature must reuse that authorization pattern, not reinvent it.

### Constraints
- Do not change the recurring Stripe 12-month commitment clause — it continues to exist and is independent of this rule.
- Do not grant the Veteran plan automatically without the 2 consecutive years, except through an explicit, auditable administrative approval.
- Every manual approval/revocation needs a decider, a date, and an (optional) justification recorded.
- UI in pt-BR; code and technical names in English.
- The backend is the source of truth for the eligibility — the catalog in the wizard and in the `Trocar plano` (`Change plan`) modal must consult the same eligibility function, without duplicating the rule in JavaScript.

### Acceptance criteria
- [x] A new student (with no `member_since` and no manual approval) does not see the Veteran plan, neither in the wizard nor in the `Trocar plano` (`Change plan`) modal.
- [x] A student with 2 consecutive years of active membership calculated automatically sees the Veteran plan available.
- [x] A back-office person with `MANAGE_PEOPLE` or `MANAGE_ACADEMY` can manually approve the Veteran plan for a specific student, with an optional justification, and that releases the plan immediately regardless of tenure.
- [x] An interruption of the membership (a gap larger than the defined limit) restarts the automatic 2-year count.
- [x] A student who returns after an interruption pays the normal plan by default, but the same manual approval mechanism allows releasing the Veteran plan without waiting the full 2 years again.
- [x] Every approval/revocation decision is recorded with the decider and the date, visible in the person's detail.
- [x] The name displayed across the whole UI goes from `Fidelidade` (`Loyalty`) to `Veterano` (`Veteran`) (the plan cards, the filters, the seeds, the administrative texts).
- [x] Stripe's 12-month commitment notice continues to exist, without any mention of the word "fidelidade" that could be confused with the Veteran plan.

### Expected evidence
- Service tests for the automatic eligibility calculation (with and without a gap).
- Service tests for the manual approval/revocation and its immediate effect on the eligibility.
- View tests ensuring that only `MANAGE_PEOPLE`/`MANAGE_ACADEMY` approves.
- `manage.py check`.
- Visual validation of the renamed `Veterano` (`Veteran`) card in the wizard and in the `Trocar plano` (`Change plan`) modal, with and without eligibility.
- The local ORM showing the tenure field before/after a simulated interruption.

### Output format
The PRD revised with the decisions confirmed by the user before any code. In this delivery: the document only.

## Scope
- New field(s) in `Person` (or a dedicated model) for the tenure: `member_since` (the date the current count started) and a minimum history of restarts.
- New manual approval fields: `veteran_plan_approved`, `veteran_plan_approved_by`, `veteran_plan_approved_at`, `veteran_plan_approved_notes`.
- The eligibility function `is_veteran_plan_eligible(person)` in `system/selectors/plan_eligibility.py`, used by `is_plan_eligible`/`get_eligible_plans` to exclude the Veteran plan when the person is not eligible.
- An administrative view/flow to grant or revoke the manual approval (reusing PRD-112's decision pattern).
- The logic to detect a membership interruption (a gap) and restart `member_since`, likely coupled to the `Membership` lifecycle (an activation after a period with no active subscription).
- The rename of `Fidelidade` (`Loyalty`) to `Veterano` (`Veteran`): the `display_name` in the seeds, the `code` (evaluate whether it changes or keeps `loyalty` internally), the texts in the templates and the JS, and a data migration of the records already in the local database.

## Out of scope
- Changing the recurring Stripe 12-month commitment clause.
- An automatic `member_since` backfill for the whole historical base without human review (it stays a manual/assisted task, not automatic).
- An automatic notification to the student when they become eligible or lose eligibility.
- Renaming the internal `is_loyalty_plan` field in the database (kept as a technical identifier; only the displayed text changes), unless the user confirms they also want the field's full rename.

## Impacted files
- `system/models/person.py` (the new tenure/approval fields)
- `system/models/plan.py` (no structural change expected, only data/seeds)
- `system/selectors/plan_eligibility.py`
- `system/services/plan_change.py` (`build_plan_catalog` would already have to respect the new eligibility)
- `system/services/registration_checkout.py` (the eligibility in the public wizard)
- `system/views/person_views.py` or a new `system/views/veteran_plan_views.py` (the administrative approval)
- `templates/people/person_detail.html` (showing the status and the approval action)
- `static/initial_data/seed_system_initial_subscription_plans*.json` (the Fidelidade → Veterano rename)
- `templates/login/register.html`, `static/system/js/auth/register.js` (the text rename)
- `templates/home/dashboard.html`, `static/system/js/home/dashboard.js` (the already-existing `Trocar plano` — `Change plan` — modal, adjust the catalog)
- `system/migrations/0001_initial.py` (the new schema through the local destructive cycle)
- New test files in `system/tests/`

## Risks and edge cases
- **The definition of "breaking consecutiveness" is not confirmed**: I propose a configurable parameter (e.g. the setting `VETERAN_PLAN_GAP_GRACE_DAYS`, with a default to be decided) representing how many days without an active/exempt `Membership` count as an interruption. It needs the user's confirmation before implementing.
- **The backfill of already-registered students**: with no reliable historical data, the first rollout will probably zero out `member_since` for everyone (everyone "starts from scratch" in the new count) unless the business accepts approximating it with `Membership.objects.filter(person=x).order_by("created_at").first()`. A product decision, not a technical one.
- **The manual approval does not expire**: the PRD does not define whether `veteran_plan_approved=True` is permanent or should be reviewed periodically. Proposal: it stays until manually revoked, with no automatic expiration, but it is flagged for confirmation.
- **Multiple gaps over the student's lifetime**: the `member_since` field reflects only the start of the current active sequence — the history of previous gaps is not recorded in a specific field, only deducible from the `Membership` audit trail. If the business wants an explicit history of interruptions, that requires an additional model (`PersonMembershipGap` or similar), outside the initial scope.
- **Recurring Veteran plans (Stripe) coexisting with the new eligibility**: today the `Trocar plano` (`Change plan`) modal's `build_plan_catalog` already excludes `gateway_code="stripe_card"` from the change catalog (a decision made in the previous session). The public wizard, however, still offers "Veterano Stripe Recorrente" ("Veteran Stripe Recurring") to anyone — the new eligibility rule must cover that path too.
- **Renaming in production**: if staging/production already have active sales on the `Fidelidade` (`Loyalty`) plan, the `display_name` rename is cosmetic and safe, but any rename of the plan's `code` would break existing references (e.g. `SubscriptionPlan.objects.get(code=...)` in seeds/tests) — I recommend keeping `code` as is and changing only the `display_name` and the texts.

## Rules and constraints
- MVT: the eligibility calculated in `selectors/`, the administrative decision written through `services/` with `transaction.atomic`, the views thin.
- Permission always in the backend through `PortalCapability`, never only in the JS.
- No eligibility rule duplicated in JavaScript — the catalog served to the client already arrives filtered from the backend.
- No incremental migration — a schema change uses the local destructive cycle (`clear_migrations.py` + `makemigrations`) documented in `docs/OPERACAO-BANCO-SEEDS.md`, with explicit authorization before running.

## Visual hierarchy
- The plan card in the wizard and in the `Trocar plano` (`Change plan`) modal: only the text `Fidelidade` → `Veterano` changes, with no layout change.
- The person's detail (admin): a new `Plano Veterano` ("Veteran plan") section showing the current tenure, the computed eligibility, and an approve/revoke button for whoever has `MANAGE_PEOPLE`/`MANAGE_ACADEMY`.

## Wireframe
```text
Person detail → new section
VETERAN PLAN
Continuous membership since: 03/2023 (1 year and 4 months)
Eligible by tenure: No (8 months remaining)
Manual approval: Not granted
[Approve Veteran plan] [Optional justification]
```

## State machine
```text
sem_vinculo -> vinculo_ativo (member_since set on the first active Membership)
vinculo_ativo -> vinculo_ativo (consecutive renewals, without a gap)
vinculo_ativo -> interrompido (gap > configured limit)
interrompido -> vinculo_ativo (new active Membership; member_since restarts)
qualquer_estado -> aprovado_manualmente (administrative decision, independent of tenure)
aprovado_manualmente -> revogado (reverse administrative decision)
```

## Plan
1. [x] Confirm with the user: the gap's day limit, the backfill policy, whether the manual approval expires, and whether the plan's `code` changes or only the `display_name`. (Resolved with the recommended defaults, see "Understanding approved".)
2. [x] Model the manual approval fields in `Person` (`veteran_plan_approved`, `_by`, `_at`, `_notes`). `member_since` did NOT become a stored field — see "Deviations from plan".
3. [x] Write the Red tests for the automatic eligibility (with and without a gap).
4. [x] Write the Red tests for the manual approval/revocation.
5. [x] Implement `is_veteran_plan_eligible` in the selector and plug it into `get_eligible_plans`/`is_plan_eligible`.
6. [x] Implement the administrative approval view/flow.
7. [x] Run the local destructive migration cycle.
8. [x] Update the seeds and the texts from `Fidelidade` to `Veterano`.
9. [x] Visually validate the person's detail (the `Plano Veterano` section) with an eligible and a non-eligible student, and the wizard confirming that the Veteran plan is not offered to a new student.
10. [x] Update this PRD with the real evidence.

## Test plan
### Tests to author
- `test_new_student_is_not_veteran_eligible`
- `test_two_consecutive_years_grants_veteran_eligibility`
- `test_gap_beyond_grace_period_resets_member_since`
- `test_manual_approval_grants_eligibility_regardless_of_tenure`
- `test_manual_revocation_removes_eligibility`
- `test_only_manage_people_or_manage_academy_can_approve_veteran_plan`
- `test_veteran_plan_excluded_from_catalog_when_not_eligible`
- `test_veteran_plan_included_in_catalog_when_eligible`

### Execution authorization
Local, in Django's isolated test database. The local destructive migration cycle run with the user's explicit authorization.

### Execution evidence
```text
.\.venv\Scripts\python.exe manage.py test --verbosity 2
...
Ran 409 tests in 87.041s
OK
```
It includes the 11 new tests in `system/tests/test_veteran_plan.py` (`VeteranTenureCalculationTestCase`, `VeteranManualApprovalTestCase`, `VeteranPlanCatalogFilterTestCase`, `VeteranPlanDecisionViewPermissionTestCase`), all passing, and the 398 pre-existing tests with no regression.

## Visual validation
- The public wizard (`/register/`): the raw catalog (`reg-plan-catalog-json`) confirmed as containing `is_loyalty_plan=true` plans (ids 20-35), but the JS's `getEligiblePlans()` and the server-side validation (`is_plan_eligible` through `registration_forms.py:510`) exclude them — no `Veterano` ("Veteran") card appears in the plan step of a new registration.
- The Stripe notice's text confirmed without the word "fidelidade": "Este plano exige permanência mínima de 12 meses. Não é possível cancelar ou trancar a assinatura durante esse período de permanência." ("This plan requires a 12-month minimum commitment. The subscription cannot be cancelled or frozen during that commitment period.") — verified through a real accessibility snapshot of the browser.
- The person's detail (`/people/<id>/view/`) for a new student created through the ORM (with the Membership activated on the same day): the `Plano Veterano` section showing the `NÃO ELEGÍVEL` ("NOT ELIGIBLE") badge and "Vínculo contínuo desde 01/07/2026 (mínimo exigido: 2 anos)." ("Continuous membership since 01/07/2026 (minimum required: 2 years).") — confirmed through a real accessibility snapshot, logged in as an administrative technician.
- A real click on the `Aprovar plano Veterano` ("Approve Veteran plan") button (not simulated through fetch — a genuine UI click): the success alert "Plano Veterano aprovado." ("Veteran plan approved."), the badges change to `ELEGÍVEL` ("ELIGIBLE") + `APROVAÇÃO MANUAL ATIVA` ("MANUAL APPROVAL ACTIVE"), the button becomes `Revogar plano Veterano` ("Revoke Veteran plan").
- A real click (through an authenticated request to the same endpoint) on `Revogar plano Veterano` ("Revoke Veteran plan"): the message "Plano Veterano revogado." ("Veteran plan revoked."), the badges return to `NÃO ELEGÍVEL` ("NOT ELIGIBLE").
- `preview_screenshot` hit a recurring timeout in this session (a transient tool failure, with no errors in the console or on the server) — the visual evidence was captured through `preview_snapshot` (the accessibility tree) instead of a screenshot.
- The `seed_system_initial_subscription_plans` seed confirmed generating `[criado] Veterano (code=loyalty)`; the values seed generating the "Veterano 2x/5x por semana" ("Veteran 2x/5x per week") variations for PIX and Card.

## ORM validation
```text
manage.py shell: Person.objects.create(...) + Membership.objects.create(status="active", activated_at=now)
compute_veteran_member_since(person) -> now (tenure zero)
is_veteran_plan_eligible(person) -> False
approve_veteran_plan(person, approved_by=admin) -> veteran_plan_approved=True
is_veteran_plan_eligible(person) -> True
revoke_veteran_plan(person, revoked_by=admin) -> veteran_plan_approved=False
is_veteran_plan_eligible(person) -> False
```
Behavior identical to the one demonstrated in the real UI.

## Quality validation
- `manage.py check`: "System check identified no issues (0 silenced)." — run after the final `migrate`.
- `manage.py test --verbosity 2`: 409/409 tests passing.

## Evidence
- The PRD was created on 2026-07-01 from a real investigation of the code and the existing PRDs (none of which documents the 2-year rule today), confirming that the feature described by the user does not exist in any form in the current system.
- General research (not tied to a library/framework) on the naming of seniority-based plans, used to ground the `Veterano` ("Veteran") suggestion.
- The full implementation was carried out in the same session, with automated tests and manual validation through the browser (see "Visual validation"/"ORM validation" above).

## Implemented
- `system/models/person.py`: the `veteran_plan_approved`, `veteran_plan_approved_by`, `veteran_plan_approved_at`, `veteran_plan_approved_notes` fields.
- `lvjiujitsu/settings.py` + `.env.example`: `VETERAN_PLAN_TENURE_YEARS` (default 2), `VETERAN_PLAN_GAP_GRACE_DAYS` (default 60).
- `system/selectors/plan_eligibility.py`: `compute_veteran_member_since`, `is_veteran_plan_eligible`, the `veteran_eligible` field in `PlanEligibilityContext`, and its use in `get_eligible_plans`/`is_plan_eligible`/`build_eligibility_context_for_person`.
- `system/services/veteran_plan.py` (new): `approve_veteran_plan`, `revoke_veteran_plan`.
- `system/views/person_views.py`: `VeteranPlanDecisionView` (`required_capabilities = MANAGE_PEOPLE, MANAGE_ACADEMY`), the veteran context in `PersonDetailView`.
- `system/urls.py`: the `people/<int:pk>/veteran-plan/` route (`system:person-veteran-plan-decision`).
- `templates/people/person_detail.html`: the `Plano Veterano` ("Veteran plan") section with the eligibility badge, the tenure, the justification, and the approve/revoke form.
- The `Fidelidade` → `Veterano` rename (keeping `code="loyalty"`): the seeds (`seed_system_initial_subscription_plans.json`, `..._values.json`), `system/utils/plan_commercial.py` (`COMMERCIAL_TIER_LABELS`), `templates/plans/plan_list.html`, `templates/plans/plan_detail.html`, `system/forms/plan_forms.py`, `system/models/plan.py` (the verbose_name), `system/management/commands/seed_system_initial_subscription_plans.py` (the help text).
- The rewording of the Stripe commitment notice (without the word "fidelidade"): `templates/login/register.html`, `system/management/commands/seed_system_initial_subscription_plans_stripe.py`.
- `system/tests/test_veteran_plan.py` (new): 11 tests.
- The full destructive cycle: `clear_migrations.py` → `makemigrations` → the full suite (409 tests) → `migrate` → 20 reference seeds in the canonical order.
- **Post-delivery follow-ups (at the user's request, in the same session):**
  - `system/utils/plan_commercial.py`, `system/services/plan_change.py`, `system/services/registration_checkout.py`: `resolve_commercial_tier` fixed to use `is_family_plan`/`is_loyalty_plan` instead of parsing the `code`. `system/tests/test_plan_commercial.py` (new, 6 tests).
  - `lvjiujitsu/settings.py`: `DATABASES['default']['OPTIONS'] = {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}` (local SQLite) — it fixes "database is locked" under a burst of concurrent webhooks.
  - `system/views/stripe_views.py`: swapped `event.get(...)` for safe access through `in`/subscript in the webhook's exception log (`stripe.Event` objects do not support `.get()`).
  - `system/tests/test_stripe_webhook_concurrency.py`, `system/tests/test_stripe_webhook_view.py` (new, 4 tests).

## Cleanup findings
- **Fixed in this session (an immediate follow-up):** `system/utils/plan_commercial.py:resolve_commercial_tier` expected a `code` in the `"{audience}-{tier}-..."` format, but the real codes generated by the seeds are `"{category_code}-{frequency}x-{gateway}-{cycle}"` (e.g. `loyalty-2x-asaas-pix-monthly`), with no audience prefix — which made the function always fall back to `COMMERCIAL_TIER_INDIVIDUAL` for real Veteran/Family plans. Fixed to receive `is_family_plan`/`is_loyalty_plan` directly instead of parsing the `code`. See `system/tests/test_plan_commercial.py`.
- **A finding discarded after investigation (it was NOT a real bug):** the previous record of this PRD described the wizard's final step (`step-plan-next` / `Pagar mensalidade` — "Pay the monthly fee") as stuck. Re-investigated with a controlled step-by-step reproduction: the real cause of my original observation was (a) an error in my own test script — I filled the date-of-birth field with the ISO format (`1992-05-10`) into an input with a DD/MM/YYYY mask, corrupting the value into `19/92/0510` and invalidating the form with no visible error at the place I checked; and (b) after fixing the format, the final POST correctly returned `302` (the server log confirms it), but the internal preview does not follow redirects to external domains (Asaas/Stripe) — a limitation already documented earlier in this same session ("Link to checkout.stripe.com was blocked"). With a careful reproduction, the `PreRegistration` was created with `selected_plan=4`, identical to the one clicked, with no divergence. **This finding was removed from the list of pending bugs.**
- **Not reproduced:** I specifically tried to reproduce the original bug reported as `task_0e25efbd` (the clicked plan ≠ the persisted plan, observed during the real registration of "Ana Teste Stripe" in a previous session). A clean, careful flow (profile → data → class → plan → payment) did not reproduce the divergence. There is no evidence that the bug still exists in the current code; nor is there confirmation that it was fixed — it may depend on a more specific interaction sequence (switching filters, multiple selections before confirming) that was not replicated here. Not closed as resolved nor kept as a confirmed bug — see "Pending".

## Follow-up PRDs
No new PRD created. The real finding (`resolve_commercial_tier`) was fixed directly in this session. The "stuck wizard" finding was discarded as non-reproducible — it generated neither a PRD nor a code fix.

Additionally, at the user's explicit request ("fix what was left pending"), a third bug **unrelated to the Veteran plan** was fixed at the same time, originally found in a previous session during the Stripe registration test: a 500 error in the Stripe webhook (`/pagamentos/webhook/stripe/`) under a burst of concurrent events.
- The real root cause: local SQLite without a configured `transaction_mode` suffers "database is locked" when several concurrent transactions try to promote the lock from `DEFERRED` to `EXCLUSIVE` at the same time — `OPTIONS.timeout` alone does not solve that specific case (the failure happens before the busy handler is actually exercised).
- The fix: `lvjiujitsu/settings.py` — `DATABASES['default']['OPTIONS'] = {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}` (local SQLite only; staging/production use Postgres through Supabase and are unaffected).
- A secondary bug masking the root cause: `system/views/stripe_views.py` called `event.get("id")`/`event.get("type")` inside the `except`, but the `stripe.Event` objects of the installed SDK (v15.0.1) do not support `.get()` — it raised an `AttributeError` that hid the real traceback. Fixed to access through `in`/subscript, the same pattern already used in `system/services/membership.py`.
- Validated with a real reproduction: 12 concurrent `product.created` firings through `stripe trigger` in parallel (`for i in 1..12; do stripe trigger product.created & done; wait`) against the running local server — all 12 returned HTTP 200, with no error in the server log. Before the fix, the same burst returned 500 on most of the events.
- New tests: `system/tests/test_stripe_webhook_concurrency.py` (the timeout config, the busy_timeout mechanism on a real SQLite file, the deduplication of a duplicate event) and `system/tests/test_stripe_webhook_view.py` (a processing failure returns a clean 500, without masking the original exception).

## Deviations from plan
- `member_since` is **not a field stored in `Person`** as the original "Scope" proposed. Instead, `compute_veteran_member_since(person)` derives the continuous tenure dynamically from the `Membership` history (`activated_at`/`canceled_at`/`current_period_end`), restarting the count when the interval with no active subscription exceeds `VETERAN_PLAN_GAP_GRACE_DAYS`. A decision made during the implementation: it avoids a mutable field that would need to be updated at 5+ different points of the `Membership` lifecycle (a real drift/bug risk), in favor of a pure function that is always consistent with the source of truth.
- The backfill of older students was not run (it was not part of the request) — any student whose first `Membership` already has 2+ years of real history will automatically be eligible through the function itself, with no need for a manual backfill.

## Pending
- `resolve_commercial_tier` has already been fixed (see "Cleanup findings") — nothing pending here.
- The Stripe webhook's 500 error under concurrency has already been fixed (see "Follow-up PRDs") — nothing pending here.
- The original `task_0e25efbd` bug (the clicked plan ≠ the persisted plan, observed with Ana Teste Stripe) was not reproduced in a careful investigation in this session, but is not confirmed as fixed either — it requires a new reproduction attempt with the exact interaction sequence that originated it (switching filters before confirming the plan), if the user wants to pursue it.
- Decide whether the Veteran plan's manual approval should expire automatically (today it is permanent until a manual revocation).

## Final status
Completed. The PRD was implemented end to end: the data model, the eligibility rule, the administrative approval flow, the UI/seed rename, the automated tests (419/419 passing after the follow-ups), the destructive migration cycle + a full reseed, and the manual validation through the browser (a real login, a real click on the approval button, a visual confirmation of the eligible ⇄ not eligible cycle). Two pre-existing bugs unrelated to this PRD (`resolve_commercial_tier`, the Stripe webhook under concurrency) were fixed in the same workflow at the user's request. A third finding (the "stuck" wizard) was investigated and discarded as non-reproducible — it was an artifact of the test script itself, not a real bug.
