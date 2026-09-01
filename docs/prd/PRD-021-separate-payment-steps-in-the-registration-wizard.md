# PRD-021: Separate payment steps in the registration wizard

## Summary of the implementation

Split the current payment decision (concentrated in the Summary panel) into two distinct steps:

1. **Tuition payment** (`plan-payment`): the user chooses how to pay for the plan or opts for a trial class.
2. **Materials payment** (`materials-payment`): the user confirms payment for the materials in stock or reserves the sold-out ones.
3. **Summary** (`summary`): a final confirmation-only screen, with no payment decision.

## Demand type

New UX feature / registration flow refactoring.

## Current problem

The "Summary" step concentrates both the presentation of the summary and the decision of how to pay (card, PIX, or trial), mixing responsibilities. Materials and the plan have no clear, separate payment decision steps.

## Goal

- Make the flow clearer: each decision has its own moment
- Tuition: the user can pay or opt for a trial class
- Materials: the user is required to pay (if available) or reserve (if sold out)
- Summary: visual confirmation only before finishing

---

## Context Ledger

### Files read in full

- `static/system/js/auth/registration-wizard-clean.js` (3002 lines)
- `templates/login/register.html` (876 lines)

### Adjacent files consulted

- `system/forms/__init__.py`
- `system/models/membership.py`

### Limitations found

- None

---

## Execution prompt

### Persona

Development agent specializing in Django + vanilla JavaScript, following SDD + TDD.

### Action

Refactor the registration wizard, splitting the payment decision into 2 explicit steps.

### Context

The wizard uses STEP_DEFINITIONS and computeActiveSteps() to build the flow dynamically. The panels are HTML sections with `data-panel`. The payment logic lives in `checkoutActionButtons` and `renderSummary()`.

### Constraints

- No new migrations
- Backend compatibility: the `checkout_action` field stays the same
- A new `materials_action` field is added, but the backend may ignore it initially

---

## Scope

### The plan-payment step (new)

- Inserted after `materials` in the flow
- Shows a summary of the selected plan
- Option buttons:
  - The plan's method (card or PIX, according to the selected plan's `payment_method`)
  - `Fazer 1 aula experimental` (`Take 1 trial class`) (pay_later)
- On click, it sets `checkout_action` and advances to the next step

### The materials-payment step (new)

- Inserted after `plan-payment` in the flow
- If no material is selected: an informational message, with the normal Next button
- If materials are in stock: a list with a notice that they will be charged
- If materials are sold out: a list with a reservation option (registering interest)
- Advancing confirms and continues to the summary

### Summary (modified)

- Keeps the item list and the total
- Shows a summary of how the payment will be made (plan + materials)
- Removes `checkout-decision` (the payment buttons)
- Submission happens through the `Concluir cadastro` (`Finish registration`) button

## Out of scope

- Changes to the backend checkout processing
- Splitting the materials and plan charges into separate transactions

## Impacted files

- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`

---

## Plan

- [x] 1. Create the PRD
- [ ] 2. Add the plan-payment and materials-payment HTML panels
- [ ] 3. Modify the summary panel (remove checkout-decision)
- [ ] 4. Add STEP_DEFINITIONS and computeActiveSteps()
- [ ] 5. Create renderPlanPayment() and renderMaterialsPayment()
- [ ] 6. Modify renderSummary() to show how the payment will be made
- [ ] 7. Adjust the checkoutActionButtons listeners
- [ ] 8. Update the asset version

## Acceptance criteria

- [ ] When a plan is selected and the user advances, the `Pagamento da mensalidade` (`Tuition payment`) step is displayed with the correct options
- [ ] When the user chooses how to pay the tuition, the flow advances to `Pagamento dos materiais` (`Materials payment`)
- [ ] When there are no materials, the materials step shows an informational message and advances
- [ ] When there are materials in stock, it shows the list with a charging notice
- [ ] When materials are sold out, it shows the reservation option
- [ ] The final Summary shows the total and the payment method with no decision buttons
- [ ] The form is submitted through the `Concluir cadastro` (`Finish registration`) button on the Summary
- [ ] checkout_action is set correctly according to the user's choice
