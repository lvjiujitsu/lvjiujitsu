# PRD-120: The dependent in a modal on the home

## Summary
Fix the authenticated add-a-dependent flow so it works as a popup/modal over the home, and not as a standalone screen at `/dependents/add/`.

## Demand type
A UX and authenticated visual flow fix with impact on Django MVT, the template, the CSS, the JS, and the tests.

## Current problem
- The `Adicionar dependente` ("Add dependent") action takes the user to `/dependents/add/`, creating a separate surface.
- The user expects a popup/modal from the home, following the pattern of the other short operational flows.
- After a dependent's pre-registration payment, the return also sends the user to `/dependents/add/`, keeping the full-screen behavior.

## Goal
The user starts, continues, and completes the dependent registration as a modal opened over the home. The `/dependents/add/` route becomes the modal's content when called with `?modal=1`; direct access redirects to `/home/?dependent_modal=1`.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-118-add-dependent-after-enrollment.md`
- `docs/prd/PRD-119-dependent-material-idempotency-and-cpf.md`
- `system/views/home_views.py`
- `system/views/dependent_views.py`
- `system/views/payment_views.py`
- `system/urls.py`
- `templates/dependents/dependent_registration.html`
- `static/system/css/dependents/dependent_registration.css`
- `static/system/js/home/dashboard.js`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`

### Internet / official documentation
- Django 5.2 class-based views and test client: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/ and https://docs.djangoproject.com/en/5.2/topics/testing/tools/
  - Conclusion: the view can distinguish the modal variant through the query string and the tests can cover a `GET` with parameters.
- MDN `HTMLDialogElement.showModal()`: https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal
  - Conclusion: `showModal()` displays the dialog in the top layer, makes the rest of the document inert, and blocks background interaction.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: consulted for `TemplateView`, `get_context_data`, and `Client.get(..., query_params=...)`.
- PowerShell and `rg`: working.

### Limitations found
- The current home already uses modals through a custom overlay, but the fix will use `<dialog>` for the new modal because it is native and suitable for a long-form popup.
- A real external payment is not part of this fix; the validation covers the local redirect that reopens the modal.
- The internal browser had failed in PRD-119; in this PRD the validation must be attempted again and recorded.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The current request says "it should be a popup, not a screen, fix it". That authorizes implementing the visual and functional fix of the dependent flow into a modal on the home.

## Execution prompt
### Persona
A senior Django/MVT agent for LV JIU JITSU, with TDD and visual validation in the internal browser.

### Action
Turn the add-a-dependent experience into a modal over the home, preserving the already-implemented server-side validation, payments, and completion.

### Context
PRD-118 created `/dependents/add/` as an authenticated wizard. PRD-119 added the materials, the idempotency, and the pending CPF. The current behavior fulfills the business rule but violates the UX expectation: it should open as a popup.

### Constraints
- Do not remove or rewrite the `DependentRegistrationForm` and services logic.
- Do not create the person before the already-implemented payments/conditions.
- Do not move validation into the JS.
- Do not edit `staticfiles/`.
- Update the `?v=` of any changed assets.
- Direct access to `/dependents/add/` must not leave the user on a standalone screen.

### Acceptance criteria
- [x] The home renders the add-a-dependent modal with an iframe or a loadable body.
- [x] The `Adicionar dependente` ("Add dependent") buttons/links on the home open the modal, they do not navigate to a standalone screen when JS is active.
- [x] `/dependents/add/?modal=1` renders the wizard in modal mode.
- [x] An authenticated `/dependents/add/` redirects to `/home/?dependent_modal=1`.
- [x] `/home/?dependent_modal=1` opens the modal automatically.
- [x] An invalid POST in modal mode re-renders the errors inside the modal.
- [x] A completed POST in modal mode signals the completion to the home and reloads the home.
- [x] The dependent's payment return redirects to the home with the modal open.
- [x] The modal closes through the button, the backdrop, and Esc.
- [x] The focused tests cover the home/modal, the direct route, the modal variant, and the payment return.
- [x] The internal browser validates desktop/mobile, the light/dark theme, and a console with no critical error.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1`
- `.\.venv\Scripts\python.exe manage.py check`
- `node --check` on the changed/created JS.
- The internal browser at `/home/` and `/home/?dependent_modal=1`.

