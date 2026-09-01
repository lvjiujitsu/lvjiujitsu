# PRD-100: The Profiles route versus operational roles

## Summary
Rename and restructure the `Perfis e acessos` (`Profiles and access`) UX to distinguish **relationship types** (`PersonType`) from **cumulative operational roles** (`OperationalRole` / `PersonOperationalRole`), eliminating the confusion that prevents Miguel from "becoming a student" through the profiles screen.

## Demand type
A UX fix + navigation + copy.

## Current problem
- The quick link and the `administracao/perfis/` route list `PersonType` (Student, Instructor, Back office).
- The user reads "profiles" as functions that accumulate per person.
- `PersonType` is global; changing Miguel's type affects the record's semantics, not the enrollment/training.
- The `person_types/*` templates are missing — the screen does not even open today.

## Goal
- **Relationship types:** a restricted CRUD for the global catalog (technical management).
- **The person's roles:** assigned in the person record (PRD-091).
- Unambiguous Brazilian Portuguese navigation and labels; the home's link updated.

## Context Ledger
### Files read in full
- `system/views/person_views.py` (the PersonType* views)
- `templates/home/dashboard.html` (the Profiles quick link)
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Adjacent files consulted
- `system/constants.py`
- `docs/prd/PRD-091-operational-role-ui-on-person-form.md`

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Renaming the public routes requires PRD-075 for English; this PRD can focus on the copy and the initial structure in Portuguese with a future slug.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Miguel's problem + the 2026-06-30 audit.

## Execution prompt
### Persona
Administrative UI product engineer.

### Action
Rename the menus; a relationship types page with a notice; a cross-link to the person's edit screen.

### Context
PRD-091 delivers the roles in the person form.

### Constraints
- Do not remove `PersonType` from the model.
- The old routes redirect with a 301 or a documented alias.

### Acceptance criteria
- [ ] The home's quick link says `Tipos de vínculo` (`Relationship types`) or equivalent, not the ambiguous `Perfis e acessos` (`Profiles and access`).
- [ ] The `/administracao/perfis/` page explains that operational roles are edited in People.
- [ ] Miguel: the operator follows the documented flow — edit the person → classes + roles, without changing the global Student type.
- [ ] The `person_type_list.html` template renders (it can be minimal).
- [ ] The contract test updates the string on the home.

### Expected evidence
- A screenshot of the home + the types list.
- The home hub test updated.

### Output format
The PRD's Evidence.

## Scope
- The copy, minimal person_types templates, and redirect documentation.
- Update `test_admin_hubs_contract.py`.

## Out of scope
- A complete OperationalRole CRUD (a fixed catalog in constants).
- Migrating the URLs to English (PRD-075).

## Impacted files
- `templates/home/dashboard.html`
- `templates/person_types/*` (to create)
- `system/tests/test_admin_hubs_contract.py`
- `docs/UI-SCREEN-CONTRACT.md` (an inventory entry)

## Risks and edge cases
- External links/bookmarks to "Profiles".

## Rules and constraints
- A short approved wireframe.

## Plan
1. [x] The copy and the wireframe.
2. [x] The list template with the callout (reusing the CRUD already delivered in PRD-078).
3. [x] Adjust the home + the tests.

## Test plan
### Tests to author
- Update the `expected_quick_links` label.

### Execution authorization
Local.

### Execution evidence
- `templates/home/dashboard.html`, `system/views/admin_views.py`, and `templates/person_types/person_type_list.html`: the label changed from `Perfis e acessos` (`Profiles and access`) to `Tipos de vínculo` (`Relationship types`), with a description explaining that the cumulative roles (class support, management) are edited in People.
- A callout added at the top of the listing: `Para habilitar apoio de turma, gestão ou outra função em uma pessoa específica, edite o cadastro dela em Pessoas` (`To enable class support, management, or another function for a specific person, edit their record in People`).
- `system/tests/test_home_dashboard.py` and `system/tests/test_admin_hubs_contract.py` updated for the new text.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract system.tests.test_lv_foundation_templates_gap --verbosity 2` — 14 tests OK.

## Visual validation
## Wireframe
### The relationship types list
- The callout: `Para habilitar apoio de turma ou gestão em uma pessoa, edite o cadastro em Pessoas.` (`To enable class support or management for a person, edit their record in People.`)
- The table: the code, the name, the number of people, and the view/edit actions (for a manager).

## ORM validation
- N/A

## Quality validation
- `manage.py check` — 0 problems.

## Evidence
- The routes were already in English since PRD-078 (`/administration/person-types/...`), so the "Follow-up: English slugs" item was already resolved before this PRD.
- The `person_types/*` templates already existed since PRD-078; this PRD only adjusted the copy/label and did not need to create a new CRUD.

## Implemented
- See Execution evidence.

## Cleanup findings
- No residue. No other occurrence of `Perfis e acessos` (`Profiles and access`) in the active code (confirmed through `rg`).

## Follow-up PRDs
- PRD-091 remains responsible for exposing the operational role assignment in the Person form (this PRD only adjusted the navigation/copy, not the assignment itself).

## Deviations from plan
- No deviation. The relationship types CRUD and the migration of the routes to English had already been delivered by PRD-078; this PRD focused exclusively on the copy/navigation, per its original scope.

## Pending
- PRD-091 (assigning operational roles on the People screen) is this copy fix's functional complement.

## Final status
Completed.
