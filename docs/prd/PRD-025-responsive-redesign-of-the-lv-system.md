# PRD-025: Responsive redesign of the LV system

## Summary of the implementation

Create the specification foundation to reimplement, in stages, the LV JIU JITSU system's interface on phones and computers, preserving every existing feature, the light and dark themes, and the real per-person-type permission contracts.

This PRD does not yet authorize the visual replacement of any screen. It creates the execution track for the upcoming per-screen or per-module PRDs.

## Demand type

Architectural UI change, documentation regeneration, and preparation for a visual refactoring.

## Current problem

The screens exist and cover several system routines, but the visual experience is inconsistent across modules, with mixed use of cards, tables, inline scripts, inline styles, manually versioned assets, and different behaviors between authenticated and public templates.

The main risk of the redesign is improving appearance while removing, hiding, or breaking operational features that already exist.

## Goal

Define a UI contract for the system as a jiu jitsu academy, with the LV visual standard, responsiveness, minimum accessibility, per-role behavior, and a mandatory validation rule before any screen is reimplemented.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `system/urls.py`
- `lvjiujitsu/urls.py`
- `templates/base.html`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/selectors/person_selectors.py`
- `system/middleware.py`
- `system/context_processors.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/plan_views.py`
- `system/views/product_views.py`
- `system/views/calendar_views.py`
- `system/views/graduation_views.py`
- `system/views/auth_views.py`
- `system/views/billing_admin_views.py`
- `system/views/payment_views.py`
- `system/views/plan_change_views.py`
- `system/views/asaas_views.py`

### Adjacent files consulted

- `templates/`
- `static/system/`
- `docs/prd/`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/portal/person-detail.css`
- `static/system/css/auth/login.css`
- `static/system/css/billing/billing.css`
- `static/system/css/shared/plan-selector.css`
- `templates/login/register.html`
- `templates/login/login_form.html`
- `templates/calendar/admin_calendar.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/student_schedule.html`
- `static/system/js/shared/theme-toggle.js`
- `static/system/js/shared/drawer-menu.js`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/js/products/product-store.js`
- `static/system/js/billing/plan-change-selector.js`
- `static/system/js/auth/registration-wizard-clean.js`

### Internet / official documentation

- MDN `prefers-color-scheme`: https://developer.mozilla.org/en-US/docs/Web/CSS/%40media/prefers-color-scheme
- MDN `color-scheme`: https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme
- MDN Container size and style queries: https://developer.mozilla.org/docs/Web/CSS/CSS_containment/Container_size_and_style_queries
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- W3C Understanding Target Size Minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum

### MCPs / tools verified

- The `figma-use` skill: loaded and read. Status: available. Test executed: reading `SKILL.md`. `use_figma` was not called because there is no target Figma file URL at this stage.
- PowerShell: available. Test executed: read commands and `git status --short`.
- The project's Python: available. Test executed: `.\.venv\Scripts\python.exe --version` returned Python 3.12.10.
- Django check: available. Test executed: `.\.venv\Scripts\python.exe manage.py check` returned 0 problems.

### Limitations found

- The current stage does not validate screens visually in a browser because it does not yet change the UI.
- The visual reference file `LOGO_LV.pdf` is outside the workspace at `C:\Users\whsf\Downloads\LOGO_LV.pdf`; the file's existence was verified, but the main visual identity used in this PRD came from the PNG image provided and from the assets already in `static/system/img/`.
- There are current occurrences of inline JavaScript, inline styles, and `innerHTML` in templates/scripts. That will be treated as UI/security debt to resolve through per-screen PRDs, without blocking the creation of this contract.

## Execution prompt

### Persona

Development agent specializing in server-rendered Django, responsive UI, SDD, TDD, and in-browser visual validation.

### Action

Reimplement each screen of the LV JIU JITSU system following the `docs/UI-SCREEN-CONTRACT.md` contract, creating a specific PRD per screen or module before any visual change.

### Context

The system is a Django monolith operating the public portal and the authenticated areas of a jiu jitsu academy. The interface must reflect the LV identity: the mat, discipline, martial culture, black/grey/white with red as the accent, keeping the light and dark themes.

### Constraints

- do not create new folders
- do not edit `staticfiles/`
- no migrations
- no hardcoded secrets or variable rules
- do not remove existing features
- do not hide critical features through responsiveness
- no new inline JS/CSS, except data JSON in `<script type="application/json">`
- do not change business rules in a template or in JavaScript
- mandatory full reading of the screen before changing it
- mandatory visual validation on desktop and mobile before finishing any screen

### Acceptance criteria

- [ ] Each redesign stage must have its own PRD or an approved PRD subsection, with a clear screen/module scope.
- [ ] Each changed screen must preserve existing links, forms, permissions, messages, empty states, error states, and POST actions.
- [ ] The light and dark themes must remain available on every changed screen.
- [ ] On a phone, critical information must appear in a vertical flow with clear scrolling, without disappearing.
- [ ] On desktop, information must use width, grid, and density appropriate to the operational flow.
- [ ] Operational tables must be replaced by responsive cards or given readable overflow handling, without losing critical columns.
- [ ] The people screen must visibly differentiate the behavior of Student, Dependent, Guardian, Instructor, Back office, and Technical admin according to the real permission contracts.
- [ ] Every CSS/JS asset versioned with `?v=` must have its version updated when changed.
- [ ] The redesign must pass `manage.py check`, the applicable tests, `collectstatic --noinput` when there are static files, and visual validation with the browser/Playwright.

### Expected evidence

- the updated screen/module PRD
- passing tests
- `manage.py check` with no problems
- `collectstatic --noinput` with no error when there are static files
- desktop and mobile browsers with no critical console errors
- the server terminal with no stack traces
- screenshots or an objective account of the validated screens

### Output format

Implemented code + tests + validation evidence + real pending items.

## Scope

- Create a documented UI and responsiveness contract in `docs/UI-SCREEN-CONTRACT.md`.
- Update `CLAUDE.md` to declare that contract as the local source of truth for the redesign.
- Record in the PRD the initial inventory of areas and the per-stage execution protocol.

## Out of scope

- Reimplementing screens at this stage.
- Changing production CSS/JS at this stage.
- Creating new folders.
- Changing models, migrations, services, or business rules.
- Creating or modifying a Figma file with no target URL and no stage of its own.

## Impacted files

- `docs/prd/PRD-025-responsive-redesign-of-the-lv-system.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `CLAUDE.md`
- `AGENTS.md` only when a generic source-of-truth reinforcement is needed, with no project-specific rule.

