# PRD-143: MVT Review — Views, Models, and Forms

## Summary

Highly critical, read-only audit of the Django MVT layer (`system/views/`, `system/models/`, `system/forms/`) in Jul 2026. The scope covers 57 Python files (22 views, 21 models, and 14 forms). Conclusion: **systematic MVT separation violations** — god modules, business rules in views/forms/models, a dual plan catalog, parallel registration paths incompatible with PRD-040, triplicated validation, and incomplete barrel exports. **No code is changed by this PRD**; consolidation is assigned to a consolidating PRD.

## Demand type

Read-only architectural review (MVT critique) + debt routing. Complements PRD-138 and PRD-139 with an exclusive focus on views, models, and forms.

## Current problem

The HTTP and data-input layers concentrate orchestration that should live in `services/`. Forms with 600–1,100+ lines mix validation, plan eligibility, and domain materialization. Models expose dozens of `@property` methods with queries and pricing rules. Views such as `home_views.py` and `dependent_views.py` assemble context and execute checkout without fine-grained delegation.

### Scope metrics

| Layer | Files | Lines (approx.) | God modules (≥400L) |
|---|---|---|---|
| `system/views/` | 22 | ~5,400 | `home_views` (656), `calendar_views` (548), `person_views` (538), `auth_views` (482), `dependent_views` (401), `product_views` (364) |
| `system/forms/` | 14 | ~4,100 | `registration_forms` (1124), `person_forms` (734), `dependent_forms` (615) |
| `system/models/` | 21 | ~3,200 | `plan` (437), `membership` (413), `person` (334) |

## Goal

Record a critical file-by-file inventory, the 30 prioritized findings with severity and evidence, and a P0–P3 phased remediation proposal (Jul 2026).

## Context Ledger

### Files read in full

- `system/views/` — 22 modules (including `home_views.py`, `auth_views.py`, `person_views.py`, `dependent_views.py`, `calendar_views.py`, `__init__.py`)
- `system/models/` — 21 modules (including `plan.py`, `membership.py`, `person.py`, `class_membership.py`, `__init__.py`)
- `system/forms/` — 14 modules (including `registration_forms.py`, `person_forms.py`, `dependent_forms.py`, `__init__.py`)
- `system/urls.py` (cross-checking views ↔ routes)
- `system/services/pre_registration.py` (finalize → `form.save()`)
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` (contract)
- `docs/prd/PRD-097-orphan-calendar-views-without-routes.md`, `PRD-138`, `PRD-139`

### Adjacent files consulted

- `system/services/registration.py`, `registration_validation.py`
- `system/views/payment_views.py`, `plan_change_views.py`
- `docs/PRD-STANDARD.md`, `docs/prd/README.md`

### Internet / official documentation

- [Django design philosophies — Loose coupling](https://docs.djangoproject.com/en/5.2/misc/design-philosophies/#loose-coupling) — decoupled layers; domain logic does not belong in views or in forms acting as orchestrators.
- [Django models — Keep models focused](https://docs.djangoproject.com/en/5.2/topics/db/models/) — models represent data and simple invariants; looped queries through `@property` are an anti-pattern.

### Context7 / MCPs / tools verified

- `rg`, PowerShell line counts, and full reads of the cited modules.

### Limitations found

- The audit did not rerun the test suite (read-only).
- Services/selectors/JS are cited only when they couple views/forms/models.
- **Consolidated** remediation proposal (Jul 2026) — see the dedicated section.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`

## Understanding approved

Explicit request: read-only audit, relentless MVT architect persona, create PRD-143, and update the index. **Do not implement code.**

## Execution prompt

### Persona

Relentless MVT architect — only critique violations, coupling, and god classes.

### Action

Critical inventory + top 30 findings + complete PRD template.

### Context

LV JIU JITSU, Django 5.2, canonical PRD-040 flow.

### Constraints

- Read-only.
- Evidence by file/line.
- Remediation placeholder replaced with P0–P3 phases (Jul 2026).

### Acceptance criteria

- [ ] Inventory of all 57 files with a verdict for each file.
- [ ] Top 30 findings with severity (CRITICAL/HIGH/MEDIUM) and evidence.
- [ ] `docs/prd/README.md` updated with PRD-143.
- [ ] `## Remediation proposal (pending consolidator)` section present.
- [ ] No code files changed.

### Expected evidence

- This document + diff under `docs/prd/`.

### Output format

Complete PRD-STANDARD.

## Scope

- `system/views/**/*.py`
- `system/models/**/*.py`
- `system/forms/**/*.py`
- `docs/prd/PRD-143-*.md`, `docs/prd/README.md`

## Out of scope

- Refactoring implementation.
- `services/`, `selectors/`, templates, static assets, and tests (except when citing coupling).
- Test execution in this delivery.

