# PRD-125: Sincronizacao remota do upgrade familiar Stripe

## Summary
Definir a sincronizacao remota de assinatura Stripe quando um titular com plano recorrente ativo adiciona dependente e migra para plano familiar.

## Demand type
Follow-up tecnico de pagamento fora do escopo da PRD-124.

## Current problem
A PRD-124 corrige o wizard, a validacao local e a criacao local de pedido/mensalidade familiar. Ela nao altera a assinatura remota Stripe ja existente do titular. Para titulares com `stripe_subscription_id`, o estado local pode ficar correto enquanto a assinatura remota ainda segue no plano anterior.

## Goal
Criar regra transacional para migrar assinatura Stripe existente para o plano familiar correto, preservando webhook, historico local e idempotencia.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `stripe:stripe-best-practices`
- `lv-cleanup-audit`

## Scope
- Mapear assinatura local `Membership.stripe_subscription_id` para item de assinatura Stripe.
- Definir quando usar troca imediata, proration ou nova Checkout Session.
- Persistir metadata suficiente para reconciliacao por webhook.
- Cobrir idempotencia de retorno de checkout/webhook.
- Testar upgrade familiar com assinatura Stripe ativa.

## Out of scope
- Criar novos precos comerciais.
- Alterar fluxo Asaas.
- Implementar sem aprovacao explicita.

## Acceptance criteria
- [ ] Titular com assinatura Stripe ativa pode migrar para plano familiar sem duplicar assinatura remota.
- [ ] Webhook confirma o plano familiar local e mantem `stripe_subscription_id` correto.
- [ ] Retry de webhook/refresh nao duplica pedido nem membership.
- [ ] Falha Stripe nao cancela plano local anterior.
- [ ] Testes focados passam.

## Evidence planned
- Documentacao oficial Stripe sobre atualizar assinatura/itens de assinatura e Checkout Sessions.
- Testes unitarios com mocks Stripe.
- Validacao local com Stripe CLI quando aprovado.

## Status
Proposto, nao implementado.
