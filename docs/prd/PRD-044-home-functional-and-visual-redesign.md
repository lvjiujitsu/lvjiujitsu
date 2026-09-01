# PRD-044: Home — functional and visual redesign

> A complete review of the `/home/` screen based on the mapping of the legacy system (May/2026).
> PRD-043 consolidated the 4 routes into one. This PRD defines what must be displayed,
> how it must behave, and how it must look — with visual quality consistent
> with the `register.html` / `register.css` standard.

---

## Summary of the implementation

A complete redesign of `templates/home/dashboard.html` and `static/system/css/home/dashboard.css`, fixing field bugs, adding the missing components (the belt visual, a plan card with a real status, a `Trocar plano` (`Change plan`) button, attendance history, SVG icons), and raising the visual quality to the registration wizard's standard — clean, minimalist, functional, and not looking like a generic template.

---

## Demand type

UI redesign + bug fixes + implementation of missing features

---

## Current problem

### Critical bugs (wrong fields in the template)
| Field used | Correct field in the service | Impact |
|---|---|---|
| `graduation_progress.percentage` | `graduation_progress.progress_pct` | The graduation bar is always at 0% |
| `graduation_progress.current_belt_display` | `graduation_progress.current_belt_rank.display_name` | The belt name never appears |
| `graduation_progress.classes_count` | `graduation_progress.approved_classes_in_window` | The class count never appears |

### Features missing vs. the legacy system
- No belt visual (an SVG belt with colors and degrees)
- The tuition section does not show the real status (`active_membership.status`)
- No `Trocar plano` (`Change plan`) button for students with an active plan
- No notice of a different financial guardian (`billing_owner`)
- The attendance history (`attendance_history`) is never rendered
- No check-in button for the student
- The quick-link icons are emoji — informal and inconsistent with the visual standard

### Design problem
- A generic "AI dashboard template" look — with no identity
- Correct tokens, but shadows, transitions, and composition below the `register.css` standard
- Emoji in the quick-links contradict the SVG icon standard of `register.html`
- The graduation section is mapped but never displays anything (the wrong field)

---

## Goal

1. Fix the 3 field bugs from the graduation service.
2. Implement an inline SVG belt visual with the belt's colors and degrees.
3. Implement a tuition card with the real status, amount, and a `Trocar plano` (`Change plan`) button.
4. Implement a compact attendance history (the last 5 entries).
5. Implement a check-in button for the student (a POST with `schedule_id` or `special_id`).
6. Replace the quick-link emoji with inline SVG icons consistent with `register.html`.
7. Add real routes to the quick access shortcuts (staff).
8. Raise the CSS to the `register.css` quality standard: double shadows, transitions, and a strict typographic hierarchy.

---

## Context Ledger

### Files read in full
- `templates/home/dashboard.html` — the current template (the post-PRD-043 version)
- `static/system/css/home/dashboard.css` — the current CSS
- `templates/login/register.html` — the visual pattern and component reference
- `static/system/css/auth/register.css` — the CSS quality reference
- `system/views/home_views.py` — the view and its complete context
- `system/services/graduation.py` — the real fields of `compute_graduation_progress`
- `system/models/graduation.py` — `BeltRank`: `color_hex`, `tip_color_hex`, `stripe_color_hex`, `get_grade_slots()`
- `system/models/membership.py` — `MembershipStatus`, the `Membership` fields
- `docs/UI-SCREEN-CONTRACT.md` — tokens, breakpoints, roles, UX principles
- `AGENTS.md` and `CLAUDE.md` — the work protocols

