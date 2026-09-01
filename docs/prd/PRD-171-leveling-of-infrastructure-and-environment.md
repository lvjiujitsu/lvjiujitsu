# PRD-171: Infrastructure and Environment Alignment

## Summary

Dependencies, `.gitignore`, the agent workflow, and the environment-key set were aligned with the declared standard. The highest-impact finding was in `LOGGING`: it existed only inside `if not DEBUG:`, so the local environment ran **without any logging configuration**. Five code-convergence items remained outside scope and are recorded in `Pending`.

## Demand type

Configuration and dependencies. No business-rule, schema, or visual change.

## Current problem

- `requirements.txt` pinned `PyYAML==6.0.2` instead of the `6.0.3` the project targets, and contained grouping comments that the declared standard does not use.
- **`LOGGING` was inside `if not DEBUG:`.** Locally, with `DEBUG=True`, Django fell back to its default configuration: no project formatter, no controlled level, and no handling for `django.db.backends`. The level was also hardcoded as `'WARNING'`, without an environment variable.
- `settings.py` read `CACHE_TIMEOUT` and `WHITENOISE_MAX_AGE`, but **none of the four environment files declared these keys**: the code depended on keys absent from the environment contract.
- `.env` declared `DJANGO_DEBUG=1` instead of `True`, diverging from the declared convention.
- `.gitignore` had 28 lines and lacked entries the project needs (`pytest-cache-files-*/`, `tmp_*.py`, and `.codex-runtime/`—the latter two already used here).
- `.github/workflows/copilot-setup-steps.yml` existed only here, and its comment cited a PRD from this repository, preventing literal mirroring.
- `.env.example` did not explain why `SUPABASE_RESET_CONFIRM` is absent, inviting someone to "correct" the omission and disarm the remote-reset guard.

## Goal

Every package is pinned to an exact version string. `LOGGING` applies in every environment, and its level comes from the environment. Every declared environment key has a reader, and every reader has a declared key.

## Context Ledger

### Files read in full

- `requirements.txt`, `.gitignore`
- `lvjiujitsu/settings.py`
- `.env`, `.env.example`, `.env.hg`, `.env.prod`—key names and non-secret values
- `.github/workflows/ci.yml`, `.github/workflows/copilot-setup-steps.yml`

### Adjacent files consulted

- `clear_migrations.py`—process-termination comparison
- `system/services/stripe_*.py`—to confirm that `stripe` is actually imported
- `system/tests/test_settings_hosts.py`

### Internet / official documentation

- python-decouple, precedence and `cast`: https://pypi.org/project/python-decouple/
- Django 5.2, `LOGGING` and `django.db.backends` reference: https://docs.djangoproject.com/en/5.2/ref/logging/

### Context7 / MCPs / tools verified

- Context7 was not consulted: versions came from an actual `pip install` and `pip check`, which are the most reliable source for what resolves in this environment.

### Limitations found

- `python-decouple` **does not** fall back to `default` when a key exists with an empty value: it returns an empty string. This broke project startup during execution and is recorded under `Deviations from plan`.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: a six-stage plan, with Stage 4 described item by item.
- User approval: "continue."
- Date: 2026-07-26.

## Execution prompt

### Persona

Engineer responsible for the repository's local and deployment infrastructure.

### Action

Unify dependencies, `.gitignore`, the agent workflow, and the environment-key set, and make `LOGGING` unconditional and configurable.

### Context

Disposable MVP. Re-creatable local environment. No declared key may lack a reader, and no reader may depend on an undeclared key.

### Constraints

- identical pinned version for any package present in more than one project;
- direct dependencies only in `requirements.txt`;
- no secret value written to an environment file or this PRD;
- `SUPABASE_RESET_CONFIRM` **must not** be declared in an environment file;
- passing suite after any dependency or logging change.

### Acceptance criteria

- [x] `requirements.txt` contains direct dependencies, alphabetically ordered, without comments;
- [x] an exact pinned version for every package;
- [x] clean `pip check`;
- [x] `LOGGING` is defined in every environment, its level comes from `DJANGO_LOG_LEVEL`, and `django.db.backends` uses `INFO`;
- [x] `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE`, and `DJANGO_LOG_LEVEL` are declared in all four files;
- [x] `.env` uses `DJANGO_DEBUG=True`;
- [x] `.gitignore` has a single variant after normalization;
- [x] `copilot-setup-steps.yml` is aligned with `ci.yml` in runner, timeout, and Python version;
- [x] `SUPABASE_RESET_CONFIRM` is absent from all four files, with the reason documented in `.env.example`;
- [x] `check`, `makemigrations --check --dry-run`, index, skills, `pip check`, and the full suite pass;
- [ ] convergence of `clear_migrations.py` and infrastructure commands—**not delivered**; see `Pending`.

