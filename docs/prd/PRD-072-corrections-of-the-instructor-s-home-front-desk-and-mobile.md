# PRD-072: Fixes to the instructor home, attendance, and mobile

## Summary
Fix the visual and functional observations made in the internal browser about the instructor's Home: allow undoing attendance and indicating a substitute for the day's class, improve the attendance history filters, replace long actions with icons on mobile, and fix the graduation history modal in a narrow viewport.

## Demand type
A Django functional fix + a responsive UI adjustment.

## Current problem
- The instructor can record attendance but cannot cancel their own attendance when something unexpected happens.
- There is no structured representation for a substitute instructor per daily session.
- The history filters use long text such as `Todas as turmas` (`All classes`), which reads as running text inside the modal.
- The `Histórico` (`History`), `Criar aulão` (`Create open class`), and `Cronograma` (`Schedule`) actions break the width on a phone.
- The graduation history modal is large and scrolls poorly on mobile.
- The attendance JavaScript uses `innerHTML` to update the UI, diverging from the local contract.

## Goal
Implement a safe flow for the instructor's attendance in the day's class, with cancellation and a substitute, and fix the responsive/modal problems reported without changing the Home's other roles.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`
- `docs/prd/PRD-018-instructor-home-mobile-buttons.md`
- `system/views/calendar_views.py`
- `system/services/class_calendar.py`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/person.py`
- `system/forms/class_forms.py`
- `system/tests/test_calendar.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/views/home_views.py`
- `system/urls.py`

### Internet / official documentation
- Django 5.2 class-based views: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: confirmed the `View.dispatch` flow, POST in a CBV, and the Test Client.
- The local PowerShell and the `.venv` available.
- The internal browser available at `http://127.0.0.1:8000/home/`.

### Limitations found
- A real substitution by an instructor on the day does not fit the current schema without a new daily-session field.
- The schema change will be local and small; HG/production stay out of scope.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The request "continue foque nas correcoes enviadas" ("continue, focus on the fixes sent") authorizes implementing the fixes noted in the browser comments. A remote environment change, deploy, HG, and production are not authorized.

## Execution prompt
### Persona
Django MVT agent focused on the operational class flow and mobile UI.

### Action
Implement the fixes to the instructor's Home, keeping server-side permissions, CSRF, and responsiveness.

### Context
The system uses Django 5.2, server-rendered templates, and a single Home at `/home/`. The instructor's attendance already uses `ClassSession.instructor_present` and `SpecialClass.instructor_present`.

### Constraints
- No business rules in a template/JavaScript.
- No `innerHTML` to update data.
- Do not edit `staticfiles/`.
- Create a local migration only for the substitute field required.
- Validate the instructor role first, since the comments came from that case.

### Acceptance criteria
- [x] A present instructor sees an action to cancel their own attendance.
- [x] The instructor can indicate an active substitute instructor for the day's regular class.
- [x] The substitute instructor starts seeing the day's class as an instructor and can be authorized by the ownership checks.
- [x] The history filters use the default value `Todos` (`All`).
- [x] The Classes header actions on mobile become 44x44 iconic buttons, with no horizontal overflow.
- [x] The graduation history modal sits over the screen with a controlled height and internal scrolling on mobile.
- [x] `dashboard.js` does not use `innerHTML` in the changed flow.
- [x] The focused tests and `manage.py check` pass.
- [x] The internal browser validates desktop/mobile and a console with no critical error.

### Expected evidence
- A focused Red before the implementation.
- A focused Green afterwards.
- `manage.py check`.
- Browser validation as an instructor on desktop/mobile with screenshots or snapshots.
- An audited diff.

### Output format
Implemented code, real evidence, limitations, and status.

