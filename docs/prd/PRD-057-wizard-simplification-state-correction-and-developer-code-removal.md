# PRD-057: Wizard simplification — state fixes and removal of development code

## Summary of the implementation

Fix the bug that shows multiple steps at once in the registration wizard, remove the development code added in commit `00c39f8` (DevLoadPreRegistrationView + the command + the autofill JavaScript), and review the `Recomeçar cadastro` (`Restart registration`) mechanism.

## Demand type

Targeted fix + code cleanup

## Current problem

### A critical visual bug (from the user's screenshot)

`step-profile` and `step-plan` are displayed at the same time after returning from Asaas with `post_plan_payment_complete=True`.

**Root cause:**
- `step-profile` has no `hidden` attribute in the template — it is visible by default
- `showPlanPaidMode()` hides only the steps present in `state.stepSequence`
- `state.stepSequence` is empty when the profile was not restored (e.g. the PreRegistration was deleted after a database reset)
- Result: a `forEach` over an empty array → no step is hidden → `step-profile` stays visible alongside `step-plan`

**The same bug exists in:**
- `showPostPaymentMode()` — the Back button handler in `step-plan-confirmed`

### Development code that adds complexity with no value

Added in commit `00c39f8`:
- `DevLoadPreRegistrationView` in `system/views/auth_views.py`
- The `/dev/carregar-pre-cadastro/<id>/` route in `system/urls.py`
- `system/management/commands/dev_create_test_pre_registration.py`
- `static/system/js/auth/register_test_autofill.js`

### `/register/recomecar/` returns 400 in production (HG)

The exact cause cannot be identified without server logs. The endpoint is simple (`session.pop` + redirect), but it returns 400. Switching to `session.flush()` is semantically more robust.

## Goal

1. Fix the overlapping-steps bug with 1 line of change per occurrence
2. Remove the development code added in `00c39f8`
3. Make `ResetRegistrationView` more robust with `session.flush()`
4. Validate locally before any deploy

## Registration flow — an immutable contract

```
Create account → Data steps (profile, personal data, dependents, health, martial arts, classes)
→ Plan payment (Asaas — data persisted in PreRegistration)
→ Return with payment confirmed
→ Materials (pay or skip)
→ Summary
→ Finish (writes Person, PortalAccount, etc.)
```

Rules:
- The user may go back at any moment, with the data preserved in the session/PreRegistration
- A `Person` is never created before the finalization POST
- No step may skip the Summary

## Context Ledger

### Files read in full
- `static/system/js/auth/register.js` (3049 lines, v33)
- `templates/login/register.html`
- `system/views/auth_views.py` (ResetRegistrationView, DevLoadPreRegistrationView, PortalRegisterView)
- `system/urls.py`
- `lvjiujitsu/settings.py`
- `system/middleware.py`

### Confirmed root cause

```javascript
// showPlanPaidMode() lines 2751-2753 — BUG
state.stepSequence.forEach(function (sid) {
  var el = document.getElementById(sid);
  if (el) el.hidden = true;  // does not run when stepSequence is empty
});

// showPostPaymentMode() lines 2158-2160 — same bug
state.stepSequence.forEach(function (sid) {
  var sel = document.getElementById(sid);
  if (sel) sel.hidden = true;
});
```

### The template — `step-profile` is visible by default

```html
<section class="wizard-step" id="step-profile" data-step="1">
  <!-- NO hidden attribute — visible when the page loads -->
```

Every other step inside `wizard-form` has `hidden`.

## Scope

- `static/system/js/auth/register.js` — 2 `querySelectorAll` fixes
- `system/views/auth_views.py` — remove `DevLoadPreRegistrationView`, change `ResetRegistrationView`
- `system/urls.py` — remove the dev route
- `system/management/commands/dev_create_test_pre_registration.py` — delete
- `static/system/js/auth/register_test_autofill.js` — delete
- `templates/login/register.html` — bump `?v=34`

## Out of scope

- Refactoring the wizard JavaScript (a larger scope, a separate PRD)
- Changes to the `PreRegistration` model
- A visual redesign

## Plan

- [x] 1. Diagnosis and full reading
- [ ] 2. Fix the bug in `showPlanPaidMode()`
- [ ] 3. Fix the bug in the `showPostPaymentMode()` back handler
- [ ] 4. Remove the development code
- [ ] 5. Robustness in `ResetRegistrationView` with `session.flush()`
- [ ] 6. Bump `?v=34` in the template
- [ ] 7. Local validation: `manage.py check`, `manage.py test`, the server + the browser
- [ ] 8. Evidence

## Acceptance criteria

- [ ] On returning from Asaas with `post_plan_payment_complete=True`, only `step-plan` (in paid mode) must be visible — no other step (verifiable: Chrome MCP at `/register/` with a post-payment session)
- [ ] `Recomeçar cadastro` (`Restart registration`) clears the session and returns to a fresh `/register/` with no 400 error (verifiable: Chrome MCP, a console with no errors)
- [ ] Back navigation on `step-plan-confirmed` shows only `step-plan`, with no visible `step-profile` (verifiable: Chrome MCP)
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 failures
- [ ] The `/dev/carregar-pre-cadastro/` route returns 404 in DEBUG and does not exist in production (removed)
- [ ] `register_test_autofill.js` no longer exists in the repository

## Rules and constraints

- No migrations
- No hardcoding
- No error masking
- Mandatory full reading ✓
- Mandatory local validation before the HG deploy

## Evidence

(to be filled in after implementation)

## Deviations from plan

(to be filled in)
