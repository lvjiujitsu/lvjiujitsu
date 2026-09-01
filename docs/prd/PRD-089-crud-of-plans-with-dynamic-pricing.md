# PRD-089: Plans CRUD with dynamic pricing

## Summary of the implementation
Expand the `SubscriptionPlan` model with dynamic pricing fields (the desired net amount, the gateway fees, and the cycle discount), implement automatic price calculation through `save()`, update the CRUD form with a real-time preview, and create the JSON seed with the academy's 72 initial plans.

## Demand type
New feature + a model change + a seed

## Current problem
The model stores only the final `price` manually. If the operator's fee changes, every plan has to be recalculated and re-edited individually. There is no traceability of the price's components.

## Goal
- The gateway fee (fixed + %) is configurable per plan and is reflected in the price automatically
- The cycle discount (monthly → quarterly → biannual → annual) is configurable and is reflected automatically
- The admin can create, edit, and delete plans through the existing CRUD
- The seed loads the 72 initial plans (3 categories × 2 frequencies × 3 gateways × 4 cycles)

---

## The calculation formula

```
gross_price = (base_net × n_meses × (1 − desconto_ciclo) + taxa_fixa) / (1 − taxa_pct)
```

Where:
- `base_net` = the desired monthly net amount (what the academy wants to receive per month)
- `n_meses` = 1 (monthly), 3 (quarterly), 6 (biannual), 12 (annual)
- `desconto_ciclo` = the discount granted for a longer-term commitment (e.g. 0.0257 = 2.57%)
- `taxa_fixa` = the gateway's fixed fee per charge (e.g. R$ 1.99 on Asaas PIX)
- `taxa_pct` = the gateway's percentage fee (e.g. 0.0599 = 5.99% on Stripe)

---

## New fields in SubscriptionPlan

| Field | Type | Description |
|---|---|---|
| `is_loyalty_plan` | BooleanField | Distinguishes Loyalty plans from Individual ones |
| `base_monthly_net_price` | DecimalField null/blank | The desired monthly net amount |
| `gateway_code` | CharField | The gateway identifier: asaas_pix, asaas_card, stripe_card |
| `gateway_fixed_fee` | DecimalField | The gateway's fixed fee (R$) |
| `gateway_percentage_fee` | DecimalField(4 decimals) | The percentage fee as a decimal (0.0429 = 4.29%) |
| `cycle_discount_percentage` | DecimalField(4 decimals) | The cycle discount as a decimal (0.0257 = 2.57%) |

The existing `price` field: it receives `default=0` and is computed automatically in `save()` whenever `base_monthly_net_price` is filled in.

---

## The initial plans (72 records)

| Category | Frequency | Monthly net base | Discounts (M/Q/B/A) |
|---|---|---|---|
| Individual | 2x/week | R$ 220.00 | 0% / 2.57% / 5.15% / 7.72% |
| Individual | 5x/week | R$ 250.00 | 0% / 4.00% / 8.00% / 12.00% |
| Loyalty | 2x/week | R$ 203.01 | 0% / 0.50% / 1.00% / 1.48% |
| Loyalty | 5x/week | R$ 220.01 | 0% / 2.28% / 4.55% / 6.82% |
| Family | 2x/week | R$ 203.01 | 0% / 0.50% / 1.00% / 1.48% |
| Family | 5x/week | R$ 220.01 | 0% / 2.28% / 4.55% / 6.82% |

The gateways: Asaas PIX (active), Asaas Card (inactive by default), Stripe Card (active).

---

## Impacted files

- `system/models/plan.py` — the new fields + save() + _compute_price()
- `system/forms/plan_forms.py` — the new fields in the form
- `system/tests/test_plan_models.py` — new calculation tests
- `templates/plans/plan_form.html` — the pricing section + the preview
- `templates/plans/plan_list.html` — show the price components
- `templates/plans/plan_detail.html` — the pricing detail
- `static/system/css/portal/plans.css` — styles for the plans CRUD
- `static/system/js/shared/plan-form.js` — the real-time calculator
- `static/initial_data/subscription_plans.json` — the 72 plans
- `system/management/commands/seed_system_initial_subscription_plans.py` — the seed
- `CLAUDE.md` — document the new seed

## Acceptance criteria
- [ ] On changing `gateway_percentage_fee` and saving, `price` reflects the new calculation
- [ ] On changing `cycle_discount_percentage` and saving, `price` reflects the new calculation
- [ ] Plans with no `base_monthly_net_price` keep their manual price intact
- [ ] The JavaScript preview shows the computed price in real time while the form is edited
- [ ] The seed creates the 72 plans idempotently; a second run does not duplicate them

## Plan
- [x] 1. The PRD
- [ ] 2. The model (it requires the destructive cycle)
- [ ] 3. The form
- [ ] 4. CSS + JS
- [ ] 5. The templates
- [ ] 6. The JSON seed
- [ ] 7. The seed command
- [ ] 8. Tests
- [ ] 9. CLAUDE.md
