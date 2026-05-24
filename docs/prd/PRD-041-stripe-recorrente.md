# PRD-041: Stripe — Planos Recorrentes

## Resumo do que será implementado

Reintroduzir o Stripe como gateway de pagamento no fluxo de cadastro, exclusivamente em modo recorrente (Stripe Subscriptions). O aluno escolhe um plano com `gateway_code=stripe_card`, é redirecionado para o Stripe Checkout em modo `subscription`, o Stripe gerencia as cobranças automáticas no ciclo configurado, e os webhooks do Stripe confirmam o pagamento e mantêm o estado da assinatura no banco local.

---

## Tipo de demanda

Nova feature — integração externa (Stripe Subscriptions)

---

## Problema atual

Stripe foi removido do fluxo operacional (PRD-037). Toda cobrança recorrente é manual via Asaas. O Asaas não gerencia renovações automáticas de assinatura — cada ciclo exige uma nova cobrança. O Stripe Subscriptions resolve isso nativamente: criada a assinatura, o Stripe cobra automaticamente a cada ciclo, notifica via webhook e emite faturas.

---

## Objetivo

Permitir que o aluno pague a mensalidade com cartão de crédito via Stripe Checkout em modo recorrente. O banco local reflete o estado real da assinatura via webhooks. A academia recebe os repasses do Stripe no ciclo configurado, sem intervenção manual por renovação.

---

## Context Ledger

### Arquivos lidos integralmente (obrigatório antes de implementar)

- `system/models/plan.py` — `SubscriptionPlan`, `PlanPaymentMethod`, `STRIPE_INTERVAL_BY_CYCLE`
- `system/models/registration_order.py` — `RegistrationOrder`, `PaymentProvider`, `PaymentStatus`
- `system/models/membership.py` — `Membership` e ciclo de vida de assinaturas
- `system/models/pre_registration.py` — `PreRegistration`, `form_snapshot`
- `system/views/auth_views.py` — `PortalRegisterView.form_valid`, `_create_pre_registration_plan_payment`
- `system/views/payment_views.py` — `PaymentSuccessView`, `_handle_pre_registration_success`
- `system/views/asaas_views.py` — padrão existente de webhook + checkout
- `system/services/asaas_client.py` — padrão de cliente HTTP externo
- `system/services/asaas_checkout.py` — padrão de criação de cobrança
- `system/constants.py` — `CheckoutAction`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` — estrutura atual de planos
- `system/management/commands/seed_system_initial_subscription_plans_values.py` — seed ativa

### Arquivos adjacentes consultados

- `lvjiujitsu/settings.py` — variáveis `STRIPE_*`
- `lvjiujitsu/urls.py` — registro de rotas
- `system/urls.py` — rotas existentes
- `system/services/financial_transactions.py` — `apply_order_financials`
- `system/services/registration_checkout.py` — `gross_up_order_for_checkout`
- `static/system/js/auth/register.js` — inicialização e checkout do wizard
- `templates/login/register.html` — template do wizard

### Internet / documentação oficial

- Stripe Checkout Sessions em modo `subscription`: https://docs.stripe.com/billing/subscriptions/build-subscriptions
- Stripe Webhooks — eventos relevantes: https://docs.stripe.com/webhooks
- Stripe Python SDK: https://github.com/stripe/stripe-python
- Eventos obrigatórios: `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

### MCPs / ferramentas verificadas

- `manage.py check` — deve passar após mudanças de modelo
- Ciclo destrutivo — obrigatório se qualquer campo novo for adicionado ao modelo

### Limitações encontradas

- `PlanPaymentMethod` não tem choice `STRIPE_CARD` — usar `gateway_code="stripe_card"` como discriminador (campo já existe)
- Stripe requer HTTPS para webhooks — em dev, usar ngrok (mesmo padrão do Asaas)
- Stripe não deve substituir Asaas — os dois gateways coexistem; o wizard escolhe com base no plano selecionado

---

## Prompt de execução

### Persona

