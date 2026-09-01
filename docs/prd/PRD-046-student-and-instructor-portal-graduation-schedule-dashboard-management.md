# PRD-046: Student and instructor portal — enriched graduation + schedule management on the dashboard

## Summary of the implementation

Enrichment of the dashboard's graduation section for every profile with detailed progression data (time at the belt, approved classes, % completion, a blocking/enabling message, a collapsible history). Addition of check-in management for instructors in the `Turmas de hoje` (`Today's classes`) section: a list of students per class with an approval button, the count of confirmed/pending, a `Criar aulão` (`Create open class`) button with an inline modal, and a `Gerir cronograma` (`Manage schedule`) link to the calendar screen. Registration of the instructor action routes that already exist in the code but are not mapped in `urls.py`. Creation of the calendar templates (`instructor_calendar.html` and `student_schedule.html`).

## Demand type

New feature + enrichment of an existing screen

## Current problem

1. The graduation section on the dashboard shows only the belt, degree, and a progress bar — with no graduation date, no breakdown of months at the belt vs. the required minimum, no count of approved classes vs. required, no enabling/blocking message, and no history.
2. The `Turmas de hoje` (`Today's classes`) section for instructors shows only the count of confirmed per class — with no student listing, no check-in approval button, no `Criar aulão` (`Create open class`), and no link to the schedule.
3. The instructor action views (`InstructorApproveCheckinView`, `InstructorApproveSpecialCheckinView`, `InstructorSpecialClassCreateView`, `InstructorToggleSessionView`, etc.) exist but their routes are not registered in `system/urls.py` — making them unreachable.
4. The `calendar/instructor_calendar.html` and `calendar/student_schedule.html` templates are referenced by the views but do not exist — they would cause a 500 in production if the routes were enabled.

## Goal

- Students see on the dashboard: the time at the current belt, approved classes vs. the minimum, % completion, a clear enabling or specific blocking message, and an expandable history.
- Instructors see on the dashboard: per class, a list of students with their check-in status and an `Aprovar` (`Approve`) button; a working `Criar aulão` (`Create open class`) button with a modal; and a `Gerir cronograma` (`Manage schedule`) link.
- Every instructor action route registered and working.
- The calendar templates created and working (monthly, navigable, with instructor actions).

## Context Ledger

### Files read in full

- `system/views/home_views.py` — the dashboard's context; graduation_progress, belt_rank, belt_stripes, billing_tabs
- `system/services/graduation.py` — compute_graduation_progress returns a complete SimpleNamespace with applicable_rule, current_graduation_date, months_in_current_grade, required_months, months_remaining, approved_classes_in_window, required_classes, missing_classes, is_eligible, progress_pct, blocker; get_graduation_history returns a list of entries with belt_rank, grade_number, awarded_at, period_months, is_current
- `system/services/class_calendar.py` — get_today_classes_for_instructor returns entries with checkins[], approved_count, pending_count; get_today_classes_for_person; approve_class_checkin; approve_special_checkin; create_special_class; toggle_session_cancel
- `system/views/calendar_views.py` — InstructorApproveCheckinView, InstructorApproveSpecialCheckinView, InstructorSpecialClassCreateView, InstructorSpecialClassDeleteView, InstructorToggleSessionView, InstructorCalendarView, StudentScheduleView — they all exist and have no route
- `system/urls.py` — only student-checkin and student-special-checkin are registered; the instructor routes are absent
- `templates/home/dashboard.html` — the current template; the graduation section with grad-card; the classes section with class-item
- `static/system/css/home/dashboard.css` — tokens, components; the current version is v5
- `static/system/js/dashboard.js` — bindCheckins (student), bindTabs, bindThemeToggle; v1

### Adjacent files consulted

- `system/models/calendar.py` — ClassCheckin, SpecialClassCheckin, CheckinStatus, ClassSession
- `system/forms/class_forms.py` — SpecialClassForm

### Internet / official documentation

- N/A — a pure Django/JavaScript/CSS implementation with no new dependencies

### MCPs / tools verified

- Chrome MCP — will be used for visual validation
- The `.venv` Python — a local Windows + PowerShell environment

### Limitations found

- `templates/calendar/` does not exist; the folder must be created (justification: the views already reference those paths and produce a 500 without the template)
- CLAUDE.md section 12 forbids creating ad-hoc folders during redesigns; this creation is justified by the PRD and because it is new functionality (not a redesign)

---

## Visual hierarchy

