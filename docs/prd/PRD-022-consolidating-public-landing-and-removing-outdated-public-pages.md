# PRD-022: Consolidate the public landing page and remove outdated public pages

## Summary of the implementation

Reduce the portal's public area to just three essential functions — login, registration, and contact — eliminating the intermediate menu, the public plan and materials catalog pages, and the informational classes page. The new landing page (the site root, `/`) becomes the login form itself, with two additional CTAs: `Criar conta` (`Create account`) and `Falar com a LV` (`Talk to LV`) (WhatsApp).

## Demand type

Architectural refactoring with removal of public surface. Changes to URLs, views, templates, tests, and cross-references. No schema change.

## Current problem

The public area today carries five different paths (Login, Registration, Classes and Schedules, Materials, Plans) served by distinct views (`PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView`, `PortalLoginView`, `PortalRegisterView`) and legacy URL names (`templates/login/login.html`, `legacy-home`, `legacy-info`...). This:

1. **Dilutes lead capture.** The user lands on the home and has 5 buttons to choose from; the "buy/sign up" path gets lost.
2. **Keeps dead code.** `PlanCatalogView` and `ProductCatalogView` display redundant information: plans already appear inside the registration wizard and in the plan change flow; materials live in the authenticated `/store/`. The `/info/` page was superseded by the calendar.
3. **Pollutes legacy URLs.** Four `templates/login/...` routes became live aliases for compatibility — now obsolete.

## Goal

- Make the site's landing screen the login form itself with two clear CTAs: registration and WhatsApp.
- Remove every public page that has no direct lead-capture or authentication function.
- Clean up the `legacy-*` URL names, replacing them with the canonical ones.

## Context Ledger

### Files read in full

- [system/urls.py](system/urls.py)
- [system/views/auth_views.py](system/views/auth_views.py)
- [system/views/plan_views.py](system/views/plan_views.py)
- [system/views/product_views.py](system/views/product_views.py)
- [system/views/__init__.py](system/views/__init__.py)
- [templates/login/login.html](templates/login/login.html)
- [templates/login/login_form.html](templates/login/login_form.html)
- [templates/login/info.html](templates/login/info.html)
- [templates/login/register.html](templates/login/register.html)
- [templates/login/password_reset_*.html] (4 files)
- [templates/plans/plan_catalog.html](templates/plans/plan_catalog.html)
- [templates/products/product_catalog.html](templates/products/product_catalog.html)
- [templates/home/student/dashboard.html](templates/home/student/dashboard.html)
- [system/views/payment_views.py](system/views/payment_views.py)
- Tests: `test_views.py`, `test_plan_views.py`, `test_product_views.py`, `test_class_portal_views.py`

### Adjacent files consulted

- `static/system/js/auth/registration-wizard-clean.js` (indirect reference to `legacy-*` — there is none)

### Internet / official documentation

- N/A (a purely internal refactoring).

### MCPs / tools verified

- All local tools (Read, Grep, Glob, Edit, Write) — working.

### Limitations found

- None. A 100% internal refactoring.

## Execution prompt

### Persona

Senior Django agent in control-first mode with SDD + TDD.

### Action

Remove four obsolete public views (`PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView`), their templates and URLs, and make the site root serve `PortalLoginView` with two new CTAs (registration + WhatsApp).

### Context

The system is the LV Jiu Jitsu academy portal. The authenticated area (dashboard, store, plan-change, calendar) already covers every operational function. The public area only needs to capture leads and authenticate.

### Constraints

- no hardcoded secrets
- no error masking
- no migrations
- mandatory full reading (completed above)
- preserve the canonical URL `name`s (`root`, `login`, `register`)
- replace every `legacy-*` referenced in the project with the canonical names before removing the routes
- the WhatsApp number `+55 62 99987-6471` (link `https://wa.me/5562999876471`) kept as it was on the old home

### Acceptance criteria

- [ ] `/` renders `templates/login/login_form.html` (verifiable: `manage.py test` + a GET on the root)
- [ ] `login_form.html` has a visible `Criar conta` (`Create account`) button linking to `/register/`
- [ ] `login_form.html` has a visible `Falar com a LV` (`Talk to LV`) button linking to `https://wa.me/5562999876471`
- [ ] `/info/`, `/plans-catalog/`, `/materials/`, and the 4 `templates/login/...` routes return 404 (verifiable: assertions in tests)
- [ ] The templates `login.html`, `info.html`, `plan_catalog.html`, `product_catalog.html` no longer exist in the repository (verifiable: `Glob`)
- [ ] The views `PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView` do not exist in `system/views/` (verifiable: `Grep`)
- [ ] No template or Python code references `legacy-home`, `legacy-login-form`, `legacy-register`, `legacy-info`, `info`, `plan-catalog`, `product-catalog` (verifiable: `Grep`)
- [ ] `manage.py test --verbosity 2` passes with 0 failures
- [ ] `manage.py check` passes with no new warnings

### Expected evidence

- passing tests
- a clean browser console on the root
- a screenshot of the new landing page with 3 elements: form, registration CTA, WhatsApp CTA

### Output format

Code + tests + report.

## Scope

