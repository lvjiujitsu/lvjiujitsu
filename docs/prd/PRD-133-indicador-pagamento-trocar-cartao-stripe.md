# PRD-133: Indicador de forma de pagamento + trocar cartão Stripe + histórico de cobrança falhada

## Summary
Complemento direto da PRD-132 (transição livre de planos + pausa), pedido pelo usuário ao revisar a tela de mensalidade: hoje não há nenhuma indicação de qual **forma de pagamento** e **gateway** o cliente usa (PIX/Cartão, Asaas/Stripe), e não existe nenhum jeito do cliente **trocar o cartão** de uma assinatura Stripe recorrente sem mexer em plano ou pausa. Quando o cartão de um cliente Stripe é recusado, o sistema só muda `Membership.status` para `past_due` — sem deixar rastro no histórico e sem indicar ao cliente o que fazer.

## Demand type
Nova funcionalidade + correção de lacuna (pedida explicitamente pelo usuário, com dois cenários concretos).

## Current problem
- `_build_billing_tab` (`system/services/membership.py`) não expõe forma de pagamento/gateway — o card de mensalidade só mostra o nome do plano.
- Não existe nenhum mecanismo de troca de cartão Stripe — nem view, nem service, nem Billing Portal.
- `mark_invoice_failed` (`system/services/membership.py`) só muda `Membership.status` para `past_due`; não cria nenhum registro em `MembershipInvoice` nem em nenhum outro model — a cobrança falhada não aparece em lugar nenhum do histórico.
- O botão "Pagar agora" existente só aparece quando há `tab.pending_order` (um `RegistrationOrder` Asaas) — uma falha de cobrança Stripe recorrente nunca gera esse tipo de pedido, então o cliente ficava sem nenhuma ação visível quando o cartão falhava.
- **Bug pré-existente descoberto durante a implementação**: `_build_payment_history_items` (`system/views/home_views.py`) acessava `membership.plan.display_name` incondicionalmente — quebrava a home com HTTP 500 assim que qualquer `MembershipInvoice` existisse para uma `Membership` baseada em `PlanPrice` (6ª ocorrência da mesma família de bug das PRD-127/129/130/132).
- **Gap descoberto durante a validação ao vivo**: o fluxo de confirmação Stripe do wizard público (`_handle_pre_registration_checkout_completed` em `stripe_webhooks.py` + `finalize_pre_registration` em `pre_registration.py`) nunca capturava/propagava `stripe_customer_id` para a `Membership` — só `stripe_subscription_id`. Sem `stripe_customer_id`, a nova função de trocar cartão nunca teria como funcionar para quem se cadastrou pelo wizard.

## Goal
1. O cliente vê claramente sua forma de pagamento e gateway (ex. "Cartão de crédito · Stripe (recorrente)", "PIX · Asaas").
2. Cliente com assinatura Stripe recorrente pode trocar o cartão a qualquer momento — mesmo travado pela carência de fidelidade (trocar cartão nunca é bloqueado, só trocar plano/cancelar) — sem expor ao cliente a opção de cancelar ou trocar de plano pelo próprio painel do Stripe.
3. Quando uma cobrança Stripe falha, o cliente vê um aviso claro + CTA "Trocar cartão", e o histórico de faturas registra a tentativa falhada até ser regularizada (quando a mesma fatura for paga depois, o registro se atualiza automaticamente).

## Context Ledger
### Files read in full
- `system/services/membership.py` (`mark_invoice_failed`, `record_invoice_from_stripe`, `_build_billing_tab`, `activate_membership_from_paid_order`)
- `system/services/stripe_webhooks.py` (todos os event types tratados; `_handle_pre_registration_checkout_completed`)
- `system/services/stripe_checkout.py` / `system/services/stripe_admin_actions.py` (confirmado: nenhum mecanismo de Billing Portal/troca de cartão existia)
- `templates/home/dashboard.html` (seção MENSALIDADE completa, incluindo `tab.recent_invoices` e o modal "Histórico de pagamentos")
- `system/models/plan.py` (`PlanPaymentMethod`, `gateway_code` — confirmado: só 3 valores usados no projeto — `asaas_pix`, `asaas_card`, `stripe_card`)

### Internet / official documentation
- `docs.stripe.com/api/customer_portal/sessions/create` (via fetch direto): parâmetro `flow_data={"type": "payment_method_update"}` direciona o cliente direto pra tela de troca de cartão, sem expor cancelar assinatura ou trocar plano. Confirmado que a chamada funciona mesmo sem configuração prévia do portal no Dashboard (usa configuração padrão automática).

