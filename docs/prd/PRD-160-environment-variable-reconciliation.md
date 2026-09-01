# PRD-160: Environment-Variable Reconciliation

## Summary

`lvjiujitsu/settings.py` reads fourteen variables that exist only in `.env.example` and are undeclared in `.env`, `.env.hg`, and `.env.prod`. Two other variables exist in real environment files and are read nowhere. This PRD reconciles all four files into one key set and removes a test password from versioned documentation.

## Demand type

Infrastructure and configuration. No business-rule change.

## Current problem

1. Fourteen keys read by `lvjiujitsu/settings.py` are declared only in `.env.example`: `DJANGO_ENVIRONMENT`, `DATABASE_URL`, `DB_CONN_MAX_AGE`, `DJANGO_SECURE_HSTS_SECONDS`, `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_SECURE_HSTS_PRELOAD`, `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SESSION_COOKIE_SAMESITE`, `DJANGO_CSRF_COOKIE_SAMESITE`, `STRIPE_PLAN_SYNC_ENABLED`, `VETERAN_PLAN_TENURE_YEARS`, and `VETERAN_PLAN_GAP_GRACE_DAYS`.

   The defect direction matters: `.env.example` is correct; the three real files are incomplete. In staging and production, every transport and cookie-security directive falls back to a default without an explicit decision — including HSTS, HTTPS redirection, and the `Secure` marker on session and CSRF cookies.

   `DJANGO_ENVIRONMENT` deserves special mention: local `.env` does not declare it, and the project relies on the `local` fallback in `lvjiujitsu/settings.py:23-27`. An environment contract that works only by omission is fragile.

2. `SUPABASE_URL` and `SUPABASE_KEY` exist in `.env.hg` and `.env.prod` but are never read by `settings.py`. They are dead keys in secret files.

3. `docs/OPERACAO-BANCO-SEEDS.md:94` documents the `LvTest@2026` test password in plaintext in a versioned file. Even as a disposable MVP, `CLAUDE.md` retains the rule that operational secrets are treated as secrets.

4. The four environment files must declare exactly the same key set, with an empty diff among them. Today they do not.

## Goal

All four environment files declare the same key set; every declared key is read by `settings.py`; every key read by `settings.py` is declared; and no password appears in versioned documentation.

## Context Ledger

### Files read in full

- `lvjiujitsu/settings.py`
- `.env`, `.env.example`, `.env.hg`, `.env.prod` (structure, not values)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `CLAUDE.md`, `AGENTS.md`
- `clear_migrations.py`

### Adjacent files consulted

- `system/management/commands/_supabase_public_schema_reset.py`
- The four `system/management/commands/seed_system_initial_test_*.py` commands
- `system/management/commands/create_admin_superuser.py`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`

### Internet / official documentation

- [Django — Security settings (`SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`)](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-hsts-seconds)
- [Django — `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE`](https://docs.djangoproject.com/en/5.2/ref/settings/#session-cookie-secure)
- [Django — Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Supabase — Connecting to your database](https://supabase.com/docs/guides/database/connecting-to-postgres)

### Context7 / MCPs / tools verified

- Context7 available for Django 5.2. Cited security directives were checked against the official documentation above.

### Limitations found

- `.env*` is covered by `.gitignore`; key parity cannot be verified by CI and depends on a documented local runbook check.
- Enabling HSTS in production has persistent effects in a user’s browser; the initial value should be conservative.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: audit of the four environment files of this repository, conducted by read-only subagents and one reviewing auditor, with a verdict that intervention was required.
- User approval: explicit operator order to generate this PRD and then implement it.
- Date: 2026-07-25.

## Execution prompt

### Persona

Platform engineer responsible for LV environment configuration.

### Action

Declare the fourteen missing keys in the project’s real files with values appropriate to each environment, decide the fate of `SUPABASE_URL` and `SUPABASE_KEY`, and move the test password to an environment variable.

### Context

Staging and production run on Supabase and Render behind HTTPS. Security directives must be decided explicitly, not inherited by omission.

### Constraints

- No secret value is printed in output, logs, or PRD.
- Local security values remain permissive; HG and production values are restrictive.
- `DJANGO_ENVIRONMENT` is explicitly declared in `.env` with value `local`.
- No product behavior change beyond transport hardening in remote environments.

### Acceptance criteria

- [ ] The fourteen listed keys exist in `.env`, `.env.hg`, and `.env.prod`, with values coherent for each environment.
- [ ] `.env` declares `DJANGO_ENVIRONMENT=local` and an empty `DATABASE_URL`.
- [ ] `.env.hg` and `.env.prod` declare `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, and `DJANGO_CSRF_COOKIE_SECURE` as true, with nonzero `DJANGO_SECURE_HSTS_SECONDS`.
- [ ] The key-name set is identical across all four files. Verification: compare sorted keys from all four files, with an empty diff.
- [ ] Every key declared in all four files is read by `lvjiujitsu/settings.py` or has a justification recorded in this PRD. Verification: search every key name in code.
- [ ] `SUPABASE_URL` and `SUPABASE_KEY` are removed from real files or read by `settings.py`. Record the decision and rationale under `Deviations from plan`.
- [ ] `docs/OPERACAO-BANCO-SEEDS.md` contains no plaintext password. Test-seed password comes from an environment variable declared in all four files. Verification: textual search for `LvTest` returns zero occurrences outside `docs/prd/`.
- [ ] All four `seed_system_initial_test_*` commands read the password from the environment variable and fail with a clear message when it is absent. Verification: one test per command.
- [ ] `clear_migrations.py` continues refusing the lifecycle when a required variable, including the new one, is missing.
- [ ] `python manage.py check --deploy` reports no warning for HSTS, SSL redirect, or insecure cookies when run with `.env.prod`.
- [ ] `python manage.py check` passes and the test suite is green.