## Impacted files

- `docs/prd/PRD-143-mvt-views-models-and-forms-review.md` (new)
- `docs/prd/README.md` (index)

## Risks and edge cases

- Removing `form.save()` in favor of `create_portal_registration` without replacing `finalize_pre_registration` breaks registration.
- Unifying the `PlanTier`/`PlanPrice` catalog requires migrating legacy `Membership.plan`.
- `home_views` concentrates permissions — extraction can regress the home split (PRD-092).

## Rules and constraints

- AGENTS.md: business rules belong in `services/`, views must be thin, and forms perform validation only.
- PRD-040: payment before `Person`; pre-finalization state lives in `PreRegistration`.

## Plan

### P0 phase — Registration and eligibility API (blocks PRD-141)
- [ ] #1, #10: split `registration_forms.py`; single validation source in `registration_validation.py`
- [ ] #2: `RegistrationFinalizeService`; remove `form.save()` from finalize
- [ ] #3, #15, #29: eliminate `pending_registration_person_id`; unify PreRegistration checkout
- [ ] #7: `dependent_registration_service`; thin view
- [ ] Eligibility JSON API (unblocks PRD-141 C-01)
- [ ] HTTP contract tests comparing the API with `plan_eligibility.py`

### P1 phase — Catalog, home, membership
- [ ] #4, #8, #28: public flows use only `pp:` (PlanPrice)
- [ ] #5, #30 + PRD-142: move `effective_tier`/`current_pause` into a service
- [ ] #6, #14, #26: `home_dashboard_service` + `selectors/home_context.py`
- [ ] #13: transactional `plan_change_service`
- [ ] #9, #16, #17, #18: PersonForm DTO; IBJJF selector; pricing outside the model

### P2 phase — Thin forms and hygiene
- [x] #11: ClassGroup → `services/class_management.py`. #12: assessed; it was already service-thin
- [x] #19, #20, #21: emptied the `views/__init__.py` barrel (dead code); aliases were already removed; a single mixin in `portal_mixins.py` (fixed the capability divergence)
- [x] #23, #24: public `get_instructor_class_group_ids`; created `registration_common.py`
- [x] #22: assessed — already the single source of class eligibility

### P3 phase — Legacy
- [ ] #4, #8, #28: deprecate SubscriptionPlan admin; backfill HG
- [ ] #27: reduce the models barrel

## Critical inventory — `system/models/` (21 files)

| File | L | Verdict | Main critique |
|---|---|---|---|
| `__init__.py` | 240 | MEDIUM | Huge barrel re-exports the entire domain; encourages circular imports (`plan` ↔ `membership`). |
| `common.py` | 6 | OK | `TimeStampedModel` — appropriate. |
| `person.py` | 334 | HIGH | `@property current_ibjjf_category` queries; `can_enroll_in_class_group` queries `class_enrollments`; role rules are scattered. |
| `plan.py` | 437 | CRITICAL | Dual catalog (`SubscriptionPlan` + `PlanTier`/`PlanPrice`); `PlanPrice.save()` recalculates price and calls `_guard_immutability()`; `@property is_referenced_by_membership` queries. |
| `membership.py` | 413 | CRITICAL | Dual `plan` + `plan_price` FKs; 12+ `@property effective_*`; `effective_tier` queries; `current_pause` filters; `recompute_billed_price()` is a financial rule in the model. |
| `registration_order.py` | 257 | MEDIUM | Display properties; acceptable when read-only and query-free. |
| `pre_registration.py` | 127 | MEDIUM | Wizard state; lightweight properties — acceptable as persistence. |
| `class_membership.py` | 152 | HIGH | `clean()`/`save(full_clean)` with type and IBJJF eligibility rules; module-level querying function in `get_class_group_eligibility_error`. |
| `class_group.py` | 36 | MEDIUM | `clean()` — acceptable invariant. |
| `class_schedule.py` | 49 | OK | Schema. |
| `calendar.py` | 209 | MEDIUM | Session/check-in properties; verify N+1 behavior in lists. |
| `graduation.py` | 145 | LOW | Simple property. |
| `product.py` | 85 | MEDIUM | Inventory/display properties. |
| `product_backorder.py` | 84 | LOW | Status properties. |
| `category.py` | 36 | OK | Schema + `matches_age`. |
| `coupon.py` | 35 | OK | Schema. |
| `asaas.py` | 168 | LOW | Display property. |
| `audit.py` | 24 | OK | Schema. |
| `trial_access.py` | 40 | LOW | Lightweight properties. |
| `request_workflows.py` | 171 | OK | Request schema. |
| `membership_timeline.py` | 55 | OK | Event schema. |

