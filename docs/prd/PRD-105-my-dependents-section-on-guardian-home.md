# PRD-105: A "My dependents" section on the guardian's home

## Summary
`HomeView.get_context_data()` already computes `context["dependents"]` (through `_build_dependents()`) with each dependent's graduation progress, today's classes, and tuition summary — but `templates/home/dashboard.html` never renders that variable. The guardian does not see, on the home, a summary of their dependents beyond the tuition tab (`billing_tabs`, which only covers billing).

## Demand type
A UI fix (data computed in the backend with no interface entry point — the same pattern as PRD-103).

## Current problem
- `system/views/home_views.py:167-168`: `if has_dependents(person): context["dependents"] = _build_dependents(person)`.
- `_build_dependents()` (line 278) assembles, per dependent: `person`, `belt_view` (a dict ready for the SVG, never used in any template), `classes` (today's classes), `billing` (through `_billing_summary`), and `graduation_progress`.
- A search across `templates/` confirms it: no template references `dependents`, `belt_view`, or the shape returned by `_build_belt_view` (`body`/`tip`/`stripes`/`needs_border`/`grade`/`label`).
- `billing_tabs` (a different context, already rendered) covers billing per person, but it does not show each dependent's graduation or today's classes on the home.

## Goal
The guardian sees, on the home, a `Meus dependentes` (`My dependents`) section with each dependent's name, current belt/degree, and the number of classes today, with a link to the person's complete detail (`person-detail`).

## Context Ledger
### Files read in full
- `system/views/home_views.py` (`HomeView.get_context_data`, `_build_dependents`, `_billing_summary`, `_build_belt_view`)
- `templates/home/dashboard.html` (the tuition/`billing_tabs` section, confirming the absence of any dependents block)
- `system/middleware.py` (it confirms that `portal_is_student`/`is_student` reflects `ACCESS_STUDENT_AREA`, granted to `GUARDIAN`, not "being enrolled" — ruling out an initial hypothesis of a bug in `_build_billing_context`)
- `system/constants.py` (`PERSON_TYPE_CAPABILITIES`, confirming the capability above)

### Adjacent files consulted
- `system/services/graduation.py` (`compute_graduation_progress` — the shape of `current_belt_rank`/`current_grade_number`)
- `system/services/class_calendar.py` (`get_today_classes_for_person`)

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The finding came from a re-audit of the instructor/guardian panels; 5 of the exploration agent's 6 findings were discarded as false positives (the Portuguese class routes are already a separate historical pattern, outside this PRD's scope; the supposed "missing critical section" was refined after a manual check — `billing_tabs` already covers billing, and what is missing is graduation/today's classes per dependent).

## Scope
- Simplify `_build_dependents()` so it no longer depends on `_build_belt_view()`/`_billing_summary()` (both without a real consumer) — using `graduation_progress.current_belt_rank`/`current_grade_number` and `get_active_membership()` directly.
- Render the `Meus dependentes` (`My dependents`) section in `templates/home/dashboard.html`.

## Out of scope
- Migrating the class routes to English (a separate finding, unrelated to this gap; do not open a PRD for it now, since it is a larger route restructuring and not a functional bug).
- Redesigning `billing_tabs`.

## Impacted files
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `system/tests/test_home_dashboard.py`

## Risks and edge cases
- A guardian with no dependents: the section must not appear (an empty `dependents` is already handled by `has_dependents`).
- A dependent with no registered belt: show them with no belt badge, without breaking the card.

## Rules and constraints
- The UI in Brazilian Portuguese, with no business logic in the template (the counts/joins already arrive ready from the view).

## Plan
- [x] Simplify `_build_dependents`.
- [x] Render the section in the dashboard.
- [x] A focused test.
- [x] Visual validation.

## Test plan
### Tests to author
- A guardian with a dependent sees the `Meus dependentes` (`My dependents`) section with the dependent's name and belt.
- A person with no dependents does not see the section.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_home_dependents_section.py` (2 tests): the guardian sees the `Meus dependentes` (`My dependents`) section with the dependent's name and belt; a person with no dependents does not see the section.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dependents_section --verbosity 2` — 2 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 348 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- Live validation in the browser (a demo André→Aline relationship created through the ORM and removed after the test, with André's real portal account restored through `seed_system_initial_teacher`): the `Meus dependentes` (`My dependents`) section shows the name, the belt (`Roxa · 1º grau` — `Purple · 1st degree`), the tuition status (`Sem plano ativo` — `No active plan`), and `2 aulas hoje` (`2 classes today`); the `Ver perfil` (`View profile`) button navigates correctly to `people/6/view/`; validated on desktop and mobile (375x812) with no overflow.

**Operational note**: during the validation, I discovered that the local preview server runs with `--noreload` (`.claude/launch.json`), so changes in `.py` files (unlike templates) require a manual server restart to take effect — that caused a ~40-minute investigation of a "phantom bug" (the section did not appear because the server process was still running the old `home_views.py` code). After restarting the server, the section rendered correctly on the first try.

## Visual validation
Desktop, mobile, the dark theme, with real data (a guardian with a dependent).

## ORM validation
`PersonRelationship` (RESPONSIBLE_FOR) used for the test.

## Quality validation
- `manage.py test system.tests.test_home_dashboard` and the full suite.
- `manage.py check`.

## Evidence
- The `Ver perfil` (`View profile`) link only appears when `can_access_people` is true (the `SUPPORT_PEOPLE` capability), since `PersonDetailView` requires that capability — a pure guardian (without that role) would see the section with no link, avoiding a 403.

## Implemented
- `system/views/home_views.py`: `_build_dependents()` simplified to return `person`, `graduation_progress`, `today_classes`, and `active_membership` directly; the orphaned `_billing_summary()` and `_build_belt_view()` functions removed (never consumed by any template).
- `templates/home/dashboard.html`: a new `Meus dependentes` (`My dependents`) section, rendered when `dependents` is non-empty, with a belt/degree badge, a tuition status badge, the count of today's classes, and a conditional link to the complete profile.
- `system/tests/test_home_dependents_section.py` (new).

## Cleanup findings
- Removed dead code that existed only to feed `_build_dependents()` (the `_build_belt_view` function would have required a new SVG partial that was never created); the simplification avoided reintroducing that debt.
- No test data residue; André's portal account restored to its original seed state through `seed_system_initial_teacher` (idempotent).

## Follow-up PRDs
- Migrating the class routes (`aulas/...`) to English with compatibility — a real finding from the re-audit, but out of scope here since it is a broad route restructuring; recorded for a future assessment if the sweep continues.

## Deviations from plan
_None so far._

## Pending
_None so far._

## Final status
Completed.
