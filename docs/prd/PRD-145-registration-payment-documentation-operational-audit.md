# PRD-145: Operational Audit of Registration, Payments, and Documentation

## Summary

Audit the actual state of PRDs 138–144 against code, tests, and observable execution; fix directly related gaps; validate every requested profile through the interface; review the project’s operational documentation; and remove exposed credentials from external Obsidian guides.

## Demand type

Operational audit + proven Django/UI fixes + Stripe/Asaas sandbox integration + documentation regeneration + security review.

## Current problem

- PRDs 138–144 mix read-only audits, later execution, and outdated final states.
- PRD-140 still records implementation and evidence as pending even though corresponding code exists in the working tree.
- External Render and Supabase guides contain plaintext secrets and credentials despite warning that the vault may be stored in a public repository.
- The client testing guide retains Claude-specific passages and contradictory claims about Asaas sandbox confirmation.
- The seven requested registration scenarios still lack consolidated browser, gateway, and ORM evidence in the current state.

## Goal

1. Reconcile PRDs 138–144 with actual code and results.
2. Fix bugs found in the flows exercised directly.
3. Create seven distinct accounts/scenarios through the interface:
   - student with Stripe;
   - student with Asaas;
   - guardian with student and Stripe;
   - guardian with student and Asaas;
   - student + administrative access;
   - administrative-only person;
   - instructor.
4. Validate desktop and mobile, console, terminal, sandbox gateway, and local ORM.
5. Update the five external guides and affected internal contracts.
6. Deliver test usernames and passwords without exposing infrastructure secrets.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `docs/prd/README.md`
- `docs/prd/PRD-138-architectural-audit-single-flow-and-consistency-of-mvp.md`
- `docs/prd/PRD-139-full-coverage-audit-file-by-file-inventory.md`
- `docs/prd/PRD-140-dependent-wizard-fixes.md`
- `docs/prd/PRD-141-frontend-problem-review.md`
- `docs/prd/PRD-142-backend-performance-review.md`
- `docs/prd/PRD-143-mvt-views-models-and-forms-review.md`
- `docs/prd/PRD-144-implementation-pending-items-july-2026-scan.md`
- The five `comandos-*.md` files identified by the user in the Obsidian vault.

### Adjacent files consulted

- Current flows under `system/models/`, `forms/`, `services/`, `selectors/`, `views/`, `urls.py`, `templates/login/register.html`, `static/system/js/auth/register.js`, and registration/payment tests.
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` and PRD-058.

### Internet / official documentation

- Django 5.2: https://docs.djangoproject.com/en/5.2/topics/db/optimization/
- Stripe CLI: https://docs.stripe.com/stripe-cli/triggers and https://docs.stripe.com/cli/listen
- Asaas sandbox payment confirmation: https://docs.asaas.com/reference/confirm-payment
- Asaas sandbox FAQ: https://docs.asaas.com/docs/sandbox-1
- ngrok agent/CLI: https://ngrok.com/docs/agent/cli and https://ngrok.com/docs/agent/api
- Render Django: https://render.com/docs/deploy-django
- Supabase Data API/RLS: https://supabase.com/docs/guides/api/securing-your-api and https://supabase.com/docs/guides/database/postgres/row-level-security

### Context7 / MCPs / tools verified

- Context7 consulted for Django 5.2, Stripe CLI, and Supabase.
- In-app browser connected to the real `http://localhost:8000/register/` route.
- Local Django server, ngrok, and Stripe CLI detected as active.

### Limitations found

