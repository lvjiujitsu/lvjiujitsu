# PRD-142: Backend Review — Performance and Queries

## Summary

**Highly critical** read-only performance audit of the LV JIU JITSU backend
(Jul/2026), focused on `system/services/`, `system/selectors/`, `system/views/`,
`system/models/` (properties that issue queries), `system/signals.py`, and
indexes inferred from `system/migrations/0001_initial.py`. Result: **47
hotspots** classified (12 CRITICAL, 18 HIGH, 12 MEDIUM, 5 LOW); **zero tests**
using `assertNumQueries` or a query-budget contract; dominant risk in **home**,
the **graduation overview**, and the **monthly calendar** as student/order
volume grows.

## Demand type

Read-only performance audit (queries, N+1, indexes, missing tests). **Does not
implement code** — records findings with evidence and routes corrections to a
child PRD or consolidator.

## Current problem

The backend concentrates business rules in services/selectors, but recurring
patterns degrade latency and scalability:

| Pattern | Occurrences | Typical impact |
|---|---|---|
| Loop over queryset without prefetch + internal property/query | 15+ | N+1, O(n) queries |
| View/home aggregating multiple heavy services per request | 1 (`HomeView`) | O(n × dependents) |
| `@property` with `.objects.filter()` | 3 in `Membership`, 1 in `Person` | Hidden query on access |
| Full scan + nested in-memory loop | `get_calendar_month_data` | O(days × schedules) |
| Missing indexes on high-volume tables | calendar, orders, graduation | Sequential scan in staging (Postgres) |
| Complete absence of performance tests | `system/tests/` | Invisible regression |

### Top 5 hotspots (production risk order)

1. **`get_graduation_overview`** — 1 request × N students × ~5–7 queries/student.
2. **`HomeView.get_context_data`** — stacks schedule, graduation, billing, and
   payroll; multiplies by dependent.
3. **`Membership.effective_tier` / `current_pause`** — query in property used
   in family and home loops.
4. **`get_calendar_month_data`** — loads all active `ClassSchedule` rows and
   crosses them with every day of the month.
5. **`calculate_monthly_payroll` → `_get_order_students_for_groups`** — one
   query per order paid in the month.

## Goal

Document a complete hotspot inventory with **file:line**, severity, impact
estimate, and recommended indexes; correction proposal in P0–P2 waves
(Jul/2026).

## Context Ledger

### Files read in full

- `docs/PRD-STANDARD.md`, `AGENTS.md`, `CLAUDE.md`
- `system/services/class_calendar.py` (1533L)
- `system/services/membership.py`
- `system/services/registration_checkout.py`
- `system/services/graduation.py`
- `system/services/family_pricing.py`
- `system/services/financial_dashboard.py`
- `system/services/payroll_rules.py` (in-depth sample of
  `calculate_monthly_payroll` and helpers)
- `system/services/asaas_billing_cycle.py`
- `system/services/plan_change.py` (`build_plan_catalog` excerpts)
- `system/services/membership_timeline.py`
- `system/services/product_backorders.py` (sample)
- `system/selectors/graduation.py`
- `system/selectors/plan_eligibility.py`
- `system/selectors/person_selectors.py`
- `system/views/home_views.py` (733L)
- `system/views/person_views.py` (list/detail/update excerpts)
- `system/views/calendar_views.py`
- `system/views/admin_views.py` (`AdminHubView`)
- `system/views/graduation_views.py` (`GraduationOverviewView`)
- `system/models/membership.py` (properties)
- `system/models/person.py` (`current_ibjjf_category`)
- `system/models/calendar.py` (Meta/indexes)
- `system/models/registration_order.py` (Meta/indexes)
- `system/signals.py`
- `system/migrations/0001_initial.py` (`AddIndex` section and calendar models)

### Adjacent files consulted

- `docs/prd/PRD-138-architectural-audit-single-flow-and-consistency-of-mvp.md`
- `docs/prd/PRD-139-full-coverage-audit-file-by-file-inventory.md`
- `docs/prd/README.md`
- `rg` under `system/` for `assertNumQueries`, `select_related`,
  `prefetch_related`, and `.objects.` inside loops

### Internet / official documentation