### Limitations found
- Requer que a `Membership` tenha `stripe_customer_id` preenchido — corrigido nesta PRD (ver Goal 3 / gap descoberto).
- Validação ao vivo completa (criar cliente Stripe real, simular fatura falhada, confirmar Billing Portal Session real) exigiu ajustar manualmente os dados de teste de "Beatriz Aluna Stripe" (criada em sessão anterior via `stripe trigger`, que gera evento `checkout.session.completed` em modo `payment`, não `subscription` — por isso nunca teve `stripe_subscription_id`/`stripe_customer_id` reais). Revertido ao estado limpo após validar.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário pediu diretamente, com dois cenários de aceite explícitos: (1) cliente Stripe recorrente não pode cancelar/pausar exceto por atestado, mas se o cartão falhar deve ser indicado pra trocar e a pendência deve constar no histórico até regularizar; (2) cliente Asaas cartão quer trocar de cartão no mês seguinte sem pausar o serviço.

## Scope
- `system/models/membership.py::Membership`: novas properties `effective_payment_method`, `effective_gateway_code`, `effective_payment_summary_label`, `is_stripe_recurring`.
- `system/services/stripe_checkout.py::create_billing_portal_session(membership, request)`: cria Billing Portal Session com `flow_data={"type": "payment_method_update"}`.
- `system/views/plan_change_views.py::MembershipUpdateCardView`: view cliente (GET), redireciona pro Billing Portal real; bloqueia se não houver assinatura Stripe.
- `system/services/membership.py::mark_invoice_failed`: passa a registrar `MembershipInvoice(status="failed", amount_paid=0, paid_at=None)` via `update_or_create` pelo `stripe_invoice_id` — se a mesma fatura for paga depois, `record_invoice_from_stripe` atualiza o mesmo registro pra "paid" automaticamente.
- `system/services/membership.py::activate_membership_from_paid_order` / `system/services/stripe_webhooks.py::_handle_pre_registration_checkout_completed` / `system/services/pre_registration.py::finalize_pre_registration`: captura e propaga `stripe_customer_id` (gap pré-existente corrigido).
- `system/views/home_views.py::_build_payment_history_items`: corrigido bug pré-existente (`membership.plan.display_name` → `membership.effective_display_name`).
- `templates/home/dashboard.html`: badge de forma de pagamento; aviso "Pagamento pendente" + botão "Trocar cartão" (sempre visível pra assinatura Stripe não cancelada, independente de lock/pausa); lista de faturas e modal "Histórico de pagamentos" distinguem Pago/Falhou/Estornado.
- `static/system/css/home/dashboard.css`: `.billing-lock-notice--danger`, `.billing-compact-info__method`.

## Out of scope
- Configuração customizada do Stripe Customer Portal (logo, textos, features habilitadas além do padrão) — fica a cargo do Stripe Dashboard, fora do código.
- Retry automático de cobrança falhada (Stripe já tem Smart Retries configurável no Dashboard — não é código deste projeto).
- Troca de "cartão" para clientes Asaas — não existe cartão salvo no Asaas neste projeto (cada cobrança é um checkout novo); a próxima cobrança já naturalmente usa o cartão que o cliente informar.

## Rules and constraints
- Nunca usar o portal genérico do Stripe sem `flow_data=payment_method_update` — evita expor cancelamento/troca de plano self-service pelo Stripe, o que quebraria toda a trava de fidelidade da PRD-132.
- Sem chamada real a gateway em teste automatizado — mock de `stripe.billing_portal.Session.create`.
- Preservar suíte existente sem regressão.

## Test plan
- Properties de label/gateway para os 3 gateways existentes.
- `create_billing_portal_session`: erro sem `stripe_customer_id`; sessão criada com `flow_data` correto quando mockado.
- `MembershipUpdateCardView`: redireciona pro portal quando Stripe; redireciona pra home com erro quando não-Stripe.
- `mark_invoice_failed`: cria `MembershipInvoice(status=failed)`; mesma fatura paga depois atualiza o mesmo registro (não duplica).
- Regressão: home renderiza (200, sem 500) com `MembershipInvoice` de uma `Membership` `PlanPrice`.
- Captura/propagação de `stripe_customer_id` no fluxo de confirmação do wizard.

### Execution authorization
Local — mock de Stripe para testes automatizados; validação ao vivo contra API real do Stripe test-mode.

## Implemented
Ver Scope — todos os itens implementados nesta sessão.

