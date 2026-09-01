# PRD-073: Administrative seeds and a consistent bootstrap

## Summary
Fix the order and atomicity of the initial seeds that create instructors, back-office staff, and training links. The reported error (`ClassCategory matching query does not exist`) happens because `seed_system_initial_administrative` tries to synchronize `class_category`, enrollments, and class support before the categories/classes exist in the external command file's cycle.

## Demand type
A local bootstrap fix + seed governance.

## Current problem
- `seed_system_initial_administrative.py` creates the person/portal account and also calls `sync_administrative_training_links`, which requires an existing `ClassCategory` and `ClassGroup`.
- The legacy `seed_system_initial_class_categories_administrative` and `seed_system_initial_class_catalog_administrative` seeds depend on the back-office person already existing; when the main seed fails, both fail with a CPF not found.
- `docs/OPERACAO-BANCO-SEEDS.md` also needs reconciling: the currently documented order still places the instructor links before the instructor is created.

## Goal
Have a reproducible, idempotent, transactional local cycle for the first load:
- categories before links by category;
- instructors before classes;
- classes before administrative training links;
- back-office staff created without leaving partial state when a dependent link is missing;
- the commands and the documentation aligned.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/management/commands/seed_system_initial_class_categories.py`
- `system/management/commands/seed_system_initial_class_categories_administrative.py`
- `system/management/commands/seed_system_initial_class_catalog_administrative.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_class_categories_teacher.py`
- `system/services/administrative_training.py`
- `system/tests/test_commands.py`
- `static/initial_data/initial_administrative.json`

### Adjacent files consulted
- `system/models/person.py`
- `system/models/category.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `docs/prd/PRD-024-atomic-decoupled-seed-governance.md`
- `docs/prd/PRD-031-standardize-seed-json-files.md`

### Internet / official documentation
- Django 5.2 custom management commands: https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `CommandError`, `transaction.atomic`, `call_command`.
- `.venv\Scripts\python.exe manage.py check`: passed, 0 issues.
- The existing tests run: `system.tests.test_admin_hubs_contract`, `system.tests.test_home_dashboard`.

### Limitations found
- `system/migrations/0001_initial.py` was already modified before this cycle, only by a timestamp.
- The Obsidian command file lives outside LV's Git repo; a change to it must be recorded as an external file.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the user's current request, which asked to consistently fix the seed errors and reorganize the system before the final implementation.

## Scope
- Fix the documented order in `docs/OPERACAO-BANCO-SEEDS.md`.
- Fix the external PowerShell command file, if it is kept as the operational source.
- Add focused tests reproducing the ordering failure and the correct cycle.
- Adjust the seeds for clear prerequisite messages and no partial state.

## Out of scope
- Writing to HG, production, or Render.
- Creating remote data.
- Redesigning roles/permissions; that belongs to PRD-074.

## Impacted files
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/tests/test_commands.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/services/administrative_training.py`

## Risks and edge cases
- The current administrative seed bundles person creation with dependent links; a missing dependency must abort with no partially created person.
- A JSON shared by several seeds preserves hidden coupling.
- Reordering with no test may simply move the failure to the instructor, the class, or the payroll.

## Rules and constraints
- Use an explicit `CommandError` for a missing prerequisite.
- Keep `transaction.atomic` for multiple writes.
- Test with an isolated Django database.
- Do not mask exceptions.

## Plan
- [x] Create a test reproducing the failure when the back office runs before the categories/classes.
- [x] Create a test of the correct administrative seed cycle with training links.
- [x] Adjust the documentation and the commands.
- [x] Adjust the seeds' messages/validations when necessary.
- [x] Run the focused test and `manage.py check`.
- [x] Run the cleanup audit.

## Test plan
### Tests to author
- `seed_system_initial_administrative` fails with a clear message when the dependent `ClassCategory`/`ClassGroup` does not exist.
- The correct cycle creates Aline, the portal account, the graduation, the adult enrollments, and the kids support idempotently.
- The legacy administrative seeds stay idempotent after the main seed.

### Execution authorization
Authorized locally by the current request.

### Execution evidence
- A real Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.AdministrativeSeedCommandTestCase --verbosity 2` failed on 2 tests because the messages contained neither `seed_system_initial_class_categories` nor `seed_system_initial_class_catalog`.
- A real Green: the same command passed with 3 tests OK after validating the dependencies before writing.
- Focused regression: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` passed with 23 tests OK.

## Visual validation
Not applicable.

## ORM validation
Validate in the test database and, when necessary, through a read-only local ORM shell after the local seeds.

## Quality validation
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py check`

## Evidence
- `seed_system_initial_administrative.py` calls `sync_administrative_training_links` inside `transaction.atomic`.
- `system/services/administrative_training.py` looks up `ClassCategory.objects.get(code=...)` and `ClassGroup.objects.get(class_category__code=..., main_teacher__cpf=...)`.
- `initial_administrative.json` defines `class_category`, `class_enrollments`, and `class_instructor_assignments` for the CPF `920.000.011-81`.
- The local inventory showed the external order calling the back office before the categories/classes.
- A subagent confirmed that the non-existent CPF in the legacy seeds was a likely consequence of the main seed's rollback.
- `docs/OPERACAO-BANCO-SEEDS.md` had `seed_system_initial_class_categories_teacher` before `seed_system_initial_teacher`; fixed.

## Implemented
- `system/services/administrative_training.py`: explicit validation of the category and the class added, with messages pointing at `seed_system_initial_class_categories` and `seed_system_initial_class_catalog`.
- `system/management/commands/seed_system_initial_administrative.py`: the training dependencies are validated before creating/updating a `Person`.
- `system/tests/test_commands.py`: `AdministrativeSeedCommandTestCase` added, covering missing categories, a missing catalog, and the idempotency of the legacy seeds after the main seed.
- `docs/OPERACAO-BANCO-SEEDS.md`: the reference order fixed.

## Cleanup findings
- The diff reviewed within PRD-073's scope.
- The changed files re-read in full.
- No temporary residue, dead import, or improper scope expansion was found.
- Out-of-scope debt already separated: PRD-074 for cumulative roles/permissions; PRD-079 for duplicate PRDs; PRD-083 for legacy documentation.

## Follow-up PRDs
- PRD-074 for cumulative roles/permissions.

## Deviations from plan
- No functional deviation. The fix also updated the external Obsidian PowerShell file because it was the operational source reproducing the error.

## Pending
- PRD-074 remains pending to fix the cumulative roles model; this PRD does not change permissions.

## Final status
Completed with limitations.
