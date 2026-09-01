# PRD-141: In-Depth Frontend Review — Identified Problems

## Summary

**Highly critical** read-only audit of the LV JIU JITSU frontend (Jul/2026): 92
templates and 27 assets under `static/system/` (CSS, JS, images). Complements
PRD-138/139 (cross-cutting disorder) with an **in-depth UI-only** analysis. The
consolidated correction proposal is organised into P0–P2 waves (Jul/2026).

## Demand type

Read-only frontend audit + routing PRD. **Does not implement code.**

## Current problem

The frontend works, but concentrates risk across four axes:

1. **Architecture** — no `base.html`; three parallel shells; theme and assets
   repeated across dozens of templates.
2. **Domain in JS** — plan/class/IBJJF eligibility and checkout reimplemented
   in the browser (3k+ lines).
3. **Security/maintenance** — 43 uses of `innerHTML` in JS; PRD-080 not
   executed; JSON with `|safe` in `<script type="application/json">`.
4. **UX/a11y/performance** — monolithic `dashboard.html` (1.3k lines), 12
   modals in the initial DOM, no focus trap, full catalog rerender on every
   filter.

## Goal

Record **every frontend problem** with severity, evidence (file/line/pattern),
and a verifiable P0–P2 wave-based correction plan.

## Context Ledger

### Files read in full

- `static/system/js/auth/register.js` (3,334 lines)
- `static/system/js/dependents/dependent_registration.js` (1,204 lines)
- `static/system/js/home/dashboard.js` (1,716 lines)
- `static/system/css/lv/base.css`
- `static/system/css/auth/register.css` (2,015 lines)
- `static/system/css/home/dashboard.css` (2,860 lines)
- `templates/login/register.html` (1,053 lines)
- `templates/home/dashboard.html` (1,366 lines)
- `templates/auth/base_auth.html`
- `templates/lv/modal_frame.html`
- `static/system/js/lv/theme_boot.js`, `crud_modal.js`, `theme_toggle.js`
- `docs/PRD-STANDARD.md`, `docs/prd/PRD-138-*.md`,
  `docs/prd/PRD-139-*.md`, `docs/prd/PRD-080-*.md`

### Adjacent files consulted

- Inventory: 92 templates (`Glob templates/**/*.html`), 27 assets
  (`Glob static/system/**/*`)
- `rg` for: `innerHTML`, `?v=`, `extends`, `|safe`, `<script`, `theme_boot`,
  `aria-modal`, `style=`
- Sample: `templates/dependents/dependent_registration.html`,
  `templates/people/person_list.html`, `templates/calendar/calendar.html`,
  `static/system/js/products/store_cart.js`,
  `static/system/css/people/people.css`

### Internet / official documentation

