# PRD-019: Standardize the plan change screen with the registration `plan-selector` pattern

## Summary of the implementation
Rewrite the plan change screen (`/plan-change/`) reusing the same visual pattern as the `Escolha seu plano` (`Choose your plan`) step of the registration wizard: filter chips (audience, type, frequency, recurrence) + PIX/Card cards side by side + a highlighted summary. The summary now shows the calculation of the selected change (credit, prorated cost, and net difference). The intermediate `plan_change_confirm.html` screen is eliminated — the POST to `plan-change-select` itself applies the change (downgrade/free) or creates the order and redirects to `payment-checkout` (upgrade).

## Demand type
Visual refactoring / UX standardization (no business rule or schema change).

## Current problem
Even after PRD-006, the `plan_change_select.html` screen remains visually divergent from the registration screen:

- the registration screen uses horizontal chips per dimension (audience, type, frequency, cycle) + PIX and Card cards side by side + a highlighted summary;
- the plan change screen uses a grouped vertical list (`catalog-cluster-card` + `record-card-catalog`) with proration collapsed in `<details>`;

The user ("the plan change screen is off-pattern") wants to see the same layout on both screens, with the calculation of the selected change visible in the selection summary. Keeping two patterns for the same operation ("choose a plan") is a source of inconsistency and confusion.

## Goal
- Reuse exactly the `.plan-selector-*` pattern of the registration wizard on the plan change screen.
- Show the prorated credit, prorated cost, and net difference in the summary, updated when the filter / method changes.
- Eliminate the intermediate confirmation screen (`plan_change_confirm.html`) — the flow becomes: select plan → submit → the backend applies the change (free) or redirects to the checkout (upgrade).
- Extract the `plan-selector` styles into shared CSS, avoiding future visual drift.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `MEMORY.md` (auto-memory root)
- `templates/billing/plan_change_select.html`
- `templates/billing/plan_change_confirm.html`
- `templates/login/register.html` (the `plan` step — lines 740–840)
- `templates/base.html`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/services/registration_checkout.py`
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/tests/test_views.py` (the `PlanChangeSelectViewGroupingTest` class, lines 1993–2110)
- `static/system/css/billing/billing.css`
- `static/system/css/auth/login.css` (the `plan-selector*` block, lines 2575–2760)
- `static/system/js/auth/registration-wizard-clean.js` (`renderPlanList`, `buildPlanSelectorRow`, `buildPlanSelectorPaymentCard`, `buildPlanSelectorSummary`, lines 2150–2470)
- `docs/prd/PRD-006-standardize-plan-change-screen-with-portal-design-system.md`

### Adjacent files consulted
- `system/urls.py` — the `plan-change-select`, `plan-change-confirm`, `payment-checkout` routes
- `system/views/__init__.py` — exports
- `templates/home/student/dashboard.html` — calls to `plan-change-select`
- `static/system/js/auth/registration-wizard-clean.js` — `pixIconUrl`/`cardIconUrl` come from `data-pix-icon-url`/`data-card-icon-url` on the form

### Internet / official documentation
- Not applicable: a visual refactoring reusing a pattern already established in the project.

### MCPs / tools verified
- PowerShell shell — ok — reading, editing, execution
- Playwright / browser MCP — mandatory for visual validation (registration must stay identical after moving the CSS; the new plan change screen needs validating)

### Limitations found
- The number `019` is the next free one in `docs/prd/`, even though there were earlier collisions (duplicate PRD-008, 015, 016). Reorganizing the numbering is not in the scope of this PRD.

## Execution prompt
### Persona
Django + server-rendered frontend development agent following SDD + TDD + Clean Code.

### Action
Rewrite the plan change screen to reuse the registration `plan-selector` pattern, showing the calculation of the selected change in the summary and eliminating the intermediate confirmation screen.

### Context
The `PlanChangeSelectView` view already computes proration for every eligible plan. The registration wizard already implements the desired visual pattern in JavaScript (`registration-wizard-clean.js`). The `.plan-selector-*` CSS lives today in `static/system/css/auth/login.css`. We will extract that CSS into `static/system/css/shared/plan-selector.css`, create JavaScript specific to the plan change in `static/system/js/billing/plan-change-selector.js`, rewrite the plan change template to use the same pattern, and add a change-calculation panel to the summary. The view now accepts a POST with `selected_plan` and applies the change directly (no intermediate confirmation screen).

### Constraints
- no hardcoded business rules
- no error masking
- no migrations
- mandatory full reading (already done)
- mandatory in-browser visual validation (registration + plan change)
- Brazilian Portuguese interface
- preserve the already-tested behavior of `calculate_plan_change` and `apply_plan_change`/`create_plan_change_order`

