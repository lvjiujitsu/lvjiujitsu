# PRD-011: Home with a collapsed graduation section

## Summary of the implementation
On the student and instructor homes, the graduation card must initially display only the current belt. The progress information currently exposed on screen must move inside a small dropdown triggered by the `Mais sobre a graduação` (`More about the graduation`) control.

## Demand type
Targeted UI fix.

## Current problem
The graduation card takes up space on the authenticated homes because it shows time at the belt, approved classes, completion, and status directly on screen.

## Goal
Reduce the initial volume of information on the student and instructor homes while keeping access to the complete graduation information on demand.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `manage.py`
- `requirements.txt`
- `templates/home/student/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/graduation/_progress_card.html`
- `templates/graduation/_belt_visual.html`
- `templates/graduation/_history_modal.html`
- `templates/base.html`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/urls.py`
- `system/services/graduation.py`
- `system/selectors/graduation.py`
- `system/models/graduation.py`
- `system/templatetags/graduation_tags.py`
- `system/tests/test_graduation.py`
- `system/tests/test_views.py`
- `static/system/css/portal/portal.css`
- `docs/prd/PRD-010-graduation-control-module-belts-degrees-rules-and-overview.md`

### Adjacent files consulted
- `docs/prd/`
- `system/tests/test_calendar.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`

### Internet / official documentation
- Not applicable: the change uses the native HTML behavior of `<details>/<summary>` and local CSS, with no new framework API.

### MCPs / tools verified
- PowerShell — ok — `Get-ChildItem`, `Get-Content`, `Select-String`.
- `.venv` — ok — `.\.venv\Scripts\python.exe --version` returned Python 3.12.10.
- Django — ok — `.\.venv\Scripts\python.exe -m django --version` returned 4.1.13.
- `rg` — unavailable — execution failed with access denied to the bundled binary; replaced by native PowerShell commands.
- Browser Use / node_repl — limited in this review — returned `No active Codex browser pane available`.
- Playwright MCP — ok — desktop/mobile validation at `http://127.0.0.1:8000/`.

### Limitations found
- The worktree already carries several unrelated changes; this delivery must not revert them.
- There are `cleanup-artifacts-*` directories that return access denied when listed through Git; they are not part of the scope.
- The first Playwright Python run inside the sandbox failed on permissions; the validation was repeated outside the sandbox with approval.
- The Django server that was open on port 8000 kept the old template in memory; it was restarted to validate the HTML served by the current code.

## Execution prompt
### Persona
Development agent specializing in Django 4.1, following SDD + TDD + server-rendered MVT.

### Action
Implement the collapsed graduation card on the student and instructor homes.

### Context
Both homes include the shared component `templates/graduation/_progress_card.html`; therefore the change must be concentrated in that include and in the portal CSS.

### Constraints
- no hardcoded graduation rules
- no error masking
- no migrations
- mandatory full reading
- mandatory validation
- preserve the worktree's pre-existing changes

### Acceptance criteria
- [x] The student home must render the current belt immediately.
- [x] The instructor home must render the current belt immediately.
- [x] Time at the belt, approved classes, completion, and status must sit inside a dropdown that is closed by default.
- [x] The dropdown must be triggered by the text `Mais sobre a graduação` (`More about the graduation`).
- [x] The history button/modal, when there is history, must remain reachable from the expanded detail.
- [x] The `portal.css` version must be updated in the template that references the asset.