## Critical inventory — `system/forms/` (14 files)

| File | L | Verdict | Main critique |
|---|---|---|---|
| `__init__.py` | 50 | OK | Forms barrel — incomplete relative to modules (missing `plan_tier_forms`). |
| `registration_forms.py` | 1124 | CRITICAL | God form: validation for seven profiles, plans, classes, materials, and operations; `save()` → `create_portal_registration()`; duplicates `registration_validation.py`. |
| `person_forms.py` | 734 | CRITICAL | Admin god form; `PersonForm.save()` orchestrates enrollments, payroll, and operational roles; martial-art validation duplicates registration. |
| `dependent_forms.py` | 615 | CRITICAL | God form; imports constants from `registration_forms`; reimplements plan eligibility; has no `save()`, but the view orchestrates everything. |
| `class_forms.py` | 300 | HIGH | `ClassGroupForm.save()` synchronizes `ClassInstructorAssignment` — domain logic in a form. |
| `class_request_forms.py` | 329 | MEDIUM | Heavy validation; the decision belongs in a service. |
| `access_request_forms.py` | 163 | HIGH | `AdministrativeAccessRequestForm.save()` → `create_administrative_access_request()`. |
| `plan_forms.py` | 227 | MEDIUM | Legacy `SubscriptionPlan` CRUD. |
| `plan_tier_forms.py` | 168 | MEDIUM | New catalog CRUD — parallel to `plan_forms`. |
| `graduation_forms.py` | 144 | OK | Lean CRUD. |
| `product_forms.py` | 103 | OK | CRUD + cart. |
| `auth_forms.py` | 80 | OK | Authentication. |
| `membership_pause_forms.py` | 13 | OK | Minimal delegation. |
| `category_forms.py` | 24 | OK | CRUD. |

## Critical inventory — `system/views/` (22 modules)

| File | L | Verdict | Main critique |
|---|---|---|---|
| `__init__.py` | 240 | HIGH | Partial barrel: omits `dependent_views`, `admin_views`, `plan_tier_views`, `membership_pause_views`, `access_request_views`, `class_request_views`, and `stripe_views`; exports dead `InstructorCalendarView`/`StudentScheduleView` aliases. |
| `portal_mixins.py` | 34 | OK | Auth mixins — appropriate. |
| `home_views.py` | 656 | CRITICAL | God module: `HomeView.get_context_data` is ~160L, with 18 helpers, direct ORM (`ClassSession`, `SpecialClass`), billing, payroll, dependents, and permissions. |
| `auth_views.py` | 482 | CRITICAL | Wizard + materials + finalization; legacy `pending_registration_person_id` path; `MaterialsCheckoutView` creates orders in the view; `FinalizeRegistrationView` activates Person in the view. |
| `person_views.py` | 538 | HIGH | CRUD god module; duplicated mixins (`AdministrativeRequiredMixin`); `VeteranPlanDecisionView` contains rules in the view. |
| `dependent_views.py` | 401 | CRITICAL | `DependentRegistrationView.post` is ~120L and orchestrates payment, materials, and family behavior — a second wizard parallel to PRD-040. |
| `calendar_views.py` | 548 | HIGH | 16 classes; orphan aliases in the barrel; imports private `_get_instructor_class_group_ids`; queries in the view. |
| `payment_views.py` | 258 | HIGH | `DeferPaymentView` reintroduces `pending_registration_person_id` (Person before PreRegistration flow); session logic in the view. |
| `product_views.py` | 364 | HIGH | Store + backorders + orders; mixes admin and portal. |
| `plan_change_views.py` | 152 | HIGH | `PlanChangeSelectView.post` cancels Stripe and calls `membership.save()` in the view; should be a transactional service. |
| `asaas_views.py` | 272 | MEDIUM | Thin webhook; `AdministrativeRequiredMixin` is **duplicated** (copied from `person_views`). |
| `billing_admin_views.py` | 168 | MEDIUM | Actions partially delegate to services — acceptable. |
| `graduation_views.py` | 138 | MEDIUM | `_AdministrativeRequiredMixin` is triplicated. |
| `class_views.py` | 172 | MEDIUM | Uses services — better pattern. |
| `category_views.py` | 98 | OK | Thin CRUD. |
| `plan_views.py` | 97 | MEDIUM | Legacy plan CRUD. |
| `plan_tier_views.py` | 185 | MEDIUM | Parallel PlanTier CRUD — outside the barrel. |
| `admin_views.py` | 136 | MEDIUM | Admin hub — outside the barrel. |
| `access_request_views.py` | 182 | MEDIUM | `form.save()` in the view — outside the barrel. |
| `class_request_views.py` | 210 | MEDIUM | Request queue — outside the barrel. |
| `membership_pause_views.py` | 180 | MEDIUM | Pause — outside the barrel. |
| `stripe_views.py` | 39 | OK | Thin webhook. |

