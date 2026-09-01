# PRD-028: Home and People in full screen

## Summary of the implementation
Restart the visual standard of the homes and the People home with a full screen, distinct modules, simple side navigation, and clear redirection from the main home to the functional homes, starting with People.

## Demand type
UI refactoring with documentation regeneration.

## Current problem
The reimplemented screens still look like blocks grouped inside cards, waste space on different monitors, and mix a decorative summary with real actions. The side menu is also heavy to navigate between routines.

## Goal
- Use the screen's full usable width on the homes and on People.
- Show direct commands on the initial home inside light contextual blocks per operational domain.
- Simplify the side menu with icons, clear labels, and direct links by permission.
- Preserve the per-profile redirection and every existing action.
- Keep the light/dark theme and real responsiveness on phones and desktops.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-027-responsive-admin-home-redesign.md`
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/views/portal_mixins.py`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/admin-dashboard.css`
- `static/system/css/portal/people.css`
- `static/system/js/shared/drawer-menu.js`
- `static/system/js/shared/people-list.js`
- `static/system/js/home/instructor-dashboard.js`
- `system/tests/test_views.py`

### Adjacent files consulted
- `docs/prd/`

### Internet / official documentation
- Not applicable; the change uses the existing Django templates and CSS.

### MCPs / tools verified
- PowerShell — OK.
- Django test runner — OK.
- Browser/Playwright — OK.

### Limitations found
- No folder creation.
- No migrations.
- The scope of this stage is limited to the Home, the side menu, and the People home.
- The request mentioned Figma; the `figma-generate-design` skill was read to guide the composition, but no target Figma file was provided for mutation.

## Functional matrix by profile

### Technical administrator
- Must reach the `admin-home` home after a technical login.
- Must reach People, Types, Plans, Categories, Classes, Schedules, the administrative Schedule, Stock, Pre-orders, the Graduation overview, Belts, Rules, Graduation history, Financial control, Approvals, Pending payments, Instructor payroll, the Payment queue, and the Django Admin.
- Must not see the same action duplicated on the initial home.

### Back office
- Must reach the administrative home.
- Must operate People, Stock, Pre-orders, the Schedule, Plans, Financial control, and their own finances where applicable.
- Must not reach the technical `admin-home` home.

### Instructor
- Must reach the instructor home.
- Must see the day's classes, check-ins, create an open class, manage the schedule, view students, register a student, request materials, and their own finances.
- In People, must list only the permitted students/dependents and must not receive Delete.

### Student, guardian, and dependent
- Must reach the student home.
- Must see the tuition, plan, shop, the day's classes, check-in, attendance history, and graduation.
- Guardian/dependent must preserve the financial context linked by the backend.

## Non-functional requirements
- The initial home must organize commands by functional proximity: People and access, Academy, Materials, Graduation, Finance, and Technical.
- The blocks must guide navigation without hiding actions, with no collapsing and no long decorative text.
- The side menu must use simple, consistent icons with short text and a comfortable touch target.
- The first screen on desktop must make use of wide monitors without creating empty columns.
- On mobile, commands must become a single-column list/grid with no horizontal overflow.
- On desktop, operational blocks and listings must use horizontal behavior: context on the left and commands/records on the right; on a phone they must stack in a vertical sequence.
- The light/dark theme must use the existing tokens.
- Icons are decorative and must carry `aria-hidden="true"`.

## Execution prompt
### Persona
Development agent specializing in Django MVT, following SDD + TDD + operational responsive CSS.

### Action
Reimplement the Home and People surfaces in full screen, preserving the functional requirements per profile.

### Context
The LV JIU JITSU portal has different homes for the technical administrator, back office, instructor, and student/guardian/dependent. The home must take the user to functional modules such as People, Mat, Finance, Materials, and Graduation without turning the screen into a landing page.

### Constraints
- no hardcoded business rules
- no migrations
- do not create folders
- do not remove features
- CSS under `static/`
- templates under `templates/`
- mandatory visual validation

### Acceptance criteria
- [ ] The side menu must have direct links with icons and no cluttered visual tree.
- [ ] The technical home must show direct commands for every administrative module inside contextual blocks.
- [ ] `Django Admin` must appear exactly once on the technical home.
- [ ] The back-office home must show People, Stock, Pre-orders, the Schedule, Plans, and Finance.
- [ ] The instructor home must show the day's classes, check-ins, the schedule, students, student registration, the shop, and their own finances.
- [ ] The student/guardian/dependent home must show the tuition, graduation, shop, plans, the day's classes, check-in, and history.
- [ ] The People home must use the full width, keep the functional KPIs, filters, modal viewing, and actions according to permission.
- [ ] Desktop and mobile must have no horizontal overflow.
- [ ] The People, Types, Plans, Categories, Classes, Schedules, Stock, and Belts listings must stack on mobile and align in horizontal rows on desktop.
- [ ] Financial screens and administrative tables must use the usable width and preserve horizontal scrolling only inside the table when necessary.
- [ ] The light/dark theme must keep working.

## Scope
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/workbench.css`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `docs/UI-SCREEN-CONTRACT.md`