Agente de desenvolvimento especialista em Django 4.x + Stripe Python SDK seguindo SDD + TDD + arquitetura MVT com services.

### Ação

Implementar o fluxo completo de assinatura recorrente via Stripe Checkout no wizard de cadastro público, incluindo modelo de assinatura local, views de checkout e webhook, seed de planos e ajuste no JSON.

### Contexto

O wizard de cadastro atual encaminha pagamentos para o Asaas (PIX e Cartão). O roteamento ocorre em `PortalRegisterView._create_pre_registration_plan_payment` com base no `checkout_action` submetido. A nova rota `stripe_card` deve ser detectada ali e disparar uma Stripe Checkout Session em modo `subscription`.

O retorno do Stripe para `successUrl` confirma o pagamento via `PaymentSuccessView`. O webhook do Stripe atualiza o estado da assinatura localmente.

### Restrições

- sem hardcode de chaves Stripe — lidas de `.env` via `python-decouple`
- sem migrações manuais — ciclo destrutivo executado pelo usuário
- sem alterar o fluxo Asaas existente
- seed não aceita argumentos `--`; toda configuração via `.env`
- idempotente: rodar a seed duas vezes não duplica planos

---

## Escopo

### Modelo

| Item | Ação |
|---|---|
| `SubscriptionPlan.gateway_code` | já existe — usar `stripe_card` como valor discriminador |
| `Membership` ou novo `StripeSubscription` | registrar o `stripe_subscription_id` retornado pelo checkout |
| `RegistrationOrder.payment_provider` | adicionar `STRIPE = "stripe"` ao enum `PaymentProvider` |

> **Decisão de design**: verificar se `Membership` já tem campo para `stripe_subscription_id`. Se não, adicionar. O campo pode ser `CharField(blank=True)` e não quebra a lógica existente.

### CheckoutAction

Adicionar `STRIPE_CARD = "stripe_card"` em `system/constants.py`.

### Roteamento no wizard

Em `PortalRegisterView._create_pre_registration_plan_payment`:
```python
if checkout_action == CheckoutAction.STRIPE_CARD:
    return _create_stripe_checkout_session(pre_registration, plans_by_id, selected_plans)
```

### Nova view: `CreateStripeCheckoutSessionView`

```
POST /pagamentos/<pre_registration_id>/stripe-checkout/
```

Ou integrar diretamente em `_create_pre_registration_plan_payment` retornando a `session.url`.

Parâmetros da Checkout Session:
- `mode = "subscription"`
- `line_items`: uma entrada por plano selecionado, usando `stripe_price_id`
- `success_url = SITE_BASE_URL + /pagamentos/sucesso/?pre_registration_id=X&stage=plan&session_id={CHECKOUT_SESSION_ID}`
- `cancel_url = SITE_BASE_URL + /pagamentos/cancelado/`
- `client_reference_id = f"pre-registration:{pre_registration.pk}:plan"`
- `customer_email` do snapshot

### Webhook Stripe

```
POST /pagamentos/webhook/stripe/
```

Eventos tratados:

| Evento | Ação |
|---|---|
| `checkout.session.completed` | confirmar pagamento da pre-registration; registrar `stripe_subscription_id` |
| `invoice.paid` | renovação confirmada — atualizar status de assinatura local |
| `invoice.payment_failed` | marcar assinatura como inadimplente |
| `customer.subscription.updated` | sincronizar status e ciclo |
| `customer.subscription.deleted` | cancelar assinatura local |

### PaymentSuccessView

Adicionar fallback por `session_id` (Stripe) além do `id` (Asaas):
```python
stripe_session_id = request.GET.get("session_id")
if stripe_session_id:
    # buscar pre-registration pelo session_id registrado no metadata da session
```

### Seed

**Comando:** `seed_system_initial_subscription_plans_stripe`