### Removal
1. The `PortalHomeView` view in `system/views/auth_views.py`.
2. The `PortalInfoView` view in `system/views/auth_views.py`.
3. The `PlanCatalogView` view in `system/views/plan_views.py` (and the `_build_plan_groups` helper and the `PUBLIC_CATALOG_GROUP_ORDER` and `AUDIENCE_LABELS` constants when unused elsewhere).
4. The `ProductCatalogView` view in `system/views/product_views.py` (preserving `_build_product_groups` when used by `ProductStoreView`).
5. The `templates/login/login.html` template.
6. The `templates/login/info.html` template.
7. The `templates/plans/plan_catalog.html` template.
8. The `templates/products/product_catalog.html` template.
9. The `/` URL pointing to `PortalHomeView` → switch to `PortalLoginView`.
10. The `/info/` URL.
11. The `/plans-catalog/` URL.
12. The `/materials/` URL.
13. The legacy URLs `templates/login/login.html`, `templates/login/login-form.html`, `templates/login/cadastro.html`, `templates/login/informacoes.html`.
14. The corresponding exports in `system/views/__init__.py`.

### Reference replacement
15. Templates: `legacy-home` → `root`, `legacy-login-form` → `login`, `legacy-register` → `register`.
16. Python code (auth_views, payment_views): `legacy-login-form` → `login`.
17. Tests: likewise.
18. `templates/home/student/dashboard.html`: the `Ver planos` (`View plans`) link now points to `system:plan-change-select` (an authenticated student already uses that flow).

### UX update
19. `templates/login/login_form.html`:
    - Remove the `Voltar` (`Back`) button (the root has nowhere to go back to).
    - Add a block below the form with the link `Ainda não possui cadastro? **Criar conta**` (`Don't have an account yet? **Create account**`) → `/register/`.
    - Add a `Falar com a LV` (`Talk to LV`) button (the same style as the old landing page) → `https://wa.me/5562999876471`.
    - Bump the CSS cache-busting.

### Tests
20. Remove tests for the pages that are gone.
21. Replace `legacy-*` references in the tests with the canonical names.
22. Add a test of the registration and WhatsApp CTAs on the new landing page.

## Out of scope

- The shop on the authenticated home with pre-orders + a notification when the product arrives — goes to PRD-009.
- Any CSS/JS change beyond the cache bump in `login.css`.

## Impacted files

- [system/urls.py](system/urls.py)
- [system/views/auth_views.py](system/views/auth_views.py)
- [system/views/plan_views.py](system/views/plan_views.py)
- [system/views/product_views.py](system/views/product_views.py)
- [system/views/payment_views.py](system/views/payment_views.py)
- [system/views/__init__.py](system/views/__init__.py)
- [templates/login/login_form.html](templates/login/login_form.html)
- [templates/login/register.html](templates/login/register.html)
- [templates/login/password_reset_form.html](templates/login/password_reset_form.html)
- [templates/login/password_reset_done.html](templates/login/password_reset_done.html)
- [templates/login/password_reset_complete.html](templates/login/password_reset_complete.html)
- [templates/login/password_reset_confirm.html](templates/login/password_reset_confirm.html)
- [templates/home/student/dashboard.html](templates/home/student/dashboard.html)
- [system/tests/test_views.py](system/tests/test_views.py)
- [system/tests/test_plan_views.py](system/tests/test_plan_views.py)
- [system/tests/test_product_views.py](system/tests/test_product_views.py)
- [system/tests/test_class_portal_views.py](system/tests/test_class_portal_views.py)
- **Delete:** `templates/login/login.html`, `templates/login/info.html`, `templates/plans/plan_catalog.html`, `templates/products/product_catalog.html`

## Risks and edge cases

- **External bookmarks** pointing to `/info/`, `/plans-catalog/`, `/materials/`, or `templates/login/...` will 404. Acceptable: those pages were informational and will be replaced by the registration/plan change wizard.
- **SEO**: no known external index for those pages. There is no 301 redirect plan.
- **Password reset templates** keep linking to login after a reset — only the `name` changes (from `legacy-login-form` to `login`).

## Rules and constraints

- SDD before code (this PRD)
- TDD, adjusting the tests alongside the removals
- no hardcoding
- no masking
- no migration

## Plan

- [x] 1. Context and full reading
- [ ] 2. Replace `legacy-*` with the canonical names everywhere (templates + Python + tests)
- [ ] 3. Update `login_form.html` with the new CTAs and remove the Back button
- [ ] 4. Switch the `/` route to `PortalLoginView`
- [ ] 5. Remove the `PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView` views + exports
- [ ] 6. Remove the `/info/`, `/plans-catalog/`, `/materials/` URLs and the 4 legacy ones
- [ ] 7. Delete the obsolete templates (4)
- [ ] 8. Update `dashboard.html` (plan-catalog link → plan-change-select)
- [ ] 9. Clean up the tests
- [ ] 10. Bump the CSS/JS cache
- [ ] 11. `manage.py check` validation
- [ ] 12. Final cleanup
- [ ] 13. Report

## Visual validation

### Desktop
- `/` shows the login form + the registration CTA + the WhatsApp CTA
- `/login/` keeps responding (the same view, now also on the root)
- `/register/` stays intact
- `/info/`, `/plans-catalog/`, `/materials/` return 404

### Mobile
- the same screen in a viewport ≤ 480px

### Console
- no asset 404s
- no JavaScript errors

## ORM validation

### Database
- No schema change.

### Shell checks
- No data touched.

### Flow integrity
- Login + registration + password recovery keep working intact.

## Quality validation

### No hardcoding
- The WhatsApp number appears only in `login_form.html` as a link, aligned with the old landing page.

### No brittle conditional structures
- A subtractive refactoring.

### No `except: pass`
- Nothing introduced.

### No error masking
- Nothing.

### No unnecessary comments or docstrings
- Nothing.

## Evidence

(to be filled in after implementation)

## Implemented

(to be filled in after implementation)

## Deviations from plan

(to be filled in after implementation)

## Pending

- PRD-009: the shop on the authenticated home with pre-orders + product arrival notification.
