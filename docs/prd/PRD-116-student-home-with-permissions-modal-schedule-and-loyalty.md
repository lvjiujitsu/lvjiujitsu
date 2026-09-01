# PRD-116: The student home with permissions, a modal schedule, and the loyalty period

## Summary
Fix the student home so an ordinary student has no create-open-class action, the schedule opens in a modal on the home itself, approved attendances can be shown as a local example, and recurring Stripe plans stay blocked for a change/cancellation until the commitment release date.

## Demand type
A UI/UX fix + a Django permission/billing rule + a local load of demo data.

## Current problem
- The home renders `instructor_toolbar="full"` whenever `today_classes` exists, even for an ordinary student, exposing `Criar aulão` ("Create open class").
- The `Cronograma` ("Schedule") action is a link to another page, but the expected behavior is a popup/modal.
- A newly registered student has no approved attendance history for the demo.
- The plan change lock depends only on `Membership.stripe_subscription_id`; in the real Stripe flow, the active monthly fee can be on a recurring plan without that field persisted.
- The screen shows `Trocar plano` ("Change plan") despite the acceptance of the recurring plan's commitment/loyalty period.

## Goal
- Normalize today's classes toolbar by real permission.
- Keep an ordinary student without `Criar aulão` ("Create open class") in the home's DOM.
- Open the schedule in a modal with embedded content, without changing the home's URL.
- Centralize the recurring plan blocking rule for both the UI and the POST endpoint.
- Show a message with the release date for the change/cancellation.
- Insert fictitious approved attendances into the local database for the validation student.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `templates/calendar/calendar.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/services/membership.py`
- `system/models/membership.py`
- `system/models/plan.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_plan_change_views.py`

### Adjacent files consulted
- `system/tests/test_membership_actions_ui.py`
- `system/tests/test_plan_commercial.py`
- `docs/prd/README.md`

### Internet / official documentation
- Django 5.2 authentication and view protection via Context7: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Conclusion: permissions must be applied in the backend/view and the UI cannot be the only barrier.

### Limitations found
- There is no dedicated loyalty/commitment end field in the `Membership` or `SubscriptionPlan` model; in this delivery the operational date displayed uses `current_period_end`.
- The student home has no cancellation flow of its own today; the message mentions the change/cancellation because that is the requested business rule, but the visible action fixed here is the plan change.
- Creating an open class already has protection at the operational endpoint; the failure observed is a toolbar/template one for the student.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: fix it, insert local fictitious data, and validate the screen.

## Design proposal
- The goal: keep the student home as a personal panel, with no operational instructor actions.
- The hierarchy:
  - The `Turmas de hoje` ("Today's classes") section: the title on the left; compact actions on the right.
  - An ordinary student: History when there are attendances + Schedule.
  - An operational/instructor person: History + Create open class + Schedule.
  - The schedule modal: a `Cronograma` ("Schedule") header, a close button, and an internal iframe with the calendar in embedded mode.
  - The expanded monthly fee: the current data, the term, and the block notice when the recurring plan is within its commitment period.
- The states:
  - The schedule closed/open/loaded.
  - An unlocked plan shows `Trocar plano` ("Change plan").
  - A locked plan hides `Trocar plano` ("Change plan") and shows the notice with the date.
  - Desktop and mobile keep the actions with no overflow.

## Acceptance criteria
- [x] An authenticated ordinary student at `/home/` does not see `Criar aulão` ("Create open class").
- [x] An instructor/operational person keeps the `Criar aulão` ("Create open class") action when authorized.
- [x] The `Cronograma` ("Schedule") action at `/home/` is a button/modal and not a direct navigation link.
- [x] Clicking `Cronograma` ("Schedule") opens a popup without changing the home's URL.
- [x] The embedded calendar does not render a duplicated topbar.
- [x] A recurring Stripe plan with `gateway_code="stripe_card"` is blocked even without `stripe_subscription_id`.
- [x] The plan change endpoint rejects a blocked recurring plan with a pt-BR message.
- [x] The home shows the release date for the change/cancellation when blocked.
- [x] The local database contains fictitious approved attendances for the validation student.
- [x] The validation in the internal browser covers desktop/mobile, a console with no errors, and the modal flow.

## Expected evidence
- Focused home and plan change tests.
- `python manage.py check`.
- Visual validation in the internal browser on desktop and mobile.
- The local ORM confirming the fictitious approved attendances.

## Scope
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `templates/calendar/calendar.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_plan_change_views.py`
- A local database load for the test student.

## Out of scope
- Creating a new contract/loyalty field in the schema.
- Redesigning the whole financials or the Stripe checkout.
- Creating a self-service cancellation flow.
- Changing the registration again.

## Executed evidence
- The expected Red: `python manage.py test system.tests.test_home_dashboard.HomeDashboardContractTestCase.test_student_with_today_class_does_not_receive_instructor_toolbar system.tests.test_plan_change_views.PlanChangeSelectViewTestCase.test_stripe_gateway_membership_is_rejected_without_subscription_id system.tests.test_plan_change_views.HomeDashboardPlanChangeContextTestCase.test_home_locks_stripe_gateway_plan_without_subscription_id`: 3 tests, failed before the code because of the missing toolbar and the Stripe gateway with no block.
- An additional expected Red: `python manage.py test system.tests.test_calendar.CalendarServiceTestCase.test_calendar_embedded_mode_is_same_origin_and_hides_topbar`: failed with `X-Frame-Options: DENY`.
- `node --check static/system/js/home/dashboard.js`: OK.
- `python manage.py check`: OK, no issues.
- `python manage.py test system.tests.test_home_dashboard system.tests.test_plan_change_views system.tests.test_calendar system.tests.test_lv_foundation_calendar`: 111 tests, OK.
- The local ORM: 8 approved attendances created/confirmed for `Aluno Stripe Codex`, `schedule_ids=[3, 4]`.
- The internal browser on desktop at `/home/`: `dashboard.css?v=18`, `dashboard.js?v=12`, `createButtons=0`, the text `Criar aulão` ("Create open class") absent, `calendarButtons=1`, direct links to `/calendar/` absent.
- The internal browser on desktop: the notice shown as `Troca e cancelamento liberados em 02/08/2026, após a carência da assinatura recorrente.` ("Change and cancellation released on 02/08/2026, after the recurring subscription's commitment period."), the `Trocar plano` ("Change plan") button absent.
- The internal browser on desktop: the schedule modal opened without changing `http://127.0.0.1:8000/home/`; the iframe with `calendar-board=1`, `topbar=0`, the title `Cronograma` ("Schedule"), the month `Julho 2026` ("July 2026").
- The internal browser on desktop: the attendance history opened with 8 approved items, 6 visible on the first page.
- The internal browser on mobile 390x844: no horizontal overflow, `createButtons=0`, `calendarButtons=1`, `historyButtons=1`, the `Trocar plano` ("Change plan") button absent, and the commitment notice visible.
- The internal browser on mobile 390x844: the schedule modal opened at width 390, with no overflow, the title `Cronograma` ("Schedule") and `topbar=0`.
- The internal browser's console: no errors.

## Cleanup / follow-up
- The schedule's direct link behavior removed from the home.
- The blocking rule was centralized in `system.services.plan_change`.
- Debt outside the scope recorded in `PRD-117-contractual-fidelity-to-recurring-plans.md`: a dedicated contractual field for the commitment/loyalty end date.
