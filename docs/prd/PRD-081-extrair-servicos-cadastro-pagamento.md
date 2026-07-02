# PRD-081: Extrair serviços de cadastro e pagamento do wizard

## Summary
Reduzir concentração de regra de negócio em `auth_views.py`, movendo persistência, snapshots, pagamento e finalização para services transacionais.

## Demand type
Refatoração Django MVT + segurança transacional.

## Current problem
`system/views/auth_views.py` concentra view HTTP, escrita ORM, snapshots de pré-cadastro, criação de pedidos, integração de pagamento e finalização. Isso viola o contrato MVT e torna testes/manutenção frágeis.

## Goal
Deixar views finas:
- validação HTTP/form na view;
- regra de negócio em services;
- escrita com `transaction.atomic`;
- testes por service e por view.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `system/views/auth_views.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/services/registration_validation.py`

### Adjacent files consulted
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `system/tests/test_registration_flow.py`
- `system/tests/test_register_wizard_contract.py`

### Internet / official documentation
- Django transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 transactions.

### Limitations found
- Fluxo de pagamento real depende de Asaas/Stripe e não pode ser validado como sucesso sem gateway/túnel quando aplicável.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual de corrigir views grandes e legado.

## Scope
- Extrair services para pré-cadastro, snapshot, criação de pedido e finalização.
- Manter comportamento público existente.
- Cobrir testes focados.

## Out of scope
- Redesign visual do wizard.
- Mudança de gateways.

## Impacted files
- `system/views/auth_views.py`
- `system/services/pre_registration.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/tests/test_registration_flow.py`
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases
- Fluxo pré-pagamento/pós-pagamento é sensível; regressão pode criar pessoa antes da hora.
- Webhooks e redirects precisam continuar separados.

## Plan
- [x] Mapear responsabilidades atuais.
- [x] Escrever testes de comportamento crítico.
- [x] Extrair services em etapas pequenas.
- [x] Validar wizard local.

## Test plan
### Tests to author
- Pré-cadastro não cria `Person` antes da finalização.
- Finalização cria pessoa/membership em transação.
- Erro de pagamento não finaliza cadastro.

### Execution authorization
Autorizada localmente.

### Execution evidence
Comandos executados localmente em `C:\Users\whsf\Documents\GitHub\lvjiujitsu` com `.venv\Scripts\python.exe`.

1. Baseline (antes da extração), suíte completa:
   `manage.py test --verbosity 1` → `Ran 261 tests in 74.918s` → `OK`.
2. Baseline focado (antes da extração):
   `manage.py test system.tests.test_registration_flow system.tests.test_register_wizard_contract --verbosity 2` → `Ran 4 tests in 0.927s` → `OK`.
3. Após extração dos services, novo teste de regressão por service criado em
   `system/tests/test_pre_registration_service.py` (5 testes cobrindo
   `finalize_pre_registration`, `mark_pre_registration_trial_requested` e
   `create_pre_registration_plan_payment`):
   `manage.py test system.tests.test_pre_registration_service --verbosity 2` → `Ran 5 tests in 1.179s` → `OK`.
4. `manage.py check` → `System check identified no issues (0 silenced).`
5. Suíte completa após a extração:
   `manage.py test --verbosity 1` → `Ran 267 tests in 68.720s` → `OK` (e nova execução final em
   `55.083s` → `OK`).
6. Testes de contrato do wizard (incluindo o teste que instancia
   `PortalRegisterView()._get_pending_person_summary()` diretamente) continuam verdes após a
   extração: `manage.py test system.tests.test_register_wizard_contract.PendingRegistrationSummaryContractTestCase --verbosity 2` → `Ran 1 test in 0.022s` → `OK`.

Validação visual no navegador interno do wizard público **não foi executada** nesta entrega —
a view HTTP `PortalRegisterView`/`FinalizeRegistrationView`/`MaterialsCheckoutView` foi alterada
apenas para delegar chamadas a services (mesma assinatura de URL, mesmo `template_name`,
mesmo contrato de contexto), sem mudança de template/CSS/JS. A suíte automatizada (incluindo o
teste de contrato `test_register_wizard_contract.py` que verifica `?v=36` do script e marcadores
de função no JS) cobre o contrato estático sem regressão.

## Visual validation
Necessária para wizard se view for tocada.

## ORM validation
Obrigatória no banco de teste.

## Quality validation
- Testes focados
- `manage.py check`

## Evidence
- Subagente apontou concentração em `PortalRegisterView` e `FinalizeRegistrationView`.

