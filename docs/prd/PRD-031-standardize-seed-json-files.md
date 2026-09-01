# PRD-031: Standardize the seed JSON files

## Summary of the implementation
Rename the JSON files under `static/initial_data/` so they reflect the seed command that consumes them whenever there is a direct one-file-to-one-seed relationship. Files consumed by two or more seeds will not be renamed at this stage without being split, to avoid preserving hidden coupling.

## Demand type
Documentation regeneration and a targeted seed governance fix.

## Current problem
The JSON files use domain names (`belt_ranks.json`, `class_categories.json`, etc.), while the project's real operation runs through atomized seeds (`seed_system_initial_*`). Some JSON files are shared by several seeds, mainly the instructor and back-office ones, which makes ownership hard to trace.

## Goal
Give the single-use JSON files the same name as the consuming seed and record a clear plan to split the shared JSON files by responsibility.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `system/management/commands/seed_system_initial_belt_ranks.py`
- `system/management/commands/seed_system_initial_class_categories.py`
- `system/management/commands/seed_system_initial_class_catalog.py`
- `system/management/commands/seed_system_initial_ibjjf_age_categories.py`
- `system/management/commands/seed_system_initial_graduation_rules.py`
- `system/management/commands/seed_system_initial_product_categories.py`
- `system/management/commands/seed_system_initial_product_catalog.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_class_categories_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/management/commands/seed_system_initial_class_categories_administrative.py`
- `system/management/commands/seed_system_initial_class_catalog_administrative.py`

### Adjacent files consulted
- `static/initial_data/`
- `docs/prd/`

### Internet / official documentation
- Not applicable. An internal change of file names and local contracts.

### MCPs / tools verified
- PowerShell — OK — `Get-ChildItem`, `Get-Content`, `Move-Item`
- ripgrep — OK — `rg`
- Django — OK with a limitation — `manage.py check` passed; the full suite still has pre-existing template/route failures

### Limitations found
- `system/migrations/0001_initial.py` was already modified before this task and will not be touched.
- `legacy_product_skus.json` has no active consumer in the current commands.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + seed governance.

### Action
Rename the single-use JSON files to the consuming seed's name and document a plan to split the shared JSON files.

### Context
The current seeds are individual commands in `system/management/commands/`, and the data lives in `static/initial_data/`.

### Constraints
- no migrations
- do not change the schema
- do not run the destructive cycle
- do not create an orchestrator
- no hardcoding outside the seed file's explicit contract
- preserve manual, sequential execution of the seeds

### Acceptance criteria
- [ ] JSON files consumed by a single seed have a name derived from the consuming command.
- [ ] The consuming commands point to the new names.
- [ ] Shared JSON files are listed with a separation plan by key and dependency.
- [ ] `manage.py check` passes.
- [ ] There are no references to the old names of the renamed JSON files.

### Expected evidence
- `manage.py check`
- a shell check loading the renamed JSON files with no error
- `rg` with no obsolete references to the renamed files

### Output format
Adjusted code + PRD + validation evidence.

## Scope
Rename:
- `belt_ranks.json`
- `class_categories.json`
- `class_catalog.json`
- `ibjjf_age_categories.json`
- `graduation_rules.json`
- `product_categories.json`
- `product_catalog.json`
- `product_inventory.json`
- `subscription_plans.json`

## Out of scope
Splitting the JSON files shared by instructors and back-office staff right now.
Creating new seeds for orphaned files.
Changing the database, models, or migrations.

## Impacted files
- `static/initial_data/*.json`
- `system/management/commands/seed_system_initial_*.py`
- `docs/prd/PRD-031-standardize-seed-json-files.md`

## Risks and edge cases
- Commands may fail if messages or old names remain hardcoded.
- Two files may belong to the same seed, such as the product catalog and inventory; in those cases the main file takes the seed's name and the complementary one takes a functional suffix.
- A JSON file shared by several seeds must not take the name of only one seed without splitting the content.

## Rules and constraints
- SDD before code
- mandatory validation
- no migrations
- mandatory full reading
- the smallest correct change before expanding scope

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Tests/checks before the change
- [x] 4. Direct renaming of the single-use JSON files
- [x] 5. Adjustment of the consuming commands
- [x] 6. Split plan for the shared JSON files
- [x] 7. Full validation
- [x] 8. Final cleanup
- [x] 9. Documentation update

## Visual validation
### Desktop
Not applicable.
### Mobile
Not applicable.
### Browser console
Not applicable.
### Terminal
Run the Django checks and inspect the references.

## ORM validation
### Database
There will be no database change.
### Shell checks
Load the renamed JSON files through the commands' `_load_json()`.
### Flow integrity
Confirm the commands still find the files.

