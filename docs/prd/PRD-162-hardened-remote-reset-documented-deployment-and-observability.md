# PRD-162: Hardened Remote Reset, Documented Deployment, and Observability

## Summary

Adopt in LV three operational defenses it lacks: identify the Supabase project during remote reset with simulation mode by default, block the Data API through RLS with a read-only audit mode, and create a deployment document containing Build Command, Start Command, and health check. Also add the currently missing `clear_test_data` and `check_database_connection` commands.

## Demand type

Remote infrastructure, deployment, and observability. No business-rule change.

## Current problem

1. `system/management/commands/_supabase_public_schema_reset.py` validates environment, `DEBUG=False`, Supabase host, `SUPABASE_RESET_CONFIRM`, and database vendor, but **executes `DROP` on the first successful invocation**. It has no simulation mode and does not verify which Supabase project is targeted. With two provisioned projects and the correct confirmation variable exported, an accidentally swapped `DATABASE_URL` destroys the wrong schema. The required defense is to match `SUPABASE_PROJECT_REF` against the host and to require `--execute` to leave simulation mode.
2. `system/management/commands/lock_supabase_api_access.py` has 46 lines, revokes privileges from `anon` and `authenticated`, but does not enable RLS or offer audit mode. It must enable RLS per table and accept `--check`.
3. Build Command is documented in `CLAUDE.md:84` and `docs/OPERACAO-BANCO-SEEDS.md:137`, but Start Command is not: `CLAUDE.md:87` says only “Gunicorn according to Render service configuration.” No dedicated deployment document exists; the rest lives in an Obsidian note outside the repository.
4. There is no health-check route or `check_database_connection`. Render lacks a cheap endpoint to verify application startup.
5. Four `seed_system_initial_test_*` commands create fictional staging data, but no command removes it. A `clear_test_data` command with explicit confirmation is missing.

## Goal

Remote reset identifies the target project and destroys nothing without `--execute`; the Data API is blocked with auditable RLS; deployment is documented in-repository; and health check, connection check, and reversible test-data removal exist.

## Context Ledger

### Files read in full

- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`
- `system/management/commands/lock_supabase_api_access.py`
- The four `system/management/commands/seed_system_initial_test_*.py` commands
- `lvjiujitsu/settings.py`, `lvjiujitsu/urls.py`
- `CLAUDE.md`, `docs/OPERACAO-BANCO-SEEDS.md`

### Adjacent files consulted

- `.env`, `.env.hg`, `.env.prod`, `.env.example` (structure, not values)
- `system/models/person.py`, `system/models/plan.py`
- `system/middleware.py`

### Internet / official documentation

- [Supabase — Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase — Connecting to your database](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Render — Deploying a Django application](https://render.com/docs/deploy-django)
- [Django — `transaction.atomic`](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#django.db.transaction.atomic)
- [PostgreSQL — `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`](https://www.postgresql.org/docs/current/sql-altertable.html)

### Context7 / MCPs / tools verified

- Context7 available for Django 5.2 and PostgreSQL client material.
- The existing LV infrastructure commands were read directly from disk before being replaced.

### Limitations found

- `SUPABASE_PROJECT_REF` does not yet exist in LV `.env*`; add it to all four variants in coordination with PRD-160, which governs the key set.
- Validation of hardened reset against a real Supabase project depends on the operator; the agent validates through automated tests and simulation mode.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: repository infrastructure audit.
- User approval: explicit operator order on 2026-07-25.
- Date: 2026-07-25.

## Execution prompt

### Persona

Platform engineer responsible for LV remote operations.

### Action

Harden the remote-reset guards and block the Data API with RLS; create `docs/DEPLOY-RENDER-SUPABASE.md`, `/health/`, `check_database_connection`, and `clear_test_data`.

### Context

LV Jiu Jitsu runs a single infrastructure model: Render as Web Service and Supabase as PostgreSQL. These items are governed by that model.

### Constraints

- No destructive remote command runs without explicit `--execute`.
- No secret value is printed.
- `clear_test_data` removes only what the four `seed_system_initial_test_*` commands create; the 21 initial seeds remain intact.
- Seeds never enter the Build Command.
- No model or migration change.

### Acceptance criteria

- [ ] `_supabase_public_schema_reset.py` reads `SUPABASE_PROJECT_REF` and rejects a value that does not match the `DATABASE_URL` host.
- [ ] Without `--execute`, the command lists relations that would be removed and emits no `DROP`. Verification: test confirms zero destructive command in simulation mode.
- [ ] With `--execute` and all guards satisfied, current behavior is preserved.
- [ ] `clear_migration_supabase_hg` and `clear_migration_supabase_prod` still require `SUPABASE_RESET_CONFIRM` equal to `RESET_HG` and `RESET_PROD`.
- [ ] `lock_supabase_api_access` enables RLS on `public` schema tables and accepts `--check`, which audits without writing. Verification: test confirms no write in `--check` mode.
- [ ] `lock_supabase_api_access` is idempotent and skips SQLite.
- [ ] `docs/DEPLOY-RENDER-SUPABASE.md` exists with Build Command, complete Start Command (`gunicorn lvjiujitsu.wsgi:application`), per-environment variable list, health check, and auto-deploy policy. No secret in the document.
- [ ] `CLAUDE.md` and `docs/OPERACAO-BANCO-SEEDS.md` reference the new document instead of independently describing deployment.
- [ ] `/health/` returns 200 without authentication or a database query. Verification: route test includes an anonymous user passing through `PortalSessionMiddleware`.
- [ ] `check_database_connection` validates the active connection without changing data and fails clearly when no connection exists.
- [ ] `clear_test_data` requires `--confirm CLEAR_TEST_DATA`, requires `--allow-production` when `DJANGO_ENVIRONMENT` is `prod`, removes only data from four test seeds, and preserves data from 21 initial seeds. Verification: test counts reference records before and after.
- [ ] `SUPABASE_PROJECT_REF` exists in all four `.env*` files.
- [ ] `python manage.py check` passes and the suite is green.

### Expected evidence

Simulation-mode reset output; `lock_supabase_api_access --check` output; preservation-test output; `/health/` response; check and suite output.

### Output format

Diff of commands, `urls.py`, and documents, plus PRD updated with actual execution evidence.

## Scope

- `SUPABASE_PROJECT_REF` and `--execute` guards in remote reset.
- RLS and `--check` in Data API blocking.
- `docs/DEPLOY-RENDER-SUPABASE.md`.
- `/health/` route and `check_database_connection` command.
- `clear_test_data` command.
- `SUPABASE_PROJECT_REF` in all four `.env*` files.

## Out of scope

- Reconciliation of other environment variables (PRD-160).
- Slash commands, index, and hygiene (PRD-161).
- Provisioning or reconfiguring Render and Supabase services.
- Changing 21 initial seeds or four domain-specific academy test seeds.

## Impacted files

- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/lock_supabase_api_access.py`
- `system/management/commands/check_database_connection.py` (new)
- `system/management/commands/clear_test_data.py` (new)
- `lvjiujitsu/urls.py`, `system/views/` (health-check view)
- `system/tests/test_supabase_reset_guards.py` (new)
- `system/tests/test_clear_test_data.py` (new)
- `system/tests/test_health_check.py` (new)
- `docs/DEPLOY-RENDER-SUPABASE.md` (new)
- `CLAUDE.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `.env`, `.env.example`, `.env.hg`, `.env.prod`
- `docs/prd/README.md`

## Risks and edge cases

- Missing `SUPABASE_PROJECT_REF` in an already provisioned environment: command rejects and names the variable.
- Pooler host differs from direct host: accept both official Supabase formats.
- Enabling RLS without a policy could block the application: Django connects as table owner, which is not subject to RLS by default; validate in staging before production.
- `PortalSessionMiddleware` might intercept `/health/` and require a session: route needs an anonymous-user test.
- `clear_test_data` must not delete a real person by name heuristic: identify records through explicit markings created by test seeds, not names or email.

## Rules and constraints

- Services concentrate business and transactions; views remain thin.
- No hardcoded secret, masked error, or query in a loop.
- Destructive Supabase actions require environment, confirmation, and `--execute`.

## Plan

- [ ] Context and research
- [ ] Write tests first for guards, `--check`, and preservation
- [ ] Harden remote reset
- [ ] Add RLS and `--check` to Data API blocking
- [ ] Health check and `check_database_connection`
- [ ] `clear_test_data`
- [ ] `docs/DEPLOY-RENDER-SUPABASE.md` and contract adjustments
- [ ] Validation
- [ ] Cleanup audit

## Test plan

### Tests to author

- `test_supabase_reset_guards.py`: reject mismatched `SUPABASE_PROJECT_REF`; simulation without `DROP`; reject environment, `DEBUG`, host, and confirmation.
- `test_clear_test_data.py`: require `--confirm`; require `--allow-production` in `prod`; preserve initial-seed data.
- `test_health_check.py`: `/health/` returns 200 for anonymous user.

### Execution authorization

- Status: authorized by the operator’s explicit 2026-07-25 order.

### Execution evidence

Focused tests by workstream:

```
system.tests.test_supabase_reset_guards ......... Ran 11 tests OK
system.tests.test_health_check .................. Ran 3 tests OK
system.tests.test_clear_test_data ............... Ran 5 tests OK
```

Complete suite, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 741 tests in 252.065s

OK
```

Suite grew from 722 to 741 tests: 19 new cases.

## Visual validation

`/health/` is an infrastructure route without UI; verified by test, not browser. No product screen changed.

## ORM validation

`test_clear_test_data` counts `PersonType`, `BeltRank`, and `ClassCategory` before fictional seeds and after `clear_test_data`, confirming all three remain identical while fictional people disappear. `Person.objects.count` returns exactly to its pre-test-seed value.

All operations use the suite’s isolated test database. No staging or production write occurred.

## Quality validation

Remote-reset simulation mode, verified by a test intercepting the cursor:

```
Supabase project confirmed: abcdefghijklmnop
Objects found in public schema: 2
 - table public.system_person
 - sequence public.system_person_id_seq
Simulation complete. No object was removed. Review the project and list above
before using --execute.
```

`test_dry_run_does_not_execute_destructive_sql` asserts that the executed SQL list is empty. Without `--execute`, zero commands.

Project guard in the scenario this PRD exists to prevent — one project’s `DATABASE_URL` with another project’s `SUPABASE_PROJECT_REF`:

```
CommandError: The connection does not match the expected SUPABASE_PROJECT_REF.
```

Accepts both official Supabase host forms: pooler (`postgres.<ref>@aws-0-...pooler.supabase.com`) and direct (`db.<ref>.supabase.co`).

`lock_supabase_api_access --check` on SQLite:

```
Local database is not PostgreSQL; Data API blocking skipped.
```

`check_database_connection`:

```
Valid local SQLite connection: version=3.49.1.
--require-postgresql on SQLite:
CommandError: PostgreSQL was required, but the active database is sqlite.
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Evidence

- 19 new tests pass; complete 741-test suite passes.
- Simulation mode proven by test: zero destructive SQL without `--execute`.
- `SUPABASE_PROJECT_REF` guard rejects a mismatched project.
- `/health/` returns 200 for anonymous users with `assertNumQueries(0)`.
- `clear_test_data` preserves all three reference counts.

## Implemented

- `SUPABASE_PROJECT_REF` in `lvjiujitsu/settings.py` and all four environment files.
- `_supabase_public_schema_reset.py`: `validate_project_ref` checks the reference against host; `--execute` with simulation by default; `list_public_relations` and `RELKIND_LABELS` for readable listing.
- `system/tests/test_supabase_reset_guards.py` with 11 cases.
- Replaced `lock_supabase_api_access` with a version that enables per-table RLS and offers a nonwriting `--check`, using the `system_` table prefix.
- Added `check_database_connection` with `--require-postgresql`.
- `HealthCheckView` in `system/views/auth_views.py` and `health/` route in `system/urls.py`; `system/tests/test_health_check.py` with three cases.
- Created `clear_test_data`, identifying people by CPF from fixture JSON and relationships by `TEST_SEED_NOTE`; `system/tests/test_clear_test_data.py` with five cases.
- Created `docs/DEPLOY-RENDER-SUPABASE.md` with Build, Start, health check, variable groups, Supabase, auto-deploy, and reset ritual.
- `CLAUDE.md`, `AGENTS.md`, and `docs/OPERACAO-BANCO-SEEDS.md` now reference the deployment document instead of independently describing the subject.

## Cleanup findings

- **Guard order required revision.** Placing `SUPABASE_PROJECT_REF` validation before confirmation broke four preexisting `SupabaseResetCommandSafetyTestCase` tests expecting confirmation/vendor messages. The guard moved to the end: first “am I authorized?” and “is this PostgreSQL?”, then “is this the correct project?”. All four returned green unchanged.
- **Second plaintext password found:** `docs/OPERACAO-BANCO-SEEDS.md:110` publishes `lv-pessoas-2026`, password for `seed_system_people_flow_samples`. PRD-160 covered only `LvTest@2026`. The command is marked obsolete and emits `DeprecationWarning`; this item is outside this PRD. Recorded under `Follow-up PRDs`.
- `system/urls.py` uses `app_name = "system"`, so route name is `reverse("system:health")`. Render uses `/health/`, which does not depend on namespace.
- No residue introduced.

## Follow-up PRDs

- LV: remove `lv-pessoas-2026` from `docs/OPERACAO-BANCO-SEEDS.md:110` together with a decision about retiring already-obsolete `seed_system_people_flow_samples`.
- LV: create `scripts/validate_skill_frontmatter.py` and connect it to CI. This is the last CI-homogeneity item.

## Deviations from plan

- The guard order validates `SUPABASE_PROJECT_REF` after confirmation, to preserve contracts proven by four preexisting tests. The guard set is complete; only the first error changes when multiple failures coexist.
- `lock_supabase_api_access` was replaced wholesale rather than incrementally. The new version already covered everything the previous one did; merging would create a third behavior without benefit.
- LV Build Command **did not** gain `create_admin_superuser`. In LV, superuser creation is a one-time explicit operation; adding it to build would change operational behavior without a request.

## Pending

- Run hardened reset against real staging Supabase; depends on operator. `SUPABASE_PROJECT_REF` was created empty in all four files and must be populated with each project’s actual reference before the next reset — **without it, the command rejects**, as intended.
- Register `SUPABASE_PROJECT_REF` and Health Check Path `/health/` in both Render services.
- Confirm in staging that `lock_supabase_api_access` with RLS does not affect the application before applying to production. Django connects as table owner, which is not subject to RLS by default, but this must be observed in the real environment.

## Final status

Completed with external limitations. Everything repository-dependent is implemented and verified by 19 new tests, with the complete 741-test suite green. Limitations concern provisioning and service configuration, are listed under `Pending`, and block neither local use nor the next delivery.
