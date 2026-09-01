# PRD-033: Seed for initial holidays

## Summary of the implementation
Create a granular seed to load the initial 2026 holidays into the `Holiday` model, replacing the old `seed_holidays --year 2026` command without reintroducing command-line arguments.

## Demand type
New feature

## Current problem
The old commit had `seed_holidays --year 2026`, but the current project removed seeds with `--` arguments and has no equivalent command to populate `Holiday`.

## Goal
Provide `python manage.py seed_system_initial_holidays`, idempotent, auditable, and based on its own JSON in `static/initial_data/`.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `system/models/calendar.py`
- `system/tests/test_commands.py`
- `system/management/commands/seed_system_initial_product_categories.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_teacher_payroll_configs.py`

### Adjacent files consulted
- `system/models/__init__.py`
- `static/initial_data/`
- the old `seed_holidays.py` command in the downloaded commit

### Internet / official documentation
- Not applicable; the behavior is derived from the local code and the legacy command.

### MCPs / tools verified
- PowerShell — status ok — file reading and local commands

### Limitations found
- The full suite has pre-existing failures outside the scope in templates/routes.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD.

### Action
Implement the initial holidays seed using JSON and a granular command.

### Context
`Holiday` is used by the calendar/class flows for non-working dates. The seed must restore the legacy command's operational behavior for 2026.

### Constraints
- no `--` arguments
- no migrations
- no hardcoding inside the command
- data in `static/initial_data/seed_system_initial_holidays.json`
- an idempotent seed
- an audit log per record

### Acceptance criteria
- [ ] `python manage.py help seed_system_initial_holidays` registers the command.
- [ ] Running the seed creates the 13 holidays of 2026.
- [ ] Running the seed twice does not duplicate records.
- [ ] The seed updates the name/status when the date already exists.

### Expected evidence
- `python manage.py check`
- `python manage.py test system.tests.test_commands --verbosity 2`

### Output format
Implemented code + tests + validation evidence.

## Scope
- Create the initial holidays JSON.
- Create the `seed_system_initial_holidays` command.
- Cover idempotency in a command test.
- Update the operational documentation.

## Out of scope
- Changing the schema.
- Implementing dynamic per-year holidays through an argument.
- Fixing the full suite's pre-existing failures.

## Impacted files
- `static/initial_data/seed_system_initial_holidays.json`
- `system/management/commands/seed_system_initial_holidays.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Risks and edge cases
- Movable holidays must be explicitly recorded in the JSON per year.
- The legacy command accepted `--without-optional`; the current policy forbids arguments, so the initial set has to be decided in the JSON.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding in the command
- no migrations
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Tests
- [x] 4. Implementation
- [x] 5. Full validation where possible
- [x] 6. Documentation update

## Visual validation
Not applicable; a change with no UI.

## ORM validation
### Database
Validated through a Django test with the test database.

### Shell checks
Not necessary.

### Flow integrity
An idempotent seed through `update_or_create(date=...)`.

## Quality validation
### No hardcoding
The data lives in the JSON; the command only interprets the structure.

### No brittle conditional structures
The command is linear and validated by required fields.

### No `except: pass`
Not introduced.

### No error masking
A missing JSON or an invalid entry raises a `CommandError`.

### No unnecessary comments or docstrings
Not introduced.

## Evidence
- `python manage.py help seed_system_initial_holidays` registered the command with no custom arguments.
- `python manage.py check` passed with `System check identified no issues`.
- `python manage.py test system.tests.test_commands --verbosity 2` passed with 6 tests.

## Implemented
- Created `static/initial_data/seed_system_initial_holidays.json` with the 13 holidays of 2026.
- Created `seed_system_initial_holidays`, idempotent by date and with an audit log per holiday.
- Updated the JSON governance test and the seed's idempotency test.
- Updated `CLAUDE.md` with the new operational command.

## Deviations from plan
- None so far.

## Pending
- The full suite still has pre-existing failures outside this scope, already observed before this seed.