- Lê `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- Depende de: nenhuma (planos Stripe são independentes dos planos Asaas)
- Cria planos Stripe com `gateway_code="stripe_card"`, `is_active=True`
- Para cada plano, sincroniza com Stripe API: cria `Product` se não existe, cria `Price` recorrente
- Armazena `stripe_product_id` e `stripe_price_id` no modelo

### JSON de dados da seed

**Arquivo:** `static/initial_data/seed_system_initial_subscription_plans_stripe.json`

Estrutura por item:
```json
{
  "code": "individual_2x_stripe_monthly",
  "display_name": "Individual 2x por semana - Stripe Cartão - Mensal",
  "audience": "adult",
  "weekly_frequency": 2,
  "billing_cycle": "monthly",
  "payment_method": "credit_card",
  "gateway_code": "stripe_card",
  "is_family_plan": false,
  "is_loyalty_plan": false,
  "base_monthly_net_price": "200.00",
  "gateway_fixed_fee": "0.00",
  "gateway_percentage_fee": "0.0399",
  "cycle_discount_percentage": "0.00",
  "display_order": 50
}
```

Planos a criar (mesma lógica dos planos Asaas existentes):
- Individual 2x / 5x × Mensal / Trimestral / Semestral / Anual
- Kids/Juvenil 2x / 5x × mesmos ciclos
- Família 2x / 5x × mesmos ciclos
- Total: mesma quantidade dos planos Asaas, mas com `gateway_code=stripe_card`

### Variáveis de ambiente necessárias

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Atualização no wizard (register.js)

Em `elStepPlanNext.addEventListener`:
```javascript
var action = (firstPlan && firstPlan.payment_method === 'pix') ? 'pix'
           : (firstPlan && firstPlan.gateway_code === 'stripe_card') ? 'stripe_card'
           : 'asaas_card';
