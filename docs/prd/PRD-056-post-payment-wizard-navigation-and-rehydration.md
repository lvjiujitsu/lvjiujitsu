# PRD-056: Post-payment wizard — blocking backward navigation and rehydrating classes

## Summary of the implementation

Two bugs in the public registration wizard (`/register/`), confirmed after validation in the HG environment:

1. **Navigation bug**: after the tuition payment, the `Voltar` (`Back`) button remains active and lets the user return to the class selection step, where the class appears unchecked.
2. **Rehydration bug**: when `sessionStorage` is cleared (which happens on entering `showPlanPaidMode`), `state.classSelections` is not restored from the Django form's initial data, causing a visual "unchecked class" and blocking navigation if the user manages to reach the classes step.

## Demand type

Bug fix (two bugs related to the wizard's post-payment state)

## Current problem

### Bug 1 — The Back button active after payment

In `showPlanPaidMode()` (register.js ~line 2842):
```javascript
if (back) {
  back.style.visibility = 'visible';  // visible button
  if (backLabel) backLabel.textContent = 'Voltar';
  back.onclick = null;                // no override — the addEventListener listener remains active
}
```

With `back.onclick = null`, the listener registered through `addEventListener` (line ~2043) stays active. That listener navigates to the sequence's previous step. Since `state.stepIndex` points to `step-plan` (not to 0), the navigation happens and the user returns to the classes step.

### Bug 2 — state.classSelections not restored

When `regPostPlan = true`, init calls:
```javascript
clearWizardState();   // remove lv-wiz-v1 from sessionStorage
showPlanPaidMode();
```

If the user manages to reach the classes step (through Bug 1), `tryRestoreWizard()` finds nothing in sessionStorage. The init fallback (line ~2992) restores only the profile and the dependent count — it never restores `state.classSelections` from the `<input name="holder_class_groups">` elements Django rendered through `initial`.

## Goal

- Prevent the user from returning to previous steps after the tuition payment is confirmed
- Ensure that, when init loads with no sessionStorage, `state.classSelections` is populated with the class data already present in the Django form's hidden inputs

## Context Ledger

### Files read in full
- `static/system/js/auth/register.js` (complete — v30)
- `system/views/auth_views.py` (complete)
- `system/models/pre_registration.py`

### Adjacent files consulted
- `templates/login/register.html` (the asset versions)
- `system/models/plan.py`

### The HG database inspected
```
PreRegistration #2
  status: payment_confirmed
  holder_class_groups: ['1::Jiu Jitsu']
  plan_paid: True
```
The data is correct in the database — the bugs are exclusively frontend JavaScript state.

### Limitations found
- None

## Scope

- `static/system/js/auth/register.js` — two behavior fixes
- `templates/login/register.html` — a version bump `?v=30` → `?v=31`

## Out of scope

- Restoring `student_class_groups` / `guardian` (there is no validated test case; it can be done in a separate PRD if reproduced)
- Any backend, model, or migration change

## Rules and constraints

- no migrations
- no hardcoding
- no file creation in new folders
- full reading done before the implementation

## Plan

- [x] 1. Full reading of the relevant files
- [ ] 2. Implement Fix 1: hide the Back button in `showPlanPaidMode()`
- [ ] 3. Implement Fix 2: restore `state.classSelections` in the init fallback
- [ ] 4. Version bump in the template (`?v=31`)
- [ ] 5. `manage.py check`
- [ ] 6. `collectstatic --noinput`
- [ ] 7. Visual validation in Chrome (HG after the redeploy)
- [ ] 8. Documentation update

## Acceptance criteria

- [ ] After the tuition payment, the `Voltar` (`Back`) button is hidden — the user can only advance to materials or restart the registration
- [ ] On reloading `/register/` with no sessionStorage but with a pre-registration in the session, the previously selected class appears checked in the classes step
- [ ] The complete flow (materials → summary → finish) works normally after the payment

## Expected evidence

- The Chrome console with no JavaScript errors
- A database snapshot with `holder_class_groups` populated
- The classes step shows the selected class when rehydrated

## Implemented

*(fill in after implementation)*

## Deviations from plan

*(fill in when there are any)*

## Pending

*(fill in when there are any)*
