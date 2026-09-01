# PRD-069: The LV home with mature visual governance

## Summary
Recreate only LV JIU JITSU's authenticated Home, using mature visual governance and preserving only the LV rules needed for authentication, permissions, and the People flow.

## Demand type
UI + Django MVT, with no new schema and without reopening modules outside the scope.

## Current problem
PRD-068 left the project with only the login and its linked assets. LV's Python code still has `HomeView`, routes, and historical home tests, but `templates/home/dashboard.html` and the `static/system/css/home/dashboard.css` and `static/system/js/home/dashboard.js` assets no longer exist.

## Goal
Implement a single Home at `/home/`, clean and lean, with mature styling and governance and with LV's content and permission rules.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/create_admin_superuser.py`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/views/auth_views.py`
- `system/middleware.py`
- `system/services/portal_auth.py`
- `system/forms/auth_forms.py`
- `system/models/person.py`
- `system/constants.py`
- `system/runtime_config.py`
- `system/context_processors.py`
- `lvjiujitsu/settings.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_admin_hubs_contract.py`

### Adjacent files consulted
- `system/tests/test_commands.py`

### Internet / official documentation
- The Django 5.2 official docs through Context7: custom management commands, class-based views, templates, and login mixins.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`
- The internal browser already validated for the LV login in PRD-068.

### Limitations found
- Resolved by PRD-070: `system/migrations/0001_initial.py` was generated, applied to the local SQLite, and validated.
- The local database received only the seeds necessary for the target flow: the admin, person types, belts, and 5 sample people.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Approved by the user in the message "Implemente" ("Implement it").

## Execution prompt
### Persona
Senior Django MVT engineer, pragmatic, with mature visual governance.

### Action
Recreate only the LV Home with the first operational module: People.

### Context
LV must follow the structural reference style, but must not port an external domain. The home's content must reflect the academy: people, technical/admin access, recent students, and an empty state.

### Constraints
- Do not run broad seeds or legacy imports outside the target flow.
- Do not reintroduce the complete People module, the CRUD modal, a broad global base, or other modules.
- Do not create unrequested aggregate KPIs.
- Do not add dead links, `href="#"`, or disabled shortcuts.
- Do not edit `staticfiles/`.

### Acceptance criteria
- `/home/` renders for an authenticated technical admin.
- The home loads the light/dark theme with `lv-theme`.
- The home uses its own minimal shell, with a topbar.
- Quick access shows only the links permitted and existing at this stage: `Pessoas` (`People`) and `Django Admin`.
- Recent people appear when there is data.
- The empty state appears when there are no people.
- Mobile has no horizontal overflow.
- The console has no critical error.

### Expected evidence
- `manage.py check`
- `node --check static/system/js/home/dashboard.js`
- The internal browser for the real route available.
- The internal browser authenticated at `http://localhost:8000/home/`.

### Output format
A closing statement in Brazilian Portuguese with what was implemented, evidence, what was not validated, pending items, and status.

## Scope
- `templates/home/dashboard.html`
- `templates/home/partials/_dashboard_chevron.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- A minimal adjustment in `HomeView`, only when necessary for the home's context.
- A focused home contract test, if it needs adjusting to the minimal behavior.

## Out of scope
- Importing the legacy mass of people.
- Implementing People, classes, finance, graduation, materials, plans, or the CRUD modal.
- Recreating a broad `templates/lv/base.html`.
- Importing an external domain.

## Impacted files
- To create: `templates/home/dashboard.html`
- To create: `templates/home/partials/_dashboard_chevron.html`
- To create: `static/system/css/home/dashboard.css`
- To create: `static/system/js/home/dashboard.js`
- To assess: `system/views/home_views.py`
- To assess: `system/tests/test_home_dashboard.py`

## Risks and edge cases
- A database with no tables prevents a real validation of the home through the browser.
- Creating a broad shell now may reintroduce files outside the home module.
- Links to modules not yet recreated would break the progressive strategy.
- The technical admin has no `portal_person`; the home needs to work without a person.

## Rules and constraints
- The interface in Brazilian Portuguese.
- The code and identifiers in English.
- CSS tokens per theme.
- No inline behavioral CSS/JS.
- No business rules in a template or in JavaScript.

## Visual hierarchy
- The topbar: the LV logo, the theme, sign out.
- The header: the date, a greeting, the operational context.
- Section 1: Quick access, with defined groups.
- Section 2: Recent people, with a dense list and the belt/degree when it exists.
- The empty state: a simple panel with an action toward People.

## Wireframe
### Region: Topbar
- The LV logo on the left.
- The theme and sign-out buttons on the right.

### Region: Header
- Eyebrow: the day and date.
- Title: `Ola, <nome>` (`Hi, <name>`).

### Region: Quick access
- The `Operacao` (`Operations`) group.
- A `Pessoas` (`People`) link.
- A `Django Admin` link, only for the technical user.

### Region: Recent people
- A `summary-list` list.
- Each item: the status/type on the left, the name and CPF/class in the center, and a belt/degree badge when it exists.
- An empty state with objective text and a link to People.

## State machine
### The theme
- `light` -> a click -> `dark`
- `dark` -> a click -> `light`
- Persistence in `localStorage["lv-theme"]`

### Collapsible sections
- `expanded` -> a click -> `collapsed`
- `collapsed` -> a click -> `expanded`
- Persistence in `localStorage["lv-home-sections"]`

### The people list
- `empty`: no recent people.
- `populated`: renders up to six recent people coming from `HomeView`.

## Plan
1. Approve the visual proposal.
2. Create the home's template, partial, CSS, and JavaScript.
3. Adjust the view's minimal context when necessary.
4. Write/adjust the automated contract and run a proportional test.
5. Validate with the checks.
6. Validate in the authenticated browser.
7. Audit the cleanup.

## Test plan
### Tests available
- `system/tests/test_home_dashboard.py`
- `system/tests/test_admin_hubs_contract.py`

### Execution authorization
The authorization updated by PRD-070: local tests, migrations, seeds, and the admin authorized for an operational delivery.

### Execution evidence
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 tests OK.
- `manage.py test --verbosity 2`: 226 tests run; 9 legacy errors from templates outside the progressive scope, removed earlier.

## Visual validation
The authenticated visual validation completed in the internal browser at `http://localhost:8000/home/`.

