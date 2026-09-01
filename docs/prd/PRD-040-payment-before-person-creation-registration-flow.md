# PRD-040: Uncompromising registration flow with payment before creating a Person

## Summary of the implementation

Fix the public registration wizard so that no record in `Person` is created before the flow is fully complete. A registration may exist in the people table only after:

1. filling in the wizard data;
2. choosing the plan;
3. paying the tuition in Asaas;
4. returning to the tuition payment screen with a payment-confirmed message;
5. advancing to materials;
6. buying or skipping materials;
7. reviewing the complete summary;
8. clicking finish registration.

Any flow that creates a `Person`, `PortalAccount`, relationships, classes, or access before the final step is wrong.

## Demand type

Architectural fix + external integration + registration flow.

## Current problem

Earlier PRDs accepted an intermediate solution in which a `Person` was created with `is_active=False` after the plan submission, because `RegistrationOrder.person` is a required FK. That solution does not meet the product's expected contract: the user has not finished registering yet, and therefore must not exist as a registered person in the domain.

The correct behavior is to keep the wizard data as a pre-registration / pending transaction until the end. The plan payment and the materials payment belong to the pre-registration financial flow, not to the person's final registration.

## Goal

Make it mandatory and verifiable that:

- `Person.objects.filter(cpf=<wizard_cpf>).exists()` stays `False` until the final click on `Finalizar cadastro` (`Finish registration`);
- after paying the tuition in Asaas, the user returns to the wizard itself, on the tuition payment screen, with a payment-confirmed message;
- only after that does the user advance to choose materials;
- the materials payment and the summary happen before the person is created;
- the creation of `Person`, `PortalAccount`, relationships, classes, and access happens in a single atomic finalization.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-001-client-registration-with-cpf-validation.md`
- `docs/prd/PRD-088-full-registration-flow-review.md`
- `docs/prd/PRD-021-separate-payment-steps-in-the-registration-wizard.md`
- `docs/prd/PRD-038-materials-and-equipment-registration-wizard-step-redesign.md`
- `docs/prd/PRD-039-registration-flow-guardian-asaas-home-multiplier.md`
- `system/forms/registration_forms.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/views/asaas_views.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`

### Adjacent files consulted

- `docs/UI-SCREEN-CONTRACT.md`
- `system/models/registration_order.py`
- `system/models/pre_registration.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/services/asaas_checkout.py`

### Internet / official documentation

- Not used in this documentation regeneration. The rule derives from the user's current request and the flow's local contract.

### MCPs / tools verified

- PowerShell — working — file reading through `Get-Content -Raw -Encoding UTF8`
- `rg` — working — searching for references to the registration and Asaas flow

### Limitations found

- The current implementation still uses `RegistrationOrder.person` as a required FK, which prevents fulfilling this PRD without refactoring the pre-registration order modeling or using `PreRegistration` as the checkout's temporary holder.
- A schema change, if required, needs the destructive cycle to be run by the user. The agent cannot run `makemigrations` or `migrate`.
- A real Asaas payment requires an active ngrok, the correct `SITE_BASE_URL`, and human intervention when the external provider requires a manual action.

## Execution prompt

### Persona

Development agent specializing in Django + Asaas + transactional flows, following SDD + TDD + MVT with services.

### Action

Implement the registration flow in which the tuition and materials payments happen before the `Person` is created, and in which the atomic finalization is the only point where the real registration is created.

### Context

The public wizard in `templates/login/register.html` and `static/system/js/auth/register.js` collects data for a holder student, a holder student with dependents, and a guardian of student(s). The active payment method is Asaas. The flow must preserve the filled-in data when returning from Asaas and must never turn a pre-registration into a registered person before the final summary.

### Constraints

- do not create a `Person` before `register-finalize`;
- do not create a `PortalAccount` before `register-finalize`;
- do not create relationships, class links, or access before `register-finalize`;
- no error masking;
- no hardcoded host, URL, plan, CPF, product, or session state;
- do not use `request.build_absolute_uri()` for the Asaas `successUrl`;
- no autonomous migrations by the agent;
- mandatory full reading;
- mandatory automated and visual validation.

### Acceptance criteria

- [ ] Before the tuition payment, no `Person` exists for the CPFs entered in the wizard (verifiable: test + ORM).
- [ ] Submitting the tuition creates only a pre-registration state / pending financial order, with no `Person`, `PortalAccount`, family relationship, or class (verifiable: test + ORM).
- [ ] The Asaas `successUrl` returns to the wizard in the post-plan-payment state, keeping the filled-in data and showing `Pagamento confirmado` (`Payment confirmed`) on the tuition payment screen (verifiable: browser + console).
- [ ] After the plan confirmation, the user only advances to materials by clicking `Continuar para materiais` (`Continue to materials`) (verifiable: visual test).
- [ ] Materials are paid in a separate pre-registration order; paying or skipping materials does not create a `Person` (verifiable: test + ORM).
- [ ] The final summary shows the registration data, the paid plan, the materials paid or skipped, and the total amount before the person is created (verifiable: browser).
- [ ] `Person`, `PortalAccount`, relationships, and classes are created only in the final POST to `register-finalize` (verifiable: test + ORM).
- [ ] The finalization is atomic: if any final creation fails, nothing partial stays persisted as a real registration (verifiable: error test).
- [ ] A holder student with no dependents completes the whole flow without creating a `Person` before the end (verifiable: test + browser).
- [ ] A holder student with dependent(s) completes the whole flow without creating a `Person` for the holder or the dependents before the end (verifiable: test + browser).
- [ ] A guardian registering student(s) completes the whole flow without creating a `Person` for the guardian or the students before the end (verifiable: test + browser).
- [ ] The browser console has no critical JavaScript error during the Asaas return and the wizard resumption (verifiable: browser).
- [ ] The server terminal has no stack trace during checkout, return, materials, and finalization (verifiable: logs).

### Expected evidence

- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput` when JS/CSS/templates change
- shell checks that no `Person` exists before the end
- shell checks that a `Person` exists only after finalization
- desktop and mobile visual validation of the wizard
- real Asaas validation with an active ngrok

