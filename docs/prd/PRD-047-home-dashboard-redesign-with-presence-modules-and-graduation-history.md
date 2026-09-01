# PRD-047: Home dashboard — redesign with attendance modals and graduation history

## Summary of the implementation

A complete redesign of the `/home/` screen (the unified dashboard) for every profile:

1. **Class attendance → a modal per class** (instructor/staff): replace the inline check-in list (`class-item__checkins`) with a modal triggered by the `Ver presenças` (`View attendance`) button on each class. This solves the problem of 100 students rendered inline.
2. **Graduation history → a modal**: replace the inline toggle (`grad-history-panel`) with a modal triggered by `Ver histórico` (`See history`). It improves the section's visual proportion.
3. **Collapsible sections**: each main section gains a collapse button (a chevron), with the state persisted in `localStorage`. It lets the user minimize information.
4. **Proportions and layout**: a general visual review — more compact cards, a clearer typographic hierarchy, better use of space on desktop and mobile.
5. **Asset versions**: CSS `?v=7`, JS `?v=3`.

## Demand type

Interface redesign with UX refactoring — with no backend change.

## Current problem

- The check-in list rendered inline in the `class-item` expands the card to an unusable size (100 students = 100 lines in the class's own list).
- The graduation history in an inline toggle stacks many items inside the graduation card.
- Sections cannot be minimized — a long screen for every profile.
- The visual proportions are uneven: the graduation section is too big, and the classes section mixes information density with nested lists.

## Goal

A proportional, scannable, usable home interface: compact cards with visible quick actions, detail reachable through a modal, and collapsible sections to adapt the density to the user's profile.

## Context Ledger

### Files read in full

- `templates/home/dashboard.html` — the complete current template
- `static/system/css/home/dashboard.css` — the complete current CSS (v3 in the comment, ?v=6 in the template)
- `static/system/js/dashboard.js` — the complete current JavaScript (v2)
- `system/views/home_views.py` — the view's context and available variables
- `system/urls.py` — the existing routes
- `templates/calendar/calendar.html` — a reference for the unified modal pattern

### Adjacent files consulted

- `docs/UI-SCREEN-CONTRACT.md` — the UX contract
- `docs/prd/PRD-046-student-and-instructor-portal-graduation-schedule-dashboard-management.md` — the previous PRD (the evidence pattern)

### MCPs / tools verified

- Chrome MCP — available for visual validation

### Limitations found

- No model/service change needed: the data already exists
- `graduation_history` does not include "who awarded it" or "the reason" — the modal will show only the existing fields (date, belt, degree, is_current)

---

## Visual hierarchy

- Reading pattern: F Pattern (mobile: a single column, desktop: F reading)
- Topbar: weight 700, --text
- Page title `Olá, [nome]` (`Hi, [name]`): weight 800, 2rem, --text
- Section title (eyebrow): weight 700, 0.6875rem, --muted, uppercase
- Class name: weight 600, 0.875rem, --text
- Time: weight 700, 0.8125rem, --brand-red
- Subtitle (instructor, counter): weight 400, 0.75rem, --muted
- Status pills: weight 700, 0.6875rem
- Primary button: --brand-red, weight 600
- Secondary button: --border, weight 600

---

## Wireframe

### Region: Topbar (sticky)
- The LV logo + name (left)
- The theme button + logout (right)

### Region: Page header
- Eyebrow: the weekday + date (muted, uppercase)
- Title: `Olá, [nome]` (`Hi, [name]`) (bold 800)

### Region: Quick access (admin/staff)
- A 2→3→4 column grid of quick-links with an icon + label
- Collapsible (a chevron in the header)

### Region: Today's classes
- Section header: the title + actions (`Criar aulão` — `Create open class`, `Gerir cronograma` — `Manage schedule`) + a collapse chevron
- Panel: a list of class-items
  - [Time] · [Name · Category] / [sub info] / [action]
  - For the instructor: a `Ver presenças (N)` (`View attendance (N)`) button opens the attendance modal
  - For the student: a Check-in button / a `Confirmado` (`Confirmed`) pill / an `Aguardando` (`Waiting`) pill
  - Cancelled: a `Cancelada` (`Cancelled`) pill + the reason

### Region: Attendance modal (instructor)
- Title: `Presenças — [Nome da turma]` (`Attendance — [Class name]`)
- A close button (X)
- A scrollable list of students: [name] | [status pill] | [an `Aprovar` — `Approve` button when pending]
- An empty state when there are no check-ins

### Region: Graduation (student/staff)
- Section header: the title + a collapse chevron
- Panel: the belt SVG + name + degree + the "since" date
- A 3-column stats grid (when there is a rule)
- A progress bar + label
- A blocking/enabling message
- A `Ver histórico` (`See history`) button → opens the modal

### Region: Graduation history modal
- Title: `Histórico de graduação` (`Graduation history`)
- A close button (X)
- A list of belts with the date, name, degree, and an `Atual` (`Current`) badge

### Region: Tuition (student/guardian)
- Collapsible (a chevron)
- The active plan, a status badge, the due date, and the action buttons

### Region: Attendance history
- Collapsible (a chevron)
- A compact list: date + time | class · category | ✓

### Screen states
- Loading: rendered by the server; no spinner
- Empty (no classes): an empty-state with a calendar icon
- With data: the complete list
- Modal open: a darkened overlay, the modal centered (desktop) / a bottom sheet (mobile)

---

## State machines

### The attendance modal
- States: `closed` → `open`
- Transitions: the `Ver presenças` (`View attendance`) button → open; the ✕ button or the overlay → closed; Escape → closed
- Visual representation: an overlay + a modal with the check-in list

### The graduation history modal
- States: `closed` → `open`
- Transitions: the `Ver histórico` (`See history`) button → open; the ✕ button or the overlay → closed; Escape → closed
- Visual representation: an overlay + a modal with the graduation list

### The Approve button (inside the modal)
- States: `idle` → `loading` → `success`
- Transitions: click → disabled + `Aprovando…` (`Approving…`) → a `Confirmado` (`Confirmed`) pill
- On error: it restores the `Aprovar` (`Approve`) button

### A collapsible section
- States: `expanded` (default) ↔ `collapsed`
- Transitions: a click on the chevron toggles the state
- Persistence: `localStorage['lv-sections']`
- Visual representation: the chevron rotates 90°, the content is hidden

### The Check-in button (student)
- States: `idle` → `loading` → `success (Aguardando aprovação — Awaiting approval)` | `error`
- Visual representation: the button → an `Aguardando aprovação` (`Awaiting approval`) pill (warning) | an error message below

---

## Acceptance criteria

### Functional

- [ ] A `Ver presenças` (`View attendance`) button on each non-cancelled class (instructor/admin): on click, the modal opens with that specific class's check-in list (verifiable: visual inspection in Chrome MCP with the instructor profile)
- [ ] The attendance modal shows: the student's name, a status pill, and an `Aprovar` (`Approve`) button when pending (verifiable: visual inspection)
- [ ] On approving inside the modal, the button turns into a `Confirmado` (`Confirmed`) pill without reloading the page; the same approval is reflected if the modal is closed and reopened (verifiable: a Chrome MCP flow)
- [ ] The `Ver histórico` (`See history`) button in the graduation section opens a modal with every history entry (verifiable: a student with history in the database)
- [ ] The history modal shows an `Atual` (`Current`) badge on the current entry (verifiable: visual inspection)
- [ ] A chevron on each main section collapses/expands the section's content (verifiable: a click in Chrome MCP)
- [ ] The collapse state is persisted in localStorage (verifiable: a page reload)
- [ ] Every modal closes with Escape or a click on the overlay (verifiable: keyboard + click)
- [ ] The student's check-in flow stays functional (verifiable: a Chrome MCP flow with the student profile)
- [ ] The `Criar aulão` (`Create open class`) section and its creation modal stay functional (verifiable: a Chrome MCP flow with the instructor profile)

### UX / Visual

- [ ] Visual hierarchy: the section title at weight 700 muted uppercase; the class name at 600; the time in brand-red bold (verifiable: visual inspection)
- [ ] The modals render as a bottom sheet on mobile (≤600px) and centered on desktop (verifiable: resizing in Chrome MCP)
- [ ] The light and dark themes work across the whole screen and its modals (verifiable: the theme toggle)
- [ ] Every class-item state (normal, cancelled, with check-in, without check-in) renders correctly (verifiable: visual inspection)
- [ ] No `class-item__checkins` rendered inline for the instructor (verifiable: DevTools → no `.class-item__checkins` in the DOM)

---

## Expected evidence

- `manage.py test --verbosity 2` → 0 failures, 0 errors
- `manage.py check` → no issues
- Chrome MCP: screenshots of the screen with the student, instructor, and admin profiles in the light and dark themes
- The browser console: no JavaScript errors
- The terminal: no stack trace

---

## Scope

- `templates/home/dashboard.html` — a partial rewrite (the HTML structure + the modals)
- `static/system/css/home/dashboard.css` — CSS additions + a version bump (in the comment)
- `static/system/js/dashboard.js` — replacing `bindGradHistoryToggle` + adding the modals and section collapse

## Out of scope

- `system/views/home_views.py` — no changes
- `system/services/` — no changes
- New fields in the graduation model (granter, reason) — a future PRD
- The financial module (the stub remains)

## Impacted files

| File | Type of change |
|---|---|
| `templates/home/dashboard.html` | Modification — the main HTML + the modals |
| `static/system/css/home/dashboard.css` | Addition — the new modal and collapse components |
| `static/system/js/dashboard.js` | Modification — binding the modals and the collapse |

---

## Risks and edge cases

- **Cloning the check-in DOM**: if the checkin-source has many items, cloning may be slow → acceptable up to ~500 items
- **Approving in the modal with stale state**: after closing and reopening the modal with no reload, the approved buttons in the source div are already updated → OK
- **A collapsed section with no classes**: the empty-state must stay hidden while the section is collapsed → correct behavior, since the entire body is hidden
- **The technical admin profile (with no portal_person)**: `today_classes` and `graduation_progress` are empty → the screen renders with no conditional sections → OK
- **An open class (special class)**: `item.is_special = True`, the check-ins carry `data-is-special="true"` → the JavaScript uses `instructorApproveSpecialUrl` → OK

---

## Rules and constraints

- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking (`except: pass`)
- no migrations (no model change)
- mandatory full reading ✓
- mandatory in-browser visual validation

---

## Plan

- [x] 1. Full reading of every file in the flow
- [ ] 2. Writing PRD-047 with the visual hierarchy, wireframe, and state machines
- [ ] 3. Existing tests: ensure they pass with no backend change
- [ ] 4. Implementation: dashboard.html + dashboard.css + dashboard.js
- [ ] 5. Version bumps: CSS ?v=7, JS ?v=3
- [ ] 6. Visual validation: Chrome MCP, the themes, mobile and desktop
- [ ] 7. Final cleanup

---

## Visual validation

### Desktop (≥768px)
- A compact topbar, the logo visible
- Sections with a clear header and a collapse chevron
- Compact class items: the time in red, the name bold, the sub muted, the button on the right
- The attendance modal centered, max-width 520px
- Graduation: the belt SVG at 280–340px, a 3-column stats grid, a progress bar

### Mobile (375px)
- Sections stacked in a single column
- Class items on a compact line
- The modals as a bottom sheet (bottom: 0, border-radius only at the top)

### Browser console
- No JavaScript errors (TypeError, ReferenceError, etc.)
- No 404s on assets

### Terminal
- No stack trace

### Iteration 3 — Horizontal overflow fix
- Diagnosis in the browser before the fix: `.grad-history-list` with `clientWidth=421`, `scrollWidth=429`, `overflowX=auto`; the excess caused by `.grad-history-entry--current` with `margin: 0 -0.5rem`.
- Validation in the browser after the fix: `.grad-history-list` with `clientWidth=318`, `scrollWidth=318`, `overflowX=hidden`, `hasHorizontalOverflow=false`.
- The browser console: zero errors.
- `manage.py check` → 0 issues.
- `collectstatic --noinput` → 1 file copied, 173 unchanged.
- `manage.py test --verbosity 2` → 168 tests passing.
- No migration warnings

### Iteration 4 — Removal of the bottom `Fechar` (`Close`) button
- Validation in the browser: the history modal opened with `footerExists=false`, `footerCloseButtonCount=0`, `headerCloseButtonCount=1`.
- The header's X button closes the modal correctly.
- The browser console: zero errors.
- `manage.py check` → 0 issues.

### Iteration 5 — Removal of the Completion KPI
- Validation in the browser: `conclusionCards=0`, `gradStatCount=2`, `progressBarExists=true`.
- The browser console: zero errors.

### Iteration 6 — Attendance history inside Today's classes
- Validation in the browser: the main section headings = `Turmas de hoje` (`Today's classes`), `Graduação` (`Graduation`); `separateHistorySections=0`.
- Validation in the browser: `classesHistoryButtonCount=1`, with a `Histórico` (`History`) button inside `Turmas de hoje` (`Today's classes`).
- Validation in the browser: the modal opened with `modalRows=1`, a text filter, and `Página 1 de 1` (`Page 1 of 1`) pagination.
- Validation in the browser: the `sem` filter returned `visibleRows=0`, `pageText=Sem resultados` (`No results`); the `teste` filter returned `visibleRows=1`, `pageText=Página 1 de 1` (`Page 1 of 1`).
- The browser console: zero errors.

### Iteration 7 — Structured filters in the attendance history
- UX decision: replace the free text filter with explicit filters for class, instructor, month, and year.
- Updated criterion: the modal must render four selects (`Turma`, `Professor`, `Mês`, `Ano` — `Class`, `Instructor`, `Month`, `Year`) and a `Limpar` (`Clear`) button; each history row must expose structured attributes for client-side filtering.
- Red/Green test: `HomeDashboardTestCase.test_attendance_history_modal_uses_structured_filters` failed before the implementation because `type="search"` was still present, and passed after switching to the selects.
- Validation in the browser: `textSearchCount=0`, the filter labels = `Turma`, `Professor`, `Mês`, `Ano` (`Class`, `Instructor`, `Month`, `Year`); options rendered for class, instructor, month, and year.
- Validation in the browser: a combined class/instructor/month/year selection kept `visibleRows=1` and `Página 1 de 1` (`Page 1 of 1`) pagination; the `Limpar` (`Clear`) button reset every select and kept the list visible.
- The browser console: zero errors.

### Iteration 8 — Schedule visible to the student
- UX decision: the student must also reach `Cronograma` (`Schedule`) from `Turmas de hoje` (`Today's classes`) to look up the month's classes.
- Updated criterion: the `Turmas de hoje` (`Today's classes`) header must render the `/cronograma/` link for the student, without rendering instructor actions such as `Criar aulão` (`Create open class`).
- Red/Green test: `HomeDashboardTestCase.test_student_home_renders_calendar_link` failed before the implementation because the link did not exist for the student, and passed after the fix.

---

## ORM validation

No model change → no ORM validation needed.

---

## Quality validation

- No colors or measurements hardcoded outside the CSS tokens
- No `except: pass`
- No `innerHTML` with user data (use `textContent` or DOM cloning)
- No business rules in the template or the JavaScript

---

## Implemented

### Iteration 1 (the original PRD-047)
- `templates/home/dashboard.html` — rewritten with the attendance and history modals, collapsible sections, and the CSS ?v=7 and JS ?v=3 versions
- `static/system/css/home/dashboard.css` — added: `.section__title-row`, `.section__toggle`, `.modal__header`, `.modal__close`, `.modal-checkin-list`, `.modal-checkin-item*`, `.modal-empty`, `.grad-history-list`, `.grad-card__footer`; the comment updated to v4
- `static/system/js/dashboard.js` — added `bindPresenceModal`, `bindGradHistoryModal`, `bindSectionCollapse`; `bindApproveCheckins` converted to event delegation; `bindGradHistoryToggle` removed

### Iteration 2 — Redesign of the graduation section (requested by the user)
- `system/services/graduation.py` — `get_graduation_history` enriched with `belt_stripes` per entry (the stripe positions computed as in the main view)
- `templates/home/dashboard.html` — the graduation section restructured: compact by default (the belt SVG + `MINHA FAIXA` (`MY BELT`) + name/degree + a `Mais sobre a graduação +` (`More about the graduation +`) button), an inline expandable panel (`grad-details`) with enriched IBJJF stats, a progress bar, and `Ver histórico` (`See history`); the history modal rewritten with a belt SVG per entry, a date range, tenure, the granter, and notes; CSS `?v=8`, JS `?v=4`
- `static/system/css/home/dashboard.css` — added: `.grad-compact-header`, `.grad-compact-info*`, `.grad-details`, `.grad-stat__rule`, `.grad-stat__detail`, `.grad-details__footer`, `.grad-history-entry*`, `.grad-history-modal-footer`; the comment updated to v5
- `static/system/js/dashboard.js` — added `bindGradDetailsToggle` (an inline toggle for the details panel, with a + / − icon)

### Iteration 3 — Horizontal overflow fix in the history modal
- `static/system/css/home/dashboard.css` — `.grad-history-list` now blocks overflow on the X axis; the `margin: 0 -0.5rem` was removed from `.grad-history-entry--current`, which made the current entry exceed the list's usable width and triggered unnecessary horizontal scrolling.
- `templates/home/dashboard.html` — the CSS updated from `?v=8` to `?v=9`.

### Iteration 4 — Removal of a duplicated action in the history modal
- `templates/home/dashboard.html` — the `Fechar` (`Close`) button removed from the graduation history modal's footer. The modal remains closable through the X button in the header, a click on the overlay, and the Escape key.

### Iteration 5 — Removal of the duplicated completion KPI
- `templates/home/dashboard.html` — the `Conclusão` (`Completion`) KPI removed from the graduation section, because the percentage is already represented by the progress bar.
- `static/system/css/home/dashboard.css` — the graduation KPI grid adjusted from three to two columns; the comment updated to v7.
- `templates/home/dashboard.html` — the CSS updated from `?v=9` to `?v=10`.

### Iteration 6 — Attendance history in a modal triggered from Today's classes
- `templates/home/dashboard.html` — the separate `Histórico de presença` (`Attendance history`) section removed; a `Histórico` (`History`) button added to the `Turmas de hoje` (`Today's classes`) header; the `attendance-history-modal` created with a filter, a list, and pagination.
- `static/system/css/home/dashboard.css` — added styles for a wide modal, the attendance history's list, rows, and pagination; the comment updated to v8.
- `static/system/js/dashboard.js` — added `bindAttendanceHistoryModal`, with a normalized text filter and client-side pagination over the items rendered by the server.
- `templates/home/dashboard.html` — the CSS updated to `?v=11` and the JavaScript to `?v=5`.

### Iteration 7 — Filters by class, instructor, month, and year
- `templates/home/dashboard.html` — the text filter removed; the modal updated with selects for class, instructor, month, and year, a `Limpar` (`Clear`) button, and the `data-class-filter`, `data-teacher-filter`, `data-month-filter`, `data-month-label`, and `data-year-filter` attributes; the CSS updated to `?v=12` and the JavaScript to `?v=6`.
- `static/system/css/home/dashboard.css` — added styles for `.modal__select` and the responsive `.attendance-history-filters` grid; the wide modal widened to 720px; the comment updated to v9.
- `static/system/js/dashboard.js` — `bindAttendanceHistoryModal` now populates the selects from the rendered items and applies combined equality filters, preserving pagination and the empty state.
- `system/tests/test_home_dashboard.py` — a contract test added to prevent a regression back to the text filter.

### Iteration 8 — A Schedule link for the student
- `templates/home/dashboard.html` — the non-instructor branch of the `Turmas de hoje` (`Today's classes`) header now renders actions with `Histórico` (`History`) when there is history, and `Cronograma` (`Schedule`) always available.
- `system/tests/test_home_dashboard.py` — a test added ensuring `Cronograma` (`Schedule`) for the student and the absence of `Criar aulão` (`Create open class`).

## Evidence

### Automated tests
- `manage.py test --verbosity 2` → 168 tests passing, 0 errors
- `manage.py check` → 0 issues
- `collectstatic --noinput` → 2 files copied, 172 unchanged
- `manage.py test system.tests.test_home_dashboard.HomeDashboardTestCase.test_attendance_history_modal_uses_structured_filters --verbosity 2` → the new test passing

### Visual validation — the student profile (Wagner, light theme)
- The Graduation section compact by default: a white belt SVG + `MINHA FAIXA` (`MY BELT`) + `Branca` (`White`) + a `Mais sobre a graduação +` (`More about the graduation +`) button ✓
- Clicking the button expands the inline panel: `Faixa atual desde...` (`Current belt since...`), stats with IBJJF context (`regra IBJJF tempo mínimo: N meses` — `IBJJF rule minimum time: N months`, `faltam N meses para habilitar...` — `N months remaining to unlock...`), a progress bar, a blocking message, and `Ver histórico` (`See history`) ✓
- The button changes to `Mais sobre a graduação −` (`More about the graduation −`) when expanded ✓
- `Ver histórico` (`See history`) opens the `Histórico de graduações` (`Graduation history`) modal with a miniature belt SVG, a date range, tenure in red, notes in italics, and a green dot on the current entry ✓
- Escape closes the history modal ✓
- Console: zero JavaScript errors ✓

### Visual validation — the instructor profile (André, light theme)
- The Graduation section compact: a black belt with a red tip + degree 1 ✓
- The expanded panel: 1 month / a 36-month rule, 0 classes / a 192-class rule, a progress bar, and a block with 35 months and 192 classes remaining ✓
- The `Histórico de graduações` (`Graduation history`) modal: 18+ scrollable entries, each with the correct belt SVG (colors and degrees), dates, tenure in red, and closing through the header's X ✓
- The attendance modal (the 👥 1 button): opens with `WAGNER HELIO DA SILVA FILHO | Confirmado` (`| Confirmed`) ✓
- Escape closes the modals ✓
- Console: zero TypeError, ReferenceError, or critical network errors ✓

### Terminal
- No stack trace

## Deviations from plan

- `presenceModalsExist: false` for the student is the correct behavior: the attendance modal is only rendered when `show_instructor_area=True`
- The section collapse localStorage is shared per browser session (not per user); acceptable behavior
- The graduation section no longer has a section-chevron collapse — the internal toggle (`Mais sobre a graduação` — `More about the graduation`) replaced the previous pattern as requested by the user

## Pending

- None