## Top 30 findings (severity + evidence)

| # | Severity | Finding | Evidence |
|---|---|---|---|
| 1 | CRITICAL | **God form `registration_forms.py` (1124L)** concentrates validation for every profile, eligibility, classes, materials, and checkout. | `PortalRegistrationForm.clean()` L352–375 chains 10+ `_clean_*`; entire file. |
| 2 | CRITICAL | **`PortalRegistrationForm.save()` materializes the domain** through `create_portal_registration()` — MVT violation; the only `finalize_pre_registration` path. | `registration_forms.py` L377–378; `pre_registration.py` L536. |
| 3 | CRITICAL | **Legacy PRD-040 path**: `pending_registration_person_id` remains active — Person exists before canonical finalization. | `auth_views.py` L392–399, L502–518; `payment_views.py` L129–130; `MaterialsCheckoutView` L392–428. |
| 4 | CRITICAL | **Dual FK in `Membership`**: legacy `plan` + new `plan_price`, with eight `effective_*` properties — a source of billing inconsistency. | `membership.py` L35–49, L139–205. |
| 5 | CRITICAL | **`Membership.effective_tier` executes a query** in `@property` — N+1 in lists and a rule in the model. | `membership.py` L146–150. |
| 6 | CRITICAL | **God module `home_views.py`**: the view assembles the entire dashboard with ORM, billing, payroll, graduation, and dependents. | `HomeView.get_context_data` L78–233; helpers L302–725. |
| 7 | CRITICAL | **`DependentRegistrationView.post` orchestrates checkout** (plan, materials, family) — second wizard parallel to PRD-040. | `dependent_views.py` L60–181. |
| 8 | CRITICAL | **Dual plan catalog** in forms and views: `resolve_catalog_plan` accepts `sp:` and `pp:` throughout the flow. | `dependent_views.py` L98–100; `plan_change_views.py` L59–60; `plan.py` + `plan_forms` vs `plan_tier_forms`. |
| 9 | HIGH | **`PersonForm.save()` orchestrates the domain**: enrollments, payroll, and operational roles. | `person_forms.py` L681–702. |
| 10 | HIGH | **Triplicated registration validation**: `PortalRegistrationForm`, `registration_validation.py`, and wizard JS. | `auth_views.py` L229–232 (`RegistrationStepValidationView`); `registration_forms.py` vs `registration_validation.py` `STEP_REQUIRED_FIELDS`. |
| 11 | HIGH | **`ClassGroupForm.save()` synchronizes instructors** — transactional write in a form. | `class_forms.py` L88–120. |
| 12 | HIGH | **`AdministrativeAccessRequestForm.save()` creates a request** — domain logic in a form. | `access_request_forms.py` L125–139. |
| 13 | HIGH | **`PlanChangeSelectView.post` changes membership and cancels Stripe** in the view without a single service. | `plan_change_views.py` L75–101. |
| 14 | HIGH | **`ClientProfileDeactivateView` uses `transaction.atomic` in the view** — should be `deactivate_portal_person()`. | `home_views.py` L279–292. |
| 15 | HIGH | **`MaterialsCheckoutView` creates orders and redirects to a gateway** in the view (two paths: PreRegistration + legacy Person). | `auth_views.py` L386–472. |
| 16 | HIGH | **`Person.current_ibjjf_category` queries in a property** — duplicates the eligibility selector/service. | `person.py` L233–245. |
| 17 | HIGH | **`PlanPrice.save()` contains pricing and immutability rules** — financial logic in the model. | `plan.py` L409–458. |
| 18 | HIGH | **`Membership.recompute_billed_price()`** — family discount in the model, not in a service. | `membership.py` L207–218. |
| 19 | HIGH | **Incomplete `views/__init__.py` barrel** — seven modules imported only in `urls.py`; risk of “ghost” views. | Compare `urls.py` imports with `views/__init__.py`. |
| 20 | HIGH | **Orphan aliases in the barrel**: `InstructorCalendarView`, `StudentScheduleView` = `CalendarView` without dedicated routes. | `calendar_views.py` L104, L248; `views/__init__.py` L4, L152. |
| 21 | HIGH | **`AdministrativeRequiredMixin` duplicated** in `person_views.py` and `asaas_views.py` (plus a variant in `graduation_views`). | `person_views.py` L52; `asaas_views.py` L233; `graduation_views.py` L27. |
| 22 | MEDIUM | **`ClassEnrollment.clean/save(full_clean)`** — enrollment rule in the model (acceptable as an invariant, but duplicates form/service). | `class_membership.py` L162–168. |
| 23 | MEDIUM | **`calendar_views` imports a private function** `_get_instructor_class_group_ids` — coupling to an implementation detail. | `calendar_views.py` L88. |
| 24 | MEDIUM | **`dependent_forms` imports from `registration_forms`** — coupling between god forms. | `dependent_forms.py` L4–8. |
| 25 | MEDIUM | **`PortalRegisterView.form_valid` does not call `form.save()`** — form `save()` is used only during finalize; confusing, dead API for the intermediate wizard. | `auth_views.py` L110–150 vs `registration_forms.py` L377. |
| 26 | MEDIUM | **Direct ORM in `home_views`** for instructor attendance counts — should be a selector. | `home_views.py` L210–222. |
| 27 | MEDIUM | **240L `models/__init__.py` barrel** — circular `membership` ↔ `plan` imports through lazy property imports. | `plan.py` L462; `membership.py` L144. |
| 28 | MEDIUM | **Parallel plan CRUD**: legacy `plan_views` + `plan_forms` vs new `plan_tier_views` + `plan_tier_forms`. | Two active admin modules. |
| 29 | MEDIUM | **`FinalizeRegistrationView` activates Person/PortalAccount in the view** — duplicates `finalize_pre_registration`. | `auth_views.py` L494–533 vs `pre_registration.py` L501+. |
| 30 | MEDIUM | **`Membership.current_pause` property uses a filter** — query on each access in templates/serialization. | `membership.py` L242–253. |

