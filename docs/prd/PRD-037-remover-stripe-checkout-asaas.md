# PRD-037: Remover Stripe do checkout e usar Asaas

## Resumo do que será implementado
Remover a Stripe do fluxo operacional de planos e checkout, mantendo apenas Asaas para PIX e cartão de crédito. O cartão deve gerar cobrança Asaas e redirecionar o cliente para a `invoiceUrl` da Asaas.

## Tipo de demanda
Integração externa.

## Problema atual
O catálogo de planos contém linhas `stripe_card`, o frontend envia `checkout_action=stripe` para cartão, e o backend tenta criar checkout Stripe. A Stripe não atende ao parcelamento necessário para o negócio.

## Objetivo
- JSON de valores de planos sem Stripe.
- Seed de valores criando apenas planos Asaas PIX e Asaas Cartão.
- Checkout de cartão usando Asaas.
- Rotas reais para checkout Asaas registradas.
- Testes cobrindo remoção de Stripe dos planos gerados e payload de cobrança Asaas cartão.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/constants.py`
- `system/forms/registration_forms.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/views/asaas_views.py`
- `system/urls.py`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/services/registration_checkout.py`
- `system/services/financial_transactions.py`
- `system/services/pricing.py`
- `system/models/plan.py`
- `system/models/registration_order.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/system/js/auth/register.js`
- `system/tests/test_asaas.py`
- `system/tests/test_commands.py`
- `system/tests/test_services.py`
- `system/tests/test_plan_models.py`

### Internet / documentação oficial
- Asaas: Cobranças via cartão de crédito.
- Asaas: Criar uma cobrança parcelada.
- Asaas: Criar parcelamento com cartão de crédito.

### Limitações encontradas
- Remoção física dos campos e models Stripe exige mudança de schema. Pela política do projeto, isso fica fora desta entrega.

## Critérios de aceite
- [x] A seed `seed_system_initial_subscription_plans_values` cria/atualiza apenas planos Asaas.
- [x] Linhas `stripe_card` existentes são inativadas pela seed.
- [x] Plano cartão resolve `PaymentProvider.ASAAS`.
- [x] Botão de cartão do cadastro envia `checkout_action=asaas_card`.
- [x] Checkout de cartão cria cobrança Asaas `CREDIT_CARD` e redireciona para `invoiceUrl`.
- [x] Planos parcelados enviam `installmentCount` e `totalValue`; plano mensal 1x envia `value`.
- [x] Rotas de checkout Asaas existem.
- [x] Testes e `manage.py check` passam.

## Fora do escopo
- Remover campos Stripe dos models/migrations.
- Implementar captura transparente de dados do cartão dentro do site.
- Reescrever tela administrativa financeira inteira.

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e documentação Asaas
- [x] 3. Testes
- [x] 4. Implementação
- [x] 5. Validação completa
- [x] 6. Atualização documental

## Evidências
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 163 testes, OK.
- `.\.venv\Scripts\python.exe manage.py check` — sem issues.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 2 arquivos copiados, 167 inalterados.

## Implementado
- JSON de valores dos planos reduzido para Asaas PIX e Asaas Cartão.
- Seed de valores valida gateways suportados e inativa planos `stripe_card` legados.
- Checkout de cartão usa Asaas `CREDIT_CARD` e redireciona para `invoiceUrl`.
- Frontend do cadastro envia `asaas_card` para cartão.
- Rotas `asaas-pix-create`, `asaas-card-create`, `payment-checkout` e webhook Asaas registradas.

## Pendências
- Remoção física de campos/models/serviços Stripe exige ciclo destrutivo de schema e não foi feita nesta entrega.
