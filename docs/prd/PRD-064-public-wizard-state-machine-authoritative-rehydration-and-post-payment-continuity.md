# PRD-064: Public wizard — consolidating the state machine, authoritative rehydration, and post-payment continuity

## Summary

Consolidate the public wizard's state machine (`/register/`, `static/system/js/auth/register.js`) to eliminate the class of bugs that PRD-056 and PRD-057 addressed one at a time: an empty `state.stepSequence` and `state.classSelections` after `sessionStorage` is cleared, multiple steps visible at once, and inconsistent backward navigation after payment. It adapts to LV the principle of continuity and return to origin (a multi-step chain that preserves context and returns to the starting point), applied here to the single-page step machine — not to nested modals.

## Demand type

An architectural frontend fix (consolidating the state machine) + UI. No business rule change in the backend.

## Current problem

- `register.js` derives `state.stepSequence` on the client; when `sessionStorage` is cleared (on entering `showPlanPaidMode` or when the `PreRegistration` is removed), the sequence is empty and step visibility stops being reliable.
- `step-profile` is visible by default in the template (with no `hidden`); `showPlanPaidMode()` only hides steps present in `stepSequence`, so with an empty sequence two steps appear together (the root cause of PRD-057).
- `state.classSelections` is not restored from the initial data rendered by Django, showing an "unchecked class" after payment (the root cause of PRD-056).
- PRD-056 and PRD-057 fixed specific symptoms, but the source of truth for the sequence and the selection is still client state, with no authoritative rehydration from the server.
- There is no explicit "exactly one visible step" invariant and no documented post-payment state machine (states: pre-payment, gateway return, paid, materials, review, finalization).

## Goal

1. Make rehydration from the initial data rendered by Django the authoritative source of `stepSequence` and `classSelections` whenever `sessionStorage` is missing or inconsistent.
2. Guarantee the "exactly one visible step" invariant, including when the sequence has not been derived yet (including `step-profile`).
3. Formalize the post-payment state machine and the continuity: on completing/cancelling a step, the user stays in the correct flow with no regression to a paid step.
4. Do not reintroduce the development code removed in PRD-057.
5. Validate through the desktop/mobile UI, a clean console, and the PRD-056/057 scenarios as a regression.

## Context Ledger

### Files read in full

- `static/system/js/auth/register.js` (the `state` structure, sequence derivation, `showPlanPaidMode`, navigation)
- `docs/prd/PRD-056-post-payment-wizard-navigation-and-rehydration.md`
- `docs/prd/PRD-057-wizard-simplification-state-correction-and-developer-code-removal.md`

### Adjacent files consulted

- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/wizard-step-plan-aluno-titular.md`, `docs/wizard-step-plan-aluno-com-dependente.md`, `docs/wizard-step-plan-responsavel-com-aluno.md`
- the wizard's template in `templates/login/` (the steps and the `hidden` attribute)
- `docs/UI-SCREEN-CONTRACT.md`

### Internet / official documentation

- [MDN — Window.sessionStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage)
- [MDN — History API / popstate](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [MDN — hidden attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/hidden)

### Context7 / MCPs / tools verified

- There is no new external library; `register.js` is vanilla JavaScript. Context7 is not mandatory, except for a doubt about a browser API.
- The internal browser available at `http://127.0.0.1:8000` for validation and regression.
- PowerShell, Git, and `rg` available.

### Limitations found

- The post-payment Asaas flow requires a tunnel/HG environment for the real return; the scenarios can be reproduced through the `post_plan_payment_complete` parameter in the local environment as in PRD-056.
- `register.js` is long (3,059 lines); the consolidation must be surgical, without rewriting the wizard.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: consolidate the wizard's state machine and the authoritative rehydration, adapting the continuity principle.
- User approval: an explicit request for complete PRDs for sequential implementation.
- Date: 2026-06-28.

## Execution prompt

### Persona

Frontend engineer responsible for LV's public wizard state machine.

### Action

Make the rehydration authoritative, enforce the single-step invariant, formalize the post-payment machine, and validate the regressions, with an approved UI proposal before the code.

### Context

A single-page wizard in `register.js`, with steps controlled through `hidden` and state in `sessionStorage`. Payment happens before the `Person` is created (PRD-040).

### Constraints

- Do not rewrite the wizard; a surgical change.
- Do not reintroduce development code (DevLoad/autofill).
- Do not change the backend's business rules.
- Update the versioned asset's `?v=` when changing `register.js`.
- UI requires an approved proposal before the code.

### Acceptance criteria

- [ ] With an empty `sessionStorage` and Django data present, `stepSequence` and `classSelections` are rehydrated correctly.
- [x] In any validated state, exactly one step is visible (including `step-profile`).
- [ ] After payment, the user does not regress to an already-paid step and the class appears checked.
- [x] The post-payment state machine documented and reflected in the code.
- [ ] The PRD-056 and PRD-057 scenarios pass as a UI regression.
- [x] No development code reintroduced.

### Expected evidence

- Screenshots of the key states (pre-payment, gateway return, paid, materials, review) on desktop and mobile.
- A console with no errors.
- A surgical diff of `register.js` and the template, with the `?v=` updated.

### Output format

A short summary, the state machine, evidence, limitations, and status.

## Visual hierarchy

