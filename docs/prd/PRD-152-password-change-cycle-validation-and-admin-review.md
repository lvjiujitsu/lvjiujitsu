# PRD-152: Password-Change Lifecycle — Signed-In, Forgotten Password with Default Password, and Admin Review

## Summary

The user requested (1) adjustment of the password-change screen to complete the full lifecycle — changing a password while signed in (old password + two new-password fields) and recovering a forgotten password by email with a fixed default password (`LV@123`) that forces a change at first login — and (2) a review of whether admin is functional and well implemented. Round 1 of this PRD validated the old behavior (token link) and left the visual adjustment open because the specification was incomplete. In round 2, with the user’s complete specification, the lifecycle was implemented: “forgot password” now sets `LV@123` and sends it by email (instead of generating a token link); login with that default password forces the change screen before granting access; and a voluntary password-change screen now exists (“Trocar senha” / “Change password” link in the client account modal) for users who are already signed in. Both flows reuse the same view/form/template.

## Demand type

Django + UI implementation (TDD) + functional validation + admin review.

## Current problem

- (Round 1) The portal had only a token-link “forgot password” flow (`password-reset` → `reset/<token>/`), with no password-change screen for signed-in users.
- (User specification, round 2) Desired behavior differs from the link flow: after a forgotten password, the system must generate a fixed temporary password (`LV@123`), email it, and force a change on the next login (using `LV@123` as “old password” + two new-password fields). Signed-in users need a screen to change their own password (old password + two new-password fields) without email.
- `system/admin.py` (43 models after PRD-151) and Django’s native `django-admin/password_change/` were already reviewed/validated as working in round 1 — unchanged in this round.

## Goal

1. Implement `PortalChangePasswordForm` (old password + two new-password fields, reused in both flows).
2. Replace forgot-password token links with direct reset to the default password (`LV@123`) + email.
3. Detect the default password at login and force a change before granting dashboard access.
4. Create a voluntary password-change screen accessible from the “Dados do cliente” (“Client data”) modal for signed-in users.
5. Cover everything with automated tests (TDD) and manually validate both flows in the browser (desktop + mobile).

## Context Ledger

### Files read in full