- [Django — Database access optimisation](https://docs.djangoproject.com/en/5.2/topics/db/optimization/) — `select_related`/`prefetch_related`, `annotate`, `iterator`, profiling with `connection.queries`, and query-in-loop anti-pattern.
- [Django — Model index reference](https://docs.djangoproject.com/en/5.2/ref/models/indexes/) — `Meta.indexes` and impact on filtering/ordering.
- `supabase-postgres-best-practices` skill (`query-` / `schema-` category) —
  composite and partial indexes for frequent filters (`status`, `date`, FK).

### Context7 / MCPs / tools verified

- `rg` / complete reading of listed files
- `lv-prd` skill applied for structure
- `supabase-postgres-best-practices` skill consulted for index prioritisation

### Limitations found

- **Static** audit — no `EXPLAIN ANALYZE`, `assertNumQueries`, or HTTP latency
  measurement run in this PRD.
- Impact estimates are **inferred** from code patterns and expected cardinality
  (medium academy: 200–800 students, dozens of schedules/day).
- `staticfiles/` and the staging environment were not profiled.
- Concrete corrections documented in the Correction Proposal section
  (Jul/2026).

## Required skills

- `lv-task-intake` (completed)
- `lv-prd` (this PRD)
- `lv-django-delivery` (future execution)
- `supabase-postgres-best-practices` (staging/production indexes)

## Understanding approved

Request (Jul/2026): relentless read-only backend performance audit; criticise
with evidence; create PRD-142; update index; **do not implement**.

## Execution prompt

### Persona

Relentless performance reviewer — criticise only with evidence; do not soften
findings.

### Action

Consolidate corrections in a child PRD or dedicated wave; apply tests with
query budgets before refactoring CRITICAL hotspots.

### Context

This PRD is the hotspot map; implementation requires new explicit approval.

### Constraints

- Single-migration baseline (`0001_initial.py`) — new indexes require a schema
  PRD + staging/production confirmation.
- Do not alter functional behaviour without regression tests.
- Measure before/after with `assertNumQueries`, `django-debug-toolbar`, or query
  logging in a controlled environment.

### Acceptance criteria

- [ ] CRITICAL hotspots (PERF-001–012) addressed or explicitly accepted with justification
- [ ] `get_graduation_overview` with documented budget (for example, ≤15 queries for 500 students)
- [ ] `HomeView` with budget by persona (single student, guardian + 3 dependents, teacher+admin)
- [ ] Recommended indexes (section 6) evaluated in staging with `EXPLAIN`
- [ ] At least 1 `*Performance*` test module or `assertNumQueries` per critical area

### Expected evidence

- `manage.py test` output with query-budget tests
- `EXPLAIN (ANALYZE, BUFFERS)` in staging for 3 representative post-index queries
- Command + query count (`connection.queries`) before/after on seeded fixture

### Output format

Child PRD per wave: `PERF-waves` with checklist by PERF-xxx ID.

## Scope

- `system/services/` (emphasis: `class_calendar.py`, `membership.py`,
  `registration_checkout.py`, `graduation.py`, `payroll_rules.py`,
  `financial_dashboard.py`, `family_pricing.py`, `plan_change.py`,
  `asaas_billing_cycle.py`)
- `system/selectors/` (`graduation.py`, `plan_eligibility.py`,
  `person_selectors.py`)
- `system/views/` (`home_views.py`, `person_views.py`, `calendar_views.py`,
  `graduation_views.py`, `admin_views.py`)
- Querying properties under `system/models/`
- `system/signals.py`
- Indexes in `system/migrations/0001_initial.py` versus observed filter patterns
- Performance-test gap under `system/tests/`

## Out of scope

- Implementing corrections (execution through child PRDs by wave)
- Frontend / `register.js`
- Optimising external Asaas/Stripe calls (mentioned where they block admin home)
- Connection pooling / PgBouncer (Render/Supabase infrastructure)
- General architectural refactor (PRD-138)

## Impacted files

| File | Role in audit |
|---|---|
| `system/selectors/graduation.py` | CRITICAL hotspot PERF-001 |
| `system/views/home_views.py` | CRITICAL hotspots PERF-002, PERF-003 |
| `system/services/class_calendar.py` | CRITICAL hotspots PERF-004, PERF-005, HIGH PERF-013–016 |
| `system/models/membership.py` | CRITICAL hotspots PERF-006, PERF-007 |
| `system/services/family_pricing.py` | HIGH PERF-017 |
| `system/services/financial_dashboard.py` | CRITICAL PERF-008 |
| `system/services/payroll_rules.py` | CRITICAL PERF-009 |
| `system/services/plan_change.py` | HIGH PERF-018 |
| `system/services/membership.py` | HIGH PERF-019–021 |
| `system/selectors/plan_eligibility.py` | HIGH PERF-022–023 |
| `system/views/person_views.py` | HIGH PERF-024 |
| `system/selectors/person_selectors.py` | HIGH PERF-025 |
| `system/views/admin_views.py` | HIGH PERF-026 |
| `system/signals.py` | MEDIUM PERF-035 |
| `system/migrations/0001_initial.py` | Index section (Section 6) |

## Risks and edge cases

- Optimising `HomeView` without breaking role combinations (student + teacher +
  admin + guardian).
- An incorrect composite index may worsen writes in high-volume check-in.
- Caching `effective_tier` may stale a family discount if a legacy tier changes.
- `get_calendar_month_data` precomputes an entire month — monthly cache may
  serve stale data after class cancellation.
- Payroll depends on an order window — incorrect SQL aggregation changes payout.

## Rules and constraints

- Evidence by `file:line` or repeated named pattern.
- Classification: **CRITICAL** = likely degradation >1s or O(n²)/N+1 on a
  frequent route; **HIGH** = N+1 or full scan on an administrative route;
  **MEDIUM** = redundancy or missing index at moderate volume; **LOW** =
  micro-optimisation or acceptable in an MVP.
- Project migration policy: index changes through a dedicated schema PRD.

## Plan

### Wave P0 — Tests + home + graduation + properties
- [ ] Create `test_performance_graduation.py`, `test_performance_home.py`, `test_performance_membership.py` (baseline budgets)
- [ ] PERF-006/007: `resolve_effective_tier` + pause prefetch (coordinate with PRD-143)
- [ ] PERF-001/010/011: bulk `get_graduation_overview` (≤15 queries / 50 students)
- [ ] PERF-002/003/015: extract `selectors/home_context.py`; deduplicate dependents/billing
- [ ] PERF-008/009/012: financial SQL aggregation, payroll batch, plan catalog cache

### Wave P1 — Calendar and eligibility
- [x] PERF-005/013: `get_calendar_month_data` (`select_related main_teacher`) and batched staff check-ins — implemented. PERF-004: evaluated, not applicable (`SpecialClass` has no `class_group`)
- [x] PERF-014: memoised instructor groups (memoisation per `person` instance, request scope) — implemented. PERF-032: holiday cache reverted (cross-request cache incompatible with Django test isolation)
- [x] PERF-019/020: unified `get_membership_owner`/`get_active_membership` in billing — implemented. PERF-016/018: evaluated, not implemented (would change historical data displayed to the user — product decision)
- [x] PERF-022/027: PERF-022 (family eligibility prefetch) implemented; PERF-023 evaluated, no N+1; PERF-027 evaluated, not implemented (`select_for_update` concurrency risk)

### Wave P2 — Staging indexes + admin + backlog
- [ ] Index schema PRD from Section 6 (CRITICAL/HIGH) + staging `EXPLAIN`
- [ ] PERF-026: single AdminHub aggregation
- [ ] PERF-017/021/024/025/028/029: family pricing, person list, Asaas jobs
- [ ] Document final budgets in every `*Performance*` test

### Hotspot inventory (read-only audit)

Impact legend:

- **N+1**: 1 initial query + N queries inside loop
- **O(n×m)**: nested in-memory loop with per-item work
- **FTS**: potential full table scan without suitable index

#### CRITICAL

| ID | Location | Pattern | Estimated impact |
|---|---|---|---|
| PERF-001 | `system/selectors/graduation.py:23-25` | `for person in queryset: compute_graduation_progress(person)` | **Severe N+1**: ~5–7 queries per student (`get_current_graduation`, `_resolve_applicable_rule`, `count_approved_classes_in_window` with 2 queries). Admin overview: **O(n) queries**, n = active students. |
| PERF-002 | `system/views/home_views.py:78-233` | `get_context_data` stacks `get_today_classes_*`, `compute_graduation_progress`, `build_financial_dashboard`, `_build_billing_context`, `build_client_timeline`, payroll | **Request storm**: 15–40+ queries per complex persona before dependents. Most frequently accessed portal route. |
| PERF-003 | `system/views/home_views.py:567-591` (`_build_dependents`) | Per dependent: `compute_graduation_progress`, `get_graduation_history`, `get_today_classes_for_person`, `get_student_checkin_history`, `get_active_membership`, `get_membership_owner` | **O(d × Q)**: d dependents × ~15–25 queries each. Guardian with 3 dependents may **triple** home cost. |
| PERF-004 | `system/services/class_calendar.py:253-257`, `661-665` | `SpecialClass.objects.filter(date=today)` without role filter; complete daily list for each student/admin | **FTS + over-fetch**: loads every special class that day for a user needing only a subset. Scales with special classes, not enrolments. |
| PERF-005 | `system/services/class_calendar.py:1337-1434` (`get_calendar_month_data`) | Loads **all** active `ClassSchedule` rows (`1351-1355`); `day_num × day_schedules` loop (`1378-1405`) | **O(days × schedules)**: ~31 × \|schedules\| iterations/request. `main_teacher` accessed without `select_related` (`1398-1400`) → additional **N+1**. |
| PERF-006 | `system/models/membership.py:139-151` (`effective_tier`) | `@property` with `PlanTier.objects.filter(audience=..., weekly_frequency=...).first()` when `plan_price` is null | **Hidden query** per access. Loop in `family_pricing.py:35-36` calls property → **N+1** for legacy memberships. |
| PERF-007 | `system/models/membership.py:243-252` (`current_pause`) | `@property` with `pause_requests.filter(...).first()` | **N+1** in `get_today_classes_for_person:267-268` for every schedule entry reading membership without `prefetch_related('pause_requests')`. |
| PERF-008 | `system/services/financial_dashboard.py:200-204` | `_aggregate_net_inflows`: `for order in queryset` materialises **all** paid orders | **O(n) Python** over `RegistrationOrder` on every admin home. Should use `Sum(Coalesce('net_amount', 'total'))`. |
| PERF-009 | `system/services/payroll_rules.py:561-566`, `658-672` | `_build_student_entries_from_orders` calls `_get_order_students_for_groups` **per order** | **N+1**: 1 `ClassEnrollment` query × paid orders in month. Teacher home with active payroll. |
| PERF-010 | `system/services/graduation.py:22-45` (`count_approved_classes_in_window`) | 2 queries per person (regular + special check-ins) | Component of PERF-001; acceptable alone, but **multiplied by N students** becomes a bottleneck. |
| PERF-011 | `system/views/graduation_views.py:177` | `get_graduation_overview` in administrative view | Triggers PERF-001 in production without pagination or cache. |
| PERF-012 | `system/services/plan_change.py:314-320` | `build_plan_catalog`: `calculate_plan_change` per eligible plan | **O(plans × internal cost)** on billing home; each iteration touches membership/orders. Large catalog → perceptible latency. |

#### HIGH

| ID | Location | Pattern | Estimated impact |
|---|---|---|---|
| PERF-013 | `system/services/class_calendar.py:786-788` (`get_today_classes_staff_overview`) | `for special in ...: SpecialClassCheckin.objects.filter(special_class=special)` | **N+1**: 1 query per special class that day. |
| PERF-014 | `system/services/class_calendar.py:1212-1221` | `_get_instructor_class_group_ids` called twice in `assert_instructor_owns_schedule` / `_can_instructor_access_session` | **2 duplicate queries** (ClassGroup + ClassInstructorAssignment) per permission check. |
| PERF-015 | `system/views/home_views.py:159-176` | `get_today_classes_for_person` + `get_today_classes_for_instructor` + merge — overlapping schedule queries | Redundancy: same date/holiday/sessions queried multiple times in one request. |
| PERF-016 | `system/views/home_views.py:209-221` | `ClassSession` + `SpecialClass` `values_list('date')` without limit for teacher attendance count | **Potential FTS** over complete attended-session history. |
| PERF-017 | `system/services/family_pricing.py:34-51` | Loop over `membership.effective_tier` + individual `save` + `_sync_stripe_discount` | N tier queries + N writes; Stripe cancellation triggers in `mark_membership_canceled:471-483` per membership. |
| PERF-018 | `system/views/home_views.py:516-537` (`_build_payment_history_items`) | `MembershipInvoice.objects.filter(membership=...)` **without** `[:limit]` per billing tab | Loads complete invoice history × tabs (holder + dependents). |
| PERF-019 | `system/services/membership.py:690-702` (`get_guardian_billing_tabs`) | `_build_billing_tab` per dependent calls `get_active_membership` + `get_latest_open_order` | **2–4 queries × dependents**; duplicates `_build_dependents` work. |
| PERF-020 | `system/services/membership.py:636-658` (`get_membership_owner` / `_person_has_financial_records`) | `.exists()` on Membership and RegistrationOrder per candidate guardian | Up to **2 queries × guardians** in billing chain. |
| PERF-021 | `system/services/membership.py:471-483` (`mark_membership_canceled`) | `recompute_family_discounts_for_person` in loop per cancelled membership | Repeated family recomputation; each rescans family group. |
| PERF-022 | `system/selectors/plan_eligibility.py:253-264` (`build_eligibility_context_for_person`) | Loop over `family_people` → `_classify_person_audience` | **N+1 enrolments** per family member (`301-303`). |
| PERF-023 | `system/selectors/plan_eligibility.py:62-65` (`compute_veteran_member_since`) | Uncached membership query; called from `build_eligibility_context_for_person:264` | Extra query per eligibility/plan-change context. |
| PERF-024 | `system/views/person_views.py:145-146` | Loop over `_hydrate_person_relationships` on paginated list | CPU + ORM access per row; prefetch helps but `prepare_class_group_for_display` repeats work. `distinct()` filters (PERF-025) worsen it. |
| PERF-025 | `system/selectors/person_selectors.py:154-185` | Filters with multiple `Q` ORs over M2M/FK relationships + `.distinct()` | **JOIN explosion** + costly Postgres `DISTINCT` in person listing. |
| PERF-026 | `system/views/admin_views.py:31-105` | 17 separate `.count()` calls in admin hub | 17 DB round trips per page view; should be one aggregation or cache. |
| PERF-027 | `system/services/registration_checkout.py:595-607` (`apply_order_variant_stock`) | `resolve_order_item_variant` with query per item (`613-627`) | **N queries** (with `select_for_update`) per order item. |
| PERF-028 | `system/services/asaas_billing_cycle.py:44-48` | Loop in `find_due_asaas_memberships`: `_has_pending_renewal_order` per membership | **N× exists** on `RegistrationOrder` in billing job. |
| PERF-029 | `system/services/financial_dashboard.py:85-116` | `_build_local_totals`: multiple aggregates + repeated `RegistrationOrder` filters | 6+ separate aggregations; acceptable admin-only, but cumulative. |
| PERF-030 | `system/views/person_views.py:227-228`, `293-294` | `compute_graduation_progress` + `get_graduation_history` per detail/update | Duplicates PERF-010 for one person — fine alone, heavy in frequent modals. |

#### MEDIUM

| ID | Location | Pattern | Estimated impact |
|---|---|---|---|
| PERF-031 | `system/models/person.py:233-245` (`current_ibjjf_category`) | Property loads **all** `IbjjfAgeCategory` rows per access | Repeated query if property is used in a loop (list uses local cache in `_hydrate` — fine there). |
| PERF-032 | `system/services/class_calendar.py:265`, `421`, `521`, `736` | Repeated `Holiday.objects.filter(date=today)` in functions within same flow | 2–4 identical queries per schedule request. |
| PERF-033 | `system/views/home_views.py:409` | `get_student_checkin_history(dependent["person"])` without `limit` in tab | Duplicates history already loaded in `_build_dependents` (`limit=5`). |
| PERF-034 | `system/services/membership.py:232-234`, `290-292`, `409-411` | `Membership.objects.filter(stripe_subscription_id=...)` without `select_related('person')` before notification | Query + lazy-loaded person in Stripe webhooks. |
| PERF-035 | `system/signals.py:18-19` | `pre_save` `ProductVariant`: `.get(pk=...)` per save | +1 query/write on stock update; acceptable at low volume, sensitive in seed/import. |
| PERF-036 | `system/services/product_backorders.py:67-87`, `147-151` | `restock_variant` / cancellation loops with query per backorder/variant | N+1 in batch stock operations. |
| PERF-037 | `system/services/registration_checkout.py:150-212`, `271-304` | Wizard catalog: full table scan of active plans/products | O(n), acceptable in MVP; no HTTP/ORM cache. |
| PERF-038 | `system/views/calendar_views.py:88-97` | Extra `ClassSchedule` + `SpecialClass` queries for instructor IDs | Redundant with already-heavy `get_calendar_month_data`. |
| PERF-039 | `system/services/class_calendar.py:50-57` (`_training_class_group_ids`) | Enrolment query + possible `class_group_id` append | Extra query per schedule; could use person prefetch. |
| PERF-040 | `system/views/home_views.py:144`, `725-732` | `class_enrollments.filter(...).exists()` and complete instructor list | `exists` fine; `_get_active_instructor_choices` uncached on every home with teacher area. |
| PERF-041 | `system/services/membership_timeline.py:30-37` | `build_client_timeline`: family-event query | Single query with `select_related` — fine; suitable limit 30. |
| PERF-042 | `system/services/graduation.py:297-345` (`get_graduation_history`) | In-memory loop over graduations | CPU O(g); g small — no extra query in loop. |

#### LOW

| ID | Location | Pattern | Estimated impact |
|---|---|---|---|
| PERF-043 | `system/services/class_calendar.py:1138-1196` | `get_student_checkin_history`: two broad queries + Python sort | Limit 12 mitigates; `(person, status)` index would help. |
| PERF-044 | `system/views/person_views.py:137-142` | `IbjjfAgeCategory` loaded once per list view | Request-level cache — acceptable. |
| PERF-045 | `system/services/membership.py:725-729` (`has_dependents`) | Dedicated `.exists()` before `_build_dependents` | +1 query; mergeable with relationship prefetch. |
| PERF-046 | `system/services/class_calendar.py:1199-1208` | `_get_instructor_class_group_ids` merges two queries in Python | Low fixed cost; repeated (see PERF-014). |
| PERF-047 | `system/views/calendar_views.py:113-120` | `_resolve_checkin_actor`: exists + get Person | 2 queries per check-in POST — acceptable. |

### Section 2 — Querying properties (Django anti-pattern)

| Model | Property | Lines | Query |
|---|---|---|---|
| `Membership` | `effective_tier` | `139-151` | `PlanTier.objects.filter(...).first()` |
| `Membership` | `current_pause` | `243-252` | `pause_requests.filter(...).first()` |
| `Person` | `current_ibjjf_category` | `233-245` | `IbjjfAgeCategory.objects.filter(is_active=True)` |

Reference: [Django optimisation — defer unnecessary queries](https://docs.djangoproject.com/en/5.2/topics/db/optimization/#defer-unnecessary-queries).

### Section 3 — Signals with an extra query

| Signal | File | Line | Query |
|---|---|---|---|
| `pre_save` ProductVariant | `system/signals.py` | `18-19` | `ProductVariant.objects.only(...).get(pk=instance.pk)` |
| `post_save` → `restock_variant` | `system/signals.py` | `33-36` | Query chain in `product_backorders` (PERF-036) |

### Section 4 — Missing performance tests

Search for `assertNumQueries`, `django_assert_num_queries`, `query_count`,
`performance` under `system/` → **0 results**.

Priority gaps:

| Area | Recommended test (not written) |
|---|---|
| `get_graduation_overview` | Budget with N-student fixture |
| `HomeView` | Budget by role matrix |
| `get_calendar_month_data` | Budget + stability with M schedules |
| `get_today_classes_for_person` | No linear growth with unrelated special classes |
| `build_plan_catalog` | Budget versus number of plans |
| `apply_order_variant_stock` | 1 query per item → fixed budget |
| Indexes | Staging `EXPLAIN` smoke test (manual/optional CI) |

### Section 5 — `select_related` / `prefetch_related` (notable gaps)

| Location | Missing |
|---|---|
| `class_calendar.py:1351-1354` | `class_group__main_teacher` |
| `class_calendar.py:267` (`get_active_membership`) | `plan_price__tier`, `plan`, `pause_requests` |
| `membership.py` webhooks | `select_related('person')` on `stripe_subscription_id` lookups |
| `graduation.py:49-53` | Prefetch rules by belt if overview is optimised |
| `plan_eligibility._classify_person_audience` | Prefetch enrolments when loading family |

### Section 6 — Inferred missing indexes (`0001_initial.py`)

Relevant **existing** indexes (sample): `Membership(person, status)`,
`Membership(stripe_subscription_id)`, `PlanTier(audience, weekly_frequency)`,
`PlanPrice(tier, payment_method, billing_cycle, is_active)`,
`PreRegistration(holder_cpf, status)`,
`ProductBackorder(variant, status, created_at)`.

**Missing** (filters observed in code, without `Meta.indexes` / `AddIndex`):

| Table | Suggested columns | Motivation (query pattern) | Severity |
|---|---|---|---|
| `ClassSession` | `(date)` | `filter(date__gte, date__lte)`, `filter(date=today)` | HIGH |
| `ClassCheckin` | `(person_id, status)` | Student history, graduation count | HIGH |
| `ClassCheckin` | through join `session__date` | `filter(person=, session__date=today)` — consider `ClassSession(date)` first | HIGH |
| `ClassSchedule` | `(weekday, is_active)` | Global daily schedule | HIGH |
| `ClassSchedule` | `(class_group_id, weekday, is_active)` | Student's classes that day | HIGH |
| `SpecialClass` | `(date)` | Daily/monthly special classes | HIGH |
| `SpecialClass` | `(teacher_id, date)` | Instructor calendar ownership | MEDIUM |
| `Graduation` | `(person_id, -awarded_at)` | `get_current_graduation` | HIGH |
| `PersonRelationship` | `(source_person_id, relationship_kind)` | Dependents/guardian | HIGH |
| `PersonRelationship` | `(target_person_id, relationship_kind)` | `get_membership_owner` | HIGH |
| `RegistrationOrder` | `(person_id, payment_status)` | Billing, renewal check | CRITICAL |
| `RegistrationOrder` | `(paid_at)` or `(payment_status, paid_at)` | Payroll, financial dashboard | HIGH |
| `RegistrationOrder` | `(person_id, plan_price_ref_id, payment_status)` | `_has_pending_renewal_order` | HIGH |
| `ClassEnrollment` | `(person_id, status)` | Eligibility, payroll | HIGH |
| `ClassEnrollment` | `(class_group_id, status)` | Payout by class | MEDIUM |
| `Person` | `(cpf, is_active)` | Login/registration (partial unique) | MEDIUM |
| `Membership` | `(person_id, -created_at)` | `_ensure_active_membership_for_person` | MEDIUM |

Note: `ClassSession` already has `UniqueConstraint(schedule, date)` — composite
index `(schedule_id, date)` exists; an additional `date`-only index remains
useful for monthly ranges.

Supabase/Postgres policy: prefer composite indexes aligned with predicates
(`query-composite-indexes`); partial index on `is_active=True` where applicable.

## Correction proposal

> Correction proposal filled in by the consolidator in Jul/2026.

Actionable **test-first** (`assertNumQueries`) plan before each refactor.
Coordinates with PRD-143 (`home_views` extraction, service-level
`effective_tier`) and PRD-141 (dashboard consumes already lean context).

### Prioritised waves

| Wave | Focus | Overall risk | Dependencies |
|---|---|---|---|
| **P0** | Budget tests + querying properties + home/graduation | High | PRD-143 P1 (#5, #6) for `effective_tier`; extract selectors before optimising view |
| **P1** | Calendar + SQL aggregations | Medium–high | Green P0 budgets |
| **P2** | Staging indexes + admin hub + HIGH backlog | Medium | Schema PRD + staging/production confirmation |

---

### Wave P0 — Budgets and frequent-route hotspots

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| PERF-004 | Create `system/tests/test_performance_*.py` with budgets before refactoring | New tests; minimum seed fixtures | `rg assertNumQueries system/` ≥ 5 tests; local CI green | Low |
| PERF-006 | Move tier resolution to `membership_service.resolve_effective_tier(membership, tier_cache)`; deprecate query in `@property` | `system/models/membership.py` L139–151; `system/services/family_pricing.py` L34–51; `system/services/membership.py` | Property becomes annotated-field read or delegates to injected cache; `recompute_family_discounts` with 10 memberships ≤ 3 queries (test) | High |
| PERF-007 | Same for `current_pause`: `prefetch_related('pause_requests')` + helper without property query | `membership.py` L243–252; `class_calendar.py` L267–268 | `get_today_classes_for_person` fixture: no extra query per schedule when accessing pause | Medium |
| PERF-001, PERF-010, PERF-011 | Rewrite `get_graduation_overview`: bulk rule prefetch + annotated check-in counts | `system/selectors/graduation.py` L23–25; `system/services/graduation.py` L22–45 | Budget: ≤15 queries for 50 students; ≤25 for 200 students (test) | High |
| PERF-002, PERF-003, PERF-015 | Extract `system/selectors/home_context.py` (`build_home_context`); deduplicate `_build_dependents` versus billing tabs | `system/views/home_views.py` L78–233, L567–591; new selector | Single student ≤12 queries; guardian+3 dependents ≤35 queries (test) | High |
| PERF-008 | `_aggregate_net_inflows`: `aggregate(Sum(Coalesce(...)))` instead of Python loop | `system/services/financial_dashboard.py` L200–204 | Same financial total in fixture; 1 aggregate query versus O(n) | Medium |
| PERF-009 | `_build_student_entries_from_orders`: prefetch `ClassEnrollment` by order batch | `system/services/payroll_rules.py` L561–566, L658–672 | Monthly payroll with 20 orders ≤ 5 enrolment queries (test) | Medium |
| PERF-012 | `build_plan_catalog`: request-level cache of `calculate_plan_change` by `(membership_id, plan_price_id)` | `system/services/plan_change.py` L314–320 | 10 eligible plans: queries do not grow linearly 10× | Medium |

**Dependencies:** PERF-006/007 **coordinated** with PRD-143 findings #4, #5,
#30 (model cleanup). PERF-002/003 **coordinated** with PRD-143 #6 (thin
`home_views`).

**What NOT to do in P0:**
- Do not add Redis/memcached without baseline measurement.
- Do not remove `@property` without updating every call site (`rg effective_tier`).
- Do not optimise `HomeView` in place without extracting a selector (permission regression).

---

### Wave P1 — Calendar and operational N+1

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| PERF-004, PERF-013 | Filter `SpecialClass` by actor's `class_group_id__in`; prefetch staff check-ins | `class_calendar.py` L253–257, L661–665, L786–788 | Student with 2 classes: special-class queries do not scale with total that day | Medium |
| PERF-005 | `get_calendar_month_data`: filter schedules by weekday; `select_related('class_group__main_teacher')` | `class_calendar.py` L1337–1434, L1351–1355 | Budget ≤10 + 2×\|active schedules\| for month; no teacher N+1 | High |
| PERF-032 | Request-level cache for `Holiday.objects.filter(date=today)` | `class_calendar.py` L265, L421, L521, L736 | 1 holiday query per schedule request | Low |
| PERF-014, PERF-046 | Memoise `_get_instructor_class_group_ids` per request | `class_calendar.py` L1212–1221 | 2nd call in same request: 0 extra queries | Low |
| PERF-016 | Limit `values_list('date')` to a 90-day range for teacher KPI | `home_views.py` L209–221 | Query with `date__gte`; identical fixture result | Medium |
| PERF-018 | `MembershipInvoice` with `[:limit]` per billing tab | `home_views.py` L516–537 | Billing history loads at most N invoices per tab | Low |
| PERF-019, PERF-020 | Unify dependent billing: one ORM pass in `get_guardian_billing_tabs` | `membership.py` L636–702 | Billing queries do not duplicate `_build_dependents` | Medium |
| PERF-022, PERF-023 | `build_eligibility_context_for_person`: prefetch family enrolments + cache veteran | `plan_eligibility.py` L253–264, L62–65 | Family of 4 people ≤ 8 queries (test) | Medium |
| PERF-027 | `apply_order_variant_stock`: batch `select_related` variants before loop | `registration_checkout.py` L595–627 | Order with 5 items: ≤ 6 queries (test) | Medium |

**Dependencies:** green P0 test suite. PRD-143 eligibility API uses the
optimised selector (PERF-022).

**What NOT to do in P1:**
- Do not persistently cache a whole precomputed month without invalidation on class cancellation.
- Do not merge all of `class_calendar.py` in this wave (PRD-138 Wave 4 scope).

---

### Wave P2 — Indexes, admin hub, and backlog

| ID | Action | Files | Acceptance criterion | Risk |
|---|---|---|---|---|
| Section 6 | Schema PRD: add CRITICAL/HIGH indexes in dedicated migration | `system/migrations/0001_initial.py` or baseline-regeneration PRD; `calendar`, `registration_order`, `graduation` models | Staging `EXPLAIN ANALYZE`: 3 representative queries use Index Scan; document in child PRD | High (staging) |
| PERF-026 | `AdminHubView`: single aggregation or `Case/When` counts | `admin_views.py` L31–105 | 17 counts → ≤3 queries | Medium |
| PERF-017, PERF-021 | `recompute_family_discounts`: batch tier resolution + 1 Stripe sync per family | `family_pricing.py`, `membership.py` L471–483 | Cancel 3 memberships: 1 family recomputation, not 3 | Medium |
| PERF-024, PERF-025 | `person_selectors`: review ORM filters; index `PersonRelationship` | `person_selectors.py` L154–185; index migration | List 100 people filtered by class ≤ 10 queries | Medium |
| PERF-028 | `find_due_asaas_memberships`: prefetch pending orders | `asaas_billing_cycle.py` L44–48 | Billing job: no N× `_has_pending_renewal_order` | Low |
| PERF-029 | Consolidate `_build_local_totals` aggregations | `financial_dashboard.py` L85–116 | 6 aggregates → 2 queries with `Case` | Low |
| PERF-030 | `person_views` detail: reuse prefetched graduation selector | `person_views.py` L227–228 | Detail view ≤ 8 queries with graduation history | Low |
| PERF-035, PERF-036 | Signals/backorders: batch on stock import | `signals.py`, `product_backorders.py` | Stock seed with 50 variants: documented budget | Low |

**Priority P2 indexes (Section 6):** `RegistrationOrder(person_id,
payment_status)`, `ClassSession(date)`, `SpecialClass(date)`,
`Graduation(person_id, -awarded_at)`,
`PersonRelationship(source/target, relationship_kind)`.

**What NOT to do in P2:**
- Do not apply production indexes without staging `EXPLAIN` and a maintenance window.
- Do not use a partial index on `is_active` without measuring actual cardinality.

---

## Cross-PRD dependencies

| Dependency | Partner PRD | Direction | Block |
|---|---|---|---|
| `effective_tier` / `current_pause` outside model | **PRD-143** P0 (#4, #5, #30) | 143 ↔ 142 | PERF-006/007 synchronised |
| `home_views` → `home_context` selector | **PRD-143** P1 (#6, #26) | 143 → 142 | PERF-002/003 after view extraction |
| Optimised `plan_eligibility` | **PRD-143** + **PRD-141** API | 142 → 141 | PERF-022 feeds wizard API |
| `registration_forms` before JS | **PRD-143** P0 | 143 → 141 | Indirect (lower checkout load) |
| Shell/dashboard split | **PRD-141** P2 | 141 ← 142 | Fast home before splitting dashboard UI |
| God module `class_calendar` | **PRD-138** Wave 4 | 138 → 142 | P1 optimises; P2 does not split file |

## Test plan

### Tests to author

- [ ] `system/tests/test_performance_graduation.py` — `assertNumQueries` in `get_graduation_overview` with 50-student fixture
- [ ] `system/tests/test_performance_home.py` — budgets: student, teacher, guardian+2 dependents
- [ ] `system/tests/test_performance_calendar.py` — `get_calendar_month_data` and `get_today_classes_for_person`
- [ ] `system/tests/test_performance_membership.py` — `effective_tier` / `recompute_family_discounts_for_person` without N+1
- [ ] `system/tests/test_performance_payroll.py` — `calculate_monthly_payroll` with order fixtures

### Execution authorization

Not authorised in this PRD (read-only).

### Execution evidence

- [ ] Performance-test command and output — **pending**

## Visual validation

N/A (backend audit).

## ORM validation

- [x] Static reading of listed services/selectors/views/models
- [x] Index cross-reference in `0001_initial.py`
- [ ] Staging `EXPLAIN ANALYZE` — **not run**
- [ ] `connection.queries` before/after — **not run**

## Quality validation

- [x] PERF-001–047 inventory with severity and impact
- [x] Official Django source documented
- [x] Correction section filled in by consolidator (Jul/2026)
- [ ] Second-reviewer review — **pending**

## Evidence

| Evidence | Type | Result |
|---|---|---|
| `rg assertNumQueries system/` | Static search | 0 matches |
| Reading `graduation.py:23-25` + `graduation.py:129-184` | Code | N+1 confirmed by construction |
| Reading `membership.py:139-151` | Code | Query in property confirmed |
| Reading `0001_initial.py` AddIndex | Schema | Missing calendar/order/graduation indexes |
| `docs/prd/PRD-142-backend-performance-review.md` | Document | Created in this delivery |

## Implemented

- PRD-142 created with complete inventory
- `docs/prd/README.md` updated with PRD-142 entry
- **[2026-07-09] Partial Wave P0 execution** (outside original read-only scope,
  authorised by the user):
  - PERF-001/010/011: `get_graduation_overview` rewritten for bulk operation —
    `compute_graduation_progress_bulk` in `system/services/graduation.py`;
    `system/selectors/graduation.py` updated. Budget: 5 fixed queries
    independent of N (measured with 25 students; previously ~4 queries/student).
    Tests: `system/tests/test_performance_graduation.py` (`assertNumQueries`,
    bulk-versus-individual comparison).
  - PERF-008: `_aggregate_net_inflows` in
    `system/services/financial_dashboard.py` rewritten with
    `Sum(Case(When(net_amount__gt=0, ...), default=F("total")))` instead of a
    Python loop materialising orders. Tests:
    `system/tests/test_services.py::AggregateNetInflowsQueryBudgetTestCase`.
  - PERF-006/007 (`effective_tier`/`current_pause`): audited —
    `family_pricing.py` already uses `select_related("plan_price__tier", "plan")`,
    mitigating most N+1 for memberships migrated to `PlanPrice`; only the
    legacy branch (`plan` without `plan_price`) remains. Complete refactor into
    a dedicated service **not** executed — coordinated with PRD-143 (model
    cleanup), not independently blocking.
  - PERF-002/003/015 (home selector), PERF-009 (payroll batch), PERF-012
    (plan-change cache): **not run** in this round — coordinated with PRD-143 #6
    (`home_views` extraction), handled next (PRD-143).
  - Evidence: `manage.py test system` — 656 tests, OK (651 before this wave).
- **[2026-07-09] Wave P1 execution** (calendar and operational N+1):
  - PERF-013: `get_today_classes_staff_overview` — check-ins for that day's
    `SpecialClass` rows now fetched in bulk
    (`SpecialClassCheckin.objects.filter(special_class__in=specials_today)`)
    rather than one query per special class in the loop.
    `system/services/class_calendar.py`.
  - PERF-005: `get_calendar_month_data` — added
    `select_related("class_group__main_teacher")` to the `ClassSchedule`
    queryset, eliminating N+1 access to `main_teacher.full_name` inside the
    monthly day loop.
  - PERF-014/046: `_get_instructor_class_group_ids` memoised per `person`
    instance (private attribute on the object, populated once and reused by
    later calls in the same request). Safe because `request.portal_person` is
    freshly resolved on each request by middleware (`system/middleware.py`) —
    no cross-request/test leakage, unlike the process-level cache attempted for
    PERF-032 below.
  - PERF-019/020: `get_active_membership(person)` gained optional
    `billing_owner=None`; `_build_billing_tab` (`membership.py`),
    `build_billing_context`, and `build_dependents` (`home_context.py`) now
    resolve `get_membership_owner` once and reuse it, eliminating duplicate
    `_person_has_financial_records`/`_get_responsible_people` recomputation for
    every dependent.
  - PERF-022: `build_eligibility_context_for_person` — the whole family is now
    resolved in 2 fixed queries
    (`Person.objects.filter(pk__in=family_ids).select_related(...)` +
    `ClassEnrollment.objects.filter(person_id__in=family_ids, ...)`) rather
    than up to 3 queries per member inside the loop.
    `_classify_person_audience` gained optional `active_enrollments` to consume
    the preloaded batch without breaking existing single-person calls.
  - PERF-032 (**reverted**): first attempt used
    `django.core.cache.cache` (LocMemCache) to memoise
    `Holiday.objects.filter(date=today)` with a 300s TTL. **It broke test
    isolation**: Django's cache is not cleared between test methods (unlike the
    database, rolled back by `TestCase`), so a negative "no holiday" entry from
    one test leaked into another expecting a holiday. A second attempt using
    `post_save`/`post_delete` signals on `Holiday` to invalidate the key made
    the outcome worse (6 failures + 15 errors versus 2 before), because a test
    transaction rollback does not fire ORM signals — the reverse leakage
    (holiday created in cache, then removed through rollback) remained.
    **Decision**: the original PRD optimisation requested request-level cache
    (memoisation per execution), not cross-request/TTL cache — Django's cache
    framework is the wrong tool here. Fully reverted (`class_calendar.py` and
    `system/signals.py` returned to 5 direct
    `Holiday.objects.filter(date=today, is_active=True).first()` calls); not
    reimplemented in this round.
  - PERF-004: evaluated and **not implemented** — `SpecialClass` has no
    `class_group` field (`system/models/calendar.py:139-179`); it is an event
    open to the entire academy by design, not tied to classes. Filtering by the
    actor's classes, as originally suggested, would change functional
    behaviour (hide legitimate special classes). Actual daily volume is small,
    so the reported over-fetch does not remain a hotspot after reading the model.
  - PERF-016: evaluated and **not implemented** —
    `instructor_attendance_count` (home) is a total historical count of days
    with teacher attendance, displayed as `Aulas presentes` ("Classes
    attended") (`templates/home/partials/graduation_section.html:93`). Limiting
    it to 90 days would change the displayed value (functional correctness
    break, not only performance). The query already projects only `date`
    through `values_list`, and expected volume is low even over years.
  - PERF-018: evaluated and **not implemented** —
    `build_payment_history_items` feeds the `Histórico de pagamentos`
    ("Payment history") modal (`templates/home/dashboard.html:1059`), a complete
    financial statement by family. Truncating without pagination would hide
    real user payments — a product decision, not merely performance; explicit
    approval is required before limiting.
  - PERF-023: evaluated — `compute_veteran_member_since` is already 1 fixed
    query per `build_eligibility_context_for_person` call (not inside a loop);
    no N+1 to correct, only acceptable fixed cost.
  - PERF-027: evaluated and **not implemented** —
    `resolve_order_item_variant` intentionally uses `select_for_update()` per
    item (avoids stock races under concurrency); order volume is small (few
    items); consolidating into one query with variable colour/size filters per
    item risks a concurrency regression without meaningful benefit.
  - Evidence: `manage.py test system` — 662 tests, OK (same count before/after —
    no new test created in this wave, only N+1/duplication corrections checked
    against the existing suite).

## Cleanup findings

- God modules (`class_calendar.py`, `home_views.py`) concentrate hotspots —
  performance correction aligns with PRD-138 consolidation waves.
- Duplicate calls between `_build_dependents` and `_build_today_classes_tabs` /
  `get_guardian_billing_tabs` increase cost without functional benefit.

## Follow-up PRDs

| Suggested PRD | Scope |
|---|---|
| PRD-142-wave-1 (to create) | PERF-001–003, PERF-006–007 — home + graduation |
| PRD-142-wave-2 (to create) | PERF-004–005, PERF-013 — calendar |
| PRD-142-wave-3 (to create) | Section 6 indexes + staging `EXPLAIN` |
| PRD-142-wave-4 (to create) | `assertNumQueries` tests |

## Deviations from plan

None — read-only scope respected.

## Pending

- Approval for execution child PRDs by wave (P0–P2).
- Staging confirmation for P2 indexes.
- Actual post-P0 HTTP measurement (home, graduation overview, calendar).

## Final status

**Completed** — static audit delivered; consolidated correction proposal
(Jul/2026). Implementation and runtime measurement pending.

## PRD-145 reconciliation — 2026-07-13

- Historical status applies to the audit. Later sections record P0/P1/P2
  correction execution but do not authorise completion of indexes or staging
  measurements.
- PRD-145 validation ran 72 focused tests without regression and validated the
  ORM of registered profiles; the broad suite is recorded in PRD-145 itself.
- Indexes, `EXPLAIN ANALYZE`, and staging backfill remain unexecuted because
  they are outside the authorised environment.
- Reconciled state: **audit completed; partial local implementation; staging
  pending**.
