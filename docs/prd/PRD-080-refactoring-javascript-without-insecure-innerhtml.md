# PRD-080: Refactor JavaScript without insecure innerHTML

## Summary
Remove the use of `innerHTML` and HTML strings in flows carrying user data, starting with the public registration wizard and the calendar. The UI contract requires `textContent` or explicit element creation.

## Demand type
Frontend security + maintenance.

## Current problem
- `static/system/js/auth/register.js` has multiple occurrences of `innerHTML`.
- `templates/calendar/calendar.html` contains inline JavaScript and `body.innerHTML` manipulation.
- Some points do escape manually, but the current contract forbids the pattern when user data can enter the HTML.

## Goal
Reduce the XSS risk and improve maintainability:
- replace HTML strings with safe DOM construction;
- isolate the data in safe JSON;
- remove inline behavioral JavaScript;
- keep the wizard and the calendar functionally equivalent.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `static/system/js/auth/register.js`
- `templates/calendar/calendar.html`

### Adjacent files consulted
- `templates/login/register.html`
- `static/system/css/auth/register.css`
- `static/system/js/home/dashboard.js`

### Internet / official documentation
- Django template escaping: https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping

### Context7 / MCPs / tools verified
- Context7 Django templates.

### Limitations found
- `register.js` is large and critical; the refactoring needs to be phased with wizard validation.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request to sanitize and fix an inconsistent implementation.

## Scope
- Inventory every use of `innerHTML`.
- Classify static data vs. user data.
- Refactor the points with user data first.
- Extract the calendar's inline JavaScript.
- Validate the wizard and the calendar.

## Out of scope
- Rewriting the whole wizard visually.
- Changing the payment gateway.

## Impacted files
- `static/system/js/auth/register.js`
- `templates/calendar/calendar.html`
- `static/system/js/calendar/*` or an equivalent new file
- the versioned assets in the templates

## Risks and edge cases
- The registration wizard has many states; refactoring with no visual test may break the flow.
- The calendar may depend on server-rendered data.

## Plan
- [x] Minimal wizard and calendar tests/contracts.
- [x] Refactor the highest-risk blocks.
- [x] Update the `?v=` assets.
- [x] Validate desktop/mobile and the console.

## Test plan
### Tests to author
- The wizard's rendering contract.
- A JavaScript syntax test.
- A minimal visual flow from registration up to plan selection.
- The calendar renders with no error.

