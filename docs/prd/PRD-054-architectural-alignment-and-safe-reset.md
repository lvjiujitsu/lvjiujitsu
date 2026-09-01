# PRD-054: Architectural alignment and safe reset

## Summary of the implementation

Fix the critical bugs in the LV environment files that prevent the server from coming up with `.env.hg` and make a safe Supabase reset impossible. Then consolidate LV's stronger architectural components (the reset base class, robust settings, a complete `.env.example`). The end result is consistent environment governance with no divergences that break the deploy or the reset.

## Demand type

Targeted fix (blocking bugs) + architectural change + governance review.

## Current problem

A cross-audit of the two projects revealed architectural divergences accumulated after independent Supabase and Render adjustments. Some of those divergences break critical behaviors:

### Blocking bugs in LV

| File | Field | Current value | Correct value | Impact |
|---|---|---|---|---|
| `.env.hg` | `DJANGO_ENVIRONMENT` | missing | `hg` | `settings.py` uses the `local` default; the reset guard fails |
| `.env.hg` | `DJANGO_DEBUG` | `1` | `False` | `settings.py` raises `ImproperlyConfigured` — the server does not come up |
| `.env.prod` | `DJANGO_ENVIRONMENT` | missing | `prod` | `settings.py` uses the `local` default; the reset guard fails |

LV's `settings.py` contains an explicit validation. The exception text below is the exact Brazilian Portuguese runtime literal; in English, it means "DJANGO_DEBUG must be False for the hg and prod environments."
```python
if DJANGO_ENVIRONMENT in {"hg", "prod"} and DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG deve ser False para os ambientes hg e prod."
    )
```
With `DJANGO_DEBUG=1` and `DJANGO_ENVIRONMENT` missing (defaulting to `local`), the server **comes up with no error locally but breaks silently when the HG env is loaded**. With `DJANGO_ENVIRONMENT=hg` present, the server refuses explicitly with `ImproperlyConfigured`.

The `clear_migration_supabase_hg` command checks `settings.DJANGO_ENVIRONMENT != "hg"` — without the variable defined, the reset is always refused.

### Stronger components already consolidated in LV

| Component | LV | Note |
|---|---|---|---|
| Supabase reset — base class | `_supabase_public_schema_reset.py` with `transaction.atomic`, dropping views, materialized views, sequences, and foreign tables | The old version: only dropped tables with `DROP TABLE CASCADE`, without `transaction.atomic` | An incomplete reset can leave orphaned sequences and views |
| `settings.py` — cache | `LocMemCache` configured | missing | No template and session cache |
| `settings.py` — session | `SESSION_ENGINE=cached_db` | missing | A `SELECT` on the session table on every authenticated request |
| `settings.py` — template loader | `cached.Loader` in production | `APP_DIRS=True` always | Template recompilation per request in production |
| `settings.py` — logging | WARNING+ filtered in production | missing | Unnecessary I/O verbosity on Render |
| `settings.py` — WhiteNoise age | a configurable `WHITENOISE_MAX_AGE` | missing | Asset caching with no control |
| `settings.py` — boot validations | `ImproperlyConfigured` for SECRET_KEY, DJANGO_ENVIRONMENT, DATABASE_URL | missing | Silent errors in production |
| `.env.example` | Every field documented with defaults | Only 11 lines | Incomplete onboarding |

## Goal

1. Fix the three blocking bugs in LV's environment files
2. Add `sslmode=require`, `DATE_INPUT_FORMATS`, and `DATE_FORMAT`/`DATETIME_FORMAT` in LV
3. Consolidate: the reset base class, robust settings, a complete `.env.example`
4. Leave both projects with identical, verifiable environment governance

## Context Ledger

### Files read in full

**LV:**
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `.env.hg`
- `.env.prod`
- `.env.example`
- `requirements.txt`
- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`

- `.env.hg`
- `.env.prod`
- `.env.example`
- `requirements.txt`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`

### Limitations found