- Database in scope: local SQLite. HG/production will not be changed.
- Asaas and Stripe are in sandbox/test mode; no real charge is authorized.
- Official Asaas documentation is temporarily contradictory: the specific, more recently updated reference publishes the sandbox confirmation endpoint, while the FAQ still says it does not exist. The flow must retain a sandbox-interface fallback.
- Credentials already exposed in an external repository require rotation at the providers; this PRD removes values from files but does not authorize external rotation.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery` when there is a visual change
- `lv-cleanup-audit`
- `browser:control-in-app-browser`
- `supabase` for the HG guide

## Understanding approved

The current request authorizes an audit, local fixes, tests, interface use, creation of local/sandbox data, and updates to the five identified documents. It does not authorize deployment, push, HG/production writes, or external credential rotation.

## Execution prompt

### Persona

Senior Django reviewer and operator focused on traceability, sandbox payments, documentation security, and visual validation.

### Action

Compare PRDs with actual state, write tests before fixing behavior, register the scenarios through the UI, verify gateway/ORM, and update contracts and guides.

### Context

The working tree contains extensive preexisting user changes; preserve everything outside scope and edit only directly necessary files.

### Constraints

- Do not expose keys, tokens, connection strings, or infrastructure passwords.
- Do not write to HG/production.
- Do not declare payment confirmed without sandbox and ORM evidence.
- Do not create `Person` before pre-registration finalization.
- Do not edit `staticfiles/`.

### Acceptance criteria

- [x] PRDs 138–144 reconciled with current evidence.
- [x] Secrets removed from external guides; placeholders and rotation instructions present.
- [x] Seven scenarios registered through the interface with deliverable credentials.
- [x] Student/guardian Stripe scenarios confirmed through hosted sandbox checkout and ORM.
- [x] Student/guardian Asaas scenarios confirmed through sandbox and ORM.
- [x] Administrative/instructor profiles persisted with correct roles and state.
- [x] Desktop and mobile render without blocking overflow or critical console errors.
- [x] `manage.py check`, focused tests, and a proportionate suite executed.
- [x] Internal and external documentation aligned with observed behavior.

### Expected evidence

- Test/check commands and outputs.
- Desktop and mobile snapshots/screenshots.
- Sandbox gateway events without unnecessarily revealing sensitive IDs.
- Consolidated ORM query for the seven scenarios.
- Documentation diff without secrets.

### Output format

Closure in English with implemented work, evidence, unvalidated items, pending work, test credentials, and final status.

## Scope

- PRDs 138–145 and index.
- Public registration, finalization, Stripe/Asaas payments, and operational profiles.
- Affected internal registration/payment/seed/UI contracts.
- Five external guides identified by the user.

## Out of scope

- Deploy/push.
- HG/production writes, reset, migration, seed, or backfill.
- Actual key rotation in external dashboards.
- Implementing all PRD-144 P2/P3 structural debt unrelated to a failure observed in these flows.

## Impacted files

- Defined after the audit and reproduced failures; always recorded under `Implemented`.

## Risks and edge cases

- Existing CPFs/emails block progress; generate new valid fictional data.
- Stripe webhooks create auxiliary events and fixture IDs distinct from the original checkout.
- Asaas confirmation may require the interface fallback because of the API/documentation contradiction.
- Guardian + student requires distinguishing the guardian account, dependent, membership, and charge.
- Administrative/instructor profiles may produce a pending request instead of immediate access; validate the actual contract before claiming active credentials.
- Clear the browser session between registrations to avoid rehydrating a previous wizard.

## Rules and constraints

- TDD for every fixed bug.
- In-app browser first; explicit desktop and mobile viewports, then reset at the end.
- Gateway and ORM are distinct evidence sources.
- Fictional-account credentials may be delivered; infrastructure secrets may not.

## Plan

1. Audit code and run the baseline suite.
2. Reproduce and fix gaps with tests.
3. Validate the seven registrations through the interface.
4. Validate desktop/mobile, console, terminal, and ORM.
5. Update PRDs and internal/external documentation.
6. Run final cleanup, secret search, and regression checks.

## Test plan

### Tests to author

- Defined by reproduced failures; do not create speculative tests.

### Execution authorization

Tests, ORM operations, and local/sandbox data are authorized by the current request.

### Execution evidence

- `manage.py test system` before changes: **675/675 passed**.
- Red failures reproduced before fixes:
  - administrative/instructor wizard did not create a request;
  - `student` intent created a person without a type;
  - instructor payout discarded condition/value;
  - finalized dependent remained inactive;
  - terminal snapshot retained passwords.
- Final focused suite: **72/72 passed** in 19.805 s.
- `manage.py check`: 0 issues.
- `manage.py makemigrations --check --dry-run`: `No changes detected`.
- `python -m compileall -q system`: no errors.
- Final suite: **679/679 passed** in 157.706 s.

## Visual validation

- Public registration: 1440×900 and 390×844, dark theme, all four profiles and CTA intact.
- Stripe student home: 390×844, light theme, active membership and visible gateway.
- “Adicionar dependente” (“Add dependent”) modal: 1440×900 and 390×844, title, close control, 1/7 progress, scrollable form, and fixed CTA without overlap.
- Instructor-request details: “Valor fixo · R$ 300,00” (“Fixed amount · BRL 300.00”) condition and two schedules visible before approval.
- Nine interface logins executed; none remained on the login form.
- Final console: 0 errors and 0 warnings.
- Evidence:
  - `docs/prd/evidence/prd-145-register-desktop.png`
  - `docs/prd/evidence/prd-145-register-mobile.png`
  - `docs/prd/evidence/prd-145-home-mobile-light.png`
  - `docs/prd/evidence/prd-145-dependent-modal-desktop.png`
  - `docs/prd/evidence/prd-145-dependent-modal-mobile.png`

## ORM validation

- Nine active `Person` and nine active `PortalAccount` records, with passwords verified by the hasher.
- Types: three students, two guardians, two dependents, one administrative person, and one instructor.
- Four active memberships: two `stripe_card` and two `asaas_pix`.
- Four paid orders: Stripe/Asaas provider consistent with each scenario.
- Two `responsible_for` relationships.
- Administrative student: `student` type + `people-support` role; no plan because the operational-access flow does not perform commercial enrollment.
- Full administrator: `administrative-assistant` type + `academy-manager` role.
- Instructor: approved request, active PIX bank account, “Jiu Jitsu Auditoria” (“Jiu Jitsu Audit”) class, and Tuesday/Thursday schedules at 20:30.
- Pre-registrations 1–4 and 6–8 finalized; invalid attempt 5 marked abandoned.
- Zero populated password fields in the eight audited terminal snapshots.

## Quality validation

- TDD observed for five behavioral failures.
- Clean `git diff --check` in both repositories.
- Search for Stripe/Asaas keys, webhook secrets, PostgreSQL connection strings, Django secrets, and SMTP passwords: zero values in the six reviewed guides.
- Local `SITE_BASE_URL` restored to the active ngrok domain.
- `lv-cleanup-audit` executed; existing instructor/class debt separated into PRD-146.

## Evidence

- Stripe: two hosted checkouts completed with a test card; return to LV, active `stripe_card` membership, and subscription/customer IDs present.
- Asaas: two PIX charges confirmed through the official sandbox endpoint; return to LV, paid order, and active `asaas_pix` membership.
- Interface: nine logins and five persisted screenshots.
- Consolidated ORM data and the 679-test suite recorded above.

## Implemented

- [x] PRD-145 created before fixes.
- [x] `submit_operational_pre_registration()` creates real pending requests for administrators and instructors with proposed schedules.
- [x] Student-intent approval preserves `PersonTypeCode.STUDENT` and grants the role.
- [x] Instructor financial condition preserved and displayed in details.
- [x] Finalization activates all dependents and their accounts.
- [x] Finalization/abandonment recursively remove passwords from snapshots.
- [x] PRDs 138–144 reconciled without erasing history.
- [x] Five external guides and two internal contracts updated.
- [x] Seven scenarios validated through the interface and approved when applicable.

## Cleanup findings

- Plaintext infrastructure credentials were removed from external guides; external rotation remains mandatory.
- The public instructor “existing classes” mode is visible and validated in the form, but has no backend workflow compatible with the current instructor’s consent.
- No residue, temporary file, unexpected migration, or `staticfiles/` edit was introduced.

## Follow-up PRDs

- [PRD-146](PRD-146-public-instructor-and-link-to-existing-classes.md): define primary/assistant/substitute relationships, approvers, and partial decisions before implementation.

## Deviations from plan

- The Asaas sandbox account had the HG domain registered and rejected the ngrok callback. Both payments were confirmed in sandbox with `SITE_BASE_URL` temporarily aligned to the registered domain; local configuration was restored.
- The audit found two additional failures directly related to the flow: inactive dependents and passwords in snapshots. Both were fixed and covered.

## Pending

- Rotate previously exposed credentials at the providers; not authorized in this execution.
- PRD-146 product decision.
- HG/production was neither changed nor validated.

## Final status

**Completed with limitations** — all requested scenarios were registered and
validated locally/in sandbox; only external rotation, the PRD-146 decision, and
any HG/production validation remain pending.
