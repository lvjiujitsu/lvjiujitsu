# PRD-010: Graduation control module (belts, degrees, rules, and overview)

## Summary of the implementation
Create a dynamic graduation control module for Jiu Jitsu students, with no hardcoded belt table. It covers:
1. CRUD for belts (`BeltRank`) and their degrees (parameterized on the belt).
2. CRUD for graduation rules (`GraduationRule`) by belt/degree, with a minimum time and minimum attendance.
3. Graduation history (`Graduation`) per person.
4. Progress calculation based on approved check-ins (already existing through PRD-009) and elapsed time.
5. An overview listing who is close to being promoted and what is missing (in months and in classes) per student.
6. Seeds with the standard IBJJF table (adult + kids), fully editable.

## Demand type
New feature with a schema change (new models, without changing `Person`).

## Current problem
- `Person.jiu_jitsu_belt` and `Person.jiu_jitsu_stripes` are static free-text/choice fields. There is no history, rule, or automatic calculation.
- There is no tool for the admin/instructor to assess who is close to being promoted.
- Changes to the IBJJF rules would require a code change.

## Goal
- Belts, degrees per belt, and graduation rules editable by the admin (zero hardcoding in code).
- Graduation progress computed from the graduation history + approved check-ins.
- An overview ordered by proximity to promotion (% completion of the current rule).

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`
- `system/models/person.py` (the `jiu_jitsu_belt`, `jiu_jitsu_stripes` fields)
- `system/models/category.py` (`CategoryAudience`, `IbjjfAgeCategory`)
- `system/models/calendar.py` (including the new `CheckinStatus.APPROVED`)
- `system/models/__init__.py`
- `system/services/seeding.py`
- `system/services/class_calendar.py`
- `system/views/__init__.py`, `system/urls.py`
- `templates/base.html` (drawer/menu)

### Internet / official documentation
- Not reachable in this environment; the default seed is parameterized, but the admin can freely edit it should the IBJJF change a rule.

### MCPs / tools verified
- `read`, `glob`, `grep` — ok
- `bash` for `manage.py check` — ok
- destructive cycle — authorized by the user

### Limitations found
- No direct access to the attached PDFs; the seeds use the known public IBJJF table.

## Execution prompt
### Persona
Django agent following SDD + TDD + MVT with a service and selector layer.

### Action
Implement a dynamic graduation module (models + services + selectors + CRUD views + overview + seeds).

### Context
The system already has `Person`, `IbjjfAgeCategory`, and `ClassCheckin` (with an approved status). What is missing is the graduation rule and the history.

### Constraints
- no hardcoded belts/rules in the code
- no error masking
- destructive cycle already authorized (PRD-009)
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] A `BeltRank` model with `code`, `display_name`, `audience`, `display_order`, `color_hex`, `max_grades`, `next_rank` (self FK), `min_age`, `max_age`, `is_active`.
- [ ] A `GraduationRule` model with `belt_rank`, `from_grade`, `to_grade` (None = next belt), `min_months_in_current_grade`, `min_classes_required`, `min_classes_window_months`, `notes`, `is_active`.
- [ ] A `Graduation` model with `person`, `belt_rank`, `grade_number`, `awarded_at`, `awarded_by`, `notes`.
- [ ] A `count_approved_classes_in_window(person, start, end)` service based on `ClassCheckin`/`SpecialClassCheckin` with `status=approved`.
- [ ] A `get_current_graduation(person)` service that returns the latest `Graduation` or a virtual `Graduation` built from `Person.jiu_jitsu_belt`/`stripes` (compatibility).
- [ ] A `compute_graduation_progress(person, reference_date)` service that returns a struct with: `current_belt_rank`, `current_grade_number`, `applicable_rule`, `months_in_current_grade`, `required_months`, `months_remaining`, `approved_classes_in_window`, `required_classes`, `missing_classes`, `is_eligible`, `progress_pct`.
- [ ] A `register_graduation(person, belt_rank, grade_number, awarded_by, notes)` service that creates the record and forces a transaction.
- [ ] A `get_graduation_overview(reference_date)` selector that lists every active `Person` of the student/dependent type with their progress, ordered by `progress_pct` descending.
- [ ] Admin CRUD for `BeltRank` (list/detail/create/update/delete).
- [ ] Admin CRUD for `GraduationRule` (list/detail/create/update/delete).
- [ ] Admin CRUD for `Graduation` (list/create/delete).
- [ ] A `GraduationOverviewView` view with the overview table.
- [ ] A `seed_belts` command that loads the default IBJJF belts + rules.
- [ ] `inicial_seed` invokes `seed_belts`.
- [ ] The Django admin registers the 3 models.
- [ ] The admin drawer has `Graduação` (`Graduation`), `Faixas` (`Belts`), and `Regras de graduação` (`Graduation rules`) entries.
- [ ] Tests in `system/tests/test_graduation.py` cover models, services, selectors, and views.
- [ ] `manage.py test` passes; `manage.py check` reports 0 issues.

### Expected evidence
- passing tests, the destructive cycle executed, visual validation of the overview page.

### Output format
Code + tests + seeds + evidence.

## Scope
- `system/models/graduation.py` (new)
- `system/models/__init__.py`
- `system/services/graduation.py` (new)
- `system/selectors/graduation.py` (new)
- `system/forms/graduation_forms.py` (new)
- `system/views/graduation_views.py` (new)
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/seeding.py` (`seed_belts`)
- `system/management/commands/seed_belts.py` (new)
- `system/management/commands/inicial_seed.py` (call seed_belts)
- `system/admin.py`
- `templates/graduation/*.html` (new)
- `templates/base.html` (drawer with the new entries)
- `static/system/css/portal/portal.css` (overview styles)
- `system/tests/test_graduation.py` (new)

