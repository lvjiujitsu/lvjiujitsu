# PRD-045: People module — list, detail, form, and delete confirmation

> Complete implementation of the people module's screens:
> a list with filters and KPIs, a detail with graduation and tuition,
> a create/edit form, and a delete confirmation.
> All the backend (views, forms, selectors, services) already exists.
> This PRD covers URLs, templates, and CSS.

---

## Summary of the implementation

1. Register the people module's 5 routes in `system/urls.py`.
2. Create `templates/people/` with 4 server-rendered templates.
3. Create `static/system/css/people/` with the module's CSS.
4. Update the `Pessoas` (`People`) quick-link on the home to point to `system:person-list`.
5. No model or migration change at all.

---

## Demand type

New feature — UI implementation for an existing backend

---

## Current problem

The `PersonListView`, `PersonDetailView`, `PersonCreateView`, `PersonUpdateView`, and `PersonDeleteView` views are implemented in `system/views/person_views.py` with all the context logic, but:

- **No route is registered** in `system/urls.py` — the module is unreachable
- **No template exists** — `templates/people/` does not exist
- **No CSS exists** — `static/system/css/people/` does not exist
- The `Pessoas` (`People`) quick-link on the home points to `href="#"`

---

## Goal

Make the people module reachable and operational for staff (admin + back office + instructor with support access), with:

- A dense, scannable list with filters, KPIs, and person cards
- A complete detail: personal data, classes, graduation, tuition
- A create/edit form with well-organized field groups
- A safe delete confirmation
- UX and CSS following the `dashboard.css` standard (tokens, shadows, typographic hierarchy)
- Mandatory light and dark themes

---

## Context Ledger

### Files read in full

- `system/views/person_views.py` — the views, the context, the `_hydrate_person_relationships` and `_build_people_kpis` helpers
- `system/models/person.py` — `Person`, `PortalAccount`, `PersonRelationship`, `PersonType`
- `system/selectors/person_selectors.py` — `get_person_queryset`, the available filters
- `system/forms/person_forms.py` — `PersonForm` (groups: identity, health, martial_art, relationship, payroll), `PersonListFilterForm`
- `system/urls.py` — no person route registered
- `system/constants.py` — `PersonTypeCode`, `CLASS_ENROLLMENT_PERSON_TYPE_CODES`, `ADMINISTRATIVE_PERSON_TYPE_CODES`, `INSTRUCTOR_PERSON_TYPE_CODES`, `PEOPLE_SUPPORT_PERSON_TYPE_CODES`
- `static/system/css/home/dashboard.css` — the token system and visual standard to follow

### Adjacent files consulted

- `system/services/graduation.py` — `compute_graduation_progress`, `get_graduation_history`
- `system/services/membership.py` — `get_active_membership`, `get_membership_owner`
- `templates/home/dashboard.html` — a reference for the visual components (topbar, panel, badge, btn)

### Limitations found

- `templates/people/` does not exist — creating a new folder in `templates/` is necessary and justified by the paths already defined in the views
- `static/system/css/people/` does not exist — likewise
- Creating new folders inside `templates/` and `static/system/css/` is allowed because the views already reference those paths; CLAUDE.md's "do not create folders" rule applies to the context of redesigning existing screens
- The people module's routes are not in `system/urls.py` — the view import exists, but it is unreachable

---

## Access permissions

| View | Mixin | Access |
|---|---|---|
| `PersonListView` | `PeopleSupportRequiredMixin` | technical admin + back office + instructor |
| `PersonDetailView` | `PeopleSupportRequiredMixin` | technical admin + back office + instructor |
| `PersonCreateView` | `PeopleSupportRequiredMixin` | technical admin + back office + instructor |
| `PersonUpdateView` | `AdministrativeRequiredMixin` | technical admin + back office |
| `PersonDeleteView` | `AdministrativeRequiredMixin` | technical admin + back office |

`_can_manage_people(request)` = technical admin or back office → controls the visibility of destructive actions and the payroll fields.

---

## Data context per screen

### List (`PersonListView`)

```python
context["people"]        # QuerySet hydrated with active_group_labels, teaching_group_labels,
                         # resolved_ibjjf_category, show_student_context, show_teacher_context
context["filter_form"]   # PersonListFilterForm — name, CPF, category, class, schedule, instructors only
context["can_manage_people"]    # bool — technical admin or back office
context["person_create_label"]  # "Nova pessoa" ("New person") | "Cadastrar aluno" ("Register student")
context["people_kpis"]          # [{"label": str, "value": int}] — 6 KPIs
```

Available KPIs: Students, Instructors, Back office, Active, Inactive, Pending (with no portal access).