## Risks and edge cases

- The visual redesign hiding administrative or financial actions on mobile.
- The people screen treating every person type as a student and hiding instructor or back-office information.
- Cards replacing tables and removing audit columns.
- The dark theme ending up readable while the light theme loses the LV identity, or the reverse.
- Red becoming a dominant accent and compromising contrast.
- The existing inline JavaScript continuing to hinder validation and maintenance.
- A visual change to a versioned asset not updating the query string.

## Rules and constraints

- SDD before code.
- TDD for the implementation.
- No hardcoding.
- No error masking.
- No migrations by default.
- Mandatory full reading.
- Mandatory validation.
- No feature may be removed, hidden, or replaced by explanatory text.
- The visual identity must use the LV language without turning the internal system into a landing page.

## Plan

- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [ ] 3. Tests (Red)
- [ ] 4. Implementation (Green)
- [ ] 5. Refactoring (Refactor)
- [ ] 6. Full validation
- [ ] 7. Final cleanup
- [ ] 8. Documentation update

## Visual validation

### Desktop

Not applicable at this documentation stage.

### Mobile

Not applicable at this documentation stage.

### Browser console

Not applicable at this documentation stage.

### Terminal

`manage.py check` was run before the documentation edit and returned with no problems.

## ORM validation

### Database

Not applicable at this stage.

### Shell checks

Not applicable at this stage.

### Flow integrity

The flows were mapped through routes, views, templates, and permission constants. No flow was changed at this stage.

## Quality validation

### No hardcoding

The documentation introduces no operational hardcoding.

### No brittle conditional structures

Not applicable to production code at this stage.

### No `except: pass`

No Python code was introduced.

### No error masking

No error handling was introduced.

### No unnecessary comments or docstrings

Not applicable.

## Evidence

- `.\.venv\Scripts\python.exe --version` -> Python 3.12.10.
- `.\.venv\Scripts\python.exe manage.py check` -> System check identified no issues.
- `docs/prd/` already existed; no new folder was created.
- The visual file provided was verified at `C:\Users\whsf\Downloads\ChatGPT Image 8 de mai. de 2026, 22_03_06 (3).png`.
- The logo PDF provided was verified at `C:\Users\whsf\Downloads\LOGO_LV.pdf`.

## Implemented

- The macro PRD for the responsive redesign.
- A documented contract for UI and per-screen behavior.
- The contract's reference in `CLAUDE.md`.

## Deviations from plan

- No deviation at this stage.

## Pending

- Create a specific PRD for the first screen to be reimplemented.
- Validate the real screen visually before and after each change.
- Extract the existing inline scripts and inline styles when the corresponding screen enters scope.
- Decide whether the first screen will be `people/person_list.html`, `people/person_detail.html`, or `people/person_form.html`.
