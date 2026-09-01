# PRD-067: People CSS parity — filters, KPIs, rows, and responsiveness

## Summary
Fix the People module's visual acceptance to reach parity with the reference hub. The first pass (PRD-066) delivered the modal/iconic actions pattern, but the CSS of the rows (cards), the filters, and the responsiveness diverged from the contract, and the KPI strip was kept — in conflict with the screen contract's anti-KPI governance.

## Demand type
A UI/CSS fix with reference parity + governance.

## Required skills
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Current problem
Comparing `static/system/css/people/people.css` (LV) with `static/system/css/client/clients.css` + `portal/modules.css`:
1. `.person-card` uses `align-items: center`; the standard calls for `flex-start` (the rows misalign when there are badges + meta).
2. `.person-card__name` and `.person-card__meta` truncate with `nowrap/ellipsis`; the standard lets them wrap (`line-height` 1.3/1.45, `overflow-wrap: anywhere`).
3. `.person-card__avatar` is grey (`surface-soft`/`muted`); the standard uses a branded avatar (`brand-muted`/`brand-strong`).
4. `.icon-actions` diverges: the standard is `justify-content: flex-end; gap: 0.375rem; flex-wrap: nowrap`.
5. `.filter-input/.filter-select` have `height: 36px`; the standard uses `44px`. `.filter-field` receives a `max-width: 200px` the contract does not foresee.
6. There is no mobile rule for the rows: at ≤768px the card must `flex-wrap: wrap` and the actions must become a grid aligned after the avatar (`margin-left: calc(40px + 1rem)`). In LV the actions end up compressed/clipped.
7. A KPI strip (6 cards) present without a request — the contract forbids an unrequested KPI in an operational hub.

## Goal
- Rewrite the `card/row`, `filters`, and `responsiveness` blocks of `people.css`, reproducing the reference contract with LV's tokens.
- Align the foundation's `.icon-actions` (`crud_modal.css`) with the contract.
- Remove People's KPI strip (the template + the context/helper in the view).
- Record the anti-KPI rule in `UI-SCREEN-CONTRACT.md`.

## Token mapping
`--brand`→`--brand-red`, `--brand-strong`→`--brand-red-strong`, `--brand-muted`→`--brand-red-muted`.

## Out of scope
- Removing KPIs from other modules (Home, etc.) — a task of its own.
- Changing the People domain or logic beyond the KPI context.
- Migrations, seeds, a reset.

## Acceptance criteria
- [x] `.person-card` aligns to the top (`flex-start`); the name and meta wrap without truncating.
- [x] The avatar uses the brand (`backgroundColor rgba(224,34,68,.12)` / `color rgb(196,18,48)` confirmed through the computed style).
- [x] `.icon-actions` = `flex-end`, `gap: 0.375rem`, `nowrap` (desktop).
- [x] The filters with 44px inputs (computed) and with no artificial `max-width`.
- [x] Mobile (≤768px): the card `flex-wrap: wrap`, the actions in a 44px grid with `margin-left: 56px`; no horizontal overflow (confirmed by the computed style).
- [x] The KPI strip removed from People (the template + the view + the orphaned CSS); `UI-SCREEN-CONTRACT.md §15.7` declares the anti-KPI rule.
- [x] Validation in the browser: desktop and mobile, light and dark, a console with no errors.

## Expected evidence
- `manage.py check` with no issues ✓.
- `collectstatic` applied ✓.
- Tests: `test_person_delete`, `test_admin_hubs_contract`, `test_home_dashboard` → 10 tests OK (no regression from the KPI removal/view adjustment).
- Desktop/mobile/light/dark screenshots with parity.

## Status
- [x] Completed and validated in the browser (desktop/mobile/light/dark) + green tests.