### Expected evidence

Output from `pip install` and `pip check`, key counts per environment file, variants per file, and the full suite.

### Output format

Diff and the PRD updated with evidence.

## Scope

- `requirements.txt`
- `.gitignore`
- `.github/workflows/copilot-setup-steps.yml`
- `lvjiujitsu/settings.py`—logging block
- `.env`, `.env.example`, `.env.hg`, `.env.prod`

## Out of scope

- Convergence of `clear_migrations.py` and the five infrastructure commands.
- Creating a single `seed_test_data` to pair with `clear_test_data`.
- `docs/UI-SCREEN-CONTRACT.md` and CSS tokens.
- Removal of comments and docstrings.
- `docs/archive/static-documentation-legacy/` and the three wizard guides.
- Changing single quotes in `settings.py` to double quotes.

## Impacted files

| File | Change |
|---|---|
| `requirements.txt` | 20 lines with comments → 10 direct, alphabetical dependencies; `PyYAML` 6.0.2 → 6.0.3 |
| `.gitignore` | 28 → 32 lines, with three shared entries added |
| `.github/workflows/copilot-setup-steps.yml` | removed local PRD reference from the comment to permit literal mirroring |
| `lvjiujitsu/settings.py` | `LOGGING` moved out of `if not DEBUG:` and always applies; `LOG_LEVEL` comes from `DJANGO_LOG_LEVEL`; `django.db.backends` pinned to `INFO`; `null` handler under `DEBUG` |
| `.env`, `.env.example`, `.env.hg`, `.env.prod` | add `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE`, and `DJANGO_LOG_LEVEL`; 68 → 71 keys each |
| `.env` | `DJANGO_DEBUG=1` → `DJANGO_DEBUG=True` |
| `.env.example` | note explaining why `SUPABASE_RESET_CONFIRM` is not declared |

## Risks and edge cases

- Making `LOGGING` unconditional changes **local** behavior, where there was previously no configuration. To avoid replacing silence with noise, the handler under `DEBUG` is `null`, and `django.db.backends` remains at `INFO`: local output volume stays the same, now by an explicit decision rather than absent configuration.
- `DJANGO_DEBUG=1` and `True` are equivalent under decouple's `cast=bool`, so the change is conventional, not behavioral.
- A declared key with an empty value breaks startup when a `cast` is used. That happened here and is recorded below.
- `stripe==15.0.1` and `requests==2.33.1` remain because both have confirmed importers in the code.

## Rules and constraints

- Section 10 of `AGENTS.md`: secrets are never printed; when reading environment data, report key names.
- Section 11 of `AGENTS.md`: destructive-cycle guards cannot be weakened.
- Section 12 of `AGENTS.md`: material debt outside scope becomes a follow-up.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

No new test. The 769-case suite is the guardrail for the dependency and logging changes, and `manage.py check` revealed the empty-key error.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python -m pip install -r requirements.txt
Requirement already satisfied: Django==5.2.14
Successfully installed PyYAML-6.0.3
exit=0

python -m pip check
No broken requirements found.
exit=0

python -c "import django; print(django.get_version())"
5.2.14
```

Error observed before correcting the empty value:

```text
python manage.py check
ValueError: invalid literal for int() with base 10: ''
exit=1
```

After correction:

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0

python manage.py test
Ran 769 tests in 390.727s
OK
exit=0
```

## Visual validation

### Design approval

Not applicable: no visual change.

### Routes and states

Not applicable: no route changed.

### Desktop

Not applicable.

### Mobile

Not applicable.

### Console and terminal

`manage.py check` produced no warning. Local output volume did not change because the handler under `DEBUG` is `null`.

### Screenshot / snapshot

Not applicable.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

No write was executed.

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
pip check                           -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Pinned versions:

```text
dj-database-url==3.1.2   Django==5.2.14        gunicorn==26.0.0
psycopg2-binary==2.9.12  python-decouple==3.8  PyYAML==6.0.3
tzdata==2026.1           whitenoise==6.12.0
```

