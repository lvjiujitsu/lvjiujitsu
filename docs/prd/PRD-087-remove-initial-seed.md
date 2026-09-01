# PRD-087: Remove inicial_seed

## Summary of the implementation
Remove the `inicial_seed` aggregator command and replace its dependency in `inicial_seed_test` with an explicit sequence of granular commands.

## Demand type
Seed governance refactoring.

## Current problem
`inicial_seed` concentrates several responsibilities and hides the real order of the system's initial load. Besides that, `inicial_seed_test` depends on that aggregator, so removing only the file would leave the test command broken.

## Goal
Eliminate the `inicial_seed` command as an entry point and record the correct execution sequence of the initial seeds without breaking the manual test setup.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_person_type.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/seed_test_personas.py`
- `system/management/commands/seed_person_administrative.py`
- `system/tests/test_commands.py`
- `system/services/seeding.py`

### Adjacent files consulted
- `README.md`
- the command listing in `system/management/commands/`
- the existing PRDs in `docs/prd/`

### Internet / official documentation
- Not applicable. The change uses Django commands that already exist in the project.

### MCPs / tools verified
- PowerShell — OK — `Get-Location`, `Get-Content`, `Get-ChildItem`
- The `.venv` Python — OK — `.\.venv\Scripts\python.exe --version`
- Django management — OK — `manage.py help inicial_seed`
- Git — OK — `git status --short`, `git diff`

### Limitations found
- `rg` failed with access denied in this environment; it was replaced by PowerShell.
- The worktree already had many unrelated changes; the change must be minimal and preserve the current state.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT with services.

### Action
Remove `inicial_seed` and adjust the live points that depend on it, without changing the granular seeds' internal implementation yet.

### Context
The project needs to migrate from an aggregating initial seed to an explicit sequence of independent seeds. This first stage removes the `inicial_seed` umbrella and documents the operational order.

### Constraints
- no hardcoded secrets
- no error masking
- no migrations
- mandatory full reading
- mandatory validation
- do not revert the worktree's pre-existing changes

### Acceptance criteria
- [ ] `manage.py help inicial_seed` must not find the command.
- [ ] `inicial_seed_test` must not call `inicial_seed`.
- [ ] `inicial_seed_test` must call an explicit sequence of granular seeds.
- [ ] `CLAUDE.md` must stop documenting `inicial_seed` as a real command.
- [ ] The recommended sequence of initial seeds must be documented.

### Expected evidence
- a specific test failing before the implementation
- the specific test passing after the implementation
- `manage.py check` with no errors
- `manage.py help inicial_seed` returning an unknown command

### Output format
Implemented code + tests + validation evidence + the correct execution sequence.

## Scope
- Remove `system/management/commands/inicial_seed.py`.
- Update `system/management/commands/inicial_seed_test.py`.
- Add governance tests for the seed commands.
- Update `CLAUDE.md`.

## Out of scope
- Refactoring `system/services/seeding.py`.
- Making `seed_class_catalog` internally isolated.
- Creating new granular seeds.
- Changing the schema or creating migrations.

## Impacted files
- `docs/prd/PRD-087-remove-initial-seed.md`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Risks and edge cases
- `inicial_seed_test` may break if it keeps calling the removed command.
- The documentation may end up divergent if `CLAUDE.md` still lists `inicial_seed`.
- The seeds are still not fully independent internally; that risk remains for the next stage.

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
Not applicable.

### Mobile
Not applicable.

### Browser console
Not applicable.

### Terminal
Validate through the Django commands.

## ORM validation
### Database
There is no schema change and no need for a permanent write at this stage.

### Shell checks
Not applicable to removing the command.

### Flow integrity
Validate that `inicial_seed_test` uses granular commands.

## Quality validation
### No hardcoding
No secret or variable configuration will be introduced.

### No brittle conditional structures
Not applicable.

### No `except: pass`
Do not introduce any.

### No error masking
The removed command must fail explicitly as an unknown command.

### No unnecessary comments or docstrings
Do not add code comments.

## Evidence
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` failed with 2 expected failures before the implementation.
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` passed with 2 tests.
- `.\.venv\Scripts\python.exe manage.py help inicial_seed` returned `Unknown command: 'inicial_seed'. Did you mean inicial_seed_test?`.
- `.\.venv\Scripts\python.exe manage.py help inicial_seed_test` returned the command's valid help.
- `.\.venv\Scripts\python.exe manage.py check` returned `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\python.exe manage.py showmigrations` showed `system [X] 0001_initial`, with no new migration.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` ran 314 tests with `OK`.
- The temporary test artifact `cleanup-artifacts-0jwsat8s` removed after the validation.

## Implemented
- `system/management/commands/inicial_seed.py` removed.
- `inicial_seed_test` updated to call the granular seeds explicitly.
- Governance tests added to prevent `inicial_seed` from returning.
- `CLAUDE.md` updated with the explicit operational sequence.

## Deviations from plan
- None.

## Pending
- Later, refactor the internal seeds so each command has a single responsibility.
