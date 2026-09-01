# PRD-132: Free transitions between plans + a monthly fee pause (a medical note and a freeze)

## Summary
Two related contractual-flexibility fronts, requested by the user after identifying that the plan change catalog never offers a migration to recurring Stripe:

**A) Free transitions between plans** — allow migrating from/to any gateway (Asaas ↔ Stripe) through `Trocar plano` ("Change plan"), respecting the already-existing Stripe loyalty lock (`is_plan_change_locked`) — today the destination catalog excludes `gateway_code="stripe_card"` unconditionally, even for someone with no loyalty commitment at all.

**B) A monthly fee pause** — two distinct mechanisms, with their own business rules:
- **B1) A medical-note pause**: always allowed, even during the Stripe loyalty commitment period. It suspends the billing for the period stated in the note and **postpones the commitment's end date** by the same number of days (the loyalty period does not shrink because of a health problem, but neither is it improperly "spent"). It requires administrative approval.
- **B2) A self-service freeze**: a quota of up to 30 days a year, requiring no medical note, available **only outside the commitment period** (Asaas always; Stripe only after the loyalty period — the original one or one already extended by B1 — ends).
- In both cases: the check-in is blocked during the pause; the due date/next charge is postponed by the paused period.

**C) Transparency at registration** — the freeze/pause rules must be visible to the client already in the plan selection/summary of the wizard (both the public and the dependent one), not only after contracting.

