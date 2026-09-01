# PRD-014: Administrative panel as a portal persona

## Summary of the implementation
Reorganize back-office, instructor, and master access in the portal. The technical master keeps a panel of its own. The back-office person starts using the same operational experience as the instructor, with an administrative area further down. The instructor gains a limited operational area for materials, student registration/lookup, and their own schedule. The shop starts allowing an order or a pre-order for the person themselves or for a selected student when the authenticated user is an instructor or back-office staff.

## Demand type
New feature + flow/permission fix + authenticated UI adjustment.

## Current problem
The back-office person has a separate, purely administrative home even though they are a portal person. The master panel and the administrative panel end up conceptually too close. The shop and pre-orders are limited to student types, preventing an instructor or back-office member from requesting materials. The instructor also has no operational shortcuts to support material sales/requests, student registration, and lookup.

## Goal
- Keep only the technical master on a different panel.
- Make the back-office home share the same base as the instructor home, adding an administrative area below.
- Expose to the instructor only the operational area consistent with classes, materials, and student support.
- Allow instructors/back-office staff to request materials for themselves or for a selected student with no new migration.
- Allow the instructor to register and view students, without unlocking editing/deletion/administrative finance.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `.cursor/rules/anti-hallucination.mdc`
- `.cursor/rules/clean-code.mdc`
- `.cursor/rules/django-architecture.mdc`
- `.cursor/rules/environment.mdc`
- `.cursor/rules/language.mdc`
- `.cursor/rules/prd.mdc`
- `.cursor/rules/protocol.mdc`
- `.cursor/rules/security.mdc`
- `.cursor/rules/templates-static.mdc`
- `.cursor/rules/testing.mdc`
- `.cursor/rules/validation.mdc`
- `system/constants.py`
- `system/middleware.py`
- `system/services/portal_auth.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/models/person.py`
- `system/views/__init__.py`
- `system/views/product_views.py`
- `system/views/calendar_views.py`
- `system/views/person_views.py`
- `system/views/class_views.py`
- `system/views/billing_admin_views.py`
- `system/forms/person_forms.py`
- `system/forms/product_forms.py`
- `system/context_processors.py`
- `system/selectors/person_selectors.py`
- `system/selectors/__init__.py`
- `system/selectors/product_backorders.py`
- `system/models/product.py`
- `system/models/product_backorder.py`
- `system/models/registration_order.py`
- `system/services/product_backorders.py`
- `system/services/registration_checkout.py`
- `system/services/class_calendar.py`
- `system/views/payment_views.py`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/products/product_store.html`
- `templates/products/student_backorder_list.html`
- `templates/billing/admin_backorder_queue.html`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/admin_calendar.html`
- `static/system/js/home/admin-dashboard.js`
- `static/system/js/products/product-store.js`
- `static/system/css/portal/portal.css`
- `system/tests/test_product_views.py`
- `system/tests/test_views.py`
- `system/tests/test_calendar.py`

### Adjacent files consulted
- `docs/prd/PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md`
- `docs/prd/PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md`
- `docs/prd/PRD-012-financial-module-and-payouts.md`
- `docs/prd/PRD-013-instructor-home-quick-actions.md`

### Internet / official documentation
- Not applicable. The delivery reuses Django CBVs, templates, and services that already exist, with no new library.

### MCPs / tools verified
- PowerShell — OK — file reading and local commands.
- `.venv` — OK — `.\.venv\Scripts\python.exe --version` returned Python 3.12.10.
- Django — OK — `.\.venv\Scripts\python.exe -m django --version` returned 4.1.13.
- `manage.py check` — OK — no issues in preflight.
- `manage.py showmigrations` — OK — `system` still has only `0001_initial`.
- Browser/Playwright — OK — embedded browser at `http://localhost:8000` with the console inspected on the changed screens.

### Limitations found
- `rg` exists but failed with `Access denied`; discovery was done with `Get-ChildItem` and `Select-String`.
- The worktree already carries many unrelated changes; the delivery must preserve that state.
- `templates/home/instructor/dashboard.html` references `static/system/js/home/instructor-dashboard.js`, but the source file does not exist yet. Visual validation will require fixing that within the scope of the instructor/back-office screen.

## Execution prompt
### Persona
Development agent specializing in Django 4.1, following SDD + TDD + MVT with services/selectors.

### Action
Implement the home, permission, and materials-flow adjustments described below.

### Context
The project has three authenticated homes: technical master (`home/admin`), back office (`home/administrative`), and instructor (`home/instructor`). The middleware already separates `portal_is_technical_admin`, `portal_is_administrative`, `portal_is_instructor`, and `portal_is_student`. The shop uses `RegistrationOrder` for one-off orders and `ProductBackorder` for pre-orders.