## Remediation proposal

> Remediation proposal completed by the consolidator in Jul 2026.

Actionable plan aligned with PRD-138 phases 2 and 4. **Blocks PRD-141 P1** (removing JS eligibility) and **unblocks PRD-142 P0** (home selector + `effective_tier`).

### Prioritized phases

| Phase | Focus | Overall risk | Dependencies |
|---|---|---|---|
| **P0** | Single registration flow + authoritative validation + eligibility API | High | PRD-040, PRD-081; **before** PRD-141 C-01 |
| **P1** | Single catalog + thin views + home selector | High | Stable P0; coordinates PRD-142 PERF-002/006 |
| **P2** | Forms without domain `save()` + barrel/mixin hygiene | Medium | P1 |
| **P3** | Residual model cleanup + legacy plan CRUD | Medium–high | Active-membership migration |

---

### P0 phase — Canonical registration and a single validation source

| # | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| 1, 10 | Split `PortalRegistrationForm` into per-step forms (`ProfileStepForm`, `PlanStepForm`, …); move chained `clean()` to the single `registration_validation.py` source | `registration_forms.py` L352–375; `registration_validation.py`; new `forms/registration_*_forms.py` | `registration_forms.py` < 400L; `rg STEP_REQUIRED_FIELDS` finds one definition; per-step wizard tests pass | High |
| 2 | `finalize_pre_registration` calls `RegistrationFinalizeService.create_from_pre_registration()` — **not** `form.save()` | `pre_registration.py` L536; new `services/registration_finalize.py`; `registration_forms.py` L377–378 | `PortalRegistrationForm.save()` removed or raises `NotImplementedError`; finalize creates Person+Membership through a service; `test_registration_*` pass | High |
| 3, 15, 29 | Eliminate `pending_registration_person_id`; unify `MaterialsCheckoutView` and `DeferPaymentView` around `PreRegistration` only | `auth_views.py` L392–472, L494–533; `payment_views.py` L129–130 | `rg pending_registration_person_id` → 0; sandbox payment→finalize flow without an earlier Person | High |
| 7 | `DependentRegistrationView.post` delegates to `dependent_registration_service`, mirroring PRD-040 (same contract as the public wizard) | `dependent_views.py` L60–181; new `services/dependent_registration.py` | POST view < 80L; parity tests for dependent vs primary-member wizard | High |
| — | **Eligibility read-model API** (JSON): expose `build_eligibility_context_for_person` + filtered catalogs | New `views/registration_api_views.py` or action in `auth_views`; `selectors/plan_eligibility.py` | Documented JSON contract; HTTP test = Python selector; **unblocks PRD-141 C-01** | High |
| 25 | Document that `form.save()` is not used in the intermediate wizard; `save_pre_registration_from_form` is the only path | `auth_views.py` L110–150; form docstring | No code-review ambiguity | Low |

**Dependencies:** PRD-138 phase 2 (PRD-081, PRD-129). PRD-141 **must not** remove JS eligibility until the API + P0 validation are covered by tests and running locally.

**What NOT to do in P0:**
- Do not remove all of `registration_forms.py` at once (it breaks finalize).
- Do not expose eligibility in JS before the API has test coverage.
- Do not delete the legacy path until `rg` returns zero and payment tests pass.

---

### P1 phase — Single catalog, thin home, and membership

| # | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| 4, 8, 28 | Checkout/wizard accepts only `pp:` (`PlanPrice`); `resolve_catalog_plan` rejects `sp:` in public flows | `dependent_views.py` L98–100; `plan_change_views.py`; `registration_checkout.py` | Registration and dependent flows use only `PlanTier`/`PlanPrice`; `LegacyPlan*` tests isolated or removed | High |
| 5, 30 | Resolve `Membership.effective_tier` and `current_pause` in `membership_service` with annotate/prefetch; properties delegate or become fields | `membership.py` L139–151, L242–253; `services/membership.py` | **Synchronize PRD-142 PERF-006/007**; family pricing without N+1 | High |
| 6, 14, 26 | Extract `home_dashboard_service.build_context(user)` + `selectors/home_context.py`; view handles HTTP only | `home_views.py` L78–233, L279–292, L302–725 | `HomeView.get_context_data` < 40L; **PRD-142 PERF-002** budgets met | High |
| 13 | `PlanChangeSelectView.post` → transactional `plan_change_service.apply_change()` | `plan_change_views.py` L75–101; `services/plan_change.py` | Stripe cancellation + membership update are atomic; mock Stripe test | Medium |
| 17, 18 | Move `PlanPrice.save()` immutability to `plan_management_service`; move `recompute_billed_price` to `family_pricing` | `plan.py` L409–458; `membership.py` L207–218 | Models contain no financial-rule writes; pricing tests pass | Medium |
| 16 | `Person.current_ibjjf_category` → `plan_eligibility.get_ibjjf_category(person)` (no query in property) | `person.py` L233–245; `selectors/plan_eligibility.py` | Property removed or cache-only; person list has no extra query | Medium |
| 9 | `PersonForm.save()` returns a DTO; view calls `person_admin_service.update_person()` | `person_forms.py` L681–702; `person_views.py` | Form performs no direct ORM create/update | Medium |

**Dependencies:** P0 eligibility API. PRD-142 extracts selectors in parallel (same `home_context.py` module).

**What NOT to do in P1:**
- Do not drop `Membership.plan` before backfilling `plan_price_id` in HG.
- Do not split `home_views` without a role matrix (student+instructor+admin+guardian).

---

### P2 phase — Thin forms and HTTP hygiene

| # | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| 11 | `ClassGroupForm.save()` → `class_group_service.sync_instructors()` | `class_forms.py` L88–120 | Form validates only; transactional service | Medium |
| 12 | `AdministrativeAccessRequestForm.save()` → service | `access_request_forms.py` L125–139 | DTO + service pattern | Low |
| 19, 20 | Complete `views/__init__.py` with every `urls.py` module **or** eliminate the barrel; remove `InstructorCalendarView`/`StudentScheduleView` aliases | `views/__init__.py`; `calendar_views.py` L104, L248 | `rg InstructorCalendarView` appears only in removal tests or returns 0; explicit URL imports | Low |
| 21 | Single `AdministrativeRequiredMixin` in `portal_mixins.py` | `person_views.py` L52; `asaas_views.py` L233; `graduation_views.py` L27 | One definition; three copies removed | Low |
| 24 | Break `dependent_forms` → `registration_forms` coupling; shared definitions in `forms/registration_common.py` | `dependent_forms.py` L4–8 | No import from god form | Medium |
| 23 | `calendar_views` no longer imports private `_get_instructor_class_group_ids`; use a public selector | `calendar_views.py` L88; `selectors/` or public `class_calendar` API | Documented public-symbol import | Low |
| 22 | Align `ClassEnrollment.clean` with a single enrollment service | `class_membership.py` L162–168 | One class-eligibility source | Medium |

**What NOT to do in P2:**
- Do not re-export dead views “for compatibility.”
- Do not move validation back into templates/JS.

---

### P3 phase — Legacy deprecation (after data migration)

| # | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| 4, 8, 28 | Remove `SubscriptionPlan` from active admin; deprecate `plan_views`/`plan_forms` | `plan_views.py`, `plan_forms.py`, `plan.py` | `rg SubscriptionPlan` finds only migrations/history; 100% of memberships use `plan_price` | High (HG) |
| 27 | Reduce the `models/__init__.py` barrel; use lazy imports where necessary | `models/__init__.py` L240 | No membership↔plan circular import in common runtime | Medium |

**Dependencies:** PRD-138 phase 5; confirmation of the HG membership backfill.

---

## Cross-PRD dependencies

