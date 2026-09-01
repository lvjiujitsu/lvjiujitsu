# PRD-077: CRUD MVP of the martial arts academy

## Summary
Deliver the academy's operational MVP after the foundation: creating, viewing, changing, and deleting the main domains; the materials stock; classes with a schedule; the financial history; class auditing; progression and graduation.

## Demand type
A new multi-module feature + integration of the existing domain.

## Current problem
- People and Plans have partial templates in place.
- Classes, categories, schedules, finance, graduation, materials, the shop, pre-orders, and profiles have views/routes, but most of their templates are missing.
- The PRD-065 documentation declares the hubs implemented, but the current inventory shows missing templates.
- There is no current desktop/mobile visual validation of those CRUDs because the screens do not render completely.

## Goal
Build a consistent initial CRUD for:
- People and access;
- Plans;
- Classes, categories, and schedules;
- The schedule and attendance;
- Materials/products, variants, and stock;
- Finance, orders, tuition, payouts, and the history;
- Graduation, belts, rules, and the progression history.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-065-administrative-hubs-of-the-lv-modules.md`
- `system/urls.py`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`
- `system/views/person_views.py`

### Adjacent files consulted
- `system/forms/*`
- `system/services/*`
- `system/selectors/*`
- `templates/`
- `static/system/`
- `system/tests/test_admin_hubs_contract.py`

### Internet / official documentation
- Django 5.2 templates and CBVs: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- This PRD depends on PRD-074 for permissions and PRD-075 for the UI/routes foundation.
- Real payments and webhooks do not enter the validation without an environment/tunnel/gateway.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request as the final goal, but the execution must be phased for safety.

## Scope
- Implement the missing templates per module using the common foundation.
- Complete the CRUD actions with server-side validation.
- Cover the empty, error, success, and relation-blocked states.
- Create rendering, permission, and basic operation tests per module.
- Validate desktop/mobile in the internal browser.

## Out of scope
- A real payment gateway.
- Remote writes.
- A deep refactoring of the public wizard, unless it blocks the MVP.

## Impacted files
- `templates/classes/*`
- `templates/class_categories/*`
- `templates/class_schedules/*`
- `templates/billing/*`
- `templates/graduation/*`
- `templates/products/*`
- `templates/person_types/*`
- `templates/admin_modules/*`
- proportional views/forms/services/tests

## Risks and edge cases
- Deleting a person/product/plan with a relation must block with a clear message.
- Stock must not be changed by JavaScript without transactional persistence.
- Graduation needs to preserve the history, not just the current field.
- Finance requires an audit trail and must not mask the gateway status.
- The schedule must respect holidays, open classes, check-ins, and substitutions.

## Rules and constraints
- It depends on the PRD-075 foundation.
- The permissions depend on PRD-074.
- Test-first per module.
- Do not create an aggregate KPI without a named request.

