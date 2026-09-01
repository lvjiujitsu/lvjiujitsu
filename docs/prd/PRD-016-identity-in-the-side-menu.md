# PRD-016: Identity in the side menu

## Summary of the implementation
Display the logged-in person's name and their access classification at the top of the side menu.

## Demand type
Targeted authenticated-interface fix with a rendering test.

## Current problem
The side menu shows only the `Menu` label, navigation, theme, and sign-out. There is no clear confirmation of which account is authenticated.

## Goal
The top of the side menu must show:
- the name of the person logged into the portal and their relationship type, when there is a `PortalAccount`;
- the technical user and the technical administrator classification, when the access is technical.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `templates/base.html`
- `system/context_processors.py`
- `system/middleware.py`
- `system/views/portal_mixins.py`

### Adjacent files consulted
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`

### Internet / official documentation
- Not applicable. The change uses local template, middleware, and Django test contracts.

### MCPs / tools verified
- PowerShell — OK — file reading.
- Django test client — to be validated through an automated test.
- Browser/Playwright — to be validated visually after the implementation.

### Limitations found
- `rg` is still unavailable due to access denied in this environment; searches were done with PowerShell.
- The worktree already carries earlier unrelated changes.

## Execution prompt
### Persona
Development agent specializing in Django MVT, following SDD + TDD.

### Action
Add an identity indicator to the authenticated side menu.

### Context
`PortalSessionMiddleware` injects `request.portal_person`, `request.portal_account`, `request.technical_admin_user`, and the role flags into the request. `templates/base.html` renders the shared drawer.

### Constraints
- no business rules in JavaScript
- no migration
- visible text in Brazilian Portuguese
- do not duplicate per screen
- preserve the responsive menu

### Acceptance criteria
- [x] A portal account must see their own name at the top of the side menu.
- [x] A portal account must see their classification/relationship type at the top of the side menu.
- [x] Technical access must show the technical user and the technical classification.
- [x] The block must not appear on public pages without authentication.
- [x] The text must fit on desktop and mobile.

### Expected evidence
- Passing rendering tests.
- `manage.py check` passing.
- Visual validation of the drawer.

### Output format
Implemented code + tests + evidence.

## Scope
The base template, the portal CSS, authenticated view tests, and this PRD.

## Out of scope
Changing authentication, permissions, routes, registration, login, or role rules.

## Impacted files
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `docs/prd/PRD-016-identity-in-the-side-menu.md`

## Risks and edge cases
- A technical user with no full name.
- A person with no relationship type.
- A long name breaking the drawer layout.
- A technical account and a portal account present at the same time.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no migrations
- mandatory validation
- no hardcoding of a specific person

## Plan
- [x] 1. Context and reading
- [x] 2. Tests (Red)
- [x] 3. Implementation
- [x] 4. Technical validation
- [x] 5. Visual validation
- [x] 6. Documentation update

## Visual validation
### Desktop
Playwright at `1280x800`: the drawer opened at `/home/instructor/`, the block showed `Layon Quirino` and `Professor` (`Instructor`), with `accountFitsDrawer=true`.

### Mobile
Playwright at `390x844`: the drawer opened at `/home/instructor/`, the block showed `Layon Quirino` and `Professor` (`Instructor`), with `accountFitsDrawer=true`.

### Browser console
No console errors in the desktop and mobile validations.

### Terminal
The local server responded `200` at `http://127.0.0.1:8000/login/`.

## ORM validation
### Database
There is no schema change.

### Shell checks
Validated through Django rendering tests.

### Flow integrity
Authenticated home rendering validated through the Django test client and Playwright.

## Quality validation
### No hardcoding
No specific person hardcoded in the code. The names used appear only in tests/validation.

### No brittle conditional structures
The condition is limited to `request.portal_person` and `request.portal_is_technical_admin`, existing middleware contracts.

### No `except: pass`
Not introduced.

### No error masking
Not introduced.

### No unnecessary comments or docstrings
Not introduced.

## Evidence
- Red: `manage.py test system.tests.test_views.PortalViewTestCase.test_drawer_shows_logged_portal_person_identity system.tests.test_views.PortalViewTestCase.test_drawer_shows_technical_admin_identity system.tests.test_views.PortalViewTestCase.test_public_route_does_not_render_logged_user_identity --verbosity 2` failed before the implementation due to the absence of the literal `aria-label="Usuário logado"` (`aria-label="Logged-in user"`).
- Green: the same command passed with 3 tests OK.
- `manage.py check` passed: `System check identified no issues (0 silenced).`
- `manage.py collectstatic --noinput` passed: 1 static file copied and 164 unchanged.
- `manage.py test --verbosity 2` ran 317 tests but did not end green due to failures that already existed outside this change:
  - `system.tests.test_services` does not import `append_order_refund_record`;
  - `system.tests.test_asaas.AsaasWebhookTests.test_withdrawal_service_is_removed` still finds `asaas_payroll.request_withdrawal`;
  - `system.tests.test_views.PortalViewTestCase.test_staff_financial_screen_rejects_withdrawal_post` receives 200 instead of 405.
- In-app browser: the drawer showed `LOGADO COMO / Layon Quirino / Professor` (`LOGGED IN AS / Layon Quirino / Instructor`) and returned no console errors.
- Playwright: desktop `1280x800` and mobile `390x844` passed with `accountFitsDrawer=true`.

## Implemented
- Added a `.drawer-account` block at the top of the authenticated side menu.
- A portal account shows `request.portal_person.full_name` and `request.portal_person.person_type.display_name`.
- Technical access shows the technical name/username and the classification `Administrador técnico` (`Technical administrator`).
- The CSS ensures long names are truncated and the classification badge stays contained.
- The CSS cache-buster updated to `20260507f`.

## Deviations from plan
- The full suite was run but failed due to existing problems in the financial/Asaas flow outside the scope of this PRD.

## Pending
- Separately fix the existing full-suite failures related to Asaas/finance.
