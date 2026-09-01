# PRD-140: Dependent Wizard Fixes

## Summary
Correct the "Add dependent" wizard (reimplemented in this same session to reuse
the visual design from `auth/register.css`) in five concrete areas identified
by the user: popup header, class filtering by age/gender, plan filtering by age,
spacing inside the popup, and the absence of a review step before final
confirmation.

## Demand type
UX correction + business rule + Django MVT.

## Current problem
1. The popup header does not display the action name ("Add dependent") below
   the step line; closing is a text link on the left rather than an "X" icon on
   the right.
2. The "Choose a class" step lists every class in the catalog without
   filtering by the dependent's age/gender — breaking the category eligibility
   business rule (`CategoryAudience`) already applied in the public wizard
   (`register.js: filterGroupsByPerson`).
3. The "Choose the dependent's plan" step also does not filter by age
   (`PlanAudience`) or family-plan eligibility — it shows adult plans for
   kids/youth dependents and vice versa.
4. Wizard content touches the popup edges in places; consistent padding is
   missing inside the modal.
5. There is no final review step: confirming the last step (materials) submits
   the form directly, without a "Review and confirm" screen before the real
   submission — unlike the public wizard, which has `step-review`.

## Goal
The "Add dependent" wizard faithfully reproduces the behaviour and business
rules of the public registration wizard (`/register/`): a header identifying
the action and using a close icon, eligible classes and plans filtered by the
dependent's age/gender, consistent spacing inside the popup, and a review step
before final submission.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`
- `templates/dependents/dependent_registration.html` (version reimplemented in this session)
- `templates/login/register.html` (layout reference, `step-dep`, `step-health`, `step-martial`, `step-classes`, `step-plan`, `step-review`)
- `static/system/js/auth/register.js` (`filterGroupsByPerson`, `resolveAudience`, `calcAgeYears`, `getEligiblePlansForCurrentPerson`)
- `static/system/css/auth/register.css`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/services/class_catalog.py` (`get_ibjjf_age_category_payload`)
- `system/services/class_overview.py` (`get_registration_catalog_payload`)
- `system/services/registration_checkout.py` (`get_plan_catalog_payload`)

### Adjacent files consulted
- `static/system/js/dependents/dependent_registration.js` (new version from this session)
- `static/system/css/dependents/dependent_registration.css` (new version from this session)
- `templates/home/dashboard.html` (`dependent-registration-modal` dialog)

### Limitations found
- The public wizard resolves class/plan eligibility entirely on the client
  (JS), using `ibjjf_categories_json` to map age → audience. The dependent
  wizard needs the same catalog injected into the view context.
- There is currently no review step in the dependent flow; a client-side
  summary (name, CPF, class, plan, materials) must be built from the fields
  already populated, without duplicating state in `sessionStorage` (the form is
  already a single POST).

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user reviewed the result of the previous reimplementation and listed
specific objections, requesting "CORRIJA ESPECIFICAMENTE TUDO ISSO. gere um prd novo. e corrija isso." ("CORRECT ALL OF THIS SPECIFICALLY. create a new PRD and correct it.") — authorising immediate implementation of the scope below.

## Scope
- Dependent wizard header: "X" icon fixed on the right to close; action text
  ("Add dependent") below the progress bar.
- Filter classes by the dependent's age/gender in step 4, using the same IBJJF
  catalog as the public wizard.
- Filter plans by the dependent's age (and family-plan eligibility) in step 5.
- Adjust `.wizard-shell` padding/spacing inside the iframe modal.
- New step 7, "Review and confirm", before actual form submission.

## Out of scope
- Changing the dependent editing flow (`dependent_edit.html`), which remains a
  single page without pagination.
- Changing the already validated payment/gateway logic (Stripe/Asaas).
- Changing the public `/register/` wizard.

## Impacted files
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`
- `system/views/dependent_views.py`
- `system/tests/test_dependent_registration.py`

## Plan
1. Inject `ibjjf_categories_json` into the `DependentRegistrationView` context.
2. Rewrite the template header (X on the right, action title below the bar).
3. Implement `resolveAudience`/`calcAgeYears` in the dependent JS and filter
   classes by `category_audience` (the same public rule).
4. Filter plans by `audience` and family-plan eligibility (person count does not
   apply here — a dependent is 1 person; the family plan requires the form's
   existing `family_plan_available`).
5. Adjust `.wizard-shell` padding CSS in modal mode.
6. Add the review step (new `data-step="7"` section) that reads the already
   populated fields through JS and builds a summary; only this step's final
   button actually submits the form.
7. Tests: adjust/add coverage for the new step total and
   `ibjjf_categories_json` context.
8. `manage.py check`, `node --check`, focused suite, visual validation in the
   internal browser.

## Test plan
### Tests to author/adjust
- View context includes `ibjjf_categories_json`.
- Existing `test_dependent_registration` suite remains green (must not break
  core payload/HTML).

### Execution authorization
Authorised by the current request.

## Visual hierarchy
- Header: centred logo, "Step X of Y" on the right, closing "X" on the right
  (top), "Back" on the left when step > 1.
- Below the progress bar: fixed action title ("Add dependent").
- Below: step badge (for example, "Class") + specific heading.
- Last step before submission: editable summary (Review and confirm).

## Evidence

- `system.tests.test_dependent_registration` included in the focused suite of
  72 tests: **72/72 OK** on 2026-07-13.
- Internal browser at 1440×900 and 390×844: dialog displays the title
  `Adicionar dependente` ("Add dependent"), the `Fechar` ("Close") action,
  progress `Etapa 1 de 7` ("Step 1 of 7"), and a fixed CTA.
- The title and "X" belong to the dialog shell in `home/dashboard.html`; the
  iframe contains only wizard content, without duplicating the header.
- Code confirms IBJJF catalog in context, audience filter, and step 7
  `Revisar e confirmar` ("Review and confirm").

## Implemented

- [x] Dialog header with title and closing action.
- [x] IBJJF catalog in context and class/plan filters.
- [x] Consistent padding in desktop/mobile modal.
- [x] Step 7 review before submission.

## Final status

**Completed** — documentation state reconciled by PRD-145 on 2026-07-13.