## Demand type
A new feature (explicitly requested by the user, with the business rules detailed by them after this session's clarifying question).

## Current problem
- `build_plan_catalog` (`system/services/plan_change.py:302-311`) excludes `gateway_code="stripe_card"` from the change catalog **always**, for any client, whether or not they are within a commitment period — there is today no self-service path to migrate to a recurring Stripe plan after the initial registration.
- There is no concept of a "pause"/"freeze" in the system: `MembershipStatus` (`system/models/membership.py:11-17`) has `pending`, `active`, `past_due`, `canceled`, `expired`, `exempted` — no temporary pause state.
- `PRD-117` (contractual loyalty) remains pending — today the "commitment period" is only a proxy through `Membership.current_period_end` (when there is a `stripe_subscription_id` or `plan.gateway_code == "stripe_card"`), with no dedicated field. This PRD does **not** create that dedicated field; it keeps using the same proxy, but it needs a new field for "how much the commitment period was extended by medical pauses" (it cannot simply overwrite `current_period_end`, which also controls the billing cycle).
- There is no reusable administrative approval queue for this case — the closest pattern is `PRD-112`'s (a pending administrative access request: `pending → approved/rejected/canceled`), which will be used as the architectural reference.
- There is no medical-note upload/record anywhere in the system.
- No annual quota (days used/year) is tracked anywhere in the domain today.

## Goal
1. A client with no loyalty lock (Asaas, or Stripe outside the commitment period) can change to **any** active plan, including recurring Stripe, through `Trocar plano` ("Change plan").
2. A client can request a medical-note pause at any time (even within the commitment period); it becomes "awaiting approval"; on approval, the billing is suspended for the stated period and the commitment period is extended by the same number of days.
3. A client outside the commitment period can freeze their enrollment with no medical note, up to 30 days in the current year, controlled automatically by the system (they cannot exceed the quota).
4. In both approved-pause cases: the check-in is blocked during the period; the due date/next charge is postponed.
5. The freeze/pause rules appear clearly to the client at the moment of the plan selection/registration summary (both the public and the dependent flow).

## Context Ledger
### Files read in full
- `system/services/plan_change.py` (`build_plan_catalog`, `is_plan_change_locked`, `get_plan_change_lock`, `_STRIPE_RECURRING_GATEWAY_CODE`)
- `system/models/membership.py` (`Membership`, `MembershipStatus`, `MembershipCredit`, `MembershipInvoice` — no pause/extended-commitment field exists)
- `system/services/stripe_admin_actions.py` (`cancel_membership`, `change_membership_plan` — the `stripe.Subscription.modify` call pattern, already using `metadata` and `transaction.atomic`)
- `system/services/stripe_checkout.py` (`create_subscription_session_for_pre_registration` — today it only creates a session for a new `PreRegistration`, not to migrate an existing `Membership`)
- `docs/prd/PRD-117-contractual-fidelity-to-recurring-plans.md` (it confirms: never implemented, "do not implement without explicit approval" — this PRD-132 does not replace it, it only adds a field for extending the commitment period, without taking on the rest of that PRD's scope)
- `docs/prd/PRD-112-request-for-administrative-access-pending.md` (the reference pattern: a model with the `pending/approved/rejected/canceled` statuses, an administrative queue with filters, a transactional decision with `select_for_update`)
- `docs/prd/PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md` (the origin of the current loyalty lock)

### Adjacent files consulted
- `system/services/class_calendar.py::perform_checkin` / `_student_instructor_present` (the check-in block point to extend)
- `templates/login/register.html`, `templates/dependents/dependent_registration.html` (where the rules' transparency needs to appear)

### Limitations found
- There is no file-upload infrastructure (a medical note as a PDF/image) used in any other flow of the system today. Recording the note as **text/a remark + the stated period** (with no file attachment) is the minimum path compatible with what already exists; attaching a file is a possible extension, but outside this PRD's initial scope (recorded as a pending item/follow-up).
- Stripe's `pause_collection` (`behavior="void"` or `"mark_uncollectible"`) needs to be validated against the API's current official documentation before the implementation (Context7/the Stripe documentation) — do not presume the exact payload without confirming.
- The "current year" for the 30-day self-service freeze quota: confirmed by the user as the **enrollment's anniversary** (`Membership.activated_at`), not the calendar year.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`

## Understanding approved
The user explicitly asked for the PRD and detailed the business rules in response to this session's clarifying questions (the self-service freeze and the medical pause are **separate** mechanisms; a medical pause always suspends the real billing and postpones the commitment period; a self-service freeze only outside the commitment period, with a 30-day/year quota; the check-in blocked during any pause).

## Scope

### Phase A — A change catalog with no gateway exclusion
- `build_plan_catalog`: remove `.exclude(gateway_code="stripe_card")` from both queries (`get_eligible_plans`/`get_eligible_plan_prices`) — the loyalty lock (`is_plan_change_locked`) already prevents the whole change where applicable; there is no need to exclude Stripe from the catalog separately.
- A new checkout path to **migrate an existing `Membership` to recurring Stripe**: a new function in `stripe_checkout.py` (e.g. `create_subscription_session_for_plan_change`), generating a `RegistrationOrder(is_plan_change=True, plan_price_ref=..., person=...)` and redirecting to the Stripe Checkout.
- **Additional bugs discovered while investigating this PRD (the same family as those already fixed in PRDs 127/129/130), which block Phase A and need to be fixed as part of it:**
  - `PaymentMethodChoiceView.get` (`system/views/payment_views.py:52-70`) decides the gateway solely by `order.plan.payment_method` — for a `plan_price_ref` order (a PlanPrice), `order.plan` is `None`, so the `order.plan and ...` condition is `False` and the order **always** falls into the `else` (Asaas PIX), even when it should be an Asaas card or Stripe. It is a silently wrong routing, not a crash. It needs to resolve the real `gateway_code` (through `order.plan_price_ref.gateway_code` or `order.plan.gateway_code`) and add the Stripe branch.
  - `activate_membership_from_session` (`system/services/membership.py:81-136`, called by the `mode == "subscription"` branch of the `checkout.session.completed` webhook in `system/services/stripe_webhooks.py:145-176`) only reads `order.plan` (`if plan is None: return None`, line 84) — for a plan change order based on a `PlanPrice`, that function aborts silently without creating/updating anything, even after a real confirmed Stripe payment. On top of that, that branch **never checks `order.is_plan_change`** (unlike the one-off payment branch, which has checked it since PRD-130) — that is, even after fixing the `plan_price_ref` read, today it would create/update a "new" `Membership` instead of applying the change over the person's existing `Membership` (potentially duplicating an active subscription). It needs: in the `mode == "subscription"` branch, check `order.is_plan_change` first and, if true, call `apply_plan_change` over the person's existing active `Membership` (the same pattern already used in the one-off payment branch), then filling in the Stripe fields (`stripe_subscription_id`, `stripe_customer_id`, `current_period_start/end`) on the resulting `Membership`.
- A new path to **migrate from Stripe to Asaas**: cancel the current Stripe subscription (reusing the `stripe_admin_actions.cancel_membership` pattern, adapted for the client's own trigger, with no required `admin_user`) and follow the normal Asaas change flow (already existing).
- `PlanChangeSelectView`/`serialize_plan_with_proration`: adapt them to signal when the destination requires a full checkout (Stripe) vs an instant change with proration (Asaas↔Asaas) — the frontend (`dashboard.js`) needs to distinguish "apply now" from "redirect to payment".

### Phase B — A medical-note pause
- A new `MembershipPauseRequest` model (or an equivalent name): `membership`, `kind` (`medical`/`self_service`), `requested_start_date`, `requested_end_date`, `reason_note` (free text — a description of the note, with no file upload in this phase), `status` (`pending/approved/rejected/canceled`), `requested_at`, `decided_by`, `decided_at`, `decision_note`.
- The client's action: a `Pausar mensalidade` ("Pause monthly fee") button on the dashboard → a modal with the type selection (a medical note vs a freeze, see Phase C) → for a medical note: the period's dates + a remark → it creates a `MembershipPauseRequest(kind=medical, status=pending)`.
- An administrative queue (reusing `PRD-112`'s pattern): list the pending ones, approve/reject, with a reason.
- On approving a medical pause:
  - Suspend the billing for the period: for Stripe, use `pause_collection` on the Subscription (validate the exact payload through the official documentation before implementing); for Asaas, postpone the next charge/due date by the same number of days (there is no Asaas "subscription" to pause, it is a date postponement).
  - A new field on `Membership` to track the commitment extension (e.g. `fidelity_extended_days` or `fidelity_end_override`) — the effective commitment end date used by `is_plan_change_locked` now considers that extension added to the original `current_period_end`.
  - `Membership.status` gains a new value (`PAUSED`), or the "paused" state is derived from an approved `MembershipPauseRequest` with a current window (a technical decision to settle during the implementation — prefer deriving it from the approved request + the dates, avoiding duplicated state and the need for a cron to automatically revert the status at the end of the period).

### Phase C — The self-service freeze (30 days/year)
- The same `MembershipPauseRequest` model, `kind=self_service`.
- The eligibility rule: only allowed when `is_plan_change_locked(membership)` is `False` at the moment of the request.
- The quota: the sum of the days already used in **approved** `self_service` requests within the current enrollment year (see the reset rule below) cannot exceed 30 days; the request states the period and the system validates the quota before allowing the submission.
- **The quota's reset**: by the **enrollment's anniversary** (the `Membership.activated_at` date, per person/subscription — it is not a global reset on January 1st). A request's "current year" is the interval `[the last anniversary ≤ today, the next anniversary)`.
- **Approval**: it requires an administrative queue, just like the medical pause (the same model, with `kind` distinguishing the type, the same screen/decision) — confirmed by the user. The 30-day quota is validated at the request's creation (blocking a submission over the quota), but the effective application (suspending the billing, blocking the check-in, postponing the due date) only happens after the approval, exactly like a medical pause.

### Phase D — Transparency at registration
- `templates/login/register.html` (the public wizard) and `templates/dependents/dependent_registration.html` (the dependent wizard): add a text block in the plan selection/summary steps explaining the two rules (a freeze of up to 30 days/year with no medical note, outside the commitment period; a medical note always pauses the billing and postpones the commitment period).

## Out of scope
- Uploading the medical note's file (it is recorded as a period + a text remark).
- PRD-117's dedicated contractual loyalty field (this PRD only adds what is necessary to extend the commitment period through a medical pause, without taking on that PRD's full scope).
- An automatic e-mail/WhatsApp notification on approval/rejection (out of scope — it can become a follow-up).
- Pausing/freezing dependents independently of the main person in this first phase (assume the pause is per `Membership`, which already covers the main person and the dependent individually, since each has their own `Membership`).

## Rules and constraints
- No real Stripe call in an automated test — mock `stripe.Subscription.modify`/`pause_collection`.
- `transaction.atomic` on every administrative decision (approve/reject) and on any write that touches `Membership` + `MembershipPauseRequest` together.
- Preserve 100% of the existing suite with no regression (especially `test_plan_change*.py` and `test_calendar.py`, because of the new check-in block).
- A schema migration is necessary (a new model + new `Membership` fields) — it follows the project's policy: regenerate the single baseline through the destructive cycle (`clear_migrations` + `makemigrations`), not an incremental migration.

## Risks and edge cases
- A Stripe client pauses through a medical note, then tries to change plans during the pause — it must stay blocked (a pause is not the same as "the end of the commitment period").
- Two overlapping pause requests (e.g. a medical note over an ongoing freeze) — it needs date-overlap validation.
- Approving a retroactive medical pause (a note issued after the period has already partly passed) — a product decision to confirm during the implementation.
- The 30-day annual quota "turns over" in the middle of an ongoing pause — define whether it counts by the start date's year or proportionally.
- The Asaas → Stripe migration fails mid-checkout (the client abandons the Stripe page) — it must keep the current plan intact until the real payment confirmation (the same pattern already used in the public registration).

## Plan
_(to be detailed at the start of each phase's execution — this PRD covers the complete design; the implementation will be done phase by phase, each with its own Red→Green)_

## Test plan
### Tests to author (per phase)
- Phase A: the catalog includes Stripe when there is no lock; the Asaas→Stripe migration creates the correct `RegistrationOrder` and redirects to the Checkout; the Stripe→Asaas migration cancels the Stripe subscription before creating the new payment.
- Phase B: a medical pause creates a `pending` request; the approval suspends the billing (a Stripe mock) and extends the commitment period; the check-in blocked during the approved window; a rejection does not change the `Membership`.
- Phase C: a freeze accepted within the quota; rejected (or automatically denied) when it exceeds 30 days/year; blocked when `is_plan_change_locked` is `True`.
- Phase D: the template contains the rules' text on the registration screens (content asserts, as already done in other wizard contracts).

### Execution authorization
Local — with Stripe mocked, with no real gateway call.

## Decisions confirmed by the user
- The self-service freeze **also requires administrative approval** (the same queue as the medical pause, the same `MembershipPauseRequest` model, with the `kind` field distinguishing them).
- The 30-day/year quota resets on the **enrollment's anniversary** (`Membership.activated_at`), not the calendar year.
- The implementation: **all 4 phases in a single delivery**, without pausing for a review between them.

## Technical verification (the Stripe pause_collection)
Confirmed through `docs.stripe.com` (a direct fetch): `pause_collection.behavior` accepts `keep_as_draft`, `mark_uncollectible`, or `void`; `void` used (the invoice voided, with no charge) + `resumes_at` (a Unix timestamp, an automatic resume). The subscription's status stays `active` during the pause — only the billing is affected.

## Implemented
### Phase A — Free transitions between plans
- `system/services/plan_change.py::build_plan_catalog`: the `gateway_code="stripe_card"` exclusion removed from both queries (`get_eligible_plans`/`get_eligible_plan_prices`).
- A new `plan_requires_stripe_checkout(plan)` and the `gateway_code`/`requires_checkout` fields in `serialize_plan_with_proration`.
- A new `create_plan_change_stripe_order(person, membership, new_plan)`: it creates a `RegistrationOrder(kind=SUBSCRIPTION, is_plan_change=True, plan_price_ref/plan=new_plan, total=new_plan.price)`.
- `system/services/stripe_checkout.py::create_subscription_session_for_plan_change(order, request)`: a new public function; `_create_subscription_session` migrated from a pre-synchronized `price` (`stripe_price_id`, which the seeds do not populate) to an inline `price_data` — the same pattern already proven in `create_subscription_session_for_pre_registration`.
- `system/views/plan_change_views.py::PlanChangeSelectView`: a new branch — a Stripe destination plan → it creates the order + the Checkout Session and returns a `redirect_url` (the hosted Stripe); migrating **away** from Stripe → it cancels the current Stripe subscription (`cancel_membership(at_period_end=False)`, with no `admin_user`) and resets `status=ACTIVE`/`stripe_subscription_id=""` before following the normal flow.
- **2 pre-existing bugs fixed** (the same family as PRDs 127/129/130 — code that only read `SubscriptionPlan`):
  - `system/views/payment_views.py::PaymentMethodChoiceView`: it routed by `order.plan.payment_method`, always falling into Asaas PIX for `plan_price_ref` orders. It now resolves the real `gateway_code` (`asaas_pix`/`asaas_card`/`stripe_card`) through the new `_resolve_order_gateway_code`.
  - `system/services/stripe_webhooks.py`: the `mode == "subscription"` branch of `checkout.session.completed` never checked `order.is_plan_change` and only read `order.plan` (`activate_membership_from_session` aborts silently for a `PlanPrice`). The new `_apply_stripe_plan_change_migration` applies the change over the existing active `Membership` (through `apply_plan_change`) and fills in the Stripe fields (`stripe_subscription_id`, `stripe_customer_id`, `current_period_start/end`) — instead of creating a duplicate subscription.
- `templates/home/dashboard.html`: the catalog's card shows "Assinatura recorrente — você será redirecionado para o pagamento" ("A recurring subscription — you will be redirected to the payment") when `requires_checkout`.

### Phases B/C — The monthly fee pause
- `system/models/membership.py`: a new `Membership.fidelity_extension_days`; a new `MembershipPauseRequest` model (`kind` medical/self_service, `status` pending/approved/rejected/canceled, the period, the decision); `Membership.current_pause`/`is_currently_paused`.
- `system/services/membership_pause.py` (new): `create_pause_request` (it blocks overlaps; `self_service` requires being outside the commitment period + the 30-day/year quota by enrollment anniversary through `_membership_year_window`); `approve_pause_request` (`@transaction.atomic`, `select_for_update`; the Stripe pause through `pause_collection` with behavior=`void`+`resumes_at` when there is a `stripe_subscription_id`; it postpones `current_period_end`; it adds to `fidelity_extension_days` only for `medical`); `reject_pause_request`/`cancel_pause_request`; `get_self_service_quota_summary`.
- `system/services/class_calendar.py::perform_checkin`/`get_today_classes_for_person`: they block the check-in during a current approved pause; the `today_classes_list.html` template shows "Matrícula pausada até DD/MM/AAAA" ("Enrollment paused until DD/MM/YYYY").
- `system/views/membership_pause_views.py` (new): `MembershipPauseRequestCreateView` (the client, JSON), `MembershipPauseQuotaView`, `MembershipPauseRequestQueueView`/`DetailView` (the administrative queue, the same pattern as PRD-112 — `PortalRoleRequiredMixin` + the `MANAGE_PEOPLE`/`MANAGE_ACADEMY` capabilities).
- `templates/membership_pauses/pause_request_list.html`/`pause_request_detail.html` (new, mirroring `access_requests/*`).
- `templates/home/dashboard.html` + `static/system/js/home/dashboard.js`: the `Pausar mensalidade` ("Pause monthly fee") button + the modal (`bindPauseModal`), the same fetch/JSON pattern as the plan change modal.
- `system/forms/membership_pause_forms.py` (new): `MembershipPauseRequestForm`, `MembershipPauseDecisionForm`.

### Phase D — Transparency at registration
- `templates/login/register.html`: the existing Stripe notice adjusted (a freeze with no medical note only outside the commitment period) + a new `plan-policy-notice` block always visible in the plan step.
- `templates/dependents/dependent_registration.html`: the same rules block in the dependent's plan step.
- `static/system/css/auth/register.css`: a new `.plan-policy-notice` class.

## Evidence
- **New automated tests**: `system/tests/test_membership_pause.py` (21 tests: the quota/overlap/commitment period, the Stripe approval mocking `pause_collection`, the check-in block, the client's views and the admin queue) + `system/tests/test_plan_change_stripe_migration.py` (10 tests: the catalog with Stripe, the Asaas→Stripe migration, the Stripe→Asaas migration with the cancellation, the webhook not duplicating the `Membership`, the gateway routing) — **31 new tests, all green**.
- `manage.py test` (the full suite) → **585 tests, OK** (554 pre-existing + 31 new), with no regression.
- `manage.py check` → clean, before and after the destructive migration reset.
- The migration regenerated through the destructive cycle (`clear_migrations` + `makemigrations`) — the single `0001_initial.py` baseline includes `MembershipPauseRequest` and `Membership.fidelity_extension_days`.
- **Live validation in the internal browser**, with the 3 real students recreated (Beatriz/Stripe, Carlos/Asaas card, Diana/Asaas PIX — the same belts as before) after the reset:
  - Carlos's (Asaas) `Trocar plano` ("Change plan") catalog now shows the recurring Stripe option with "Assinatura recorrente — você será redirecionado para o pagamento" ("A recurring subscription — you will be redirected to the payment") (a screenshot).
  - Confirmed against Stripe's real API (test mode): selecting the Stripe plan creates a `RegistrationOrder(kind=subscription, is_plan_change=True, plan_price_ref=9)` and returns a real Stripe Checkout URL (`checkout.stripe.com/c/pay/cs_test_...`) — end-to-end proof that the inline `price_data` fix (instead of a pre-synchronized `stripe_price_id`, which the seeds do not populate) works.
  - The `Pausar mensalidade` ("Pause monthly fee") modal tested end to end by Carlos: a freeze request (10 days) created as `pending`.
  - The `/requests/pausas/` queue (logged in as the `admin` technician): it lists the request, with the approval through the real UI — "Pausa de mensalidade aprovada." ("Monthly fee pause approved.")
  - Confirmed in the database: `Membership.current_period_end` postponed from `07/08/2026` to `17/08/2026` (10 days) and reflected on the home ("Vigência 07/07/2026 → 17/08/2026" — "Term 07/07/2026 → 17/08/2026"); `fidelity_extension_days=0` (correct — only `medical` extends the commitment period).
  - The Stripe validation's test orders (created against the real API, never paid) removed from the local database after the validation.

## Cleanup findings
- No code residue. The validation artifacts (the unpaid Stripe test orders) removed from the local database.
- A known debt, out of scope: the seeded `PlanPrice` records with `gateway_code=stripe_card` have no synchronized `stripe_price_id` — it is no longer a blocker (Phase A now uses inline `price_data`, dispensing with a pre-created Price), but the `stripe_price_id` field itself remains unused in this flow; evaluate whether it still makes sense to keep it or whether it should become a cleanup follow-up.

## Final status
Completed and validated — Phases A, B, C, and D implemented, tested (31 new tests, the full suite 585 OK), and validated live against the real Stripe test mode and the complete administrative approval flow.