setHidden('id_checkout_action', action);
document.getElementById('wizard-form').submit();
```

O plan catalog JSON precisa incluir `gateway_code` para que o JS consiga distinguir.

---

## Fora do escopo

- Portal de autogestão de assinatura (cancelar, trocar plano via Stripe Portal)
- Parcelamento via Stripe (somente cobrança mensal/cíclica recorrente)
- Migração de assinantes Asaas existentes para Stripe
- Relatórios de faturamento Stripe no painel admin

---

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `system/constants.py` | adicionar `STRIPE_CARD` ao `CheckoutAction` |
| `system/models/plan.py` | sem mudança de schema (gateway_code já existe) |
| `system/models/registration_order.py` | adicionar `STRIPE` ao `PaymentProvider` |
| `system/models/membership.py` | adicionar `stripe_subscription_id` (se não existe) |
| `system/services/stripe_client.py` | **novo** — cliente HTTP Stripe |
| `system/services/stripe_checkout.py` | **novo** — criar Checkout Session, tratar webhook |
| `system/views/stripe_views.py` | **novo** — `CreateStripeCheckoutView`, `StripeWebhookView` |
| `system/views/auth_views.py` | roteamento `STRIPE_CARD` em `_create_pre_registration_plan_payment` |
| `system/views/payment_views.py` | fallback por `session_id` em `PaymentSuccessView` |
| `system/urls.py` | registrar rotas Stripe |
| `system/management/commands/seed_system_initial_subscription_plans_stripe.py` | **novo** |
| `static/initial_data/seed_system_initial_subscription_plans_stripe.json` | **novo** |
| `static/system/js/auth/register.js` | detectar `gateway_code=stripe_card` para `checkout_action` |
| `system/services/registration_checkout.py` | incluir `gateway_code` no payload do plan catalog |
| `lvjiujitsu/settings.py` | ler `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` |
| `.env` | adicionar variáveis Stripe |
| `system/tests/test_stripe_checkout.py` | **novo** |
| `system/tests/test_stripe_webhook.py` | **novo** |

---

## Riscos e edge cases

| Risco | Mitigação |
|---|---|
| `stripe_price_id` não existe no Stripe (sandbox vs prod) | seed sincroniza e persiste o ID; verificar antes de criar Checkout Session |
| Webhook recebido antes do redirect `successUrl` | `checkout.session.completed` é o evento canônico; `successUrl` é UI — os dois são tratados independentemente |
| Plano Stripe selecionado mas sem `stripe_price_id` | validar no serviço; erro explícito antes de criar session |
| Asaas e Stripe coexistindo no wizard | plan catalog filtra por gateway corretamente; JS detecta pelo `gateway_code` |
| Cancelamento de assinatura no Stripe sem ação local | webhook `subscription.deleted` desativa assinatura local |

---

## Regras e restrições

- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações (política do projeto) — se `stripe_subscription_id` for novo campo, instruir ciclo destrutivo
- leitura integral obrigatória antes de tocar em qualquer arquivo
- validação obrigatória do fluxo completo (wizard → Stripe Checkout → webhook → wizard)

---

## Plano

- [ ] 1. Ler integralmente todos os arquivos listados no Context Ledger
- [ ] 2. Verificar se `Membership` já tem `stripe_subscription_id`; se não, adicionar e solicitar ciclo destrutivo
- [ ] 3. Adicionar `STRIPE_CARD` ao `CheckoutAction` e `STRIPE` ao `PaymentProvider`
- [ ] 4. Criar `stripe_client.py` com `create_checkout_session`, `retrieve_session`, `construct_webhook_event`
- [ ] 5. Criar `stripe_checkout.py` com serviço de criação de session e tratamento de webhook events
- [ ] 6. Criar `stripe_views.py` com `CreateStripeCheckoutView` e `StripeWebhookView`
- [ ] 7. Registrar rotas Stripe em `system/urls.py`
- [ ] 8. Atualizar `PortalRegisterView._create_pre_registration_plan_payment` para rota Stripe
- [ ] 9. Atualizar `PaymentSuccessView` com fallback `session_id`
- [ ] 10. Incluir `gateway_code` no payload do plan catalog (services)
- [ ] 11. Atualizar `register.js` para detectar `gateway_code=stripe_card`
- [ ] 12. Criar JSON de dados `seed_system_initial_subscription_plans_stripe.json`
- [ ] 13. Criar comando `seed_system_initial_subscription_plans_stripe`
- [ ] 14. Escrever testes (Red → Green → Refactor)
- [ ] 15. Validar fluxo completo com ngrok ativo (Stripe também precisa de webhook público em dev)
- [ ] 16. Limpeza final
- [ ] 17. Atualizar CLAUDE.md (novo seed, nova variável de ambiente)

---

## Validação visual

### Desktop
- Wizard step-plan exibe planos Stripe como opção (filtro por método)
- Clicar "Pagar mensalidade" com plano Stripe redireciona para Stripe Checkout
- Após pagamento, wizard exibe estado confirmado e permite avançar para materiais

### Mobile
- Mesma navegação do desktop; Stripe Checkout é responsivo

### Console do navegador
- Sem erros JS relacionados à seleção de plano Stripe

### Terminal
- Sem stack trace na criação da Checkout Session
- Webhook processado sem erro

---

## Validação ORM

```python
from system.models import SubscriptionPlan
SubscriptionPlan.objects.filter(gateway_code='stripe_card', is_active=True).count()
# deve retornar o número correto de planos

from system.models import PreRegistration
pr = PreRegistration.objects.latest('created_at')
pr.form_snapshot.get('plan_payment', {})
# deve conter asaas ou stripe payment id dependendo do gateway
```

---

## Validação de qualidade

- Sem hardcode de `STRIPE_SECRET_KEY`
- Webhook valida `Stripe-Signature` antes de processar
- `except: pass` proibido — erros Stripe levantam exceção explícita
- Sem `stripe_price_id` → erro antes de redirecionar

---

## Evidências (preencher após implementação)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 falhas
- [ ] Plano Stripe exibido no wizard
- [ ] Redirect para Stripe Checkout confirmado
- [ ] Webhook `checkout.session.completed` processado
- [ ] `pre_registration.status == PAYMENT_CONFIRMED` após webhook
- [ ] Wizard exibe estado "pago" ao retornar do Stripe

## Implementado

_(preencher após conclusão)_

## Desvios do plano

_(preencher após conclusão)_

## Pendências

_(preencher após conclusão)_
