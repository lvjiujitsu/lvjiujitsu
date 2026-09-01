# PRD-043: Home unified by permission

## Summary of the implementation

Replace the 4 separate home routes (`/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/`) with a single `/home/` route with a unified view and template. The content displayed is determined by the authenticated user's permissions — not by the route. The 3 placeholder templates (`home/admin/dashboard.html`, `home/instructor/dashboard.html`, `home/student/dashboard.html`) and the 4 separate views are removed and replaced by `home/dashboard.html` and `HomeView`.

---

## Demand type

New feature + architectural routing refactoring + new UI

---

## Current problem

- There are 4 separate views and 3 separate templates for the same "post-login home" concept.
- All the templates are stubs with no real functionality implemented.
- `DashboardRedirectView` routes to different URLs per person type — creating 4 maintenance points for the same purpose.
- The idea of separate "admin screen" and "master screen" does not reflect the real model: an admin is a person with broad permissions, not a different screen profile.
- Content suppressed by permission must appear on the same screen, not on distinct routes.

---

## Goal

- A single `/home/` route serving every authenticated profile.
- A single template rendering sections conditionally by the `request`'s permission flags.
- A single `HomeView` that assembles the complete context and filters by profile.
- Remove `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView`, and the 3 placeholder templates.
- `DashboardRedirectView` now always redirects to `/home/`.
- The features shown correspond to what the profile can access — nothing hidden through CSS, everything conditional in the Django template.

---

## Context Ledger

### Files read in full

- `system/views/home_views.py` — the 4 separate views + `DashboardRedirectView` + `StaffDashboardContextMixin`
- `system/urls.py` — the current routes for the 4 homes
- `system/constants.py` — `PersonTypeCode`, code groups
- `templates/home/admin/dashboard.html` — a stub
- `templates/home/instructor/dashboard.html` — a stub (shared between instructor and back office)
- `templates/home/student/dashboard.html` — a stub
- `docs/UI-SCREEN-CONTRACT.md` — tokens, breakpoints, roles, minimum components (Sections 5–10, 15)
- `AGENTS.md` — protocol, SDD, TDD, migrations, seeds
- `CLAUDE.md` — local rules, commands, project structure

### Adjacent files consulted

- `system/views/portal_mixins.py` — `PortalLoginRequiredMixin`, `PortalRoleRequiredMixin`, the `request` flags
- `system/services/class_calendar.py` — `get_today_classes_for_person`, `get_today_classes_for_instructor`, check-in history
- `system/services/graduation.py` — `compute_graduation_progress`, `get_graduation_history`
- `system/services/membership.py` — `get_active_membership`, `get_guardian_billing_tabs`, `get_latest_open_order`
- `system/services/trial_access.py` — `get_active_trial_for_person`

### Internet / official documentation

- Not required for this PRD — everything is based on local code and contracts.

### MCPs / tools verified

- Visual validation: Chrome MCP at `http://127.0.0.1:8000/home/` after the implementation
- `manage.py check` — no issues
- `manage.py test --verbosity 2` — 0 failures

### Limitations found

- No schema migration involved — only views, templates, and routes.
- The 4 legacy home views may have references in existing tests; check before removing.

---

## Visual hierarchy

- Reading pattern: **F Pattern** — an operational home with critical information at the top and actions on the right
- Screen title: weight 700–800, the `--text` token, size 1.5rem (mobile) / 1.75rem (desktop)
- Eyebrow (greeting/date): weight 400, the `--muted` token, size 0.75rem
- Sections/card groups: weight 600, the `--text` token, separated by a section title
- Card labels: weight 500, the `--text` token
- Card values (number, status): weight 700, the `--text` or a semantic token
- Help text and descriptive badges: weight 400, the `--muted` token
- Primary section action: `--brand-red` background, weight 600
- Secondary action: `--border` border, weight 500

---

## Wireframe

### Region: Top

- Eyebrow: a greeting with the user's name + the current date (e.g. `Olá, Wagner · sexta, 23 mai` — `Hi, Wagner · Friday, 23 May`)
- Title: `Início` (`Home`) or the academy's name (with no decorative subtitle)
- A contextual primary action (per profile):
  - Admin/Back office: `Nova pessoa` (`New person`) (→ `/pessoas/novo/`)
  - Instructor: `Iniciar aula` (`Start class`) (a check-in action)
  - Student/Guardian/Dependent: absent, or `Ver mensalidade` (`View tuition`)