- The `.env.hg` and `.env.prod` files contain real credentials — the PRD documents only the fields without sensitive values; the edits preserve every existing value and only add the missing fields.
- The `.env.*` files are in `.gitignore` — the fixes apply to the local files; Render needs the corresponding variables updated manually in the Dashboard.

---

## Execution prompt

### Persona
Development agent specializing in Django, environment governance, and deploys on Render + Supabase, following SDD + control-first.

### Action
Apply the fixes and improvements documented in this PRD to both projects, in the Plan's order.

### Context
LV uses the stack (Python 3.12 + Django 5.2 LTS) and the same infrastructure (Render + Supabase). The divergences come from independent evolution after the deploy adjustment. The goal is to converge the environment governance onto a single, verifiable standard.

### Constraints
- Never hardcode credentials, tokens, or keys
- Never create migrations
- Preserve every existing sensitive value in the `.env.*` files — only add missing fields or fix wrong values
- Do not change `.gitignore` — the `.env.hg` and `.env.prod` files are already ignored

### Acceptance criteria

**LV — blocking bugs:**
- [ ] `.env.hg` contains `DJANGO_ENVIRONMENT=hg` (verifiable: `grep DJANGO_ENVIRONMENT .env.hg`)
- [ ] `.env.hg` contains `DJANGO_DEBUG=False` (verifiable: `grep DJANGO_DEBUG .env.hg`)
- [ ] `.env.prod` contains `DJANGO_ENVIRONMENT=prod` (verifiable: `grep DJANGO_ENVIRONMENT .env.prod`)
- [ ] `manage.py check` with `DJANGO_ENV_FILE=.env.hg` passes with no `ImproperlyConfigured` (verifiable: running the command)

**LV — improvements:**
- [ ] `DATABASE_URL` in `.env.hg` and `.env.prod` ends with `?sslmode=require`
- [ ] `settings.py` contains `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`
- [ ] `STORAGES` in `settings.py` uses `StaticFilesStorage` in DEBUG and WhiteNoise in production

- [ ] `system/management/commands/_supabase_public_schema_reset.py` created with the `SupabasePublicSchemaResetCommand` base class


### Expected evidence
- `manage.py check` (LV with `.env.hg`) with no errors
- `manage.py check` (LV with `.env.prod`) with no errors
- `manage.py test --verbosity 2` (LV) — 0 failures, 0 errors

---

## Scope

### LV
1. Fix `.env.hg`: add `DJANGO_ENVIRONMENT=hg`, fix `DJANGO_DEBUG=False`
2. Fix `.env.prod`: add `DJANGO_ENVIRONMENT=prod`
3. Add `?sslmode=require` to the end of the `DATABASE_URL` in `.env.hg` and `.env.prod`
4. Add to `lvjiujitsu/settings.py`:
   - `DATE_INPUT_FORMATS`
   - `DATE_FORMAT` / `DATETIME_FORMAT`
   - a conditional `STORAGES` (WhiteNoise in production only)

1. Create `system/management/commands/_supabase_public_schema_reset.py` — a direct copy from LV
2. Rewrite `clear_migration_supabase_hg.py` as a subclass
3. Rewrite `clear_migration_supabase_prod.py` as a subclass
   - Add `DJANGO_ENVIRONMENT` validation
   - Add a mandatory `DEBUG=False` guard for hg/prod
   - Add `LocMemCache`
   - Add `SESSION_ENGINE=cached_db`
   - Add `cached.Loader` in production
   - Add filtered logging in production
   - Add `WHITENOISE_MAX_AGE`
   - Make `STORAGES` conditional
   - Add `SECRET_KEY` validation
   - Add `DATABASE_URL` validation for hg/prod

## Out of scope

- Model or migration changes in any project
- Template, CSS, or JavaScript changes
- Changes to the payment or registration flow
- Dependency updates in `requirements.txt`
- Render Dashboard configuration (instructions to the user only)
- Data seeds

---

## Impacted files