### Expected evidence

Comparison of keys across four files; search for every key in code; textual `LvTest` search; `check --deploy` output; test output.

### Output format

Diff of environment files, seed commands, and documentation, plus this PRD updated with actual evidence.

## Scope

- Declare fourteen keys in the project’s real files.
- Decide and act on `SUPABASE_URL` and `SUPABASE_KEY`.
- Test-seed password through an environment variable.
- Adjust four `seed_system_initial_test_*` commands.
- Update `docs/OPERACAO-BANCO-SEEDS.md`.

## Out of scope

- Slash commands, PRD index, and repository hygiene (PRD-161).
- Remote reset, deployment, and observability (PRD-162).
- Any Asaas or Stripe change.
- Model, migration, or registration-flow changes.

## Impacted files

- `.env`, `.env.example`, `.env.hg`, `.env.prod`
- `system/management/commands/seed_system_initial_test_students.py`
- `system/management/commands/seed_system_initial_test_guardians.py`
- `system/management/commands/seed_system_initial_test_administrative.py`
- `system/management/commands/seed_system_initial_test_teachers.py`
- `system/tests/test_seed_test_commands.py` (new or extended)
- `clear_migrations.py`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/README.md`

## Risks and edge cases

- Enabling `SECURE_SSL_REDIRECT` in staging could create a redirect loop behind Render’s proxy: confirm `SECURE_PROXY_SSL_HEADER` is configured before enabling, and validate with a real request.
- High HSTS value could pin the browser to HTTPS before the domain is stable: start conservatively and record the decision.
- Removing `SUPABASE_URL` and `SUPABASE_KEY` might reveal later that an external tool consumed them: search the whole repository and operational note before removal.
- Test seeds may fail because the new variable is absent from an already configured environment: error message names the missing variable.

## Rules and constraints

- Never print a secret, even a disposable one.
- Explicit configuration, with no magic value embedded in code.
- Seeds are always explicit.

## Plan

- [ ] Context and research
- [ ] Determine the final key list and per-environment value
- [ ] Write tests first for environment-based password
- [ ] Declare keys in the project’s real files
- [ ] Decide and act on `SUPABASE_URL` and `SUPABASE_KEY`
- [ ] Adjust all four test-seed commands
- [ ] Update `docs/OPERACAO-BANCO-SEEDS.md`
- [ ] Validation
- [ ] Cleanup audit

## Test plan

### Tests to author

`system/tests/test_seed_test_commands.py`: every `seed_system_initial_test_*` command fails with a message naming the variable when the password is not configured and uses the variable value when it exists.

### Execution authorization

- Status: authorized by the operator’s explicit 2026-07-25 order.

### Execution evidence

Focused test, `manage.py test system.tests.test_test_seed_fixtures`:

```
Ran 5 tests in 37.353s

OK
```

Three new cases: rejection when `SEED_TEST_PORTAL_PASSWORD` is empty without creating any person; configured password use verified through `check_password`; and absence of `portal_password` in all four fixture JSON files.

Complete suite, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 722 tests in 220.453s

OK
```

The first suite run failed in one case — recorded under `Deviations from plan` — and passed after correction.

## Visual validation

Not applicable. No template, CSS, or JavaScript changed. Transport hardening is verified through `check --deploy`.

## ORM validation

No model, migration, or query change. Test-seed write behavior is covered by the tests above, which run against the suite’s isolated database.

## Quality validation

