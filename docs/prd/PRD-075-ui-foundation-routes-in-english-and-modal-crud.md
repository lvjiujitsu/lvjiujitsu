# PRD-075: UI foundation, English routes, and modal CRUD

## Summary
Rebuild LV's authenticated foundation so the CRUD modules use canonical English routes, a Brazilian Portuguese interface, and short actions in a modal/dialog on the same screen, following the pattern described in the current contract, without copying an external domain.

## Demand type
A multi-module UI/UX reimplementation + route governance.

## Current problem
- `system/urls.py` uses Portuguese paths for the administrative modules (`pessoas`, `planos`, `administracao`, `turmas`, `financeiro`, `graduacao`, `materiais`), while the current request requires English routes.
- The local inventory found 49 `template_name` entries in views and 36 missing templates.
- `templates/lv/base.html`, `templates/lv/modal_base.html`, `templates/lv/modal_done.html`, `static/system/css/lv/base.css`, `static/system/js/lv/crud_modal.js`, and `crud_frame.js` do not exist.
- `PersonCreateView`, `PersonUpdateView`, and `PersonDetailView` point at non-existent modal templates.
- The existing People/Home/Plans templates are standalone HTML, with an inline theme and scripts, out of line with the shared foundation required.
- PRD-066 declares part of the foundation as delivered, but the current code does not contain the files.

## Goal
- Create a single authenticated shell and a reusable modal foundation.
- Define canonical English routes with URL names already in English.
- Keep the frontend's labels and messages in Brazilian Portuguese.
- Implement short CRUD in a modal/dialog for People as the reference.
- Prepare the replication for Plans, Classes, Materials, Finance, and Graduation.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-066-visual-and-modal-crud-pattern.md`
- `docs/prd/PRD-068-clean-people-rework-and-lv-foundation.md`
- `docs/prd/PRD-065-administrative-hubs-of-the-lv-modules.md`
- `system/urls.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `static/system/css/people/people.css`
- `templates/home/dashboard.html`