### Acceptance criteria
- [ ] `/plan-change/` loads with a `plan-selector` layout identical to the plan step of registration (chips + PIX/Card cards + summary) — verifiable by visual inspection.
- [ ] Selecting PIX or Card, the summary shows the name, cycle, full amount, and the change calculation: credit (R$), prorated cost (R$), and difference/saving (R$) — verifiable by test and visually.
- [ ] When the selected plan is free or a downgrade (`net_amount <= 0`), the CTA button is `Confirmar troca` (`Confirm change`); when it is an upgrade, it is `Confirmar e pagar` (`Confirm and pay`) — verifiable by test and visually.
- [ ] A POST to `/plan-change/` with a valid `selected_plan=<id>` applies a direct change (free/downgrade) and redirects to `student-home` with a success message — verifiable by test.
- [ ] A POST to `/plan-change/` with a valid upgrade `selected_plan=<id>` creates a `RegistrationOrder` and redirects to `payment-checkout` — verifiable by test.
- [ ] The `plan_change_confirm.html` screen and the `plan-change-confirm` route cease to exist — verifiable by inspection and by `manage.py check`.
- [ ] The `.plan-selector-*` CSS moved to `static/system/css/shared/plan-selector.css`; registration stays visually identical — verifiable by visual validation of the registration plan step.
- [ ] Specific JavaScript in `static/system/js/billing/plan-change-selector.js` loaded only on the plan change screen — verifiable by inspecting the template.
- [ ] `?v=` updated on the files whose content changed — verifiable by inspection.
- [ ] `manage.py test --verbosity 2` passes with no failures — verifiable in the terminal.
- [ ] `manage.py check` with no errors — verifiable in the terminal.
- [ ] Clean browser console on both screens — verifiable in DevTools.

### Expected evidence
- output of `manage.py test --verbosity 2` with 0 failures
- output of `manage.py check` with no errors
- screenshot/visual description of both screens after the change
- browser console with no errors
- terminal with no stack traces

### Output format
Code (view + template + JS + shared CSS) + tests + evidence.

## Scope
- `system/views/plan_change_views.py`: replace `PlanChangeSelectView` with a `View` that serves `GET` (renders the template with a JSON payload) and `POST` (applies the change / creates the order). Remove `PlanChangeConfirmView`.
- `system/urls.py`: remove the `plan-change-confirm` route. Keep `plan-change-select` (only).
- `system/views/__init__.py`: adjust the exports.
- `templates/billing/plan_change_select.html`: full rewrite using the `plan-selector` pattern.
- `templates/billing/plan_change_confirm.html`: **delete**.
- `static/system/css/shared/plan-selector.css`: a new file with the `plan-selector*` styles and additions for the change-calculation panel.
- `static/system/css/auth/login.css`: remove the `plan-selector*` block (it now comes from `shared/`).
- `templates/login/register.html`: include `shared/plan-selector.css` before `auth/login.css`.
- `static/system/css/billing/billing.css`: remove the now-obsolete rules (`.plan-change-grid`, `.plan-change-card*`, `.plan-change-action-row`, `.plan-change-net*`); keep `.plan-change-badge*` if it is used in another context (to check). Bump `?v=`.
- `static/system/js/billing/plan-change-selector.js`: a new file containing only the plan-selector rendering + the calculation panel, receiving data through `data-` attributes.
- `system/tests/test_views.py`: replace `PlanChangeSelectViewGroupingTest` with `PlanChangeSelectViewTest` covering:
  - GET returns 200 and injects `plan_catalog_json` (a list) with each item containing proration
  - GET returns `membership` in the context
  - POST with a free/downgrade plan applies the change and redirects to `student-home`
  - POST with an upgrade plan creates the order and redirects to `payment-checkout`
  - POST with a missing/invalid `selected_plan` redirects with an error message
  - unauthenticated access is redirected.

## Out of scope
- Changes to the proration calculation (`system/services/plan_change.py`).
- Changes to `apply_plan_change` / `create_plan_change_order`.
- Changes to the subsequent checkout/payment flow.
- Changes to plan eligibility (`plan_eligibility.py`).
- Visual changes to the `Escolha seu plano` (`Choose your plan`) registration step beyond what is needed to move the CSS.