### Output format

Implemented code + tests + a PRD updated with real evidence + a record of the limitations.

## Scope

- Temporary persistence of the pre-registration before the `Person` is created.
- A tuition financial order linked to the pre-registration, not to a `Person`.
- A materials financial order linked to the pre-registration, not to a `Person`.
- Resuming the wizard after the Asaas return with the data filled in.
- An atomic finalization creating the real registration only in the last POST.
- Tests per registration type: holder student, holder student with dependent(s), guardian with student(s).

## Out of scope

- A broad visual redesign of the wizard.
- Changing the plan, price, or product catalog.
- Switching payment gateway.
- The administrative post-registration refund/cancellation flow.
- Creating migrations through the agent.

## Impacted files

| File | Expected change |
|---|---|
| `system/models/pre_registration.py` | Use or adjust the temporary pre-registration entity, when sufficient |
| `system/models/registration_order.py` | Allow a pre-registration order with no `Person`, when necessary |
| `system/services/registration.py` | Move the `Person` creation into the atomic finalization |
| `system/services/registration_checkout.py` | Create plan/materials orders linked to the pre-registration |
| `system/views/auth_views.py` | Adjust register, materials checkout, and finalize |
| `system/views/payment_views.py` | Resume the wizard after Asaas with no login and no person |
| `system/views/asaas_views.py` | Preserve `SITE_BASE_URL` in the `successUrl` |
| `templates/login/register.html` | Post-payment states and resumption data |
| `static/system/js/auth/register.js` | Wizard resumption, materials, and summary with no early registration |
| `system/tests/test_registration_flow.py` | Coverage of the whole contract |
| `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` | Final evidence |

## Risks and edge cases

