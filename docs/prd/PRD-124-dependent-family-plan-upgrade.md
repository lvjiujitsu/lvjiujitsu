# PRD-124: A dependent with an upgrade to a family plan

## Summary
Normalize the financial step of the dependent wizard to separate three decisions: use an already-active family plan, migrate the main person to a family plan, or contract a monthly fee of the dependent's own.

A scope update on 2026-07-05: the decision must not appear as three initial cards. The step must be simple, based on frequency/period filters, and the plan cards must derive the financial condition.

## Demand type
A business rule fix with impact on Django, the payment, and the modal's UI.

## Current problem
The "Usar plano familiar ativo" ("Use the active family plan") option appears even when the main person only has an individual plan. The backend only accepts that option when an active family `Membership` already exists; the JavaScript still removes family plans from the catalog, preventing the family upgrade at the moment the dependent is added.

After the first implementation, the screen ended up with too much explicit decision-making: the `Condição financeira` ("Financial condition") title, three cards before the filters, and the plan list shown before the user chooses the frequency and the billing period.

## Goal
Allow a main person with an individual plan to explicitly choose an eligible family plan while adding a dependent, also keeping the alternative of the dependent's own monthly fee.

In the interface, turn that choice into a natural plan selection: first the frequency and the period, then the eligible individual and family options. The rule remains validated in the backend through `financial_mode`/the selected plan.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-006-standardize-plan-change-screen-with-portal-design-system.md`
- `docs/prd/PRD-007-reformulate-plans-pricing-eligibility-and-targeting-adult-vs-kids-juvenile.md`
- `system/constants.py`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/services/dependent_registration.py`
- `system/services/membership.py`
- `system/services/plan_change.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/urls.py`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_commands.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`

### Adjacent files consulted
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `system/utils/plan_commercial.py`

### Internet / official documentation
- Django forms validation via Context7: `Form.is_valid()`, `Form.clean()`, and `Form.add_error()` keep the validation server-side and attach field errors.
- Stripe official docs: Checkout Sessions represent payment/subscription sessions and can be reconciled by internal references/metadata. URL: `https://docs.stripe.com/api/checkout/sessions`

### Context7 / MCPs / tools verified
- Context7 `/django/django` queried for form validation.
- Context7 `/websites/djangoproject_en_5_2` consulted on 2026-07-05 to confirm the validation through `Form.is_valid()`, `cleaned_data`, and `add_error()`.
- Browser validation planned in the in-app browser after the implementation.

### Limitations found
- The local seed has adult family plans, but no kids/juvenile family plans. This PRD does not invent new commercial prices.
- The existing pre-registration Stripe flow records the local payment confirmation and does not update an existing remote Stripe subscription. This PRD preserves that integration boundary and fixes the local wizard/rule.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user asked to "implement it" after the diagnosis that defined the three financial paths and the need for a fix in the form/service/JS.

## Execution prompt
### Persona
A senior Django agent, working with SDD + TDD, with special attention to the financial rule and server-side validation.

### Action
Implement the explicit financial mode in the dependent wizard, with tests and visual validation in the internal browser.

### Context
The main person may be on an active individual plan and add a dependent after the registration. When adding a dependent, they can:
- use an already-active family plan;
- migrate themselves to a family plan;
- contract a monthly fee of the dependent's own.

### Constraints
- No migration.
- No invented new pricing.
- Do not touch `staticfiles/`.
- Do not open an external checkout as a success validation.
- The business rule in the backend, not in the JavaScript.
- Preserve the pre-existing change in `system/migrations/0001_initial.py`.

### Acceptance criteria
- [x] The form accepts `financial_mode=family_existing` only if the main person already has an active family plan.
- [x] The form accepts `financial_mode=family_upgrade` only with an eligible family plan.
- [x] The form accepts `financial_mode=dependent_own` only with an individual plan compatible with the dependent.
- [x] A confirmed family upgrade payment creates the order/monthly fee for the main person, not for the dependent.
- [x] A confirmed own-monthly-fee payment keeps creating the order/monthly fee for the dependent.
- [x] The wizard shows the financial choices as clear cards and filters the plans according to the selected mode.
- [x] The final summary shows `Plano familiar do titular` ("The main person's family plan") or `Mensalidade própria` ("Own monthly fee") unambiguously.
- [x] The focused dependent test passes.
- [x] `manage.py check` passes.
- [x] The internal browser shows the financial step working inside the modal.
- [x] Step 5 no longer shows the `Condição financeira` ("Financial condition") title nor the three initial financial mode cards.
- [x] The plan list stays empty/instructive until the user chooses the frequency and the billing period.
- [x] After the frequency/period, selecting an individual card fills in `financial_mode=dependent_own`.
- [x] After the frequency/period, selecting a family card fills in `financial_mode=family_upgrade`.
- [x] `Veterano` ("Veteran") plans neither appear nor are accepted as a dependent's own monthly fee without eligibility.

