# PRD-153: Fix the Recurring Stripe Billing-Period Filter in Public Registration

## Summary

In the public-registration wizard, selecting “Cartão” (“Card”) displays all three recurring Stripe prices (monthly, semiannual, and annual — approved and recorded in PRD-137 as cheaper loyalty options for longer cycles) together, regardless of the selected “Período de cobrança” (“Billing period”) pill (Monthly/Quarterly/Semiannual/Annual). This was **intentional** behavior documented in PRD-137 (“the display mechanism is not broken… do not change”), but the user found it confusing during the current review and requested a correction. When asked whether to reverse the business decision (monthly recurring only) or only fix display, the user chose to retain all three PRD-137-approved prices and fix only the filter: the period pill must also apply to Stripe and display one matching card at a time.

## Demand type

UI/JS fix (filter behavior), without catalog/price or business-rule changes.

## Current problem

`static/system/js/auth/register.js`, `getFilteredPlans` function (lines ~1498–1506):

```js
function getFilteredPlans() {
  var filtered = getEligiblePlansForCurrentPerson().filter(function (p) {
    if (planFilter.frequency !== null && p.weekly_frequency !== planFilter.frequency) return false;

    var isStripe = p.gateway_code === 'stripe_card';
    if (!isStripe && planFilter.cycle && p.billing_cycle !== planFilter.cycle) return false;
    if (planFilter.method && p.payment_method !== planFilter.method) return false;
    return true;
  });
  ...
}
```

The `!isStripe &&` deliberately bypasses the `planFilter.cycle` filter for every `PlanPrice` with `gateway_code === 'stripe_card'`. Therefore, with “Cartão” selected, all three tier Stripe prices (monthly/semiannual/annual) always appear together, regardless of the active period pill. Confirmed live in this session while validating a real registration (Asaas student profile, step 6, “Cartão” payment method).

This behavior was deliberately introduced/documented in PRD-137 (section “2. Recorrente Stripe só existe no ciclo mensal” / “Recurring Stripe exists only for the monthly cycle,” line 18: *“The frontend (register.js:1470-1472) already displays the Stripe card in any selected cycle tab… when the ‘Card’ filter is active — the display mechanism is not broken.”*) and reinforced as an explicit constraint (“Do not change the frontend Stripe-card display mechanism [already working correctly]”). It is not an unintended technical bug — it is a UX choice the user now wants changed.

## Goal

Make the “Período de cobrança” (“Billing period”) pill also filter `gateway_code === 'stripe_card'` plans, displaying **one** recurring card at a time (matching the selected period), while preserving all three PRD-137-approved commercial values (monthly BRL 229.14, semiannual BRL 1,195.00, annual BRL 2,265.00 for Adult 2x — and equivalent values for other tiers).

## Context Ledger

### Files read in full

- `docs/prd/PRD-137-recurring-stripe-long-cycles-and-broken-asaas-installments-in-new-catalog.md`
- `static/system/js/auth/register.js` (`getEligiblePlansForCurrentPerson`, `planCycles`, `planMethods`, `getFilteredPlans`, lines 1444–1514)
- `system/tests/test_register_wizard_contract.py` (project’s static-contract testing pattern for `register.js`/`register.html`)

### Adjacent files consulted

- `system/models/plan.py` (`BillingCycle`, `PlanPrice`) — confirms Stripe has only `monthly`/`semiannual`/`annual` rows (no `quarterly`).

### Internet / official documentation

Not applicable — internal JS filter-logic fix with no external API/SDK dependency.

### Context7 / MCPs / tools verified

Not applicable.

### Limitations found

