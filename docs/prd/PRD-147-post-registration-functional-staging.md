# PRD-147: Post-Registration Functional Validation

## Summary

Validate, with local data and sandbox integrations, the post-registration flows for the accounts created in PRD-145: class/check-in, instructor operations, time-based pause and resumption, plan and card changes, the complete dependent lifecycle, and change history. Validation combines the real interface, ORM, controlled date simulation, Django tests, and desktop/mobile rendering.

## Demand type

End-to-end functional validation + regression audit + fixes conditioned on proven failures.

## Current problem

- The nine PRD-145 users were registered and authenticated, but subsequent usage flows have not yet been rerun with those accounts.
- PRDs 131 through 134 declare class, pause, plan, card, and timeline work complete, but their evidence comes from previous rounds and does not prove the current working-tree and local-database state.
- PRD-121 formally remains `Not completed`, although later PRDs cover part of its scope.
- PRD-118 left explicit idempotency and materials limitations; removal and family history must be exercised in the current flow.
- No single evidence set correlates a visual action, persisted transition, and timeline event for every requested scenario.

## Goal

Prove that the created accounts can use the requested flows without regression and, when an in-scope failure is reproduced, fix it with TDD, revalidate the affected path, and record actual evidence.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md`
- `docs/prd/PRD-118-add-dependent-after-enrollment.md`
- `docs/prd/PRD-121-client-home-dependents-tuition-and-modal-crud.md`
- `docs/prd/PRD-123-client-account-modal-with-editing-and-deletion.md`
- `docs/prd/PRD-130-migrate-plan-change-to-plantier-planprice-catalog.md`
- `docs/prd/PRD-131-fix-default-instructor-present-on-cancel-and-restore-class.md`
- `docs/prd/PRD-132-free-plan-transitions-and-tuition-pause.md`
- `docs/prd/PRD-133-payment-indicator-and-stripe-card-change.md`
- `docs/prd/PRD-134-subscription-family-event-history-information-timeline-client-technical-audit-admin.md`
- `docs/prd/PRD-145-registration-payment-documentation-operational-audit.md`
- `docs/prd/PRD-146-public-instructor-and-link-to-existing-classes.md`

### Adjacent files consulted

- `system/urls.py`
- Models, forms, services, selectors, views, templates, assets, and tests for calendar, membership, pause, plan, card, dependent, and timeline flows, as detailed during execution.

### Internet / official documentation

- Django 5.2 testing: https://docs.djangoproject.com/en/5.2/topics/testing/overview/
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Stripe Customer Portal: https://docs.stripe.com/customer-management
- Stripe payment-detail updates: https://docs.stripe.com/payments/checkout/subscriptions/update-payment-details
- Stripe subscription plan changes: https://docs.stripe.com/billing/subscriptions/change-price

Conclusions: database tests must remain isolated; multi-write domain operations must be atomic; Billing Portal is the official payment-method update path; changing a price requires replacing the current subscription item and may produce proration.

### Context7 / MCPs / tools verified

- Context7: `/websites/djangoproject_en_5_2` and `/websites/stripe`.
- In-app browser available at `http://127.0.0.1:8000`.
- Stripe test mode, local listener, and tunnel reported active by the user.
- PowerShell, `rg`, Python/Django, and local ORM available.

### Limitations found

- No HG or production write is authorized; gateways are sandbox/test mode only.
- Time simulation must use controlled test/ORM dates without changing the operating-system clock.
- Stripe hosts Billing Portal and it cannot be validated in an iframe; entry, redirect, and API/webhook confirmation are the appropriate evidence.
- PRD-146 remains outside scope because it depends on product decisions about associating instructors with existing classes.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `browser:control-in-app-browser`
- `lv-cleanup-audit`

## Understanding approved

The current request authorizes local/sandbox tests through completion, operation of the created accounts, controlled date simulation, and fixes for proven failures within the listed flows. Product changes, HG/production work, or expansion into PRD-146’s pending decision are not authorized.

## Execution prompt

