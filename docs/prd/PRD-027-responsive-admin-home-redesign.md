# PRD-027: Responsive redesign of the master home

## Summary of the implementation
Reimplement the technical administrator's home to follow the visual standard applied to People: a wide page, clear sections per domain, always-visible shortcuts, the light/dark theme preserved, and no decorative or non-functional controls.

## Demand type
UI refactoring.

## Current problem
The master home still uses the old `panel-card` structure with poorly grouped shortcut lists. On desktop the content does not make good use of the available width, and on mobile the groups do not make clear where each administrative routine belongs.

## Goal
- Standardize the master home with the portal's new look.
- Group shortcuts by domain: Records, Mat, Materials, Graduation, Finance, and Technical.
- Remove the dependency on a toggle or hidden action.
- Keep every current link reachable.

## Context Ledger
### Files read in full
- `templates/home/admin/dashboard.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `system/views/home_views.py`
- `system/tests/test_views.py`

### Adjacent files consulted
- `templates/home/administrative/dashboard.html`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_calendar.py`

### Internet / official documentation
- Not applicable.

### MCPs / tools verified
- Django test runner — OK.
- Playwright — OK.

### Limitations found
- No folder creation.
- No migrations.

## Execution prompt
### Persona
Development agent specializing in Django MVT, following SDD + TDD + responsive CSS.

### Action
Reimplement the administrative master home, preserving links and permissions.

### Context
The master home is the administrator's technical entry surface and must be clear, direct, and consistent with the People screen.

### Constraints
- no hardcoded business rules
- no unnecessary JavaScript
- CSS under `static/`
- templates under `templates/`
- mandatory validation

### Acceptance criteria
- [ ] The master home must load with no `Mostrar mais` (`Show more`) button.
- [ ] The master home must contain the groups: Records, Mat, Materials, Graduation, Finance, and Technical.
- [ ] Every old link must remain reachable.
- [ ] The layout must use the desktop width similarly to the People screen.
- [ ] The home must work with no horizontal overflow on desktop and mobile.

### Expected evidence
- passing tests
- `manage.py check`
- `collectstatic --noinput`
- Playwright desktop/mobile with no console errors

## Scope
- `templates/home/admin/dashboard.html`
- `static/system/css/portal/admin-dashboard.css`
- `system/tests/test_views.py`
- this PRD's documentation

## Out of scope
- Changing permissions.
- Changing routes.
- Changing the instructor, student, or conventional back-office dashboards.

## Impacted files
- `docs/prd/PRD-027-responsive-admin-home-redesign.md`
- `templates/home/admin/dashboard.html`
- `static/system/css/portal/admin-dashboard.css`
- `system/tests/test_views.py`

## Risks and edge cases
- Accidentally removing a link.
- Leaving cards too wide on mobile.
- Reintroducing decorative text with no function.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no migrations
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contract test
- [x] 3. Implementation
- [x] 4. Technical validation
- [x] 5. Visual validation

## Visual validation
### Desktop
OK. Playwright at 1622x1411 confirmed a usable width of 1480px, 3 columns, and 6 sections.

### Mobile
OK. Playwright at 390x900 confirmed 1 column and no horizontal overflow.

### Browser console
OK. No critical errors captured.

### Terminal
OK. Focused tests, `manage.py check`, `collectstatic`, and `git diff --check` were run.

## Evidence
- Red: `test_master_dashboard_uses_grouped_responsive_layout` failed due to the absence of `admin-dashboard.css`.
- Green: the focused tests for the master home and the adjacent shortcuts passed.
- Playwright desktop/mobile passed.

## Implemented
- `templates/home/admin/dashboard.html` restructured into sections per domain.
- `static/system/css/portal/admin-dashboard.css` created.
- Contract tests updated.

## Deviations from plan
None.

## Pending
No known pending items at this stage.
