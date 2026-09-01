# PRD-134: Subscription and family event history — client information timeline and admin technical audit

## Summary
During the investigation of the family-discount bug (corrected outside this PRD; see Context Ledger), the user asked where the subscription change history was recorded ("it was like this on day X, changed to this on day Y, paid, and so on"). Nothing like that exists today. The only audit mechanism (`OperationalAuditEntry`) is admin-only, free-form text, has no structured link to `Membership`/`Person`, and covers none of the subscription/family events: adding or removing a dependent, pausing, changing a plan, cancellation, changing a card, payment, refund, or family discount. This PRD creates a single structured event source with two distinct presentations reading the same data: an information timeline for the client (plain language without technical details) and a technical audit for the admin (actor, before/after values, IDs, and filters).

## Demand type
New feature explicitly requested by the user.

## Current problem
- `system/models/audit.py::OperationalAuditEntry` is the only existing structured record: `module` (person/checkin/financial), `action` (create/update/delete/approve/mark_paid), `actor_label` (free-form text), `entity_label` (free-form text), `summary` (free-form text, maximum 500 characters), and `created_at`. It has no foreign keys to `Membership`/`Person`/`PersonRelationship` and no structured before/after fields.
- `system/services/audit.py::record_audit_event` is a simple creation service with no additional logic.
- The only actual use in a billing flow is `system/views/billing_admin_views.py::MarkOrderPaidActionView` (approximately lines 112–118); no other subscription/family event is recorded.
- The existing UI (`system/views/admin_views.py::AuditLogListView`, `templates/audit/audit_log_list.html`, route `system:audit-log-list`) is admin-only through `AdministrativeRequiredMixin`. **There is no client-facing equivalent.**
- Subscription/family events are currently **not recorded in any structured location**:
  - Adding a dependent (`system/services/dependent_registration.py`)
  - Removing a dependent (`system/views/dependent_views.py::DependentRemoveView`)
  - Self-service cancellation blocked by the commitment period (`system/services/plan_change.py::get_plan_change_lock`) and admin cancellation (`system/services/stripe_admin_actions.py::cancel_membership`, `system/services/membership.py::mark_membership_canceled` via webhook)
  - Tuition pause request/approval/rejection (`MembershipPauseRequest`, PRD-131/132)
  - Self-service plan change (`system/services/plan_change.py::apply_plan_change`) and admin plan change (`system/services/stripe_admin_actions.py::change_membership_plan`)
  - Card change (Stripe Billing Portal, PRD-133; no local record is generated, only a redirect)
  - Family-discount change (`system/services/family_pricing.py::recompute_family_discounts_for_person`)
  - Confirmed/failed payment (`system/services/membership.py::record_invoice_from_stripe`, `mark_invoice_failed`)
  - Refund (`system/services/stripe_admin_actions.py::refund_order`)
- Some of these events leave a *partial* trace in isolated timestamp fields (`Membership.canceled_at`, `Membership.created_at`/`updated_at`, `RegistrationOrder.paid_at`/`refunded_at`, `MembershipPauseRequest.created_at`/`decided_at`), but there is no readable context or unified chronological view. Each record lives in a different table with no narrative.

## Goal
1. Every relevant subscription/family event listed above generates a single structured record, captured within the same `transaction.atomic` used by the service that changes state.
2. In the authenticated client area, the client sees an informative chronological timeline of their family's events in plain language (for example, "07/07/2026 — Dependente Gustavo removido da família" — "07/07/2026 — Dependent Gustavo removed from the family"), without technical IDs, internal admin names, or gateway jargon.
3. The admin sees a technical audit containing the same events, but with an identified actor, structured before/after values, technical IDs (Stripe/Asaas when applicable), and filters by person, period, and type.
4. Both views read the same data source; presentation differs, capture is not duplicated.