### Persona

Senior Django/MVT agent responsible for functional validation and LV JIU JITSU regression testing.

### Action

Execute the end-to-end matrix, correlate each visual action with persistence and timeline state, fix only reproduced in-scope defects, and deliver desktop/mobile evidence.

### Context

The accounts, memberships, and `Jiu Jitsu Auditoria` (“Jiu Jitsu Audit”) class already exist in the local database. Instructor `Auditoria Professor` (“Audit Instructor”) has Tuesday and Thursday schedules at 20:30.

### Constraints

- Use the real interface for user-accessible actions.
- Use ORM/controlled tests only for inspection, proportionate setup, and time simulation impossible to perform in real time.
- Preserve history and avoid physical person deletion.
- Do not expose secrets, keys, or tokens in evidence.
- Use TDD before any behavioral fix.
- Do not edit `staticfiles/`.

### Acceptance criteria

- [x] Student checks into the created instructor’s class and the instructor approves attendance.
- [x] Instructor confirms presence, assigns/changes a substitute, and the transition is persisted and visible.
- [x] Instructor cancels and restores the class without improperly locking check-in.
- [x] Pause is requested and approved and blocks check-in during its window.
- [x] Time simulation proves resumption/unlocking after the end date and quota reset on the enrollment anniversary.
- [x] Plan change is executed and membership reflects the resulting plan without a duplicate subscription.
- [x] Stripe card change enters through Billing Portal and the change is confirmed in test mode without ending the active term.
- [x] Dependent is added, has the plan changed, and is then removed without physical deletion.
- [x] Client timeline and administrative audit record addition, plan, and removal without leaking technical data to the client.
- [x] Forgotten adjacent features are inventoried and classified as working, reproduced defects, or documented debt.
- [x] Main paths and error states render on desktop and mobile, in light and dark themes, without overflow or critical console errors.
- [x] Focused tests, `manage.py check`, and a proportionate suite pass in the final state.

### Expected evidence

- Before/after ORM state for sessions, check-ins, pause, membership, dependent, and timeline.
- Sandbox IDs only when necessary for traceability, without secrets.
- Desktop/mobile screenshots of key states.
- Actual test/check commands and results.

### Output format

Closure in English: implemented/fixed work, actual evidence, unvalidated items with reasons, pending work/deviations, and final status.

## Scope

- Student check-in and instructor approval.
- Presence, substitution, class cancellation, and restoration.
- Medical pause/freeze, approval, and time-based resumption.
- Plan change among eligible options and Stripe card change.
- Dependent addition, plan change, and removal.
- Client timeline and administrative audit.
- Strictly necessary fixes for defects reproduced in these paths.
- Updates to this PRD, the index, and documentation directly affected by actual findings.

## Out of scope

- Deployment, HG/production, or real charges.
- Decision/implementation of PRD-146 `existing` mode.
- General home redesign or complete resolution of the frontend/backend critique in PRDs 138 through 144.
- Physical deletion of a dependent person.
- Commercial-rule or price changes without an existing contract.

## Impacted files

- `docs/prd/PRD-147-post-registration-functional-staging.md`
- `docs/prd/README.md`
- Evidence under `docs/prd/evidence/`.
- Code/test/documentation files only when a failure is proven and fixed; recorded under `Implemented`.

## Risks and edge cases

- Lazy class session does not yet exist for the day.
- Pending versus confirmed substitute instructor.
- Class canceled while check-in is pending.
- Overlapping pauses, retroactive periods, and 30-day limit.
- Stripe plan in a grace period and change to another gateway.
- Abandoned checkout must not alter the active membership.
- Real `customer.subscription.updated` event must not zero out the active term.
- Removed dependent must remain as a historical person and disappear only from the active family group.
- Timeline must maintain isolation between families.

## Rules and constraints

- Backend is the authority for permissions and transitions.
- Compound writes use `transaction.atomic`.
- Simulated dates use controlled, timezone-aware mocks/fixtures.
- Destructive actions use POST/CSRF and visual confirmation.
- Screenshots must not display secrets.

