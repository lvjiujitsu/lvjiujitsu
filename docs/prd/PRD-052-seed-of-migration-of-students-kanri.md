# PRD-052: Kanri student migration seed

## Summary of the implementation
Create an idempotent management command to populate the local records from the individual JSON files extracted from Kanri in `static/initial_data/kanri_students_migration/`.

## Demand type
New feature / data migration seed.

## Current problem
The sanitized migration data exists in individual JSON files, but there is still no auditable seed turning it into system records. The local model requires a unique `Person.cpf`, while some of the Kanri files use the guardian's CPF, repeat a CPF across dependents, or have no document at all.

## Goal
Populate people, guardians, dependents, family relationships, and whatever graduation history is possible, preserving traceability and avoiding inventing tuitions, check-ins, or classes without a sufficient contract.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/models/person.py`
- `system/models/graduation.py`
- `system/models/category.py`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/membership.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/utils/person_data.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `system/management/commands/seed_system_initial_belt_ranks.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/tests/test_commands.py`
- `static/initial_data/seed_system_initial_belt_ranks.json`

### Adjacent files consulted
- `static/initial_data/kanri_students_migration/88622-elisa-candido-ungarelli.json`
- `static/initial_data/kanri_students_migration/120166-davi-rodrigues-siqueira.json`
- `static/initial_data/kanri_students_migration_review.json`

### Internet / official documentation
- Not applicable. The implementation follows the local Django management command contracts already present in the repository.

### MCPs / tools verified
- PowerShell — available — file reading and JSON statistics executed.
- Django test runner — to be validated after the implementation.

### Limitations found
- `Person.cpf` is required and unique, but 36 files have no document and there are documents that are repeated or belong to the guardian.
- `Person` has no field for the state (UF); the importable address is limited to the postal code, street, number, complement, neighborhood, and city.
- `Membership` requires a `SubscriptionPlan`; `MembershipInvoice` is tied to Stripe. Kanri's financial entries must not be imported without a plan/gateway mapping.
- `ClassCheckin` requires a `ClassSession` and compatible class/schedule. Kanri's class history must not be imported without a calendar mapping.
- There is at least one file with the address `Carregando...` (`Loading...`); the seed must clear those fields and log a warning.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + auditable seeds.

### Action
Implement a `seed_system_initial_kanri_students_migration` seed that reads the individual Kanri migration JSON files and creates/updates people, guardians, dependents, relationships, and graduations.

### Context
The migration must preserve as much of the Kanri records as possible without corrupting documents, without creating financial data or check-ins with no contract, and without requiring a schema migration.

### Constraints
- No migrations.
- No `--` arguments in the seed.
- No `PortalAccount` creation, since the JSON files have no password.
- No creation of tuitions, invoices, classes, enrollments, or check-ins.
- No `except: pass`.
- Do not mask problematic documents: use the deterministic identifier `KANRI-<code>` only when the student's CPF is missing, duplicated, or is the guardian's CPF, logging a warning.
- Address data containing `Carregando...` (`Loading...`) must be discarded field by field and logged.

### Acceptance criteria
- [ ] The seed fails with a clear `CommandError` when the `student`, `guardian`, or `dependent` types do not exist.
- [ ] The seed fails with a clear `CommandError` when the required belts do not exist.
- [ ] When importing a student with their own valid CPF, it creates/updates a `Person` of type `student`.
- [ ] When importing a student with a documented guardian, it creates/updates the guardian as a `guardian`, the student as a `dependent`, and a `responsible_for` relationship.
- [ ] When the student's document is missing, duplicated, or equal to the guardian's CPF, the seed uses `KANRI-<code>` in the student's/dependent's `cpf` field and logs a warning.
- [ ] A repeated run does not duplicate `Person`, `PersonRelationship`, or `Graduation`.
- [ ] The Kanri belt progression generates a `Graduation` when the belt is mappable to a `BeltRank`.
- [ ] An address with the placeholder `Carregando...` (`Loading...`) is not written literally.
- [ ] The financial history and the class history are counted in the log as not imported due to the lack of a safe contract.

### Expected evidence
- A targeted automated test passing.
- `manage.py check` passing.
- The absence of a new migration.

### Output format
Implemented code + tests + an updated PRD/documentation + validation evidence.

## Scope
- Create the seed management command.
- Create automated tests focused on idempotency, the guardian/dependent relationship, the migration substitute CPF, placeholder cleanup, and graduation.
- Update `CLAUDE.md` with the real new command.

## Out of scope
- Re-extracting the data from Kanri.
- Creating portal accounts.
- Creating classes, enrollments, sessions, check-ins, tuitions, invoices, or payments.
- Manually fixing problematic JSON files.
- Changing the schema.

## Impacted files
- `docs/prd/PRD-052-seed-of-migration-of-students-kanri.md`
- `system/management/commands/seed_system_initial_kanri_students_migration.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Risks and edge cases
- Students carrying a parent's CPF may be imported with the identifier `KANRI-<code>` until a manual review.
- An existing person with the same CPF and a different operational type must not be silently overwritten.
- A kids belt must go into `Graduation`, but `Person.jiu_jitsu_belt` accepts only adult choices.
- The financial and attendance data stay out of the database to avoid false consistency.