### Output format
A summary of the fix, the real evidence, the visual validation, the limitations, and the status.

## Scope
- Adjust the home to open the dependent modal.
- Adjust the dependent view/template for the modal variant.
- Adjust the dependent's payment return to reopen the modal on the home.
- Create the minimum JS to open/close the modal and receive the iframe's completion.
- Update the focused tests and the PRD.

## Out of scope
- Redesigning the whole dependent wizard.
- Switching the gateway or simulating a real payment.
- Rewriting the whole home.
- Creating a shared CRUD foundation.

## Impacted files
| File | Expected change |
|---|---|
| `system/views/home_views.py` | The URLs and the flag for the open modal |
| `system/views/dependent_views.py` | The direct-access redirect and the modal completion response |
| `system/views/payment_views.py` | The payment return to the home with the modal |
| `templates/home/dashboard.html` | The dependent modal and the opening links |
| `templates/dependents/dependent_registration.html` | The modal variant |
| `templates/dependents/dependent_registration_done.html` | The success signal to the parent |
| `static/system/js/home/dashboard.js` | Opening/closing the modal and postMessage |
| `static/system/js/dependents/dependent_registration.js` | Closing the frame and signaling the submit |
| `static/system/js/dependents/dependent_registration_done.js` | Notifying the completion |
| `static/system/css/home/dashboard.css` | The modal's layout |
| `static/system/css/dependents/dependent_registration.css` | The modal compaction |
| `system/tests/test_home_dependents_section.py` | The home/modal contract |
| `system/tests/test_dependent_registration.py` | The modal route's contract |
| `docs/prd/README.md` | The index |

## Risks and edge cases
- If the modal completes and the home does not reload, the newly created dependent does not appear.
- If an external payment returns into the iframe, it could load the home inside the iframe; the local return prioritizes a top-level home with the modal.
- A user without JS can still access `?modal=1`; the server-side rule and the permissions remain.
- The backdrop/Esc must not lose data accidentally without intent; a manual close only closes the modal, without erasing the draft in the session.

## Rules and constraints
- The new modal uses `<dialog>` and `showModal()`.
- The iframe loads only a same-origin route.
- The iframe-parent communication uses `postMessage` with origin validation.
- No `innerHTML` with user data.
- CSS through tokens, with no `staticfiles/`.

## Plan
- [x] 1. Create PRD-120.
- [x] 2. Write the Red tests.
- [x] 3. Implement the view/context/modal template.
- [x] 4. Implement the JS/CSS.
- [x] 5. Run the tests/check/node.
- [x] 6. Validate in the internal browser.
- [x] 7. Audit the diff and update the PRD.

## Test plan
### Tests to author
- `test_student_without_dependents_can_start_dependent_registration_in_modal`
- `test_home_query_opens_dependent_modal`
- `test_direct_authenticated_get_redirects_to_home_modal`
- `test_modal_get_renders_wizard_content`
- `test_modal_family_plan_completion_returns_modal_done`
- Update the payment return to expect `/home/?dependent_modal=1`.

### Execution authorization
Authorized by the current request. A real external payment is out of scope.

