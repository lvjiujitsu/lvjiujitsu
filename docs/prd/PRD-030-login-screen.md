# PRD-030: Login screen — implementation from scratch

## Summary of the implementation

Complete from-scratch implementation of the LV JIU JITSU portal login screen: a standalone HTML template, CSS with light/dark theme tokens, and minimal JavaScript (theme toggle + password visibility). Includes cleaning up `system/urls.py` to keep only the authentication and home routes, and a full rewrite of `docs/UI-SCREEN-CONTRACT.md`.

---

## Demand type

Redesign + implementation from scratch (a new UI feature)

---

## Current problem

Every template, CSS, and JavaScript file was deleted by the user to restart the visual project from scratch. The system renders no screen. The login screen is the system's entry point and must be the first delivery.

---

## Goal

Deliver a functional login screen, visually coherent with the LV identity, responsive on phone and desktop, with light and dark themes, starting from no existing template or asset.

---

## Context Ledger

### Files read in full

- `system/views/auth_views.py` — PortalLoginView, PortalLogoutView, PortalPasswordResetView, and variants
- `system/forms/auth_forms.py` — PortalAuthenticationForm (fields: identifier, password)
- `system/urls.py` — the complete route inventory before the cleanup
- `system/views/home_views.py` — DashboardRedirectView and the homes (the post-login destination)
- `system/views/__init__.py` — the re-export structure
- `docs/UI-SCREEN-CONTRACT.md` — the visual contract (rewritten in this delivery)
- `lvjiujitsu/settings.py` — general settings

### Adjacent files consulted

- `system/views/portal_mixins.py`
- `static/system/img/` — the available logo assets

### Internet / official documentation

- Django 4.1 FormView, CSRF, the messages framework
- WCAG 2.2 — minimum target size (2.5.8), contrast (1.4.3)

### MCPs / tools verified

- Playwright v1.52.0 — available in the .venv
- Python 3.12.10 through `.venv/Scripts/python.exe` — working
- `manage.py check` — 0 issues before the delivery

### Limitations found

- `templates/login/` did not exist — created in this delivery
- `static/system/css/auth/` did not exist — created in this delivery
- `static/system/js/auth/` did not exist — created in this delivery
- After a successful login, `DashboardRedirectView` redirects to homes that still have no template — a `TemplateDoesNotExist` is expected at this stage and is not a bug of this delivery

---

## Route mapping

| Route | View | Method | Purpose | Template in this delivery |
|---|---|---|---|---|
| `GET /` | PortalLoginView | GET | Redirects the root to login | `login/login_form.html` |
| `GET /login/` | PortalLoginView | GET | Displays the login form | `login/login_form.html` |
| `POST /login/` | PortalLoginView | POST | Processes the credentials | `login/login_form.html` (on error) |
| `GET /logout/` | PortalLogoutView | GET | Ends the session → root | — |
| `POST /logout/` | PortalLogoutView | POST | Ends the session → root | — |
| `GET /dashboard/` | DashboardRedirectView | GET | Redirects to the profile's home | — |
| `GET /home/admin/` | AdminHomeView | GET | Technical admin home | out of scope |
| `GET /home/administrative/` | AdministrativeHomeView | GET | Back-office home | out of scope |
| `GET /home/instructor/` | InstructorHomeView | GET | Instructor home | out of scope |
| `GET /home/student/` | StudentHomeView | GET | Student home | out of scope |
| `GET/POST /password-reset/` | PortalPasswordResetView | GET/POST | Request a reset | out of scope |
| `GET /password-reset/done/` | PortalPasswordResetDoneView | GET | Send confirmation | out of scope |
| `GET/POST /reset/<token>/` | PortalPasswordResetConfirmView | GET/POST | Reset the password | out of scope |
| `GET /reset/done/` | PortalPasswordResetCompleteView | GET | Password reset | out of scope |

---

## Functional requirements (FR)

### FR-01 — Display for an unauthenticated user
The system must display the login form when the user reaches `GET /login/` or `GET /` with no active session.

**Verifiable by:** a browser with no session → the `/login/` route → the form visible.

### FR-02 — Redirection of an already-authenticated user
When the user already has an active session (`portal_account` or `portal_is_technical_admin`), the system must automatically redirect to `/dashboard/` without showing the form.

**Verifiable by:** log in → go back to `/login/` → it must redirect, not show the form.