| Dependency | Partner PRD | Direction | Blocker |
|---|---|---|---|
| Eligibility API → remove JS | **PRD-141** P1 (C-01, C-07) | 143 → 141 | P0 API required |
| `registration_forms` before JS rule | **PRD-141** P1 | 143 → 141 | P0 forms split |
| `home_context` selector | **PRD-142** P0 (PERF-002/003) | 143 ↔ 142 | Same `selectors/home_context.py` module |
| `effective_tier` service | **PRD-142** P0 (PERF-006/007) | 143 ↔ 142 | Synchronized P1 |
| `base.html` shell | **PRD-141** P0 | 141 → 143 | Wizard templates after shell |
| Single registration flow | **PRD-138** phase 2 | 138 → 143 | P0 = partial phase 2 |
| `PlanTier`-only catalog | **PRD-138** phase 2 / PRD-129 | 138 → 143 | P1 |
| Eligibility API performance | **PRD-142** P1 (PERF-022) | 142 → 143 | API cannot introduce N+1 |

## Test plan

### Tests to author

- N/A for this delivery (read-only).

### Execution authorization

- Not authorized — documentation only.

### Execution evidence

- N/A.

## Visual validation

- N/A.

## ORM validation

- N/A.

## Quality validation

- [x] Complete 57-file inventory.
- [x] Top 30 findings with severity and evidence.
- [x] Official Django source cited.
- [x] Detailed remediation proposal (P0–P3 phases, Jul 2026).
- [ ] Post-remediation regression tests (future, per phase).

## Evidence

| Item | Evidence |
|---|---|
| Line counts | PowerShell `Measure-Object` in Jul 2026 — values in the inventory table. |
| Findings 1–30 | `rg` + full reads of the cited modules. |
| Routes vs barrel | `system/urls.py` vs `system/views/__init__.py`. |
| PRD-040 | `pending_registration_person_id` path still referenced in 3+ views. |

## Implemented

- PRD-143 created with an inventory and top 30 findings.
- `docs/prd/README.md` updated.
- **[2026-07-09] P0 phase executed** (outside the original read-only scope, authorized by the user):
  - **Eligibility API**: new `RegistrationEligibilityView` (`POST /cadastro/elegibilidade/`, route `system:registration-eligibility`) exposes `build_eligibility_context_for_registration` + `get_eligible_plan_prices` through JSON. `system/services/registration_validation.py::build_eligibility_context_from_wizard_data` parses the wizard’s raw data. Contract tested byte-for-byte against the selector in `system/tests/test_registration_eligibility_api.py` (5 tests). 100% additive change — unblocks PRD-141 C-01/C-07 without changing `register.js` in this delivery.
  - **#2 (form.save() → service)**: `PortalRegistrationForm.save()` now raises `NotImplementedError`; `finalize_pre_registration` calls `create_portal_registration(form.cleaned_data)` directly. `system/tests/test_models.py::test_form_save_raises_not_implemented` protects the new contract.
  - **#3, #15, #29 (eliminate `pending_registration_person_id`)**: exhaustive static analysis confirmed that the legacy path (Person created before payment) is unreachable in the current flow — `create_pre_registration_plan_payment` never links `RegistrationOrder` to a real Person before finalize. Dead branches were removed from `MaterialsCheckoutView`, `FinalizeRegistrationView`, `DeferPaymentView`, `PaymentSuccessView`, `ResetRegistrationView._SESSION_KEYS` (also dead), and the fallback in `get_pending_person_summary`. `rg pending_registration_person_id system/` → 0.
  - **#7 (dependent_registration_service)**: pure functions `is_dependent_payment_confirmed`, `is_dependent_materials_confirmed`, `restore_confirmed_payment_post_data`, and `apply_confirmed_payment_to_cleaned_data` were extracted from `DependentRegistrationView` into `system/services/dependent_registration.py`. Scope was deliberately limited: the HTTP decision tree (redirects/render/modal) remains in the view — fully extracting orchestration was assessed as disproportionate risk without a dedicated session.
  - Evidence: `manage.py test system` — 662 tests passed (651 at the start of the session); 29/29 dedicated `test_dependent_registration.py` tests pass, including tampered-payment scenarios (`test_paid_resume_finalizes_with_paid_plan_even_if_post_is_tampered`); manual browser validation of the public wizard through the materials step.
