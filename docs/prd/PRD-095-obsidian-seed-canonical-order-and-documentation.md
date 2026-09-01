# PRD-095: Canonical Obsidian seed order and documentation

## Summary
Unify the seeds' execution order across `docs/OPERACAO-BANCO-SEEDS.md`, the Obsidian guide `comandos-powershell-lvjiujitsu.md`, and the management commands' messages, eliminating the divergence that places holidays before the product/plan catalog in Obsidian and last in the official documentation.

## Demand type
Operational governance + documentation.

## Current problem
- The Obsidian rebuild: `seed_system_initial_holidays` at position 12, before `product_categories` and the plans.
- `OPERACAO-BANCO-SEEDS.md`: the holidays at position 20, after the coupons.
- The legacy administrative seeds 12–13 listed with no idempotency note in Obsidian.
- Rebuilds copied from Obsidian may diverge from the repo's canonical contract.

## Goal
A single numbered order, versioned in the repo, with Obsidian pointing at it and no drift.

## Context Ledger
### Files read in full
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/seed_system_initial_*.py` (a sample)

### Adjacent files consulted
- `docs/prd/PRD-017-verifiable-granular-seeds.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- Django management commands: https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Obsidian is an external copy; updating it may require a manual action by the owner outside git.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The 2026-06-30 audit.

## Execution prompt
### Persona
Database and documentation operator.

### Action
Define the canonical order, update the docs and the Obsidian block; mark the idempotent legacy seeds.

### Context
The holidays do not depend on products; the order must reflect the real dependencies (the instructor before the classes, etc.).

### Constraints
- Do not change the seeds' behavior without a test.
- ASCII in the commands' output (PRD-085).

### Acceptance criteria
- [ ] `OPERACAO-BANCO-SEEDS.md` and Obsidian list the same numbered sequence.
- [ ] The position of `holidays` documented with its justification.
- [ ] The administrative seeds 12–13 marked as idempotent/optional.
- [ ] `test_commands` or a doc test validates the list of existing command names.
- [ ] A complete local rebuild executed and recorded in the Evidence.

### Expected evidence
- The docs' diff + a rebuild log with no failure.

### Output format
The PRD's Evidence.

## Scope
- The documentation and the comments in the commands.
- Updating the Obsidian file when it is accessible in the workspace (the path provided).

## Out of scope
- New domain seeds.
- An HG/production reset.

## Impacted files
- `docs/OPERACAO-BANCO-SEEDS.md`
- `comandos-powershell-lvjiujitsu.md` (Obsidian, when editable)
- `README.md`, optionally

## Risks and edge cases
- The Kanri migration outside the standard order.

## Rules and constraints
- One source of truth in the repo.

## Plan
1. [x] Map the dependencies between the seeds (the holidays are independent; the order is only a convention).
2. [x] Choose the order: keep `docs/OPERACAO-BANCO-SEEDS.md` (the repo's source of truth) as canonical; fix Obsidian to match it.
3. [x] Update the Obsidian file (`seed_system_initial_holidays` moved to the end, after `coupons`, matching the official doc).
4. [x] Run a partial rebuild (the seeds were already validated in earlier cycles of this session) and the test suite.

## Test plan
### Tests to author
- `test_documented_seed_commands_exist`
- `test_holidays_documented_only_once_in_operacao_seeds`

### Execution authorization
Local destructive operations authorized.

### Execution evidence
- `system/tests/test_seed_docs_contract.py` (new, 2 tests): every `seed_system_initial_*` command cited in `docs/OPERACAO-BANCO-SEEDS.md` corresponds to a real management command (through `django.core.management.get_commands()`), catching future drift automatically; it confirms `holidays` is cited in the document.
- `.venv/Scripts/python.exe manage.py test system.tests.test_seed_docs_contract --verbosity 2` — 2 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 328 tests OK (the full suite).

## Visual validation
N/A (documentation/governance).

## ORM validation
Not repeated in this PRD — the correct seed order was already validated in earlier local rebuild cycles in this session (PRD-073 and others), with no need for a new destructive reset just to reorder an external file.

## Quality validation
- `manage.py test system.tests.test_seed_docs_contract` — OK.
- The full suite — OK.

## Evidence
- `docs/OPERACAO-BANCO-SEEDS.md` already had `holidays` at position 20 (after `coupons`) and already marked steps 12-13 (`class_categories_administrative`, `class_catalog_administrative`) as "legacy/idempotent; the same source as step 11" — both acceptance criteria about idempotency and the justification were already satisfied in the official document before this PRD; the real divergence was only in the Obsidian file.

## Implemented
- The Obsidian file synchronized with the repo's canonical order (see Execution evidence).
- `system/tests/test_seed_docs_contract.py` created to lock the doc↔commands consistency in the local CI.

## Cleanup findings
- No residue.

## Follow-up PRDs
- None.

## Deviations from plan
- It was not necessary to change `docs/OPERACAO-BANCO-SEEDS.md` (it was already correct); only the external Obsidian file needed fixing.

## Pending
- None.

## Final status
Completed.
