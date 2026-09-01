# PRD-006: Standardize the plan change screen with the portal design system

## Summary of the implementation
Redesign the `billing/plan_change_select.html` screen to use the same design system applied to the class and materials screens (`class-catalog.css` + `billing.css`), grouping plans by type (individual / family) in a readable list with a collapsible proration detail, eliminating the confusing grid of flat cards.

## Demand type
Targeted UX fix / visual standardization

## Current problem
The screen displays 11+ plans in a 3-column `grid` with the full proration detail always expanded and no visual hierarchy at all. The result is confusing: the user cannot quickly identify what they are choosing, which option is an upgrade, which is a downgrade, and how much they will pay.

## Goal
- Organize plans into two semantic groups: **`Planos Individuais`** (**`Individual Plans`**) and **`Planos Família`** (**`Family Plans`**) (through `is_family_plan`)
- Display each plan as a list card (`info-record-list` / `record-card-catalog`) with name, price, cycle, and a type badge (`Upgrade`/`Downgrade`/`Gratuito` — `Free`)
- Show the net amount (difference) immediately on the card
- Put the detailed proration breakdown in a collapsible `<details>` (`catalog-dropdown`)
- The `Trocar para este plano` (`Switch to this plan`) button stays visible outside the dropdown
- No migration, no business logic change, no service change

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `templates/billing/plan_change_select.html`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/models/plan.py`
- `static/system/css/billing/billing.css`
- `static/system/css/portal/class-catalog.css`
- `templates/products/product_store.html`
- `docs/prd/PRD-002-simplify-class-display-in-registration.md`
- `docs/prd/PRD-004-correction-of-catalogue-of-materials-by-variant.md`

### Adjacent files consulted
- `system/views/__init__.py` (export check)
- `system/models/membership.py` (through grep for MembershipStatus)
- `system/urls.py` (route check)

### Internet / official documentation
- Not applicable: a purely template/CSS/view change using patterns already established in the project.

### MCPs / tools verified
- PowerShell shell — ok — file reading and grep
- Playwright / browser — mandatory for post-implementation visual validation

### Limitations found
- No critical limitation. Playwright is available for the mandatory visual validation.

## Execution prompt
### Persona
Development agent specializing in server-rendered Django + a CSS design system, following SDD + TDD.

### Action
Redesign the plan selection screen (`plan_change_select.html`) and adjust the corresponding view to group plans by `is_family_plan`, without changing services, models, or the business flow.

### Context
The student portal has standardized screens (classes during registration, the materials shop) using `class-catalog.css` with the patterns `info-record-list`, `record-card-catalog`, `catalog-cluster-card`, `catalog-dropdown`. The plan change screen (`/plan/change/`) uses an old, non-standardized grid that confuses the user. The `PlanChangeSelectView` view already computes proration and passes `plans_with_proration`; it only needs to also pass `plan_groups` (a list grouped by `is_family_plan`). The template must be rewritten using the established visual patterns.

### Constraints
- no hardcoded business rules
- no error masking
- no migrations
- mandatory full reading (already done)
- mandatory in-browser visual validation
- Brazilian Portuguese interface

### Acceptance criteria
- [ ] The `/plan/change/` screen loads without a 500 error or stack trace (verifiable: terminal)
- [ ] Plans appear grouped as `Planos Individuais` (`Individual Plans`) and `Planos Família` (`Family Plans`) (verifiable: visual + view test)
- [ ] Each card displays: plan name, price + cycle, `Upgrade`/`Downgrade`/`Gratuito` (`Free`) badge, net amount, and a `Trocar para este plano` (`Switch to this plan`) button (verifiable: visual)
- [ ] The proration breakdown (remaining credit, prorated cost) sits in a collapsible `<details>` (verifiable: visual)
- [ ] Plans without `is_family_plan=True` appear in the Individual group; those with `is_family_plan=True` in the Family group (verifiable: view unit test)
- [ ] The `Trocar para este plano` (`Switch to this plan`) button navigates correctly to `/plan/change/<id>/confirm/` (verifiable: visual)
- [ ] `manage.py check` passes with no errors (verifiable: terminal)
- [ ] `manage.py test --verbosity 2` passes with no failures (verifiable: terminal)
- [ ] Browser console with no critical JavaScript errors (verifiable: DevTools)
- [ ] The `?v=` of `billing.css` updated in the template (verifiable: code)

### Expected evidence
- output of `manage.py test --verbosity 2` with 0 failures
- output of `manage.py check` with no errors
- screenshot or visual description of the screen with two plan groups
- browser console with no errors
- terminal with no stack traces

### Output format
Implemented code (view + template + CSS) + tests + validation evidence

## Scope
- `system/views/plan_change_views.py`: add grouping by `is_family_plan` to the context
- `templates/billing/plan_change_select.html`: rewrite using the design system
- `static/system/css/billing/billing.css`: add helper classes for the action row and net value; version bump
- `system/tests/test_views.py`: add/adjust `PlanChangeSelectView` tests to cover the grouping

## Out of scope
- Changes to `plan_change_confirm.html`
- Changes to proration services
- Changes to models or migrations
- Changes to the payment confirmation screen
- New plan filtering or search behavior

## Impacted files
| File | Type of change |
|---|---|
| `system/views/plan_change_views.py` | add `plan_groups` to the context |
| `templates/billing/plan_change_select.html` | full template rewrite |
| `static/system/css/billing/billing.css` | new classes + `?v=` bump |
| `system/tests/test_views.py` | grouping coverage in the view |

## Risks and edge cases
- User with no active plan: the screen already handles this with `plans_with_proration = []`; the groups simply stay empty and the fallback message is displayed
- All plans are individual (no family ones): the `Planos Família` (`Family Plans`) group is not rendered (the `{% if group.entries %}` condition)
- `calculate_plan_change` may raise `PlanChangeError` for some plan: already handled with `continue` in the view — that plan does not enter the list

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations (project policy)
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling (no model change)
- [x] 3. Tests (Red) — cover the grouping in the view
- [x] 4. Implementation (Green) — view + template + CSS
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation (test + check + visual + console)
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
- Two separate groups: `Planos Individuais` (`Individual Plans`) and `Planos Família` (`Family Plans`)
- Cards in a readable list with name, price, badge, net, button
- The collapsible detail dropdown works

### Mobile
- Single-column list with no horizontal overflow

### Browser console
- No critical JavaScript errors

### Terminal
- No stack trace in runserver

## ORM validation
### Database
- No schema change

### Shell checks
- `SubscriptionPlan.objects.filter(is_active=True).count()` returns the available plans
- `SubscriptionPlan.objects.filter(is_active=True, is_family_plan=True).count()` returns only the family ones

### Flow integrity
- Navigation to `/plan/change/<id>/confirm/` remains functional

## Quality validation
### No hardcoding
- Grouping through the model's `is_family_plan`, not by a hardcoded string
### No brittle conditional structures
- Groups generated dynamically; if a group is empty, it is not rendered
### No `except: pass`
- Not applicable to this change
### No error masking
- Proration errors remain handled with `continue` (behavior preserved)
### No unnecessary comments or docstrings
- No unnecessary comments added

## Evidence
- `manage.py test --verbosity 2`: 201 tests, 0 failures, 0 errors
- `manage.py check`: System check identified no issues (0 silenced)
- `manage.py collectstatic --noinput`: 1 file copied, 161 unchanged
- 6 new unit tests passing in `PlanChangeSelectViewGroupingTest`

## Implemented
- `system/views/plan_change_views.py`: `plan_groups` added to the context with grouping by `is_family_plan`
- `templates/billing/plan_change_select.html`: rewritten with `catalog-cluster-card`, `info-record-list`, `record-card-catalog`, and a collapsible `catalog-dropdown`
- `static/system/css/billing/billing.css`: classes `.plan-change-action-row`, `.plan-change-net`, `.plan-change-net-label`, `.plan-change-net-value` added; version bumped to `?v=20260421b`
- `system/tests/test_views.py`: class `PlanChangeSelectViewGroupingTest` with 6 tests (grouping, filtering, omission of an empty group, label rendering, unauthenticated access)

## Deviations from plan
None.

## Pending
- Visual validation with Playwright (mandatory per AGENTS.md §17) — to be performed by the developer after starting the local server