## Impacted files
| File | Type of change |
|---|---|
| `system/views/plan_change_views.py` | rewrite: single GET + POST; removal of `PlanChangeConfirmView` |
| `system/urls.py` | remove the `plan-change-confirm` route |
| `system/views/__init__.py` | remove the `PlanChangeConfirmView` export |
| `templates/billing/plan_change_select.html` | full rewrite |
| `templates/billing/plan_change_confirm.html` | **delete** |
| `templates/login/register.html` | add a `<link>` to `shared/plan-selector.css` |
| `static/system/css/shared/plan-selector.css` | **new** |
| `static/system/css/auth/login.css` | remove the `plan-selector*` block |
| `static/system/css/billing/billing.css` | remove obsolete rules; bump `?v=` |
| `static/system/js/billing/plan-change-selector.js` | **new** |
| `system/tests/test_views.py` | replace `PlanChangeSelectViewGroupingTest` |

## Risks and edge cases
- Visual breakage on the registration screen when moving the CSS — mitigation: validate visually after the move.
- If the user has lost `request.portal_person` or `membership`, GET returns to the home with a message (current behavior preserved).
- A plan with `requires_special_authorization` keeps being filtered by eligibility (preserved).
- If the catalog JSON ends up empty (e.g. no plan eligible for a change), the screen shows an empty state identical to registration's (`Nenhum plano disponível…` — `No plan available…`).
- POST with a non-existent `selected_plan`: a 404 when looking up `SubscriptionPlan` results in an error message and a redirect.
- Decimal serialized to JSON: use `str(value)` (same as `get_plan_catalog_payload`).

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts: define the catalog's JSON format (plan + proration)
- [x] 3. Tests (Red): replace `PlanChangeSelectViewGroupingTest`
- [x] 4. Implementation (Green): view + template + JS + shared CSS
- [x] 5. Refactoring (Refactor): clean up billing.css, update `?v=`
- [x] 6. Full validation: test/check/collectstatic + desktop/mobile visual
- [x] 7. Final cleanup
- [x] 8. Documentation update (this PRD)

## Visual validation
### Desktop
- The registration plan step stays identical.
- The plan change screen shows chips + PIX/Card cards side by side + a summary with the change calculation.

### Mobile
- Single-column layout; PIX/Card cards stacked (the existing `@media max-width: 360px`).

### Browser console
- No critical JavaScript errors on either screen.

### Terminal
- No stack trace when navigating either flow.

## ORM validation
### Database
- No schema change.

### Shell checks
- `SubscriptionPlan.objects.filter(is_active=True).exclude(requires_special_authorization=True).count()` returns the expected list.
- `Membership.objects.filter(status="active")` remains queryable.

### Flow integrity
- After a free POST: membership.plan switched, status preserved.
- After an upgrade POST: a `RegistrationOrder` created with `is_plan_change=True` and `total = net`.

## Quality validation
### No hardcoding
- The catalog is generated through the existing selector; icons through `data-*-icon-url`.
### No brittle conditional structures
- The logic stays in the service; the view is thin; the JavaScript is structured into functions.
### No `except: pass`
- `PlanChangeError` handling still uses `continue` (preserved).
### No error masking
- Explicit error messages through `messages.error`.
### No unnecessary comments or docstrings
- Do not add any.

## Evidence
- `manage.py check`: `System check identified no issues (0 silenced).`
- `manage.py test --verbosity 1` (full suite): `Ran 341 tests in 66.893s — OK`
- `manage.py test system.tests.test_views.PlanChangeSelectViewTest --verbosity 2`: `Ran 12 tests in 1.841s — OK`
  - `test_unauthenticated_access_redirected` ok
  - `test_get_renders_membership_in_context` ok
  - `test_get_template_carries_plan_catalog_script_and_icons` ok
  - `test_get_plan_catalog_excludes_current_plan` ok
  - `test_get_plan_catalog_serializes_amounts_as_strings_with_proration` ok
  - `test_get_plan_catalog_marks_upgrade_and_downgrade_correctly` ok
  - `test_post_with_upgrade_creates_order_and_redirects_to_checkout` ok
  - `test_post_with_downgrade_applies_change_and_redirects_home` ok
  - `test_post_without_selected_plan_redirects_with_error` ok
  - `test_post_with_same_plan_redirects_with_error` ok
  - `test_post_with_inactive_plan_returns_404` ok
  - `test_confirm_route_was_removed` ok (NoReverseMatch for `plan-change-confirm`)
- `manage.py collectstatic --noinput`: `167 static files copied`
- HTTP probes: `/plan-change/` 302 → login (no session); `/register/` 200; the new assets `shared/plan-selector.css` and `js/billing/plan-change-selector.js` 200
- In-browser visual validation (Preview MCP, portal session authenticated as the "teste" persona):
  - Desktop: chips (Frequency, Recurrence) + PIX/Card cards side by side + a summary with name, cycle, full amount, and the change calculation (Credit, Cost, Difference/Saving). Selecting PIX (downgrade) → CTA `Confirmar troca` (`Confirm change`), net = `Grátis` (`Free`) (green). Selecting Annual Card (upgrade) → CTA `Confirmar e pagar` (`Confirm and pay`), net = R$ 12.88 (orange).
  - Mobile (375x812): responsive grid, cards side by side, readable breakdown, full-width CTA.
  - Clean console at both resolutions (`No console logs` at level=error).
  - Registration (`/register/`) loading `shared/plan-selector.css` before `auth/login.css`; the computed style of `.plan-selector-chip` preserved (border-radius 999px, padding 8px 14px, font-weight 600).