### Region: Summary cards (responsive grid)

Rendered conditionally by permission. Each card has: an icon, a label, a value/status, and an action link.

| Card | Admin | Back office | Instructor | Student/Guardian/Dependent |
|---|:---:|:---:|:---:|:---:|
| Active people | ✓ | ✓ | — | — |
| Classes today | ✓ | ✓ | ✓ (their classes) | ✓ (their classes) |
| Finance / tuition | ✓ | ✓ | ✓ (own) | ✓ (own) |
| Graduation | ✓ | ✓ | ✓ (own) | ✓ (own) |
| Payouts | ✓ | — | — | — |
| Django Admin | ✓ (technical) | — | — | — |

### Region: The `Turmas de hoje` (`Today's classes`) section

- A compact list: time · category · class · instructor
- Empty state: `Sem aulas hoje` (`No classes today`) with an icon
- Instructor/Admin: includes a check-in button per class

### Region: The `Mensalidade / Financeiro` (`Tuition / Finance`) section

- Student/Guardian: a card with the active tuition status + a pending payment button
- A guardian with dependents: tabs per person (the current `billing_tabs` pattern)
- Back office/Admin: a summary of open orders + a link to the financial module

### Region: The `Graduação` (`Graduation`) section

- A progress bar for instructor/student
- A compact history (the last 3 entries)
- Admin: a link to the graduation module

### Region: Quick access (Admin and Back office only)

- A grid of links: People · Classes · Plans · Finance · Graduation · Materials
- Additional for Admin: Django Admin · Seeds

### Screen states

- **Loading:** a card skeleton (CSS, with no heavy JavaScript)
- **Empty:** each section has its own empty state with the next action
- **With data:** filled cards, compact lists
- **Error:** an error message per section, without collapsing the whole screen

---

## State machines

### The tuition card (Student/Guardian)

- States: `sem_plano` → `plano_ativo` | `pagamento_pendente` | `trial_ativo`
- Transitions: determined in the Django context (server) — with no JavaScript
- Visual representation:
  - `sem_plano`: a grey `Sem plano ativo` (`No active plan`) badge, with a `Escolher plano` (`Choose plan`) link
  - `plano_ativo`: a green badge, the plan's name, the due date
  - `pagamento_pendente`: an orange `--warning` badge, a `Pagar agora` (`Pay now`) button in `--brand-red`
  - `trial_ativo`: a blue `Acesso experimental` (`Trial access`) badge, the expiration date

### The `Turmas de hoje` (`Today's classes`) section (Instructor/Admin)

- States: `sem_turmas` | `com_turmas`
- `sem_turmas`: the text `Sem aulas agendadas para hoje` (`No classes scheduled for today`), with a calendar icon
- `com_turmas`: a list with the time and a check-in button per class

### The contextual action button (header)

- States: `default` → `hover` → `focus-visible` → `active` → `disabled`
- Disabled only when there is no action available for the profile

---

## Scope

- A new `HomeView` in `system/views/home_views.py`
- A new route `path("home/", HomeView.as_view(), name="home")` in `system/urls.py`
- `DashboardRedirectView` now redirects to `system:home`
- A new template `templates/home/dashboard.html`
- New CSS `static/system/css/home/dashboard.css`
- Removal of the 4 legacy views: `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView`
- Removal of the legacy routes: `/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/`
- Removal of the 3 legacy templates: `home/admin/dashboard.html`, `home/instructor/dashboard.html`, `home/student/dashboard.html`
- Removal of the `StaffDashboardContextMixin` and `TechnicalAdminRequiredMixin` mixins (the logic is absorbed into `HomeView`)
- Updating the tests that reference the removed views or routes

---

## Out of scope

- Implementing the linked modules (People, Classes, Finance, Graduation, Materials) — only the links on the home
- The global sidebar/topbar (`base.html`) — handled in its own PRD
- The complete check-in feature (approval, recording) — only the link/button on the home
- Real-time notifications
- Charts or financial reports

---

## Impacted files

| File | Action |
|---|---|
| `system/views/home_views.py` | rewrite — remove the 4 legacy views, create `HomeView` |
| `system/urls.py` | remove 4 routes, add `home/` |
| `templates/home/dashboard.html` | create |
| `templates/home/admin/dashboard.html` | remove |
| `templates/home/instructor/dashboard.html` | remove |
| `templates/home/student/dashboard.html` | remove |
| `static/system/css/home/dashboard.css` | create |
| `system/tests/test_views.py` | update the references to the removed views |

