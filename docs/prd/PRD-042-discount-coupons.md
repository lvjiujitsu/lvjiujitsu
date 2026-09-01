# PRD-042: Discount coupons

## Summary of the implementation

Create a discount coupon system applicable to the tuition payment in the public registration wizard. A coupon may grant a percentage discount (%) or a fixed-amount discount (R$) on the plan's total. It is applied before the payment is created in the gateway (Asaas or Stripe). The database records the applied coupon on the pre-registration. Seeds load the initial coupons from JSON.

---

## Demand type

New feature — model + service + UI + seed

---

## Current problem

There is no discount mechanism in the system. Promotions, trials, and negotiations require manually changing the plan's price or an operational waiver outside the system. There is no traceability of the discounts granted.

---

## Goal

Allow the user to enter a coupon code in the wizard's step-plan before paying. The system validates the coupon, computes the final discounted amount, and forwards that amount to the gateway. The coupon is recorded on the pre-registration for auditing. Seeds create pre-loaded initial coupons.

---

## Context Ledger

### Files read in full (mandatory before implementing)

- `system/models/plan.py` — `SubscriptionPlan`, price calculation
- `system/models/pre_registration.py` — `PreRegistration.form_snapshot`
- `system/views/auth_views.py` — `PortalRegisterView._create_pre_registration_plan_payment`, `_parse_selected_plan_payload`
- `system/services/asaas_client.py` — `create_pix_payment`, `create_credit_card_payment`
- `system/views/payment_views.py` — `PaymentSuccessView`
- `static/system/js/auth/register.js` — the step-plan flow, form submit
- `templates/login/register.html` — the wizard step-plan structure
- `system/constants.py` — `CheckoutAction`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` — a JSON structure reference

### Adjacent files consulted

- `system/models/__init__.py` — model registration
- `system/urls.py` — routes
- `system/tests/` — the existing test pattern
- `lvjiujitsu/settings.py` — no changes expected

### Internet / official documentation

- Django JSONField queries: https://docs.djangoproject.com/en/4.1/topics/db/queries/#querying-jsonfield
- Django `CheckConstraint`: https://docs.djangoproject.com/en/4.1/ref/models/constraints/

### MCPs / tools verified

- `manage.py check` — mandatory after the destructive cycle
- The destructive cycle — mandatory (the new `Coupon` model)

---

## Execution prompt

### Persona

Development agent specializing in Django 4.x, following SDD + TDD + MVT architecture with services. Special attention to input validation and data integrity.

### Action

Implement a complete coupon system: the model, a validation/application service, an AJAX verification endpoint, the wizard UI, an initial coupon seed, and tests.

### Context

The registration wizard lets the user select a plan and pay. The amount charged is `SubscriptionPlan.price`. The coupon must be applied to that amount before creating the payment in the gateway. The coupon is entered by the user in step-plan, validated through AJAX before the submit, and the discounted amount is sent to the gateway.

The pre-registration already has `form_snapshot` (JSON) — record the applied coupon there for auditing.

### Constraints

- no hardcoded coupon codes
- no manual migrations — the destructive cycle is run by the user
- an invalid or expired coupon → an error shown in the wizard without redirecting
- the seed accepts no `--` arguments; all configuration through `.env`
- idempotent: running the seed twice does not duplicate coupons

---

## Scope

### Model: `Coupon`

**File:** `system/models/coupon.py`

The Brazilian Portuguese strings in the code examples below are exact model labels and UI copy and are intentionally preserved as technical literals.

```python
class DiscountType(models.TextChoices):
    PERCENT = "percent", "Percentual (%)"
    FIXED   = "fixed",   "Valor fixo (R$)"

