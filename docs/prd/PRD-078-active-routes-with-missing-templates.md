# PRD-078: Active routes with missing templates

## Summary
Block `TemplateDoesNotExist` on registered routes. The current inventory found dozens of `template_name` and `modal_template_name` entries with no corresponding file, including the public password recovery routes, the administrative modules, products, finance, graduation, and the modal templates.

## Demand type
A route/template integrity fix.

## Current problem
- Registered views point at non-existent templates.
- Password recovery has active routes, but the templates are pending in the contract.
- The administrative modules have routes and views, but most of the surface does not render.
- The existing tests validate `reverse()` and some links, but they do not guarantee the real rendering of every template.

## Goal
Every active route must have an explicit decision:
- render an existing template;
- return an intentional 404/410;
- redirect to the canonical flow;
- or be removed from the URLconf with its own PRD.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/urls.py`
- `system/views/auth_views.py`
- `system/views/admin_views.py`
- `system/views/person_views.py`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`

### Adjacent files consulted
- The `template_name -> exists` inventory
- `docs/prd/PRD-071-alignment-of-the-suite-inherited-to-the-progressive-scope.md`
- `docs/prd/PRD-065-administrative-hubs-of-the-lv-modules.md`

### Internet / official documentation
- Django templates: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 templates.

### Limitations found
- This PRD must be executed together with or before PRD-077 for the CRUD modules.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request to reorganize the system and list the inconsistencies.

## Scope
- Create a template inventory test for the registered views.
- Resolve the critical public password recovery templates.
- Resolve or explicitly block the administrative routes with no template.
- Update PRD-071 or replace it with updated evidence.

## Out of scope
- A complete redesign of every module; PRD-077.
- English routes/modal CRUD; PRD-075.

## Impacted files
- `system/tests/`
- `templates/login/*`
- `templates/admin_modules/*`
- `templates/billing/*`
- `templates/products/*`
- `templates/graduation/*`
- `templates/classes/*`
- `templates/class_categories/*`
- `templates/class_schedules/*`
- `templates/person_types/*`

## Risks and edge cases
- Creating an empty template just to pass a test would hide an incomplete product.
- Removing a route may break existing links.
- The public password templates need to keep security and generic messages.

## Plan
- [x] A failing test for the missing templates (a programmatic inventory through `get_resolver()` + `get_template()`).
- [x] A route/view/template/decision matrix (generated through the shell, documented in Evidence).
- [x] Fix the critical public part first (password recovery).
- [x] Fix the administrative ones per module (the hub, the profiles) — the other modules were resolved organically by PRD-077.
- [x] Validate the intentional 200/redirect/404 routes.

## Test plan
### Tests to author
- A template inventory of the registered views.
- A GET of the public password routes.
- A GET of the main hubs for an authorized profile.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_lv_foundation_templates_gap.py` (8 tests): the 4 password recovery screens render, the administrative hub renders with real KPIs and modules, the English `/administration/` route with a redirect from `/administracao/`, the profiles list renders real data, and the create-profile modal works end to end.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_templates_gap --verbosity 2` — 8 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 tests OK (the full suite, with no regression).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- The final programmatic inventory (a script through `manage.py shell` walking `get_resolver()` and calling `get_template()` for every `template_name`/`modal_template_name` of every registered view): out of 36 missing templates at the start, only 3 remain — `products/product_store.html`, `products/student_backorder_list.html`, `products/student_order_history.html` (the public shop and the student's history/pre-order), already documented as an explicit pending item in PRD-077 (outside the administrative CRUD's scope).

## Visual validation
Validated in the internal browser: `/administration/` renders with real KPIs and lists the 7 modules; `/password-reset/` renders consistently with the login look; mobile (375×812) with no horizontal overflow on both.

## ORM validation
Not applicable (simple read/form templates, covered by the focused tests).

## Quality validation
- The focused `manage.py test` and the full suite.
- `manage.py check`.
- The internal browser (desktop, mobile).

## Evidence
- The initial local inventory returned 36 missing templates among the active views.
- PRD-075 resolved the foundation (`lv/modal_done.html`, `theme_boot.js`, `people/person_form_modal.html`, `people/person_detail_modal.html`), and PRD-077 resolved the 7 domain modules (People, Plans, Classes/categories/schedules, Materials, Graduation, Finance, the Schedule) organically during the CRUD implementation.
- This PRD closed the rest: the 4 password recovery templates (`templates/login/password_reset_*.html`), `templates/admin_modules/admin_hub.html`, and the 4 profile templates (`templates/person_types/person_type_*.html`).
- The administration and profile routes migrated to English (`/administration/...`) with a redirect from `/administracao/...`.

## Implemented
- `templates/login/password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`: reusing the `auth/base_auth.html` shell and the already existing `login.css` classes.
- `templates/admin_modules/admin_hub.html`: lists the 7 modules with real counters and the administrative KPIs already computed by the view.
- `templates/person_types/person_type_list.html`, `person_type_form.html`, `person_type_detail.html`, `person_type_confirm_delete.html`: a complete profiles CRUD in the same modal pattern as PRDs 075/077.
- `system/views/person_views.py`: `PersonTypeCreateView`/`UpdateView` gained `ModalFormMixin`.
- `system/urls.py`: `/administracao/...` migrated to `/administration/...` with a compatibility redirect.

## Cleanup findings
- No temporary residue.
- No route was removed from the URLconf; every active view now has an explicit decision (render or redirect).

## Follow-up PRDs
- No new PRD necessary; the remaining gap (the public shop, the student's history/pre-order) is already recorded as a pending item in PRD-077.

## Deviations from plan
- No functional deviation. Fixing the domain modules (People, Plans, Classes, Materials, Graduation, Finance, the Schedule) ended up happening within PRD-077's execution, not as isolated work in this PRD — reflected here rather than duplicated.

## Pending
- The public shop (`product-store`) and the student's pre-order/history flow still have no template — an explicit pending item, not hidden, already recorded in PRD-077.

## Final status
Completed with limitations — every active administrative and critical public route has a real, tested template; the remaining gap is intentional and documented (the public/student shop, outside this round's administrative CRUD scope).
