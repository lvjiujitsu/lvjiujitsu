# PRD-017: Auditable granular seeds

## Summary of the implementation
Split the seeds that currently perform multiple domain writes and improve the audit logs so they explicitly list what each command created or updated.

## Demand type
Seed governance refactoring.

## Current problem
Some seeds still bundle responsibilities:

- `seed_belts` creates belts and graduation rules.
- `seed_class_catalog` calls other seeds, creates instructors, creates classes and schedules, and configures payouts.
- `seed_products` creates product categories, products, and variants.
- `seed_plans` reports only a total count.
- `seed_holidays` reports only a total count.

This prevents visual auditing during a local reset and makes the real startup sequence less predictable.

## Goal
Each seed must act only on its own objective and must print logs sufficient for manual auditing while bringing the system up.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/management/commands/seed_person_type.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_test_personas.py`
- `system/management/commands/seed_person_administrative.py`
- `system/tests/test_commands.py`
- `system/tests/test_class_catalog.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_models.py`
- `system/tests/test_product_models.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/test_plan_models.py`
- `system/models/category.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/class_membership.py`
- `system/models/graduation.py`
- `system/models/product.py`
- `system/models/plan.py`
- `system/models/calendar.py`
- `system/models/person.py`
- `system/models/__init__.py`
- `system/constants.py`

### Adjacent files consulted
- `system/services/registration.py`
- the existing commands in `system/management/commands/`
- the existing PRDs in `docs/prd/`

### Internet / official documentation
- Not applicable. The demand is internal governance of Django commands that already exist.

### MCPs / tools verified
- PowerShell — OK — file reading and Git status.
- The `.venv` Python — OK — `.\.venv\Scripts\python.exe --version`.
- Django management — OK — `manage.py help seed_belts`.
- Git — OK — `git status --short`.

### Limitations found
- The worktree already carries many pre-existing changes. The implementation must preserve that state and change only the necessary files.
- `seed_test_personas` is still a manual-validation seed; the base sequence must be granular, and the test command may keep orchestrating manual scenarios.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT with services.

### Action
Split the base seeds into granular commands and audit the output of each one.

### Context
The local reset now runs the seeds one by one. Each command has to make clear what it did, without running another seed underneath.

### Constraints
- no hardcoded secrets
- no error masking
- no migrations
- mandatory full reading
- mandatory validation
- do not revert the worktree's pre-existing changes

### Acceptance criteria
- [x] `seed_belts` must create only belts, with no graduation rules.
- [x] `seed_graduation_rules` must create only graduation rules and require belts to already exist.
- [x] `seed_class_categories` must create only class categories.
- [x] `seed_ibjjf_age_categories` must create only IBJJF age categories.
- [x] `seed_official_instructors` must create the official instructors and their portal accounts.
- [x] `seed_class_catalog` must not call any other seed and must list the classes, instructors, and linked schedules.
- [x] `seed_teacher_payroll_configs` must configure payouts separately from the class catalog.
- [x] `seed_product_categories` must create only product categories.
- [x] `seed_products` must require existing categories, create products/variants, and list the products.
- [x] `seed_plans` must list the registered plans.
- [x] `seed_holidays` must list the registered holidays.
- [x] `inicial_seed_test` must reflect the granular sequence.
- [x] `CLAUDE.md` must document the real startup sequence.

### Expected evidence
- Red tests failing before the implementation
- Green tests passing after the implementation
- `manage.py check` with no errors
- `manage.py test --verbosity 2` with no failures
- observable execution of the main commands with no stack traces

### Output format
Implemented code + tests + validation evidence + the correct execution sequence.

## Scope
- The seed services in `system/services/seeding.py`.
- The Django commands in `system/management/commands/`.
- Command and service tests.
- Operational documentation in `CLAUDE.md`.

## Out of scope
- Changing the schema.
- Creating migrations.
- Changing the UI.
- Changing the seeds' business data, apart from the separation of responsibilities and the logs.

## Impacted files
- `docs/prd/PRD-017-verifiable-granular-seeds.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_class_categories.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_graduation_rules.py`
- `system/management/commands/seed_ibjjf_age_categories.py`
- `system/management/commands/seed_official_instructors.py`
- `system/management/commands/seed_product_categories.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/seed_teacher_payroll_configs.py`
- new granular seed commands
- `system/tests/test_commands.py`
- `system/tests/test_class_catalog.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_models.py`
- `system/tests/test_product_models.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/seed_helpers.py`

## Risks and edge cases
- Dependent commands may fail when run out of order; the failure must be explicit.
- `seed_test_personas` depends on an already-seeded base and must keep working in the manual validation flow.
- Logs that are too short hinder auditing; excessively nested logs are hard to read in the terminal.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoded secrets
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
Not applicable.

### Mobile
Not applicable.

### Browser console
Not applicable.

### Terminal
Validate through management commands.

## ORM validation
### Database
Validate in the test database and, where safe, through idempotent commands.

### Shell checks
Not required for this stage.

### Flow integrity
The base sequence must work with no hidden command.

## Quality validation
### No hardcoding
Do not introduce secrets or credentials.

### No brittle conditional structures
Prerequisites must be validated by an explicit helper.

### No `except: pass`
Do not introduce any.

### No error masking
Seeds run out of order must fail with an explicit message.

### No unnecessary comments or docstrings
Do not add unnecessary code comments.

## Evidence
- Red observed: `manage.py test system.tests.test_commands.SeedAuditLogCommandTestCase system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` failed before the implementation because the new commands did not exist and the seeds still bundled responsibilities.
- Partial Green: `manage.py test system.tests.test_commands.SeedAuditLogCommandTestCase system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` passed with 15 tests.
- Green on the affected regression: `manage.py test system.tests.test_commands system.tests.test_class_catalog system.tests.test_class_portal_views system.tests.test_forms system.tests.test_graduation.GraduationSeedTestCase system.tests.test_graduation.InitialGraduationRegistrationTestCase system.tests.test_graduation.TestPersonaInitialGraduationTestCase system.tests.test_models system.tests.test_product_models.SeedProductsTestCase system.tests.test_services system.tests.test_views --verbosity 2` passed with 153 tests.
- Full suite: `manage.py test --verbosity 2` passed with 329 tests.
- Django check: `manage.py check` returned `System check identified no issues (0 silenced).`
- Migrations: `manage.py showmigrations` confirmed `system.0001_initial` applied with no new migrations.
- Cleanup: removed 15 temporary `cleanup-artifacts-*` directories created by the suite.

## Implemented
- Removed the graduation rules responsibility from `seed_belts`.
- Created `seed_graduation_rules` for graduation rules.
- Created separate commands for class categories, IBJJF age categories, official instructors, instructor payouts, and product categories.
- `seed_class_catalog` now requires prerequisites and creates only classes/schedules.
- `seed_products` now requires existing categories and creates only products/variants.
- The audit logs now list classes, instructors, schedules, payouts, categories, products, plans, and holidays.
- Legacy tests that need the complete catalog now use an explicit dependency helper.
- `CLAUDE.md` now documents the correct granular sequence.

## Deviations from plan
- No scope deviation. No migrations were created.

## Pending
- No technical pending items identified in this delivery.