## Implemented
- `system/views/plan_change_views.py`: rewritten; `PlanChangeSelectView` now accepts GET (renders the serialized catalog with proration) and POST (applies a direct change for free/downgrade or creates a `RegistrationOrder` for an upgrade and redirects to `payment-checkout`). `PlanChangeConfirmView` removed. Local helpers `_serialize_plan_with_proration` and `_build_plan_catalog`.
- `system/urls.py`: the `plan-change-confirm` route removed.
- `system/views/__init__.py`: the `PlanChangeConfirmView` export removed.
- `templates/billing/plan_change_select.html`: rewritten using `plan-selector` + `json_script` for the catalog, `data-pix-icon-url` / `data-card-icon-url` on the form, and a dynamic CTA (`Confirmar troca` / `Confirmar e pagar` — `Confirm change` / `Confirm and pay`) through JavaScript. Includes the new `?v=20260509a` for `shared/plan-selector.css` and `billing/billing.css`.
- `templates/billing/plan_change_confirm.html`: deleted.
- `templates/login/register.html`: now includes a `<link>` to `shared/plan-selector.css` before `auth/login.css` (`?v=20260509a` on both).
- `static/system/css/shared/plan-selector.css`: created from the block extracted out of `auth/login.css`, with additions for the `plan-selector-summary-breakdown` panel (credit, cost, and a net value colored per scenario).
- `static/system/css/auth/login.css`: the `.plan-selector-*` block removed (now loaded through shared).
- `static/system/css/billing/billing.css`: obsolete rules (`.plan-change-grid`, `.plan-change-card*`, `.plan-change-action-row`, `.plan-change-net*`, `.plan-change-badge*`, `.proration-breakdown`, `.proration-total`) removed. `.plan-change-cta-row` and `.plan-change-empty` added.
- `static/system/js/billing/plan-change-selector.js`: a new IIFE module that reads the catalog JSON, renders the filter chips (audience/type/frequency/recurrence) + PIX/Card cards + a summary with the change calculation, and syncs `#selected-plan` and the form's CTA.
- `system/tests/test_views.py`: `PlanChangeSelectViewGroupingTest` replaced by `PlanChangeSelectViewTest` with 12 tests covering GET, POST (upgrade/downgrade/no plan/same plan/inactive), catalog serialization, and removal of the old route.
- `.claude/launch.json`: created to support visual validation through Preview MCP (a "django" config pointing to `runserver 127.0.0.1:8000`).

## Deviations from plan
- The `shared/plan-selector.css` stylesheet is loaded **before** `auth/login.css` in `register.html` to preserve the intended cascade precedence (the shared styles as the base; auth.css may override in the future if needed). No visual impact today — validated by inspection and screenshot.
- **Post visual validation** (after the initial screenshots): two bugs identified by the user and fixed:
  1. **Selected chips illegible in the dark theme**: the shared CSS used `var(--panel-strong)` (a token defined only in `auth/login.css`); on the plan change screen, which inherits only `portal/portal.css`, the token stayed `unset` and `color` was inherited from the parent, matching the selected chip's background color. Fix: `shared/plan-selector.css` now uses `var(--panel-solid)` (a token defined in `portal/portal.css`); since `auth/login.css` still uses `--panel-strong` in 32 other places, `--panel-solid` was added alongside `--panel-strong` in both `:root` blocks of `auth/login.css` (an alias with the same value).
  2. **CTA button stretched vertically on mobile**: `.plan-change-cta-row .btn { flex: 1 1 220px }` combined with `flex-direction: column` in the media query made `flex-grow: 1` operate on the vertical axis. Fix: in the mobile media query it was redefined to `flex: 0 0 auto`, keeping `width: 100%` and a natural height (`min-height: 44px`).
  - `?v=` bumped to `20260509c` in `plan_change_select.html` and `register.html` to invalidate caches.
  - Desktop + mobile re-validation after the fix confirmed: legible chips (bg `#f5f7fa` / color `#14161b` in dark) and mobile buttons at 44px height and 321px width (full-width with no stretch).

## Pending
- None. Desktop and mobile visual validation completed through Preview MCP with an authenticated portal session; all tests and checks passing.