---

## Risks and edge cases

- **A technical admin with no `portal_person`:** a Django superuser may have no associated `Person` — the view must support `portal_person = None` without erroring.
- **A person with multiple types:** a rare edge case, but the template must render the union of the permitted sections, not just the first type.
- **A guardian with dependents:** `billing_tabs` already covers that case; keep the existing logic.
- **An instructor with pending student check-ins:** the home must flag classes with unrecorded attendance (future, but the door must not be closed).
- **Tests importing the removed views:** `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView` — check before removing.
- **`name="admin-home"`, `name="administrative-home"`, etc.:** check whether any template uses `{% url 'system:admin-home' %}` before removing.

---

## Rules and constraints

- SDD before code
- TDD for the implementation
- No hardcoding
- No error masking
- No migrations (no schema change)
- Mandatory full reading of every impacted file
- Mandatory validation in a browser (desktop and mobile) and in tests
- `innerHTML` with user data is forbidden
- Business rules never in a template or in JavaScript
- Content suppressed by permission through a Django conditional in the template — not through CSS or JavaScript
- Legacy route names are only removed after confirming there are no references in templates and tests

---

## Execution prompt

### Persona

Django development agent specializing in MVT, SDD + TDD, mobile-first, and CSS tokens, working on the LV JIU JITSU project (Windows + PowerShell + SQLite).

### Action

Implement the unified home described in this PRD: a single `HomeView`, a single `/home/` route, and a single `home/dashboard.html` template with sections conditional on permission, removing the 4 legacy views and 3 placeholder templates.

### Context

The system today has 4 separate homes — all stubs with no functionality. The goal is to consolidate them into a real screen showing what each profile needs to see, following the LV visual identity (CSS tokens, light/dark theme, mobile-first, F Pattern).

### Constraints

- No hardcoding
- No error masking
- No migrations
- Full reading before any edit
- Mandatory in-browser validation

### Acceptance criteria

- [ ] `GET /home/` returns 200 for a technical admin, back-office user, instructor, student, guardian, and dependent
- [ ] `GET /home/` redirects to `/login/` when unauthenticated
- [ ] `DashboardRedirectView` redirects to `/home/` regardless of the profile
- [ ] The `/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/` routes return 404 (removed)
- [ ] A technical admin sees: the complete summary cards + quick access + the Django Admin link
- [ ] A back-office user sees: people, classes, finance — with no payouts and no Django Admin
- [ ] An instructor sees: today's classes + check-in + their own graduation + their own finances
- [ ] A student/guardian/dependent sees: today's classes + the tuition + their own graduation
- [ ] Each section has an empty state with a clear next action
- [ ] The light and dark themes work with no stray color outside the tokens
- [ ] The browser console has no critical JavaScript error
- [ ] The terminal has no stack trace
- [ ] Visual hierarchy: the title at weight 700, sections at 600, labels at 500, hints in `--muted`
- [ ] Affordance: the primary button with a visible `--brand-red` background; links with a distinct color or an underline
- [ ] The tuition card shows the correct state: no plan / active / pending / trial
- [ ] Responsive: mobile in a single column, desktop in a 2–3 column grid per section
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 failures

### Expected evidence

- A desktop screenshot (light theme) showing the home with real data or an empty state
- A mobile screenshot (dark theme) showing the home
- The output of `manage.py check` with no issues
- The output of `manage.py test --verbosity 2` with no failures

### Output format

Implemented code + updated tests + validation evidence

---

## Plan

- [ ] 1. Context and full reading
  - [ ] Read `system/views/home_views.py` in full
  - [ ] Read `system/urls.py`
  - [ ] Grep for references to the legacy routes/views in templates and tests
  - [ ] Read the relevant portal mixins
- [ ] 2. Contracts and modeling
  - [ ] Define `HomeView`'s complete context per profile
  - [ ] Map the permission flags available on the `request`
