# PRD-152: Ciclo de troca de senha — logado, esquecida com senha padrão e revisão do admin

## Summary

O usuário pediu para (1) ajustar a tela de troca de senha para fechar o ciclo
completo — trocar senha estando logado (com senha antiga + 2 senhas novas) e
recuperar senha esquecida via e-mail com uma senha padrão fixa (`LV@123`) que
força a troca no primeiro login — e (2) revisar se o admin está funcional e
bem implementado. A Rodada 1 desta PRD validou o comportamento antigo
(token por link) e deixou o ajuste visual em aberto por falta de
especificação. Nesta Rodada 2, com a especificação completa do usuário, o
ciclo foi implementado: o fluxo "esqueci minha senha" agora define a senha
`LV@123` e envia por e-mail (em vez de gerar um link de token); o login com
essa senha padrão força a exibição da tela de troca antes de liberar acesso;
e existe agora uma tela de troca de senha voluntária (link "Trocar senha" no
modal de conta do cliente) para quem já está logado. Ambos os fluxos
reaproveitam a mesma view/formulário/template.

## Demand type

Implementação Django + UI (TDD) + validação funcional + revisão de admin.

## Current problem

- (Rodada 1) O portal só tinha o fluxo "esqueci minha senha" via link com
  token (`password-reset` → `reset/<token>/`), sem tela de troca para quem
  já está logado.
- (Especificação do usuário, Rodada 2) O comportamento desejado é diferente
  do fluxo por link: ao esquecer a senha, o sistema deve gerar uma senha
  temporária fixa (`LV@123`), enviá-la por e-mail, e forçar a troca no
  primeiro login subsequente (usando `LV@123` como "senha antiga" + 2 senhas
  novas). Para quem já está logado, deve existir uma tela para trocar a
  própria senha (senha antiga + 2 senhas novas), sem depender de e-mail.
- `system/admin.py` (43 models pós-PRD-151) e o `django-admin/password_change/`
  nativo do Django já haviam sido revisados/validados como funcionais na
  Rodada 1 — não foram alterados nesta rodada.

## Goal

1. Implementar `PortalChangePasswordForm` (senha antiga + 2 senhas novas,
   reaproveitada nos dois fluxos).
2. Trocar o "esqueci minha senha" de link-com-token para
   redefinição-direta-para-senha-padrão (`LV@123`) + e-mail.
3. Fazer o login detectar a senha padrão e forçar a troca antes de liberar
   o dashboard.
4. Criar tela de troca de senha voluntária, acessível a partir do modal
   "Dados do cliente" para quem já está logado.
5. Cobrir tudo com testes automatizados (TDD) e validar manualmente no
   navegador (desktop + mobile), ambos os fluxos.

## Context Ledger

### Files read in full

- `system/services/portal_auth.py` (fluxo completo: `authenticate_portal_identity`,
  `login_portal_identity`, `create_password_reset_token` [antigo],
  `get_valid_password_reset_token`, `reset_portal_password`)
- `system/forms/auth_forms.py` (`PortalAuthenticationForm`,
  `PortalPasswordResetRequestForm`, `PortalSetPasswordForm`)
- `system/views/auth_views.py` (`PortalLoginView`, `PortalPasswordResetView`,
  `PortalPasswordResetConfirmView` e afins)
