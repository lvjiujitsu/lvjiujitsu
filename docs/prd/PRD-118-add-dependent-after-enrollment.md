# PRD-118: Adding a dependent after enrollment

## Summary
Allow a person already authenticated in the portal, whether a main student or a guardian, to add a dependent after the initial enrollment. The flow must start from the home, use its own authenticated wizard, collect the dependent's complete data, resolve the class, the plan, the payment, and the materials, and only create `Person`, `PortalAccount`, `PersonRelationship`, the enrollment, and the monthly fee after a valid completion.

## Demand type
A new product feature with impact on the authenticated UI, Django MVT, persistence, Asaas/Stripe payment, and visual validation.

## Current problem
- The public registration (`/register/`) allows dependents only during the initial enrollment.
- `HomeView` only populates `context["dependents"]` when `has_dependents(person)` is already true.
- `templates/home/dashboard.html` only renders the `Meus dependentes` ("My dependents") section inside `{% if dependents %}`.
- `system/tests/test_home_dependents_section.py` today encodes that a person with no dependents does not see the section.
- `system/urls.py` has no authenticated route to add a dependent after the enrollment.
- Using `/register/` as a shortcut would be incorrect: it is a public flow, it creates a complete registration, and it does not link the new student to the authenticated guardian.
- `RegistrationOrder` still requires a `Person`, so the payment for a dependent who does not exist yet must follow the pre-registration-before-person logic, as in PRD-040.

## Goal
An authenticated student or guardian can start "Adicionar dependente" ("Add dependent") from the home, complete a standardized wizard, and end with the dependent correctly linked, without creating partial data or bypassing the payment, the plan, the class, or the family relationship.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/prd/PRD-105-my-dependents-section-on-guardian-home.md`
- `docs/prd/PRD-106-guardian-material-purchase-for-dependent.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `system/urls.py`
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `system/tests/test_home_dependents_section.py`
- `system/forms/registration_forms.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/models/pre_registration.py`
- `system/models/registration_order.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/services/membership.py`

### Adjacent files consulted
- `system/services/class_overview.py`
- `system/services/registration_validation.py`
- `system/selectors/plan_eligibility.py`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

### Internet / official documentation
- Django 5.2 forms: https://docs.djangoproject.com/en/5.2/topics/forms/
  - Conclusion: user input must be processed through `POST`, validated server-side by `Form.is_valid()`, and persisted only from `cleaned_data`.
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
  - Conclusion: the final creation of the dependent, the relationship, the account, the enrollment, the order, and the subscription must happen inside `transaction.atomic`.
- Django 5.2 authentication: https://docs.djangoproject.com/en/5.2/topics/auth/default/
  - Conclusion: the flow must require an authenticated session through a mixin/guard equivalent to `PortalLoginRequiredMixin`.
- Stripe subscriptions integration: https://docs.stripe.com/billing/subscriptions/design-an-integration
  - Conclusion: a recurring subscription must keep using Billing/Checkout Sessions, not a manual `PaymentIntent`.
- Stripe Checkout overview: https://docs.stripe.com/payments/checkout
  - Conclusion: Checkout Sessions remain valid for a hosted or embedded payment; this PRD keeps the project's current session/return/webhook pattern.

### Context7 / MCPs / tools verified
- Context7: `/websites/djangoproject_en_5_2` for Django 5.2.
- `stripe-best-practices`: read; the billing/subscriptions reference requires the Billing APIs + Checkout Sessions for recurrence.
- PowerShell: working.
- `rg`: working.

### Limitations found
- The final implementation avoided a schema change: `flow_kind` and `owner_person_id` live in `PreRegistration.form_snapshot`, encapsulated by `system/services/dependent_registration.py`.
- A real external payment depends on the environment, the gateway, and active webhooks. The local validation covered the pre-registration creation, the payment return, and the family path; a new real charge for a dependent was not run.
- Optional materials were not incorporated into this delivery's wizard; they remain in the existing shop/material request flow after the dependent's creation.
- Full idempotency of a double submit/refresh of the completion was not implemented in this delivery.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `stripe-best-practices`
- `browser:control-in-app-browser`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: "implement it and validate it". This delivery implements and validates the PRD's functional core: the home with the action, the authenticated route, the server-side form, a paid pre-registration without creating a person, the payment return into the correct flow, and the completion covered by a family plan.