class Coupon(TimeStampedModel):
    code            = models.CharField("Código", max_length=40, unique=True, db_index=True)
    discount_type   = models.CharField("Tipo de desconto", max_length=10, choices=DiscountType.choices)
    discount_value  = models.DecimalField("Valor do desconto", max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(Decimal("0.01"))])
    max_uses        = models.PositiveIntegerField("Usos máximos", null=True, blank=True,
                                                  help_text="Nulo = ilimitado")
    uses_count      = models.PositiveIntegerField("Usos realizados", default=0)
    valid_from      = models.DateField("Válido a partir de", null=True, blank=True)
    valid_until     = models.DateField("Válido até", null=True, blank=True)
    is_active       = models.BooleanField("Ativo", default=True)
    description     = models.CharField("Descrição interna", max_length=200, blank=True)

    class Meta:
        verbose_name = "Cupom de desconto"
        verbose_name_plural = "Cupons de desconto"
        constraints = [
            CheckConstraint(
                check=Q(discount_type='fixed') | Q(discount_value__lte=100),
                name="coupon_percent_max_100",
            )
        ]
```

The retained model labels above translate respectively to: "Percentage," "Fixed amount," "Code," "Discount type," "Discount amount," "Maximum uses," "Null = unlimited," "Uses completed," "Valid from," "Valid until," "Active," "Internal description," "Discount coupon," and "Discount coupons."

> Do not create a relationship field between `Coupon` and `PreRegistration` — record only the code and the computed discount in the pre-registration's `form_snapshot`.

### Service: `system/services/coupon.py`

```python
def validate_coupon(code: str, total: Decimal) -> dict:
    """
    Validates the coupon and returns the calculated discount.
    Raises ValueError with a Brazilian Portuguese message on error.
    Returns: {'coupon_id': int, 'code': str, 'discount_type': str,
              'discount_value': Decimal, 'discount_amount': Decimal, 'final_total': Decimal}
    """

def apply_coupon(coupon_id: int) -> None:
    """Increments uses_count atomically."""
```

Validation rules (in `validate_coupon`):
1. The coupon does not exist → `ValueError("Cupom inválido.")` (`Invalid coupon.`)
2. `is_active=False` → `ValueError("Cupom inativo.")` (`Inactive coupon.`)
3. `valid_from` in the future → `ValueError("Cupom ainda não é válido.")` (`Coupon is not valid yet.`)
4. `valid_until` in the past → `ValueError("Cupom expirado.")` (`Expired coupon.`)
5. `max_uses` reached → `ValueError("Cupom esgotado.")` (`Coupon exhausted.`)
6. Percentage discount: `discount_amount = total * (discount_value / 100)`
7. Fixed discount: `discount_amount = min(discount_value, total)` — never negative
8. `final_total = max(total - discount_amount, Decimal("0.01"))` — a minimum of R$ 0.01

### AJAX validation endpoint

```
GET /cadastro/validar-cupom/?code=XXXXX&total=230.38
```

**View:** `ValidateCouponView`

Success response:
```json
{
  "valid": true,
  "discount_type": "percent",
  "discount_value": "10.00",
  "discount_amount": "23.04",
  "final_total": "207.34",
  "message": "Cupom aplicado: 10% de desconto"
}
```

Error response:
```json
{"valid": false, "error": "Cupom expirado."}
```

### Integration in the form/view

In `PortalRegistrationForm`:
- Add the field `coupon_code = CharField(max_length=40, required=False)`

In `PortalRegisterView._build_form_snapshot`:
- `coupon_code` is already captured by the POST fields loop

In `PortalRegisterView._create_pre_registration_plan_payment`:
```python
coupon_code = snapshot.get("coupon_code", "").strip().upper()
coupon_data = None
if coupon_code:
    coupon_data = validate_coupon(coupon_code, total)
    total = coupon_data["final_total"]

# ... create payment with the already-discounted total ...

if coupon_data:
    apply_coupon(coupon_data["coupon_id"])
    snapshot["applied_coupon"] = {
        "code": coupon_data["code"],
        "discount_type": coupon_data["discount_type"],
        "discount_value": str(coupon_data["discount_value"]),
        "discount_amount": str(coupon_data["discount_amount"]),
        "final_total": str(coupon_data["final_total"]),
    }