### FR-03 — Form fields
The form must display two fields with visible labels:
- `CPF ou acesso técnico` (`CPF or technical access`) (the `identifier` field)
- `Senha` (`Password`) (the `password` field)

The `autofocus`, `autocomplete`, and `placeholder` attributes of `PortalAuthenticationForm` must be preserved.

**Verifiable by:** visual inspection and inspection of the rendered HTML.

### FR-04 — Submission and authentication
- The form must be submitted through `POST` with a mandatory CSRF token.
- On success, redirect to the query string's `next` value, or to `/dashboard/`.
- On failure, re-display the form with visible non-field errors.

**Verifiable by:** POST with an invalid credential → the form re-displayed with the error.

### FR-05 — Field and non-field errors
- Individual field errors must appear below the corresponding field.
- Non-field errors (invalid credentials, pending payment) must appear above the fields with visual emphasis and `role="alert"`.

**Verifiable by:** an invalid POST → the error visible in the right place.

### FR-06 — Django messages
Session messages (e.g. a redirect due to a pending payment) must be displayed before the form.

**Verifiable by:** a session with a pending message → the message visible when the login renders.

### FR-07 — Password recovery link
The form must display a link with the text `Esqueceu sua senha?` (`Forgot your password?`) pointing to `/password-reset/`.

**Verifiable by:** visual inspection and inspection of the rendered HTML.

### FR-08 — Theme toggle
- The screen must provide a light/dark toggle button.
- The initial theme respects `localStorage["lv-theme"]` or, in its absence, `prefers-color-scheme`.
- The preference must persist after a reload through `localStorage`.

**Verifiable by:** clicking the button → the theme changes; reload → the theme persists.

### FR-09 — Password visibility
The password field must have a toggle button that shows/hides the content (toggling `type="text"` / `type="password"`).

**Verifiable by:** clicking the eye button → the field toggles between text and dots.

### FR-10 — The `next` parameter
When present in the query string, the `next` value must be propagated into the form's `action` so it is sent with the POST.

**Verifiable by:** `GET /login/?next=/home/student/` → the form's action contains `?next=/home/student/`.

---

## Non-functional requirements (NFR)

### NFR-01 — Responsiveness
- **Mobile (up to 639px):** a single-column layout; the logo centered at the top; the form below with a controlled width.
- **Desktop (768px+):** a two-column layout — the brand panel on the left, the form on the right.

### NFR-02 — Light and dark themes
- Every CSS token of the `UI-SCREEN-CONTRACT.md` contract must be used.
- No color hardcoded outside the tokens.
- Minimum text contrast: WCAG AA (4.5:1 for normal text).

### NFR-03 — Accessibility
- Visible labels associated through `for`/`id`.
- Visible focus on every control (`:focus-visible` with `--focus-ring`).
- Buttons with a descriptive `aria-label`.
- Errors with `role="alert"`.
- Minimum touch target: 44×44px (WCAG 2.5.8).

### NFR-04 — Performance
- CSS loaded from an external file at `static/system/css/auth/login.css`.
- JavaScript loaded with `defer` from an external file at `static/system/js/auth/login.js`.
- No inline CSS or JavaScript.

### NFR-05 — Security
- `{% csrf_token %}` mandatory in the POST form.
- No credentials or secrets in HTML/JavaScript.
- No `innerHTML` with user data.
- The password input with `autocomplete="current-password"`.

### NFR-06 — LV visual identity
- The LV logo prominently visible.
- Palette: black/graphite base, LV red as the accent.
- No generic gradients.

### NFR-07 — Template autonomy
- The login screen does not inherit `base.html` (it does not exist yet).
- It is a complete, self-sufficient HTML document.

---

## Scope of this delivery

- [x] `system/urls.py` — cleanup to keep only the authentication and home routes
- [x] `docs/UI-SCREEN-CONTRACT.md` — full rewrite of the visual contract
- [x] `docs/prd/PRD-030-login-screen.md` — this document
- [x] `templates/login/login_form.html` — a standalone login template
- [x] `static/system/css/auth/login.css` — CSS with light/dark tokens
- [x] `static/system/js/auth/login.js` — theme + password visibility

---

## Out of scope

- The password recovery templates (`password_reset_*.html`)
- The registration template (`register.html`)
- `base.html` and the global shell
- The home dashboards (admin, back office, instructor, student)
- Any other module of the system