- The wizard header with the progress (`wizard-step-current`/`wizard-step-total`).
- A single step card visible at a time.
- Primary actions: Next/Back/Finish according to the state; Back disabled in post-payment states.

## Wireframe

To be defined in the approved design proposal. Reuse the wizard's current layout; the change is in the visibility and navigation behavior, not a visual redesign.

## State machine

States: `profile` → `data/health/martial art/dependents/classes` → `plan` → `gateway-return` → `plan-paid` → `products` → `review` → `finalize`. Backward transitions blocked from `plan-paid`. Each transition guarantees a single visible step and rehydrated state.

## Scope

- `static/system/js/auth/register.js`
- the wizard's template in `templates/login/` (the `hidden` attribute and the step markup)
- the asset version (`?v=`)
- this PRD.

## Out of scope

- A visual redesign of the wizard.
- The payment backend and the creation of a `Person`.
- The materials/coupon steps beyond what the invariant requires.

## Impacted files

- `static/system/js/auth/register.js`
- the wizard's template
- the `?v=` reference in the template that loads the asset
- this PRD.

## Risks and edge cases

- A partial rehydration may check the wrong class if the Django→`classSelections` mapping does not cover every profile (holder, dependent, guardian).
- `popstate`/the browser's physical button may bypass the Back block.
- Sequences with multiple `step-classes`/`step-dep` require a faithful reconstruction.
- A corrupted (partial) `sessionStorage` is worse than an empty one; treat it as inconsistent and rehydrate.

## Rules and constraints

- The smallest correct change; the root cause, not the symptom.
- No central business rule in JavaScript.
- No `innerHTML` with user data.
- Update `?v=`.

## Plan

- [x] Context and research
- [x] An approved UI/state proposal
- [x] Authoritative rehydration from Django
- [x] The single-step invariant
- [x] The post-payment state machine
- [ ] UI validation and the 056/057 regression
- [x] Cleanup audit (no DevLoad)
- [x] Documentation

## Test plan

### Tests to author

- Django tests are limited for client JavaScript; prioritize browser validation. If there is server-side rehydration logic (the initial context), cover the rendered context with a view test.

### Execution authorization

- Status: not authorized in this run. The server-side tests were written, not run, per policy.

### Execution evidence

The test was written, not run, per policy. There is no Red/Green claim.

## Visual validation

- The internal browser at `http://localhost:8000/register/`, desktop `1365x900`: `register.js?v=36`, the sentinel absent, `visibleSteps=["step-profile"]`, progress `1 de 11` (`1 of 11`).
- The internal browser at `http://localhost:8000/register/`, mobile `390x844`: `visibleSteps=["step-profile"]`, `bodyScrollWidth=390`, `viewportWidth=390`, console errors `[]`.
- Desktop/mobile screenshots captured in the internal browser during the validation.
- The real post-payment return was not reproduced because it requires a session with a pre-registration/pending payment; no local mutation was created without authorization.

## ORM validation

Not applicable (no data mutation in this change).

## Quality validation

- `manage.py check`.
- `node --check static/system/js/auth/register.js`.
- A review of the diff and the state machine.
- `git diff --check`.

## Evidence

- `node --check static/system/js/auth/register.js` returned exit code 0.
- `python manage.py check` returned `System check identified no issues (0 silenced).`
- `python -m py_compile system/tests/test_person_delete.py system/tests/test_register_wizard_contract.py` returned exit code 0.
- The internal desktop browser: a single visible step (`step-profile`), the asset `register.js?v=36`, the sentinel absent.
- The internal mobile browser: a single visible step (`step-profile`), no horizontal overflow, and console errors `[]`.
- `system/tests/test_register_wizard_contract.py` created for the template/JavaScript and `pending_person_json` contract, not run per policy.

## Implemented

- `pending_person_json` now includes `class_group_ids` and `class_group_name` for the holder, students/dependents, and additional dependents in the `PreRegistration` snapshot.
- `register.js` gained `showOnlyWizardStep()` and now hides every `.wizard-step` before showing the target.
- `register.js` gained `rehydratePendingWizardState()` to rebuild the profile, count, dependents, and `classSelections` from the Django JSON.
- Initialization with no `sessionStorage` preserves the hidden input snapshot before calling `selectProfile()` and rehydrates the classes of the holder, dependent, guardian, and extras.
- Post-payment states hide the header's Back button to prevent a regression to an already-paid step.
- `templates/login/register.html` removed `SENTINEL_TEST_XZ99` and updated the asset to `register.js?v=36`.

## Cleanup findings

- No `DevLoad`/autofill code was added.
- No payment, plan, or `Person` creation business rule was changed.
- No database mutation was executed.

## Follow-up PRDs

None foreseen.

## Deviations from plan

- The visual validation covered the initial public screen on desktop/mobile, but it did not reproduce a real post-payment session for lack of authorization to create/use a test pre-registration.
- The tests written were not run, per policy.

## Pending

- Authorization to run `system.tests.test_register_wizard_contract`.
- Authorization to create a test pre-registration with an ordinary student and a student with a dependent and validate the post-payment/materials/review return in the browser.

## Final status

**Completed with limitations** — the implementation, the checks, and the initial visual validation are complete; the real post-payment regression and the automated tests remain pending under the authorization policy.
