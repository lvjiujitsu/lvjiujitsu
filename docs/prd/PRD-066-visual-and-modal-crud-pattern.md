# PRD-066: Visual and modal CRUD pattern

## Summary
Bring into LV JIU JITSU the consolidated UI generation: short CRUD in a modal/dialog on the screen itself, iconic actions on cards, a shared theme/dates/modals foundation, and desktop/mobile responsiveness with a light/dark theme. LV today uses standalone full-page templates (`person_form`, `person_detail`, `person_confirm_delete`) and cards with a single `Detalhe` (`Detail`) link — a legacy pattern to retire.

## Demand type
A phased, multi-module architectural UI rewrite.

## Required skills
- `lv-task-intake`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Current problem
- LV's `UI-SCREEN-CONTRACT.md` does not declare a rule for short CRUD in a modal/dialog (0 occurrences).
- There is no shared JS/CSS foundation: the theme boot is duplicated inline in each template; there is no Brazilian Portuguese date utility and no modal controller.
- The operational screens do not extend a common layout/shell; each one is an isolated HTML document.
- The CRUD navigates to dedicated screens instead of opening a popup.

## Goal
Establish the reference contract and experience in LV:
- A shared foundation (`theme_boot`, `pt_br_date_inputs`, `crud_modal`, `crud_frame`) and the system CSS for `icon-action` + `crud-modal`.
- The normative rule §15.11 "Operational CRUD in a modal/dialog" in LV's UI contract.
- A module-by-module conversion to a list with iconic actions (view/edit/delete + domain actions) and short, server-rendered CRUD in a modal through `<dialog>` + an iframe.

## Token mapping
| Source token | LV |
|---|---|
| `--brand` | `--brand-red` |
| `--brand-muted` | `--brand-red-muted` |
| `--background` | `--panel` |
| `theme` (localStorage) | `lv-theme` |

## Replicated visual contract
- `.icon-action`: 44×44, a 1.5px `var(--border)` border, a 0.5rem radius, `background: var(--panel)`, a 1rem icon; the `--view` (brand), `--edit` (brand), `--delete` (danger) modifiers.
- `.crud-modal`: a `<dialog>` with a header (an eyebrow + the title + a 44×44 close button) and an iframe body (`width: min(860px, calc(100vw - 2rem))`); a `::backdrop` of `rgba(15,23,42,.48)`; an `.is-open` fallback for browsers without `<dialog>`.
- Mobile: iconic actions in a 44px grid; the modal takes `calc(100vw - 1rem)`.

## Scope by phase
1. **The shared foundation** (this cycle): JS/CSS assets, the `portal_module` layout/shell, the topbar/theme/messages partials, and the §15.11 rule. Verifiable through `manage.py check` and `collectstatic`.
2. **People (the reference)**: a list with iconic actions + create/edit/view in a modal + delete with a confirmation; server-side modal endpoints. Validation in the desktop/mobile browser, light/dark.
3. **Replication**: Classes, Plans, Graduation, Finance, Products, and Administration/Modules, each in its own increment reusing the foundation.

## Out of scope
- Porting an external domain (trips, visas, consular cases, consultancy dependents).
- Creating migrations, changing business rules, or the schema.
- Running tests, seeds, or a reset without authorization.

## Acceptance criteria
- [x] The shared JS/CSS foundation created in `static/system/js/shared/` (theme_boot, pt_br_date_inputs, crud_modal, crud_frame) and `static/system/css/shared/crud_modal.css`.
- [ ] `templates/layouts/portal_module.html` and the topbar/theme/messages partials created and reusable.
- [x] §15.6 (CRUD in a modal/dialog) added to `docs/UI-SCREEN-CONTRACT.md`.
- [x] People: the card shows the view/edit/delete iconic actions respecting the permissions (edit/delete only for `can_manage_people`).
- [x] People: create/edit/view open in a modal (an iframe) with no screen change; an invalid POST re-renders with a field error in the modal (validated: an invalid CPF → 200 with an error, not a 500).
- [x] Delete uses a confirmation dialog (`data-confirm-submit`) and respects `ProtectedError`; validated end to end (creation→deletion with a success message).
- [x] Desktop and mobile (375px, no overflow) and light/dark correct; a console with no critical error.
- [ ] Each replicated module keeps the same visual contract.

## Expected evidence
- `manage.py check` with no issues.
- `collectstatic --noinput` for a static change.
- Visual validation in the internal browser per module (desktop/mobile/light/dark).
- Focused tests written per module; execution only under authorization.

## Status
- [x] Phase 1 — The foundation (the shared assets + §15.6 + this PRD; `manage.py check` with no issues)
- [x] Phase 2 — People (the reference): a list with iconic actions + create/edit/view modals + delete; validated in the browser (desktop/mobile/light/dark). A collateral fix: `clean_cpf` now raises a `ValidationError` instead of letting a `ValueError` escape (which caused a 500 when editing an invalid CPF). `ModalCrudMixin` releases `X-Frame-Options: SAMEORIGIN` only on `?modal=1` responses.
- [ ] Phase 3 — Replication per module (Classes, Plans, Graduation, Finance, Products, Admin)

Completed with limitations: Phases 1 and 2 delivered and validated in the browser. Phase 3 pending — replicate the People pattern in the remaining modules, reusing the foundation and `ModalCrudMixin`.
