# PRD-024: Atomic, decoupled seed governance

## Summary of the implementation
Supersede PRD-023 and remove `initial_load`/`seeding` as the official architecture. Seeds become strictly optional, atomic, and isolated from the runtime. Demo/test seeds are no longer called in any "natural" flow (aggregators included). Refactor `seed_product_prices` to use a public helper extracted from `registration_checkout`.

## Demand type
Architectural change / initial data governance.

## Current problem
- The `system/services/initial_load` and `system/services/seeding` packages are part of the official architecture, creating coupling between the runtime and data population.
- Seeds call seeds (internal chains), which breaks atomicity.
- Demo/test seeds create orders/memberships and enter the standard flow through the aggregator.
- `seed_product_prices` uses a private checkout helper.
- Seed flags in settings reinforce an unnecessary architectural dependency.

## Goal
- Remove `initial_load` and `seeding` from the official architecture and from the runtime.
- Keep seeds only as optional, atomic, independent commands.
- Demo/test seeds run only when called explicitly (no aggregators in the natural flow).
- Catalog seeds (products, classes, prices) do not call other seeds; they fail explicitly when dependencies were not run.
- `seed_product_prices` uses a public helper in a shared module.

## Context Ledger
### Files read in full
- AGENTS.md
- CLAUDE.md
- docs/prd/PRD-023-optional-seeds-env-orchestrator-initial-data-in-json.md
- lvjiujitsu/settings.py
- .env.example
- system/services/seeding/__init__.py
- system/services/seeding/bootstrap.py
- system/services/seeding/exceptions.py
- system/services/seeding/plan_price_defaults.py
- system/services/seeding/plans.py
- system/services/seeding/product_price_defaults.py
- system/services/seeding/product_unit_prices.py
- system/services/initial_load/__init__.py
- system/services/initial_load/flags.py
- system/services/initial_load/io.py
- system/services/initial_load/parsers.py
- system/management/commands/seed_class_categories.py
- system/management/commands/seed_ibjjf_age_categories.py
- system/management/commands/seed_belts.py
- system/management/commands/seed_graduation_rules.py
- system/management/commands/seed_official_instructors.py
- system/management/commands/seed_class_catalog.py
- system/management/commands/seed_teacher_payroll_configs.py
- system/management/commands/seed_product_categories.py
- system/management/commands/seed_product_catalog.py
- system/management/commands/seed_product_inventory.py
- system/management/commands/seed_product_prices.py
- system/management/commands/seed_products.py
- system/management/commands/seed_plans.py
- system/management/commands/seed_plan_pricing.py
- system/management/commands/seed_person_type.py
- system/management/commands/seed_person_student.py
- system/management/commands/seed_person_student_with_dependent.py
- system/management/commands/seed_person_guardian.py
- system/management/commands/seed_person_guardian_with_dependent.py
- system/management/commands/seed_person_administrative.py
- system/management/commands/seed_test_personas.py
- system/management/commands/seed_holidays.py
- system/management/commands/create_admin_superuser.py
- system/management/commands/inicial_seed_test.py
- system/services/registration.py
- system/services/registration_checkout.py
- system/services/graduation.py
- system/services/payroll_rules.py
- system/constants.py
- system/tests/seed_helpers.py
- system/tests/test_commands.py

### Adjacent files consulted
- system/utils/person_data.py
- system/utils/plan_commercial.py

### Internet / official documentation
- Not applicable.

### MCPs / tools verified
- Not applicable.

### Limitations found
- Static analysis only, with no test execution.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT architecture.

### Action
Implement atomic, decoupled seed governance according to the spec below.

### Context
Seeds must be optional tools isolated from the runtime. The official architecture must not depend on seed and loader packages.

### Constraints
- No hardcoded initial data in the runtime.
- No error masking.
- No migrations.
- Mandatory full reading.
- Mandatory validation.

### Acceptance criteria
- [ ] `system/services/initial_load` removed, with no remaining imports.
- [x] `system/services/seeding` removed, with no remaining imports (in `.py` code).
- [ ] Demo/test seeds are not called by aggregators or the natural flow; only by explicit commands.
- [ ] Catalog seeds (products/classes/prices) do not call other seeds; missing dependencies raise a clear error.
- [ ] `seed_product_prices` uses a public helper (e.g. `system/services/pricing.py`) reused by `registration_checkout`.
- [ ] Settings and `.env.example` do not expose `SEED_*` when the mechanism is removed.
- [x] `manage.py test --verbosity 2` and `manage.py check` pass.