## Execution prompt
### Persona
A senior Django/MVT agent for LV JIU JITSU, following SDD, TDD, visual validation in the internal browser, and the project's payment rules.

### Action
Implement the authenticated post-enrollment dependent addition flow, from the home to the transactional completion, with the plan/payment/optional materials and the correct family relationship.

### Context
The system already has:
- the public wizard with dependents in `PortalRegistrationForm`, `register.js`, and `register.html`;
- `PreRegistration` for payment before creating a `Person`;
- `PersonRelationship` with `RESPONSIBLE_FOR`;
- an authenticated home that only shows already-existing dependents;
- Asaas and recurring Stripe payments with the return in `PaymentSuccessView`;
- PRD-040's rule: payment before the person.

### Constraints
- Do not reuse `/register/` as a visual or HTTP shortcut for an authenticated student.
- Do not create a dependent's `Person`, `PortalAccount`, `ClassEnrollment`, `PersonRelationship`, `Membership`, or `RegistrationOrder` before the correct completion.
- Do not store passwords in the snapshot.
- Do not apply a business rule in a template or in JavaScript.
- Do not expose the dependent route to an unauthenticated user.
- Do not allow a student to link a dependent to another person.
- Do not allow a CPF already active in another registration without an explicit administrative decision.
- Do not edit `staticfiles/`.
- Update the `?v=` of any changed CSS/JS.