## Context Ledger
### Files read in full
- `system/models/audit.py` (complete `OperationalAuditEntry` model)
- `system/services/audit.py` (`record_audit_event`)
- `system/views/admin_views.py` (`AuditLogListView`)
- `system/services/family_pricing.py` (`recompute_family_discounts_for_person`, `_sync_stripe_discount`)
- `system/services/stripe_discounts.py` (`apply_family_discount`, `remove_family_discount`)
- `system/services/stripe_admin_actions.py` (`cancel_membership`, `change_membership_plan`, `refund_order`)
- `system/services/membership.py` (`mark_membership_canceled`, `record_invoice_from_stripe`, `mark_invoice_failed`)
- `system/views/dependent_views.py` (`DependentRemoveView`)
- `system/models/membership.py` (`Membership`, `MembershipPauseRequest`, `MembershipPauseRequestKind`, `MembershipPauseRequestStatus`, `MembershipInvoice`)

### Adjacent files consulted
- `docs/prd/PRD-131-fix-default-instructor-present-on-cancel-and-restore-class.md`, `docs/prd/PRD-132-free-plan-transitions-and-tuition-pause.md` (`MembershipPauseRequest` model and approval flow)
- `docs/prd/PRD-133-payment-indicator-and-stripe-card-change.md` (card changes through the Billing Portal without a local record; used as the reference PRD for level of detail)
- `templates/home/dashboard.html` (`MENSALIDADE` — "TUITION" — section / `billing_tabs`, where the client timeline must fit)

### Internet / official documentation
No external research was required. This feature concerns internal data modeling and presentation, with no new gateway integration.

### Context7 / MCPs / tools verified
Not applicable; this scope introduces no new external library, SDK, or API.

### Limitations found
- Real family-discount synchronization bugs were found and corrected in this session outside this PRD, before this PRD was opened:
  1. `system/services/stripe_discounts.py::apply_family_discount` used `Subscription.modify(coupon=...)`, a parameter rejected by Stripe when `billing_mode.type=flexible` (the current default). It was corrected to `discounts=[{"coupon": ...}]`. `remove_family_discount` retained `delete_discount()` because it already worked, as confirmed live.
  2. `cancel_membership`, `change_membership_plan` (`stripe_admin_actions.py`), and `mark_membership_canceled` (`membership.py`) did not call `recompute_family_discounts_for_person`. This was corrected.
- There is currently no recurring Asaas billing synchronization with `Membership.billed_price`. This project does not use an Asaas "subscription"; each charge is an individual payment recalculated from the full catalog price. This is a pre-existing architectural gap **outside this PRD's scope**. The timeline records what already happens today and does not correct the gateway.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
The user explicitly requested tracking all events listed above and displaying them in two places with distinct purposes (client information and admin audit) for better control.

## Execution prompt
### Persona
LV JIU JITSU Django developer following `AGENTS.md`/`CLAUDE.md`, TDD, and the project's MVT layers.

### Action
Implement a new structured subscription/family event model, a central emission service, and two read-only views/templates (client and admin) using the same source.

### Context
See Current problem and Context Ledger above: nine mutation points were mapped, and none currently generates a structured record.

### Constraints
- Record each event within the same existing `transaction.atomic` used by the mutating service; do not create a new transaction.
- Do not expose technical data (Stripe/Asaas IDs or admin names) in the client timeline.
- Do not expose one family's event to another family; always filter by the authenticated user's `person`/family group.
- Do not duplicate `OperationalAuditEntry`. The new model is specific to subscriptions/families; the generic audit log continues serving its existing modules (person/checkin).
- No new real gateway call. This PRD only records and displays events already produced by other services.

### Acceptance criteria
- The nine mapped event categories (dependent added/removed, pause requested/approved/rejected, self-service/admin plan change, self-service/admin cancellation, card change, payment confirmed/failed, refund, and family-discount change) each generate a record with `event_type`, `person`, `membership` when applicable, and structured `context`.
- The client timeline shows only the family's own events in reverse chronological order, using plain text and no technical data.
- The admin audit shows the same events with actor, before/after values, technical IDs when available, and filters by person, period, and type.
- No event from one family appears in another family's timeline.

### Expected evidence
Test command plus actual result, `manage.py check`, and visual validation of both screens (client and admin) in the internal browser.

### Output format
Implemented code plus this PRD updated with actual Evidence, Implemented, Pending, and Final status sections.