## Plan

1. Baseline database, routes, contracts, and focused tests.
2. Class: check-in, approval, confirmation/substitution, cancellation/restoration.
3. Pause: request, approval, blocking, and time-based resumption.
4. Financial: plan and card changes.
5. Family: add, change plan, remove, and audit timeline.
6. Adjacent inventory, proven fixes, and regression.
7. Desktop/mobile/theme/console validation and final cleanup.

## Test plan

### Tests to author

- Only when an uncovered failure is reproduced: write the smallest regression test before the fix.
- Rerun existing calendar, pause, plan, card, dependent, and timeline tests as the baseline.
- Simulate pause dates with `mock.patch`/reference dates without waiting for real calendar time.

### Execution authorization

Tests, ORM, and sandbox gateways are authorized by the current request. HG/production is not.

### Execution evidence

- `system.tests.test_calendar`: 107 tests, `passed`, 48.193 s.
- `system.tests.test_dependent_registration`: 31 tests, `passed`, 24.672 s in the post-cleanup rerun.
- `system.tests.test_membership_pause`, `test_membership_card_update`, and `test_membership_timeline`: 61 tests, `passed`, 20.493 s.
- `system.tests.test_dependent_cancellation_lock`, `test_home_dependents_section`, and `test_home_dashboard`: 27 tests, `passed`, 24.414 s.
- Four plan-change modules: 40 tests, `passed`, 6.492 s.
- `manage.py check`: no issues.
- `makemigrations --check --dry-run`: no changes detected.
- `compileall` and `node --check` for both changed JavaScript files: no errors.
- Complete `system` suite: 689 tests, `passed`, 304.461 s; test database created and destroyed in isolation.

## Visual hierarchy

- Student/guardian home: today’s class, membership, dependents, and history.
- Instructor home: today’s class, presence, substitution, cancellation, and check-ins.
- Administration: pause queues and technical history.
- Primary actions remain close to the state they change; messages explain the next state.

## Wireframe

### Class

- Class header and time.
- Class/instructor state.
- Allowed actions: check in, confirm/cancel presence, assign substitute, cancel/restore class.
- Pending/approved check-in list.

### Membership

- Current plan and gateway.
- Active term/pause.
- Actions: change plan, pause, and change card when applicable.
- Change history.

### Dependent

- Card with relationship, plan, graduation, and actions.
- Addition/edit modal.
- Removal confirmation.

## State machine

- Class: `scheduled` -> `teacher_absent` or `substitute_pending` -> `confirmed`; `scheduled` -> `canceled` -> `scheduled`.
- Check-in: `absent` -> `pending` -> `approved`; cancelable only while pending.
- Pause: `pending` -> `approved` or `rejected`; `approved_in_window` -> `ended_unlocked` by date.
- Plan: `current` -> `order_pending` -> `paid/applied` or `abandoned`.
- Dependent: `not_linked` -> `linked` -> `plan_changed` -> `unlinked`, preserving the person and historical events.

## Visual validation

- Real browser: instructor home, approved check-in, confirmed presence, substitute, cancellation/restoration, dependent plan, and client/admin timelines.
- Desktop: 1440x900/1425x891; mobile: 375x812; light and dark themes.
- Administrative mobile timeline fixed to stack the card and wrap name/description, without unrecoverable ellipsis or horizontal overflow.
- DOM measurement at 390 px confirmed `flex-direction: column`, `white-space: normal`, `text-overflow: clip`, and no horizontal overflow.
- In-app browser console: zero application errors and warnings. Chrome displayed noise from a Méliuz extension; the overlay was closed and the contaminated capture removed from evidence.
- Evidence: `prd-147-instructor-class-desktop.png`, `prd-147-instructor-class-mobile-dark.png`, `prd-147-admin-timeline-desktop.png`, `prd-147-admin-timeline-mobile-light.png`, `prd-147-admin-timeline-mobile-dark.png`, and `prd-147-dependent-plan-mobile-dark.png`.

