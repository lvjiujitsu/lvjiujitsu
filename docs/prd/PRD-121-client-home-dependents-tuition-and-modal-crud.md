# PRD-121: The client home with dependents, monthly fees, and a modal CRUD

## Summary
Fix the authenticated student/guardian home so it shows the main person's monthly fee again, separates the dependents' monthly fees, shows each dependent's graduation/history, and offers a short CRUD in a popup/modal. The large header with the greeting/date leaves the main area; the client's data moves into an icon on the topbar, next to the theme toggle.

## Demand type
A functional fix + UI + Django MVT.

## Current problem
- The current home can hide the monthly fee when the person trains but `portal_is_student` is not true.
- Dependents appear as a plain list, with no separate monthly fee, detailed graduation, history, or edit/remove actions.
- The `Adicionar dependente` ("Add dependent") text link breaks the pattern of iconic actions.
- The `Olá, Aluno` ("Hello, Student") header takes over the screen and should become a client data popup.
- Short dependent actions must not switch screens.

## Goal
Deliver an operational client home in which the main person and the dependents have visible financial and graduation information, with add/edit/remove actions in a popup/modal and permissions validated in the backend.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`

### Adjacent files consulted
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/models/plan.py`
- `system/services/membership.py`
- `system/services/graduation.py`
- `system/urls.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

### Internet / official documentation
- Django 5.2 generic editing views: `https://docs.djangoproject.com/en/5.2/topics/class-based-views/generic-editing`
- Django 5.2 class-based editing reference: `https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing`
- Django 5.2 messages framework: `https://docs.djangoproject.com/en/5.2/ref/contrib/messages`

### Context7 / MCPs / tools verified
- Context7: `/websites/djangoproject_en_5_2`, consulted about `FormView`/`UpdateView`/`DeleteView`, POST redirects, messages, and protected deletion.
- The internal browser will be used in the UI validation.

### Limitations found
- The user's local database was changed in previous cycles; the visual validation must consider the current state and also isolated tests.
- Removing a dependent will be the removal of the guardian -> dependent relationship, not a physical deletion of the `Person`, to preserve the financial history, the graduation, and the audit trail.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user explicitly asked: "generate a fix PRD with the information and implement it." The local implementation, the tests, and the validation in the internal browser are authorized by the current request and by the repository's protocol.

## Execution prompt
### Persona
A senior Django/UI agent at LV JIU JITSU.

### Action
Fix the client home and the short dependent CRUD, keeping the business rule in the backend and the visual actions in a modal.

### Context
The portal uses server-rendered Django 5.2, `system/` as the domain app, the assets in `static/system/`, and the templates in `templates/`. The unified home already has a dependent modal through an iframe.

### Constraints
- Do not edit `staticfiles/`.
- Do not physically delete a dependent person.
- Do not create a business rule in the template/JS.
- Do not show a destructive action without a POST and a confirmation.
- Do not show another person's dependent CRUD.
- Update the `?v=` when an asset is edited.

### Acceptance criteria
- [ ] The home no longer renders the large `.page-header` block with the date/greeting/role.
- [ ] The topbar shows a client data icon next to the theme toggle and opens a popup with the client's data, the profiles, and the dependent actions.
- [ ] The monthly fee section appears for the main person when they train or have dependents, even if the `portal_is_student` flag is not true.
- [ ] The main person's monthly fee and each dependent's monthly fee are separate and identified.
- [ ] Each dependent shows the current graduation, a progress summary, the history, and today's classes.
- [ ] Each dependent has iconic actions to edit and remove.
- [ ] Editing a dependent opens a popup/modal, validates the fields on the server, and only allows a dependent linked to the logged-in client.
- [ ] Removing a dependent uses a POST, confirms on the front end, validates the relationship on the server, and removes only the `PersonRelationship`.
- [ ] A user with no relationship neither edits nor removes a third party's dependent.
- [ ] The UI works in the light/dark theme, on desktop/mobile, and with no critical console error.

### Expected evidence
- Focused Django tests run with a real result.
- `manage.py check` run.
- Validation in the internal browser at `/home/` with a dependent state.
- The PRD updated with the executed evidence.

### Output format
A short summary in pt-BR: what was implemented, the evidence, the limitations, and the status.

## Scope
- The authenticated client home.
- The dependent cards.
- The client data popup.
- The iframe modal reused to add/edit a dependent.
- The removal of a dependent's relationship.
- The focused tests.

