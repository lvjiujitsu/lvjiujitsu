# PRD-097: Orphaned calendar views with no routes

## Summary
Remove or integrate the legacy classes in `calendar_views.py` that have no entry in `urls.py`, reducing the dead surface and the confusion between the unified calendar and the old admin calendar.

## Demand type
Code cleanup + governance.

## Current problem
- `AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, and `AdminSpecialClassDeleteView` defined with the non-existent template `calendar/admin_calendar.html`.
- The unified `CalendarView` already serves `/cronograma/` for every profile.
- The `StudentScheduleView` and `InstructorCalendarView` aliases kept with no use in `urls.py`.
- A ~650-line file makes maintenance harder.

## Goal
A single canonical calendar surface (`CalendarView` + the existing JSON endpoints); the dead code removed or routed with a test.

## Context Ledger
### Files read in full
- `system/views/calendar_views.py`
- `system/urls.py`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Adjacent files consulted
- `system/tests/test_calendar.py`
- The legacy `calendar/admin_calendar.html` snapshot (for reference only)

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- `rg` confirms the absence of admin calendar routes.

### Limitations found
- If some administrative feature only existed in the dead views, it must migrate into `CalendarView` before deleting.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The 2026-06-30 audit.

## Execution prompt
### Persona
Django cleanup engineer.

### Action
Inventory the imports; remove the orphaned classes; ensure functional parity.

### Context
PRD-055's check-in and the unified schedule.

### Constraints
- Do not break the registered URLs.
- Proportional tests.

### Acceptance criteria
- [ ] No View class in `calendar_views.py` without a route or a tested use.
- [ ] `rg AdminCalendarView` returns only git history, or zero in the active code.
- [ ] `test_calendar` green.
- [ ] Document in the PRD if an administrative feature was consolidated into `CalendarView`.

### Expected evidence
- The diff + the tests.

### Output format
The PRD's Evidence.

## Scope
- `calendar_views.py`
- `urls.py` when a redirect is necessary
- The tests

## Out of scope
- A new separate admin calendar template.

## Impacted files
- `system/views/calendar_views.py`
- `system/tests/test_calendar.py`

## Risks and edge cases
- An external import of an alias in untracked code.

## Rules and constraints
- PRD-076's controlled cleanup.

## Plan
1. [x] `rg` for imports of the aliases.
2. [x] Migrate the behavior when there is a gap (no gap: `CalendarView` already covered every profile).
3. [x] Remove the dead code.
4. [x] Tests.

## Test plan
### Tests to author
- `system/tests/test_lv_foundation_calendar.py::CalendarDeadCodeRemovedTestCase` confirms through `hasattr` that the 4 views were removed.

### Execution authorization
Local.

### Execution evidence
- `rg "AdminCalendarView|AdminToggleSessionView|AdminSpecialClassCreateView|AdminSpecialClassDeleteView" system/` returned only `calendar_views.py` itself and the `system/views/__init__.py` barrel before the removal; no route, template, or test referenced them.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_calendar --verbosity 2` — 3 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 tests OK after the removal (no regression).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
The schedule (`/calendar/`) validated in the internal browser during PRD-077 — with no dependence at all on the removed views.

## ORM validation
N/A.

## Quality validation
- `manage.py check` — OK.
- The full suite — OK.

## Evidence
- `AdminCalendarView` pointed at `template_name = "calendar/admin_calendar.html"`, which never existed in the repository — confirming the view was never actually executable.
- `AdminSpecialClassCreateView`/`AdminSpecialClassDeleteView` duplicated exactly the logic of `InstructorSpecialClassCreateView`/`InstructorSpecialClassDeleteView`, which already cover administrators through a capability override.

## Implemented
- The 4 classes removed from `system/views/calendar_views.py`, along with their entries in `system/views/__init__.py` (the imports and `__all__`).
- The now-unused imports in `calendar_views.py` cleaned up: `PersonTypeCode`, `Person`, `AdministrativeRequiredMixin`.

## Cleanup findings
- No residue. The `calendar_views.py` file is smaller and has no orphaned symbols left.

## Follow-up PRDs
- None.

## Deviations from plan
- This PRD was implemented as part of PRD-077's work (the Schedule module), not in isolation — the evidence is recorded here to close the tracking.

## Pending
- None.

## Final status
Completed.