### Execution evidence
- The initial Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1` failed at 7 expected points: the home with no modal, the direct route with no redirect, the payments returning to `/dependents/add/`, and the wizard with no modal variant.
- An additional iframe Red: `test_product_catalog_renders_in_dependent_wizard` failed with `X-Frame-Options: DENY`; fixed to `SAMEORIGIN`.
- The final Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1` -> 17 tests OK.
- The full regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` -> 450 tests OK.
- `.\.venv\Scripts\python.exe manage.py check` -> no issues.
- `node --check static\system\js\home\dashboard.js` -> OK.
- `node --check static\system\js\dependents\dependent_registration.js` -> OK.
- `node --check static\system\js\dependents\dependent_registration_done.js` -> OK.

## Visual hierarchy
- The home stays the main surface.
- The modal occupies a large operational width, centered, with a compact title and a close button.
- The wizard inside the iframe loses its standalone-page appearance and becomes compact.
- The `Adicionar dependente` ("Add dependent") action stays in the section's header and in the empty state.

## Wireframe
### Region: Home / Dependents section
- The `Dependentes` ("Dependents") or `Meus dependentes` ("My dependents") header.
- The `Adicionar dependente` ("Add dependent") button with the modal-opening class.
- The empty state with a primary button opening the same modal.

### Region: The modal
- A `<dialog>` with a header:
  - Eyebrow: `Dependentes` ("Dependents")
  - Title: `Adicionar dependente` ("Add dependent")
  - An icon close button.
- The body:
  - A same-origin iframe for `/dependents/add/?modal=1`.
- The states:
  - Loading: the iframe empty/loading.
  - Editing: the wizard visible.
  - Error: the per-field errors inside the iframe.
  - Success: the iframe sends `dependent-modal-done`; the parent closes and reloads.

## State machine
### The dependent modal
- `closed` -> `open`
- `open` -> `submitting`
- `submitting` -> `error`
- `submitting` -> `done`
- `done` -> `reload_home`
- `open` -> `closed`

## Visual validation
- [x] Desktop `/home/` opens the modal.
- [x] Mobile `/home/` opens the modal with no horizontal overflow.
- [x] `/home/?dependent_modal=1` opens the modal automatically.
- [x] The light theme.
- [x] The dark theme.
- [x] A console with no critical error.

## ORM validation
- There is no schema change or new persistence in this PRD.

## Quality validation
- [x] The focused tests.
- [x] `manage.py check`.
- [x] `node --check`.
- [x] The diff reviewed.

## Evidence
- The internal browser at `http://127.0.0.1:8000/dependents/add/`: it redirected to `http://127.0.0.1:8000/home/?dependent_modal=1`, with `title = "Início — LV Jiu Jitsu"`, `modalOpen = true`, `isStandaloneDependentPage = false`, the `/dependents/add/?modal=1` iframe, the wizard present, and no connection-refused error.
- The internal browser at `http://127.0.0.1:8000/home/?dependent_modal=1`: the modal opened automatically, the iframe loaded `Dados pessoais` ("Personal data"), `Condição financeira` ("Financial condition"), and `Materiais opcionais` ("Optional materials").
- The desktop layout 1280x900: the modal 1040x820 within the viewport, with no horizontal overflow.
- The mobile layout 390x844: the modal within the viewport, with no horizontal overflow.
- The initial dark theme and the light theme after the toggle: the modal kept opening with the wizard.
- The internal browser's console after a clean navigation: `errorLogs = []`.
- The closing validated through the button, the backdrop, and Esc inside the iframe's form.

## Implemented
- The home renders `<dialog id="dependent-registration-modal">` and `js-open-dependent-modal` links to `/dependents/add/?modal=1`.
- `DependentRegistrationView` redirects a direct GET to `/home/?dependent_modal=1`, renders modal mode with `?modal=1`, returns a completion page to the iframe, and allows `SAMEORIGIN` framing.
- The dependent's pre-registration payment return reopens the home with the modal.
- The home's JS opens/closes the modal, clears the query state, validates `postMessage` by origin, and reloads the home on completion.
- The iframe's JS closes through the buttons/Esc and signals the completion.
- The home's and the wizard's CSS adjusted for a responsive modal.

## Cleanup findings
- The iframe error blocked by `X-Frame-Options: DENY` was identified only during the visual validation and is covered by a test.
- The workspace already contained previous changes in shared home/registration files; they were preserved.
- No edit to `staticfiles/`.

## Follow-up PRDs
No follow-up opened in this PRD.

## Deviations from plan
- The implementation had to add `xframe_options_sameorigin` to the modal view to allow the same-origin iframe.

## Pending
No known pending items in this PRD's scope.

## Final status
Completed.
