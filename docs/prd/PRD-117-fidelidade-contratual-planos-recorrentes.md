# PRD-117: Fidelidade contratual para planos recorrentes

## Summary
Criar campo e regra contratual explicita para carencia/fidelidade de planos recorrentes, separando a data de bloqueio de troca/cancelamento do periodo mensal corrente da mensalidade.

## Demand type
Follow-up documental de regra financeira fora do escopo da PRD-116.

## Current problem
- A PRD-116 bloqueia troca/cancelamento de plano Stripe recorrente usando `Membership.current_period_end` como data operacional.
- O modelo atual nao tem campo dedicado para fim de carencia/fidelidade, aceite de termo ou prazo contratual diferente da vigencia mensal.

## Goal
- Definir onde armazenar a data fim de carencia/fidelidade.
- Registrar aceite do termo aplicado ao plano recorrente.
- Separar renovacao mensal, periodo pago e fidelidade contratual.
- Atualizar home, endpoints de troca/cancelamento e gestao financeira para usar a data contratual.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Status
Pendente. Nao implementar sem aprovacao explicita.