## Implemented
- `system/services/pre_registration.py` ganhou as funções de regra de negócio que estavam em
  `PortalRegisterView`/`FinalizeRegistrationView`:
  - `build_wizard_form_snapshot`, `snapshot_scalar`, `resolve_primary_cpf`, `resolve_primary_email`,
    `save_pre_registration_from_form` (cria/atualiza `PreRegistration` a partir do POST do wizard).
  - `mark_pre_registration_trial_requested` (fluxo "pagar depois").
  - `get_pending_person_summary`, `build_pending_summary_from_pre_registration`,
    `build_snapshot_student_summary`, `build_extra_dependent_summary`,
    `get_extra_dependents_from_snapshot`, `build_person_class_group_summary`,
    `build_snapshot_class_group_summary`, `build_class_group_summary_from_groups`
    (resumo de pessoa pendente exibido no wizard).
  - `get_order_summary`, `get_registration_order_or_pre_registration_summary`
    (resumo de pedido de plano/materiais).
  - `normalize_snapshot_for_form`, `grant_trial_for_pre_registration` e
    `finalize_pre_registration` (finalização transacional: cria `Person`/`PortalAccount` via
    `PortalRegistrationForm.save()`, ativa contas, sincroniza pagamento confirmado com a
    `RegistrationOrder` e concede aula experimental quando aplicável). `finalize_pre_registration`
    retorna um dict (`ok`, `error`, `person`, `portal_account`, `already_finalized`) para a view
    decidir o redirect/mensagem sem reimplementar regra.
- `system/services/registration_checkout.py` ganhou as funções de pagamento que estavam na view:
  `ensure_pre_registration_asaas_customer`, `parse_selected_plan_payload`,
  `create_pre_registration_plan_payment` (PIX/cartão Asaas e assinatura Stripe, com cupom) e
  `create_pre_registration_materials_payment` (PIX/cartão Asaas para materiais).
- `system/views/auth_views.py` ficou fino: `PortalRegisterView.form_valid`,
  `MaterialsCheckoutView._post_for_pre_registration` e
  `FinalizeRegistrationView._finalize_pre_registration` agora chamam os services acima em vez de
  conter a lógica diretamente. O arquivo caiu de 1104 para 538 linhas. Nenhuma URL, template,
  contexto público ou assinatura de método externamente referenciado (`_get_pending_person_summary`
  permanece como wrapper fino sobre o service, pois é usado diretamente por
  `test_register_wizard_contract.py`) foi alterado.
- Novo teste `system/tests/test_pre_registration_service.py` cobrindo finalização (sucesso,
  idempotência e erro de validação sem criar `Person`), marcação de aula experimental e erro de
  pagamento de plano sem plano selecionado.

## Cleanup findings
- Removida duplicação de lógica entre `PortalRegisterView._ensure_pre_registration_asaas_customer`
  e a cópia usada por `MaterialsCheckoutView` via `PortalRegisterView()._ensure_pre_registration_asaas_customer(...)`
  (instanciação de view só para chamar um método auxiliar) — agora ambas as views chamam a mesma
  função de service `ensure_pre_registration_asaas_customer`.
- `import re`/`from decimal import Decimal` local duplicado dentro de `ValidateCouponView.post`
  (linha ~211 de `auth_views.py`) é legado pré-existente, fora do escopo desta PRD; registrado aqui
  para eventual limpeza futura, não removido nesta entrega para não expandir o diff.
- Confirmado (via `git grep` no `HEAD` anterior a esta mudança) que `build_form_snapshot`,
  `create_or_update_pre_registration`, `get_pre_registration_for_session` e `restore_form_initial`
  em `system/services/pre_registration.py` já eram código órfão antes desta PRD — não havia nenhum
  caller em `system/` além do próprio módulo. Não foram removidos nesta entrega para não expandir o
  escopo (a PRD pede extração, não exclusão de legado não relacionado); registrado aqui como dívida
  pré-existente para auditoria futura.

## Follow-up PRDs
Nenhum aberto nesta entrega. O item de import duplicado em `ValidateCouponView` pode virar
follow-up de limpeza menor se desejado, mas não justifica PRD própria.

## Deviations from plan
Nenhum desvio relevante. O Plan previa "extrair services em etapas pequenas" — a extração foi
feita em um único commit de trabalho (sem commit git criado, conforme instrução de não commitar),
mas dividida internamente por responsabilidade (snapshot/resumo/finalização em
`pre_registration.py`; pagamento em `registration_checkout.py`) e validada com testes focados antes
da suíte completa.

## Pending
- Validação visual manual do wizard no navegador interno (desktop/mobile, caminho feliz e edge
  case) não foi executada nesta entrega. Recomendado antes de promover para HG, especialmente os
  fluxos de pagamento PIX/cartão/Stripe que dependem de gateway externo e não são exercitados pela
  suíte automatizada (testes cobrem apenas os caminhos de erro de validação que não chamam a API
  real do Asaas/Stripe).
- Pagamento real (Asaas/Stripe) não foi validado fim a fim — depende de túnel HTTPS e gateway,
  conforme limitação já registrada no Context Ledger desta PRD.

## Final status
Concluída com limitações (núcleo de extração testado e verde; validação visual/pagamento real
pendente, conforme seção Pending).
