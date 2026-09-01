# PRD-032: Instructor payout seed

## Summary of the implementation
Implement `seed_system_initial_teacher_payroll_configs` to create the initial payout configurations in `TeacherPayrollConfig`, loading data from `static/initial_data/seed_system_initial_teacher_payroll_configs.json`.

## Demand type
Targeted fix.

## Current problem
`teacher_payroll_configs.json` exists, but there is no active command consuming that file. The old JSON uses `class_group_code`, a field removed from the `ClassGroup` model.

## Goal
Create an idempotent seed for instructor payouts using the current keys and without depending on `ClassGroup.code`.

## Context Ledger
### Files read in full
- `system/models/asaas.py`
- `system/models/class_group.py`
- `system/models/category.py`
- `system/models/class_membership.py`
- `system/services/payroll_rules.py`
- `static/initial_data/teacher_payroll_configs.json`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Adjacent files consulted
- `CLAUDE.md`
- `system/tests/test_services.py`
- `system/management/commands/`
- `docs/prd/PRD-031-standardize-seed-json-files.md`

### Internet / official documentation
- Not applicable. An internal change in a Django management command.

### MCPs / tools verified
- PowerShell — OK
- ripgrep — OK
- Django — OK, with the pre-existing full-suite limitation

### Limitations found
- `system/migrations/0001_initial.py` was already changed before this task and will not be touched.
- The full suite already fails on templates/routes outside the scope.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD.

### Action
Implement an atomized seed for instructor payout configurations.

### Context
The financial module computes payouts from `TeacherPayrollConfig`. The rules live as versioned JSON inside `TeacherPayrollConfig.notes`.

### Constraints
- no migrations
- no `--` arguments
- no `ClassGroup.code`
- do not mask a missing dependency
- an idempotent seed

### Acceptance criteria
- [x] `manage.py seed_system_initial_teacher_payroll_configs` exists.
- [x] The seed reads `seed_system_initial_teacher_payroll_configs.json`.
- [x] The seed fails with a clear `CommandError` when the instructor, category, or class does not exist.
- [x] The persisted rules use `class_group_id`, not `class_group_code`.
- [x] Running the seed twice does not duplicate configurations.
- [x] The final bootstrap order includes the seed after `seed_system_initial_class_catalog`.

### Expected evidence
- an automated test of the seed
- `manage.py check`
- a real load of the JSON

### Output format
Code + adjusted JSON + tests + the final command order.

## Scope
- Create the command in `system/management/commands/`.
- Rename/adjust the JSON.
- Update the local documentation.
- Add a focused test.

## Out of scope
- Creating instructor bank accounts.
- Changing the payout calculation.
- Changing models or migrations.

## Impacted files
- `system/management/commands/seed_system_initial_teacher_payroll_configs.py`
- `static/initial_data/seed_system_initial_teacher_payroll_configs.json`
- `system/tests/test_commands.py`
- `CLAUDE.md`
- `docs/prd/PRD-032-instructor-payout-seed.md`

## Risks and edge cases
- `ClassGroup` is resolved by `(class_category__code, main_teacher__cpf)`; multiple records must raise an explicit error.
- Rules scoped as `all` do not need a class.
- Rules scoped as `class_group` require `class_group_category` and `class_group_teacher_cpf`.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no migrations
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. A focused test of the seed
- [x] 4. Implementation of the seed
- [x] 5. Adjustment of the JSON
- [x] 6. Full validation
- [x] 7. Documentation update

## Visual validation
Not applicable.

## ORM validation
### Database
No schema change.
### Shell checks
Run the seed against the test database through the automated test.
### Flow integrity
Confirm the creation of 5 `TeacherPayrollConfig` records.

## Quality validation
### No hardcoding
The payout data lives in the JSON.
### No brittle conditional structures
Class resolution centralized in a helper.
### No `except: pass`
Not allowed.
### No error masking
Missing dependencies raise a `CommandError`.
### No unnecessary comments or docstrings
Do not add superfluous comments.

## Evidence
- `.\.venv\Scripts\python.exe manage.py check` — passed: `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\python.exe manage.py help seed_system_initial_teacher_payroll_configs` — the command is registered.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.TeacherPayrollSeedCommandTestCase --verbosity 2` — passed: 1 test OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` — passed: 5 tests OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — failed with 5 failures and 109 errors, matching pre-existing failures such as `TemplateDoesNotExist: home/student/dashboard.html`, `TemplateDoesNotExist: home/admin/dashboard.html`, and `NoReverseMatch: person-list`.

## Implemented
- Created `seed_system_initial_teacher_payroll_configs`.
- Renamed and adjusted the JSON to `seed_system_initial_teacher_payroll_configs.json`.
- Replaced the old `class_group_code` link with the current link through `class_group_category` + `class_group_teacher_cpf`.
- Rules persisted in `TeacherPayrollConfig.notes` with `class_group_id`.

## Deviations from plan
- None.

## Pending
- Running the full suite still depends on fixes outside this scope, since there are pre-existing template and route failures.
