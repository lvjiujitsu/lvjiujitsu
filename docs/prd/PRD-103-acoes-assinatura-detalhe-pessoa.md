# PRD-103: Ações de assinatura no detalhe de pessoa

## Summary
`CancelMembershipActionView` e `ChangeMembershipPlanActionView` existem e funcionam (POST), mas nenhuma tela tem botão que os dispare — órfãs de UI, gap já documentado na PRD-077 (Pending).

## Demand type
Correção de UI (ação de backend sem entrada na interface).

## Current problem
- `templates/people/person_detail.html` mostra o plano ativo (badge de status, nome, vencimento) mas não tem ação de cancelar nem trocar plano.
- Gestor precisa usar Django Admin ou uma chamada manual para essas ações.

## Goal
Na seção "Plano ativo" do detalhe de pessoa (somente para quem gerencia, `can_manage_people`), o gestor pode cancelar a assinatura (ao fim do período) e trocar o plano ativo por outro plano ativo do catálogo.

## Context Ledger
### Files read in full
- `templates/people/person_detail.html` (seção "Plano ativo")
- `system/views/billing_admin_views.py` (`CancelMembershipActionView`, `ChangeMembershipPlanActionView`)
- `system/views/person_views.py` (`PersonDetailView.get_context_data` — já expõe `available_plans`)

### Adjacent files consulted
- `system/services/stripe_admin_actions.py`

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"), gap já documentado na PRD-077.

## Scope
- Adicionar formulários de ação (cancelar, trocar plano) na seção "Plano ativo" do detalhe de pessoa, com `next` apontando de volta para a própria página.

## Out of scope
- Checkbox de "cancelar imediatamente vs. fim do período" (mantém o default `at_period_end=True` do backend).
- Redesenhar a seção de faturamento.

## Impacted files
- `templates/people/person_detail.html`
- `system/tests/`

## Risks and edge cases
- Ação só deve aparecer quando há `active_membership` com status cancelável.
- Erros do gateway (`StripeAdminActionError`) já são tratados na view com `messages.error` e redirect — nenhuma mudança necessária ali.

## Rules and constraints
- Só renderiza para `can_manage_people`.
- CSRF em ambos os POSTs.

## Plan
- [x] Adicionar os dois formulários na seção "Plano ativo".
- [x] Teste focado.
- [x] Validação visual.

## Test plan
### Tests to author
- Detalhe de pessoa com assinatura ativa mostra os botões; sem assinatura ativa, não mostra.
- POST de cancelar assinatura funciona a partir da própria tela (redirect de volta).

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_membership_actions_ui.py` (4 testes): botões aparecem com assinatura ativa; não aparecem sem assinatura ativa; POST de cancelar sem `stripe_subscription_id` cancela localmente (status `canceled`); POST de trocar plano sem `stripe_subscription_id` mostra erro e mantém o plano.
- `.venv/Scripts/python.exe manage.py test system.tests.test_membership_actions_ui --verbosity 2` — 4 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 346 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Validação ao vivo no navegador (dado demo criado via ORM para Aline Blanch Freiria, removido após o teste): seção "Mensalidade" mostra "Trocar plano" (select com planos ativos) e "Cancelar assinatura"; POST de cancelamento mudou o status real para "Cancelada" e a seção passou a mostrar "Nenhum plano ativo" com o histórico "CANCELADA"; validado em mobile (375x812) e tema escuro sem overflow.

## Visual validation
Desktop, mobile, tema escuro.

## ORM validation
`Membership.status` verificado via teste.

## Quality validation
- `manage.py test` focado e suíte completa.
- `manage.py check`.

## Evidence
- `change_membership_plan` exige `stripe_subscription_id` (assinaturas antigas/manuais não têm); nesse caso a ação mostra mensagem de erro e não altera o plano — comportamento correto e já coberto pelo teste.

## Implemented
- `templates/people/person_detail.html`: seção "Plano ativo" ganhou formulário de troca de plano (select com `available_plans` + botão) e formulário de cancelamento de assinatura, visíveis apenas quando `m.status` é `active`, `past_due` ou `exempted`; ambos usam `next` para retornar à própria página.
- `system/tests/test_membership_actions_ui.py` (novo).

## Cleanup findings
- Nenhum resíduo; dado demo (membership de teste) removido do banco local após a validação visual.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
- Nenhum desvio funcional.

## Pending
- Nenhuma.

## Final status
Concluída.