Key parity across all four files, comparing each sorted name list against `.env`:

```
=== key parity ===
.env.example IDENTICAL to .env
.env.hg IDENTICAL to .env
.env.prod IDENTICAL to .env

total keys: 67
```

Before this PRD: `.env` had 52 keys, `.env.example` 66, `.env.hg` and `.env.prod` 56, with 14 `settings.py`-read keys absent from real files and two dead keys present only there.

`manage.py check --deploy` pointing to `.env.prod`, after `collectstatic` as prescribed by the runbook:

```
WARNINGS:
?: (security.W005) You have not set the SECURE_HSTS_INCLUDE_SUBDOMAINS setting to True...
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True...

System check identified 2 issues (0 silenced).
```

Only the two warnings corresponding to deliberate conservative choices remain. Warnings for missing HSTS, SSL redirect, and cookies without `Secure`, which previously appeared because values fell back to defaults, disappeared because they are now explicitly declared.

Password absent from all versioned files:

```
grep -rn "LvTest" --include=*.md --include=*.py --include=*.json . | grep -v docs/prd/
--- (empty: no occurrence outside docs/prd/) ---
```

The destructive-lifecycle guard remains active with the new variable in its list:

```
[ERROR] Local destructive lifecycle refused: use the local .env file.
EXIT: 1
```

Local database retained the same size and timestamp before and after.

## Evidence

- 67 identical keys in all four environment files, empty diff.
- `check --deploy` with only two deliberate warnings.
- Zero `LvTest` occurrence outside PRD history.
- Five focused tests pass; complete 722-test suite passes.

## Implemented

- The 14 keys read by `settings.py` but absent from real project files were declared with permissive local and restrictive HG/production values: remote `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, and `DJANGO_CSRF_COOKIE_SECURE` are true and `DJANGO_SECURE_HSTS_SECONDS=3600`.
- `SUPABASE_URL` and `SUPABASE_KEY` removed from `.env.hg` and `.env.prod`.
- `SEED_TEST_PORTAL_PASSWORD` created in `lvjiujitsu/settings.py` and declared in all four environment files.
- `system/services/test_seed_fixtures.py`: `_portal_password` reads from settings; `_sync_portal_account` uses it; validation now rejects an absent variable instead of a missing JSON field; `portal_password` removed from `REQUIRED_ENTRY_KEYS`.
- `portal_password` removed from 31 entries across four fixture JSON files.
- `system/tests/test_test_seed_fixtures.py`: existing case now compares against settings, and three new cases were added.
- `SEED_TEST_PORTAL_PASSWORD` added to `clear_migrations.py` `REQUIRED_LOCAL_SEED_SETTINGS`, with two environment tests updated.
- `docs/OPERACAO-BANCO-SEEDS.md` no longer publishes the password and now describes the variable and refusal behavior.

## Cleanup findings

- `staticfiles/` regenerated by `collectstatic` to permit `check --deploy`. It is gitignored output and the procedure is prescribed by the runbook.
- Reconciliation helper script remained outside the repository in the session’s temporary directory.
- Backups of all four environment files were created before changes and discarded after verification.

## Follow-up PRDs

- PRD-161 — slash commands, PRD index, and repository hygiene.
- PRD-162 — hardened remote reset, documented deployment, and observability.

## Deviations from plan

- The plan treated the test password as a documentation problem. Investigation showed it lived in four versioned JSON files, in the `portal_password` field of 31 entries, and the document merely repeated it. Actual scope was larger: service, fixtures, and tests needed changes. Direction remained what the PRD declared.
- `SUPABASE_URL` and `SUPABASE_KEY` were removed instead of read. A search across all Python code found zero references, and the project connects to Supabase exclusively through `DATABASE_URL`. Retaining them would preserve secrets without a consumer.
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` remained `False`, with `SECURE_HSTS_SECONDS` at 3600 rather than a high value. HSTS pins the browser to HTTPS and is expensive to reverse; acceptance required only a nonzero value. The two remaining `check --deploy` warnings are a conscious consequence.
- First suite run broke `test_local_environment_validation_accepts_complete_sqlite_config`: the test creates a synthetic `.env` unaware of the new variable. Both environment tests were updated and the suite returned to green.

## Pending

- Rotate the currently used test password if the operator believes `LvTest@2026` has circulated enough to warrant replacement. It is now a value change in four environment files without code changes.
- Confirm in real staging that `SECURE_SSL_REDIRECT=True` does not produce a redirect loop behind Render’s proxy before applying to production.

## Final status

Completed. All four environment files declare the same 67 keys, every declared key is read by `settings.py`, no password remains in a versioned file, and the complete 722-test suite is green.