### Adjacent files consulted
- `system/services/class_calendar.py` — the structure of `get_today_classes_for_person`, `get_student_checkin_history`
- `system/urls.py` — the real routes available (to fill in the quick-links' `href`)
- The legacy `C:\Users\whsf\Downloads\lvjiujitsu-b37d45f1576e928d3f8a2be67ea05579ee696c48\` — a mapping of the existing features

### MCPs verified
- The Django preview server at `http://127.0.0.1:8000` — active
- `manage.py check` — 0 issues (before the implementation)
- `manage.py test --verbosity 2` — 165 tests OK (before the implementation)

---

## Product decisions — what stays on the home

### Everything inline (rendered directly on the home)
| Block | Profiles | Data |
|---|---|---|
| Greeting + date | all | `today_weekday`, `today_date`, the user's name |
| Belt visual + progress | student, instructor, admin | `graduation_progress` |
| Today's classes | all | `today_classes` |
| Check-in (a button per class) | student | `schedule_id` / `special_id` |
| Tuition card + status | student | `active_membership`, `pending_order`, `active_trial_access` |
| Attendance history (the last 5) | student, instructor | `attendance_history[:5]` |
| Quick access — a grid of links | admin, back office | real URLs through `{% url %}` |
| Financial summary (a stub) | admin, back office | a placeholder until the financial module exists |

### Navigates to another screen (a button/link — not a popup)
| Action | Profile | Route |
|---|---|---|
| `Trocar plano` (`Change plan`) | student (active plan) | `system:plan-change-select` |
| `Ir para pagamento` (`Go to payment`) | student (pending) | `system:payment-checkout` |
| `Ver cronograma` (`View schedule`) | student | `system:student-schedule` |
| `Ver financeiro` (`View finances`) | instructor | `system:teacher-financial` |
| `Ver loja` (`View shop`) | student, instructor | `system:product-store` |
| `Ver módulo financeiro` (`View financial module`) | admin, back office | `system:financial-control` |
| `Django Admin` | technical admin | `/admin/` |

### Not on the home (it belongs to a dedicated module)
- Creating an open class — the instructor uses the calendar (`system:instructor-calendar`)
- Approving students' check-ins — the instructor's calendar screen
- The complete invoice history — the financial module
- Editing plans / rules — the plans module
- Registering people — the people module

### No popups
The home is a **summary and launch panel**. Every destructive or complex action happens on a dedicated page. No modal or popup will be implemented on this screen.

---

## Visual hierarchy

- Reading pattern: **F Pattern** — critical information at the top, actions on the right
- Font: `system-ui` (inherited from the body)
- `h1` (greeting): weight 800, `--text`, 1.625rem mobile / 2rem desktop
- Eyebrow (date): weight 500, `--muted`, 0.75rem, uppercase, `letter-spacing: 0.07em`
- Section title: weight 700, `--muted`, 0.6875rem, uppercase, `letter-spacing: 0.08em`
- Plan / class name: weight 700, `--text`, 1rem
- Card detail / subtitle: weight 400, `--muted`, 0.8125rem
- Status badge: weight 700, a semantic color, 0.6875rem, uppercase, `letter-spacing: 0.02em`
- Primary action (button): weight 600, `--brand-red` background, 0.875rem
- Secondary action (link): weight 500, `--brand-red` color, 0.8125rem

---

## New or redesigned components

### 1. Belt visual (belt-visual)

Inline SVG in the Django template. Generated server-side with the `BeltRank` data.

```
Visual structure:
┌─────────────────────────────┬──────────────────┐
│  BELT BODY (color_hex)      │  TIP             │
│                             │ ████████         │
│                             │ (tip_color_hex)  │
│                             │ with degree      │
│                             │ stripes          │
│                             │ (grade_slots in  │
│                             │ stripe_color)    │
└─────────────────────────────┴──────────────────┘
```

Size: 100% width, max-width: 280px, height: 28px (mobile) / 36px (desktop).
Responsive through CSS. Border radius: 4px.
Stripes: vertical rectangles on the tip; `get_grade_slots(grade_number)` returns `[bool, bool, bool, bool]`.

Django template:
```html
{% with belt=graduation_progress.current_belt_rank grade=graduation_progress.current_grade_number %}
{% if belt %}
<div class="belt-visual" aria-label="{{ belt.display_name }}{% if grade %}, {{ grade }} grau{{ grade|pluralize }}{% endif %}">
  <svg ...>
    <!-- body -->
    <rect x="0" y="0" width="72%" height="100%" fill="{{ belt.color_hex }}" rx="4"/>
    <!-- tip -->
    <rect x="72%" y="0" width="28%" height="100%" fill="{{ belt.tip_color_hex }}" rx="0 4 4 0"/>
    <!-- degree stripes -->
    {% for filled in belt.get_grade_slots(grade) %}
    {% if filled %}
    <rect x="..." ... fill="{{ belt.stripe_color_hex }}"/>
    {% endif %}
    {% endfor %}
  </svg>
  <span class="belt-visual__label">{{ belt.display_name }}{% if grade %} · {{ grade }}º grau{% endif %}</span>
</div>
{% endif %}
{% endwith %}
```

> **Implementation note:** `get_grade_slots()` is a model method. Call it in the template through `{% with slots=graduation_progress.current_belt_rank.get_grade_slots graduation_progress.current_grade_number %}` — check whether `with` supports a call with an argument; if not, enrich the view's context with `belt_grade_slots = belt_rank.get_grade_slots(grade_number)`.

### 2. Tuition card (billing-card) — redesigned

Layout (per tab/person):

```
┌─────────────────────────────────────────────────────────────────┐
│ [STATUS badge]                                      [plan name] │
│ Due date: DD/MM/YYYY    R$ 00.00/month                          │
│                                                                   │
│ [Button: "Change plan" — secondary]  [Button: "Pay" — primary] │
└─────────────────────────────────────────────────────────────────┘
```

The states and their visuals:

| State | Badge | Badge color | Primary button | Secondary button |
|---|---|---|---|---|
| `active` | `Ativo` (`Active`) | `--success` | — | `Trocar plano` (`Change plan`) |
| `past_due` | `Em atraso` (`Overdue`) | `--danger` | `Pagar agora` (`Pay now`) | `Trocar plano` (`Change plan`) |
| `pending` (no membership, with pending_order) | `Pendente` (`Pending`) | `--warning` | `Ir para pagamento` (`Go to payment`) | — |
| `trial` | `Experimental` (`Trial`) | `--info` | — | — |
| `sem_plano` | `Sem plano` (`No plan`) | `--muted` | — | — |
| `exempted` | `Isento` (`Exempt`) | `--success` | — | — |
| `canceled` | `Cancelado` (`Cancelled`) | `--muted` | — | — |

Notice of a different financial guardian:
```html
<!-- Exact Brazilian Portuguese UI copy; English: "Tuition linked to guardian ..." -->
{% if tab.billing_owner and tab.billing_owner != tab.person %}
<p class="billing-card__owner-note">
  Mensalidade vinculada ao responsável {{ tab.billing_owner.full_name }}.
</p>
{% endif %}
```

### 3. Today's classes list — with check-in (student)

Each list item:

```
┌──────────────────────────────────────────────────────────────────┐
│ 18:30  •  Adult · Gi             Prof. Wagner          [Check-in] │
│         Fundamentals Class                                      │
└──────────────────────────────────────────────────────────────────┘
```

- The time in `--brand-red`, weight 700
- The separator dot (·) in `--muted`
- The class name in `--text`, weight 600
- The instructor in `--muted`, weight 400
- Check-in button: `btn--sm btn--secondary` → an AJAX POST to `system:student-checkin`
- After a successful check-in: replace the button with an `Aguardando aprovação` (`Awaiting approval`) pill (`--warning`)
- If the check-in is already approved: a `Confirmado` (`Confirmed`) pill (`--success`)
- If the class is cancelled: strike through the time + a `Cancelada` (`Cancelled`) badge (`--muted`)

### 4. SVG icons — quick-links

Replace the emoji with inline SVG icons. Style: `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`, `width="18" height="18"`. The same language as `register.html`.

| Module | SVG icon |
|---|---|
| People | `<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>` |
| Classes | `<path d="M17 21v-2a4 4 0 0 0-4-4H5..."/><circle cx="9" cy="7" r="4"/>...` |
| Finance | `<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>` |
| Graduation | `<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>` |
| Materials | `<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/>` |
| Plans | `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12..."/><polyline points="14 2 14 8 20 8"/>` |
| Django Admin | `<circle cx="12" cy="12" r="3"/><path d="M19.07 4.93..."/>` (settings) |
| Schedules | `<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>` |

### 5. Attendance history (compact)

Shown for the student and the instructor. At most 5 entries. A `Ver mais` (`See more`) link navigates to the module (future).

```
ATTENDANCE HISTORY
────────────────────────────────────────────────────
May 20 · 18:30   Fundamentals Class · Prof. Wagner   ✓ Confirmed
May 17 · 18:30   Fundamentals Class · Prof. Wagner   ✓ Confirmed
...
────────────────────────────────────────────────────
[See full history →]
```

---

## CSS — the quality standard to follow

### Shadows (the `register.css` standard)
```css
--card-shadow: 0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.05);
--card-shadow-dark: 0 1px 6px rgba(0,0,0,.4), 0 4px 20px rgba(0,0,0,.3);
```

### Borders
```css
border: 1.5px solid var(--border);
border-radius: 0.875rem; /* panels */
border-radius: 0.75rem;  /* smaller cards */
border-radius: 8px;      /* buttons */
```

### Card hover with a ring (the `register.css` profile-card standard)
```css
.quick-link:hover {
  border-color: var(--brand-red);
  box-shadow: 0 0 0 3px var(--brand-red-muted), var(--card-shadow);
}
```

### Transitions
```css
transition: border-color 0.15s, box-shadow 0.15s, background 0.15s, transform 0.12s;
```

### Entrance animation per section
```css
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.section { animation: fadeSlideIn 0.35s ease both; }
.section:nth-child(2) { animation-delay: 0.05s; }
/* etc. */
```

### Subtle background (the `register.css` standard)
```css
body {
  background-image:
    radial-gradient(ellipse 60% 50% at 110% 110%, rgba(196,18,48,.05) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at -10% -10%, rgba(196,18,48,.02) 0%, transparent 60%);
}
html[data-theme="dark"] body {
  background-image:
    radial-gradient(ellipse 70% 55% at 100% 100%, rgba(196,18,48,.14) 0%, transparent 65%),
    radial-gradient(ellipse 50% 45% at 0% 0%, rgba(196,18,48,.06) 0%, transparent 60%);
}
```

### Theme-aware logo
```css
.topbar__logo { filter: none; transition: filter 0.2s; }
html[data-theme="dark"] .topbar__logo { filter: invert(1); }
```

---

## JavaScript — inline behavior

The home's JavaScript must be **minimal and declarative**. Follow the `register.html` pattern:

- Server data through `<script type="application/json" id="page-data">` — never in `data-*` with JSON objects
- Theme: a simple toggle (already implemented)
- Billing tabs: a simple toggle (already implemented)
- **Check-in (new)**: an AJAX POST with `fetch()` and the CSRF token from the input or the cookie; it updates only the affected button (with no reload)
- Zero external dependencies — plain vanilla JavaScript
- Protected with an IIFE `(function() { ... })()`
- Never use `innerHTML` with user data — use `textContent` and element creation

### The student check-in flow
```
click "Check-in"
→ btn.disabled = true, btn.textContent = "Aguardando…" ("Waiting…")
→ fetch POST /aulas/checkin/ { schedule_id }
→ success: replace the button with the "Aguardando aprovação" ("Awaiting approval") pill (`--warning` badge)
→ error: btn.disabled = false, btn.textContent = "Check-in"; display an inline error message
```

---

## Wireframe per profile

### Student / Guardian / Dependent
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Friday, May 23, 2026
Hello, Lucas 👋

GRADUATION
┌──────────────────────────────────────────────────────┐
│ [████████████████████░░░░░░░░░]  White Belt · 2nd   │
│ [SVG belt with real colors]                         │
│ 24 of 40 required classes · 60%                   │
└──────────────────────────────────────────────────────┘

TUITION
┌──────────────────────────────────────────────────────┐
│ [ACTIVE]       Monthly Individual Plan                │
│ Due date: 06/15/2026    R$ 150.00/month              │
│                                           [Change plan →] │
└──────────────────────────────────────────────────────┘

TODAY'S CLASSES
┌──────────────────────────────────────────────────────┐
│ 18:30  ·  Fundamentals · Gi  Prof. Wagner  [Check-in] │
│ 20:00  ·  Advanced · Gi       Prof. Wagner  [Confirmed] │
└──────────────────────────────────────────────────────┘

RECENT ATTENDANCE
┌──────────────────────────────────────────────────────┐
│ May 20 · 18:30   Fundamentals · Gi   ✓ Confirmed   │
│ May 17 · 18:30   Fundamentals · Gi   ✓ Confirmed   │
│                                    [View history →] │
└──────────────────────────────────────────────────────┘
```

### Admin / Back office
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Friday, May 23, 2026
Hello, Wagner 👋

QUICK ACCESS
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│[svg]    │ │[svg]    │ │[svg]    │ │[svg]    │
│People   │ │Classes  │ │Finance   │ │Graduation│
└─────────┘ └─────────┘ └─────────┘ └─────────┘
┌─────────┐ ┌─────────┐ ┌─────────┐
│[svg]    │ │[svg]    │ │[svg]    │
│Materials│ │Plans    │ │Admin    │ ← technical admin only
└─────────┘ └─────────┘ └─────────┘

TODAY'S CLASSES
(same component — compact list)

FINANCE
┌──────────────────────────────────────────────────────┐
│ 💰  Financial module coming soon.      [View module →] │
└──────────────────────────────────────────────────────┘
```

### Instructor
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Friday, May 23, 2026
Hello, Professor Wagner 👋

GRADUATION
(same component — belt + progress bar)

TODAY'S CLASSES
┌──────────────────────────────────────────────────────┐
│ 18:30  ·  Fundamentals · Gi                          │
│ 3 confirmed check-ins · 1 awaiting approval            │
│                              [View schedule →]         │
│ 20:00  ·  Advanced · Gi                              │
│ 5 confirmed check-ins                                │
└──────────────────────────────────────────────────────┘

RECENT ATTENDANCE
(the last 5 classes with total attendance)
```

---

## Functional requirements

### FR-01 — Graduation field fixes
- `graduation_progress.progress_pct` (not `percentage`)
- `graduation_progress.current_belt_rank.display_name` (not `current_belt_display`)
- `graduation_progress.approved_classes_in_window` (not `classes_count`)
- The section only renders when `graduation_progress is not None` and `graduation_progress.current_belt_rank is not None`

### FR-02 — SVG belt
- Rendered server-side through the Django template with the `BeltRank` data
- Proportion: 3:1 (body: 72%, tip: 28%)
- Colors: `belt.color_hex` (body), `belt.tip_color_hex` (tip), `belt.stripe_color_hex` (stripes)
- Stripes: `belt.get_grade_slots(current_grade_number)` → a list of booleans
- No external library — plain inline SVG
- Fallback when `belt` is None: the component is not rendered (with no error)

### FR-03 — Tuition card
- Displays: the plan name, status (badge), the monthly amount (`plan.price`), the due date (`next_billing_date`)
- The `Trocar plano` (`Change plan`) button: visible when `active_membership.status in ('active', 'exempted')`
- The `Pagar agora` (`Pay now`) button: visible when `active_membership.status == 'past_due'` or `pending_order is not None`
- The guardian notice: visible when `billing_owner and billing_owner != person`
- Tabs per dependent: when `billing_tabs|length > 1`

### FR-04 — Check-in (student)
- A `Check-in` button per class with no check-in
- An AJAX POST to `system:student-checkin` with `schedule_id`, or `system:student-special-checkin` with `special_id`
- The CSRF token through `document.cookie` or a hidden `{% csrf_token %}` input embedded inline
- Button states: `default` → `loading` (disabled + `Aguardando…` — `Waiting…`) → `pill-pending` | `error`
- No page reload
- If the check-in is already approved: a green `Confirmado` (`Confirmed`) pill
- If the check-in is pending (already made): a yellow `Aguardando aprovação` (`Awaiting approval`) pill

### FR-05 — Attendance history
- At most 5 entries from `attendance_history`
- Shown for the student and the instructor
- Each entry: date, time, class name, category, status
- A `Ver histórico completo` (`See full history`) link → a future route (it may be disabled while the module does not exist: `href="#"`)
- If `attendance_history` is empty: do not render the section

### FR-06 — Quick access shortcuts with real routes
| Link | Django route |
|---|---|
| People | `system:person-list` |
| Classes | `system:class-group-list` |
| Schedules | `system:class-schedule-list` |
| Finance | `system:financial-control` |
| Graduation | *(the route is pending — href="#" for now)* |
| Materials | `system:product-list` |
| Plans | `system:plan-list` |
| Django Admin | `/admin/` |

### FR-07 — Django messages
- Render `{% if messages %}` with a visual component per tag: error, success, warning, info
- An info/alert SVG icon before the text
- The block positioned after the topbar, before the header

### FR-08 — Asset cache version
- When changing `dashboard.css`, update `?v=N` in the template (`?v=3` in the next delivery)
- When extracting the JavaScript into a separate file: update the corresponding `?v=`

---

## Non-functional requirements

### NFR-01 — Performance
- Zero external JavaScript libraries
- Zero images beyond the logo (inline SVG for everything)
- CSS compiled into a single file, with no chained imports
- No N+1 query: `select_related()` / `prefetch_related()` where necessary in the view

### NFR-02 — Accessibility
- Every interactive button with a descriptive `aria-label`
- `role="status"` on the empty states
- `role="alert"` on errors and system messages
- `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on the graduation bar
- `role="tablist"` / `role="tab"` / `role="tabpanel"` on the dependent tabs
- `:focus-visible` on every interactive element with a visible `outline`
- Minimum touch target: 44×44px (WCAG 2.5.8)
- The SVG belt with a descriptive `aria-label` (belt name + degree)

### NFR-03 — Responsiveness
- Mobile-first, a single column below 640px
- Quick-access: 2 columns on mobile, 3 on tablet, 4 on desktop
- Classes: always a vertical list
- Tuition: a full-width card, with the badge aligned right
- The SVG belt: `max-width: 280px`, centered on mobile

### NFR-04 — Light and dark themes
- Every color through a CSS token — zero hardcoding
- The logo: `filter: invert(1)` in dark mode (the `register.css` standard)
- `color-scheme: light` / `dark` defined on the `html`
- The SVG belt uses `fill="{{ belt.color_hex }}"` — the belt's real colors, with no token (correct: they are the belt's colors, not the UI's)

### NFR-05 — Security
- `innerHTML` forbidden — use `textContent` or DOM element creation
- CSRF on every POST (the `X-CSRFToken` header through fetch)
- User data never in `eval()` or interpolated into a JavaScript string

### NFR-06 — Maintainability
- CSS with tokens, no stray colors
- Template sections clearly commented with `{# ─── ... ─── #}`
- Minimal JavaScript — prefer server-side rendering over client-side logic
- No CSS class created as an exception — only extensions of the defined patterns

---

## Scope

- `templates/home/dashboard.html` — rewrite
- `static/system/css/home/dashboard.css` — rewrite
- `system/views/home_views.py` — enrich the context: `belt_grade_slots` if necessary
- `static/system/js/home/dashboard.js` — create (extract the JavaScript from the template)

---

## Out of scope

- Creating an open class through the instructor (the calendar screen)
- The instructor approving students' check-ins (the calendar screen)
- The complete financial module (a separate PRD)
- The complete graduation module (a separate PRD)
- The global sidebar/drawer (`base.html`) — a separate PRD
- Real-time notifications
- Charts or reports

---

## Impacted files

| File | Action |
|---|---|
| `templates/home/dashboard.html` | rewrite |
| `static/system/css/home/dashboard.css` | rewrite (bump `?v=3`) |
| `static/system/js/home/dashboard.js` | create (extract the JavaScript from the template) |
| `system/views/home_views.py` | enrich the context if necessary |

---

## Risks and edge cases

- **`get_grade_slots()` in the template:** a method with an argument — check whether the Django template engine supports `object.method arg`; if not, enrich the view's context with `belt_grade_slots = [...]`.
- **A technical admin with no `portal_person`:** `graduation_progress` will be `None`; the graduation section must not render.
- **Empty `billing_tabs` for admin/instructor:** the tuition section must not render.
- **`today_classes` with a different structure per profile:** the student gets `get_today_classes_for_person`, the instructor gets `get_today_classes_for_instructor` — check the fields returned by both services before using them in the template.
- **A duplicate check-in:** the backend rejects it; the frontend must handle the 400 by showing an inline message without reloading.
- **`attendance_history` with a different structure per profile:** student vs. instructor — check the fields before rendering.
- **The `system:class-group-list` route may not exist:** check in `system/urls.py` before referencing it in the template.

---

## Rules and constraints

- SDD before code — the implementation only starts after fully reading the graduation, tuition, and calendar services
- TDD — route and view context tests before implementing the template
- No hardcoded color, profile, or person type string
- No schema migration
- No `innerHTML` with user data
- `?v=` updated on every changed asset
- Full reading of `class_calendar.py` before implementing check-in and the classes
- Full reading of `membership.py` before implementing the tuition card

---

## Implementation plan

- [ ] 1. Full reading
  - [ ] `system/services/class_calendar.py` — the return structure of `get_today_classes_for_person`, `get_student_checkin_history`
  - [ ] `system/services/membership.py` — the `Membership` fields, `get_active_membership`, `get_guardian_billing_tabs`
  - [ ] `system/urls.py` — confirm the routes available for the quick-links
  - [ ] Test the `get_grade_slots()` call in the Django shell to verify template compatibility
- [ ] 2. Enrich the view's context (if necessary)
  - [ ] Add `belt_grade_slots` to the context if `get_grade_slots()` does not work in the template
  - [ ] Check that `get_today_classes_for_person` returns `schedule_id` or `special_id` for check-in
- [ ] 3. Tests (Red)
  - [ ] Test: `GET /home/` with a student with an active membership → the context has `billing_tabs[0].active_membership`
  - [ ] Test: `GET /home/` with a student with no graduation → the graduation section is absent
  - [ ] Test: `GET /home/` with an admin → `show_staff_area=True`, `billing_tabs=[]`
- [ ] 4. Implementation (Green)
  - [ ] Rewrite `dashboard.css` following the `register.css` standard
  - [ ] Rewrite `dashboard.html` with the complete components
  - [ ] Create `dashboard.js` with the AJAX check-in
  - [ ] Fix the graduation fields in the template
  - [ ] Implement the SVG belt
  - [ ] Implement the tuition card with its states
  - [ ] Implement the SVG icons in the quick-links
  - [ ] Implement the attendance history
  - [ ] Fill in the real routes in the quick-links
- [ ] 5. Refactoring
  - [ ] Check the per-section entrance animation
  - [ ] Check that no color sits outside a token
  - [ ] Check that the `aria-*` attributes are complete
- [ ] 6. Full validation
  - [ ] `manage.py check` — 0 issues
  - [ ] `manage.py test --verbosity 2` — 0 failures
  - [ ] Desktop screenshot, light theme
  - [ ] Desktop screenshot, dark theme
  - [ ] Mobile screenshot (375px), light theme
  - [ ] Mobile screenshot, dark theme
  - [ ] The browser console with no errors
  - [ ] The terminal with no stack trace
  - [ ] Validate the empty state of every section (an admin with no data)
  - [ ] Validate the state with data (a student with an active plan, a belt, and classes)
- [ ] 7. Cleanup
  - [ ] Remove the inline JavaScript from the template
  - [ ] No temporary artifacts
- [ ] 8. Documentation update
  - [ ] PRD-044 with evidence
  - [ ] `CLAUDE.md` Section 13 if there is a relevant change

---

## Acceptance criteria

### Functional
- [ ] The graduation bar shows the real percentage (`progress_pct`) — verifiable: a screenshot with a student who has a graduation
- [ ] The SVG belt renders with the correct `BeltRank` colors — verifiable: visual inspection
- [ ] The degree stripes filled in correctly per `grade_number` — verifiable: visual inspection
- [ ] The tuition card shows the plan name, a status badge, and the due date — verifiable: a screenshot
- [ ] The `Trocar plano` (`Change plan`) button visible for a student with an active plan — verifiable: a screenshot + an ORM check
- [ ] The `Pagar` (`Pay`) button visible for a student with a `pending_order` — verifiable: a screenshot
- [ ] The check-in button performs a POST with no reload and updates the status — verifiable: interaction in the browser
- [ ] The attendance history shows the last 5 entries for a student — verifiable: a screenshot
- [ ] Quick-links with SVG icons and real routes (not `href="#"`) — verifiable: clicking and inspecting
- [ ] Django messages rendered with the correct styling — verifiable: triggering a test message

### Visual
- [ ] Typographic hierarchy: the greeting at 800, sections at 700 muted uppercase, cards at 700, details at 400 muted
- [ ] Double shadows on the panels (not `box-shadow: none` or a flat shadow)
- [ ] Hover on the quick-links with a `--brand-red-muted` ring
- [ ] The logo inverted in dark mode through `filter: invert(1)`
- [ ] No color hardcoded outside a CSS token — verifiable: a grep over the CSS
- [ ] The `fadeSlideIn` animation on the sections — verifiable: observing a reload

### Accessibility
- [ ] The graduation bar with `role="progressbar"` and the correct `aria-valuenow`
- [ ] The dependent tabs with `role="tablist"`, `role="tab"`, `aria-selected`
- [ ] Buttons with an `aria-label` where `textContent` is not enough
- [ ] The SVG belt with a descriptive `aria-label`
- [ ] `:focus-visible` visible on every interactive control

### Technical
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 failures
- [ ] `manage.py collectstatic` — no error
- [ ] The browser console — no critical JavaScript error
- [ ] The server terminal — no stack trace

---

## Expected evidence

- Desktop screenshot, light theme: the admin home with quick access + empty classes + the finance stub
- Desktop screenshot, dark theme: the same structure, the logo inverted, correct token colors
- Mobile screenshot at 375px: a single column, quick-access in 2 columns, a compact belt
- Screenshot of a student with an active plan: the tuition card with a green badge + the `Trocar plano` (`Change plan`) button
- Screenshot of a student with a belt: the SVG belt with colors + the graduation bar with the real %
- Output of `manage.py check` — System check identified no issues
- Output of `manage.py test --verbosity 2` — OK

---

## Implemented

- The immediate functional slice of the current home was fixed:
  - the `system:student-checkin` and `system:student-special-checkin` JSON routes registered in `system/urls.py`
  - the student's check-in button is no longer a dead link and now uses `fetch()` with CSRF
  - the home's inline JavaScript extracted into `static/system/js/dashboard.js`
  - `dashboard.css` versioned in the template as `?v=5`
  - shortcuts to modules that are not renderable in the current state are no longer `href="#"` and now appear as disabled items
  - the `Trocar plano` (`Change plan`) button no longer points to `#` while `billing/plan_change_select.html` does not exist in the current template tree
  - the plan field in the tuition card adjusted to `m.plan.display_name`
- Coverage added in `system/tests/test_home_dashboard.py` for:
  - rendering the student home with the real check-in endpoint
  - creating a pending check-in through the JSON endpoint
  - the technical admin home with no dead `href="#"` links

## Deviations from plan

- The complete visual routes for People, Classes, Finance, Graduation, Materials, and Plans were not restored in this slice. The views exist in the code, but the corresponding templates do not exist in the current `templates/`; registering those routes now would cause a template error.
- `static/system/js/home/dashboard.js` was not created because the `static/system/js/home/` folder does not exist and `CLAUDE.md` forbids creating new folders in this project. The JavaScript was created at `static/system/js/dashboard.js`, inside an existing folder.
- Visual validation was done with a technical admin and empty states. The complete visual flow for a student with a belt, an active tuition, and a class for the day depends on coherent local data/seeds.

## Pending

- A specific PRD to restore the complete internal modules from the legacy system without copying templates directly:
  - recreate the templates within the current UI contract
  - register the corresponding routes
  - validate permissions and states per profile
- Re-enable `Trocar plano` (`Change plan`) on the home once `billing/plan_change_select.html` is recreated in the current template tree.
- Re-enable the real staff links once the destination screens exist and pass visual validation.