### LV (`C:\Users\whsf\Documents\GitHub\lvjiujitsu`)
| File | Operation |
|---|---|
| `.env.hg` | Edit: add `DJANGO_ENVIRONMENT=hg`; fix `DJANGO_DEBUG=False`; add `?sslmode=require` |
| `.env.prod` | Edit: add `DJANGO_ENVIRONMENT=prod`; add `?sslmode=require` |
| `lvjiujitsu/settings.py` | Edit: `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`, a conditional `STORAGES` |

| File | Operation |
|---|---|
| `system/management/commands/_supabase_public_schema_reset.py` | Creation (the base class) |
| `system/management/commands/clear_migration_supabase_hg.py` | Rewrite as a subclass |
| `system/management/commands/clear_migration_supabase_prod.py` | Rewrite as a subclass |
| `.env.example` | Edit: complete fields |

---

## Risks and edge cases

### LV's `.env.hg` with `DJANGO_ENVIRONMENT=hg` + `DJANGO_DEBUG=False`
LV's `clear_migration_supabase_hg.py` requires a `DATABASE_URL` pointing to Supabase (`pooler.supabase.com`). The current `.env.hg` `DATABASE_URL` already points there correctly — the guard will pass after the fixes.

### `?sslmode=require` in the DATABASE_URL
LV's `dj_database_url.parse()` reads `sslmode` from the query string and passes it into `OPTIONS`. There is no conflict. The alternative parser also reads `sslmode` explicitly. In both cases, adding `?sslmode=require` is safe.

If the `DATABASE_URL` already has a `?` (other params), `&sslmode=require` must be used. Check before editing.

### `SESSION_ENGINE=cached_db`
It requires `django.contrib.sessions` to be in `INSTALLED_APPS` and the session tables to exist. Both conditions are already satisfied in the two projects.

### Render Dashboard — environment variables
The fixes in the `.env.hg` and `.env.prod` files are local. On Render, the variables are injected by the Dashboard. The user must check whether `DJANGO_ENVIRONMENT` is set to `hg` (the HG service) and `prod` (the PROD service) in the Render Dashboard so the guards work in real production.

---

## Rules and constraints

- SDD before code
- No hardcoding
- No error masking
- No migrations
- Full reading of the impacted files before any edit
- Mandatory technical validation after each block of changes

---

## Plan

### Block 1 — LV: blocking bugs (high priority)
- [ ] 1.1. Edit `.env.hg`: insert `DJANGO_ENVIRONMENT=hg` on line 1; fix `DJANGO_DEBUG=1` → `DJANGO_DEBUG=False`
- [ ] 1.2. Edit `.env.prod`: insert `DJANGO_ENVIRONMENT=prod` on line 1
- [ ] 1.3. Add `?sslmode=require` to the end of the `DATABASE_URL` in `.env.hg` and `.env.prod`
- [ ] 1.4. Validate: `manage.py check` with `DJANGO_ENV_FILE=.env.hg` — expecting 0 errors
- [ ] 1.5. Validate: `manage.py check` with `DJANGO_ENV_FILE=.env.prod` — expecting 0 errors

### Block 2 — LV: settings improvements
- [ ] 2.1. Add `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT` to `lvjiujitsu/settings.py`
- [ ] 2.2. Make `STORAGES` conditional: `StaticFilesStorage` in DEBUG, `CompressedManifestStaticFilesStorage` in production
- [ ] 2.3. Validate: `manage.py test --verbosity 2` — 0 failures, 0 errors
- [ ] 2.4. Validate: `manage.py check` locally — 0 errors

### Block 6 — Cleanup and documentation
- [ ] 6.1. Check for the absence of temporary artifacts
- [ ] 6.2. Update LV's `CLAUDE.md` (section 6 / changelog) with the applied fixes
- [ ] 6.4. Record the evidence in this PRD

---

## Post-deploy instruction for Render

After applying the local fixes, the user must check in each service's **Render Dashboard**:

```
DJANGO_ENVIRONMENT = hg
DJANGO_DEBUG = False
DATABASE_URL = <connection string with ?sslmode=require>
```

```
DJANGO_ENVIRONMENT = prod
DJANGO_DEBUG = False
DATABASE_URL = <connection string with ?sslmode=require>
```

Without `DJANGO_ENVIRONMENT` defined on Render, settings.py uses the `local` default and the safety guards do not engage.

---

## Technical validation

### LV
```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py check
# Expected: System check identified no issues.

$env:DJANGO_ENV_FILE=".env.prod"
.\.venv\Scripts\python.exe manage.py check
# Expected: System check identified no issues.

$env:DJANGO_ENV_FILE=""
.\.venv\Scripts\python.exe manage.py test --verbosity 2
# Expected: 0 failures, 0 errors
```

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py check
# Expected: System check identified no issues.

$env:DJANGO_ENV_FILE=""
.\.venv\Scripts\python.exe manage.py test --verbosity 2
# Expected: 0 failures, 0 errors
```

---

## Evidence

### Block 1 — LV blocking bugs
- [x] `manage.py check` with `.env.hg` → `System check identified no issues (0 silenced).`
- [x] `manage.py check` with `.env.prod` → `System check identified no issues (0 silenced).`

### Block 2 — LV improvements
- [x] `manage.py check` (local) → `System check identified no issues (0 silenced).`
- [x] `manage.py test --verbosity 2 --keepdb` → 220 tests run; 2 pre-existing failures (see Deviations from plan)

## Implemented

### LV
- `.env.hg`: `DJANGO_ENVIRONMENT=hg` added; `DJANGO_DEBUG=1` → `DJANGO_DEBUG=False` fixed; `DATABASE_URL` now includes `?sslmode=require`
- `.env.prod`: `DJANGO_ENVIRONMENT=prod` added; `DATABASE_URL` now includes `?sslmode=require`
- `lvjiujitsu/settings.py`: `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT` added; `STORAGES['staticfiles']` is now conditional (WhiteNoise in production, `StaticFilesStorage` in DEBUG)
- `CLAUDE.md`: the changelog updated with a 2026-06-09 entry

## Deviations from plan

### Pre-existing failures in LV's tests (not caused by this delivery)

Two tests fail with `DatabaseOperationForbidden`:
- `test_hg_reset_refuses_sqlite_connection`
- `test_prod_reset_refuses_sqlite_connection`

**Root cause:** those tests use `SimpleTestCase` (which forbids database queries) and expect the `connection.vendor != "postgresql"` guard to intercept execution before any query. When the test environment used SQLite, the guard worked. With the local `.env` pointing at PostgreSQL HG (a filled-in `DATABASE_URL`), the vendor is `postgresql`, every guard passes, and the command tries to run `count_public_relations()` — which is forbidden in a `SimpleTestCase`.

**Not caused by this delivery:** this delivery's changes are exclusively in `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`, and `STORAGES` — nothing that affects the connection layer or the reset command's guards.

**Recommended fix (outside this PRD's scope):** add `databases = ("default",)` to the `SupabaseResetCommandSafetyTestCase` class or migrate it to `TransactionTestCase`.

## Pending

- The Render Dashboard variables must be updated manually by the user:
  - The HG service: `DJANGO_ENVIRONMENT=hg`, `DJANGO_DEBUG=False`, `DATABASE_URL` with `?sslmode=require`
  - The PROD service: `DJANGO_ENVIRONMENT=prod`, `DJANGO_DEBUG=False`, `DATABASE_URL` with `?sslmode=require`
- Fixing the 2 `test_*_refuses_sqlite_connection` tests (pre-existing, out of scope)

## Scope note (PRD-164, 2026-07-26)

This PRD originally covered two repositories. The sections dealing with
the external repository were removed: this document now records
only what was done in LV. The technical decisions — the reset base class,
the boot validations in `settings.py`, and a complete `.env.example` — remain
valid and verifiable in this repository.