- Reading pattern: F Pattern (sections stacked on mobile, horizontal skimming on desktop)
- Section title (`GRADUAÇÃO`, `TURMAS DE HOJE` — `GRADUATION`, `TODAY'S CLASSES`): weight 700, `--muted`, uppercase 0.69rem
- Belt name: weight 700, `--text`, 1rem
- Stats (value): weight 700, `--text`, 1rem
- Stats (label): weight 600, `--muted`, 0.625rem uppercase
- Stats (sub): weight 400, `--muted`, 0.6875rem
- Blocking message: weight 500, `--warning`, background `--warning-muted`
- Eligible message: weight 500, `--success`, background `--success-muted`
- Student name in a check-in: weight 500, `--text`, 0.8125rem
- The `Aprovar` (`Approve`) button: `btn--primary btn--sm` (brand-red)

## Wireframe

### Graduation section (with applicable_rule)

```
[Belt SVG ─────────────────────────────────────────────]
[Belt: Name] [Xth degree]
Current belt since DD/MM/YYYY

[AT THE BELT   ] [APPROVED CLASSES] [COMPLETION ]
[X months      ] [X               ] [X%         ]
[min. Y months ] [min. Y classes  ] [           ]
[Z remaining   ] [Z remaining     ] [           ]

NEXT DEGREE                                      X%
[████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]

[X months and Y classes are still needed to unlock the next... ] ← blocker
OR
[✓ Eligible for the next graduation.                       ] ← eligible

[See history ▼]
  [MM/YYYY] [Belt, Degree] [Current?]
```

### Today's classes section (instructor)

```
TODAY'S CLASSES            [Create open class] [Manage schedule]

[19:00 · Adult — Prof. Preview · 3 confirmed · 1 pending ]
  [Student A ─────────────────────── Confirmed               ]
  [Student B ─────────────────────── Awaiting approval  [Approve]    ]

[—— empty ——]
```

### Create open class modal

```
╔════════════════════════════════╗
║  Create open class             ║
║  Title     [_________________] ║
║  Date      [_________________] ║
║  Time      [_________________] ║
║  Duration  [_________________] ║
║  [Error]                       ║
║              [Cancel] [Create]║
╚════════════════════════════════╝
```

### Screen states

- The `Aprovar` (`Approve`) button: idle → loading (disabled + `Aprovando…` — `Approving…`) → success (a `Confirmado` — `Confirmed` pill) | error (back to idle)
- The modal: hidden → open (slide-up) → loading (submit disabled) → closed (reload)
- The history: collapsed → expanded (the chevron rotates)

## State machines

### The check-in Approve button

- States: idle, loading, success, error
- Transitions: idle → click → loading → an OK response → success; a non-OK response → error → idle
- Visual representation: idle = btn--primary `Aprovar` (`Approve`); loading = disabled `Aprovando…` (`Approving…`); success = status-pill--success `Confirmado` (`Confirmed`); error = back to idle with a message

### The Create open class modal

- States: hidden, open, submitting, closed
- Transitions: click `Criar aulão` (`Create open class`) → open; click on the overlay/esc → hidden; submit → submitting → closed (reload) | error → open
- Visual representation: hidden = [hidden]; open = an overlay + slide-up; submitting = submit disabled

### The graduation history toggle

- States: collapsed, expanded
- Transitions: click → toggle; `aria-expanded` reflects the state
- Visual representation: collapsed = a normal chevron; expanded = the chevron rotated 180º

---

## Scope

1. `system/urls.py` — register the instructor routes (approve, approve-special, toggle-session, special-create, special-delete) and the calendar ones (instructor-calendar, instructor-calendar-month, student-schedule, student-schedule-month)
2. `templates/home/dashboard.html` — the enriched graduation section; the today's classes section for the instructor with the student list + an `Aprovar` (`Approve`) button + a `Criar aulão` (`Create open class`) button + a `Gerir cronograma` (`Manage schedule`) link; the create open class modal; the updated home-config JSON
3. `static/system/css/home/dashboard.css` — v6: .grad-awarded, .grad-stats, .grad-stat, .grad-message, .grad-history-toggle, .grad-history-panel, .grad-history-item, .class-item__checkins, .checkin-row, .section__actions, .modal-overlay, .modal, and their children
4. `static/system/js/dashboard.js` — v2: bindApproveCheckins, bindSpecialClassModal, bindGradHistoryToggle
5. `templates/calendar/instructor_calendar.html` — new (folder creation justified by the PRD)
6. `templates/calendar/student_schedule.html` — new