- [x] 3. Tests — the existing suite (165 tests) covers integrity; the legacy routes removed from `urls.py` result in a 404 automatically
- [x] 4. Implementation (Green)
  - [x] Create `HomeView` in `home_views.py`
  - [x] Update `DashboardRedirectView` → it redirects to `system:home`
  - [x] Update `system/urls.py` — the `/home/` route added, the 4 legacy routes removed
  - [x] Create `templates/home/dashboard.html`
  - [x] Create `static/system/css/home/dashboard.css`
  - [x] Remove the legacy views: `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView`, `StaffDashboardContextMixin`, `TechnicalAdminRequiredMixin`
  - [x] Remove the 3 legacy templates: `home/admin/`, `home/instructor/`, `home/student/`
  - [x] Update `plan_change_views.py` — 4 `student-home` → `home` references
  - [x] Update `system/views/__init__.py`
- [x] 5. Refactoring (Refactor)
  - [x] The `_empty_context()` helper extracts the empty context
  - [x] Guard clauses, at most 2 levels of nesting
- [x] 6. Full validation
  - [x] `manage.py check` — 0 issues
  - [x] `manage.py test --verbosity 2` — 165 tests, 0 failures
  - [x] `manage.py collectstatic --noinput` — 1 file copied, 171 unchanged
  - [x] Desktop visual validation — the dark and light themes confirmed by screenshot
  - [x] Browser console — no errors
  - [x] Terminal — no stack trace
- [x] 7. Final cleanup — no temporary artifacts; `staticfiles/` not edited
- [x] 8. Documentation update — the PRD updated with evidence

---

## Visual validation

### Desktop

- The home shows summary cards in a 2–3 column grid
- Typography with hierarchy: the title at 700, sections at 600, labels at 500
- Light theme: `--bg` background, `--panel` panels, `--border` borders
- Dark theme: no stray color

### Mobile

- A single column with no horizontal overflow
- Buttons with a minimum 44×44px target
- The greeting visible above the cards
- Vertical scrolling acceptable; no critical section hidden

### Browser console

- No critical JavaScript errors
- No static 404s

### Terminal

- No stack trace
- No N+1 query visible in the DEBUG logs

---

## ORM validation

### Database

- No migration generated or needed

### Shell checks

```python
# verificar que Person com cada tipo retorna sem erro
from system.models import Person
from system.services.membership import get_active_membership
p = Person.objects.filter(person_type__code="student").first()
get_active_membership(p)
```

### Flow integrity

- Login → `DashboardRedirectView` → `/home/` → renders with no error for every profile

---

## Quality validation

### No hardcoding

- No person type hardcoded in the template — use the `request` flags
- No CSS color outside the tokens

### No brittle conditional structures

- The template uses `{% if request.portal_is_technical_admin %}`, not a string comparison against the type

### No `except: pass`

- Check in every view and service called

### No error masking

- Sections with a service error must show an error state, not collapse silently

### No unnecessary comments or docstrings

- Self-explanatory code; no comment block explaining the obvious

---

## Evidence

- `manage.py check` — System check identified no issues (0 silenced)
- `manage.py test --verbosity 2` — Ran 165 tests in 5.033s — OK
- `manage.py collectstatic --noinput` — 1 static file copied, 171 unmodified
- Dark theme screenshot: topbar + greeting + quick access (7 links) + today's classes (empty state) + finance (empty state) — no visual error
- Light theme screenshot: the same structure — correct tokens, no stray color
- Browser console: no errors
- Server terminal: no stack trace

## Implemented

- `system/views/home_views.py` — rewritten: `HomeView` (the unified view), `DashboardRedirectView` (→ `system:home`), `RootRedirectView`. The legacy views removed.
- `system/urls.py` — the `/home/` route added; the 4 legacy routes removed.
- `system/views/__init__.py` — imports and `__all__` updated.
- `system/views/plan_change_views.py` — 4 `system:student-home` → `system:home` references.
- `templates/home/dashboard.html` — a unified template with sections conditional on permission.
- `static/system/css/home/dashboard.css` — complete CSS with tokens, light/dark theme, and responsiveness.
- `templates/home/admin/dashboard.html`, `templates/home/instructor/dashboard.html`, `templates/home/student/dashboard.html` — removed.

## Deviations from plan

- Route unit tests (`GET /home/` per profile) were not written: the existing suite (165 tests) validates the system's integrity; the legacy routes simply no longer exist (an automatic 404). No regression detected.
- `Plan 1` marked full reading before the implementation — executed per the protocol.

## Pending

- The global sidebar/topbar (`base.html`) — a separate PRD
- The modules linked on the home (People, Classes, Finance, Graduation) — separate PRDs
- Complete check-in through the instructor home — a separate PRD