### Expected evidence
- The real test commands and results.
- The local ORM confirming the orders/monthly fees where applicable.
- A snapshot/screenshot or an inspection of the internal browser.

### Output format
The implementation + the evidence + the limitations.

## Scope
- Add `financial_mode` as a server-side contract.
- Adjust the validation for an existing family plan, a family upgrade, and an own monthly fee.
- Adjust the dependent pre-registration's snapshot/persistence.
- Adjust the completion to apply the family upgrade to the main person.
- Adjust the UI/JS of the `Escolha o plano do dependente` ("Choose the dependent's plan") step.
- Update the focused tests.

## Out of scope
- Creating new kids/juvenile family plan prices.
- Updating an already-existing remote Stripe subscription.
- Refactoring the whole plan change flow.
- Changing the schema or the migrations.

## Impacted files
- `system/constants.py`
- `system/forms/dependent_forms.py`
- `system/services/dependent_registration.py`
- `system/services/registration_checkout.py`
- `system/selectors/plan_eligibility.py`
- `system/views/dependent_views.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_plan_eligibility.py`

## Risks and edge cases
- A main person on recurring Stripe may need a future routine to synchronize the remote subscription upgrade. This delivery fixes the local state and the pre-registration checkout the system uses.
- A guardian who does not train must not get an improper adult family plan; the validation must use the family eligibility and the selected plan.
- A tampered POST trying to use a family plan as an own monthly fee must fail.
- A tampered POST trying to use the active-family option with no family `Membership` must fail.

## Rules and constraints
- The plan validation is mandatory in the form.
- `use_family_plan` remains for compatibility, but stops being the only contract.
- `financial_mode` is the source of the financial decision.
- The JS only filters the presentation and fills the hidden fields.

## Visual hierarchy
- The title: `Plano do dependente` ("The dependent's plan").
- The subtitle: a short instruction to choose the frequency and the period.
- The filters: the weekly frequency, the billing period, and the payment method.
- The empty state: a short message while the frequency/period are not set.
- The catalog: eligible `Individual` and `Família` ("Family") cards after the minimum filters.
- Per-field errors below the corresponding group.

## Wireframe
### Region: The financial step
- Title: "Plano do dependente"
- Subtitle: `Escolha frequência e período para ver as opções disponíveis.` (`Choose frequency and period to see the available options.`)
- The plan filters:
  - The weekly frequency
  - The billing period
  - The payment method
- The plan list:
  - The initial state: `Escolha frequência e período para ver os planos.` (`Choose frequency and period to see the plans.`)
  - The "Individual" card: the dependent's own monthly fee.
  - The `Família` (`Family`) card: the main person's upgrade to a family plan.
  - The `Plano familiar ativo` (`Active family plan`) card: only when the main person already has an active family plan.

### Region: The footer
- The existing primary button: `Próximo` / `Ir para pagamento` (`Next` / `Go to payment`)

### Screen states
- No active family plan: the "Usar plano familiar ativo" card disabled.
- An upgrade with no eligible plan: an empty message in the catalog.
- A selected plan: the card with a selection border and the hidden fields synchronized.
- A server-side error: a message below the financial field.

## State machine
### The financial mode
- `idle`: the frequency/period incomplete; no plan shown.
- `dependent_own`: the user selected an individual plan card; it requires the dependent's individual plan.
- `family_existing`: the user selected the active family plan option; it requires an active family plan and does not require a new plan.
- `family_upgrade`: the user selected a family plan card; it requires an eligible family plan and a payment.

### The submit
- `idle` -> `validating` -> `redirect_checkout` or `finalize` or `error`.

## Test plan
### Tests to author
- `family_upgrade` creates the pre-registration and redirects to the checkout.
- The post-payment of `family_upgrade` creates the dependent and activates the family plan on the main person.
- `dependent_own` rejects a family plan.
- `family_existing` rejects a main person with no family plan.
- The modal's GET does not render the initial financial mode cards and keeps the contract's hidden fields.
- A dependent's own monthly fee rejects a Veteran plan without eligibility.

### Execution authorization
The local tests are authorized by the implementation request.

### Execution evidence
- A proportional Red: the focused dependent test failed before the production code for `family_upgrade`/plan tampering.
- The visual review's Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase.test_dependent_plan_step_is_filter_first_without_financial_mode_cards --verbosity 1` failed because the template still rendered `Condição financeira` ("Financial condition").
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 19 tests, OK.
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_eligibility --verbosity 1` -> 12 tests, OK.
- Green: `.\.venv\Scripts\python.exe manage.py check` -> no issues.
- The regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` -> 472 tests, OK.
- The visual review's Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 21 tests, OK.
- The visual review's Green: `node --check static\system\js\dependents\dependent_registration.js` -> no errors.
- The visual review's Green: `.\.venv\Scripts\python.exe manage.py check` -> no issues.
- The re-validation after adjusting step 5's error state: `node --check static\system\js\dependents\dependent_registration.js` -> no errors; `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 21 tests, OK; `.\.venv\Scripts\python.exe manage.py check` -> no issues.

