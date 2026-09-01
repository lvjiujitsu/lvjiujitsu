# PRD-165: Honest Test Runner and Direct Dependencies

## Summary

Correct the test runner’s name and scope, which claims to run on PostgreSQL but does not; move `STATIC_ROOT` creation outside the test path; and reduce `requirements.txt` to the project’s direct dependencies.

## Demand type

Infrastructure and configuration. No business-rule or schema change.

## Current problem

1. **The name `PostgreSQLDiscoverRunner` claims more than the class does.** It inherits from `DiscoverRunner` and **does not select a database**: it does not change `DATABASES`, configure the `TEST` key, or force an engine. The engine comes from configuration like any other run — SQLite when `DATABASE_URL` is empty, as in the local environment.

   The class does have one PostgreSQL-specific behavior: `teardown_databases` terminates remaining sessions when `conn.vendor == "postgresql"`, without which dropping the test database fails because a connection remains open. This behavior is necessary and correct when the suite runs against PostgreSQL. The name, however, generalizes this teardown detail into the runner’s identity.

   The harm is interpretive: someone reading `TEST_RUNNER = '...PostgreSQLDiscoverRunner'` in `settings.py` concludes the suite covers the production engine. Locally it does not — it uses SQLite. A PostgreSQL-only constraint or sorting/type difference can pass green and fail in staging. The name suggests nonexistent coverage.

   The class’s other responsibilities — creating `STATIC_ROOT` and disabling logging through `WARNING` — are also unrelated to its name.

2. **`STATIC_ROOT` is created inside the test runner.** The directory is required by `collectstatic` and WhiteNoise in every execution, not only tests. Creating it only in the test path means `collectstatic` fails immediately after a destructive lifecycle, before the directory exists, and running the suite “repairs” the environment as a side effect, making the same command depend on what ran earlier.

3. **`requirements.txt` has 49 lines including transitive dependencies.** It lists packages the project does not import — `annotated-types`, `anyio`, `certifi`, `cffi`, `h11`, `hpack`, `hyperframe`, `idna`, `mdurl`, `propcache`, `pycparser`, `pydantic_core`, `six`, `typing-inspection`, `urllib3`, and others — solely because direct packages require them.

   This obscures what the project chose versus what `pip` resolved. Removing a direct dependency leaves its transitives pinned without ownership. Updating a direct dependency can be blocked by a stale transitive pin with an error that hides the cause.

4. **`.gitignore` contains entries matching no file.** `.env-prod` and `.env-hg` use hyphens alongside `.env.prod` and `.env.hg`. Real files use dots. Hyphen entries imply a naming convention adopted nowhere.

5. **`.claude/scheduled_tasks.lock` is neither tracked nor ignored.** It is an agent-tool runtime artifact present in the working tree and absent from `.gitignore`, appearing in every `git status` and vulnerable to broad `git add`.

6. **`kill_project_python_processes` protects only the direct parent.** The filter excludes `current_pid` and `os.getppid()`. This covers the common case because `.venv/Scripts/python.exe` is a shim executing the base interpreter and appears in WMI as a distinct in-repository executable, matching `is_project_python_process`.

   It does not protect ancestors above the parent. An in-repository Python grandparent remains a valid target and is terminated. Damage is limited because termination uses `taskkill /F` without `/T`, so killing an ancestor on Windows does not kill the descendant — the lifecycle does not self-destruct. But terminating an unrelated process remains wrong and surprises the operator.

## Goal

The runner name describes its behavior. `STATIC_ROOT` exists independently of suite execution. `requirements.txt` lists project choices. A clean `git status` shows no runtime artifact. Process termination never reaches an ancestor of the running script.

## Context Ledger

### Files read in full

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `AGENTS.md` sections 7 and 8

### Adjacent files consulted

- `.github/workflows/ci.yml` — suite invocation in CI
- `clear_migrations.py` — artifacts removed by lifecycle
- `docs/OPERACAO-BANCO-SEEDS.md` — canonical local lifecycle order
- Sample under `system/tests/` using `assertLogs`, confirming logging suppression must remain at `WARNING`

### Internet / official documentation

- Django 5.2: `TEST_RUNNER`, `DiscoverRunner`, `DATABASES.TEST`, and test-database configuration.
- Django 5.2: `STATIC_ROOT`, `collectstatic`, and directory requirements.
- `pip`: dependency resolution and `pip check`.

### Context7 / MCPs / tools verified

- Context7 consulted for Django 5.2 (test runner, test database, static files) and `pip check` behavior.
- `pip check` and full-suite execution used for verification.

### Limitations found

- Confirming the suite’s engine requires runtime observation, not reading: evidence is runner output naming the created test database.
- Actually moving the suite to PostgreSQL is outside this PRD; it requires a database service in CI and locally. This PRD corrects the name so it stops claiming nonexistent behavior.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

