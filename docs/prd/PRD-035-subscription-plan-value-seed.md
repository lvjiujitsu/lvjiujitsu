# PRD-035: Subscription plan value seed

## Summary of the implementation
Create `seed_system_initial_subscription_plans_values` to insert the amounts charged per plan, weekly frequency, gateway, payment method, and periodicity, from its own JSON.

## Demand type
New feature

## Current problem
`seed_system_initial_subscription_plans` creates only the base category plans. The real charging amounts are in the spreadsheet attached by the user and need to become editable data in the database.

## Goal
Generate 72 priced plans: 3 categories × 2 frequencies × 3 gateways/methods × 4 billing cycles.

## Context Ledger
### Files read in full
- `system/models/plan.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `static/initial_data/seed_system_initial_subscription_plans.json`
- `system/tests/test_plan_models.py`
- `system/tests/test_commands.py`

### Adjacent files consulted
- `system/signals.py`
- `system/models/__init__.py`
- `system/tests/test_plan_eligibility.py`
- the summarized plan and detailed plan attachments sent by the user

### Internet / official documentation
- Not applicable.

### MCPs / tools verified
- PowerShell — status ok — local reading and validation.

### Limitations found
- Some card amounts differ by cents when recalculated using only `Decimal(2)` net-value fields. The seed preserves the amount charged from the JSON as the source of truth.

## Execution prompt
### Persona
Django development agent following SDD + TDD.

### Action
Implement a granular plan value seed using the existing dynamic model.

### Context
The `SubscriptionPlan` model already has fields for the desired monthly net amount, fixed fee, percentage fee, cycle discount, gateway, payment method, and periodicity.

### Constraints
- no migrations
- no `--` arguments
- data in `static/initial_data/seed_system_initial_subscription_plans_values.json`
- an idempotent seed
- the amounts charged from the JSON prevail over intermediate rounding

### Acceptance criteria
- [x] The `seed_system_initial_subscription_plans_values` command exists.
- [x] The seed creates/updates 72 priced plans.
- [x] Running it twice does not duplicate plans.
- [x] The `individual`, `loyalty`, and `family` base plans become inactive after the values are applied.
- [x] `python manage.py test system.tests.test_commands --verbosity 2` passes.
- [x] `python manage.py check` passes.

### Expected evidence
- Focused tests passing.
- The check passing.

### Output format
Implemented code + the command for manual execution.

## Scope
- The plan values JSON.
- The value seed command.
- A command/idempotency test.
- An update to the operational documentation.

## Out of scope
- Changing the schema.
- Synchronizing the plans in Stripe.
- Recreating the plan selection screens.

## Impacted files
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Risks and edge cases
- If the user changes the values manually in the admin and reruns the seed, the JSON becomes the source of truth again.
- Card amounts may round differently from the pure calculation; for that reason the seed pins `price` to the amount charged as provided.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no migrations
- mandatory validation

## Plan
- [x] 1. Read the model and the existing seed.
- [x] 2. Extract the values from the attachments.
- [x] 3. Create the JSON.
- [x] 4. Create the command.
- [x] 5. Create the test.
- [x] 6. Validate.

## Visual validation
Not applicable; a change with no UI.

## ORM validation
Validated through Django tests with the test database.

## Quality validation
### No hardcoding
The values live in the JSON; the command only expands and applies them.

### No brittle conditional structures
The cycle and gateway mappings are explicit and small.

### No `except: pass`
Not introduced.

### No error masking
Invalid entries raise a `CommandError`.

### No unnecessary comments or docstrings
Not introduced.

## Evidence
- `python manage.py help seed_system_initial_subscription_plans_values`: the command is registered with no custom arguments.
- `python manage.py test system.tests.test_commands --verbosity 2`: 7 tests, OK.
- `python manage.py test`: 158 tests, OK.
- `python manage.py check`: no issues.

## Implemented
- Created the `seed_system_initial_subscription_plans_values.json` JSON with the values extracted from the attachments.
- Created the `seed_system_initial_subscription_plans_values` command.
- Created a test for the seed's idempotency and key values.
- Updated `CLAUDE.md` with the operational command.

## Deviations from plan
- None so far.

## Pending
- Recreate the UI tests when the screens are reimplemented.
