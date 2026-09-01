# PRD-023: Optional seeds, `.env` orchestrator, initial data in JSON

> Superseded by PRD-024-atomic-decoupled-seed-governance. This PRD must not guide new changes.

## Summary of the implementation

Orchestration through `.env` (`SEED_DATA_ROOT`, `SEED_STRICT`, `SEED_ENABLE_*`), bulky data in `config/initial_data/*.json`, loading in `system/services/initial_load/`, and `seed_*` commands that no-op when switched off. The runtime (views/services) stays on the ORM only; with no seeds the system comes up empty and manual registration still works.

## Demand type

Architectural change / initial data governance.

## Current problem

`bootstrap.py` concentrates huge tuples; plan/product prices already use `.env`, but the rest of the initial content remains in Python code.

## Goal

- `.env` defines **where** and **whether** to load initial data.
- Versioned JSON is the source of content (not lists in `.env`).
- Seeds are **optional**; `migrate` + the app with no seeds does not break the existing atomic flows.

## Context Ledger

### Files read in full


### Limitations

- `seed_person_types` stays in `registration` + `constants` (out of this PRD's scope unless there is a dedicated JSON).
- Migrations: none new unless explicitly required.

## Acceptance criteria

- [ ] `SEED_ENABLE_CLASS_CATEGORIES=0` → `seed_class_categories` prints a skip and writes nothing.
- [ ] With `SEED_STRICT=1` and a missing JSON file → the command fails with a clear message.
- [ ] With the defaults, `config/initial_data/` is present in the repo and the seeds produce the same functional result as before (tests).
- [ ] `manage.py check` and `manage.py test system.tests` pass.
- [ ] `.env.example` documents `SEED_DATA_ROOT` and the toggles.

## Scope

- The `initial_load` package, the JSON files, settings, and refactoring `bootstrap` to read JSON and normalize enums.
- `seed_*` commands with a guard at the start.

## Out of scope

- Moving `DEFAULT_PERSON_TYPE_DEFINITIONS` to JSON.
- Full visual validation of the wizard (an optional manual smoke test).

## Execution plan (summary)

1. Generate JSON from the current state (a one-shot versioned script or equivalent).
2. Implement the loaders + string normalization for `CategoryAudience`, `WeekdayCode`, `TrainingStyle`.
3. Externalize `teacher_payroll` to JSON.
4. Remove the tuples from `bootstrap.py`; keep the transactional functions.
5. Toggles + PRD + CLAUDE + tests.

## Expected evidence

- Green automated tests.
- The list of `.env` keys in `.env.example`.