## Out of scope
- The materials shop.
- The full purchase history.
- A schema change.
- The physical deletion of a `Person`.
- A redesign of the whole administrative/instructor dashboard.
- A remote migration, a deploy, staging, or production.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-121-client-home-dependents-tuition-and-modal-crud.md`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `templates/dependents/dependent_edit.html`
- `templates/dependents/dependent_registration_done.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

## Risks and edge cases
- A dependent with their own monthly fee versus one covered by the guardian.
- A guardian who also trains.
- A person with an enrollment/belt but no `portal_is_student`.
- A dependent with no recorded graduation.
- A dependent with a financial history that cannot be erased.
- An iframe modal with no `showModal` support.
- The theme and the focus on mobile.

## Rules and constraints
- `GET /dependents/add/` without `modal=1` keeps redirecting to `/home/?dependent_modal=1`.
- `GET /dependents/<pk>/edit/` without `modal=1` redirects to the home, opening a predictable modal.
- `POST /dependents/<pk>/remove/` removes the relationship only when the `source_person` is the logged-in client.
- The dependent actions use icons with `aria-label` and `title`.

## Plan
1. Create the contract tests for the home and the dependent.
2. Implement the edit form/view/URL.
3. Implement the relationship removal POST view.
4. Adjust the home's context for the billing, the client's profile, and the enriched dependents.
5. Adjust the template, the CSS, and the JS.
6. Run the tests, `manage.py check`, and the visual validation.
7. Update the PRD and the cleanup audit.

## Visual hierarchy
- The topbar: the logo on the left; the actions on the right: the client's data, the theme, sign out.
- The content: starts directly at `Minha área` ("My area") or at the first operational section.
- The monthly fee: the main person's own section; the dependents have a summarized monthly fee inside the card.
- The dependents: a list of cards with the name, the badges, the monthly fee, the graduation, the classes, and the iconic actions.

## Wireframe
### Region: Topbar
- The LV logo.
- A `Dados do cliente` ("Client data") icon button.
- An `Alternar tema` ("Toggle theme") icon button.
- A `Sair` ("Sign out") icon button.

### Region: The Client Data popup
- The header: the full name and the active profiles.
- The data: CPF, e-mail, phone.
- The main person's plan: the status, the plan's name, and the term where it exists.
- The dependents: a counter and an iconic action to add one.

### Region: The Main Content
- The `Minha área` ("My area") section when there is personal training.
- The `Turmas de hoje` ("Today's classes") section.
- The main person's `Graduação` ("Graduation") section.
- The main person's `Mensalidade` ("Monthly fee") section.
- The `Meus dependentes` ("My dependents") section: cards with the financials, the graduation, the history, and the CRUD.

### Screen states
- No dependents: an empty state with an iconic action/short text to add one.
- With dependents: an operational list.
- No monthly fee: a `Sem plano ativo` ("No active plan") badge.
- An active/overdue/exempt monthly fee: a semantic badge.
- Removal: a confirmation before the POST.

## State machine
### The client data popup
- States: `closed` -> `open` -> `closed`.
- Closing: the button, the backdrop, or `Esc`.

### The dependent modal
- States: `closed` -> `open` -> `submitting` -> `success` or `error`.
- Success: the iframe sends `dependent-modal-done`, the modal closes, and the home reloads.

### Removing a dependent
- States: `idle` -> `confirmable` -> `submitting` -> `success` or `error`.
- Success: a redirect to the home with a message.

## Test plan
### Tests to author
- The home renders with no `.page-header` and with the client's button/modal.
- The home shows the monthly fee for a person who trains, even without depending solely on the `portal_is_student` flag.
- The dependent's card shows a separate monthly fee, the graduation, the history, and the iconic actions.
- Editing a dependent changes the permitted fields for one's own relationship.
- Editing another guardian's dependent is blocked.
- Removing a dependent removes only one's own relationship.

### Execution authorization
Authorized by the current request and by `AGENTS.md`.

### Execution evidence
- Pending.

## Visual validation
- Pending.

## ORM validation
- Pending.

## Quality validation
- Pending.

## Evidence
- Pending.

## Implemented
- Pending.

## Cleanup findings
- Pending.

## Follow-up PRDs
- Pending.

## Deviations from plan
- Pending.

## Pending
- Pending.

## Final status
Not completed.
