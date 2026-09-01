# PRD-053: Safe Render/Supabase reset

## Summary of the implementation
Prepare the project for a manual deploy on Render with Supabase HG and PROD, removing fragile deploy automation, adding explicit reading of environment files, and creating safe destructive commands to clear the `public` schema of the remote databases.

## Demand type
Architectural change, external integration, security review, and documentation regeneration.

## Current problem
The deploy is partly automated through fragile files (`render.yaml`, `build.sh`, `bootstrap.py`) that do not reflect the desired flow. `bootstrap.py` masks seed failures, `render.yaml` uses variables misaligned with `settings.py`, and the project has no auditable commands for a remote HG/PROD reset.

## Goal
Leave the repository as the reliable source of the application's behavior, and leave Render configured manually in the dashboard. A remote reset must require the correct environment, an explicit confirmation, and observable validation before any deploy with a clean database.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `.env.example`
- `system/tests/test_commands.py`
- `system/management/commands/bootstrap.py`
- `system/management/commands/create_admin_superuser.py`
- `render.yaml`
- `build.sh`

### Adjacent files consulted
- `system/management/commands/`
- `docs/prd/`

### Internet / official documentation
- Django downloads/supported versions — Django 5.2 LTS 5.2.14 with extended support until April 2028.
- Django 5.2 release notes — Django 5.2 is an LTS.
- Render free instances — a free web service with no shell/one-off jobs.
- Render deploys — the pre-deploy command is available for paid/private plans and background workers.
- Supabase connect to Postgres — the session pooler for persistent application traffic.
- Supabase backups — the free tier requires external dumps/logical backups.

### MCPs / tools verified
- The Supabase skill — read — applied to the reset and security rules.
- Context7 — unavailable due to an OAuth token that expired in a previous check; fallback to the official web documentation.

### Limitations found
- The agent must not insert, display, or copy secrets from `.env.hg`/`.env.prod` into Render.
- The agent must not run a destructive remote reset without the user's intervention.
- Render free provides no shell/one-off jobs to run commands after the deploy.

## Execution prompt
### Persona
Development agent specializing in Django, Render, and Supabase, following SDD + TDD + control-first operation.

### Action
Implement the manual Render deploy flow + a safe Supabase HG/PROD reset according to the spec below.

### Context
The system must come up as a shell with no mandatory seeds. Initial and legacy data must be loaded only through manual, auditable commands.

### Constraints
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation
- do not run a remote reset without human authorization
- do not commit without human authorization

### Acceptance criteria
- [x] `render.yaml`, `build.sh`, and `bootstrap.py` removed from the versioned flow (verifiable through `git status`).
- [x] `settings.py` supports `DJANGO_ENV_FILE` and fails when an explicitly configured file does not exist (verifiable through a test/command).
- [x] `DJANGO_ENVIRONMENT` exists and accepts `local`, `hg`, or `prod` (verifiable through `manage.py check`).
- [x] `requirements.txt` pins Django 5.2 LTS (verifiable by reading it and through `pip show Django`).
- [x] `clear_migration_supabase_hg` refuses SQLite, `DEBUG=True`, an environment other than `hg`, and a missing confirmation (verifiable through a test).
- [x] `clear_migration_supabase_prod` refuses SQLite, `DEBUG=True`, an environment other than `prod`, and a missing confirmation (verifiable through a test).
- [x] The remote reset limits the cleanup to the `public` schema and preserves Supabase's internal schemas (verifiable by inspecting the SQL).
- [x] `.env.example` contains no secret, real project ref, real password, or external key (verifiable by reading it).
- [x] `CLAUDE.md` documents the manual Render setup, Django 5.2 LTS, and the remote reset commands (verifiable by reading it).

### Expected evidence
- `python -m pip check`
- `python manage.py check`
- `python manage.py test --verbosity 2`
- `python manage.py collectstatic --noinput`
- the destructive command tests passing
- `git diff --stat`

### Output format
Implemented code + tests + validation evidence + pending items requiring human intervention.

