# PRD-096: UTF-8 encoding of the schedule template

## Summary
Fix `templates/calendar/calendar.html` and the contract test to guarantee UTF-8 reading on Windows, eliminating the suite's ERROR (a cp1252 `UnicodeDecodeError` at position 3727).

## Demand type
A quality fix + a test.

## Current problem
- `test_calendar_template_loads_external_script_without_inline_logic` uses `Path.read_text()` with no encoding on Windows.
- The template contains byte(s) outside ASCII/cp1252 (likely a Unicode character in a comment or in text).
- The suite: 262 tests, 1 ERROR.

## Goal
The file saved as valid UTF-8; the test passes on Windows and Linux; the Brazilian Portuguese content preserved.

## Context Ledger
### Files read in full
- `templates/calendar/calendar.html`
- `system/tests/test_register_wizard_contract.py`
- The output of `manage.py test --verbosity 2` on 2026-06-30

### Adjacent files consulted
- `static/system/js/calendar/calendar.js`

### Internet / official documentation
- Python pathlib read_text encoding: https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Fixing only the test without normalizing the template leaves a risk in Windows editors.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The local test evidence in the audit.

## Execution prompt
### Persona
Cross-platform quality engineer.

### Action
Normalize the template to UTF-8; adjust the test to `encoding="utf-8"` as a defense.

### Context
PRD-080 forbids insecure innerHTML in the calendar's JavaScript.

### Constraints
- Do not change the visual behavior.
- Update `?v=` when the JavaScript changes.

### Acceptance criteria
- [ ] `manage.py test system.tests.test_register_wizard_contract` green on Windows.
- [ ] The file with no problematic BOM; the Brazilian Portuguese characters correct in the browser.
- [ ] No `.innerHTML` in the calendar's JavaScript (the existing contract).

### Expected evidence
- The test command and an OK output.

### Output format
The PRD's Evidence.

## Scope
- `calendar.html`
- `test_register_wizard_contract.py`
- A targeted review of special characters.

## Out of scope
- A redesign of the schedule.

## Impacted files
- `templates/calendar/calendar.html`
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases
- Git autocrlf changing the bytes.

## Rules and constraints
- Prefer HTML entities or ASCII in comments when necessary.

## Plan
1. [x] Reproduce the original failure.
2. [x] Confirm the template's current state.
3. [x] Add an explicit `encoding="utf-8"` to every file read in the test (a cross-platform defense).
4. [x] A proportional Green on the full suite.

## Test plan
### Tests to author
- Keep the existing test (an encoding adjustment).

### Execution authorization
Local.

### Execution evidence
- When reproducing it locally, `manage.py test system.tests.test_register_wizard_contract --verbosity 2` already passed (4 tests OK) even before the fix — the original `UnicodeDecodeError` happened in an earlier state of `templates/calendar/calendar.html` (already fixed organically during PRD-080/077).
- The defensive fix was applied anyway: the 5 `Path.read_text()` calls in `system/tests/test_register_wizard_contract.py` (lines 15, 16, 26, 55, 56) now use an explicit `encoding="utf-8"`, removing the dependence on the OS locale (cp1252 on Windows) for any future regression.
- `.venv/Scripts/python.exe manage.py test system.tests.test_register_wizard_contract --verbosity 2` — 4 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 tests OK.

## Visual validation
`/calendar/` renders correctly with Brazilian Portuguese accents in the internal browser (validated during PRD-077).

## ORM validation
N/A.

## Quality validation
- `manage.py test --verbosity 2` — 0 failures.

## Evidence
- The original problematic byte is no longer present in the current `calendar.html` (already rewritten during PRD-080/077); the historically reported root cause is no longer reproducible, but the defense (an explicit encoding) was applied so as not to depend on a specific file state.

## Implemented
- `system/tests/test_register_wizard_contract.py`: an explicit `encoding="utf-8"` on every file read.

## Cleanup findings
- No residue.

## Follow-up PRDs
- None.

## Deviations from plan
- It was not necessary to identify/replace a specific byte, because the current file no longer reproduces the error; the fix applied was purely defensive, per the acceptance criteria.

## Pending
- None.

## Final status
Completed.