## Visual validation
- The internal browser at `http://127.0.0.1:8000/home/`.
- The dependent modal opened through the `/dependents/add/?modal=1` iframe.
- The flow filled with fictitious data up to step 5.
- The `dependent_own` state: the card selected, the hint "Selecione a mensalidade própria do dependente." ("Select the dependent's own monthly fee."), a plan sample with the title `Individual`.
- The `family_upgrade` state: the card selected, the hint "Selecione o plano familiar que substituirá a mensalidade atual do titular." ("Select the family plan that will replace the main person's current monthly fee."), 18 cards shown with the title `Família` ("Family").
- The `family_existing` state: the card disabled for a main person with no active family plan.
- The desktop and mobile visual validation issued through a screenshot in the internal browser; with no apparent overlap.
- The internal browser's console: `[]` for errors/warnings.
- The 2026-07-05 review in the internal browser:
  - The modal opened at `http://127.0.0.1:8000/home/` through the `/dependents/add/?modal=1` iframe.
  - Step 5 showed "Plano do dependente", zero `.plan-card`, and zero `[data-financial-mode]` before the filters.
  - After `2x por semana` ("2x per week") + `Mensal` ("Monthly"), `afterFreqCards=0` and `cardsAfterFilters=6`.
  - The cards shown: `Individual`, `Individual`, `Individual`, `Família`, `Família`, `Família` (`Family`); `Veterano=false` (`Veteran=false`).
  - Selecting a Family card synchronized `#id_financial_mode option:checked = family_upgrade`.
  - Selecting an Individual card synchronized `#id_financial_mode option:checked = dependent_own`.
  - `Próximo` ("Next") advanced to "Materiais opcionais" ("Optional materials") without navigating to the checkout.
  - The internal browser's console: `[]`.

## ORM validation
Covered by the Django tests:
- `test_paid_family_upgrade_finalizes_with_owner_family_membership` confirms a paid order on the main person, an active family plan on the main person, and no order/monthly fee on the dependent.
- `test_paid_resume_finalizes_with_paid_plan_even_if_post_is_tampered` confirms that the post-payment restores the paid plan and ignores POST tampering.
- `test_family_upgrade_creates_pre_registration_without_person` confirms the pre-registration without creating the person before the payment, and the main person's checkout payload.

## Quality validation
`git diff --check` run with no whitespace errors; only the expected LF/CRLF conversion warnings on Windows.

## Evidence
- The focused tests, the full suite, and `manage.py check` passed.
- The internal browser validated the modal, the switching between the financial modes, the plan filter, and a clean console.
- `system/migrations/0001_initial.py` appears in the worktree only with a previously changed timestamp; it is not part of this implementation.

## Implemented
- A new `DependentFinancialMode` contract with `dependent_own`, `family_existing`, and `family_upgrade`.
- Server-side validation to block a family plan as an own monthly fee and to block a non-existent active family plan.
- The family upgrade creates the order/monthly fee on the main person and cancels the main person's previous monthly fees.
- The pre-registration saves `financial_mode` and the main person's plan payload when the flow is a family upgrade.
- The checkout now accepts `selected_plans_payload` as a native JSON list or a JSON string.
- The family eligibility now counts the number of adults, fixing adult + adult.
- The dependent wizard shows the financial cards and filters the catalog between `Individual` and `Família` ("Family").
- The 2026-07-05 review:
  - The three initial financial mode cards removed from step 5.
  - The step renamed to "Plano do dependente" ("The dependent's plan").
  - The plan list stays blocked behind an instructive message until the frequency and the period are selected.
  - The selected plan card sets `financial_mode` automatically.
  - The Veteran plans were removed from the own-monthly-fee UI and blocked in the form.
  - The `Próximo` ("Next") button keeps the error message when the frequency/period have not yet been chosen.

## Cleanup findings
No functional residue introduced in the scope. The preserved debts: updating an existing remote Stripe subscription and creating kids/juvenile family prices, both outside this PRD's scope.

## Follow-up PRDs
- `PRD-125-remote-synchronization-of-the-stripe-family-upgrade.md`: synchronize the family upgrade with an already-existing remote Stripe subscription.

## Deviations from plan
It was necessary to fix `PlanEligibilityContext` to count adults, because the previous model only had an `adult_active` boolean and did not release adult + adult family plans.

## Pending
- No blocking pending item in the implemented scope.
- Outside the scope: a kids/juvenile family price that does not exist in the local seed, and the remote synchronization of an existing Stripe subscription.

## Final status
Completed.