Per hydrated person:
- `person.active_group_labels` — the student's classes (a list of str)
- `person.active_schedule_labels` — the student's schedules (a list of str)
- `person.teaching_group_labels` — the classes the instructor teaches
- `person.teaching_schedule_labels` — the teaching schedules
- `person.resolved_ibjjf_category` — the IBJJF category (an object or None)
- `person.show_student_context` — bool
- `person.show_teacher_context` — bool
- `person.has_portal_access` — bool (a property)

### Detail (`PersonDetailView`)

Beyond the person's fields:
```python
context["graduation_progress"]   # SimpleNamespace from compute_graduation_progress
context["graduation_history"]    # list of Graduation
# Only when can_manage_people:
context["memberships"]           # list of all Membership records
context["active_membership"]     # active Membership or None
context["billing_owner"]         # Person responsible for payment
context["person_invoices"]       # list of the last 10 MembershipInvoice records
context["person_orders"]         # list of the last 15 RegistrationOrder records
context["pending_orders"]        # list of RegistrationOrder records with pending payment
context["available_plans"]       # list of active SubscriptionPlan records
```

### Form (`PersonCreateView` / `PersonUpdateView`)

The `PersonForm` field groups:
| Group | Fields |
|---|---|
| Identity | `full_name`, `cpf`, `email`, `phone`, `birth_date`, `biological_sex` |
| Health | `blood_type`, `allergies`, `previous_injuries`, `emergency_contact` |
| Martial art | `has_martial_art`, `martial_art`, `martial_art_graduation`, `jiu_jitsu_belt`, `jiu_jitsu_stripes`, `martial_art_started_at`, `martial_art_last_graduation_at`, `previous_academy` |
| Relationship | `person_type`, `class_groups`, `is_active` |
| Address | `postal_code`, `address`, `address_number`, `address_complement`, `address_neighborhood`, `city` |
| Payout (only for `can_manage_people`) | `payroll_enabled`, `payroll_payment_day`, `payroll_fixed_monthly`, `payroll_per_student_amount`, `payroll_student_percentage`, `payroll_per_class_amount` |

---

## Visual hierarchy

- Reading pattern: **F Pattern** (the list) / **Z Pattern** (the form and the detail)
- Topbar: the same as the home — sticky, 56px tall, logo + actions
- Module eyebrow: `--muted`, 0.6875rem, uppercase, `letter-spacing: 0.09em`
- Screen title: weight 800, `--text`, 1.625rem mobile / 2rem desktop
- Section title (field groups): weight 700, `--muted`, 0.6875rem, uppercase
- Person name (card): weight 700, `--text`, 0.9375rem
- Detail / meta: weight 400, `--muted`, 0.8125rem
- Type badge: by role semantics (student=info, instructor=success, admin=warning, etc.)
- Status badge: active=success, inactive=neutral, no access=warning
- Primary action (button): weight 600, `--brand-red` background, 0.875rem
- Secondary action (link): weight 500, `--border` border, 0.8125rem
- KPI number: weight 800, `--text`, 1.375rem
- KPI label: weight 500, `--muted`, 0.75rem

---

## Wireframe

### Screen: People list (`person_list.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐
│ ← LV JIU JITSU                                           ☀  ⎋              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── PAGE HEADER ──────────────────────────────────────────────────────────────┐
│ PEOPLE                                                                       │
│ Registered people                               [+ New person  btn-primary]  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── KPIs ─────────────────────────────────────────────────────────────────────┐
│  45 Students │  4 Instructors │  2 Back office │  48 Active │  3 Inactive │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── FILTERS (collapsible on mobile) ─────────────────────────────────────────┐
│ [Name ________] [CPF _________] [Category ▾] [Class ▾] [Schedule ▾] [Filter]│
└──────────────────────────────────────────────────────────────────────────────┘