- The project has no JS test runner (no `package.json`/Jest) — regression coverage uses a Django contract test (`SimpleTestCase` reading the static file), following the existing `test_register_wizard_contract.py` pattern, plus real manual browser validation.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery` (public-wizard visual behavior change)
- `lv-cleanup-audit`

## Understanding approved

The user chose between the two presented options (“revert to monthly only” vs “retain all three and fix display”): **retain all three PRD-137-approved values and fix display**, so the period filter also applies to Stripe.

## Scope

- `static/system/js/auth/register.js`: remove the `!isStripe &&` bypass in `getFilteredPlans`, so `planFilter.cycle` also filters Stripe plans.
- Bump the asset `?v=` (`register.js`) in the template and contract test.
- New/extended contract test confirming removal of the source-code bypass.
- Manual browser validation (desktop + mobile): with “Cartão” selected, each period pill shows exactly one matching recurring Stripe card.

## Out of scope

- Any Stripe plan catalog/value change (already approved and recorded in PRD-137).
- Filter behavior for Asaas (PIX/nonrecurring Card) — already correct and unchanged.
- PRD-117 (recurring contractual loyalty/grace period) — unrelated.

## Impacted files

- `static/system/js/auth/register.js`
- `templates/login/register.html` (`?v=` bump)
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases

- If a tier has no Stripe `PlanPrice` for the selected period (for example, no Stripe `quarterly`), no Stripe card appears for that pill — correct behavior because that offer does not exist, consistent with existing Asaas behavior when a combination is missing.
- `planCycles()` continues to use unfiltered `getEligiblePlansForCurrentPerson()` to decide which pills to display — unchanged; ensures “Semestral” (“Semiannual”)/“Anual” (“Annual”) still appears even if only Stripe or only Asaas has an offer for that period.

## Rules and constraints

- Smallest correct change: only the bypass line, without refactoring `getFilteredPlans` further.
- Asset version bump mandatory after editing JS (`CLAUDE.md` §2).
- TDD: write/adjust contract test before JS edit.

## Plan

1. Write/adjust contract test (Red) — bypass string must no longer exist; new `?v=` version present.
2. Remove bypass in `getFilteredPlans` (Green).
3. Run complete suite.
4. Validate in real browser (desktop + mobile): resume Carla Mendes registration (Asaas/PIX student — unaffected) and independently test period-pill changes with “Cartão” selected for an Adult 2x registration.

## Test plan

### Tests to author

- [x] Extended `test_register_template_and_script_contract`: assert bypass `if (!isStripe && planFilter.cycle` no longer exists in `register.js`; assert new `?v=` version in template.

### Execution authorization

Authorized by the user’s explicit decision in this session.

### Execution evidence

- Red: `manage.py test system.tests.test_register_wizard_contract.RegisterWizardStaticContractTestCase.test_register_template_and_script_contract` → failed on `?v=57` (still `?v=56`) before edit — bypass also present, confirming old state.
- Green (after fix): same command → **6/6 passed** (entire contract class).
- Complete suite: `manage.py test system` → **711/711 passed**.
- `manage.py check` → no issues.

## Visual validation

Validated in the real in-app browser (Student profile, Adult 2x tier, `registration_profile=holder`, without finalizing registration — step 6 only), reading rendered page text (screenshot capture unavailable in this session because of a temporary tool instability — `get_page_text`/DOM confirmed the same user-visible content):

| Selected period | Cards displayed with “Cartão” (“Card”) |
|---|---|
| Monthly | BRL 230.00/Monthly (Asaas) + **one** RECURRING BRL 229.14/month (Stripe) |
| Semiannual | **one** RECURRING BRL 1,195.00/month (Stripe) — exact PRD-137-approved amount |
| Annual | **one** RECURRING BRL 2,265.00/month (Stripe) — exact PRD-137-approved amount |
| Quarterly | BRL 660.00/Quarterly (Asaas) — no Stripe card (no quarterly Stripe `PlanPrice`, correct) |

Before the fix, Monthly + Card showed four cards (one Asaas + three simultaneous RECURRING); afterward, at most one RECURRING card appears per period, matching the selected pill. PIX checked without regression (Quarterly/PIX → BRL 630.00/Quarterly, one card, unchanged).

## ORM validation

Not applicable — no data/catalog change. No residual `PreRegistration`: validation did not submit the form (only navigated steps through programmatic clicks), confirmed by final ORM query (no record for the test CPF).

## Quality validation

- `manage.py check` → no issues.
- `manage.py test system` → 711/711 passed.

## Evidence

See “Execution evidence” and “Visual validation” above.

## Implemented

- [x] Removed `!isStripe &&` bypass from `getFilteredPlans` (`static/system/js/auth/register.js`) — `planFilter.cycle` now applies to every `gateway_code`, including `stripe_card`.
- [x] Incremented `register.js` `?v=` (`56` → `57`) in `templates/login/register.html`.
- [x] Extended contract test (`system/tests/test_register_wizard_contract.py`) covering bypass absence and the new asset version.
- [x] Validated in real browser: four billing periods + PIX without regression.

## Cleanup findings

No residue — fix removed one condition without introducing dead code. Local `isStripe` variable (used only by the bypass) was also removed because it had no remaining use.

## Follow-up PRDs

None identified.

## Deviations from plan

No deviation — visual validation used DOM/rendered-text reading instead of a screenshot because the capture tool was temporarily unstable in this session (page-reading mechanism confirmed functional and faithful to actual rendered content).

## Pending

No pending work.

## Final status

**Completed.** Presentation bug fixed (period filter now applies to Stripe), tested (contract + complete 711/711 suite), and validated live in the browser across all four billing periods, without changing any PRD-137-approved commercial value and without regression in the Asaas flow (PIX/nonrecurring Card).
