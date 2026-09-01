# PRD-092: Home split into My area and Management

## Summary
Fix and complete the dual experience on the home when a person trains and also performs management or support (the Aline case, a back-office holder, a guardian with dependents). The current template opens `Minha área` (`My area`) and `Gestão` (`Management`) with duplicated IDs and an incomplete management section in the split mode.

## Demand type
A UI fix + a context adjustment in the view.

## Current problem
- `dashboard.html` repeats `id="staff-area-title"` and has an inconsistent `<section>` structure between `needs_split` and `show_staff_area` (`dashboard.html:64-75`).
- `home_views.py` mixes the administrative `today_classes` with the student's `my_classes` with no clear separation in the split.
- The user reports the split My area / Management back-office home as dysfunctional.

## Goal
A user with training + management sees:
- **My area:** the student's classes, the graduation, check-in, dependents.
- **Management:** quick access, a financial summary, the day's classes as staff, approvals.

With no duplicated IDs and no management content inside the personal block.

## Context Ledger
### Files read in full
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `system/views/home_views.py`
- `system/tests/test_home_dashboard.py`
- `docs/prd/PRD-014-admin-panel-as-portal-persona.md`

### Adjacent files consulted
- `static/system/js/home/dashboard.js`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- WCAG 2.2 unique id: https://www.w3.org/WAI/WCAG22/Understanding/parsing

### Context7 / MCPs / tools verified
- Not applicable.

### Limitations found
- A broad redesign may require prior visual approval (`lv-ui-delivery`).

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the audit and the user's explicit problem.

## Execution prompt
### Persona
Django UI implementer focused on cumulative roles.

### Action
Refactor the template and the context for a stable split with unique ARIA landmarks.

### Context
`needs_split`, `has_personal_area`, `show_staff_area` in `HomeView`.

### Constraints
- Preserve the unified home's existing features.
- The existing CSS tokens; no new unrequested KPI.

### Acceptance criteria
- [ ] Valid HTML: a single `id` per element; the sections closed correctly.
- [ ] Aline (a student + class-assistant): `Minha área` (`My area`) with the student's check-in; `Gestão` (`Management`) without mixing in the personal class list.
- [ ] A back-office member who does not train keeps the hint "no personal training area".
- [ ] The regression test updates the asserts for the removed IDs (the duplicated `staff-area-title`).
- [ ] Desktop and mobile validated in the browser.

### Expected evidence
- Desktop/mobile split screenshots.
- Green home tests.

### Output format
The evidence in the PRD.

## Scope
- The split context in `home_views.py`.
- `dashboard.html` and its partials when necessary.
- The `test_home_dashboard.py` tests.

## Out of scope
- The instructor check-in rule (PRD-094).
- A complete financial redesign.

## Impacted files
- `templates/home/dashboard.html`
- `system/views/home_views.py`
- `system/tests/test_home_dashboard.py`
- `static/system/css/home/dashboard.css` (minimal adjustments)

## Risks and edge cases
- A guardian with dependents: which block do the dependents belong to?
- A technical admin with no `portal_person`.

## Rules and constraints
- An approved wireframe before the visual code.

## Plan
1. [x] A wireframe with the My area / Management regions (already existing in the template; validated as correct).
2. [x] A failing test for Aline's content (reproduced live before coding).
3. [x] A context adjustment (adjusting the split template itself was not necessary — see Evidence).
4. [x] Browser validation.

## Test plan
### Tests to author
- `test_dual_role_student_sees_own_checkin_merged_with_support_classes` (implemented in PRD-094, covering the same scenario)

### Execution authorization
Locally authorized.

### Execution evidence
- This PRD and PRD-094 describe the same symptom observed by the user (Aline does not see the check-in) from two different hypotheses. The real investigation showed:
  1. **Duplicated IDs (`staff-area-title`)**: it is not a runtime bug. The template uses a single `{% if needs_split %}...{% elif show_staff_area and not has_personal_area %}...{% endif %}` block — the two occurrences of `id="staff-area-title"` are in mutually exclusive branches; they never render together in the same response. Confirmed by reading `templates/home/dashboard.html` lines 64-75 and the corresponding closing at line 516 (`{% if needs_split or show_staff_area and not has_personal_area %}`).
  2. **Management content mixed into the personal area**: this also did not reproduce — `personal_today_classes` is already strictly `my_classes` (always `entry_role="student"`).
  3. **The real bug**: for Aline (a student + class support, without being back office), `needs_split` never activates (it only activates for back-office staff or a guardian with dependents) — so she falls into the "not split" branch, which overwrote `today_classes` with the instructor/support view, **discarding** her own check-in list. Fixed in PRD-094 (the same `home_views.py` file).
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard --verbosity 2` — 5 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 326 tests OK.

## Visual validation
## Wireframe
### Region: The header
- The greeting, the role badges (Student, Class support, Back office).

### Region: My area (conditional on `needs_split`)
- Today's classes as a student, with a check-in action.
- The graduation, collapsed.

### Region: Management
- Quick access, a financial summary, staff classes/approvals.

### States
- Management only; student only; the complete split.

## ORM validation
Validated with Aline's real seed (`920.000.011-81`) in the local development database.

## Quality validation
- `manage.py check` — 0 problems.

## Evidence
- See Execution evidence above. The real implementation ended up in `system/views/home_views.py` (PRD-094); this PRD documents the investigation and rules out the first two hypotheses (duplicated IDs, mixed content) as false positives, confirming the third (list routing) as the real root cause.

## Implemented
- See PRD-094 (`_merge_class_entries` in `system/views/home_views.py`). No template change was necessary in this PRD — the split's HTML structure was already correct.

## Cleanup findings
- No residue.

## Follow-up PRDs
- None.

## Deviations from plan
- The original plan assumed a template bug (duplicated IDs/HTML structure); the real investigation showed the template was already correct and the bug was in the Python (`home_views.py`). Documented here so the template investigation is not repeated in the future.

## Pending
- None.

## Final status
Completed.