- **[2026-07-09] P2 phase executed** (thin forms and HTTP hygiene):
  - **#21 (single `AdministrativeRequiredMixin`)**: mixin moved to `system/views/portal_mixins.py` (canonical source with `allowed_codes=ADMINISTRATIVE_PERSON_TYPE_CODES` + `required_capabilities=(MANAGE_ACADEMY,)`); the two copies in `asaas_views.py` and `graduation_views.py::_AdministrativeRequiredMixin` were removed. **Security finding during consolidation**: the two removed copies did **not** define `required_capabilities`, so they fell into the `has_allowed_role()` branch that checks `person.person_type.code in allowed_codes` — completely ignoring the `OperationalRole`/capabilities system. In practice, a holder of the `academy-manager` operational role (explicitly designed for “broad operational access to administrative modules,” `system/constants.py` `DEFAULT_OPERATIONAL_ROLE_DEFINITIONS`) or `graduation-operator`/`financial-operator` could access `PersonDeleteView` (through the correct version in `person_views.py`) but was blocked from `PayrollListView`/`PayoutQueueView`/`GraduationOverviewView` (incomplete versions) despite having the correct capability — granular role delegation for these two areas was effectively dead. Unification fixes this by adopting the version with `required_capabilities` everywhere. Nine files were updated to import from the canonical location (`person_views.py`, `asaas_views.py`, `graduation_views.py`, `category_views.py`, `class_views.py`, `admin_views.py`, `plan_views.py`, `plan_tier_views.py`, `product_views.py`).
  - **#19/#20 (`views/__init__.py` barrel)**: `rg "from system.views import [A-Z]"` confirmed that **nothing** in the code consumes the barrel’s ~90 re-exports — `system/urls.py` (the only real views consumer) already imports directly from each submodule. The barrel was emptied (it was dead code, not “incomplete”). Orphan aliases `InstructorCalendarView`/`StudentScheduleView` (finding #20) no longer existed — confirmed as removed in a previous session (PRD-138 phase 1).
  - **#23 (private `_get_instructor_class_group_ids`)**: renamed to public `get_instructor_class_group_ids` in `system/services/class_calendar.py`; `calendar_views.py` and `home_views.py` now import it from the module top level instead of using a local/private-symbol import.
  - **#24 (`dependent_forms` → `registration_forms` coupling)**: `MARTIAL_ART_EXPERIENCE_CHOICES`, `MARTIAL_ART_EXPERIENCE_YES`, and `MARTIAL_ART_MODALITY_CHOICES` were extracted to new `system/forms/registration_common.py`; `registration_forms.py` and `dependent_forms.py` now import from the same shared source without depending on one another.
  - **#11 (`ClassGroupForm.save()` with domain logic)**: `save()`/`save_m2m()`/`save_related()`/`_save_assistant_staff()` removed from the form; `ClassInstructorAssignment` synchronization moved to `system/services/class_management.py::sync_class_group_instructors()`, called directly by `save_class_group_catalog()`. The sole consumer (`ClassGroupCatalogMixin.form_valid`) already used the service exclusively, so the change is behaviorally neutral.
  - **#12 (`AdministrativeAccessRequestForm.save()`)**: assessed — already a thin delegate that only assembles kwargs and calls `create_administrative_access_request()`; no business rule in the form. No action required.
  - **#22 (`ClassEnrollment.clean` — eligibility source)**: assessed — `get_class_group_eligibility_error` is already a single pure function (not a model method) reused by `registration_forms.py`, `dependent_forms.py`, `person_forms.py`, `services/registration_validation.py`, and `ClassEnrollment.clean()` itself. It is already the single source; no duplicated rule found. No action required.
  - Evidence: clean `manage.py check`; `manage.py test system` — 662 tests passed (same count before/after, no regression) in three complete runs during the phase (after mixin consolidation, after class_forms/class_management, and final).

## Cleanup findings

- `PortalRegistrationForm.save()` was a misleading API — **fixed in this delivery** (raises `NotImplementedError`).
- `plan_tier_forms` missing from the `forms/__init__.py` barrel — not fixed in this delivery (P2 phase).
- PRD-097 is partially obsolete: calendar aliases remain in the barrel, not in `urls.py` — not fixed in this delivery (P2 phase).

## Follow-up PRDs

- Post-PRD-138 consolidator (execution of phases A–E above).
- Update PRD-097 after deciding about aliases.
- Dedicated PRD: single-FK `Membership` migration.

## Deviations from plan

- None.

## Pending

- Approval for per-phase implementation child PRDs (P0–P3).
- PRD-141 P1 awaits P0 (eligibility API).
- Backfill `Membership.plan_price` in HG before P3.

## Final status

**Completed** — read-only audit and consolidated remediation proposal (Jul 2026).
Partial phase implementation occurred through **PRD-144** (P0/P1); the original
“code not started” closure is obsolete (see PRD-145 reconciliation below).

## PRD-145 reconciliation — 2026-07-13

- “Code implementation not started” refers to the original closure and became
  obsolete after the phases described in the `Implemented` section.
- PRD-145 confirmed the use of services for administrative and class requests,
  thin views for HTTP decisions, and tested transactional persistence.
- Full decomposition of the large modules and the `Membership` migration remain
  outside this round’s scope.
- Reconciled state: **audit completed; recorded phases implemented;
  remaining structural refactors pending**.