## Evidence
- `manage.py test system.tests.test_membership_card_update` → **12 testes, OK**.
- `manage.py test` (suíte completa) → **597 testes, OK** (585 da PRD-132 + 12 novos), sem regressão.
- `manage.py check` → limpo.
- **Validação ao vivo contra API real do Stripe (test-mode)**:
  - Criado `stripe.Customer.create` real (`cus_UqGp3TeMKgVw04`) e vinculado à Membership de Beatriz.
  - `stripe.billing_portal.Session.create(..., flow_data={"type": "payment_method_update"})` retornou uma URL real e válida (`billing.stripe.com/p/session/...`).
  - View real (`GET /minha-mensalidade/trocar-cartao/`) confirmada retornando 302 (redirect real para o Billing Portal).
  - Simulado `mark_invoice_failed` com fatura real (`amount_due=22914`) — `Membership.status` virou `past_due`, badge "CARTÃO DE CRÉDITO · STRIPE (RECORRENTE)" e aviso "Pagamento pendente — a cobrança automática não foi concluída. Atualize seu cartão para regularizar." apareceram corretamente, com botão "Trocar cartão" em destaque (`btn--primary`).
  - Lista de faturas e modal "Histórico de pagamentos" mostraram "Falhou" corretamente (`billing-invoice-list` → `"07/07/2026\nR$ 0,00\nFalhou"`; modal → `"Adulto 2x por semana\nR$ 0,00\nFalhou"`).
  - Dados de validação revertidos ao estado limpo (Membership de Beatriz voltou a `active`, invoice falhada de teste removida; `stripe_customer_id` mantido por representar corretamente uma assinatura Stripe real).

## Evidence — rodada 2 (validação end-to-end completa, seguindo docs.stripe.com/testing#cards)
Pedido do usuário: trocar cartão seguindo a documentação oficial de teste do Stripe, pausar mensalidade e conferir vigência, adicionar 3 dependentes (um por gateway), pausar os 3, trocar cartão de 2, trocar modalidade PIX→Crédito de 1 e trocar ciclo de cobrança pra semestral de 1 — tudo contra as APIs reais (Asaas sandbox + Stripe test-mode), para simular integridade ponta a ponta do sistema.

- **3 dependentes reais criados** sob a titular Diana (Asaas PIX), cada um com gateway diferente: Eduarda (Asaas PIX), Fabio (Stripe recorrente — checkout REAL completado no navegador externo com o cartão de teste `4242 4242 4242 4242`, validade `12/34`, CVC `123`, exatamente conforme `docs.stripe.com/testing#cards`), Gustavo (Asaas cartão). Faixas diversificadas (branca/azul/marrom).
- **Pausa aprovada nos 3 dependentes**: Eduarda e Gustavo via trancamento self-service (permitido, fora de carência); Fabio via atestado médico (obrigatório nele — Stripe recorrente dentro da carência bloqueia self-service, confirmado pelo erro real `ValidationError` ao tentar self-service nele antes de trocar para `medical`). `current_period_end` postergado 10 dias nos 3; `fidelity_extension_days` só somou no Fabio (medical), confirmando a regra de negócio exata pedida pelo usuário.
- **Trocar cartão real, contra a API do Stripe test-mode, com o cartão oficial de teste**: Billing Portal aberto no navegador externo, preenchido `4242 4242 4242 4242` / `12/34` / `123` — Stripe criou um novo `PaymentMethod` (`pm_1TqbQPItFp0xr82skkS4VH6I`) e o definiu como `invoice_settings.default_payment_method` do customer real (confirmado via `stripe.Customer.retrieve` direto na API, não só pela UI).
- **Troca de cartão Asaas**: confirmado que não existe (nem deveria existir) um botão equivalente — Asaas neste projeto não guarda cartão, cada cobrança é um checkout novo; a "troca" acontece naturalmente informando outro cartão na próxima cobrança.
- **Troca de modalidade (Eduarda, PIX → Crédito, mesmo tier/ciclo)** e **troca de ciclo (Gustavo, mensal → semestral)**: ambas via `POST /minha-mensalidade/trocar-plano/` real, gerando `RegistrationOrder` de upgrade, pagamento Asaas real confirmado via `/sandbox/payment/{id}/confirm`, e aplicação da troca via processamento do evento `PAYMENT_CONFIRMED` (`process_asaas_event`) — confirmado no banco: Eduarda com `plan_price.gateway_code=asaas_card`; Gustavo com `billing_cycle=semiannual` e vigência ~6 meses à frente.