## Quality validation
### No hardcoding
File names stay explicit inside each seed, which is the project's current contract.
### No brittle conditional structures
Not applicable.
### No `except: pass`
Not applicable.
### No error masking
`CommandError` stays explicit when a file does not exist.
### No unnecessary comments or docstrings
Do not add unnecessary new comments.

## Split plan for the shared JSON files
### `initial_teachers.json`
Current consumers:
- `seed_system_initial_teacher`
- `seed_system_initial_class_categories_teacher`

Proposed separation:
- `seed_system_initial_teacher.json`: person data, portal account, and graduation history.
- `seed_system_initial_class_categories_teacher.json`: links `{ "cpf": "...", "class_category": "..." }`.

Join keys:
- `cpf` identifies a `Person`.
- `class_category` references `ClassCategory.code`.

Order:
1. `seed_system_initial_person_type`
2. `seed_system_initial_belt_ranks`
3. `seed_system_initial_teacher`
4. `seed_system_initial_class_categories`
5. `seed_system_initial_class_categories_teacher`

### `initial_administrative.json`
Current consumers:
- `seed_system_initial_administrative`
- `seed_system_initial_class_categories_administrative`
- `seed_system_initial_class_catalog_administrative`

Proposed separation:
- `seed_system_initial_administrative.json`: person data, portal account, and graduation history.
- `seed_system_initial_class_categories_administrative.json`: links `{ "cpf": "...", "class_category": "..." }`.
- `seed_system_initial_class_catalog_administrative.json`: links `{ "cpf": "...", "class_group_category": "...", "class_group_teacher_cpf": "..." }`.

Join keys:
- `cpf` identifies the back-office `Person`.
- `class_category` references `ClassCategory.code`.
- `class_group_category` references `ClassCategory.code`.
- `class_group_teacher_cpf` references the `Person.cpf` of the class's main instructor.
- The `ClassGroup` is resolved by `(class_category__code, main_teacher__cpf)`, per the current contract after the removal of `ClassGroup.code`.

Order:
1. `seed_system_initial_person_type`
2. `seed_system_initial_belt_ranks`
3. `seed_system_initial_administrative`
4. `seed_system_initial_class_categories`
5. `seed_system_initial_class_categories_administrative`
6. `seed_system_initial_teacher`
7. `seed_system_initial_class_catalog`
8. `seed_system_initial_class_catalog_administrative`

### `product_catalog.json` and `product_inventory.json`
Both belong to a single seed: `seed_system_initial_product_catalog`.

Separation applied at this stage:
- `seed_system_initial_product_catalog.json`: the product catalog.
- `seed_system_initial_product_catalog_inventory.json`: variants and stock by SKU.

Join keys:
- `sku` identifies a `Product`.
- `category` references `ProductCategory.code`.
- `inventory[].sku` references `Product.sku`.

### Files with no active consumer
Current files:
- `legacy_product_skus.json`

Proposed handling:
- keep it unrenamed at this stage, because there is no active seed declaring ownership.
- before renaming, choose an explicit destination:
  - remove the file if it is dead legacy; or
  - recreate a dedicated seed once there is an active consumer.

## Evidence
- `.\.venv\Scripts\python.exe manage.py check` — passed: `System check identified no issues (0 silenced).`
- A Django shell check loading the commands' `_load_json()` — passed:
  - `seed_system_initial_belt_ranks`: 13 records
  - `seed_system_initial_class_categories`: 4 records
  - `seed_system_initial_class_catalog`: 6 records
  - `seed_system_initial_ibjjf_age_categories`: 22 records
  - `seed_system_initial_graduation_rules`: 52 records
  - `seed_system_initial_product_categories`: 4 records
  - `seed_system_initial_subscription_plans`: 3 records
  - `seed_system_initial_product_catalog`: 5 products
  - `seed_system_initial_product_catalog_inventory`: 5 inventory entries
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` — passed: 4 tests OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — failed with 5 failures and 109 errors, matching the pattern observed before this change: examples include `TemplateDoesNotExist: home/student/dashboard.html`, `TemplateDoesNotExist: home/admin/dashboard.html`, and `NoReverseMatch: person-list`.

## Implemented
- Renamed the single-use JSON files to the `seed_system_initial_<domain>.json` pattern.
- Kept `initial_teachers.json` and `initial_administrative.json` unrenamed until the split.
- Kept `legacy_product_skus.json` unrenamed since there is no active consumer.
- Adjusted the consuming commands to load the new names.

## Deviations from plan
- No deviation in the seed change.
- The full validation did not end green due to pre-existing failures in the overall suite.

## Pending
- Split `initial_teachers.json` and `initial_administrative.json` in a PRD/stage of their own.
- Decide the fate of `legacy_product_skus.json`, which has no active consumer.