Explicit operator order authorized infrastructure fixes and implementation without further confirmation. Decision: suite remains on Django’s default test database; `requirements.txt` lists only direct dependencies, with transitive resolution delegated to `pip` and validated by CI `pip check`.

## Execution prompt

### Persona

Django engineer responsible for LV test and dependency infrastructure.

### Action

Rename the runner to describe actual behavior, move `STATIC_ROOT` creation into `settings.py`, reduce `requirements.txt` to direct packages, and correct `.gitignore`.

### Context

The suite uses Django’s default test database. `STATIC_ROOT` is needed outside tests. CI already validates dependency resolution with `pip check`.

### Constraints

- Logging suppression remains limited to `WARNING`, preserving tests using `assertLogs(level="ERROR")`.
- WhiteNoise warning filter remains.
- No test may be removed, adapted, or marked expected-failure to accommodate the change.
- Removing a transitive pin must not change any direct dependency’s installed version.
- Test count before and after must be identical.

### Acceptance criteria

1. Class name describes its role without claiming a database engine, and the old name is unused across the repository. PostgreSQL remains mentioned only where true: `teardown_databases` and the rename-explaining docstring.
2. `settings.py` references the new `TEST_RUNNER` name.
3. `settings.py` creates missing `STATIC_ROOT` outside the test path.
4. Runner no longer creates `STATIC_ROOT`.
5. `collectstatic --noinput` passes immediately after a destructive local lifecycle before the suite runs.
6. `logging.disable(logging.WARNING)` remains, and `assertLogs(level="ERROR")` tests pass.
7. `requirements.txt` lists only project-imported or execution-required packages (server, database driver, static files), without transitives.
8. `pip check` passes in an environment recreated from the new `requirements.txt`.
9. `pip freeze` in the recreated environment resolves the same direct dependency versions as before.
10. `.gitignore` contains neither `.env-prod` nor `.env-hg` and still ignores `.env.prod` and `.env.hg`.
11. `.gitignore` ignores `.claude/scheduled_tasks.lock`.
12. `git status --short` is clean in a freshly reset working tree.
13. `ancestor_pids` exists, and `kill_project_python_processes` protects current PID and every ancestor, not only direct parent.
14. `ancestor_pids` terminates even with a cycle in the parent map, and a sibling process remains a valid target.
15. Complete suite green with unchanged test count.

### Expected evidence

Actual output: suite before/after with count, `pip check`, compared `pip freeze`, `collectstatic` after reset, `git status --short`, and test-database name reported by runner.

### Output format

Diff, command output, and updated PRD.