## Out of scope

- Cancelling a scheduled class through the dashboard (the button lives in the calendar, not on the dashboard)
- Approving a session cancellation through the dashboard
- The complete schedule CRUD in the calendar
- The student's attendance history on the dashboard (it already exists)
- The instructor's financial module (an existing stub)
- Creating new administrative calendar routes

## Impacted files

| File | Type of change |
|---|---|
| `system/urls.py` | Route additions |
| `templates/home/dashboard.html` | Edits to existing sections + the modal |
| `static/system/css/home/dashboard.css` | Style additions (v5→v6) |
| `static/system/js/dashboard.js` | Function additions (v1→v2) |
| `templates/calendar/instructor_calendar.html` | Creation |
| `templates/calendar/student_schedule.html` | Creation |

## Risks and edge cases

- `graduation_progress.applicable_rule` may be None → do not show the stats grid in those cases
- `graduation_progress.current_graduation_date` may be None (legacy with no date) → omit the date line
- An instructor with no classes today → the existing empty state works
- An open class created the same day → schedule_id does not exist (is_special=True) → checkin_kind="special"
- A check-in already approved before the click → the server returns success but is_approved is already true → idempotent
- A person with no belt_rank → the graduation section shows an empty state

## Rules and constraints

- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation through Chrome MCP
- `?v=` updated in the template when changing CSS and JavaScript

## Plan

- [x] 1. Context and full reading (completed above)
- [ ] 2. Register the routes in system/urls.py
- [ ] 3. Update dashboard.css (v6)
- [ ] 4. Update dashboard.js (v2)
- [ ] 5. Update dashboard.html (graduation + instructor + modal + config)
- [ ] 6. Create templates/calendar/instructor_calendar.html
- [ ] 7. Create templates/calendar/student_schedule.html
- [ ] 8. manage.py check + manage.py test
- [ ] 9. Visual validation with Chrome MCP
- [ ] 10. Cleanup and documentation update

## Acceptance criteria

- [ ] Student dashboard: shows `Faixa atual desde DD/MM/AAAA` (`Current belt since DD/MM/YYYY`) when current_graduation_date is not None (verifiable: visual)
- [ ] Student dashboard: shows a 3-column grid with `NA FAIXA / X meses / mín. Y` (`AT THE BELT / X months / min. Y`), `AULAS APROVADAS / X / mín. Y` (`APPROVED CLASSES / X / min. Y`), `CONCLUSÃO / X%` (`COMPLETION / X%`) when applicable_rule is not None (verifiable: visual)
- [ ] Student dashboard: shows a blocking message with the text of the blocking fields when not is_eligible (verifiable: visual)
- [ ] Student dashboard: shows the green message `Habilitado para a próxima graduação` (`Eligible for the next graduation`) when is_eligible (verifiable: visual)
- [ ] Student dashboard: the `Ver histórico` (`See history`) button expands/collapses the graduation list with the chevron rotating (verifiable: visual + click)
- [ ] Instructor dashboard: the `Turmas de hoje` (`Today's classes`) section has `Criar aulão` (`Create open class`) and `Gerir cronograma` (`Manage schedule`) buttons in the header (verifiable: visual)
- [ ] Instructor dashboard: each class shows a list of students with a status pill and an `Aprovar` (`Approve`) button for the pending ones (verifiable: visual)
- [ ] Instructor dashboard: clicking `Aprovar` (`Approve`) POSTs to instructor-approve-checkin or instructor-approve-special-checkin with checkin_id; on success it replaces the waiting pill + button with `Confirmado` (`Confirmed`) (verifiable: visual + network)
- [ ] Instructor dashboard: clicking `Criar aulão` (`Create open class`) opens the modal; submitting valid data creates the special class and reloads; an invalid submit shows the error in the modal (verifiable: visual + network)
- [ ] The `Gerir cronograma` (`Manage schedule`) link navigates to /cronograma/ (instructor-calendar) without a 404 (verifiable: navigation)
- [ ] GET /cronograma/ returns 200 for an instructor (verifiable: navigation)
- [ ] GET /cronograma/alunos/ returns 200 for a student (verifiable: navigation)
- [ ] manage.py check: 0 issues (verifiable: terminal)
- [ ] manage.py test: 0 failures, 0 errors (verifiable: terminal)
- [ ] The browser console: no JavaScript errors (verifiable: DevTools)

