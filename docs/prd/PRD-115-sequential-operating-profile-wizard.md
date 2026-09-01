# PRD-115: A sequential operational profile wizard

## Summary
Fix the public registration so that Instructor and Back office keep being people inside the main wizard, using `registration_profile=other` and additional sequential steps. The flow must not open separate public pages for those profiles. The instructor states their link to an existing active class or a new schedule proposal in a multi-day modal, plus a single financial condition. The back-office person states the requested areas, whether they also train, and their single financial condition.

## Demand type
A UI/UX fix + a Django workflow adjustment + the structured persistence of pending requests.

## Current problem
- In `/register/`, the `Professor` (`Instructor`) card is a link (`<a>`) separate from the wizard's state machine, so it appears highlighted by the browser/comment and skips the normal selection sequence.
- There is no `Administrativo` (`Back office`) card on the initial screen, even though PRD-112 already has the public pending request flow.
- Instructor and Back office still do not collect enough payout/intent data for management to correctly approve the composite profiles described in PRDs 111, 112, and 113.
- The operational financials allowed incoherent combinations, such as barter and PIX payout at the same time.
- The instructor's schedule proposal had only a single weekday select, preventing a recurring Monday-to-Friday proposal.
- The instructor's class selection considered only "without an instructor"; the correct rule is to allow requesting a link to an active class, recording in the payload whether there is a current instructor for a later approval.
- The Back office's sub-option shows up with a native fieldset/radio, outside the visual pattern of the dependents block.
- The Instructor and Back office icons do not communicate the profile correctly.
- `/register/teacher-proposal/` and `/register/admin-access/` use the administrative topbar, the theme toggle, and a long single-page form, instead of the conventional step-based registration.

## Goal
- Keep Student and Guardian in the current enrollment wizard.
- Turn Instructor and Back office into selectable options of the same wizard, with no redirect on the card or on the `Próximo` (`Next`) button.
- Persist Instructor and Back office as a person registration (`other`) with the correct `other_type_code`.
- Reuse the personal data, health, and martial arts steps for those profiles.
- Add extra steps: the instructor's schedule, the administrative areas, and the financial/payout condition.
- Redirect the legacy public instructor/back-office URLs to `/register/?profile=...`, without rendering the old form.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`
- `docs/prd/PRD-111-staging-seeds-registration-nn.md`
- `docs/prd/PRD-112-request-for-administrative-access-pending.md`
- `docs/prd/PRD-113-instructor-class-and-schedule-request.md`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `system/models/request_workflows.py`
- `system/forms/access_request_forms.py`
- `system/forms/class_request_forms.py`
- `system/services/access_requests.py`
- `system/services/class_requests.py`
- `system/views/access_request_views.py`
- `system/views/class_request_views.py`
- `templates/access_requests/request_form.html`
- `templates/access_requests/request_detail.html`
- `templates/class_requests/new_teacher_form.html`
- `templates/class_requests/request_detail.html`
- `system/tests/test_register_wizard_contract.py`
- `system/tests/test_administrative_access_requests.py`
- `system/tests/test_class_catalog_requests.py`
- `system/tests/test_administrative_access_request_views.py`
- `system/tests/test_class_catalog_request_views.py`

### Adjacent files consulted
- `system/models/asaas.py`
- `system/forms/person_forms.py`
- `system/services/asaas_payroll.py`
- `system/urls.py`
- `system/tests/test_administrative_access_request_views.py`
- `system/tests/test_class_catalog_request_views.py`

### Internet / official documentation
- Django 5.2 FormView: `https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/#formview`
- Django 5.2 form validation: `https://docs.djangoproject.com/en/5.2/ref/forms/validation/`
- Django 5.2 JSONField: `https://docs.djangoproject.com/en/5.2/ref/models/fields/#jsonfield`
- MDN button element: `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/button`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `FormView`, validation in `clean()`, form errors, `TestCase`.