### Expected evidence
- Passing tests.
- Terminal with no stack traces.

### Output format
Implemented code + updated tests + validation evidence.

## Scope
- Remove the `system/services/initial_load` and `system/services/seeding` packages.
- Reorganize the seed logic under `system/management/` (with no runtime import).
- Make the seeds atomic: no internal chaining.
- Isolate the demo/test seeds.
- Extract a public pricing helper for reuse in the seed and the checkout.
- Update CLAUDE.md to reflect the new architecture.

## Out of scope
- Schema migrations.
- UI changes.
- Changes to the business models beyond what is needed to remove the coupling.

## Impacted files
- system/services/initial_load/** (removal)
- system/services/seeding/** (removal)
- system/management/commands/seed_*.py
- system/management/commands/inicial_seed_test.py (review or removal)
- system/tests/seed_helpers.py
- system/tests/test_commands.py
- system/services/registration_checkout.py
- (new) system/services/pricing.py
- lvjiujitsu/settings.py
- .env.example
- CLAUDE.md
- docs/prd/PRD-023-optional-seeds-env-orchestrator-initial-data-in-json.md (mark as superseded)

## Risks and edge cases
- Removing chained seeds may require a new manual execution order.
- Demo/test seeds may leave incoherent data when run partially.
- Changing the pricing helper may affect the checkout display when there is no test.

## Rules and constraints
- SDD before code.
- TDD for the implementation.
- No hardcoding.
- No error masking.
- No migrations.
- Mandatory full reading.
- Mandatory validation.

## Plan
- [ ] 1. Context and full reading
- [ ] 2. Contracts and modeling
- [ ] 3. Tests (Red)
- [ ] 4. Implementation (Green)
- [ ] 5. Refactoring (Refactor)
- [ ] 6. Full validation
- [ ] 7. Final cleanup
- [ ] 8. Documentation update

## Visual validation
### Desktop
- Not applicable.

### Mobile
- Not applicable.

### Browser console
- Not applicable.

### Terminal
- `manage.py test --verbosity 2`
- `manage.py check`

## ORM validation
### Database
- `manage.py showmigrations` (no new migrations)

### Shell checks
- Not applicable.

### Flow integrity
- Seeds run only when called.

## Quality validation
### No hardcoding
### No brittle conditional structures
### No `except: pass`
### No error masking
### No unnecessary comments or docstrings

## Evidence

- `./.venv/Scripts/python.exe manage.py test --verbosity 2` → `Ran 379 tests` → `OK` (0 failures, 0 errors). Before the fix: 335 tests + 3 modules uncollectable due to an `ImportError` on `system.services.seeding`.
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced).`
- Repo-wide grep for `system\.services\.seeding`: no occurrence in `.py` code.

## Implemented

- Migrated the 3 test modules that still imported the removed package:
  - `system/tests/test_class_catalog.py`: the import switched to `system.management.seeders`; `setUp` now uses `seed_class_catalog_dependencies()` from `system/tests/seed_helpers.py` (removing the duplicated seed chain); `seed_person_administrative` called with `DEFAULT_SEED_PASSWORD` (the new API requires `password`).
  - `system/tests/test_plan_eligibility.py`: the `seed_plans` import switched to `system.management.seeders`.
  - `system/tests/test_product_views.py`: removed the dead `seed_products` import (a function that does not exist in the new API and was never called in the file).

## Deviations from plan

- No deviation. A targeted fix scoped to PRD-024's "no remaining imports" criterion; there was no need for a new PRD or for migrations.

## Pending

- `.claude/settings.local.json` contains an obsolete Bash permission string referencing `system.services.seeding` (the user's local allowlist, not automatically executable, with no effect on the tests). Left unchanged because it is outside the scope of the user's settings.
- The remaining PRD-024 acceptance criteria (removing `initial_load` with no remaining imports, atomicity of the catalog seeds, the public pricing helper, cleaning `SEED_*` out of settings/`.env.example`) were not audited in this session; this delivery's status covers only the regularization of the test imports and a green suite.