## Scope
- `system/models/calendar.py`
- `system/migrations/0002_classsession_substitute_teacher.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- This PRD.

## Out of scope
- Deploy, HG, or production.
- Payout rules for a substitution.
- Notifications for the student/instructor.
- Rewriting the complete calendar.
- Validating every Home role in this round.

## Impacted files
- `system/models/calendar.py`
- `system/migrations/0002_classsession_substitute_teacher.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `docs/prd/PRD-072-corrections-of-the-instructor-s-home-front-desk-and-mobile.md`

## Risks and edge cases
- The substitute instructor must be active and have the `instructor` type.
- The original instructor must not indicate themselves as the substitute.
- A cancelled class must not accept attendance/substitution as though it were active.
- An open class already has its own instructor; substituting an open class is outside the schema and continues through the `teacher` field.
- Mobile at 375px must not have horizontal overflow from the header buttons.

## Rules and constraints
- SDD before code.
- Proportional TDD.
- The smallest correct change.
- Permission in the backend.
- Mandatory visual validation.

## Visual hierarchy
- The section header keeps the title on the left.
- Desktop preserves the text buttons.
- Mobile converts the section actions into square icon buttons with an `aria-label`/`title`.
- The instructor's attendance sits next to the class card, as an operational state.
- The graduation modal uses a visually fixed header, a scrolling body, and a contained width.

## Wireframe
### Today's classes — mobile
- Line 1: a chevron + "Turmas de hoje" ("Today's classes") + iconic actions: history, open class, schedule.
- The class card: the time, the name, the counters.
- Attendance: a `Presente 12:08` (`Present 12:08`) pill + the `Cancelar` (`Cancel`) and `Trocar professor` (`Change instructor`) buttons.

### The substitution modal
- Title: `Indicar substituto` (`Indicate a substitute`).
- Field: the substitute instructor.
- Actions: Cancel, Save.

### The graduation history modal — mobile
- A dark overlay.
- A sheet with a `max-height`.
- A header and a close button.
- A scrollable list, each item on a compact row.

## State machine
### The instructor's attendance
- `not_present`: a `Registrar presenca` (`Record attendance`) button.
- `present`: a `Presente HH:mm` (`Present HH:mm`) pill + `Cancelar` (`Cancel`) + `Trocar professor` (`Change instructor`).
- `cancelled`: no attendance action.
- `substituted`: the original instructor sees the substitute indicated; the substitute sees the class as an instructor.
- `loading`: the buttons disabled during the POST.
- `error`: a text error near the buttons.

### The modal
- `closed` -> `open` -> `submitting` -> `success` or `error`.

## Plan
- [x] 1. Intake, contracts, and context.
- [x] 2. The PRD before the code.
- [x] 3. Red tests.
- [x] 4. Implementation.
- [x] 5. Green tests and the checks.
- [x] 6. Desktop/mobile browser.
- [x] 7. Cleanup audit.

## Test plan
### Tests to author
- Service: cancelling attendance clears `instructor_present` and the time.
- Service: indicating a substitute validates ownership, an active instructor, and not oneself.
- Service/query: the substitute sees the day's regular class in `get_today_classes_for_instructor`.
- View: the cancel attendance endpoint returns JSON and respects the permission.
- View: the substitution endpoint returns JSON and blocks an invalid instructor.
- Template: the Home renders the cancellation/substitution actions when the instructor is present.

### Execution authorization
Local tests, a local migration, and the local ORM are authorized by the operational scope requested. Remote environments are not authorized.

### Execution evidence
- Focused Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - The result expected before the implementation: an import failure for `assign_session_substitute`.
- Focused Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - Result: OK.
- Proportional regression: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - Result: 24 tests OK.
- Django check: `.\.venv\Scripts\python.exe manage.py check`
  - Result: System check identified no issues.
- JS check: `node --check static\system\js\home\dashboard.js`
  - Result: no syntax error.
- Migration check: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
  - Result: No changes detected.