### Limitations found
- `AdministrativeAccessRequest` had no JSON payload before this PRD; it needs a structured field so the operational intent is not mixed into free text.
- The existing instructor bank account model (`TeacherBankAccount`) stores PIX; a traditional bank account will be kept in the request's payload for a manual decision, with no automatic transfer in this delivery.
- The full payment/barter rule for the back office still depends on a later financial design; this delivery records the intent for the approval, it does not create an automatic payroll/payout.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: "implement the fixes and let's move on".

## Design proposal
- The goal: keep the screen as a profile questionnaire and continue the conventional step-based registration.
- The hierarchy: four cards of the same visual family in one column: Student, Guardian, Instructor, Back office.
- The states:
  - Student: reveals the existing question about dependents.
  - Guardian: reveals the existing summary about the student(s) under their responsibility.
  - Instructor: reveals a short note and continues to personal data, health, martial arts, the schedule, and the financials.
  - Back office: reveals the initial training/compensation choice and continues to personal data, health, martial arts, the administrative areas, and the financials.
- The instructor:
  - can select one or more existing active classes;
  - classes with a current instructor record `approval_scope=admin_and_current_teacher`;
  - classes with no instructor record `approval_scope=admin_only`;
  - can create a schedule proposal through a modal in the step itself, with a weekday checklist.
- The operational financials:
  - use a single condition: `pays_monthly`, `barter`, `volunteer`, `paid_fixed`, `paid_per_student`, or `paid_mixed`;
  - `barter`, `pays_monthly`, and `volunteer` do not accept payout data;
  - the paid conditions require an amount/percentage as appropriate and PIX or a bank account.
- Desktop/mobile: keep the current wizard's width and rhythm, with one main column and no wide administrative forms.

## Acceptance criteria
- [x] The `Professor` (`Instructor`) card in `/register/` is no longer an `<a>` and does not redirect on a card click.
- [x] Instructor and Back office use the same visual state (`aria-pressed`, the circular check, the `Próximo` — `Next` — button) as Student/Guardian.
- [x] Selecting Instructor and clicking `Próximo` (`Next`) opens the personal data step of the same wizard.
- [x] Selecting Back office and clicking `Próximo` (`Next`) opens the personal data step of the same wizard.
- [x] Instructor and Back office submit `registration_profile=other` with the correct `other_type_code`.
- [x] Instructor and Back office reuse the personal data, health, and martial arts steps.
- [x] The instructor has a step to choose an existing active class or create a proposal in a modal.
- [x] An active class with a current instructor appears in the selection and records a review by management and the current instructor.
- [x] The schedule proposal modal uses a weekday checklist and accepts Monday through Friday in the same payload.
- [x] The back-office person has a step for the requested administrative areas.
- [x] Both have a single financial condition step, without allowing barter together with PIX/a bank account.
- [x] The paid conditions require a payout method and the corresponding amount/percentage fields.
- [x] The `/register/teacher-proposal/` and `/register/admin-access/` URLs redirect to the main registration with the profile preselected.
- [x] The old public `request_wizard` template/JS is not part of the registration contract.
- [x] A public administrative request saves the payload with `training_intent`, `compensation_preference`, and the PIX data where applicable.
- [x] A public instructor proposal saves the payload with `payout_method` and the PIX/bank account data.
- [x] Approving a new instructor with PIX creates/updates the approved instructor's `TeacherBankAccount`.

## Expected evidence
- A static test of the wizard's contract.
- Form/service tests for the administrative request.
- Form/service tests for the instructor proposal.
- `manage.py check`.
- A focused test or a proportional suite.
- Desktop/mobile visual validation in the internal browser.

## Scope
- `templates/login/register.html`, `static/system/js/auth/register.js`, `static/system/css/auth/register.css`.
- `PortalRegistrationForm`, light validation, and the creation of `other`.
- The redirect of the legacy public routes.
- The forms, services, and templates of the already-existing instructor/back-office requests.
- A model/migration for a structured payload in `AdministrativeAccessRequest`.
- Proportional tests in the affected contracts.

## Out of scope
- Creating a charge, a monthly fee, a payroll, or an automatic payout for the barter/PIX back-office person.
- Resolving the full financial contract for a traditional bank account.
- Changing the student/guardian checkout.