- [Django static files](https://docs.djangoproject.com/en/5.2/howto/static-files/) — asset versioning/caching and `{% static %}`.
- [MDN — `Element.innerHTML` security considerations](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML#security_considerations) — XSS risk and preference for safe APIs.
- [MDN — WAI-ARIA `dialog` pattern](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/dialog_role) — focus trap, `aria-modal`, focus return.

### Context7 / MCPs / tools verified

- `Glob`, `Grep`, `Read` in the workspace (no code changes).
- Context7 not consulted in this round (findings based on code and the
  Django/MDN documentation above).

### Limitations found

- Static audit; **no** browser, Lighthouse, axe, or real-device test run.
- `register.js` read by sections (file >100k characters); line count through
  PowerShell.
- `staticfiles/` not inspected (generated output).
- Runtime gateway behaviour (Asaas/Stripe) not validated in the wizard.

## Required skills

- `lv-task-intake` (completed)
- `lv-prd` (this PRD)
- `lv-ui-delivery` (future visual-validation criteria)

## Understanding approved

Demand classified as a **critical read-only frontend audit**. Scope:
`templates/` (92), `static/system/`. Deliverable: PRD-141 with a consolidated
correction proposal. Implementation through child PRDs.

## Execution prompt

### Persona

Relentless senior reviewer — criticise only, without praise. Every finding must
have evidence.

### Action

Audit the complete frontend; list problems by severity; critique shell
architecture; document in PRD-141.

### Context

PRD-138/139 documented the overall disorder. This PRD investigates **only**
the presentation layer in depth.

### Constraints

- Read-only.
- Correction proposal filled in (Jul/2026); execution requires one child PRD
  per wave.
- Follow `docs/PRD-STANDARD.md`.

### Acceptance criteria

- [ ] PRD-141 created with the complete template.
- [ ] "Identified problems" section with CRITICAL/HIGH/MEDIUM/LOW and evidence.
- [ ] Shell architecture documented.
- [ ] README updated after PRD-139.
- [ ] Plan with unchecked checkboxes.
- [ ] Official external source cited.

### Expected evidence

- Repository paths and lines.
- `rg`/PowerShell counts recorded in this PRD.

### Output format

Markdown at `docs/prd/PRD-141-frontend-problem-review.md`.

## Scope

- `templates/` — 92 HTML files.
- `static/system/` — CSS, JS, images (27 files).
- Problems: UX, a11y, responsiveness, performance, security (XSS,
  `innerHTML`, CSRF in JS), visual consistency, duplication, improper business
  rules in JS, shells, `?v=`, inline scripts, light/dark themes, mobile, modals,
  `register.js`, `dependent_registration.js`, `dashboard.js`.

## Out of scope

- Implementing corrections.
- Backend (`system/services`, forms, views), except as contrast where JS
  duplicates a rule.
- Staging/production, deployment, real payment.
- Generated `staticfiles/`.
- Implementing corrections (execution through child PRDs by wave).

## Impacted files

| Area | Main files |
|---|---|
| Public wizard | `templates/login/register.html`, `static/system/js/auth/register.js`, `static/system/css/auth/register.css` |
| Dependent wizard | `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js` |
| Home | `templates/home/dashboard.html`, `static/system/js/home/dashboard.js`, `static/system/css/home/dashboard.css` |
| Admin shell | ~57 standalone templates + `static/system/css/lv/base.css`, `people/people.css`, `classes/classes.css` |
| Auth shell | `templates/auth/base_auth.html`, `templates/login/*.html` |
| Modal CRUD shell | `templates/lv/modal_frame.html`, `static/system/js/lv/crud_modal.js` |

## Risks and edge cases

- Correcting only `innerHTML` without moving eligibility to the backend may
  hide client/server divergence.
- Unifying the shell without a `?v=` map may break caching for users with old assets.
- Iframe modals (dependent/schedule) require a parent↔child focus strategy;
  naive removal breaks UX.
- `register.js` and `dependent_registration.js` diverge in date parsing (DD/MM
  versus ISO) — a partial correction creates a silent regression.

## Rules and constraints

- Business rules belong in `services/` (AGENTS.md §9); current wizard JS
  violates this.
- PRD-080 requires eliminating `innerHTML` with user data — still pending.
- Light/dark theme is mandatory (CLAUDE.md §9) — implementation is inconsistent
  across shells.

## Frontend architecture (critical review)

### Shell inventory (92 templates)

| Shell | Mechanism | Quantity | Problem |
|---|---|---:|---|
| **Standalone monolith** | Complete `<!DOCTYPE html>`, duplicated head/body | **62** | No inheritance; every screen redeclares metadata, theme, CSS, scripts |
| **Auth** | `{% extends "auth/base_auth.html" %}` | **5** | Login + password reset only; wizard/register **does not** use it |
| **CRUD iframe modal** | `{% extends "lv/modal_frame.html" %}` | **25** | Third head/body; `theme_boot.js` without `?v=` |
| **Partials** | `{% include %}` without shell | **4** | Fine as fragments; coupled to `dashboard.html` |

There is **no** `templates/lv/base.html` or global `base.html`. PRD-075
introduced `base.css`, but not a unified Django layout.

### Three incompatible visual families

```text
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Wizard / Register   │  │ Dashboard / Home    │  │ Admin list/detail   │
│ register.css tokens │  │ dashboard.css tokens│  │ base+people+classes │
│ max-width 540px     │  │ topbar + sections   │  │ CRUD + modals       │
│ inline theme IIFE   │  │ inline theme IIFE   │  │ theme_boot.js       │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Two modal systems

1. **`<dialog class="crud-modal">` + iframe** — `crud_modal.js`,
   `modal_frame.html` (admin).
2. **`.modal-overlay` + `hidden`** — `dashboard.html` (12 modals) +
   dependent/schedule iframes.

No common API: `overflow` alternates between `style` and `classList`; closing
uses duplicated listeners per modal.

### God modules

| File | Lines | Role |
|---|---:|---|
| `register.js` | 3,334 | Complete wizard + plans + materials + operations + coupon |
| `dashboard.js` | 1,716 | Theme + 12 modals + check-in + tabs + filters + AJAX |
| `dashboard.css` | 2,860 | Home + modals + components |
| `register.css` | 2,015 | Wizard + plans + products + operations |
| `dashboard.html` | 1,366 | Markup for every area + every modal |

## Identified problems

Severity legend:

- **CRITICAL** — security risk, business divergence, or structural debt that
  blocks evolution.
- **HIGH** — serious a11y/performance/UX issue or massive duplication making
  maintenance impractical.
- **MEDIUM** — inconsistency, clear debt, repeated workaround.
- **LOW** — polish, convention, marginal optimisation.

---

### CRITICAL

| ID | Problem | Evidence |
|---|---|---|
| C-01 | **Eligibility business rules in JS** — `resolveAudience`, class filtering by age/gender/IBJJF, and plan eligibility (family, adult, kids) implemented in the browser; the server should be authoritative (`plan_eligibility.py` cited in PRD-138). | `register.js` L2218–2257 (`calcAgeYears`, `resolveAudience`, `filterGroupsByPerson`); L1427–1446 (`getEligiblePlansForCurrentPerson`); `dependent_registration.js` L146–201, L341–373 |
| C-02 | **God module `register.js`** — 3,334 lines, state machine, step validation, checkout, materials, coupon, operational profiles; impossible to review or unit-test in its current state. | Line count; functions `validatePrincipal` L644+, `validatePlan` L1688+, `submitOperationalRegistration` L2201+ |
| C-03 | **Near-complete duplication in dependent wizard** — `dependent_registration.js` (1,204 lines) replicates the class, plan, and material catalogs, step navigation, and helpers (`escHtml`, `fmtPrice`, masks) already present in `register.js`. | Mirrored structure: `bindClassCatalog` L204–277 versus `register.js` `renderClassCatalog` L2290–2343; `bindPlanCatalog` L302–721; 18× `innerHTML` in both |
| C-04 | **43 `innerHTML` occurrences in JS** — PRD-080 incomplete; pattern prohibited by the UI contract for dynamic data; manual `escHtml` does not cover every vector (attributes, URLs, concatenated SVG). | `rg innerHTML`: `register.js` 22, `dependent_registration.js` 18, `dashboard.js` 3 |
| C-05 | **Catalog JSON with `\|safe` in template** — if serialisation fails or injects `</script>`, a classic XSS vector in a JSON block. | `register.html` L13–24; `dependent_registration.html` L12–16 |
| C-06 | **No Django base layout** — 62 pages reimplement the HTML document; any global change (CSP, favicon, font, theme) requires mass editing. | `rg ^<!DOCTYPE` → 62 templates; only 30 use `extends` (25 modal + 5 auth) |
| C-07 | **Wizard state exclusively client-side** — navigation, plan filters, and class selection live in JS `state`; risk of divergence from server-side `PreRegistration` (PRD-040). | `register.js` — `state` object, `clearWizardState`, `onEnterPlan`, `validatePlan`; `novalidate` form in `register.html` L70 |

---

### HIGH

| ID | Problem | Evidence |
|---|---|---|
| A-01 | **Monolithic `dashboard.js`** — 1,716 lines, 15+ `bind*Modal` calls during boot, global `document` listeners for every feature. | L1692–1715 initialisation; functions L349–1648 |
| A-02 | **Monolithic `dashboard.html`** — 1,366 lines; 12 modals + duplicated data in the DOM (for example, check-in lists cloned into the attendance modal). | Modals L719–1320; `bindPresenceModal` clones children in `dashboard.js` L946–950 |
| A-03 | **Modals without focus trap / no background `inert`** — keyboard focus can escape; focus does not return to the trigger; incomplete ARIA dialog pattern. | `rg focus-trap|inert|aria-modal` in JS → 0 under `static/system/js`; modals use only `hidden` + `aria-modal="true"` in `dashboard.html` |
| A-04 | **12+ Escape `keydown` listeners on `document`** — one per modal; unpredictable cost and execution order. | `dashboard.js` L384–386, L443–445, L727–729, L781–783, L816–818, L862–864, L948–965, L1148–1150, L1187–1189, L1415–1417, L1507–1509, L1589–1591 |
| A-05 | **Full catalog rerender through `innerHTML`** — every filter/pill click destroys and recreates the entire DOM (plans, classes, products); focus loss, layout cost, manually reattached listeners. | `register.js` L1509, L1645 (`renderPlanFilters`/`renderPlanCards`); `dependent_registration.js` L459, L582, L843 |
| A-06 | **Inconsistent date parsing between wizards** — `register.js` accepts only `DD/MM/YYYY` (`split('/')`); dependent also accepts ISO `YYYY-MM-DD`; same IBJJF rule, different results. | `register.js` L2218–2222; `dependent_registration.js` L146–158 |
| A-07 | **Dependent iframe not clearing `src` on close** — internal document remains in memory; duplicated wizard CSS/JS load. | `bindDependentRegistrationModal` in `dashboard.js` L419–423 closes overlay but does not reset iframe; contrast with `crud_modal.js` L31–33 (`about:blank`) |
| A-08 | **Duplicated and divergent CSS tokens** — `:root` and `html[data-theme="dark"]` redefined in `base.css` L6–54 and `register.css` L6–39 with different values (`--bg`, `--surface`, etc.). | Manual diff of `:root` blocks; admin loads `base.css`, wizard loads only `register.css` |
| A-09 | **Triple admin CSS stack without contract** — ~41 screens load arbitrary `base.css?v=1` + `people.css?v=2` + `classes.css?v=1|v=2`. | `rg lv/base.css` 41 templates; `classes.css` v=1 in ~35, v=2 in 6 (`request_list.html` L11, `graduation_overview.html` L11) |
| A-10 | **Wizard validation depends on JS with `novalidate`** — HTML5 disabled; without JS, submission bypasses step barriers. | `register.html` L70 `novalidate`; `dependent_registration.html` form without guaranteed server-step equivalent on client |
| A-11 | **Correct CSRF in JSON fetch, but inconsistent** — `dashboard.js` `getCsrfToken` L31–34 works; coupon in `register.js` L2701 uses POST `fetch` — if token is absent in an edge case, it fails silently. | Mixed FormData versus JSON pattern; hidden CSRF holder in `dashboard.html` L44 |

---

### MEDIUM

| ID | Problem | Evidence |
|---|---|---|
| M-01 | **Duplicated inline theme boot (17×)** — same IIFE copied instead of versioned `theme_boot.js`. | `rg localStorage.getItem('lv-theme')` in 17 templates (`register.html` L8, `dashboard.html` L8, etc.) |
| M-02 | **`theme_boot.js` / `theme_toggle.js` / `crud_modal.js` without `?v=`** — 42 templates reference unversioned `theme_boot.js`; only `base_auth.html` uses `?v=20260629-4`. | `rg theme_boot.js` — 1 match with `?v=`, all others unversioned |
| M-03 | **Incompatible `?v=` schemes** — numeric (`?v=49`), absent, date (`20260629-4`); no single cache-busting policy. | `register.js ?v=49`, `dashboard.css ?v=29`, `login.css ?v=20260629-4`, `plans.js ?v=1` |
| M-04 | **Divergent CSS version in the same dependent flow** — `dependent_registration.css ?v=14` versus `dependent_registration_done.css ?v=7` on done. | `dependent_registration.html` L11; `dependent_registration_done.html` L10 |
| M-05 | **`installment_select.html` with `register.css ?v=7`** — registration-flow page with potentially obsolete cache (wizard at `?v=26`). | `installment_select.html` L9 |
| M-06 | **Dark-theme logo through `filter: invert`** — hack instead of existing `logo-lv-white.png` asset, unused on home. | `dashboard.html` L16 `logo-lv-dark.png`; `dashboard.css` L123 `filter: invert`; asset under `static/system/img/` |
| M-07 | **Montserrat font only in auth shell** — dashboard/register use `system-ui`; inconsistent typographic identity. | `base_auth.html` L10–12; absent from `dashboard.html`/`register.html` |
| M-08 | **Tabs without arrow-key navigation** — click only; does not follow APG tab pattern. | `dashboard.js` `bindTabs` L89–114 — no `ArrowLeft`/`ArrowRight` |
| M-09 | **Native `window.confirm` / `alert`** — UX inconsistent with custom modals. | `dashboard.js` L826 `confirm` dependent removal; L1683 `alert` class cancellation |
| M-10 | **Messages auto-dismiss after 5s** — user may miss a critical error. | `dashboard.js` L79–86 `bindAutoDismissMessages` |
| M-11 | **Inline styles in templates** — bypass tokens; make theming harder. | `rg style=` → 35 occurrences in 30 templates; `person_detail.html` 38× |
| M-12 | **Monolithic inline `home-config` JSON** — single string in `dashboard.html` L45; fragile with empty URLs and difficult to validate. | `dashboard.html` L45 |
| M-13 | **Wizard progress bar with fixed inline width** — misaligned if the server changes the step count. | `register.html` L49 `style="width:16.66%"` (6 hardcoded steps in markup L43) |
| M-14 | **Coupon validated through Portuguese route `/cadastro/validar-cupom/`** — i18n URL coupling in JS. | `register.js` L2701 |
| M-15 | **Postal code through ViaCEP in wizard** — external client-side dependency; network failure without clear degradation. | `register.js` L84 `fetch('https://viacep.com.br/ws/'` |
| M-16 | **Additional inline scripts** — `person_detail.html`, `person_confirm_delete.html`, `installment_select.html` with behaviour `<script>` blocks. | `templates/login/installment_select.html` L231+; `person_confirm_delete.html` L79+ |
| M-17 | **`plan_form_modal.html` script without `defer`** — may block iframe parsing. | `plan_form_modal.html` L52; `tier_form_modal.html` L52 |
| M-18 | **`modal-open` versus `overflow: hidden` contrast** — two APIs for locking scroll. | `client-profile` uses `body.classList.add('modal-open')` L482; calendar uses `body.style.overflow` L361 |

---

### LOW

| ID | Problem | Evidence |
|---|---|---|
| B-01 | **Minimal `store_cart.js` without feedback** — only builds JSON on submit; no client stock validation (fine if server validates). | `store_cart.js` L1–20 |
| B-02 | **`calendar.js` without `innerHTML`** — relatively positive, but `calendar.html` repeats the inline theme IIFE. | `calendar.html` L8; `calendar.js` without `innerHTML` |
| B-03 | **Duplicated inline SVG and icons** — dozens of identical SVG blocks in templates; HTML weight. | `dashboard.html` — multiple `<svg>` blocks in topbar/quick links |
| B-04 | **`prefers-reduced-motion` only in `register.css`** — dashboard does not reduce section/modal animation. | `register.css` L2280–2282; absent from `dashboard.css` |
| B-05 | **Home partials without documented visual tests** — `home/partials/*.html` (4) coupled to dashboard without isolation. | `templates/home/partials/` |
| B-06 | **Favicon not referenced in wizard/dashboard** — only in `base_auth.html` L8. | `register.html`, `dashboard.html` without `<link rel="icon">` |

---

### Summary matrix

| Severity | ID count |
|---|---:|
| CRITICAL | 7 |
| HIGH | 11 |
| MEDIUM | 18 |
| LOW | 6 |
| **Total** | **42** |

## Correction proposal

> Correction proposal filled in by the consolidator in Jul/2026.

Actionable plan aligned with PRD-138 (waves 2–3), PRD-142 (home/selectors), and
PRD-143 (eligibility API + god form). **Blocking prerequisite:** findings C-01
and C-07 enter P1 only after PRD-143 Wave P0 (unified validation + read-model
API).

### Prioritised waves

| Wave | Focus | Overall risk | Dependencies |
|---|---|---|---|
| **P0** | Base shell + JSON security + `?v=` policy | Medium | Independent of JS; **do not** deduplicate 62 templates before `base.html` |
| **P1** | Server-driven eligibility + shared wizard module | High | **Blocked by** PRD-143 P0 (`registration_forms` split + eligibility API) |
| **P2** | `innerHTML`, dashboard/modals, CSS tokens, a11y | Medium–high | P1 completed; residual PRD-080 |

---

### Wave P0 — Shell and cache foundation (without touching JS business rules)

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| C-06 | Create `templates/lv/base.html` with `title`, `extra_css`, `content`, `extra_js` blocks; include favicon, metadata, `theme_boot.js?v=…`, CSRF holder | New `templates/lv/base.html`; pilot: `templates/people/person_list.html`, `templates/calendar/calendar.html` | 2 pilot templates use `extends`; `rg ^<!DOCTYPE` drops by 2; light/dark theme works desktop+mobile in browser | Medium |
| C-05 | Replace `\|safe` in JSON with `json_script` or escaped Django serialisation | `templates/login/register.html` L13–24; `templates/dependents/dependent_registration.html` L12–16 | No `\|safe` in `<script type="application/json">`; wizard loads catalog; no console errors | Low |
| M-02, M-03 | Single `?v=YYYYMMDD-n` policy for **all** assets referenced by `base.html` and existing shells | `theme_boot.js`, `theme_toggle.js`, `crud_modal.js`; grep under `templates/` | `rg 'theme_boot\.js"'` → 0 without `?v=`; bump documented in `UI-SCREEN-CONTRACT.md` | Low |
| B-06 | Common favicon and metadata through `base.html` | Pilot + `register.html`, `dashboard.html` in P1 | `<link rel="icon">` present on pilot pages | Low |

**Internal dependency:** C-06 **before** migrating all 62 standalone templates
(phased map: admin CRUD → home → wizard).

**What NOT to do in P0:**
- Do not remove `innerHTML` or split `register.js` (would hide backend divergence).
- Do not unify CSS tokens (`register.css` `:root`) before `base.html` defines the canonical stack.
- Do not change `resolveAudience` / `getEligiblePlansForCurrentPerson` in JS.

---

### Wave P1 — Server-driven wizard and deduplication (after PRD-143 P0)

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| C-01, C-07 | Remove eligibility from JS; consume read-model API (`build_eligibility_context_for_person` exposed through JSON view) | `static/system/js/auth/register.js` L2218–2257, L1427–1446; `dependent_registration.js` L146–201, L341–373; new route in `auth_views.py` / service (PRD-143) | HTTP test: API response equals `plan_eligibility.py` result for family fixture; JS only renders disabled/enabled cards; **zero** `calcAgeYears` for plan filter | High |
| C-02, C-03 | Extract `static/system/js/lv/wizard_shared.js` (class/plan catalog, `escHtml`, masks, step navigation) | `register.js`, `dependent_registration.js`; templates with `?v=` bump | `register.js` LOC < 2000; `dependent_registration.js` < 600; duplicated `bindClassCatalog`/`renderClassCatalog` functions unified | High |
| A-06 | Unify date parsing to ISO in shared module (backend already validates) | `wizard_shared.js`; remove exclusive `split('/')` from `register.js` | Same DD/MM and ISO date produces same class eligibility in E2E test | Medium |
| C-06 (cont.) | Migrate `register.html` and `dependent_registration.html` to `extends lv/base.html` | `templates/login/register.html`, `templates/dependents/dependent_registration.html` | Wizard inherits theme/favicon/CSRF; no duplicated inline IIFE (M-01) | Medium |
| A-10 | Restore progressive HTML5 validation where possible; retain server-side gate per step | `register.html` L70 `novalidate` → conditional or removed with `required` by step | Without JS: server blocks submit with 400; with JS: intermediate steps do not POST finalisation | Medium |

**Dependencies:** PRD-143 findings #1, #10 (god form + single validation)
**completed** before C-01. PRD-138 Wave 2 (PRD-129) may proceed in parallel.

**What NOT to do in P1:**
- Do not delete all of `dependent_registration.js` before the shared module is stable.
- Do not move checkout/coupon to shared without sandbox payment tests.

---

### Wave P2 — UI hardening, client performance, and a11y

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| C-04 | Eliminate `innerHTML` with dynamic data (PRD-080); use `textContent`, `createElement`, or `<template>` | `register.js` (22×), `dependent_registration.js` (18×), `dashboard.js` (3×) | `rg innerHTML static/system/js` → 0 in user-data flows; wizard tests green | High |
| A-01, A-02 | Split `dashboard.js` / `dashboard.html` by domain; lazy-load modals | `dashboard.js`, `dashboard.html`, new `static/system/js/home/*` | `dashboard.html` < 800 lines; off-viewport modals load on demand | High |
| A-03, A-04 | Single modal module: focus trap, background `inert`, centralised Escape, focus return | New `static/system/js/lv/modal.js`; refactor `dashboard.js` `bind*Modal` | axe/dialog: focus trapped; 1 Escape listener; valid tab order in 3 sample modals | Medium |
| A-05 | Incremental catalog updates (DOM diff) instead of full rerender | `wizard_shared.js` `renderPlanCards` / `renderClassCatalog` | Plan filter does not destroy focus; Performance tab shows no visible layout thrashing | Medium |
| A-07 | Reset `iframe.src` when closing dependent/schedule modals | `dashboard.js` L419–423; align with `crud_modal.js` L31–33 | Stable memory after 5 open/close cycles; network shows no duplicate reload | Low |
| A-08, A-09 | Remove `:root` from `register.css`; admin uses only `base.css` tokens | `register.css` L6–39; admin templates | Zero visual diff in light/dark themes; one source for `--bg`/`--surface` | Medium |
| A-11 | Standardise `getCsrfToken` in `lv/csrf.js` helper | `dashboard.js`, `register.js` L2701 | Coupon/AJAX POST fails with a message if token is absent | Low |

**Dependencies:** stable P1 shared wizard. `base.html` (P0) before mass admin CSS deduplication.

**What NOT to do in P2:**
- Do not merge both modal systems (iframe CRUD versus dashboard overlay) without
  an approved design PRD.
- Do not replace ViaCEP with hardcoding; retain graceful degradation (M-15).

---

### MEDIUM/LOW findings — P2+ backlog

| IDs | Summarised action | When |
|---|---|---|
| M-01 | Remove 17 theme IIFEs after `base.html` | P0 shell migration |
| M-06–M-09, M-13–M-18 | UX polish (logo, keyboard tabs, `confirm`→modal) | After P2 modals |
| B-03–B-05 | SVG partials, dashboard `prefers-reduced-motion` | PRD-138 Wave 3 |

---

## Cross-PRD dependencies

| Dependency | Partner PRD | Direction | Block |
|---|---|---|---|
| Eligibility API + unified validation | **PRD-143** P0 (#1, #10) | 143 → 141 | C-01, C-07 cannot start without API |
| Split `registration_forms` | **PRD-143** P0 | 143 → 141 | Remove JS rule only after form/service work |
| `home_views` → selectors | **PRD-142** P0 + **PRD-143** P1 (#6) | 142+143 → 141 | Dashboard consumes already optimised context |
| `base.html` before template deduplication | **PRD-141** P0 | 141 → 141 | 62 standalone only after shell |
| `innerHTML` / PRD-080 | **PRD-141** P2 | Internal | After shared wizard |
| Shell + tokens | **PRD-138** Wave 3 | 138 ↔ 141 | Align PRD-075/084 |
| `PlanTier`-only catalog | **PRD-138** Wave 2 / **PRD-143** P1 (#8) | 143 → 141 | Wizard consumes only `pp:` through API |

## Visual hierarchy

Current state (not prescriptive):

- **Wizard** — single 540px column, fixed header (back/logo/progress), stacked
  `hidden` steps.
- **Dashboard** — global topbar + collapsible sections + tabs by person
  (billing/classes/profile).
- **Admin** — simplified topbar + table/list + CRUD actions in an iframe modal.

## Wireframe

```text
[WIZARD 540px]                 [DASHBOARD full]              [ADMIN list]
┌──────────────────┐          ┌────────────────────────┐   ┌────────────────────────┐
│ ← Logo    Step   │          │ Logo    [profile][theme]│   │ Logo    [theme] [exit]│
│ ████░░░░ progress│          ├────────────────────────┤   ├────────────────────────┤
│ Step title       │          │ ▼ Section (collapse)   │   │ Filters / KPIs         │
│ [cards/list]     │          │   cards / tables       │   │ Table                   │
│ [Next]           │          │ [modal overlay 12×]    │   │ [dialog>iframe CRUD]    │
└──────────────────┘          └────────────────────────┘   └────────────────────────┘
```

## State machine

Wizard (`register.js`): state machine **on the client** — profile → data →
martial → classes (N students) → plans (N students) → payment → materials →
review → final POST. Local `validate*` functions block transitions; server flags
(`reg-post-plan-json`, etc.) only rehydrate input.

Dependent (`dependent_registration.js`): mirrored subset with
`data-payment-confirmed` / `data-materials-confirmed` on the form.

Dashboard: no unified machine; every modal is an independent micro-state with
its own DOM.

## Plan

### Wave P0 — Shell and cache
- [x] Create `templates/lv/base.html` and migrate 2 admin pilot templates (`person_list.html`, `calendar.html`)
- [x] Correct C-05: `json_script` in `register.html` and `dependent_registration.html`
- [x] Normalise `?v=` in `theme_boot.js`, `theme_toggle.js`, `crud_modal.js` (M-02, M-03)
- [ ] Document migration map for 62 standalone templates (phases: admin → home → wizard)
- [ ] Update `docs/UI-SCREEN-CONTRACT.md` with the real shell

### Wave P1 — Wizard (after PRD-143 P0)
- [x] Validate C-01/C-07 against `plan_eligibility.py` API (contract test) — holder and dependent
- [x] Extract `wizard_shared.js` — surgical extraction of duplicated functions (age calculation, eligibility, CSRF, endpoints); **did not** reduce `register.js`/`dependent_registration.js` below LOC targets (<2000/<600) — see PRD-144 F-06/F-07
- [x] Unify date parsing (A-06) — backend + `wizard_shared.js` accept DD/MM and ISO
- [ ] Migrate wizard templates to `extends lv/base.html`
- [ ] Review `novalidate` and server-side gate (A-10)

### Wave P2 — Hardening
- [ ] Execute PRD-080: eliminate 43 `innerHTML` calls (C-04) — started (`setElementText` in dependent plan empty state), 41 occurrences remain
- [ ] Split `dashboard.html` / `dashboard.js` (A-01, A-02)
- [ ] Implement `modal.js` with focus trap + single Escape handler (A-03, A-04)
- [ ] Unify CSS tokens; remove `:root` from `register.css` (A-08, A-09)
- [x] Modal iframe lifecycle (A-07) — dependent and calendar
- [x] Standardise `getCsrfToken` (A-11) — `lv/csrf.js`

## Test plan

### Tests to author

- [ ] Wizard E2E tests: plan/class eligibility matches API/server response
- [ ] Automated a11y tests (axe) on dashboard modals
- [ ] Desktop/mobile light/dark visual regression tests by shell

### Execution authorization

Read-only audit — tests **not run** in this PRD.

### Execution evidence

- None (pending execution PRDs).

## Visual validation

| Item | Status |
|---|---|
| Desktop browser wizard | Not run |
| Mobile browser wizard | Not run |
| Dashboard browser modals | Not run |
| Dark/light theme | Not run |
| Clean console | Not run |

## ORM validation

Not applicable (read-only frontend scope).

## Quality validation

| Verification | Result |
|---|---|
| Inventory of 92 templates | OK (`Glob`) |
| Inventory of 27 assets | OK (`Glob`) |
| Full reading of critical files | OK (`register.js` by sections) |
| `rg innerHTML` / `?v=` / shells | OK |

## Evidence

- Line counts (PowerShell 2026-07-08): `register.js` 3334, `dashboard.js` 1716,
  `dependent_registration.js` 1204, `dashboard.html` 1316, `register.html`
  1053, `register.css` 2015, `dashboard.css` 2860.
- `rg innerHTML` under `static/system/js`: 43 occurrences (22+18+3).
- `rg ^<!DOCTYPE` in templates: 62 standalone.
- `rg extends`: 25 `lv/modal_frame`, 5 `auth/base_auth`.
- `rg localStorage.getItem('lv-theme')`: 17 inline IIFEs.
- `rg theme_boot.js`: 42 templates; 1 with `?v=`.

## Implemented

Nothing implemented in the original audit — documentation only.

**[2026-07-09] Wave P0 + part of P1 executed** (outside the original read-only
scope, authorised by the user):

- **Wave P0** — `templates/lv/base.html` created (pilot on 2 screens);
  `json_script` replacing `|safe` in `register.html`/`dependent_registration.html`
  (C-05); `?v=` normalised in 44 templates (M-02/M-03). See evidence in PRD-138.
- **Wave P1 (partial) — C-01/C-07 (server-driven eligibility in public
  wizard)**: `register.js` (`static/system/js/auth/register.js`, `?v=50`) now
  queries `POST /cadastro/elegibilidade/` (API created in PRD-143 P0) through
  `refreshEligibilityFromServer()`, cached in `state.eligibility` (key = hash of
  relevant payload). `getEligiblePlansForCurrentPerson()` uses the server's
  `eligible_plan_ids` list as business authorisation (family, aggregate
  audience); local calculation (`resolveAudience`) remains only as (a) fallback
  before the response arrives and (b) **presentation** filter — which person's
  tab to show, no longer the source of truth for eligibility.
  - Risk mitigation: with no E2E framework in the project, validated through
    the internal browser with network/DOM verification at each step (not just a
    screenshot) — POST confirmed in server logs, API response checked byte for
    byte against expected `context` (adult holder + kids dependent →
    `adult_family_group_eligible=true`), tab switching confirmed without
    redundant refetch (working cache), zero console errors at every step.
  - **Not closed in this round**: `dependent_registration.js` remains 100%
    client-side for eligibility (same pattern, not yet replicated); unified date
    parsing (A-06); migration of `register.html`/`dependent_registration.html`
    to `extends lv/base.html`; `novalidate` review (A-10). Deferred to the next
    P1 round.
  - Evidence: `manage.py test system` — 662 tests OK; `node --check register.js`
    without syntax errors; complete manual holder+dependent wizard validation
    (profile → data → health → martial → classes → **plan with API** → materials
    → back to plan) without regression.
- **[2026-07-09] Wave P1 closed — complete C-01/C-07, A-06, A-07, A-11**:
  - **A-06 (unified date parsing)**:
    `registration_validation.py::_parse_birthdate` now accepts `%d/%m/%Y`
    **and** `%Y-%m-%d` (fallback), because `dependent_registration.js` uses
    `<input type="date">` (ISO), while the eligibility API previously
    understood only the public wizard's BR format. Dedicated test:
    `test_registration_eligibility_api.py::test_holder_birthdate_accepts_iso_format`.
  - **C-01/C-07 (dependent) — closed**: `dependent_registration.js` now queries
    `POST /cadastro/elegibilidade/` (same endpoint as the public wizard),
    representing the dependent as an isolated "holder" in the payload. Covers
    the **actually active** branch (`dependentOwnPlanEligible` — dependent's own
    plan). The "family plan" branch (`familyUpgradePlanEligible`) remains
    client-side **because of a finding, not a shortcut**: no active `PlanPrice`
    currently has `is_family_plan=true` (PRD-127 migration moved family plans to
    the new catalog, which has no family variant — `get_eligible_plan_prices`
    filters only by audience); therefore that branch is effectively dead today,
    and there is no real business rule to migrate without first designing a
    "family PlanPrice" product (outside this PRD's scope).
  - **`wizard_shared.js` extraction**
    (`static/system/js/auth/wizard_shared.js`, `window.LV.Wizard` namespace):
    consolidated genuinely duplicated functions between both wizards —
    `calcAgeYears`/`resolveAudience` (now accept DD/MM **and** ISO in both,
    fully closing client-side A-06), `escapeHtml`, `readJsonScript`,
    `eligibilityFetchKey`/`fetchEligibility` (eligibility cache+POST machine),
    `getFormEndpoints` (reads `data-eligibility-url`/`data-validate-coupon-url`
    from `<form>`, eliminating hardcoded Portuguese URL
    `/cadastro/validar-cupom/` — also closing M-14), `setElementText` (safe DOM
    helper, beginning C-04), `formatIsoDateForDisplay`, `warn`. `register.js`
    and `dependent_registration.js` load the module first (non-deferred
    `<script>`) and abort with a console error if `window.LV.Wizard` is absent.
  - **A-11 (single CSRF)**: `static/system/js/lv/csrf.js`
    (`window.LV.getCsrfToken`) replaced 3 near-identical local implementations
    in `dashboard.js`, `register.js`, and `dependent_registration.js`.
  - **A-07 (iframe lifecycle)**: `dashboard.js` — `closeModal()` for dependent
    and calendar modals now resets `frame.src = 'about:blank'` on close (same
    pattern as `crud_modal.js`), preventing stale wizard state on reopening.
  - Validation: `manage.py test system` — 674 tests OK (674 = 662 + new tests
    from this and other parallel waves). Internal browser: public wizard
    (`/register/`) and dependent wizard (`/dependents/add/?modal=1`) traversed
    end to end through the plan step with a real holder (active membership),
    confirming in network logs that `POST /cadastro/elegibilidade/` fired with
    the correct payload and its response determined rendered plan cards (adult
    and child scenarios tested in both wizards), with no console errors.
  - **Still not closed**: F-06/F-07 (`register.js`/`dependent_registration.js`
    LOC — extraction was surgical, not a full rewrite: ~3,831L / ~1,398L
    today); complete C-04 (43 `innerHTML`, only plan empty state migrated to
    `setElementText`); A-01/A-02 (dashboard split); A-03/A-04 (`modal.js` with
    focus trap); A-08/A-09 (single CSS tokens); A-10 (`novalidate`); migration
    of `register.html`/`dependent_registration.html` to `extends lv/base.html`.
    Assessed as medium/high risk without an underlying correction bug (they are
    structural polish, not business-rule divergence corrections) — deferred to
    PRD-147 (see PRD-144).

## Cleanup findings

- PRD-080 remains open; scope expanded to include `dependent_registration.js`.
- PRD-084 (CSS tokens) partially violated because `register.css` duplicates `:root`.
- PRD number 041 already used by "Recurring Stripe"; this audit uses **PRD-141** as requested.

## Follow-up PRDs

| Suggested PRD | Scope |
|---|---|
| PRD-142+ (consolidator) | Unified shell + shared wizard extraction |
| PRD-080 (existing) | Eliminate `innerHTML` |
| PRD-084 (existing) | Single CSS tokens |

_Final numbering is the consolidator's responsibility._

## Deviations from plan

None — read-only scope fulfilled.

## Pending

- Execution of waves P0–P2 (requires an implementation child PRD per wave).
- PRD-143 P0 completed before P1 (JS eligibility).
- Desktop/mobile browser validation after implementation.

## Final status

**Completed** — static audit delivered; consolidated correction proposal
(Jul/2026). Implementation pending approval by wave.

## PRD-145 reconciliation — 2026-07-13

- The status above correctly describes delivery of the audit, not completion
  of every wave.
- P0 and the functional portion of P1 were later implemented, as recorded in
  `Implemented`; structural P2 remains pending.
- Current evidence: `/register/`, `/home/`, and the dependent modal rendered at
  1440×900 and 390×844, in light/dark themes, without console errors or warnings.
- Reconciled state: **audit completed; partial implementation**.
