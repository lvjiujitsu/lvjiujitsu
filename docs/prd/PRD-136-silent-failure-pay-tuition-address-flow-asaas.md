# PRD-136: Silent failure of the "Pay tuition" button and confirmation of the Asaas address flow

## Summary

During manual validation of public registration on Render HG (Asaas card client), the "Pagar mensalidade" ("Pay tuition") button failed repeatedly without any visible error. The page simply restarted Step 6 with the payment method reset to PIX. The root cause was isolated by elimination: `PortalRegistrationForm.is_valid()` returns `False` because validation of `holder_class_groups`/`checkout_action` fails, and the view calls `form_invalid()`, which renders the same page again with HTTP 200. However, `templates/login/register.html` never renders `form.errors` for any field, so neither the user nor the investigating agent receives any indication that something failed. Diagnosis was possible only by reading `system/forms/registration_forms.py` and directly inspecting `sessionStorage` through DevTools.

The same investigation also observed, once and not again after cleanup, a corrupted value in the hidden `holder_class_groups` field: `"['1::Jiu Jitsu']"` (the Python representation of a list rather than the clean value `"1::Jiu Jitsu"`). No choice recognizes that string, so Django's native `MultipleChoiceField` validation rejects it and reproduces the same "silent reset" symptom. The precise source of that value was not confirmed. The symptom disappeared after deleting an orphaned `PreRegistration` with `draft` status that was referenced by the browser session (`session["pending_pre_registration_id"]`; the `HttpOnly` cookie cannot be cleared through `document.cookie`).

Finally, this PRD documents that the wizard's "Endereço (opcional — pré-preenche o pagamento)" ("Address — optional; pre-fills payment") mechanism **is implemented** in the backend. `ensure_pre_registration_asaas_customer` passes `holder_postal_code`/`holder_address` and related values to `asaas_client.create_customer`. However, it has **never been confirmed end to end** in this project. The address was left blank in every real test registration so far because it is optional, and the hosted Asaas checkout page therefore always requested the address again. No test has proven that pre-filling works when the wizard address is completed.

## Demand type

Bug discovery/documentation with no correction in this PRD. The user explicitly authorized documentation only: `apenas para memory, claude e agents terem documentação` ("only so memory, Claude, and agents have documentation"). This PRD is a basis for a future implementation requiring separate approval.

## Current problem