---

## Impacted files

| File | Operation |
|---|---|
| `system/urls.py` | modified |
| `docs/UI-SCREEN-CONTRACT.md` | rewritten |
| `docs/prd/PRD-030-login-screen.md` | created |
| `templates/login/login_form.html` | created |
| `static/system/css/auth/login.css` | created |
| `static/system/js/auth/login.js` | created |

---

## Risks and edge cases

- **TemplateDoesNotExist after login:** `DashboardRedirectView` redirects to homes with no template. Expected at this stage.
- **Open redirect in `next`:** `PortalLoginView` uses the `next` parameter without validating `is_safe_url`. The risk is documented as a security pending item for a future PRD.
- **Missing logo:** if `logo-lv-bjj.png` is unavailable, the screen must still render correctly with the `alt` visible.

---

## Rules and constraints

- SDD before code
- TDD for the implementation (the existing view tests must pass)
- No colors hardcoded outside the tokens
- No `innerHTML` with user data
- No migrations (no model change)
- Mandatory full reading before editing
- Mandatory visual validation (Playwright)

---

## Plan

- [x] 1. Context and full reading (views, forms, urls, settings, contract)
- [x] 2. Clean up `system/urls.py`
- [x] 3. Rewrite `UI-SCREEN-CONTRACT.md`
- [x] 4. Create this PRD
- [x] 5. Create `login_form.html`
- [x] 6. Create `login.css`
- [x] 7. Create `login.js`
- [ ] 8. `manage.py check` — 0 issues
- [ ] 9. `manage.py collectstatic --noinput`
- [ ] 10. Desktop and mobile visual validation
- [ ] 11. Console and terminal check

---

## Acceptance criteria

- [ ] `GET /login/` renders with no 500 error
- [ ] `POST /login/` with an invalid credential re-displays the form with a visible error
- [ ] `POST /login/` with a valid credential redirects to `/dashboard/`
- [ ] Light theme: correct background, text, and border tokens
- [ ] Dark theme: every token replaced correctly
- [ ] The theme preference persists after a reload (localStorage)
- [ ] The password visibility button toggles the field correctly
- [ ] The `Esqueceu sua senha?` (`Forgot your password?`) link present and pointing to `/password-reset/`
- [ ] Desktop layout: two columns (brand + form)
- [ ] Mobile layout (< 640px): one column, logo + form stacked
- [ ] `manage.py check` — 0 issues
- [ ] Browser console — no JavaScript errors

---

## Visual validation

### Desktop
- [ ] The brand panel visible on the left with the LV logo
- [ ] The form panel on the right, vertically centered
- [ ] Fields with a visible label, placeholder, and focus
- [ ] The `Entrar` (`Sign in`) button with the LV red accent
- [ ] The `Esqueceu sua senha?` (`Forgot your password?`) link below the button
- [ ] The theme button in the top-right corner

### Mobile
- [ ] The logo centered at the top
- [ ] The form below, at an appropriate width
- [ ] Fields with a comfortable minimum touch target
- [ ] No element clipped or hidden

### Browser console
- [ ] No JavaScript errors
- [ ] No 404s on static assets

### Terminal
- [ ] No stack trace in runserver

---

## ORM validation

Not applicable to this screen. Authentication happens through `authenticate_portal_identity` in `system/services/`, with no direct database access in the view.

---

## Quality validation

- [ ] No color hardcoded outside the CSS tokens
- [ ] No `innerHTML` with user data
- [ ] No inline CSS or JavaScript in the template
- [ ] No unnecessary comment in the code

---

## Evidence

(to be filled in after validation)

---

## Implemented

- `system/urls.py` — cleaned down to 13 routes (auth + homes)
- `docs/UI-SCREEN-CONTRACT.md` — rewritten from scratch with tokens, inventory, and rules
- `templates/login/login_form.html` — standalone template created
- `static/system/css/auth/login.css` — CSS with light/dark tokens created
- `static/system/js/auth/login.js` — theme and password JavaScript created

---

## Deviations from plan

(to be filled in)

---

## Pending

- Validating the `next` parameter against safe URLs (a potential open redirect)
- The password recovery templates (a future PRD)
- The registration template (a future PRD)
- The global `base.html` shell and topbar (a future PRD)
- The home dashboards for every profile (future PRDs)