- Desktop light: `test_screenshots/prd-070-home-validation/desktop-light.png`
- Desktop dark: `test_screenshots/prd-070-home-validation/desktop-dark.png`
- Mobile light: `test_screenshots/prd-070-home-validation/mobile-light.png`
- Mobile dark: `test_screenshots/prd-070-home-validation/mobile-dark.png`
- Console: no errors.
- Horizontal overflow: absent on desktop and mobile.
- Content validated: `Ola, admin` (`Hi, admin`), the `Pessoas` (`People`) and `Django Admin` quick links, the recent people list, and the `Branca · 4º` (`White · 4th`) badge.

## ORM validation
The local database validated with 1 user, 1 superuser, 5 person types, 5 people, 13 belts, and 1 class. There was no broad import.

## Quality validation
- `py_compile system/views/home_views.py`: success.
- `manage.py check`: success, 0 issues.
- `node --check static/system/js/home/dashboard.js`: success.
- `get_template('home/dashboard.html')`: `TEMPLATE_OK`.
- A search for residue in the Home/CSS/JS/View: no `href="#"`, `quick-link--disabled`, `innerHTML`, `Planos`, `Turmas`, `Financeiro`, `Graduacao`, `Materiais`, or `Perfis e acessos`.
- `git diff --check`: no error, only a local LF/CRLF conversion warning in `system/views/home_views.py`.
- `manage.py check`: 0 issues after migrate/seeds.
- `manage.py showmigrations system`: `[X] 0001_initial`.

## Evidence
- `manage.py help create_admin_superuser`: the command is available.
- `py_compile` of the admin command, the home views, urls, and mixins: success.
- `manage.py check`: no issues.
- `manage.py showmigrations --plan`: the built-in migrations pending; the `system` app absent.
- The `ADMIN_SUPERUSER_USERNAME`, `ADMIN_SUPERUSER_EMAIL`, and `ADMIN_SUPERUSER_PASSWORD` settings: configured.
- PRD-070 removed the local blocker, generated/applied `system.0001_initial`, ran the targeted seeds, and validated the authenticated Home in the browser.

## Implemented
- `templates/home/dashboard.html`: its own minimal shell, the LV topbar, theme switching, logout, the header, and the Quick access/Recent people sections.
- `templates/home/partials/_dashboard_chevron.html`: an icon reused in the section toggles.
- `static/system/css/home/dashboard.css`: light/dark tokens, a responsive layout, operational links, the people list, and the visual belt/degree badge.
- `static/system/js/home/dashboard.js`: the theme persisted in `lv-theme`, collapsible sections persisted in `lv-home-sections`, and message dismissal with no `innerHTML`.
- `system/views/home_views.py`: the old classes, graduation, finance, trial, and payroll context removed; only auth, the date, the name, the People permission, and the recent people kept.

## Cleanup findings
- Imports and queries from modules outside Home/People removed from `HomeView`.
- The home has no dead links or disabled shortcuts.
- Access to recent people is conditioned on the technical admin or People support profiles.
- The files created are restricted to `templates/home/` and `static/system/{css,js}/home/`.

## Follow-up PRDs
PRD-070 ran the local operational cycle. Full-suite failures outside the progressive scope are recorded in PRD-070 as a legacy alignment finding.

## Deviations from plan
- The authenticated validation was completed after PRD-070's governance review.

## Pending
- Align the legacy tests of removed modules with the progressive scope, should the full suite need to be green before those modules are recreated.

## Final status
Completed.