## Scope
1. **New model** `system/models/membership_timeline.py::MembershipTimelineEvent` (name defined in this PRD):
   - `person`: foreign key to `Person`, `related_name="timeline_events"`; the person who owns the timeline event (the removed dependent, the account holder who paused, and so on).
   - `membership`: foreign key to `Membership`, `null=True, blank=True`, `related_name="timeline_events"`; used when the event has an associated subscription.
   - `event_type`: `CharField` with `TextChoices` (`MembershipTimelineEventType`): `DEPENDENT_ADDED`, `DEPENDENT_REMOVED`, `PAUSE_REQUESTED`, `PAUSE_APPROVED`, `PAUSE_REJECTED`, `PLAN_CHANGED`, `MEMBERSHIP_CANCELED`, `CARD_UPDATED`, `PAYMENT_CONFIRMED`, `PAYMENT_FAILED`, `REFUND_ISSUED`, `FAMILY_DISCOUNT_CHANGED`.
   - `actor`: foreign key to `Person`, `null=True, blank=True`, `related_name="timeline_events_caused"`; `None` when an event comes from a webhook/automated process (for example, `mark_membership_canceled` via Stripe).
   - `actor_is_admin`: `BooleanField(default=False)`; distinguishes "the client did it" from "an admin did it on the client's behalf" and controls the client-facing text versus the technical admin label.
   - `context`: `JSONField(default=dict)`; a structured payload specific to the `event_type` (for example, `{"dependent_name": "Gustavo", "old_price": "1308.65", "new_price": "1073.09"}`). It never contains a secret/token. It may contain technical IDs (Stripe/Asaas), which are rendered only in the admin view.
   - `created_at` through `TimeStampedModel`, the project standard.
   - **Design decision — do not reuse `OperationalAuditEntry`**: that model is free-form text (`summary`/`actor_label`/`entity_label` as `CharField`), has no structured foreign keys, and has no audience separation. Extending it would disrupt its current person/checkin usage and still require the same new fields. A parallel model specific to the subscription/family domain is easier to filter by family and avoids regressions in the existing audit module.
   - **Design decision — do not store `client_summary`/`admin_summary`**: text is generated at read time by presentation functions (`describe_for_client(event)` / `describe_for_admin(event)`) from `event_type` plus `context`, not persisted. This avoids remigrating historical data when wording changes; `context` already carries everything both functions require.
   - Migration through the destructive cycle (`clear_migrations` plus `makemigrations`), the project's only migration policy; no incremental migration.

2. **Central emission service** `system/services/membership_timeline.py`:
   - `record_membership_event(person, event_type, *, membership=None, actor=None, actor_is_admin=False, context=None)` creates the `MembershipTimelineEvent`. It is called from each of the nine mutation points within the existing `transaction.atomic`:
     - `dependent_registration.py` (`DEPENDENT_ADDED`, for the dependent)
     - `dependent_views.py::DependentRemoveView` (`DEPENDENT_REMOVED`, for the owner and dependent)
     - `plan_change.py::apply_plan_change` (`PLAN_CHANGED`, `actor_is_admin=False`)
     - `stripe_admin_actions.py::change_membership_plan` (`PLAN_CHANGED`, `actor_is_admin=True`)
     - `stripe_admin_actions.py::cancel_membership` (`MEMBERSHIP_CANCELED`, `actor_is_admin=True`)
     - `membership.py::mark_membership_canceled` (`MEMBERSHIP_CANCELED`, `actor=None`; webhook)
     - Pause request/approval/rejection flow (PRD-131/132; locate the exact `MembershipPauseRequest` service; events `PAUSE_REQUESTED`/`PAUSE_APPROVED`/`PAUSE_REJECTED`)
     - `stripe_checkout.py::create_billing_portal_session` (`CARD_UPDATED`; record on return from the external Billing Portal, evaluating either the return redirect or the next `customer.subscription.updated` webhook that changes `default_payment_method`)
     - `membership.py::record_invoice_from_stripe` (`PAYMENT_CONFIRMED`) and `mark_invoice_failed` (`PAYMENT_FAILED`)
     - `stripe_admin_actions.py::refund_order` (`REFUND_ISSUED`)
     - `family_pricing.py::recompute_family_discounts_for_person` (`FAMILY_DISCOUNT_CHANGED`, only when `previous != discount_applies`, matching the existing decision to synchronize Stripe)
   - `describe_for_client(event)` / `describe_for_admin(event)`: pure presentation functions keyed by `event_type`.