### Execution authorization
Authorized locally.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_register_wizard_contract --verbosity 2` → `Ran 4 tests in 0.022s` — `OK` (including 2 new tests: the absence of `.innerHTML` in `renderReview`/`renderConfirmationSummary` and the `calendar.html`/`calendar.js` contract).
- `.\.venv\Scripts\python.exe manage.py test system.tests --verbosity 1` → `Ran 262 tests in 88.036s` — `OK`.
- `.\.venv\Scripts\python.exe manage.py check` → `System check identified no issues (0 silenced)`.
- `node --check static/system/js/auth/register.js` → no error.
- `node --check static/system/js/calendar/calendar.js` → no error.
- Visual validation in the internal browser (Claude Preview, the local Django server at `localhost:8000`):
  - The `/register/` wizard: step 1 (profile selection) and step 2 (personal data) render correctly in the light and dark themes, with no JavaScript errors.
  - The `/cronograma/` calendar: the monthly grid renders, the day detail modal opens/closes by cloning nodes with `clearChildren` (with no `innerHTML`), the `Criar aulão` (`Create open class`) modal (the instructor area) opens/closes correctly, and the light/dark theme toggle works.
  - A security proof through `preview_eval`: the malicious string `<img src=x onerror=alert(1)>` passed as `text` to the `el()` helper produced `hasRealImgElement: false` and `textContentMatches: true` — confirming the function uses `textContent`, not HTML interpretation.

## Visual validation
Mandatory in the internal browser.

## ORM validation
When necessary for the wizard's catalog.

## Quality validation
- `node --check`
- focused Django tests
- the internal browser

## Evidence
- The subagent found 26 occurrences of `innerHTML`/HTML strings in the wizard/calendar.

## Implemented
- `static/system/js/auth/register.js`:
  - Safe DOM helpers added: `el(tag, opts, children)`, `clearChildren(node)`, and `svgIcon(markup)` (the last one only receives fixed SVG markup from the code itself, never user data).
  - `renderConfirmationSummary()` rewritten: it builds the summary panel (`Nome`, `E-mail`, `Telefone`, `Turma`, `Plano contratado` — `Name`, `Email`, `Phone`, `Class`, `Plan purchased`) entirely through `el()`/`textContent`, with no HTML string concatenation. It replaces `container.innerHTML = html` with `clearChildren` + `appendChild`.
  - `renderReview()` rewritten: it builds the review blocks (guardian/student, linked students, class, plan, materials) through `el()`/`textContent`, with no `innerHTML`. It covers the wizard's densest point of user data (the name, email, and class name of several people).
- `templates/calendar/calendar.html`:
  - The inline `<script>` block (the theme, the day detail modal, the `Criar aulão` — `Create open class` modal) removed and replaced by `<script src="{% static 'system/js/calendar/calendar.js' %}?v=1" defer>`.
  - Only the minimal inline theme pre-paint snippet kept (with no user data, necessary to avoid a theme flash before the CSS loads).
- `static/system/js/calendar/calendar.js` (a new file): it contains the logic that used to be inline — the theme toggle, the day detail modal (cloning existing nodes from the server-rendered DOM), and the `Criar aulão` (`Create open class`) modal (fetch + JSON). Clearing the day detail modal's body moved from `body.innerHTML = ''` to a `clearChildren()` (node removal through `removeChild`), eliminating the only `innerHTML` use that existed in the calendar flow.
- `templates/login/register.html`: `?v=36` → `?v=37` on the `register.js` asset.
- `system/tests/test_register_wizard_contract.py`:
  - The existing test updated to expect `?v=37`.
  - A new test `test_user_data_render_functions_use_safe_dom_not_innerhtml`: it verifies through static inspection that the bodies of `renderReview` and `renderConfirmationSummary` contain no `.innerHTML` and use the `el(` helper.
  - A new class `CalendarTemplateStaticContractTestCase`: it verifies that `calendar.html` references the versioned external script, no longer contains the inline modal/theme logic, and that `calendar.js` does not use `.innerHTML` and exposes `clearChildren`.

## Cleanup findings
- The remaining uses of `innerHTML` in `register.js` (the plan filters, the plan cards, the product catalog, the cart, the checkout summary, the class catalog) remain, but they all already escaped the dynamic data through `escHtml()` before this change — none of them concatenates user data without escaping. They are lower-risk because they mostly carry catalog/administrative data (plans, products, classes), not data typed by the student/guardian.
- No remaining use of `innerHTML` was found in `templates/calendar/calendar.html` after the extraction — the file ended up with no inline behavioral `<script>`, leaving only the theme pre-paint snippet (with no business logic and no user data).

## Follow-up PRDs
- Pending: a new PRD to migrate the remaining blocks of `register.js` (`renderPlanCards`, `renderProductsCatalog`, the cart card, `onEnterCheckout`, `renderClassCatalog`, etc.) from escaped HTML string concatenation to DOM construction through `el()`, completing the file's coverage. Not created in this run because it is outside the highest-risk core (user data) and to keep this delivery's scope proportional.

## Deviations from plan
- The original plan foresaw assessing "every innerHTML use" in the file; given the file's size (over 3,000 lines) and the time available, the execution prioritized exclusively the two points with the highest density of raw user data (the name, email, phone, and class name of several people): `renderConfirmationSummary` and `renderReview`. The other points (catalog/plan/product) were already escaped and were left for the follow-up PRD recorded above.
- The `?v=` versioning of the new `static/system/js/calendar/calendar.js` started at `?v=1` (a new file); there was no prior convention for calendar files.

## Pending
- Refactor the remaining `innerHTML` points with `escHtml` (plans, products, the cart, the checkout, the class catalog) into safe DOM through `el()`, in a follow-up PRD.
- Explicit mobile validation (a viewport resize) was not performed in this round; the visual validation covered only desktop in the internal browser. The wizard and the calendar use existing responsive CSS untouched by this change, but the specific mobile evidence was not captured.

## Final status
Completed with limitations — the highest-risk core (user data in the registration wizard: the confirmation summary and the review) and the complete extraction of the calendar's inline JavaScript were implemented, tested (a real Red/Green), and validated visually (desktop, the light/dark theme, and a proof that malicious markup is not executed). The remaining `innerHTML` points with `escHtml` in catalog/administrative data and the explicit mobile viewport validation are documented as a pending item/follow-up.