## Rules and constraints
- SDD before code.
- TDD for the implementation.
- No hardcoded credentials.
- No error masking.
- No migrations.
- Mandatory full reading.
- Mandatory validation.

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
Not applicable; a seed with no UI.

### Mobile
Not applicable; a seed with no UI.

### Browser console
Not applicable; a seed with no UI.

### Terminal
Run the targeted test and `manage.py check`.

## ORM validation
### Database
Validate through Django tests with a temporary database.

### Shell checks
Not necessary when the tests cover the counts and relationships.

### Flow integrity
The seed must be idempotent and transactional.

## Quality validation
### No hardcoding
No credentials or fixed personal data outside the JSON files.

### No brittle conditional structures
The belt and document mappings are centralized in small functions.

### No `except: pass`
File, JSON, and dependency errors must be explicit.

### No error masking
Records with a problematic document receive a traceable substitute CPF and a warning.

### No unnecessary comments or docstrings
Comments only when needed to explain a migration decision.

## Evidence
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.KanriStudentsMigrationSeedCommandTestCase --verbosity 2 --keepdb` failed because the command did not exist yet.
- Partial Green: the same targeted test passed with 4 tests OK after the implementation.
- Command regression: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2 --keepdb` passed with 11 tests OK.
- Technical check: `.\.venv\Scripts\python.exe manage.py check` passed with 0 issues.
- Migrations: `system/migrations/` contains only `0001_initial.py` and `__init__.py`.
- A transactional simulation with no permanent write against the 199 real JSON files: `257 people created, 15 people updated, 73 relationships created, 675 graduations created, 92 substitute CPFs, 825 financial entries not imported, 10701 class history entries not imported.`

## Implemented
- `seed_system_initial_kanri_students_migration` created.
- The seed reads `static/initial_data/kanri_students_migration/*.json`.
- The seed creates/updates a `Person` for students, guardians, and dependents.
- The seed creates/updates a `PersonRelationship` of guardian-for-dependent.
- The seed creates a `Graduation` from the mappable belt progression.
- The seed uses `KANRI-<code>` when the student's document is missing, duplicated, or represents the guardian's CPF.
- The seed strips `Carregando...` (`Loading...`) placeholders from the address fields.
- The seed audits the financial and class history in the log without creating financial records or check-ins.

## Deviations from plan
- The first test command without `--keepdb` stopped before Red because the `test_postgres` test database already existed and the runner attempted an interactive confirmation. The test was re-run with `--keepdb`, without dropping the database.

## Pending
- A human review of the records that received the substitute CPF `KANRI-<code>`.
- A human review of the financial data and class history, which were not imported due to the lack of a safe plan, invoice, class, and session contract.