1. **Silent public-registration form failure**: when `PortalRegistrationForm` fails validation of JS-managed hidden fields (`holder_class_groups`, `checkout_action`), the view (`PublicRegisterView.form_invalid`, inherited from Django's standard `FormView`) renders the same page with HTTP 200 and no visible error. The template (`templates/login/register.html`) has no `{{ form.errors }}` anywhere, and `django.contrib.messages` is used only in the `except ValueError` / `except asaas_client.AsaasClientError` blocks inside `form_valid`, never in `form_invalid`. The end user sees "Etapa 6 de 8" ("Step 6 of 8") reset with no explanation and no indication of what to correct.
2. **Observed corruption in `holder_class_groups`**: during one registration attempt for the test client "Cliente Render Asaas Credito Dois" ("Render Asaas Credit Client Two"), the hidden `holder_class_groups` input was submitted with `"['1::Jiu Jitsu']"`, including literal brackets and single quotes. That format is produced only by applying `str()` to a Python list and not by any JS path identified in `static/system/js/auth/register.js`. It matches no real class, so Django's `MultipleChoiceField.clean()` silently rejects the submission (see problem 1). The `PreRegistration` (pk=2, status `draft`) stored a clean `holder_class_groups` value in the database (`['1::Jiu Jitsu']` as a valid Python list, not a corrupted string); the corruption was therefore absent from the saved snapshot. It appeared only in browser `sessionStorage` under `lv-wiz-v1` on the next attempt, together with a clean copy: `"ids":["['1::Jiu Jitsu']","1::Jiu Jitsu"]`, with both values in the same array. Deleting the orphaned `PreRegistration` referenced by the server session and reloading after clearing `localStorage`/`sessionStorage` resolved the symptom in the next two attempts, but whether the corrupted value originated in JS or backend-served data **was not confirmed**.
3. **The optional wizard address has never been tested end to end with Asaas**: the existing code (`system/services/registration_checkout.py::ensure_pre_registration_asaas_customer`, lines 667–694) reads `holder_postal_code`/`holder_address`/`holder_address_number`/`holder_address_complement`/`holder_address_neighborhood`/`holder_city` from the snapshot and sends them to `asaas_client.create_customer` (`system/services/asaas_client.py`, lines 73–110), which builds the Asaas payload fields `postalCode`/`address`/`addressNumber`/`complement`/`province`/`city`. This should pre-fill the cardholder's address on the hosted Asaas checkout page. However, the wizard address was left blank in every real test registration in this session and earlier documented sessions because it is optional, so this behavior has never been observed working in practice.

## Goal

Record these three findings with enough evidence for future agents (Claude/Codex/Cursor) and the team to implement a solution without rediscovering the root cause from scratch. Do not implement a correction in this PRD.

## Context Ledger

### Files read in full

- `system/views/auth_views.py` (`form_valid`, lines 60–230)
- `system/forms/registration_forms.py` (relevant excerpts: `checkout_action` field definition at lines 281–286, `_clean_plan_selection` at lines 587–628, `_has_invalid_class_group_selection` at lines 691–698)
- `system/services/registration_checkout.py` (`create_pre_registration_plan_payment` at lines 749–913, `ensure_pre_registration_asaas_customer` at lines 667–694, `resolve_catalog_plan` at lines 99–119)
- `system/services/financial_transactions.py` (`resolve_checkout_action_for_plan` at lines 26–35)
- `system/services/pre_registration.py` (`_build_pre_registration_snapshot` at lines 40–60, `build_wizard_form_snapshot` at lines 63–76, `normalize_snapshot_for_form` at lines 447–472, `build_pending_summary_from_pre_registration` at lines 294–319, `build_snapshot_class_group_summary` at lines 357–364)
- `system/services/asaas_client.py` (`create_customer` at lines 73–110, `create_credit_card_payment` at line 141 and following)
- `static/system/js/auth/register.js` (`selectClassGroup` at lines 2381–2400, `_syncClassGroupInputs` at lines 947–961, `syncClassesToForm` at line 963 and following, `readHiddenValuesByName` at lines 3561–3569, `normalizeIdList` at lines 354–363, `selectPlan`/`resolvePlanCheckoutAction`/`validatePlan` at lines 1654–1711)
- `templates/login/register.html` (complete searches for `messages`, `form.errors`, and `holder_class_groups`; confirmed that the `wizard-system-messages` message block exists at lines 52–58, but no field renders `.errors`)

### Adjacent files consulted

- `system/models/pre_registration.py` (`form_snapshot`, `status` fields)

### Internet / official documentation

Not applicable. This was an internal code investigation with no external library/SDK dependency.

### Context7 / MCPs / tools verified

- `mcp__claude-in-chrome__javascript_tool` was used to inspect `sessionStorage`, `localStorage`, hidden inputs, and the form's `FormData` in real time against `https://lvjiujitsu-hg.onrender.com/register/`.
- A local Django shell using `DJANGO_ENV_FILE=.env.hg` was used to inspect the real `form_snapshot` in Supabase HG. The session was read-only except for one targeted deletion of an orphaned draft `PreRegistration`.

### Limitations found

- The exact reason `holder_class_groups` received the value `"['1::Jiu Jitsu']"` was not confirmed. It was observed once and was not reproduced in a second clean attempt. Unconfirmed hypotheses: (a) a client-side path in `register.js` applies `String(someList)` instead of handling each element individually; (b) the value came from already-corrupted backend-served data through `pending_person_json`/`context["registration_initial_step"]` while the session referenced a stale `PreRegistration`. Neither hypothesis was conclusively validated.
- Address pre-filling in the Asaas checkout was confirmed only through code reading (`ensure_pre_registration_asaas_customer` → `create_customer`) and was never observed working in practice because no real test completed the wizard address fields.

## Required skills

- `lv-task-intake`
- `lv-prd`

## Understanding approved

The user explicitly authorized this during the session: `registre um novo PRD para corrigir e para que documentemos o que foi corrigido e mal implementado na descoberta do acionamento do botao problematico. apenas para memory, claude e agents terem documentação.` ("record a new PRD to correct this and document what was corrected and poorly implemented while discovering the problematic button trigger, only so memory, Claude, and agents have documentation"). This authorizes creating the PRD as a record, but does not authorize code implementation in this PRD.

## Execution prompt

Not applicable in this PRD (documentation only). A future implementation PRD must reread this document before proposing a correction.

## Scope

No implementation scope. Only record the findings above in `docs/prd/` and update `docs/prd/README.md`.

## Out of scope

- Implement rendering of `form.errors` in the wizard template.
- Investigate/correct the exact source of the `holder_class_groups` corruption.
- Test and confirm Asaas address pre-filling with real address data completed in the wizard.
- Any code change under `system/` or `static/`.

## Impacted files

No code file is changed by this PRD; only this PRD and the index.

## Risks and edge cases

- The silent form failure affects **any** real client registering on Render HG/production whose submission fails validation of a hidden field (`checkout_action`, `holder_class_groups`, `dependent_class_groups`, `student_class_groups`, `extra_dependents_payload`). The client sees the step "reset" with no explanation and may abandon registration without the team knowing why.
- Browser sessions whose `pending_pre_registration_id` points to an old `PreRegistration` with `draft` status (never finalized, for example because the user abandoned registration at payment) may contaminate later attempts with stale data read through `pending_person_json`, even after the user clears `localStorage`/`sessionStorage`. The Django session cookie is `HttpOnly`, so neither `document.cookie` nor `localStorage.clear()` clears it.

## Rules and constraints

This PRD introduces no new business rule; it is documentation only.

## Plan

1. Write this PRD with the complete finding (completed).
2. Update `docs/prd/README.md` with the entry (completed).
3. Wait for future prioritization/approval to open an implementation PRD that:
   - makes every `form.is_valid()` failure visible in the wizard, at minimum through a rendered generic error message and ideally by identifying problematic fields without exposing technical details to the end user;
   - investigates the observed corruption through controlled reproduction, such as an automated test forcing duplicate submission of `holder_class_groups` with distinct values;
   - defines an explicit policy for stale `pending_pre_registration_id`, such as time-based expiration or a "recomeçar cadastro" ("restart registration") button that clears the server-side session;
   - runs a real test with the optional wizard address completed and visually confirms that the hosted Asaas checkout opens with ZIP code, street, number, neighborhood, and city already populated.

## Test plan

### Tests to author

None in this PRD; tests belong to the future implementation PRD.

### Execution authorization

Not applicable.

### Execution evidence

Not applicable. This PRD's evidence is the investigation recorded above: code reading, live inspection through `javascript_tool`, and an HG Django-shell query.

## Visual validation

Not applicable.

## ORM validation

A read-only query was executed during the investigation and recorded as evidence, not as part of this PRD:

```powershell
$env:DJANGO_ENV_FILE = ".env.hg"
python manage.py shell -c "
from system.models.pre_registration import PreRegistration
prs = PreRegistration.objects.order_by('-pk')[:5]
for pr in prs:
    snap = pr.form_snapshot or {}
    print('PK', pr.pk, 'name', snap.get('holder_name'))
    print('  holder_class_groups repr:', repr(snap.get('holder_class_groups')))
"
```

Observed result: `PK 2` (`Cliente Render Asaas Credito`, "Render Asaas Credit Client", status `draft`) had `holder_class_groups = ['1::Jiu Jitsu']`, a clean Python list in the database; the corruption was not persisted there.

## Quality validation

Not applicable (documentation).

## Evidence

- A live-captured `sessionStorage` (`lv-wiz-v1`) excerpt showed the duplicated value: `"classSelections":[{"ids":["['1::Jiu Jitsu']","1::Jiu Jitsu"]}]`.
- Live-captured `FormData` from `#wizard-form` showed the actual submission: `holder_class_groups=['1::Jiu Jitsu']`, one malformed value.
- After deleting orphaned draft `PreRegistration` pk=2 and reloading with clean storage, the same flow (Steps 1→6, same class, same Asaas card plan) completed successfully and redirected to `https://sandbox.asaas.com/i/...`, a real Asaas checkout.

## Implemented

Nothing was implemented in this PRD; documentation only.

## Cleanup findings

- `PreRegistration` pk=2 (orphaned draft, test CPF `444.777.222-14`) was removed from the HG database during the investigation to unblock the test. This was cleanup of owned test data, not a schema or behavior change.

## Follow-up PRDs

A future implementation PRD must cover the four Plan items above after new explicit user approval.

## Deviations from plan

None. This PRD's scope was always documentation only, as requested.

## Pending

- Confirm or reject the hypothesis about the source of `holder_class_groups` corruption.
- Test Asaas address pre-filling end to end.
- Implement wizard form-error display.

## Final status

**Completed as documentation/discovery** — no code correction was scoped or authorized in this PRD.