## Scope

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`

## Out of scope

- Moving suite to PostgreSQL: requires database service in CI/local and is an architectural decision outside this scope.
- Changing any existing test.
- Changing database driver, application server, or static backend.
- Upgrading a direct dependency; this PRD removes transitives only.

## Impacted files

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `docs/prd/README.md`

## Risks and edge cases

- **Removing transitive pin changes installed version.** Mitigation: compare recreated-environment `pip freeze`; investigate any direct version change before closure.
- **A supposed transitive is actually direct.** Check every removal against real code imports, not intuition.
- **`assertLogs(level="ERROR")` breaks.** Keep suppression at `WARNING` and explicitly run dependent tests.
- **Rename leaves orphan reference.** Search old name across repository afterward.
- **`STATIC_ROOT` creation during settings import in read-only environment.** Use `exist_ok` and tolerate permission failure with a visible, unmasked error.

## Rules and constraints

`AGENTS.md` section 7: do not declare Green without real command output; tests use an isolated database and do not touch local SQLite. Section 10: clear names, explicit configuration, no masked errors. Section 2: contract describes what exists — a name asserting nonexistent behavior is the same defect class.

## Plan

1. Run full suite and record count and test-database name.
2. Record current-environment `pip freeze`.
3. Rename class and adjust `TEST_RUNNER`.
4. Move `STATIC_ROOT` creation to `settings.py`.
5. Reduce `requirements.txt`, checking each removal against imports.
6. Recreate virtual environment from new file and run `pip check`.
7. Compare `pip freeze` with previous record.
8. Run destructive lifecycle, `collectstatic` before suite, and full suite.
9. Correct `.gitignore` and inspect `git status --short`.

## Test plan

- Existing suite is the regression test: same count, all green.
- Explicit execution of tests using `assertLogs(level="ERROR")`.
- `collectstatic --noinput` after reset, before any test run.
- `pip check` in recreated environment.

## Visual validation

Not directly applicable. Because `collectstatic` is in scope, open an authenticated route after reset to confirm CSS is served, recording a screenshot.

## ORM validation

Not applicable: no model, query, or migration change. Relevant database verification is which test database the runner creates, evidenced at runtime.

## Quality validation

`pip check`, `python manage.py check`, `makemigrations --check --dry-run`, `collectstatic --noinput`, and complete suite with compared count.

## Evidence

- `manage.py check`: “no issues (0 silenced).”
- Renamed runner import resolves: `from system.test_runner import ProjectDiscoverRunner`.
- Repository search for `PostgreSQLDiscoverRunner`: no occurrence outside this PRD and the rename-explaining docstring.
- **Criterion 5 proven in required order.** After destructive lifecycle, `Test-Path staticfiles` returned `False`; `collectstatic --noinput` then ran **before the suite** and copied 381 files with exit code 0.
- Destructive lifecycle with locked database: an in-repository Python process held `db.sqlite3` in WAL with an open transaction. Actual output: `[OK] Finished: PID 32692`, `[OK] SQLite files removed: 3`, `[OK] Migrations removed: 1`, `[OK] Cleanup completed successfully.`, exit code 0, no remaining `db.sqlite3*`.
- `pip check` in a **from-scratch recreated environment** from new `requirements.txt`: “No broken requirements found.”
- Recreated-environment `pip freeze` resolves all ten direct dependencies at the same versions: Django 5.2.14, python-decouple 3.8, tzdata 2026.1, gunicorn 26.0.0, whitenoise 6.12.0, psycopg2-binary 2.9.12, dj-database-url 3.1.2, stripe 15.0.1, requests 2.33.1, PyYAML 6.0.2.
- `makemigrations --check --dry-run`: “No changes detected.” Stable baseline: regenerated `0001_initial.py` has a one-line diff, the timestamp.
- `git status --short` no longer shows `.claude/scheduled_tasks.lock`.
- Complete suite: `Ran 745 tests in 325.678s ... OK`. Same count as before dependency and runner changes.

## Implemented

- `system/test_runner.py`: renamed `PostgreSQLDiscoverRunner` to `ProjectDiscoverRunner`, with docstring describing all three real behaviors and recording that the runner **does not choose the database**.
- `lvjiujitsu/settings.py`: `TEST_RUNNER` points to new name; `STATIC_ROOT` creation moved into settings outside test path.
- Runner no longer creates `STATIC_ROOT`; logging suppression through `WARNING` and WhiteNoise warning filter remain.
- `requirements.txt`: reduced from 49 lines to ten direct dependencies grouped by purpose with comments. Removed transitives and unused packages — `pillow`, `PyMuPDF`, `python-dotenv`, `StrEnum`, `PyJWT`, `cryptography`, `rich`, `httpx`, and others.
- `.gitignore`: removed `.env-prod` and `.env-hg`; added `.claude/scheduled_tasks.lock`, `db.sqlite3-wal`, `db.sqlite3-shm`, `db.sqlite3-journal`, and `coverage.xml`.
- Added `build_parent_map` and `ancestor_pids` to `clear_migrations.py`, with four tests in `system/tests/test_commands.py`.

## Cleanup findings

1. **Problem 1 premise was partially wrong and corrected before implementation.** Runner does not configure a database but **does** have PostgreSQL-specific logic: `teardown_databases` terminates remaining sessions when `conn.vendor == "postgresql"`, without which test database drop fails due to open connection. The name was not baseless — it misrepresented the engine used by default. New name describes role; PostgreSQL behavior is fully preserved.
2. **This project did not have a self-termination defect** possible in similar code: `kill_project_python_processes` uses `taskkill /F` without `/T` and already protected `os.getppid()`. The fix hardens the chain above the parent; it does not repair breakage.
3. **`pillow` removed after verification.** No `ImageField` or `PIL` import exists, confirmed by search, and complete suite passed without it.
4. No external-repository mention was found in project source code.
5. No residue introduced. Temporary venv used for resolution validation remained outside the repository.

## Follow-up PRDs

None. Moving the suite to PostgreSQL requires its own PRD with CI database provisioning.

## Deviations from plan

- Problem 6 did not exist when PRD was written; discovered during execution and added to scope with criteria 13 and 14.
- First hardening implementation moved executable-name filtering from PowerShell to Python, breaking `test_kill_only_targets_project_python_processes` — its mock payload lacks `Name` because filtering historically occurred in the query. Since constraints prohibit adapting tests to accommodate change, implementation was redone: filter returned to PowerShell, parent map built from already filtered enumeration. Test passed unchanged.
- Criterion 9 required before/after `pip freeze`. Instead of recreating the operator’s project venv, resolution was verified in a temporary out-of-repository venv. Same proof without risk to the working environment.

## Pending

- Run CI for real: steps verified locally, job runs only on next push.
- Commit working tree. No commit was made by the agent.

## Final status

Completed. Runner name describes actual behavior while preserving PostgreSQL teardown; `STATIC_ROOT` exists independently of suite execution, proven by `collectstatic` immediately after reset; `requirements.txt` lists ten direct dependencies with green `pip check` in a recreated environment; and `git status` no longer shows runtime artifacts. Complete 745-test suite passes.
