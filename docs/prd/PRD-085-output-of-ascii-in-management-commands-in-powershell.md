# PRD-085: ASCII output in management commands under PowerShell

## Summary
Ensure the management commands used in the local bootstrap do not break in PowerShell consoles with the `cp1252` encoding.

## Demand type
An operational seed fix and local governance.

## Current problem
During the validation of the local seed sequence, `seed_system_initial_graduation_rules` failed with a `UnicodeEncodeError` when printing the `→` character.

## Goal
The output of the operational management commands must avoid Unicode symbols outside PowerShell's default encoding.

## Scope
- Remove the Unicode arrows from the seed commands.
- Preserve the Brazilian Portuguese messages where `cp1252` supports them.
- Validate the affected seed sequence.

## Out of scope
- Rewriting every CLI text.
- Changing the global Python, terminal, or Django encoding.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Evidence
- The command executed: the local seed sequence after `migrate`.
- The real failure: `UnicodeEncodeError: 'charmap' codec can't encode character '→'`.
- The direct file: `system/management/commands/seed_system_initial_graduation_rules.py`.

## Plan
- [x] Replace `→` with `->` in the administrative, instructor/class, and graduation seeds.
- [x] Replace `↳` with `->` in the Stripe seed to avoid an equivalent failure.
- [x] Re-run the local seed sequence.

## Test plan
- Re-run the local seeds in PowerShell.
- Run `manage.py check`.

## Implemented
- The outputs with `→` were replaced with `->` in:
  - `seed_system_initial_graduation_rules`
  - `seed_system_initial_class_catalog`
  - `seed_system_initial_class_catalog_administrative`
  - `seed_system_initial_class_categories_administrative`
  - `seed_system_initial_class_categories_teacher`
- The outputs with `↳` were replaced with `->` in `seed_system_initial_subscription_plans_stripe`.

## Execution evidence
- The first local sequence failed in `seed_system_initial_graduation_rules` with a `UnicodeEncodeError` on the `→` character.
- After the fix, the local seed sequence ran with exit code 0 up to `seed_system_initial_holidays`.
- `rg -n "→|✓|×" system\management\commands` found no remaining occurrences.

## Final status
Completed.