3. **Client view and template**: a new section/tab on the home page (`templates/home/dashboard.html` or a dedicated template) listing `describe_for_client(event)` for events belonging to `get_family_group_members(authenticated_person)`, in reverse chronological order with simple pagination (latest N or by period).

4. **Admin view and template**: a new tab in the existing administration hub, or an extension to `/administration/audit/`, showing `describe_for_admin(event)`, actor, technical `context`, and filters by person, period, and `event_type`.

5. **Test plan**: event emission from each of the nine points; different `describe_for_client` and `describe_for_admin` text for the same event; chronological ordering; and family isolation (an event from one family never appears in another family's timeline).

## Out of scope
- Correcting recurring Asaas billing synchronization (a separate pre-existing architectural gap). This PRD only records what services already do and does not correct the gateway.
- Retroactively recording events that occurred before this PRD (no history backfill; the timeline begins when this feature is deployed).
- Active event notification by email/push; this is a passive timeline consulted on demand.
- Admin editing/deletion of events; the audit is append-only.

## Impacted files
- `system/models/membership_timeline.py` (new)
- `system/models/__init__.py` (export the new model)
- `system/migrations/0001_initial.py` (regenerated through the destructive cycle)
- `system/services/membership_timeline.py` (new: `record_membership_event`, `describe_for_client`, `describe_for_admin`)
- `system/services/dependent_registration.py`, `system/views/dependent_views.py`, `system/services/plan_change.py`, `system/services/stripe_admin_actions.py`, `system/services/membership.py`, `system/services/family_pricing.py`, `system/services/stripe_checkout.py` (calls to the central service)
- `MembershipPauseRequest` service/view (locate the exact implementation during development, likely `system/services/membership_pause.py` or the PRD-132 equivalent)
- `system/views/home_views.py` or new `system/views/timeline_views.py` (client view)
- `system/views/admin_views.py` or new `system/views/timeline_admin_views.py` (admin view)
- `templates/home/dashboard.html` plus a new timeline template
- `templates/audit/` extension or a new admin template directory
- `system/tests/test_membership_timeline.py` (new)

## Risks and edge cases
- An event can have `membership=None` when the removed dependent no longer has an active Membership; the model must support `null=True`.
- Event volume per family can grow without pagination; mitigate with pagination from the start.
- Sensitive `context` data could accidentally leak into the client timeline; mitigate by centralizing all `context` reads within `describe_for_client`/`describe_for_admin` and never rendering raw `context` in a template.
- A duplicate webhook could generate a duplicate event. Stripe already enforces webhook idempotency through `StripeWebhookEvent`, but the timeline emission service has no independent protection. Evaluate checking for a recent duplicate by `(membership, event_type, context)`, or accept the risk because `StripeWebhookEvent` already prevents reprocessing the same Stripe event.

## Rules and constraints
- Use the existing `transaction.atomic` in each service; do not create a new transaction only for the event.
- No business rules in templates; `describe_for_client`/`describe_for_admin` belong in `services/`.
- No comments/docstrings by default.
- Tests must cover all nine emission points before declaring Green.

## Plan
1. Add the `MembershipTimelineEvent` model and regenerate the destructive migration.
2. Add the `record_membership_event`, `describe_for_client`, and `describe_for_admin` service functions.
3. Integrate calls at each of the nine mutation points, one at a time, with a test before code (TDD).
4. Add the client view and template.
5. Add the admin view and template.
6. Run the complete suite, `manage.py check`, and visual validation of both screens.

## Test plan
### Tests to author
- `record_membership_event` creates a record with the correct fields.
- Each of the nine mutation points calls `record_membership_event` with the expected `event_type` and `context` (mock or post-call database verification).
- `describe_for_client`/`describe_for_admin` return distinct text for every `event_type`, and the client version contains no technical data.
- The client timeline does not show another family's event (isolation).
- Reverse chronological ordering.

### Execution authorization
Local; ORM, migrations, and tests authorized by `AGENTS.md`.

### Execution evidence
`manage.py test system.tests.test_membership_timeline` → 18 tests, OK (see Evidence).

## Visual validation
- Authenticated client (`529.982.247-25`): the "Histórico de alterações" ("Change history") button appears on the `MENSALIDADE` ("TUITION") card. The modal opens with five test events in reverse chronological order, including date/time and plain text, with **no technical data** (no visible Stripe/Asaas ID). Confirmed in light theme, dark theme, and mobile viewport (375×812); text is truncated with an ellipsis on the mobile card, matching the pattern used by other app modals.
- Admin (`admin`, through `/administration/historico-assinaturas/`): lists the same five events with complete technical text, for example, `Assinatura cancelada (Stripe: sub_visual_test) — por Sistema/webhook` ("Subscription cancelled (Stripe: sub_visual_test) — by System/webhook") and `Desconto família aplicado — R$ 220.00 → R$ 180.00` ("Family discount applied — R$ 220.00 → R$ 180.00"). Filtering by event type (`card_updated`) correctly reduced five results to one.
- The "Histórico de assinaturas" ("Subscription history") card appears in the `/administration/` hub with the dynamic counter `5 EVENTOS REGISTRADOS` ("5 EVENTS RECORDED").
- Browser console contained no errors.
- Validation data (person `Visual Timeline Teste` and five manual events) was removed from the local database after validation.

## ORM validation
The destructive migration was regenerated (`clear_migrations.py` plus `makemigrations` plus `migrate`) with `MembershipTimelineEvent`; reference seeds were reapplied for visual validation.

## Quality validation
`manage.py check` clean; complete suite with no regressions (639 tests).

## Evidence
- `manage.py test system.tests.test_membership_timeline` → **18 tests, OK**.
- `manage.py test` (complete suite after all corrections) → **639 tests, OK**, with no regressions.
- `manage.py check` → clean.
- **Real bug found and corrected during the complete suite**: `stripe_admin_actions.py` passed `admin_user` (a Django `User` instance representing the technical administrator) directly as `actor=` to `record_membership_event`, but `MembershipTimelineEvent.actor` is a foreign key to `Person`. This caused a real `ValueError` when cancelling a subscription through `CancelMembershipActionView`. Corrected by removing `actor=admin_user` at the affected call sites (both `cancel_membership` branches, `change_membership_plan`, and `refund_order`) while retaining `actor_is_admin=True`, because the technical admin does not necessarily have a corresponding `Person`.

## Implemented
See Scope. All items were implemented: `MembershipTimelineEvent` model (destructive migration regenerated); `membership_timeline.py` service (`record_membership_event`, `describe_for_client`, `describe_for_admin`, `build_client_timeline`, `build_admin_timeline`); emission at the mapped 9+ mutation points; client view/template (home-page modal); and admin view/template (`/administration/historico-assinaturas/` with person/type filters).

## Cleanup findings
- The `actor` foreign-key bug (`User` versus `Person`) was found and corrected; see Evidence.
- Manual visual-validation data was removed after use.

## Follow-up PRDs
- Recurring Asaas billing synchronization with `billed_price`/family discount is handled in PRD-135 (Part A), implemented next in the same session.

## Deviations from plan
- `CARD_UPDATED` is recorded when redirecting to the Billing Portal (client intent), not on a confirmed return. This was already documented as an open decision in the original PRD. Capture at the trigger point was selected because it is deterministic and does not depend on a query parameter not currently consumed by any view (`?card_update=done`).

## Pending
No pending code work. Not implemented: active notification (out of scope) and backfilling events without a reliable historical trace (treated as an accepted limitation in PRD-135).

## Final status
**Completed** — the model, service, emission at the mapped 9+ points, and client/admin views and templates were implemented and validated through automated tests plus real browser validation in light theme, dark theme, and mobile. A real type mismatch involving the `actor` foreign key was found and corrected while running the complete suite.