### Adjacent files consulted
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`

### Internet / official documentation
- Django 5.2 templates: https://docs.djangoproject.com/en/5.2/topics/templates/
- Django 5.2 class-based auth/access docs: https://docs.djangoproject.com/en/5.2/topics/auth/default/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: templates and access mixins.
- The internal browser not used yet, because there was no visual change at this stage.

### Limitations found
- Several views point at missing templates; validating every module visually requires a phased implementation.
- The old Portuguese routes may need temporary redirects so existing links do not break.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: English routes, a Portuguese frontend, and a flow with no redirect to a new screen and with a popup/modal.

## Visual hierarchy
- The shell: a compact topbar with the logo, permission-based navigation, the theme toggle, and logout.
- The content: an operational header, filters, a dense list, and iconic actions.
- The CRUD modal: a header with context, a server-rendered body, and clear actions.
- Mobile: one column, 44x44 actions, and an almost full-screen modal with no horizontal overflow.

## Wireframe
### Region: The shell
- The LV logo on the left.
- Navigation across the permitted modules.
- The theme and the user on the right.

### Region: The hub/list
- The module's eyebrow.
- The title in Brazilian Portuguese.
- An iconic/textual primary action when permitted.
- Filters before the list.
- An operational list/card with the actions: view, edit, delete.

### Region: The modal
- The title and a close button.
- A form or a detail view.
- Cancel/save or a destructive confirmation.

### Screen states
- `empty`, `populated`, `filtered`, `modal-open`, `submitting`, `success`, `error`, `forbidden`.

## State machine
- The CRUD modal: `closed -> open -> submitting -> success|error`.
- Delete confirmation: `closed -> confirmable -> submitting -> success|blocked`.
- Route compatibility: `old-portuguese-path -> redirect/query modal` only when necessary during the transition.

## Scope
- Create the `templates/lv/*`, `static/system/css/lv/base.css`, and `static/system/js/lv/*` foundation.
- Migrate People to the base + modal CRUD as the reference.
- Create redirects or aliases for the old routes when necessary.
- Write real rendering tests for the existing templates.
- Update the `?v=` of the changed assets.

## Out of scope
- Implementing every module's CRUD in this same PRD; that belongs to PRD-077.
- Changing the role/capability rules; that belongs to PRD-074.

## Impacted files
- `system/urls.py`
- `system/views/person_views.py`
- `templates/lv/*`
- `templates/people/*`
- `static/system/css/lv/base.css`
- `static/system/js/lv/theme.js`
- `static/system/js/lv/crud_modal.js`
- `static/system/js/lv/crud_frame.js`
- rendering/route tests

## Risks and edge cases
- English routes may break historical links without a controlled transition.
- The iframe modal needs a safe `X-Frame-Options` and the same origin.
- An invalid POST must reopen the modal with per-field errors.
- Permissions must be validated in the backend, not merely hidden.

## Rules and constraints
- The UI in Brazilian Portuguese.
- The code, technical names, and canonical routes in English.
- No inline behavioral JavaScript.
- No `innerHTML` with user data.
- Do not edit `staticfiles/`.

## Plan
- [x] Write an inventory/real-rendering test for the People routes.
- [x] Create the shared foundation (`templates/lv/*`, `static/system/css/lv/base.css`, `static/system/js/lv/*`).
- [x] Migrate People to the modal CRUD (create/edit in a modal iframe; the detail keeps a dedicated page, an exception documented because it concentrates finance/graduation).
- [x] Add canonical English routes (`/people/...`) with a compatibility redirect from the old Portuguese routes (`/pessoas/...`).
- [x] Validate desktop/mobile/light/dark in the internal browser.
- [ ] Replicate the pattern for the remaining modules (Plans, Classes, Materials, Finance, Graduation) — PRD-077's scope.

## Test plan
### Tests to author
- Each canonical People route renders 200 for a permitted profile.
- The old routes redirect to the canonical ones.
- The `?modal=1` modal renders the modal template; a valid POST renders `lv/modal_done.html` and persists to the database.

### Execution authorization
Authorized locally.

### Execution evidence
- The new file `system/tests/test_lv_foundation_people.py` with 8 tests: the English route renders, 3 redirects from the old routes, the create/edit/view modal renders the correct modal template, and a valid POST in the modal creates the person and renders `lv/modal_done.html`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_people --verbosity 2` — 8 tests OK (a real Red before: an invalid CPF/biological sex in the test data; a real Green after fixing the data).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 275 tests OK (the full suite, with no regression).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Run in the internal browser at `http://localhost:8000/people/` logged in as a technical admin:
- Desktop, dark theme: the list renders with Detail/Edit/Delete buttons; the create modal opens in a `<dialog>` with an iframe, in the same theme; the POST creates the person without navigating away (7→8 people) and closes itself through `postMessage`.
- Editing in the modal pre-fills the fields correctly.
- Deletion through a confirmation `<dialog>` with the person's dynamic name; the real POST deletes and shows a success message, without navigating to a separate confirmation page.
- Light theme: the modal and the shell consistent.
- Mobile (375×812): no horizontal overflow (`scrollWidth === innerWidth`); the modal takes almost the full screen, anchored to the bottom.
- A real bug found and fixed during the validation: `.crud-modal__frame { height: min(85vh, 100%) }` at the mobile breakpoint collapsed to 150px (the default height of an iframe with no resolved size, because the `<dialog>` has no height of its own for the `100%` to reference). Fixed to `height: 80vh` (a viewport unit, not dependent on the parent).
- Also fixed during the validation: a leftover Python process from an earlier session was stuck on port 8000 serving outdated templates; documented here so the next agent does not lose time on the same symptom — always kill the processes on the port before validating visually.

## ORM validation
Real data from the local development database (the seeds already applied); a test person created through the modal (`529.982.247-25` / `390.533.447-05`) and removed at the end of the validation.

## Quality validation
- `manage.py check`
- `manage.py test system.tests.test_lv_foundation_people` and the complete `manage.py test system`
- The internal browser (desktop, mobile, light, dark)

## Evidence
- The `template_name -> exists` inventory returned 36 missing templates (it remains valid for the modules not yet migrated; see PRD-078).
- `templates/lv/*` and `static/system/js/lv/*` did not exist before this run.
- `templates/people/person_list.html` and `person_form.html` contained an inline theme and JavaScript (fixed for People in this PRD; the other modules go to PRD-084).
- `system/urls.py` contained Portuguese paths for People (fixed in this PRD; the other modules go to PRD-077/078).

## Implemented
- `static/system/css/lv/base.css`: shared tokens + the CRUD modal shell (`dialog.crud-modal`, `.confirm-delete-dialog`, `.modal-frame`).
- `static/system/js/lv/theme_boot.js`, `theme_toggle.js`, `crud_modal.js`, `modal_child.js`, `confirm_delete.js`: no inline JavaScript, with parent/iframe communication through `postMessage` restricted to the same origin.
- `templates/lv/modal_frame.html` and `templates/lv/modal_done.html`: the reusable modal iframe shell and the completion page.
- `templates/people/person_form_modal.html` and `templates/people/person_detail_modal.html`: the People modal variants.
- `templates/people/person_list.html`: the Create/Edit buttons open a modal through `data-crud-modal-open`; Delete opens a confirmation `<dialog>`; the inline scripts removed.
- `system/urls.py`: the People routes migrated to `/people/...` (English); the old `/pessoas/...` routes become a `RedirectView` to the new ones.
- `system/tests/test_lv_foundation_people.py`: 8 tests covering the routes, the redirects, and the complete modal flow (GET and POST).

## Cleanup findings
- No temporary residue left in the repository (the leftover Python process on port 8000 was from an earlier session, not generated by this work, and it was terminated).
- No unnecessary comment/docstring added.
- Out-of-scope debt remains in PRD-077 (the other modules), PRD-078 (administrative templates still missing), and PRD-084 (tokens/inline styling in the remaining modules).

## Follow-up PRDs
- PRD-077 to replicate the modal/English routes pattern in the other modules.
- PRD-078 for the administrative templates still missing.
- PRD-084 for tokens/inline styling in the modules not yet migrated.

## Deviations from plan
- The person detail (`PersonDetailView`) kept a dedicated page as its primary action (it only created the compact modal template already referenced in the code, with no trigger on the card), because it is a rich screen (finance, graduation, history) — an exception explicitly documented for detail pages that concentrate multiple areas.

## Pending
- Repeat this foundation for Plans, Classes, Materials, Finance, and Graduation (PRD-077).

## Final status
Completed with limitations — the foundation created and the reference module (People) with short CRUD in a modal, English routes, and backward compatibility, tested (8 new tests + the full suite of 275) and validated visually (desktop/mobile, light/dark). The replication for the other modules goes to PRD-077.