### Bug crítico encontrado e corrigido durante a validação
A troca de cartão real do Fabio (Stripe) disparou um evento real `customer.subscription.updated` (o `stripe listen` local capturou) que **zerou `Membership.current_period_start`/`current_period_end`** — descoberto ao inspecionar o resumo final. Causa raiz: `current_period_start`/`current_period_end` **saíram do objeto `Subscription` para o `SubscriptionItem`** nas versões recentes da API do Stripe (confirmado inspecionando o payload real via `stripe.Subscription.retrieve` — os campos não existem mais no nível superior). `upsert_membership_from_stripe_subscription`, `activate_membership_from_session` e `_apply_stripe_plan_change_migration` (esta última já escrita nesta sessão, PRD-132) liam só o nível antigo — sempre `None` agora — e a primeira função **sobrescrevia incondicionalmente** a vigência da Membership com `None` a cada evento real de sincronização (qualquer coisa dispara isso: trocar cartão, qualquer ação no Dashboard Stripe, etc.), corrompendo silenciosamente a vigência de qualquer aluno Stripe recorrente. Nenhum teste (nem a validação anterior desta sessão) pegou isso porque é a primeira vez que um ciclo completo e real (checkout real → evento de sync real → segundo evento de sync real) foi exercitado ponta a ponta.

**Corrigido**: novo helper `extract_stripe_subscription_period` (`system/services/membership.py`) tenta o nível superior primeiro e cai para `items.data[0]` quando ausente; usado nos 3 pontos de leitura. `upsert_membership_from_stripe_subscription` também passou a nunca sobrescrever uma data válida com `None` (só atualiza quando a extração retorna um valor). 4 testes novos de regressão, incluindo o cenário exato do bug (evento sem período em nenhum nível não deve apagar a vigência existente). Dados do Fabio corrigidos manualmente após o fix.

- `manage.py test system.tests.test_membership_card_update system.tests.test_membership_shared_subscription` → **24 testes, OK**.
- `manage.py test` (suíte completa) → **603 testes, OK**, sem regressão.
- `manage.py check` → limpo.
- Validação visual final ao vivo (Fabio): badge "CARTÃO DE CRÉDITO · STRIPE (RECORRENTE)", valor com desconto família aplicado corretamente (R$ 229,14 → R$ 187,89, já que ele é dependente da Diana), "Vigência 07/07/2026 → 17/08/2026" (10 dias de pausa médica refletidos), aviso de carência "liberados em 17/08/2026" (mesma data, prorrogação correta), botões "Pausar mensalidade" e "Trocar cartão" — sem "Trocar plano" (bloqueado corretamente pela carência).

### Outro gap corrigido no caminho
`_create_paid_plan_order` (`system/services/dependent_registration.py`) tinha o mesmo gap já corrigido na rodada 1 para o fluxo do titular: nunca propagava `stripe_customer_id` pro `Membership` do dependente. Corrigido nos dois pontos (assinatura da função + chamada em `finalize_dependent_registration`), com teste de regressão.

## Cleanup findings
- 6ª ocorrência da família de bug "código que só lê `SubscriptionPlan`/`membership.plan`" nesta sessão — `_build_payment_history_items`. Corrigida.
- Gap de `stripe_customer_id` nunca capturado no fluxo do wizard público **e** no fluxo de dependente — corrigido nos dois, com testes de regressão.
- Bug crítico de integridade de dados: `current_period_start/end` sendo zerados em qualquer evento real `customer.subscription.updated` por causa da migração de campo do Stripe (Subscription → SubscriptionItem). Corrigido com fallback + proteção contra sobrescrita por `None`.
- Dados de teste (Membership do Fabio) corrigidos manualmente após o fix, refletindo o valor correto que o sistema já corrigido teria calculado.

## Final status
Concluída e validada em duas rodadas — testes automatizados (12 + 12 novos = 24 específicos desta PRD; suíte completa final: **603 testes, OK**) e validação ao vivo completa contra APIs reais (Stripe test-mode: customer, Billing Portal Session real com cartão de teste oficial `4242 4242 4242 4242`, checkout de assinatura real, evento de sincronização real; Asaas sandbox: 3 pagamentos reais, troca de modalidade e de ciclo de cobrança). Um bug crítico de integridade de vigência (Stripe API field migration) e um gap de captura de `stripe_customer_id` no fluxo de dependente foram descobertos e corrigidos nesta segunda rodada — só apareceram exercitando o ciclo completo real, não em nenhum teste anterior.