## Executed evidence
- `node --check static/system/js/auth/register.js`: OK.
- `python manage.py test system.tests.test_register_wizard_contract system.tests.test_administrative_access_request_views system.tests.test_class_catalog_request_views system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests`: 42 tests, OK.
- `python manage.py check`: OK, no issues.
- `python manage.py makemigrations --check --dry-run`: OK, no pending migrations.
- `python manage.py test system.tests.test_models.PersonModelTestCase.test_other_registration_creates_single_selected_type`: 1 test, OK.
- `python manage.py test`: 425 tests, OK.
- `python manage.py test system.tests.test_register_wizard_contract.RegisterWizardStaticContractTestCase system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_requires_schedule_weekdays system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_accepts_multi_day_schedule_and_paid_pix system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_accepts_active_class_with_current_teacher_payload system.tests.test_models.PersonModelTestCase.test_paid_operational_registration_requires_payout_target system.tests.test_models.PersonModelTestCase.test_barter_operational_registration_clears_payout_fields system.tests.test_models.PersonModelTestCase.test_administrative_operational_registration_requires_requested_role`: 9 tests, OK.
- The internal browser at `/register/?profile=teacher_request`: `register.css?v=24`, `register.js?v=47`, the Instructor card inside the wizard, 4 active classes rendered, classes with a current instructor showing approval by management and the current instructor, no overflow.
- The internal browser on Instructor: the `Criar horário` (`Create schedule`) modal opened with 7 weekday checkboxes, with no `#ui-teacher-schedule-weekday`; the payload saved with `weekdays=["monday","tuesday","wednesday","thursday","friday"]`.
- The internal browser on the instructor's financials: `paid_mixed` showed the fixed amount, the percentage, PIX, and hid the bank; `barter` cleared the PIX/amount/percentage and hid the payout section.
- The internal browser at `/register/?profile=administrative_request`: the Back office card inside the wizard, the sub-option with no native fieldset, 6 administrative areas, the payload `["people-support"]`, barter with no PIX, and no overflow.
- The internal browser on Student/Guardian: Student with a dependent activated the counter and a total of 12 steps; Guardian activated the counter and a total of 11 steps; no overflow.
- The internal browser on mobile 390x844: Back office in the profile with no overflow; Instructor reached `step-teacher-schedule` with 4 cards and no overflow.
- The internal browser at `/register/teacher-proposal/`: redirected to `/register/?profile=teacher_request`, `register.css?v=24`, `register.js?v=47`, the Instructor card selected, no `request-wizard-form`.
- The internal browser on desktop on Instructor: advanced to `step-teacher-schedule`, opened the `Criar horário` (`Create schedule`) modal, saved the schedule payload, and opened `step-operational-finance`; switching to PIX showed the PIX key fields and kept the bank account hidden.
- The internal browser at `/register/admin-access/?training_intent=none&compensation_preference=none`: redirected to `/register/?profile=administrative_request`, `register.css?v=24`, `register.js?v=47`, the Back office card selected, no `request-wizard-form`.
- The internal browser on desktop on Back office: advanced to `step-administrative-access`, showed 6 areas, saved the payload `["people-support"]`, and opened `step-operational-finance`.
- The internal browser on mobile 390x844 at `/register/?profile=administrative_request`: no horizontal overflow, `fieldsets=0`, `segmentCount=5`.
- The internal browser on mobile 390x844 in the `step-administrative-access` step: no horizontal overflow, 6 areas visible, cards with an adjusted width.
- The internal browser's console: no error logs.

## Cleanup / follow-up
- The old public template `templates/class_requests/new_teacher_form.html` removed for being orphaned.
- The `request_wizard` template/JS removed because the correct contract is the main wizard.
- The legacy public instructor/back-office views reduced to pure redirects to avoid dead methods and references to the removed template.
- Debt outside the scope: a unified operational approval starting from `PreRegistration` still needs a dedicated management flow; this delivery records the request as a pending pre-registration and preserves the payloads for the decision.
- Debt outside the scope: a persistent notification to the current instructor and the administrators about a class change should become its own PRD, connecting `PreRegistration`, the administrative queue, and the decision history without activating the person before the approval.