Direct dependencies unique to this project, with confirmed importers: `requests==2.33.1` and `stripe==15.0.1`.

Environment-key set (`.env` / `.env.example` / `.env.hg` / `.env.prod`):

```text
lvjiujitsu   71/71/71/71   identical set: True
```

`SUPABASE_RESET_CONFIRM` is declared in 0 files, as required.

Variants after normalization: `.gitignore` = 1 (the two historical-import lines are a project-specific tail), `copilot-setup-steps.yml` = 1.

## Implemented

- `requirements.txt` with 10 direct dependencies, alphabetically ordered and without comments;
- unconditional `LOGGING`, with its level from the environment, a `null` handler under `DEBUG`, and `django.db.backends` at `INFO`—the local environment no longer runs without logging configuration;
- `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE`, and `DJANGO_LOG_LEVEL` declared in all four files, closing the gap between what the code reads and what the environment contract provides;
- `DJANGO_DEBUG=True` in `.env`;
- `.gitignore` with the three shared entries;
- mirrorable `copilot-setup-steps.yml` present;
- `.env.example` explaining why `SUPABASE_RESET_CONFIRM` does not live there.

## Cleanup findings

- This project's `clear_migrations.py` uses `taskkill /F` without `/T` and waits up to 8 seconds; it is the baseline for the convergence recorded in `Pending`.
- There is no `seed_test_data`: the counterpart to `clear_test_data` consists of four `seed_system_initial_test_*` seeds.
- `settings.py` uses single quotes while the other files in this area use double quotes.
- `system/tests/test_class_catalog.py` has 0 lines.
- `docs/archive/static-documentation-legacy/` contains 12 superseded documents, and `docs/prd/AUDIT-2026-06-30-master-findings.md` forces the index generator to retain a named exception.
- The local `stage` branch has no corresponding remote; the remote is `origin/stage-visual`.
- `.claude/settings.local.json` exactly duplicates `settings.json`.

## Follow-up PRDs

- Converge `clear_migrations.py` and the infrastructure commands (`_supabase_public_schema_reset`, `lock_supabase_api_access`, `create_admin_superuser`, `clear_test_data`, `clear_migration_supabase_*`), using this project's implementation as the baseline for process termination.
- Align `docs/UI-SCREEN-CONTRACT.md` and converge CSS tokens.
- Next agreed stages: structure and comment/docstring cleanup.

## Deviations from plan

Three.

**Adding the keys with empty values broke this project's startup.** `python-decouple` returns an empty string when a key exists without a value instead of falling back to `default`, and `CACHE_TIMEOUT=` with `cast=int` raised `ValueError: invalid literal for int() with base 10: ''`, with `manage.py check` exiting 1. The gate itself discovered the problem, which was corrected by filling in an actual value in all four files.

**The audit that originated this stage stated that this project had no `LOGGING` block. It was wrong, and reality was worse:** the block existed but only inside `if not DEBUG:`, so the local environment ran with Django's default configuration. The initial search used a start-of-line anchor and missed the indented block.

**The audit also stated that `SUPABASE_RESET_CONFIRM` was missing from `.env.example` and should be added. It was wrong.** Persisting the value in an environment file would leave the remote-reset guard permanently satisfied. Its absence is the guard; what was missing was the explanation.

## Pending

Five code-convergence items, all related to infrastructure and none to business rules:

1. **`clear_migrations.py`**—process termination is the item still to converge; this project's implementation is the baseline to keep.
2. **Five infrastructure commands** with 2 to 3 variants: `_supabase_public_schema_reset`, `lock_supabase_api_access`, `create_admin_superuser`, `clear_test_data`, `clear_migration_supabase_hg`, and `_prod`.
3. **Seed/clear pair**—decide whether to create `seed_test_data` here or keep only the `test_*` seed model; this is a product decision, not a mechanical one.
4. **Seed policy in `/reset-local`**—optional here; decide whether it becomes mandatory.
5. The cleanup findings above that depend on an operator decision: the branch remote and `settings.local.json`.

They were not delivered by a scope decision: these are behavior changes in the destructive cycle and remote commands, and each requires a full reading of all three implementations plus its own test.

## Final status

Completed with limitations. Dependencies, `.gitignore`, the agent workflow, and the environment-key set were aligned; `LOGGING` was corrected to apply in every environment; and the 769-case suite passed. Five code-convergence items remain recorded in `Pending`.