- `system/models/person.py` (`PortalAccount`, `PortalPasswordResetToken`)
- `templates/login/password_reset_confirm.html` (padrão visual reaproveitado)
- `templates/lv/base.html`, `templates/home/dashboard.html`,
  `templates/home/includes/dashboard_modals.html` (local do link "Trocar
  senha" no modal de conta)
- `system/tests/test_models.py` (testes existentes do fluxo antigo de token)
- `lvjiujitsu/settings.py` (`EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`,
  `PORTAL_PASSWORD_RESET_TOKEN_HOURS`)

### Adjacent files consulted

- `system/services/__init__.py`, `system/forms/__init__.py` (exports)
- `system/urls.py` (rotas `password-reset*`, `reset/*`, nova
  `password-change/`)

### Internet / official documentation

- Django auth password change/reset views:
  https://docs.djangoproject.com/en/5.2/topics/auth/default/#module-django.contrib.auth.views

### Context7 / MCPs / tools verified

- Servidor local ativo; `manage.py test` completo antes e depois da mudança.
- Fluxo completo testado no navegador real (desktop + mobile): esqueci senha
  → e-mail com `LV@123` (confirmado via ORM) → login com `LV@123` →
  redirecionado para tela de troca → senha errada rejeitada → senha correta
  aceita → login automático na home. Troca voluntária testada a partir do
  modal "Dados do cliente" enquanto logado.

### Limitations found

- `DJANGO_EMAIL_BACKEND` já está configurado como SMTP real
  (`django.core.mail.backends.smtp.EmailBackend`, Gmail, remetente
  `lvjiujitsu@gmail.com`) tanto em `.env` quanto em `.env.hg` — o envio é
  real, não simulado.
- **Entrega real confirmada** com um destinatário público sem login
  (`https://mailinator.com`, caixa `lvjiujitsuteste123@mailinator.com` —
  serviço de e-mail descartável com inbox pública, sem conta/senha): o
  e-mail "Senha temporária - LV JIU JITSU" chegou em ~1 minuto, remetente
  `lvjiujitsu@gmail.com`, corpo íntegro com `LV@123`. Confirma que o envio
  real (não só o `mail.outbox` dos testes) funciona ponta a ponta.
- Achado lateral: os e-mails de teste dos 7 perfis da PRD-151 usam o domínio
  fake `@lvjiujitsu.test` (intencional, para não gerar tráfego real) — o
  Gmail configurado tenta entregar e recebe bounce
  ("Endereço não encontrado") de volta na caixa `lvjiujitsu@gmail.com`, o
  que é o comportamento esperado para esse domínio inexistente, não um
  defeito do código.
- Não usei `mail.tm` (exigiria criar conta/senha) nem o `1secmail.com`/
  `guerrillamail.com` (fora do ar no momento do teste, 403/522) — o
  Mailinator público resolveu a validação sem precisar de nenhuma
  credencial.
- O modelo `PortalPasswordResetToken` e o fluxo por link
  (`PortalPasswordResetConfirmView`, `PortalSetPasswordForm`,
  `password_reset_confirm.html`, `password_reset_complete.html`,
  `reset_portal_password`, `get_valid_password_reset_token`) ficaram
  **órfãos** — nada no fluxo atual gera mais um token ou aponta para
  `/reset/<token>/`. Não foram removidos nesta PRD porque isso exigiria
  dropar a tabela via o ciclo destrutivo de migração
  (`clear_migrations.py` + `makemigrations`), o que apagaria o
  `db.sqlite3` local (incluindo os 7 cadastros de homologação da PRD-151).
  Registrado como dívida de limpeza para uma PRD futura, quando o reset
  destrutivo do banco for aceitável.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery` (reaproveitou o componente visual já existente do
  `password_reset_confirm.html`; sem proposta de design nova, já que o
  usuário especificou o comportamento, não um visual novo)
- `lv-cleanup-audit`

## Understanding approved

Especificação completa recebida do usuário: ciclo de troca de senha logado
(3 campos: antiga + 2 novas) e recuperação por e-mail com senha padrão fixa
`LV@123` forçando troca no primeiro login (mesma tela/lógica). Autorizado
implementar.

## Scope

- `system/services/portal_auth.py`: `DEFAULT_TEMP_PASSWORD`,
  `FORCED_PASSWORD_CHANGE_SESSION_KEY`, `change_own_password()`,
  `reset_portal_password_to_default()`; `authenticate_portal_identity()`
  detecta login com a senha padrão.
- `system/forms/auth_forms.py`: `PortalChangePasswordForm`.
- `system/views/auth_views.py`: `PortalChangePasswordView` (atende os dois
  fluxos); `PortalLoginView.form_valid` trata o novo `blocked_reason`;
  `PortalPasswordResetView.form_valid` chama a nova função de reset.
- `system/urls.py`: rota `password-change/`.
- `templates/login/change_password_form.html` (novo).
- `templates/home/includes/dashboard_modals.html`: link "Trocar senha" no
  modal de conta do cliente (só para o titular).
- Testes: `system/tests/test_password_change.py` (8 casos novos);
  `system/tests/test_models.py` (remoção do teste do fluxo antigo por
  token, agora substituído em comportamento).

## Out of scope

- Remover o modelo `PortalPasswordResetToken` e o fluxo por link (dívida de
  limpeza registrada; exige ciclo destrutivo de migração).
- Restilizar o Django admin.
- Auditoria arquitetural Django `User` vs `Person`/`PortalAccount` — PRD
  própria, autorizada pelo usuário para começar após o fechamento das
  pendências anteriores (Asaas + esta PRD).

## Impacted files

- `system/services/portal_auth.py`
- `system/services/__init__.py`
- `system/forms/auth_forms.py`
- `system/forms/__init__.py`
- `system/views/auth_views.py`
- `system/urls.py`
- `templates/login/change_password_form.html` (novo)
- `templates/home/includes/dashboard_modals.html`
- `system/tests/test_password_change.py` (novo)
- `system/tests/test_models.py`

## Risks and edge cases

- Um administrador que, por acidente, defina manualmente a senha de alguém
  como `LV@123` também vai disparar a troca forçada — comportamento
  aceitável (senha conhecida/insegura deve sempre forçar troca).
- `authenticate_portal_identity` verifica a senha padrão **antes** da
  checagem de `payment_pending` — prioriza segurança da conta sobre a
  cobrança pendente.
- Sessão de troca forçada (`forced_password_change_account_id`) não
  autentica o `PortalAccount` de fato — só após a troca bem-sucedida
  `login_portal_identity` é chamado, igual ao padrão já usado pelo fluxo de
  `payment_pending`.

## Rules and constraints

- Sem migração de schema nesta PRD (nenhum campo novo em `PortalAccount`).
- Sem tocar em credenciais de usuário Django (`User`/staff).
- TDD: testes escritos antes da implementação.

## Plan

1. Escrever `system/tests/test_password_change.py` (Red).
2. Implementar serviço, formulário, views, template, URL, link no modal
   (Green).
3. Corrigir teste legado obsoleto em `test_models.py`.
4. Rodar suíte completa.
5. Validar manualmente no navegador (desktop + mobile), os dois fluxos.

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

Autorizada pela especificação completa do usuário.

### Execution evidence

- `manage.py test system.tests.test_password_change --verbosity 2` → 8/8 OK.
- `manage.py test system` (suíte completa, após remover teste obsoleto do
  fluxo por token em `test_models.py`) → **711/711 OK**.
- `manage.py check` → sem issues.

## Visual validation

- `/password-change/` (fluxo forçado, logo após login com `LV@123`):
  título "Trocar senha" + aviso "Você entrou com uma senha temporária.
  Defina uma nova senha para continuar." — desktop e mobile (375×812).
- `/password-change/` (fluxo voluntário, a partir do link no modal "Dados
  do cliente"): mesma tela, sem o aviso de senha temporária.
- Erro "Senha antiga incorreta." renderizado corretamente abaixo do campo
  em ambos os fluxos.
- Mensagem de sucesso "Senha atualizada. Bem-vindo(a)!" (forçado) ou "Senha
  atualizada com sucesso." (voluntário) exibida na home após a troca.
- Template reaproveita 100% o componente visual (`login-card`) já usado em
  `/login/`, `/password-reset/` e `/register/` — consistente com o padrão
  visual existente, sem necessidade de proposta de design nova.

## ORM validation

- `PortalAccount.check_password("LV@123")` confirmado `True` logo após o
  "esqueci minha senha" (Fernanda Costa, CPF `134.656.438-87`).
- Após a troca forçada, `check_password` confirma a nova senha e
  `must_change` deixa de ser acionado (sem campo novo — a checagem é
  puramente por comparação de hash, não há estado residual).

## Quality validation

- `manage.py check` → sem issues.
- `manage.py test system` → 711/711 OK.

## Evidence

- Testes automatizados: 8/8 novos + suíte completa 711/711 OK.
- Fluxo completo no navegador real (conta de Fernanda Costa,
  `134.656.438-87`):
  1. `/password-reset/` com o CPF → "Instruções enviadas".
  2. ORM confirma `check_password("LV@123") == True`.
  3. Login com `LV@123` → redireciona para `/password-change/` com aviso
     de senha temporária.
  4. Tentativa com senha antiga errada → "Senha antiga incorreta."
     (senha não alterada).
  5. Envio correto (`LV@123` + `Teste@12345` × 2) → "Senha atualizada.
     Bem-vindo(a)!" + login automático na home.
  6. Troca voluntária a partir do modal "Dados do cliente" → link "Trocar
     senha" → formulário sem aviso de senha temporária → troca para
     `FinalSenha@9` → "Senha atualizada com sucesso."
  7. Confirmado em mobile (375×812) nas duas telas.

## Implemented

- [x] `PortalChangePasswordForm` (senha antiga + 2 novas, validação de
  senha antiga e de coincidência das novas).
- [x] `reset_portal_password_to_default()` — substitui o link por token
  por senha fixa `LV@123` enviada por e-mail.
- [x] `authenticate_portal_identity()` detecta a senha padrão e bloqueia
  o login normal até a troca.
- [x] `PortalChangePasswordView` — atende fluxo forçado (sessão) e
  voluntário (`portal_account` logado) na mesma view/template.
- [x] Link "Trocar senha" no modal de conta do cliente (só titular).
- [x] Testes automatizados (8 novos) + suíte completa verde.

## Cleanup findings

- `PortalPasswordResetToken`, `PortalPasswordResetConfirmView`,
  `PortalPasswordResetCompleteView`, `PortalSetPasswordForm`,
  `password_reset_confirm.html`, `password_reset_complete.html`,
  `reset_portal_password()` e `get_valid_password_reset_token()` ficaram
  **órfãos** (nada mais gera link de token). Mantidos por não exigirem
  migração imediata — candidatos a remoção em uma PRD de limpeza futura,
  junto com o ciclo destrutivo de migração (dropar a tabela
  `PortalPasswordResetToken` e sua entrada em `system/admin.py`).
- Teste obsoleto removido de `system/tests/test_models.py`
  (`test_password_reset_token_request_invalidates_previous_active_tokens`),
  que testava o comportamento antigo por token — substituído em cobertura
  por `test_password_change.py`.

## Follow-up PRDs

- **Limpeza do fluxo por token órfão** — remover
  `PortalPasswordResetToken`/`PortalPasswordResetConfirmView` e afins,
  junto com o próximo ciclo destrutivo de migração autorizado.
- **Auditoria arquitetural Django `User` vs `Person`/`PortalAccount`** —
  autorizada pelo usuário para iniciar após o fechamento das pendências
  anteriores (domínio Asaas + esta PRD).

## Deviations from plan

Nenhum desvio.

## Pending

- Abertura da PRD de auditoria arquitetural, quando autorizado.

## Final status

**Concluída** — ciclo completo de troca de senha implementado (logado e
esquecida-com-senha-padrão), testado (8 testes novos, suíte completa
711/711 OK) e validado manualmente no navegador real (desktop e mobile),
incluindo os casos de erro (senha antiga incorreta) e sucesso em ambos os
fluxos.