┌─── PEOPLE LIST ──────────────────────────────────────────────────────────────┐
│ ┌─ Card ─────────────────────────────────────────────────────────────────┐   │
│ │ João da Silva                             [STUDENT] [ACTIVE] [Detail]│   │
│ │ Adult · Fundamentals Class  ·  Mon · 19:00  Wed · 19:00              │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│ ┌─ Card ─────────────────────────────────────────────────────────────────┐   │
│ │ Maria Souza                           [STUDENT] [NO ACCESS] [Detail]│  │
│ │ Kids · Children's Class  ·  Tue · 10:00                              │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│  ...                                                                          │
│ [Empty state: No person found with the applied filters.]                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Screen: Person detail (`person_detail.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐

┌─── HEADER ────────────────────────────────────────────────────────────────── ┐
│ ← People                                                                     │
│ João da Silva                       [STUDENT] [ACTIVE] [Edit] [Delete]    │
│ CPF 123.456.789-00  ·  email@email.com  ·  (11) 99999-9999                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── PERSONAL DATA ────────────────────────────────────────────────────────── ┐
│ Birth date · Sex · Blood type · IBJJF category                          │
│ Emergency contact · Allergies · Previous injuries                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── CLASSES ────────────────────────────────────────────────────────────────── ┐
│ (when show_student_context) Enrolled classes + schedules                   │
│ (when show_teacher_context) Classes taught                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── GRADUATION ─────────────────────────────────────────────────────────────── ┐
│ Belt SVG visual + name + degree                                             │
│ Progress bar + count of completed / required classes                       │
│ Blockers, if any (minimum time, minimum attendance)                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── TUITION (can_manage_people only) ───────────────────────────────── ┐
│ Active plan + status + due date                                             │
│ Invoice history (the last 10)                                               │
│ Pending orders                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Screen: Form (`person_form.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐

┌─── HEADER ────────────────────────────────────────────────────────────────── ┐
│ ← People                                                                     │
│ New person  |  Edit João da Silva                                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── GROUP: Identification ──────────────────────────────────────────────────── ┐
│ Full name*  CPF*  Email  Phone  Birth date  Sex                              │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GROUP: Health ──────────────────────────────────────────────────────────── ┐
│ Blood type  Emergency contact  Allergies  Previous injuries                  │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GROUP: Martial art ───────────────────────────────────────────────────── ┐
│ Practiced martial art? → (conditional) Art + belt + degrees + start date  │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GROUP: Relationship ────────────────────────────────────────────────────────── ┐
│ Relationship type  Allowed classes  Active                                  │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GROUP: Address ───────────────────────────────────────────────────────── ┐
│ Postal code  Street  Number  Complement  Neighborhood  City                  │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GROUP: Payout (can_manage_people only) ────────────────────────────── ┐
│ Payout active  Payment day  Monthly fixed  Per student  % per student  Per class │
└──────────────────────────────────────────────────────────────────────────────┘

                               [Cancel]  [Save person  btn-primary]
```

---

## State machines

### Person card (list)

| State | Visual |
|---|---|
| Active with portal | Name + `ALUNO|PROFESSOR|etc` (`STUDENT|INSTRUCTOR|etc.`) badges + `ATIVO` (`ACTIVE`) + classes |
| Active without portal | Name + badges + `SEM ACESSO` (`NO ACCESS`) (badge--warning) + classes |
| Inactive | Name + badges + `INATIVO` (`INACTIVE`) (badge--neutral) + classes in muted |
| No type | Name + badge--neutral `Sem tipo` (`No type`) |

### Person type badge

| Type | Color |
|---|---|
| student / dependent | `badge--info` |
| guardian | `badge--neutral` |
| instructor | `badge--success` |
| administrative-assistant | `badge--warning` |

### Graduation section (detail)

| State | Visual |
|---|---|
| No data | An empty state with the text `Sem dados de graduação` (`No graduation data`) |
| With a belt, no progress | Belt SVG + name + degree |
| With a belt and progress | Belt SVG + bar + counted classes + blockers |
| Eligible for graduation | Highlighted in `--success` |

### Conditional field (form)

| `has_martial_art` | Visual |
|---|---|
| Not selected | The martial art fields hidden (`[hidden]`) |
| `Sim` (`Yes`) | The martial art fields visible through JavaScript (`hidden` removed) |
| `Não` (`No`) | The fields hidden, the values cleared |

---

## Functional requirements

| # | Requirement |
|---|---|
| FR-01 | `GET /pessoas/` lists people with a filter by name, CPF, category, class, and schedule |
| FR-02 | The count KPIs rendered at the top of the list |
| FR-03 | Each card shows: the name, type, portal status, and active classes/schedules |
| FR-04 | `GET /pessoas/<pk>/` shows the person's complete detail |
| FR-05 | The detail shows the SVG belt with its color, tip, and degrees using the dashboard's pattern |
| FR-06 | The detail shows the graduation progress with blockers (minimum time, minimum attendance) |
| FR-07 | The detail shows the tuition and invoice history (only for `can_manage_people`) |
| FR-08 | `GET /pessoas/nova/` and `GET /pessoas/<pk>/editar/` show the grouped form |
| FR-09 | The martial art fields are conditionally visible through plain JavaScript |
| FR-10 | `GET /pessoas/<pk>/excluir/` shows a confirmation before deleting |
| FR-11 | The home's `Pessoas` (`People`) quick-link points to `system:person-list` |
| FR-12 | The `Editar` (`Edit`) button in the detail leads to `system:person-update` (only for `can_manage_people`) |

## Non-functional requirements

| # | Requirement |
|---|---|
| NFR-01 | Light and dark themes mandatory — the `dashboard.css` CSS tokens |
| NFR-02 | Mobile-first, responsive: the list in a single column (mobile) / 2 columns (desktop) |
| NFR-03 | No pagination in the MVP — the complete list; an issue is open for pagination later |
| NFR-04 | The KPIs make no extra queries — computed from the already-loaded `people` |
| NFR-05 | N+1 prevented — `get_person_queryset` with `select_related` and `prefetch_related` |
| NFR-06 | CSS separated per module: `static/system/css/people/people.css` |
| NFR-07 | JavaScript only for the conditional `has_martial_art` field — inline in the template |

---

## Scope

- `system/urls.py` — 5 new routes
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/people/people.css`
- `templates/home/dashboard.html` — update the `Pessoas` (`People`) quick-link

## Out of scope

- Pagination of the list
- Real-time / AJAX search
- CSV export
- Profile photo upload
- Managing family relationships (create/remove) — a future dedicated screen
- Managing enrollments through this screen — it uses the classes module
- The PersonType module — it exists but is not part of this PRD

---

## Impacted files

| File | Action |
|---|---|
| `system/urls.py` | Add 5 routes + import the views from `person_views.py` |
| `templates/people/person_list.html` | Create (a new folder in templates/) |
| `templates/people/person_detail.html` | Create |
| `templates/people/person_form.html` | Create |
| `templates/people/person_confirm_delete.html` | Create |
| `static/system/css/people/people.css` | Create (a new folder in static/system/css/) |
| `templates/home/dashboard.html` | Update the href of the People quick-link (already at `?v=5`) |

---

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| A person with no `person_type` | The template uses `person.person_type.display_name\|default:"Sem tipo"` |
| A person with no classes | The classes section shows a compact empty state |
| A person with no graduation data | `graduation_progress` may be `None` — the template guards it with `{% if %}` |
| A `billing_owner` different from the person | The detail indicates who the financial guardian is |
| `has_martial_art` in the edit form | The form fills `initial` correctly; the JavaScript reads the current value on load |
| The instructor sees the list but cannot edit | The `Editar` (`Edit`) button is conditioned on `can_manage_people` |
| A very long list (with no pagination) | Accepted in the MVP; `get_person_queryset` uses `.distinct()` correctly |

---

## Rules and constraints

- SDD before code
- TDD: view tests for the list and detail GETs
- No migrations — no model change
- No hardcoding
- No `except: pass`
- Full reading of the context files before implementing
- Mandatory visual validation: desktop + mobile, light + dark themes
- CSS bump: not applicable to `dashboard.css` (the quick-link does not change CSS); the new `people.css` starts at `?v=1`
- Creating the `templates/people/` and `static/system/css/people/` folders is necessary and justified by the paths of the existing views

---

## Plan

- [ ] 1. Register the routes in `system/urls.py`
- [ ] 2. Create `static/system/css/people/people.css` with tokens and components
- [ ] 3. Create `templates/people/person_list.html`
- [ ] 4. Create `templates/people/person_detail.html`
- [ ] 5. Create `templates/people/person_form.html`
- [ ] 6. Create `templates/people/person_confirm_delete.html`
- [ ] 7. Update the `Pessoas` (`People`) quick-link on the home
- [ ] 8. Tests: the list GET, the detail GET, the form GET, permissions
- [ ] 9. Visual validation: desktop + mobile, light + dark, a clean console
- [ ] 10. `manage.py check` + `manage.py test --verbosity 2`
- [ ] 11. `manage.py collectstatic --noinput`
- [ ] 12. Final cleanup and documentation update

---

## Acceptance criteria

- [ ] `GET /pessoas/` returns 200 for a logged-in admin (verifiable: browser)
- [ ] `GET /pessoas/` redirects to login for an unauthenticated user (verifiable: browser)
- [ ] The name, CPF, category, class, and schedule filters narrow the list (verifiable: browser)
- [ ] The KPIs add up correctly (verifiable: an ORM shell + visual inspection)
- [ ] Each card shows the name, a type badge, and the portal status (verifiable: visual inspection)
- [ ] `GET /pessoas/<pk>/` returns 200 and shows the person's data (verifiable: browser)
- [ ] The detail shows the SVG belt with the correct `BeltRank` colors (verifiable: visual inspection)
- [ ] The detail shows the graduation progress with `progress_pct`, `approved_classes_in_window`, `required_classes` (verifiable: shell + visual)
- [ ] The tuition section appears only for `can_manage_people` (verifiable: the browser with two profiles)
- [ ] The form groups fields by section with a visual separator (verifiable: visual inspection)
- [ ] The martial art field is hidden when `Não` (`No`) / shown when `Sim` (`Yes`) (verifiable: JavaScript interaction)
- [ ] The light and dark themes work on all 4 screens (verifiable: the toggle + inspection)
- [ ] Mobile 375px: no horizontal overflow on any screen (verifiable: DevTools)
- [ ] The browser console has no critical JavaScript errors (verifiable: DevTools)
- [ ] `manage.py test --verbosity 2` — 0 failures, 0 errors
- [ ] `manage.py check` — 0 issues
- [ ] Visual hierarchy: titles at weight 700–800, labels at 500, hints in `--muted` (verifiable: inspection)

---

## Visual validation

### Desktop
- List: the KPIs in a row, cards in 2 columns, the filters in a line
- Detail: the SVG belt full-width up to max-width, sections stacked with separators
- Form: groups in a card, the label above the field, the buttons on the right

### Mobile (375px)
- List: 1 column, the KPIs in a 2×3 grid, the filters collapsed
- Detail: stacked sections, a responsive SVG belt
- Form: fields in a single column, full-width buttons

### Browser console
- No critical JavaScript errors
- No static 404s

### Terminal
- No unhandled stack trace

---

## ORM validation

### Shell checks

```python
# Confirm that the list does not produce N+1 queries
from system.selectors import get_person_queryset
from django.test.utils import override_settings
qs = get_person_queryset()
list(qs)  # should execute prefetched queries with no N+1

# Confirm graduation
from system.services.graduation import compute_graduation_progress
from system.models import Person
p = Person.objects.first()
gp = compute_graduation_progress(p)
print(gp.progress_pct, gp.approved_classes_in_window, gp.required_classes)
```

---

## Evidence

- `manage.py check` — 0 issues
- `manage.py test --verbosity 2` — 168 tests, OK
- `manage.py collectstatic --noinput` — 1 file copied, 173 unmodified
- The `/pessoas/` list — 200, the KPIs rendered, cards with the correct badges (dark + light)
- The `/pessoas/7/` detail — 200, the correct Coral belt SVG, the `NA FAIXA`/`AULAS APROVADAS` (`AT THE BELT`/`APPROVED CLASSES`) stats, a blocker, the history, the martial art, the tuition (admin)
- The `/pessoas/nova/` form — 200, the field groups, the conditional martial art field working (`Sim` — `Yes` → the fields appear)
- Mobile 375px — no horizontal overflow in the list or the detail
- Console — no application JavaScript errors (Chrome extension errors at line 0:0 — ignored)
- The `Pessoas` (`People`) quick-link on the home points to `system:person-list`

## Implemented

1. `system/urls.py` — 5 new routes registered + imports of `PersonListView`, `PersonCreateView`, `PersonDetailView`, `PersonUpdateView`, `PersonDeleteView`
2. `system/views/person_views.py` — `_compute_belt_stripes(graduation_progress)` added and called in `PersonDetailView.get_context_data` → `context["belt_stripes_detail"]`
3. `static/system/css/people/people.css` — created (v1) with light/dark tokens, the topbar, KPIs, filters, list cards, the detail, graduation, the form, and the delete confirmation
4. `templates/people/person_list.html` — created: the topbar, KPIs, filters, the people list with badges and classes, the empty state, and the theme toggle
5. `templates/people/person_detail.html` — created: a header with badges/contact/actions, personal data, address, classes, the belt SVG + graduation stats + blockers + history, martial art, and tuition (admin-only)
6. `templates/people/person_form.html` — created: the Identification, Health, Martial Art (conditional JavaScript), Relationship, Address, and Payout (can_manage_people) groups; Cancel/Save buttons
7. `templates/people/person_confirm_delete.html` — created: a trash icon, a confirmation with the name, and Cancel/Delete actions
8. `templates/home/dashboard.html` — the `Pessoas` (`People`) quick-link updated from `<span disabled>` to `<a href="{% url 'system:person-list' %}">`

## Deviations from plan

- `_compute_belt_stripes` was added in `person_views.py` (it was not in the original plan, but it is necessary because Django templates do not support calling methods with arguments — the same pattern as `home_views.py`)
- Creating the `templates/people/` and `static/system/css/people/` folders was necessary and justified by the paths already defined in the views; accepted per this PRD

## Pending

- None