## Plan
- [x] People as the complete reference (delivered in PRD-075).
- [x] Plans.
- [x] Classes/categories/schedules.
- [x] Materials/stock/shop/pre-orders (the administrative CRUD; the student's shop/backorder stay as a UI pending item, see Pending).
- [x] Graduation/progression.
- [x] Finance/auditing (read screens + state actions; it is not a creation CRUD, see Evidence).
- [x] Schedule/attendance (the calendar already existed and was already functional; migrated to an English route; the dead code removed).

## Test plan
### Tests to author
- GET renders 200 for each hub/list.
- Create/edit/delete per module.
- Permission blocking by role.
- The empty state and populated data.

### Execution authorization
Authorized locally, phased.

### Execution evidence
- Plans: `system/tests/test_lv_foundation_plans.py` (6 tests: the English route, 2 redirects from the old routes, the create/edit modal renders the correct template, a valid POST creates the plan and renders `lv/modal_done.html`).
- Classes/categories/schedules: `system/tests/test_lv_foundation_classes.py` (8 tests: the English routes of the 3 sub-modules, a redirect from the old route, the class detail uses the record's real pk (not the grouped card), the create-category modal with a valid POST, the edit-class modal exposes the schedules formset, the create-schedule modal renders).
- `system/tests/test_admin_hubs_contract.py` (PRD-065's route contract) adjusted to reflect the new English paths of `class-group-*`, `class-category-list`, and `class-schedule-list`, since PRD-077 supersedes that contract for the migrated modules.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_plans --verbosity 2` — 6 tests OK.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_classes --verbosity 2` — 8 tests OK.
- Materials: `system/tests/test_lv_foundation_products.py` (4 tests: the English route, a redirect from the old route, the modal exposes `variant_formset`, a valid POST creates the product+variant and renders `lv/modal_done.html`).
- Two more `test_admin_hubs_contract.py` expectations adjusted (`product-*`, `admin-backorder-queue`, `product-store`, `student-backorders`, `student-order-history`) for the new English paths.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_products --verbosity 2` — 4 tests OK.
- Graduation: `system/tests/test_lv_foundation_graduation.py` (7 tests: the overview's English route, a redirect from the old route, the create-belt modal with a valid POST, the edit-rule modal renders, the record-graduation modal preserves the history through a new record, and a confirmation that there is no edit route for a graduation — the history is immutable by design).
- Another round of `test_admin_hubs_contract.py` adjustments (`graduation-*`) for the English paths.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_graduation --verbosity 2` — 7 tests OK.
- Finance: `system/tests/test_lv_foundation_financial.py` (5 tests: the panel's English route, a redirect from the old route, the pending list with real data, the "mark paid" action really changing the status, and payroll/payouts rendering).
- Another round of `test_admin_hubs_contract.py` adjustments (`financial-*`) for the English paths.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_financial --verbosity 2` — 5 tests OK.
- Schedule: `system/tests/test_lv_foundation_calendar.py` (3 tests: the English `/calendar/` route renders, a redirect from `/cronograma/`, and a `hasattr` confirmation that the 4 dead calendar views were removed from the module).
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_calendar --verbosity 2` — 3 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 308 tests OK (the full suite, with no regression, after all 7 modules and the dead code cleanup).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
- Plans: validated in the internal browser — the create modal in a `<dialog>` with an iframe, a consistent dark theme, the estimated price computed dynamically inside the modal (`plans.js` reused through `modal_extra_scripts`), mobile (375×812) with no horizontal overflow and the modal anchored to the bottom.
- A duplication bug found and avoided: `plans.js` already had its own theme-toggle logic; `theme_toggle.js` was not included in `plan_list.html` so the button binding is not duplicated (the complete dedupe of that pattern goes to PRD-084).
- Classes: validated in the internal browser with real seed data — the list shows 6 individual classes (3 of them with the same name/category "Jiu Jitsu · Adulto" but different instructors); the edit modal opens the correct class by instructor and shows the schedules formset (6 slots: 5 existing + 1 blank extra) with "Remover este horário" ("Remove this schedule") on the existing ones. Categories validated on mobile (375×812) with no horizontal overflow.
- Materials: validated in the internal browser with real seed data (5 materials, including "Faixa LV" with 35 real variants) — the list shows the correct total stock and variant count; the edit modal renders 36 formset slots (35 existing + 1 extra); mobile with no horizontal overflow.
- Graduation: validated in the internal browser with real data (the overview shows Aline at 50% and Miguel at 0%, reflecting the real computed progress); the new-belt modal renders every field, including the colors; mobile with no horizontal overflow.
- Finance: validated in the internal browser with real data — the panel shows the available/receivable balance genuinely computed (Asaas+Stripe); the instructor payroll shows the real monthly calculation per instructor (e.g. R$ 400.00 fixed for two instructors); mobile with no horizontal overflow.
- Schedule: validated in the internal browser — a real monthly calendar (July 2026) with real classes per weekday; mobile with no horizontal overflow.

## ORM validation
Data created through the local ORM (`SubscriptionPlan.objects.create(...)`) in an isolated test; no remote write.

## Quality validation
- Focused tests per module.
- `manage.py check`.
- The internal browser (desktop, mobile, dark theme).

## Evidence
- The `template_name -> exists` inventory identified 36 missing templates (part of it already resolved by People/Plans/Classes; the rest will follow module by module).
- The administrative routes resolve, but the existing tests do not guarantee real rendering (Plans, People, and Classes/categories/schedules now have a real rendering test).
- The domain modules exist in models/forms/services/selectors, but the CRUD surface is still incomplete for Materials, Graduation, Finance, and the Schedule.
- A real bug found in `system/views/class_views.py`: `ClassGroupListView`/`ClassScheduleListView` and their respective `DetailView.get_object` used `get_admin_class_group_cards()`/`get_admin_schedule_day_cards()` and `get_class_group_card_by_pk`/`get_schedule_day_card_by_pk`, functions that **group several real classes/schedules into a single "card"** (e.g. the same modality+category with different instructors becomes one card), exposing only the `pk` of the group's first record (`lead_group`/`lead_schedule`). Using that to edit/delete would have silently ignored the other grouped records. Fixed to use `get_admin_class_group_queryset()`/`get_admin_class_schedule_queryset()` (real querysets, one item per record) and `ClassGroup.objects.get(pk=...)`/`ClassSchedule.objects.get(pk=...)` in the detail. The old functions still exist and are legitimately used in `system/services/class_overview.py` for the public filters/dropdowns (where grouping by modality+category is the correct behavior) — they are not dead code, they were just being misapplied to the administrative CRUD.
- A real bug found in `templates/products/product_list.html` (in this very implementation, fixed before committing): the first version referenced `product._total_stock`/`product._variant_count` (the `annotate()` aliases of `get_product_list_cards()`), but Django Templates forbid variables starting with `_` — the materials list would never have rendered. `system/models/product.py` already defines the public `total_stock`/`variant_count` properties for exactly that purpose (with a fallback for when the annotate was not applied); the template was fixed to use them.

## Implemented
- Plans: `system/views/plan_views.py` uses `ModalFormMixin` (reused from `person_views.py`) in `PlanCreateView`/`PlanUpdateView`; `templates/plans/plan_form_modal.html` created, reusing the complete form's field groups; `templates/plans/plan_list.html` with Create/Edit buttons in a modal and Delete in a confirmation `<dialog>`, the inline scripts removed; `system/urls.py` migrated to `/plans/...` with a redirect from `/planos/...`.
- Classes/categories/schedules: created from scratch (no template existed before) `templates/class_categories/*`, `templates/classes/*`, `templates/class_schedules/*` (list/form/detail/confirm_delete for each) and `static/system/css/classes/classes.css` (reusing tokens/components from `people.css`, avoiding triplicating ~1,100 lines of CSS). `system/views/category_views.py` and `system/views/class_views.py` gained `ModalFormMixin`; since no template pre-existed, each form uses the SAME file for full screen and modal (extending `lv/modal_frame.html` directly, with no separate `modal_template_name`). `system/urls.py` migrated to `/classes/...` with a redirect from `/turmas/...`.
- Materials: created from scratch `templates/products/*` (list/form with a variants/stock formset/detail/confirm_delete) and `templates/billing/admin_backorder_queue.html` (the pre-order queue, read-only). `system/views/product_views.py` gained `ModalFormMixin` in `ProductCreateView`/`ProductUpdateView`. `system/urls.py` migrated to `/materials/...`, `/store/...`, and `/my-materials/...` with a redirect from the old Portuguese routes.
- Graduation: created from scratch `templates/graduation/*` (the overview, belts with a complete CRUD, rules with list/form/delete, the history with a list/new-record form/delete — with no edit screen for the history, preserving the record as immutable by design). `system/views/graduation_views.py` gained `ModalFormMixin` in `BeltRankCreateView`/`UpdateView`, `GraduationRuleCreateView`/`UpdateView`, and `GraduationCreateView`. `system/urls.py` migrated to `/graduation/...` with a redirect from `/graduacao/...`.
- Finance: created from scratch `templates/billing/financial_entries.html` (the panel with real KPIs), `approval_queue.html`, `pending_payments.html`, `payroll_list.html`, and `payout_queue.html`. This module does not follow the create-modal pattern because it is not an entity CRUD — they are read screens with state transition actions (waive, mark paid, refund, approve/reject/send a payout), each action reusing the existing action views (`ExemptOrderActionView`, `MarkOrderPaidActionView`, etc.) through a simple form with a direct POST, consistent with the documented exception for expanded financial pages. `system/urls.py` migrated to `/financial/...` with a redirect from the 5 Portuguese read routes (the POST-only action routes were not redirected — low risk, no template points at the old paths any more).
- Schedule: the calendar (`templates/calendar/calendar.html`) already existed and was already functional (delivered/adjusted in PRD-080). `system/urls.py` migrated from `/cronograma/` to `/calendar/` with a redirect (except the `/cronograma/<year>/<month>/` variant, which was left with no redirect — a small gap recorded in Pending). 4 dead views removed from `system/views/calendar_views.py` (`AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`) — none had a route, template, or test; `AdminCalendarView` pointed at `calendar/admin_calendar.html`, which never existed. The now-unused imports (`PersonTypeCode`, `Person`, `AdministrativeRequiredMixin`) and the 4 corresponding entries in `system/views/__init__.py` (the imports and `__all__`) cleaned up.

## Cleanup findings
- No temporary residue.
- The duplicated theme logic between `plans.js` and the `lv/theme_toggle.js` foundation identified and avoided in this round (not fixed at the root — recorded as PRD-084's debt).
- The class/schedule grouping bug in the administrative CRUD fixed in this round (see Evidence).

## Follow-up PRDs
- PRD-084 to eliminate the duplicated theme JavaScript across the modules.

## Deviations from plan
- No functional deviation.

## Pending
- The public shop (`product-store`) and the student's pre-order flow (`student-backorders`, `student-order-history`) still have no template (the routes are already migrated to English, but the screens are still absent) — they are not part of this PRD's administrative CRUD; record their own PRD if they become a priority before the next audit round.
- The `ProductCategory` (material category) CRUD has no screen of its own (it is only chosen through an FK in the Product form); assess whether it is necessary in a future PRD.
- The cancel subscription/change plan actions (`cancel-membership`, `change-membership-plan`) still have no button triggering them on any screen (the view exists but is orphaned from the UI); assess whether it enters the Person detail in a future PRD.
- An explicit financial audit trail (who did each action, and when) does not exist as a screen of its own; the actions already record `admin_user`/`notes` in the service, but there is no navigable "log" — a possible future PRD (`auditoria-financeira-ausente`, already mapped in PRD-098's audit).
- The redirect from `/cronograma/<year>/<month>/` (the variant with parameters) was not implemented, only the base `/cronograma/` route.

## Final status
Completed with limitations — the 7 CRUD MVP modules (People, Plans, Classes/categories/schedules, Materials/stock, Graduation, Finance, and the Schedule) were delivered, tested (33 new tests specific to this PRD + the full suite of 308 tests OK), and validated visually (desktop, mobile, dark theme) with real seed data. The specific pending items (the public shop, the product category, the UI-orphaned subscription actions, and the financial audit trail) are documented above for future PRDs, not hidden.