## Visual validation
- The internal browser at `http://127.0.0.1:8000/home/`, as the instructor Lauro.
- Mobile 375x667:
  - The `Turmas de hoje` (`Today's classes`) section actions rendered as 44x44 iconic buttons.
  - No horizontal overflow.
  - Attendance displayed with `Cancelar` (`Cancel`) and `Trocar professor` (`Change instructor`).
  - The history filters with `Todos` (`All`) defaults.
  - The substitute modal opened over the screen, with a select of active instructors and no console error.
  - The graduation history modal opened over the screen, with a controlled height and internal scrolling in the list.
- Desktop 1280x900:
  - The actions preserve their text and an appropriate width.
  - The filters default to `Todos` (`All`).
  - The cancel/substitute controls present.
  - No console error.
- Local screenshots:
  - `test_screenshots/prd-072-home-professor/mobile-home.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-attendance-modal.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-substitute-modal.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-grad-modal.jpg`
  - `test_screenshots/prd-072-home-professor/desktop-home.jpg`

## ORM validation
- `.\.venv\Scripts\python.exe manage.py migrate`
  - Result: `Applying system.0002_classsession_substitute_teacher... OK`.
- `.\.venv\Scripts\python.exe manage.py showmigrations system | Select-String "0002"`
  - Result: `[X] 0002_classsession_substitute_teacher`.

## Quality validation
- `git diff --check`
  - Result: no whitespace error; only local LF -> CRLF conversion warnings.
- A residue search:
  - `rg -n 'innerHTML|insertAdjacentHTML|outerHTML|debugger|console\.log|TODO|FIXME|href="#"|Django Admin' ...`
  - Result: occurrences only in this PRD and in existing negative test assertions.
- `dashboard.js` contains no `innerHTML`, `insertAdjacentHTML`, or `outerHTML` in the changed code.

## Evidence
- The official source used: Django 5.2 class-based views, `dispatch`, and the HTTP flow: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/
- Context7 confirmed the CBV, POST/CSRF, and Test Client contracts for Django 5.2.
- The visual validation done in the internal browser as the instructor Lauro on desktop and mobile.

## Implemented
- `ClassSession.substitute_teacher` added for a substitution per regular daily session.
- Services added to cancel the instructor's attendance, indicate a substitute, and cancel attendance in an open class.
- The queries adjusted so the substitute can see the day's regular class and be authorized by the ownership checks.
- JSON endpoints with CSRF added for cancelling attendance and for substitution.
- The instructor's Home now renders `Cancelar` (`Cancel`), `Trocar professor` (`Change instructor`), and the substitution modal.
- The attendance history filters now show the short `Todos` (`All`) default.
- The mobile `Turmas de hoje` (`Today's classes`) header uses 44x44 iconic actions with an `aria-label` and `title`.
- The graduation history modal now uses a controlled height and internal scrolling.
- The JavaScript removed the `innerHTML` update in the changed flow and uses a reload after the operational POSTs.

## Cleanup findings
- The diff is limited to the scope's files and to this PRD.
- No `debugger`, `console.log`, `TODO`, `FIXME`, new `href="#"`, or `innerHTML` was found in the changed Home code.
- The validation screenshots stayed in a local evidence folder ignored by Git.
- No mandatory follow-up PRD was identified within this fix's scope.

## Follow-up PRDs
- None created.

## Deviations from plan
- It was necessary to create a local migration to represent a substitute per regular daily session, because the previous schema had nowhere to persist that decision without a temporary rule in JavaScript/the template.
- During the visual validation, the browser was still loading `dashboard.js?v=1`; the template was updated to `dashboard.js?v=2` and the CSS to `dashboard.css?v=3`.

## Pending
- Deploy, HG/production, and applying the migration remotely are outside this round's scope.
- The complete validation of the student, guardian, back office, and admin was not repeated in this round; the validated fix was the instructor case requested by the comments.

## Final status
Completed with limitations: the instructor's flow fixed and validated locally; remote environments and the other roles remain pending authorization/their own round.