### Acceptance criteria
- [x] An authenticated student with no dependents sees the `Dependentes` ("Dependents") section with an empty state and the `Adicionar dependente` ("Add dependent") action.
- [x] A guardian/student with dependents sees the existing list and the `Adicionar dependente` ("Add dependent") action.
- [x] A user with no active `portal_person` does not access the flow.
- [x] The canonical authenticated route is created at `GET/POST /dependents/add/`, without depending on `/register/`.
- [x] The wizard collects the personal data, health, martial experience, class, and plan.
- [ ] The wizard collects optional materials and a dedicated review.
- [x] The dependent's CPF is validated server-side against an active `Person`.
- [ ] A CPF pending in another pre-registration of the same guardian is blocked.
- [x] The selectable classes respect the eligibility by age/sex/category.
- [x] An individual plan requires payment before completing.
- [x] The guardian's active family plan can cover the dependent without a duplicated charge.
- [x] Recurring Stripe uses the existing Checkout/Billing; Asaas uses the existing pattern.
- [x] The payment return marks the pending flow as paid without automatically creating the person.
- [x] The completion creates the dependent, the portal account, the enrollment, the `RESPONSIBLE_FOR` relationship, the initial graduation, and the subscription/monthly fee atomically.
- [ ] Resubmitting or refreshing the completion is idempotent.
- [x] The home starts showing the newly created dependent and the correct monthly fee.
- [ ] The guardian can buy materials for the new dependent inside this wizard.
- [x] Focused tests cover the home, the anonymous block, the family path, the pending payment, and the payment return.
- [x] Desktop/mobile visual validation in the internal browser covers the empty state, the wizard, and the state with a dependent.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py check`
- New and adjusted focused tests.
- A proportional payment/pre-registration test.
- `node --check` for any changed JS.
- Local ORM validation.
- The internal browser on desktop/mobile, light/dark theme, a console with no critical error.
- A record of the real gateway's limitations, if not run.

### Output format
The implemented code, the PRD updated with the real evidence, the tests run, screenshots/a description of the internal browser, the diff cleanup, and the explicit pending items.

## Scope
- Create a section/empty state on the home for dependents.
- Create a dedicated authenticated flow to add a dependent after the enrollment.
- Reuse the public registration's data rules where it makes sense, but isolating the authenticated flow.
- Persist the draft/payment before creating the real person.
- Create the dependent and the family relationship only at the completion.
- Integrate the dependent's monthly fee into one of these conditions:
  - the guardian's active family plan when eligible;
  - contracting a plan of the dependent's own;
  - a request for administrative review for an exemption/barter, if enabled by a plan rule.
- Allow optional materials for the dependent before the final review.
- Update the tests and the documentation.

## Out of scope
- Rewriting the whole public wizard.
- Creating a new plan or changing prices.
- Resolving the guardian's plan change/loyalty period beyond what is necessary to add a dependent.
- Giving administrative access to the dependent.
- Multiple guardians in the same flow. The new dependent is born linked to the authenticated user; additional relationships stay with the existing/future administrative flow.
- Real validation in production/staging without explicit authorization.

## Impacted files
| File | Expected change |
|---|---|
| `system/forms/dependent_forms.py` | A new server-side form for the post-enrollment dependent |
| `system/services/dependent_registration.py` | The transactional rules for the draft, the payment, and the completion |
| `system/services/registration.py` | Fix the initial belt resolution from the registration |
| `system/views/dependent_views.py` | The authenticated wizard and the completion |
| `system/views/payment_views.py` | The payment return for the dependent flow |
| `system/views/home_views.py` | Expose the empty state, the list, and the dependents action |
| `system/urls.py` | The flow's canonical routes |
| `templates/home/dashboard.html` | The `Dependentes` ("Dependents") section with the action/empty state |
| `templates/dependents/dependent_registration.html` | The authenticated wizard |
| `static/system/css/dependents/dependent_registration.css` | The wizard's styling |
| `static/system/css/home/dashboard.css` | The empty state adjustment |
| `system/tests/test_dependent_registration.py` | The flow's backend contract |
| `system/tests/test_home_dependents_section.py` | Update the empty state and the action |
| `docs/prd/PRD-118-add-dependent-after-enrollment.md` | The final evidence |

## Risks and edge cases
- A guardian with an active family plan may or may not cover one more dependent; the rule must be explicit and tested.
- A minor dependent with no e-mail of their own still needs portal access; decide whether the password is created by the guardian or whether the account is born without a login of its own.
- A CPF already registered as an active student cannot be duplicated; any link to an existing person must be an administrative flow, not self-service.
- A Stripe payment can be confirmed by the webhook before the visual return.
- The user can abandon the flow after the payment and before the completion.
- The user can try to complete it twice.
- Materials paid for without a completion must remain linked to the draft, with no duplicated stock write-off.
- A guardian who is also an instructor/back-office person must keep the split home without losing the dependent action.
- A newly created dependent must appear in the monthly fee, the shop, the materials, and the home without requiring a logout/login.

## Rules and constraints
- The UI source of truth: `docs/UI-SCREEN-CONTRACT.md`.
- The payment-before-person source: PRD-040.
- The dependents-on-the-home source: PRD-105.
- The purchases-for-dependents source: PRD-106.
- The backend defines the permissions and the rules; the frontend only guides the experience.
- `transaction.atomic` is mandatory at the completion.
- Every write action uses `POST` and CSRF.
- The messages and the interface in pt-BR.

## Plan
- [x] 1. Write the Red tests for the home with a student with no dependents seeing the action.
- [x] 2. Write the Red tests for the authenticated route's permission.
- [ ] 3. Write the Red tests for a duplicate CPF and a pending draft.
- [x] 4. Write the Red tests for the path with an active family plan.
- [x] 5. Write the Red tests for the path with a paid plan of its own.
- [x] 6. Implement the authenticated draft's modeling through the `PreRegistration` snapshot.
- [x] 7. Implement the dependent's form and service.
- [x] 8. Implement the wizard's views/urls.
- [x] 9. Integrate the payment return and the completion.
- [x] 10. Adjust the home/template/CSS.
- [x] 11. Validate on desktop/mobile in the internal browser.
- [x] 12. Update the evidence, the cleanup, and the pending items.

## Test plan
### Tests to author
- `HomeDependentsSectionTestCase.test_student_without_dependents_sees_add_dependent_action`
- `HomeDependentsSectionTestCase.test_guardian_with_dependents_still_sees_add_dependent_action`
- `DependentRegistrationPermissionTestCase.test_anonymous_user_redirects_to_login`
- `DependentRegistrationPermissionTestCase.test_technical_admin_without_portal_person_cannot_start_self_service_flow`
- `DependentRegistrationFormTestCase.test_rejects_active_existing_cpf`
- `DependentRegistrationFlowTestCase.test_draft_does_not_create_person`
- `DependentRegistrationFlowTestCase.test_family_plan_finalizes_without_new_charge_when_eligible`
- `DependentRegistrationFlowTestCase.test_paid_plan_requires_payment_before_finalize`
- `DependentRegistrationFlowTestCase.test_finalize_creates_dependent_relationship_enrollment_and_account_atomically`
- `DependentRegistrationFlowTestCase.test_finalize_is_idempotent`
- `DependentRegistrationPaymentReturnTestCase.test_stripe_return_marks_dependent_flow_paid_without_creating_person`
- `DependentRegistrationPaymentReturnTestCase.test_asaas_return_marks_dependent_flow_paid_without_creating_person`

### Execution authorization
Local tests, the local ORM, local migrations, and the internal browser are authorized when the implementation starts. A real external payment still requires the environment/gateway per the operational guide.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration` — 7 tests, OK in the final focused run.
- `.\.venv\Scripts\python.exe manage.py check` — no issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_graduation` — 31 tests, OK.
- `.\.venv\Scripts\python.exe manage.py test` — 440 tests, OK in 102.699s in the final run.

## Visual hierarchy
- The home must use the operational F Pattern.
- The `Dependentes` ("Dependents") section sits near `Mensalidade` ("Monthly fee") and `Graduação` ("Graduation"), not in the administrative quick access.
- The `Adicionar dependente` ("Add dependent") action is a secondary button with a user/add icon.
- The empty state is discreet, with a short text and a clear action.
- The wizard uses the registration's same step pattern: logo/top, a progress bar, the step's title, the fields in a column, the primary action at the end.
- Required fields display a per-field error, not just a global alert.
- The light and dark themes must use the existing tokens.

## Wireframe
### Region: Home / Dependents
- Title: `Dependentes`
- Action: `Adicionar dependente`
- Empty state:
  - Main text: `Nenhum dependente vinculado.`
  - Supporting text: `Cadastre um dependente para vincular turma, plano e materiais.`
  - Button: `Adicionar dependente`
- State with data:
  - The already-existing list of dependents.
  - The `Adicionar dependente` button in the header.

### Region: Wizard / Top
- Back to the home.
- The LV logo.
- The progress `Etapa X de Y` ("Step X of Y").

### Region: Wizard / Steps
- Step 1: The dependent's data.
- Step 2: Health and emergency.
- Step 3: Martial experience and belt.
- Step 4: Class.
- Step 5: The plan and the payment condition.
- Step 6: Optional materials.
- Step 7: Review and completion.

### Region: Payment
- If an external payment is necessary, the local return must reopen the wizard in the correct state.
- If a family plan covers the dependent, show the `Coberto pelo plano familiar` ("Covered by the family plan") badge and skip the monthly fee payment.

### Screen states
- Loading: the class/plan catalog is still unavailable.
- Empty: no eligible classes/plans, with an objective message.
- Editing: the fields are fillable.
- Error: a per-field error and a summary at the top.
- Paid: a persistent badge and a clear next action.
- Completed: a success message and a return to the home.

## State machine
### The dependent flow
- `idle` -> `draft`
- `draft` -> `plan_selected`
- `plan_selected` -> `covered_by_family_plan`
- `plan_selected` -> `payment_pending`
- `payment_pending` -> `payment_confirmed`
- `covered_by_family_plan` -> `ready_to_finalize`
- `payment_confirmed` -> `materials`
- `materials` -> `materials_payment_pending`
- `materials_payment_pending` -> `materials_payment_confirmed`
- `materials` -> `review`
- `materials_payment_confirmed` -> `review`
- `review` -> `finalizing`
- `finalizing` -> `finalized`
- any state -> `canceled`
- any editable state -> `error`

### Home / Dependents
- `no_dependents` -> shows the empty state and the CTA.
- `has_dependents` -> shows the list and the CTA.
- `dependent_flow_pending` -> shows a continue-the-draft CTA when the user has an unfinished flow.

## Visual validation
### Desktop
- [x] The home with no dependents shows the action.
- [x] The home with dependents preserves the existing cards and the action.
- [x] The wizard with no overflow observed.
- [x] The post-payment return redirects to `/dependents/add/` per the automated test.

### Mobile
- [x] The buttons and the form render at 390x844.
- [x] The fields do not exceed the width (`overflowX=false`).
- [x] The progress and the actions do not cover the observed content.

### Theme
- [ ] Light with no contrast loss.
- [x] Dark validated in the internal browser's current state.

### Console
- [x] No critical JS error.
- [ ] No relevant static 404.

## ORM validation
- [x] Before the paid completion: `Person.objects.filter(cpf=<dependent_cpf>).exists()` is false in the `test_paid_plan_creates_pre_registration_without_person` test.
- [x] After the family completion: an active `Person` exists for the dependent.
- [x] An active `PortalAccount` exists for the dependent.
- [x] A `PersonRelationship(source_person=guardian, target_person=dependent, RESPONSIBLE_FOR)` exists.
- [x] An active `ClassEnrollment` exists for the chosen class.
- [x] `get_active_membership(dependent)` resolves through the guardian's family plan in the internal browser.
- [ ] No order/material/stock is duplicated after a refresh.

## Quality validation
- [x] `manage.py check`.
- [x] The focused tests.
- [x] A proportional payment/return test.
- [x] `node --check` not applicable: no JS was changed/created.
- [x] The diff reviewed with `lv-cleanup-audit`.
- [x] No `except: pass` introduced.
- [x] No `innerHTML` with user data introduced.
- [x] The dependents list keeps `select_related("target_person", "target_person__person_type")`.

## Evidence
- `rg -n "PRD-118|Adicionar dependente pós-matrícula" docs\prd\PRD-118-add-dependent-after-enrollment.md docs\prd\README.md` — found the PRD and the index line.
- `git diff --check -- docs\prd\README.md docs\prd\PRD-118-add-dependent-after-enrollment.md` — no whitespace error; PowerShell warned only about a future LF→CRLF normalization in the README.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section` — 7 tests, OK.
- `.\.venv\Scripts\python.exe manage.py check` — no issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_graduation` — 31 tests, OK.
- `.\.venv\Scripts\python.exe manage.py test` — 440 tests, OK.
- The internal browser on desktop: the home showed `DEPENDENTES` ("DEPENDENTS"), `Adicionar dependente` ("Add dependent"), the empty state; afterwards it showed `Dependente Browser PRD 118`, `BRANCA` ("WHITE"), `MENSALIDADE EM DIA` ("MONTHLY FEE UP TO DATE"), `2 aulas hoje` ("2 classes today"); the console with no errors.
- The internal browser on mobile 390x844: the home and the wizard with no horizontal overflow; the console with no errors.
- The local validation database: `Dependente Browser PRD 118` (`Dependent Browser PRD 118`) and the fictitious plan/subscription `Familiar Validação Browser` (`Family Browser Validation`) created to validate the family path with no external checkout.

## Implemented
- `system/forms/dependent_forms.py`: the post-enrollment dependent's server-side form with active-CPF validation, the password, the class, the martial history, and the financial condition.
- `system/services/dependent_registration.py`: the authenticated flow's snapshot, the paid pre-registration, and the transactional completion.
- `system/views/dependent_views.py`: the authenticated `GET/POST /dependents/add/`.
- `system/views/payment_views.py`: the dependent's payment return goes back into the correct flow and marks `plan_paid`.
- `system/views/home_views.py` and `templates/home/dashboard.html`: the `Dependentes` ("Dependents") section with an empty state and a CTA.
- `templates/dependents/dependent_registration.html` and `static/system/css/dependents/dependent_registration.css`: the dependent's sequential registration screen.
- `system/services/registration.py`: fixed the initial belt resolution so it does not resolve `white` as `red_white`.
- New/adjusted tests in `system/tests/test_dependent_registration.py` and `system/tests/test_home_dependents_section.py`.

## Cleanup findings
- The touched flow's diff reviewed.
- `git diff --check` on the delivery's files reported no whitespace error; PowerShell/Git warned only about a future LF→CRLF normalization in already-tracked files.
- No `except: pass`, `innerHTML`, `console.log`, `TODO`, or `FIXME` was introduced in the flow's new files.
- The fictitious validation data was left in the local database to evidence the flow in the internal browser.
- The worktree already had many pre-existing, unrelated changes, including PRDs 115–117 and registration/instructor/back-office adjustments; they were not reverted.

## Follow-up PRDs
_None created._

## Deviations from plan
- No migration/schema: the authenticated draft's link uses `form_snapshot["flow_kind"]` and `form_snapshot["owner_person_id"]`.
- No dedicated wizard JS: the screen is sequential and server-rendered, to reduce the rule surface in the frontend.
- The optional materials and the dedicated review were left out of this implementation.
- The real external charge validation was not repeated; the integration was covered by the pre-registration/return test and by the existing checkout service.

## Pending
- Integrate the optional materials into the wizard or create an explicit CTA to the shop with the newly created dependent.
- Implement full completion idempotency.
- Block a dependent's CPF that is pending in the same guardian's pre-registration.
- Create a specific test for an authenticated technician with no `portal_person` receiving a 403.
- Explicitly validate the light theme in the internal browser in a dedicated pass.

## Final status
The feature implemented and validated, with the limitations recorded.