- The required `RegistrationOrder.person` may require a schema change to support `PreRegistration`.
- The user pays the plan and closes the browser before the materials: the pre-registration must be recoverable by session and/or a secure token.
- The Asaas webhook arrives before the redirect: the pre-registration state must accept asynchronous confirmation.
- The user tries to reuse a CPF during an abandoned pre-registration: the CPF is not yet a `Person`, but there must be control over an expired/idempotent pre-registration.
- The user pays for materials and abandons before finishing: the orders stay linked to the pre-registration, with no person created automatically.
- A failure in the atomic finalization: it must not create a partial person.
- A guardian with multiple students: no CPF of the group may be persisted in `Person` before the end.

## Rules and constraints

- SDD before code.
- TDD for the implementation.
- No hardcoding.
- No error masking.
- No autonomous migrations.
- Mandatory full reading.
- Mandatory validation.
- Uncompromising rule: payment before person; the person only at the end.

## Visual hierarchy

- Reading pattern: F Pattern.
- Screen title: weight 700-800, the `--text` token.
- Sections/groups: weight 600, the `--text` token.
- Fields/labels: weight 500, the `--text` token.
- Help text/hints: weight 400, the `--muted` token.
- Primary action: `--brand-red`, weight 600.
- Secondary action: `--border` border, weight 500.
- Confirmed states: a visually distinct success badge, without replacing the advance button.

## Wireframe

### Region: Top

- The LV logo.
- The wizard's progress.
- A back button preserving the current state.

### Region: Initial registration

- Profile: student or guardian.
- Personal data.
- Health.
- Martial arts.
- Classes.
- Plan.

### Region: Tuition payment

- The plan summary.
- The Asaas payment actions.
- After returning paid: the same screen with a `Pagamento confirmado` (`Payment confirmed`) badge and a `Continuar para materiais` (`Continue to materials`) button.

### Region: Materials

- The product catalog.
- Variant configuration.
- The cart.
- The actions to pay by card, pay by PIX, or skip materials.

### Region: Final summary

- The holder's/guardian's data.
- Dependents/students.
- Classes.
- The tuition paid.
- The materials paid or skipped.
- The `Finalizar cadastro e acessar o sistema` (`Finish registration and access the system`) button.

### Screen states

- Loading: the wizard waiting for the catalogs.
- Empty: a catalog with no plans/products shows an explicit message.
- With data: the normal flow with the data preserved.
- Error: a field, payment, or resumption error appears without erasing the filled-in data.

## State machines

### Pre-registration

- States: `draft`, `plan_payment_pending`, `plan_paid`, `materials_payment_pending`, `materials_paid`, `ready_to_finalize`, `finalized`, `expired`, `error`.
- Transitions: `draft -> plan_payment_pending -> plan_paid -> materials_payment_pending -> materials_paid -> ready_to_finalize -> finalized`.
- Alternative transition: `plan_paid -> ready_to_finalize` when materials are skipped.
- Visual representation: every post-payment state must have an explicit badge and a single continuation action.

### Wizard

- States: `editing`, `submitting_plan`, `return_plan_paid`, `editing_materials`, `submitting_materials`, `return_materials_paid`, `review`, `finalizing`, `done`, `error`.
- Transitions: every Asaas return must reconstruct the correct step without creating a `Person`.
- Visual representation: no step may look complete without a real financial confirmation or an explicit user action.

## Plan

- [ ] 1. Context and full reading.
- [ ] 2. Contracts and modeling of a pre-registration with no `Person`.
- [ ] 3. Red tests for the absence of a `Person` before finalization.
- [ ] 4. Red tests for the Asaas plan return in the wizard.
- [ ] 5. Red tests for materials without creating a `Person`.
- [ ] 6. Red tests for the atomic finalization.
- [ ] 7. Green implementation in services/views.
- [ ] 8. Template/JS adjustments for the resumption.
- [ ] 9. Refactoring.
- [ ] 10. Full automated validation.
- [ ] 11. Desktop/mobile visual validation.
- [ ] 12. Real Asaas validation with ngrok.
- [ ] 13. Documentation update with evidence.