- `system/services/portal_auth.py` (complete flow: `authenticate_portal_identity`, `login_portal_identity`, old `create_password_reset_token`, `get_valid_password_reset_token`, `reset_portal_password`)
- `system/forms/auth_forms.py` (`PortalAuthenticationForm`, `PortalPasswordResetRequestForm`, `PortalSetPasswordForm`)
- `system/views/auth_views.py` (`PortalLoginView`, `PortalPasswordResetView`, `PortalPasswordResetConfirmView`, and related views)
- `system/models/person.py` (`PortalAccount`, `PortalPasswordResetToken`)
- `templates/login/password_reset_confirm.html` (reused visual pattern)
- `templates/lv/base.html`, `templates/home/dashboard.html`, `templates/home/includes/dashboard_modals.html` (location of the “Trocar senha” / “Change password” link in the account modal)
- `system/tests/test_models.py` (existing old token-flow tests)
- `lvjiujitsu/settings.py` (`EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `PORTAL_PASSWORD_RESET_TOKEN_HOURS`)

### Adjacent files consulted

- `system/services/__init__.py`, `system/forms/__init__.py` (exports)
- `system/urls.py` (`password-reset*`, `reset/*`, and new `password-change/` routes)

### Internet / official documentation

- Django auth password change/reset views:
  https://docs.djangoproject.com/en/5.2/topics/auth/default/#module-django.contrib.auth.views

### Context7 / MCPs / tools verified

- Local server active; full `manage.py test` run before and after the change.
- Complete flow tested in a real browser (desktop + mobile): forgot password → email with `LV@123` (confirmed through ORM) → login with `LV@123` → redirect to change screen → wrong password rejected → correct password accepted → automatic home login. Voluntary change tested from the “Dados do cliente” (“Client data”) modal while signed in.

### Limitations found

- `DJANGO_EMAIL_BACKEND` is already configured as real SMTP (`django.core.mail.backends.smtp.EmailBackend`, Gmail, sender `lvjiujitsu@gmail.com`) in both `.env` and `.env.hg` — delivery is real, not simulated.
- **Real delivery confirmed** with a public recipient requiring no login (`https://mailinator.com`, mailbox `lvjiujitsuteste123@mailinator.com` — public disposable inbox without an account/password): the “Senha temporária - LV JIU JITSU” (“Temporary password - LV JIU JITSU”) email arrived in ~1 minute from `lvjiujitsu@gmail.com`, with an intact body containing `LV@123`. This confirms true end-to-end delivery, not merely the test `mail.outbox`.
- Side finding: test emails for PRD-151’s seven profiles use the fake `@lvjiujitsu.test` domain (intentional, to prevent real traffic) — configured Gmail attempts delivery and receives an “Endereço não encontrado” (“Address not found”) bounce in `lvjiujitsu@gmail.com`, which is expected for this nonexistent domain, not a code defect.
- I did not use `mail.tm` (would require creating an account/password) or `1secmail.com`/`guerrillamail.com` (unavailable during testing, 403/522) — public Mailinator completed validation without credentials.
- The `PortalPasswordResetToken` model and link flow (`PortalPasswordResetConfirmView`, `PortalSetPasswordForm`, `password_reset_confirm.html`, `password_reset_complete.html`, `reset_portal_password`, `get_valid_password_reset_token`) became **orphaned** — nothing in the current flow generates a token or points to `/reset/<token>/`. They were not removed in this PRD because dropping the table requires the destructive migration cycle (`clear_migrations.py` + `makemigrations`), which would erase local `db.sqlite3` (including PRD-151’s seven validation registrations). Recorded as cleanup debt for a future PRD when destructive database reset is acceptable.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery` (reused the existing visual component from `password_reset_confirm.html`; no new design proposal because the user specified behavior, not a new visual)
- `lv-cleanup-audit`

## Understanding approved

Complete user specification received: signed-in password-change lifecycle (three fields: old + two new) and email recovery with fixed default password `LV@123`, forcing a change on first login (same screen/logic). Implementation authorized.

## Scope

- `system/services/portal_auth.py`: `DEFAULT_TEMP_PASSWORD`, `FORCED_PASSWORD_CHANGE_SESSION_KEY`, `change_own_password()`, `reset_portal_password_to_default()`; `authenticate_portal_identity()` detects login with the default password.
- `system/forms/auth_forms.py`: `PortalChangePasswordForm`.
- `system/views/auth_views.py`: `PortalChangePasswordView` (serves both flows); `PortalLoginView.form_valid` handles the new `blocked_reason`; `PortalPasswordResetView.form_valid` calls the new reset function.
- `system/urls.py`: `password-change/` route.
- `templates/login/change_password_form.html` (new).
- `templates/home/includes/dashboard_modals.html`: “Trocar senha” (“Change password”) link in the client account modal (primary account only).
- Tests: `system/tests/test_password_change.py` (eight new cases); `system/tests/test_models.py` (removal of the old token-flow behavioral test).

## Out of scope

- Removing `PortalPasswordResetToken` and the link flow (recorded cleanup debt; requires destructive migration cycle).
- Restyling Django admin.
- Django `User` vs `Person`/`PortalAccount` architectural audit — dedicated PRD authorized by the user to begin after previous pending work (Asaas + this PRD) closes.

## Impacted files

- `system/services/portal_auth.py`
- `system/services/__init__.py`
- `system/forms/auth_forms.py`
- `system/forms/__init__.py`
- `system/views/auth_views.py`
- `system/urls.py`
- `templates/login/change_password_form.html` (new)
- `templates/home/includes/dashboard_modals.html`
- `system/tests/test_password_change.py` (new)
- `system/tests/test_models.py`

## Risks and edge cases

- An administrator who accidentally sets someone’s password to `LV@123` also triggers forced change — acceptable behavior (a known/insecure password must always force a change).
- `authenticate_portal_identity` checks the default password **before** `payment_pending` — account security takes precedence over a pending charge.
- Forced-change session (`forced_password_change_account_id`) does not actually authenticate `PortalAccount` — only after a successful change does it call `login_portal_identity`, matching the existing `payment_pending` flow pattern.

## Rules and constraints

- No schema migration in this PRD (no new `PortalAccount` field).
- Do not touch Django-user (`User`/staff) credentials.
- TDD: tests written before implementation.

## Plan

1. Write `system/tests/test_password_change.py` (Red).
2. Implement service, form, views, template, URL, and modal link (Green).
3. Fix the obsolete legacy test in `test_models.py`.
4. Run the full suite.
5. Manually validate both flows in the browser (desktop + mobile).

## Test plan

### Tests to author

- [x] `test_forgot_password_resets_to_default_and_sends_email`
- [x] `test_login_with_default_password_redirects_to_forced_change`
- [x] `test_forced_password_change_requires_default_as_old_password`
- [x] `test_forced_password_change_completes_and_logs_in`
- [x] `test_voluntary_password_change_requires_login`
- [x] `test_voluntary_password_change_requires_correct_old_password`
- [x] `test_voluntary_password_change_rejects_mismatched_new_passwords`
- [x] `test_voluntary_password_change_success`

### Execution authorization

Authorized by the user’s complete specification.

### Execution evidence

- `manage.py test system.tests.test_password_change --verbosity 2` → 8/8 passed.
- `manage.py test system` (complete suite after removing the obsolete token-flow test from `test_models.py`) → **711/711 passed**.
- `manage.py check` → no issues.

## Visual validation

- `/password-change/` (forced flow immediately after login with `LV@123`): “Trocar senha” (“Change password”) title + “Você entrou com uma senha temporária. Defina uma nova senha para continuar.” (“You signed in with a temporary password. Set a new password to continue.”) notice — desktop and mobile (375×812).
- `/password-change/` (voluntary flow from the “Dados do cliente” / “Client data” modal link): same screen without the temporary-password notice.
- “Senha antiga incorreta.” (“Incorrect old password.”) error rendered correctly beneath the field in both flows.
- Success message “Senha atualizada. Bem-vindo(a)!” (“Password updated. Welcome!”) for forced flow or “Senha atualizada com sucesso.” (“Password updated successfully.”) for voluntary flow shown on home after change.
- Template reuses 100% of the visual `login-card` component already used on `/login/`, `/password-reset/`, and `/register/` — consistent with the existing visual pattern, with no new design proposal needed.

## ORM validation

- `PortalAccount.check_password("LV@123")` confirmed `True` immediately after “forgot password” (Fernanda Costa, CPF `134.656.438-87`).
- After forced change, `check_password` confirms the new password and `must_change` no longer triggers (no new field — check is purely hash comparison, with no residual state).

## Quality validation

- `manage.py check` → no issues.
- `manage.py test system` → 711/711 passed.

## Evidence

- Automated tests: eight new tests + complete 711/711 suite passing.
- Complete real-browser flow (Fernanda Costa account, `134.656.438-87`):
  1. `/password-reset/` with CPF → “Instruções enviadas” (“Instructions sent”).
  2. ORM confirms `check_password("LV@123") == True`.
  3. Login with `LV@123` → redirect to `/password-change/` with temporary-password notice.
  4. Attempt with wrong old password → “Senha antiga incorreta.” (“Incorrect old password.”), password unchanged.
  5. Correct submit (`LV@123` + `Teste@12345` × 2) → “Senha atualizada. Bem-vindo(a)!” (“Password updated. Welcome!”) + automatic home login.
  6. Voluntary change from “Dados do cliente” (“Client data”) modal → “Trocar senha” (“Change password”) link → form without temporary-password notice → change to `FinalSenha@9` → “Senha atualizada com sucesso.” (“Password updated successfully.”)
  7. Confirmed on mobile (375×812) on both screens.

## Implemented

- [x] `PortalChangePasswordForm` (old password + two new passwords, validating old password and matching new values).
- [x] `reset_portal_password_to_default()` — replaces token link with fixed `LV@123` password sent by email.
- [x] `authenticate_portal_identity()` detects the default password and blocks normal login until change.
- [x] `PortalChangePasswordView` — serves forced (session) and voluntary (signed-in `portal_account`) flows in the same view/template.
- [x] “Trocar senha” (“Change password”) link in the client account modal (primary account only).
- [x] Automated tests (eight new) + complete suite passing.

## Cleanup findings

- `PortalPasswordResetToken`, `PortalPasswordResetConfirmView`, `PortalPasswordResetCompleteView`, `PortalSetPasswordForm`, `password_reset_confirm.html`, `password_reset_complete.html`, `reset_portal_password()`, and `get_valid_password_reset_token()` became **orphaned** (nothing generates token links anymore). Retained because they do not require immediate migration — candidates for removal in a future cleanup PRD together with the destructive migration cycle (drop the `PortalPasswordResetToken` table and its `system/admin.py` entry).
- Obsolete `system/tests/test_models.py` test removed (`test_password_reset_token_request_invalidates_previous_active_tokens`), which tested old token behavior — replaced in coverage by `test_password_change.py`.

## Follow-up PRDs

- **Orphan token-flow cleanup** — remove `PortalPasswordResetToken`/`PortalPasswordResetConfirmView` and related artifacts with the next authorized destructive migration cycle.
- **Django `User` vs `Person`/`PortalAccount` architectural audit** — authorized by the user to start after previous pending work (Asaas domain + this PRD) closes.

## Deviations from plan

No deviations.

## Pending

- Open the architectural-audit PRD when authorized.

## Final status

**Completed** — complete password-change lifecycle implemented (signed-in and forgotten-password-with-default-password), tested (eight new tests, complete 711/711 suite passing), and manually validated in a real browser (desktop and mobile), including incorrect-old-password error and success cases in both flows.