## Expected evidence

- manage.py check with 0 issues
- manage.py test with 0 failures
- A screenshot of the student dashboard with the graduation stats
- A screenshot of the instructor dashboard with the student list and the Approve button
- A screenshot of the `Criar aulão` (`Create open class`) modal
- Screenshots of the calendar pages (/cronograma/, /cronograma/alunos/)
- A clean browser console

---

## Visual validation

### Desktop
- The graduation section: the 3-column grid visible, the blocking message below the bar
- The instructor classes section: check-in rows with the pill + button aligned right
- The modal: centered on screen, max-width 480px

### Mobile
- The graduation section: the 3-column grid at 375px (smaller fonts but readable)
- Check-in rows: the name truncated but the Approve button visible
- The modal: full width, rounded corners at the top

### Browser console
- 0 JavaScript errors

### Terminal
- 0 stack traces on the server

## ORM validation

### Shell checks

```python
# Verify graduation_progress data
from system.services.graduation import compute_graduation_progress
from system.models import Person
p = Person.objects.first()
gp = compute_graduation_progress(p)
print(gp.current_graduation_date, gp.months_in_current_grade, gp.required_months, gp.is_eligible)
```

## Quality validation

### No hardcoding
- API URLs read from the JSON config, never hardcoded in the JavaScript

### No brittle conditional structures
- The JavaScript uses guard clauses; the template uses `{% if %}` directly, with no business logic

### No `except: pass`
- The JavaScript uses `.catch` with a log/error state; the Python views already have adequate handling

### No error masking
- Approve-checkin errors return to idle with the button re-enabled

### No unnecessary comments
- Self-explanatory code

---

## Evidence

### Iteration 2 — Schedule responsiveness
- UX decision: `/cronograma/` must have its own width on desktop, without being limited to the home's `max-width`; on mobile, the monthly grid must become a readable list of days.
- Interaction decision: clicking/tapping any day opens a modal with that day's complete information.
- Red/Green test: `CalendarServiceTestCase.test_calendar_page_renders_responsive_day_detail_contract` failed before the implementation because the template still used the old structure, and passed after adding `page--calendar`, `calendar-board`, `cal-grid--days`, the day buttons, and the `calendar-day-modal` modal.
- `system/services/class_calendar.py`: `weekday` now uses `date_format(..., "D")` to keep the day labels localized in pt-BR.
- Mobile validation in the browser (375px): `pageWidth=360`, `gridWidth=332`, `bodyOverflow=false`, 31 day buttons, the detail modal opened with the exact localized title `1 de Maio de 2026` (`May 1, 2026`) and the complete list of classes/cancellations.
- Desktop validation in the browser (2560px): `pageWidth=1720`, `gridWidth=1680`, columns of ~235px, days ~174px tall, `bodyOverflow=false`.

### Automated tests
- `manage.py test --verbosity 2` → **168 tests, 0 failures, 0 errors** (5.07s)
- `manage.py check` → **System check identified no issues (0 silenced)**
- `manage.py collectstatic --noinput` → **174 static files collected**

### Visual validation — Desktop (Chrome MCP, 127.0.0.1:8000)

**Admin / a user with `show_instructor_area`:**
- The dashboard shows `Criar aulão` (`Create open class`) + `Gerir cronograma` (`Manage schedule`) in the TODAY'S CLASSES header ✅
- The `Criar aulão` (`Create open class`) modal: opens on the button click, closes with Escape and the Cancel button, and contains the Title / Date (pre-filled with today) / Time / Duration fields ✅
- Navigating to `/cronograma/` renders the complete monthly calendar (May 2026) with class pills ✅
- The instructor's (owned) class pills in blue; open class pills in red; cancelled pills struck through ✅
- The legend: `Minhas turmas` (`My classes`) (blue) / `★ Aulão` (`★ Open class`) (red) / `Cancelada` (`Cancelled`) ✅
- The `Criar aulão` (`Create open class`) button present in the calendar's header ✅