## ORM validation

- Class `ClassSession.id=1`: `scheduled`, instructor present, no residual substitute; student `Person.id=8` check-in approved by `Person.id=16`.
- Pause for `Membership.id=1`: 2026-07-14 through 2026-07-16, approved; term extended by three days. Time-based tests confirmed blocking during the window, release on the first later day, and quota reset on the anniversary.
- Asaas student: changed to `PlanPrice.id=12`/Adult 5x, order 5 paid, BRL 36.47.
- Stripe student: exactly one `card_updated` event; remote default method changed to final test Mastercard 4444 without ending membership.
- Cycle dependent `Person.id=17`: added with `Membership.id=5`, changed from Adult 2x Stripe to Adult 5x Asaas, previous Stripe subscription canceled, order 7 paid in sandbox, and family relationship removed. Person and membership remain active.
- Dependent timeline preserved, in order, `dependent_added`, `payment_confirmed`, `membership_canceled`, `plan_changed`, and `dependent_removed`.

## Quality validation

- Fixes written with regression tests before code.
- Backend check-in authorization validated with HTTP 403 for an unrelated class.
- Card update records history only after confirming an actual Stripe change; opening the portal or returning without a change produces no false event.
- Dependent Asaas checkout error returns to the form; retry in the same session reuses the pre-registration, while another session cannot capture the pending record.
- Clean `git diff --check`; diff scan found no real secrets, `except: pass`, TODO, new `innerHTML`, or debug logging.
- No migration, `staticfiles/` edit, HG/production write, or real charge.

## Evidence

- Real interface and ORM correlated for every requested transition.
- Stripe test mode: real Billing Portal, Mastercard test card, and prior dependent subscription cancellation confirmed remotely.
- Asaas sandbox: payments 5 and 7 confirmed through the official endpoint, with signed webhooks received by LV over HTTP 200.
- Screenshots versioned under `docs/prd/evidence/` in the six files listed under `Visual validation`.

## Implemented

- Validation PRD created before any flow mutation.
- A session created through check-in now inherits the default instructor-present state.
- Direct check-in to a class without active enrollment is blocked in both the service and view.
- Instructor-home attendance counters update after asynchronous approval.
- Card-change event changed from “portal opened” to “remote method actually changed.”
- Dependent checkout handles Asaas errors without HTTP 500, redirects external checkout outside the iframe, resumes the password after payment, and recovers a retry only from the same session.
- Administrative mobile timeline received its own stylesheet and fully readable content.
- Explicit time-based test guarantees check-in after pause ends.

## Cleanup findings

- Evidence containing an extension pop-up was removed; only clean captures were kept.
- No residue, dead code, duplication, or material new hardcoding was found in the changed flow.
- The instructor financial condition was preserved but not made active configuration because unit, accounting period, payment day, and proration remain undefined. The debt was separated into PRD-148 without inferring a financial obligation.
- This audit covers PRD-147 scope; it does not declare the entire system free of debt cataloged in PRDs 138 through 144.

## Follow-up PRDs

- PRD-146: decide whether a publicly approved instructor creates a new class or can join existing classes.
- PRD-148: define and activate payout configuration for a publicly registered instructor.

## Deviations from plan

- The Asaas sandbox account rejected the ngrok callback because the registered domain was HG. For local validation, payment was confirmed through the official sandbox endpoint and delivered to the local webhook with a valid signature; no HG configuration was changed.
- The in-app browser screenshot backend became unavailable near the end. Final captures were taken in controlled Chrome, in a local session and real viewports.
- The first full-suite attempt exceeded the runner’s five-minute timeout without finishing; it was restarted with a longer window and is not counted as a result.

## Pending

- Product decisions in PRDs 146 and 148; neither blocks the flows validated in this PRD.

## Final status

**Completed with limitations** — all requested flows and the full regression suite were validated locally/in sandbox. Only product decisions in PRDs 146 and 148 and the external Asaas callback-domain divergence remain, without blocking the validated flows.