### Constraints
- no new migration
- no hardcoded variable rules
- no error masking
- do not unlock administrative financial/stock functions to the instructor
- the instructor may register/list/view students, but not edit/delete people or manage types
- back-office staff may keep accessing stock, the schedule, finance, and administrative records
- the technical master remains an administrative manager, not a portal person
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] Technical/staff login redirects to `admin-home` and renders `Painel master` (`Master panel`).
- [ ] A back-office person does not reach `admin-home`; the master panel stays restricted to the technical user.
- [ ] A back-office person reaches `administrative-home` with the instructor's base layout, containing `Aulas do dia` (`Today's classes`) and an administrative area below.
- [ ] The back-office home keeps shortcuts to People, Materials/Stock, Schedule, Plans, and Finance in the administrative area.
- [ ] The instructor sees an operational area below the home with materials, student registration/list, and the schedule.
- [ ] The instructor can open the materials shop.
- [ ] Back-office staff can open the materials shop as a portal person.
- [ ] The shop shows a recipient selector for instructor/back-office: the person themselves + active students/dependents.
- [ ] A material purchase POST by an instructor/back-office member may generate a `RegistrationOrder` for the selected student.
- [ ] A pre-order POST by an instructor/back-office member may generate a `ProductBackorder` for the selected student.
- [ ] The instructor can list and view students.
- [ ] The instructor can open the registration form for a new person, limited to student/dependent.
- [ ] The instructor cannot edit/delete people, manage types, control stock, or open administrative finance.
- [ ] `manage.py test --verbosity 2` passes.
- [ ] `manage.py check` passes.
- [ ] `collectstatic --noinput` passes when static files are changed.
- [ ] Desktop/mobile browser validation with no critical JavaScript errors and no relevant 404 on a changed asset.

### Expected evidence
- Red tests failing before the implementation.
- Green tests passing afterwards.
- `manage.py check`, `showmigrations`, and `collectstatic` with no failures.
- The browser opening the instructor and back-office homes, the shop, and the recipient selection flow.
- Browser console with no critical errors.

### Output format
Implemented code + tests + validation evidence.

## Scope
- Adjust the role constants for operational support and materials.
- Adjust `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, and the shared context.
- Reuse the instructor template for the back office with a conditional administrative area.
- Add the instructor's operational area.
- Adjust shop/pre-order/history permissions for portal people who may request materials.
- Add a selector for material recipients.
- Allow an order/pre-order to be created for a selected student when authorized.
- Adjust person list/detail/create permissions for the instructor with a type restriction.
- Fix the static JavaScript of the instructor home for the controls that are already rendered.
- Update the view/product tests.

## Out of scope
- A new schema for the order's representative/salesperson.
- A commission report per sale made by the instructor.
- Editing/deleting students by the instructor.
- Stock control by the instructor.
- Changes to the external payment flow beyond keeping authorization for an order created in the session.
- Email notification.

## Impacted files
- `docs/prd/PRD-014-admin-panel-as-portal-persona.md`
- `system/constants.py`
- `system/selectors/person_selectors.py`
- `system/selectors/__init__.py`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/person_views.py`
- `system/views/product_views.py`
- `templates/base.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/products/product_store.html`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `static/system/js/home/instructor-dashboard.js`
- `system/tests/test_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_calendar.py`

## Risks and edge cases
- A back-office person with no classes must see the same base as the instructor, with an empty state in `Aulas do dia` (`Today's classes`).
- A back-office member assigned as class support must be able to use the same class actions, respecting the service's ownership rules.
- The instructor must not have hidden links as the only permission barrier; the views need to block server-side.
- A material order for a selected student must authorize the checkout through the session so a third party's order is not exposed without context.
- A duplicate pre-order for the selected student must remain idempotent through the existing service.
- A technical master with no `portal_person` must not be treated as a material buyer.

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
- [x] 2. Contracts and modeling
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
The embedded browser was reloaded at `http://localhost:8000/home/administrative/` and headless Playwright ran in a `1366x900` viewport.

- `Painel administrativo` (`Administrative panel`): 1 occurrence.
- `Aulas do dia` (`Today's classes`): 1 occurrence.
- `Área administrativa` (`Administrative area`): present.
- `Controle de estoque` (`Stock control`): present.
- `Cronograma` (`Schedule`): present.
- `http://127.0.0.1:8000/home/admin/` with a back-office user returned `403`, keeping the master separate.
- Page console: no errors.

### Mobile
The embedded browser in a narrow viewport and headless Playwright in a `390x844` mobile viewport validated:

- `http://localhost:8000/home/instructor/` with `Apoio operacional` (`Operational support`), `Solicitar material` (`Request material`), `Cadastrar aluno` (`Register student`), `Visualizar alunos` (`View students`), and `Cronograma` (`Schedule`).
- `Controle financeiro` (`Financial control`) does not appear for the instructor.
- `http://localhost:8000/store/` shows `Solicitar para` (`Request for`) with a recipient selector.
- The selector accepted switching from `Layon Quirino · Professor` to `Aluno PIX Pago Masculino · Aluno`.
- Mobile Playwright found 10 options in the recipient selector.

### Browser console
No critical JavaScript errors on the screens:

- `home/administrative/`
- `home/instructor/`
- `store/`
- `people/`
- `people/create/`
- `home/admin/` returning 403 for a back-office user
- `products/`
- `admin-calendar/`
- Desktop Playwright logged `Failed to load resource: 403 (Forbidden)` only on the intentional navigation to `/home/admin/` with a back-office user. No critical JavaScript error on the valid routes.

### Terminal
`read_thread_terminal` did not find a terminal session attached to the thread. The local route responded over HTTP at `127.0.0.1:8000` with status 200.

## ORM validation
### Database
No schema change and no new migration.

### Shell checks
- `PortalAccount` with CPF `900.000.000-07`: `Administrativo Teste`, type `administrative-assistant`, active.
- Active instructors found in the seed: `Layon Quirino`, `Vinicius Antonio`, `Lauro Viana`, `Andre Oliveira`, `Vanessa Ferro`.
- Active students found for material selection, including `Aluno PIX Pago Masculino`.

### Flow integrity
- A back-office user enters `home/administrative/` and does not enter `home/admin/` (`403 Forbidden`).
- The instructor enters `home/instructor/` and reaches `store/`, `people/`, and `people/create/`.
- The registration form opened by an instructor limits `person_type` to `Aluno` (`Student`) and `Dependente` (`Dependent`).
- The instructor's person list does not render `Editar` (`Edit`), `Excluir` (`Delete`), or the financial block.

## Quality validation
### No hardcoding
OK. Role rules were centralized in constants and selectors.

### No brittle conditional structures
OK. Server-side permissions were concentrated in mixins/selectors and context flags.

### No `except: pass`
OK. No `except: pass` introduced.

### No error masking
OK. An invalid material recipient returns an explicit message and a safe redirect.

### No unnecessary comments or docstrings
OK. The new code was kept free of narrative comments.

## Evidence
- Red: the focused tests failed before the implementation for the back-office home, the master block, the instructor's operational area, and the materials shop for instructor/back office.
- Focused Green: `manage.py test system.tests.test_views.PortalViewTestCase.test_administrative_portal_account_dashboard_exposes_shortcuts ... --verbosity 2` with 4 tests OK.
- Focused Green: `manage.py test system.tests.test_product_views.ProductViewTestCase.test_instructor_product_store_exposes_student_recipient_choices ... --verbosity 2` with 4 tests OK.
- Full suite: `manage.py test --verbosity 2` ran 305 tests in 42.854s with OK.
- `manage.py check`: no issues.
- `manage.py showmigrations system`: `system` still has only `0001_initial` applied.
- `manage.py collectstatic --noinput`: completed, 0 files copied and 165 unchanged in the final run.
- Browser: real functional validation on the homes, the shop, the person list/registration, stock, and the schedule.
- Headless Playwright: desktop `1366x900` for the back-office/blocked master and mobile `390x844` for the instructor/shop.

## Implemented
- `AdminHomeView` now requires a technical/master session.
- `AdministrativeHomeView` reuses the instructor dashboard base and renders an administrative area below.
- `InstructorHomeView` gained a limited operational area.
- The materials shop lets an instructor/back-office member select an active recipient.
- Checkout and pre-order record the order for the selected student/dependent when authorized.
- The instructor can list, view, and open a student/dependent registration form, without editing/deleting/administrative finance.
- The instructor's schedule routes accept the authorized class team.
- `static/system/js/home/instructor-dashboard.js` was created for the script the template already referenced.

## Deviations from plan
- During manual validation the incorrect URL `/calendar/admin/` was tried; the system's real route is `/admin-calendar/`, validated afterwards with no error.
- The first headless Playwright run inside the sandbox failed with `WinError 5`; it was re-run outside the sandbox with approval. The first `<option>` selection by `label` failed due to whitespace normalization; it was revalidated by the option's real `value`.
- The worktree already contained many unrelated changes; they were preserved.

## Pending
- No known functional pending items in this scope.