## Scope
- The Django environment configuration.
- Governance of the manual Render deploy.
- Safe Supabase HG/PROD reset commands.
- Security tests for the commands.
- Operational documentation.

## Out of scope
- Running a real reset in HG or PROD.
- Entering env vars in Render.
- Triggering a Render deploy.
- Creating/changing the model schema.
- Creating migrations.
- Running remote seeds.

## Impacted files
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `.env.example`
- `CLAUDE.md`
- `system/tests/test_commands.py`
- `system/management/commands/`
- `docs/prd/`
- `render.yaml`
- `build.sh`

## Risks and edge cases
- A remote cleanup can delete data irreversibly; it requires an explicit confirmation.
- The Supabase free tier requires an external backup before a reset when the data matters.
- Render free does not allow a remote shell, so post-deploy commands must run locally against Supabase.
- Database URLs through the pooler must be checked per environment to avoid a cross-environment reset.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
Not applicable in this delivery; there is no UI change.

### Mobile
Not applicable in this delivery; there is no UI change.

### Browser console
Not applicable in this delivery; there is no UI change.

### Terminal
Validate with checks, tests, and collectstatic.

## ORM validation
### Database
The local environment uses SQLite for tests. HG/PROD will not be touched until human intervention.

### Shell checks
Validate the settings reading and the commands' contracts without running a remote reset.

### Flow integrity
The deploy must migrate and bring up the shell with no seeds.

## Quality validation
### No hardcoding
No secrets, real hosts, or project refs in code/example documentation.

### No brittle conditional structures
The commands use guard clauses and explicit validation.

### No `except: pass`
Do not introduce silent error handling.

### No error masking
Remove `bootstrap.py`, which masked seed failures.

### No unnecessary comments or docstrings
Comments only for destructive warnings and operational decisions.

## Evidence
- `.\.venv\Scripts\python.exe --version` — Python 3.12.10.
- `.\.venv\Scripts\python.exe -m pip show Django` — Django 5.2.14.
- `.\.venv\Scripts\python.exe -m pip check` — `No broken requirements found.`
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py check` — `System check identified no issues (0 silenced).`
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py test --verbosity 2` — 220 tests, OK.
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 374 static files recognized, 847 post-processed.
- `manage.py check --deploy` with simulated PROD variables — only `security.W021` about `SECURE_HSTS_PRELOAD`; kept off by default because it is an explicit domain/preload decision.
- The initial Red slice of the destructive commands — 12 tests, 9 expected failures before the implementation.
- The Green slice of the destructive commands — 12 tests, OK.

## Implemented
- `render.yaml`, `build.sh`, and `system/management/commands/bootstrap.py` removed.
- `settings.py` now supports `DJANGO_ENV_FILE`, `DJANGO_ENVIRONMENT`, blocking HG/PROD with `DEBUG=True`, and blocking HG/PROD with no `DATABASE_URL`.
- `settings.py` uses `DB_CONN_MAX_AGE=0` and `DISABLE_SERVER_SIDE_CURSORS=True` for safe compatibility with the Supabase Transaction Pooler.
- `requirements.txt` pinned to `Django==5.2.14`; `.python-version` pinned to `3.12.10`.
- `.env.example` sanitized and aligned with local/HG/PROD.
- `.gitignore` ignores `.env.hg`, `.env.prod`, the local Claude config, and the Kanri migration's personal data.
- `clear_migration_supabase_hg` and `clear_migration_supabase_prod` created, with a shared base and destructive guards.
- `CLAUDE.md` updated with the manual Render setup, Supabase HG/PROD, the reset commands, and the rule that seeds stay out of the deploy.

## Deviations from plan
- `HSTS_PRELOAD` was not enabled by default. The deploy check keeps emitting `security.W021`, but that setting requires an explicit domain decision and submission to the preload list.
- `.claude/settings.local.json` was added to `.gitignore`, but it was not removed from the index at this stage because that requires a controlled stage/commit.

## Pending
- The user configuring the env vars in Render.
- The user authorizing the stage/commit.
- The user authorizing the remote HG/PROD reset.
- The user triggering the manual deploy or providing the Render logs.