```

### UI in the wizard (register.js + template)

In the template's `step-plan`:
```html
<div class="form-field coupon-field" id="coupon-field-area">
  <label class="form-label" for="ui-coupon-code">Cupom de desconto <span class="form-label-optional">(opcional)</span></label>
  <div class="coupon-input-row">
    <input type="text" class="form-input" id="ui-coupon-code" placeholder="CÓDIGO DO CUPOM" maxlength="40" autocomplete="off" style="text-transform:uppercase">
    <button type="button" class="btn-coupon-apply" id="btn-apply-coupon">Aplicar</button>
  </div>
  <p class="form-field__error" id="coupon-error" hidden></p>
  <p class="coupon-success" id="coupon-success" hidden></p>
</div>
```

The retained UI literals above translate to "Discount coupon," "optional," "COUPON CODE," and "Apply."

In `register.js` — the new coupon block:
- On clicking `Aplicar` (`Apply`): calls `/cadastro/validar-cupom/?code=X&total=Y` through `fetch`
- Success: shows a green message, fills `id_coupon_code`, updates the amount shown on the selected plan's card
- Error: shows a red message
- On changing plan: clears the applied coupon and resets the field

In `elStepPlanNext.addEventListener`:
```javascript
setHidden('id_coupon_code', document.getElementById('ui-coupon-code').value.trim().toUpperCase());
```

### Hidden field in the template's form

```html
<input type="hidden" name="coupon_code" id="id_coupon_code" value="">
```

### Seed

**Command:** `seed_system_initial_coupons`

- Reads `static/initial_data/seed_system_initial_coupons.json`
- Depends on: nothing
- Idempotent: `get_or_create` by `code`
- An audit log per coupon created/already existing

**File:** `static/initial_data/seed_system_initial_coupons.json`

The `description` values in this JSON are exact initial-data content for the Brazilian Portuguese interface and are intentionally preserved.

```json
[
  {
    "code": "BEMVINDO10",
    "discount_type": "percent",
    "discount_value": "10.00",
    "max_uses": null,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Desconto de boas-vindas — 10% na mensalidade"
  },
  {
    "code": "PROMO50",
    "discount_type": "fixed",
    "discount_value": "50.00",
    "max_uses": 100,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Promoção fixa de R$ 50 de desconto"
  },
  {
    "code": "FAMILIA20",
    "discount_type": "percent",
    "discount_value": "20.00",
    "max_uses": null,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Desconto para planos família — 20%"
  },
  {
    "code": "TESTE100",
    "discount_type": "fixed",
    "discount_value": "999.00",
    "max_uses": 5,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Cupom de teste — cobre valor total do plano"
  }
]
```

The retained sample descriptions translate to "Fixed promotion with a R$50 discount" and "20% discount for family plans."

---

## Out of scope

- Coupons applicable to materials (tuition only in this PRD)
- Single-use-per-CPF coupons
- An administrative interface for creating coupons in real time (use the Django admin)
- Integration with Stripe's or Asaas's native coupons
- Coupons applied in the plan change flow (a future PRD)

---

## Impacted files

| File | Type of change |
|---|---|
| `system/models/coupon.py` | **new** — the `Coupon` model |
| `system/models/__init__.py` | export `Coupon`, `DiscountType` |
| `system/services/coupon.py` | **new** — `validate_coupon`, `apply_coupon` |
| `system/views/auth_views.py` | integrate `validate_coupon` + `apply_coupon` into `_create_pre_registration_plan_payment` |
| `system/views/coupon_views.py` | **new** — `ValidateCouponView` |
| `system/forms/__init__.py` | add `coupon_code` to `PortalRegistrationForm` (or a separate form) |
| `system/urls.py` | the `/cadastro/validar-cupom/` route |
| `templates/login/register.html` | the coupon field in step-plan + a hidden input |
| `static/system/js/auth/register.js` | coupon application logic through fetch |
| `system/management/commands/seed_system_initial_coupons.py` | **new** |
| `static/initial_data/seed_system_initial_coupons.json` | **new** |
| `system/tests/test_coupon_service.py` | **new** |
| `system/tests/test_coupon_views.py` | **new** |
| `CLAUDE.md` | update the seed table |

---

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Race condition: two users apply the same limited coupon at once | `apply_coupon` uses `F()` with `select_for_update` or validates after the increment |
| The coupon is applied but the payment fails → the coupon is consumed with no payment | `apply_coupon` is only called after the payment is confirmed (or use an atomic transaction with rollback) |
| The user changes the `total` in the DOM and sends a smaller amount | the service always recomputes from `SubscriptionPlan.price` in the backend — it never trusts the total sent by the client |
| A coupon with a discount larger than the total | `final_total = max(total - discount, Decimal("0.01"))` — never zero, to avoid rejection by the gateway |
| A coupon code in mixed case | normalize with `upper()` before comparing |

---

## Rules and constraints

- SDD before code
- TDD for the implementation
- no hardcoding
- no `except: pass`
- no manual migrations — instruct the destructive cycle
- mandatory full reading
- mandatory visual validation (apply a coupon in the wizard, confirm the discount shown)

---

## Plan

- [ ] 1. Read in full every file listed in the Context Ledger
- [ ] 2. Create `system/models/coupon.py` and register it in `__init__.py`
- [ ] 3. Request the destructive cycle from the user (a new model)
- [ ] 4. Create `system/services/coupon.py` (`validate_coupon`, `apply_coupon`)
- [ ] 5. Write the service tests — Red
- [ ] 6. Implement the service — Green
- [ ] 7. Refactor
- [ ] 8. Create `ValidateCouponView` and the route
- [ ] 9. Write the view tests
- [ ] 10. Add the `coupon_code` field to the form
- [ ] 11. Integrate `validate_coupon` + `apply_coupon` into `_create_pre_registration_plan_payment`
- [ ] 12. Add the hidden field to the template + the UI field in step-plan
- [ ] 13. Implement the JavaScript: the validation fetch, showing the discount, clearing on plan change
- [ ] 14. Create the initial coupons data JSON
- [ ] 15. Create the `seed_system_initial_coupons` command
- [ ] 16. Validate the complete flow in the browser
- [ ] 17. Final cleanup
- [ ] 18. Update CLAUDE.md

---

## Visual validation

### Desktop

- step-plan shows the coupon field below the plan cards
- typing an invalid code and clicking Apply → an inline red error message
- typing a valid code → a green message with the discount amount and the new total shown
- changing plan → the coupon cleared and the field reset
- clicking `Pagar mensalidade` (`Pay tuition`) with a coupon applied → the gateway receives the discounted amount

### Mobile

- the coupon field visible and usable on a small screen

### Browser console

- no JavaScript errors in the coupon validation through fetch

### Terminal

- no stack trace in the validation endpoint
- no stack trace when creating the discounted payment

---

## ORM validation

```python
from system.models import Coupon
Coupon.objects.filter(is_active=True).count()
# returns 4 (or the number of coupons in the JSON)

from system.models import PreRegistration
pr = PreRegistration.objects.latest('created_at')
pr.form_snapshot.get('applied_coupon')
# returns {'code': 'BEMVINDO10', 'discount_type': 'percent', ...}

from system.models import Coupon
Coupon.objects.get(code='BEMVINDO10').uses_count
# must have incremented after the payment was confirmed
```

---

## Quality validation

- `validate_coupon` never returns a silent `None` — it raises an explicit `ValueError`
- `apply_coupon` uses an atomic operation
- The total sent to the gateway is computed in the backend — it never trusts a POST field
- No unnecessary inline CSS/JS

---

## Evidence (fill in after implementation)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 failures
- [ ] `Coupon.objects.all().count()` == 4 after the seed
- [ ] A valid coupon applied in the wizard — the discount shown
- [ ] An invalid coupon → an error message
- [ ] The payment created in Asaas with the discounted amount
- [ ] `PreRegistration.form_snapshot['applied_coupon']` filled in
- [ ] `Coupon.uses_count` incremented after the payment was confirmed

## Implemented

_(fill in after completion)_

## Deviations from plan

_(fill in after completion)_

## Pending

_(fill in after completion)_