### Expected evidence
- an automated test covering the student and the instructor
- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput`
- `manage.py showmigrations`
- visual validation in a desktop and mobile browser
- browser console with no critical JavaScript errors

### Output format
Implemented code + tests + validation evidence.

## Scope
- `templates/graduation/_progress_card.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-011-home-with-collapsed-graduation-section.md`

## Out of scope
- Changing the graduation calculation rule.
- Changing models, migrations, seeds, or the administrative CRUD.
- Changing the layout of the other home cards.

## Impacted files
- `templates/graduation/_progress_card.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-011-home-with-collapsed-graduation-section.md`

## Risks and edge cases
- A person with no registered graduation must keep seeing the current message, with no empty dropdown.
- A person with a belt but no configured rule must see the rule message only in the expanded detail.
- A person with history must keep being able to open and close the history modal.
- The solution must work without additional JavaScript to open the dropdown.

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
Playwright MCP validated `desktop-student` and `desktop-instructor` in a 1280x900 viewport:
- the belt visible immediately
- `Tempo na faixa atual` (`Time at the current belt`) hidden before opening
- `Tempo na faixa atual` (`Time at the current belt`), `Aulas aprovadas` (`Approved classes`), and `Ver histórico` (`View history`) visible after clicking `Mais sobre a graduação` (`More about the graduation`)
- the history opens through `static/system/js/graduation/progress-card.js?v=20260507a`
- `inlineHistoryScriptCount=0`
- `console_errors=0`

### Mobile
Playwright MCP validated `mobile-student` and `mobile-instructor` in a 390x844 viewport with the same criteria as desktop, `console_errors=0`, and no horizontal overflow.

### Browser console
Playwright MCP: `errors=[]` for student/instructor on desktop/mobile.

### Terminal
The commands ran with no stack traces after the fix. The local server was restarted and `/login/` responded `200`.

## ORM validation
### Database
No schema change expected.

### Shell checks
Temporary personas `930.000.700-01` and `930.000.700-02` were created to validate a student and an instructor with a real graduation in the local database. At the end, the cleanup returned `False False` for residual existence of the people and of the `codex-visual-white` belt.

### Flow integrity
The authenticated student and instructor reached their respective homes, and the shared component preserved the history modal inside the expanded detail.

## Quality validation
### No hardcoding
No hardcoded graduation rule; the template keeps consuming `graduation_progress` and `graduation_history`.

### No brittle conditional structures
The change is concentrated in the shared include, keeping the existing conditionals on `current_belt_rank`, `applicable_rule`, and `graduation_history`.

### No `except: pass`
No `except: pass` introduced.

### No error masking
No error masked; the dropdown behavior is native through `<details>/<summary>`.

### No unnecessary comments or docstrings
No new comment/docstring in production code.

## Evidence
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation.GraduationDashboardCardTestCase --verbosity 2` failed before the implementation due to the absence of `Mais sobre a graduação` (`More about the graduation`).
- Focused Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation.GraduationDashboardCardTestCase --verbosity 2` — 2 tests, OK.
- Graduation module: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation --verbosity 2` — 18 tests, OK.
- Full suite: `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 305 tests, OK.
- Check: `.\.venv\Scripts\python.exe manage.py check` — 0 issues.
- JS check: `node --check .\static\system\js\graduation\progress-card.js` — OK.
- Static: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 1 file copied, 164 unchanged.
- Migrations: `.\.venv\Scripts\python.exe manage.py showmigrations` — only `system.0001_initial` applied in the local app.
- Diff check: `git diff --check` — no errors; only LF/CRLF normalization warnings on files that were already modified.
- Playwright MCP: student and instructor with the dropdown closed by default; the information appears after the click; the history opens; `scriptCount=1`; `inlineHistoryScriptCount=0`; `errors=[]`.

## Implemented
- `templates/graduation/_progress_card.html`: removed the detailed information from the initial exposure and moved time, classes, completion, status, and history inside `<details class="graduation-progress-details">`.
- `templates/graduation/_progress_card.html`: replaced the inline history script with a versioned static asset.
- `static/system/js/graduation/progress-card.js`: centralizes opening/closing the history modal.
- `static/system/css/portal/portal.css`: added styles for the `Mais sobre a graduação` (`More about the graduation`) control and the detail body.
- `templates/base.html`: updated the cache-busting of `portal.css` to `20260507a`.
- `system/tests/test_graduation.py`: added coverage for the student and instructor homes with the dropdown closed by default.

## Deviations from plan
- There was no external lookup; there was no new library API to confirm.
- Browser Use did not connect to the active pane in this review; visual validation was done through Playwright MCP.
- The local server was restarted because the previous instance was serving the old template from memory.

## Pending
No pending items for this change.