## Visual validation

### Desktop

- [ ] The complete flow with no overlapping text.
- [ ] The plan payment return shows the same tuition step with the confirmation.
- [ ] Materials and the final summary appear only after the plan is paid.

### Mobile

- [ ] The complete flow with no horizontal overflow.
- [ ] The continuation buttons stay visible and do not overlap content.

### Browser console

- [ ] No critical JavaScript errors.
- [ ] No relevant static 404s.

### Terminal

- [ ] No stack trace during registration, payment, return, materials, and finalization.

## ORM validation

### Database

- [ ] Before the final POST: `Person.objects.filter(cpf__in=wizard_cpfs).count() == 0`.
- [ ] After the final POST: the number of `Person` records matches exactly the expected holder/guardian and students/dependents.

### Shell checks

```python
from system.models import Person
cpfs = ["000.000.000-00"]
print(Person.objects.filter(cpf__in=cpfs).exists())
```

### Flow integrity

- [ ] Paid orders stay linked to the pre-registration until the finalization.
- [ ] The atomic finalization creates the person and the links exactly once.

## Quality validation

### No hardcoding

- [ ] The Asaas URLs use `settings.SITE_BASE_URL`.
- [ ] Plans and products come from real catalogs.

### No brittle conditional structures

- [ ] The flow states are explicit and tested.

### No `except: pass`

- [ ] Checkout and finalization errors are logged and propagated.

### No error masking

- [ ] A financial or finalization failure does not produce an apparent registration.

### No unnecessary comments or docstrings

- [ ] Comments only when they explain a non-trivial transactional contract.

## Evidence

- `.\.venv\Scripts\python.exe manage.py test system.tests.test_registration_flow --verbosity 2` — OK, 2 tests.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_registration_flow system.tests.test_forms --verbosity 2` — OK, 6 tests.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — OK, 165 tests.
- `.\.venv\Scripts\python.exe manage.py check` — OK, no issues.
- `node --check static\system\js\auth\register.js` — OK.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — OK, 169 files copied.
- `.\.venv\Scripts\python.exe manage.py seed_system_initial_product_catalog` — OK, 5 products updated with the unit price from the JSON.
- ORM shell: products priced `belt-lv=69.90`, `gi-lv-adulto=399.90`, `gi-lv-infantil=329.90`, `patch-kit-3=45.00`, `rash-lv=149.90`.
- Automated Playwright at `http://127.0.0.1:8000/register/` — OK:
  - An existing active CPF showed an error while typing.
  - The holder + dependent flow reached `step-plan`.
  - `step-checkout` no longer exists on the page.
  - `step-plan` showed plan selection per trainee.
  - The plan button became `Pagar mensalidade` (`Pay tuition`).
  - The post-plan materials step showed non-zero prices.
  - Skipping materials led to the summary with no false `Materiais confirmados` (`Materials confirmed`) message.
  - The browser console had no critical errors.

## Implemented

- The wizard's first POST creates/updates a `PreRegistration` and does not create a `Person`.
- `Person` is now created only in `register-finalize`.
- The Asaas success return for a pre-registration accepts `pre_registration_id` and `stage=plan|materials`.
- The tuition payment was moved into `step-plan` itself.
- `step-checkout` was removed from the template and from the JavaScript sequence.
- Plan selection became per trainee in the frontend.
- The false payment feedback for `pay_later`/skipping materials was removed.
- Existing-CPF validation now happens while typing.
- Material prices now come from the seed's JSON and were applied to the local database.

## Deviations from plan

- Real external validation in Asaas was not completed in this round because it depends on interaction outside the local browser with the provider's checkout. The code now generates pre-registration charges without creating a `Person`, but the provider's real confirmation still needs a manual test with Asaas/ngrok active.

## Pending

- Validate a real payment in Asaas with an active ngrok and a return to `payment-success`.
- Evolve the backend to persist the final financial history of the pre-registration payments in `RegistrationOrder` after the `Person` is created, should administrative finance require reconciliation by internal order.