## Out of scope
- The person editing screen.
- Person detail, deletion, and creation.
- The Mat, Finance, Materials, and Graduation CRUDs.
- Permission or route changes.

## Impacted files
- `docs/prd/PRD-028-home-and-people-in-full-screen.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/workbench.css`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`

## Risks and edge cases
- Losing a functional link while simplifying the menu.
- Hiding actions on mobile.
- Making the modules look too alike and losing scannability.
- Breaking the check-in JavaScript by moving containers.

## Plan
- [x] 1. Update the contract and the tests.
- [x] 2. Implement a simple side menu with icons.
- [x] 3. Implement the technical home in contextual blocks.
- [x] 4. Restructure the shared full-screen CSS.
- [x] 5. Restructure the People home.
- [x] 6. Validate tests, check, collectstatic, and the browser.

## Visual validation
### Desktop
OK. Browser/Playwright at `http://localhost:8000/home/admin/`:
- viewport 1440x1000: `workbench-context-grid` with 4 columns, 6 contextual blocks, 19 commands, no horizontal overflow;
- viewport 2327x1411: `workbench-context-grid` with 6 columns, 6 contextual blocks, 19 commands, no horizontal overflow;
- later validation at 1440x1000 confirmed the home's blocks with 2 internal columns per block: context on the left and commands on the right;
- later validation covered People, Types, Plans, Categories, Classes, Schedules, the Schedule, Stock, Pre-orders, the Overview, Belts, Rules, History, Financial control, Approvals, Pending payments, Instructor payroll, and the Payment queue with no horizontal overflow;
- `Django Admin` appears once on the home;
- the drawer has no `details`, `summary`, or `.drawer-group`;
- 23 icons in the drawer;
- no horizontal overflow.

### Mobile
OK. Browser at 390x900:
- `workbench-context-grid` with 1 column;
- 19 direct commands;
- no horizontal overflow.

### Browser console
No critical error observed during the navigation validation and DOM inspection.

### Terminal
OK.

## Evidence
- Initial Red:
  - `test_master_dashboard_uses_grouped_responsive_layout` failed due to the absence of `workbench.css` and `workbench-shell`.
  - `test_dashboards_and_people_home_use_fullscreen_workbench_contract` failed due to the absence of `workbench-shell`.
- Green:
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_master_dashboard_shows_all_shortcuts_without_toggle system.tests.test_views.PortalViewTestCase.test_master_dashboard_uses_contextual_command_blocks system.tests.test_class_portal_views.ClassPortalViewTestCase.test_admin_home_exposes_class_crud_shortcuts --verbosity 2` — OK.
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_master_dashboard_uses_contextual_command_blocks system.tests.test_class_portal_views.ClassPortalViewTestCase.test_admin_home_exposes_class_crud_shortcuts --verbosity 2` — OK after adjusting the blocks' natural height.
  - `manage.py test system.tests.test_views --verbosity 2` — 78 tests OK.
  - `manage.py test --verbosity 2` — 269 tests OK.
  - `manage.py test --verbosity 2` — 275 tests OK after the plan adjustments and horizontal standardization.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.

## Implemented
- A side menu with shared SVG icons and direct links.
- Collapsible groupers removed from the drawer.
- The master home with 6 contextual blocks and 19 direct commands.
- Removed the duplicate `Django Admin` on the master home.
- `workbench.css` adjusted for a responsive command grid.
- The shared CSS adjusted for horizontal lists and operational screens on desktop and vertical ones on mobile.
- The UI contract updated with the rule for a home in contextual blocks and an iconographic menu.

## Deviations from plan
The first design removed the domain proximity entirely and left the commands loose. The later correction adopted light contextual blocks, keeping every action visible.

## Pending
The back-office, instructor, student, and People homes still load `workbench.css`, but the deep visual remodeling without grouping was applied in this correction only to the master home and the side menu, per the user's current annotation.