**The instructor (Layon Quirino Vidal — black belt, 1st degree, CPF 920.000.000-01):**
- Dashboard: the greeting `Olá, Layon ...` (`Hi, Layon ...`) ✅
- TODAY'S CLASSES: `Criar aulão` (`Create open class`) + `Gerir cronograma` (`Manage schedule`) visible ✅
- The GRADUATION section: the black belt, 1st degree, with the correct visual (a black belt + a white divider + a red stripe) ✅
- `Faixa atual desde 10/10/2023` (`Current belt since 10/10/2023`) ✅
- Stats: AT THE BELT 31 months (min. 36 · 5 remaining) / APPROVED CLASSES 0 (min. 192 · 192 remaining) / COMPLETION 43% ✅
- The `Próximo grau` (`Next degree`) progress bar at 43% ✅
- The amber blocking message: `Faltam 5 meses na faixa e 192 aulas aprovadas para habilitar a próxima graduação.` (`5 months at the belt and 192 approved classes are still needed to unlock the next graduation.`) ✅
- The `Ver histórico` (`See history`) toggle present ✅
- The `Gerir cronograma` (`Manage schedule`) link navigates to `/cronograma/` with the owned pills in blue ✅

**The student (WAGNER HELIO — white belt, CPF 014.337.401-09):**
- Dashboard: the greeting `Olá, WAGNER ...` (`Hi, WAGNER ...`) ✅
- TODAY'S CLASSES: no instructor buttons (only the schedule link does not appear) ✅
- The GRADUATION section: the white belt with the correct visual ✅
- `Faixa atual desde 24/05/2026` (`Current belt since 24/05/2026`) ✅
- Stats: AT THE BELT 0 months (min. 4 · 4 remaining) / APPROVED CLASSES 0 (min. 32 · 32 remaining) / COMPLETION 0% ✅
- The progress bar at 0% ✅
- The amber blocking message: `Faltam 4 meses na faixa e 32 aulas aprovadas para habilitar a próxima graduação.` (`4 months at the belt and 32 approved classes are still needed to unlock the next graduation.`) ✅
- The `Ver histórico` (`See history`) toggle: expands and shows `05/2026 | Branca | Atual` (`05/2026 | White | Current`) with the chevron rotating ✅
- TUITION: an `ATIVO` (`ACTIVE`) badge + the plan name + the due date ✅

**The student's schedule (`/cronograma/alunos/`):**
- Renders a read-only monthly calendar ✅
- No `Criar aulão` (`Create open class`) button ✅
- The legend: `Aula regular` (`Regular class`) / `★ Aulão` (`★ Open class`) / `Cancelada` (`Cancelled`) ✅

### Browser console
- Zero application errors ✅
- Only 5 Chrome extension exceptions ("message channel closed before response") — unrelated to the app ✅

### Terminal
- Zero stack traces throughout the validation ✅

## Implemented

- `system/urls.py`: 9 new routes registered for the calendar/check-in views that already existed but had no URL
- `static/system/css/home/dashboard.css` (v5→v6): CSS for `grad-awarded`, `grad-stats`, `grad-message`, `grad-history-*`, the modal, `checkin-row`, `cal-*`, `section__actions`
- `static/system/js/dashboard.js` (v1→v2): `bindApproveCheckins()`, `bindSpecialClassModal()`, `bindGradHistoryToggle()`
- `templates/home/dashboard.html`: the enriched graduation section, the instructor's check-ins, the `Criar aulão` (`Create open class`) modal, and an update to the `home-config` JSON
- `templates/calendar/instructor_calendar.html`: created (the new `templates/calendar/` folder)
- `templates/calendar/student_schedule.html`: created
- `templates/calendar/calendar.html`: updated to the schedule's own responsive layout, with the day detail in a modal
- `static/system/css/home/dashboard.css`: responsive styles added for `.page--calendar`, `.calendar-board`, `.cal-grid--days`, `.cal-day__button`, the mobile list, and the day detail modal
- `system/tests/test_calendar.py`: a contract test added for the schedule's responsive layout

## Deviations from plan

- The `templates/calendar/` folder was created despite the general "do not create new folders" rule — necessary and justified in the PRD because the views already referenced those templates
- The `Criar aulão` (`Create open class`) modal in `instructor_calendar.html` was implemented with inline JavaScript (not in `dashboard.js`) because the calendar page is standalone and does not load `dashboard.js`
- The technical admin (`is_superuser`) receives `show_instructor_area=True` by permission inheritance in the view — existing behavior, unchanged

## Pending

- Live check-in management was not tested with classes on the day (today is Sunday — with no scheduled classes); the `checkin-row` and `js-approve-checkin` logic is implemented and the endpoints are registered, but they need testing on a weekday with classes in the schedule
- The calendar screen: the session toggle/cancel feature (`InstructorToggleSessionView`) is implemented at the URL level but has no button in the current UI (out of this PRD's scope)