## Out of scope
- Automatic notification for those who reached eligibility.
- Bulk promotion.
- Importing graduation history from external sources.
- Editing the current belt directly on `Person`; it goes through the `Graduation` record.

## Risks and edge cases
- A person with no `Graduation` and no `jiu_jitsu_belt`: progress returns `None`/no applicable rule.
- A belt with no `next_rank`: `to_grade=None` rules become invalid; the service returns `applicable_rule=None`.
- A rule with `min_classes_window_months=0`: ignores the window and considers every check-in since the last graduation.
- A student with no approved check-ins: missing_classes = required_classes; progress derived from time alone.
- Age below the `min_age` of the next belt: progress still considers the rule but marks `is_eligible=False`.

## Rules and constraints
SDD, TDD, no hardcoding, destructive cycle authorized.

## Plan
- [ ] 1. Create the PRD
- [ ] 2. Models
- [ ] 3. Services
- [ ] 4. Selectors
- [ ] 5. Forms
- [ ] 6. CRUD views/URLs + overview
- [ ] 7. Templates
- [ ] 8. Seeds + command + inicial_seed
- [ ] 9. Django admin
- [ ] 10. Drawer/menu
- [ ] 11. Tests
- [ ] 12. `manage.py check` (0 issues)
- [ ] 13. Destructive cycle (together with PRD-009)
- [ ] 14. `manage.py test`
- [ ] 15. Visual validation of the overview
- [ ] 16. Final cleanup

## Visual validation
- The overview page shows students with progress, badges, and remaining time.
- The belt/rule CRUD navigates normally.

## ORM validation
- After the destructive cycle, the schema is regenerated.
- `Graduation.objects.create(...)` ↔ `get_current_graduation(person)` returns the record.
- `compute_graduation_progress` reflects the approved check-ins.

## Quality validation
No hardcoding, explicit exceptions, comments only where necessary.

## Evidence
(fill in after execution)

## Implemented
(fill in at the end)

## Deviations from plan
(fill in at the end)

## Pending
(fill in at the end)
