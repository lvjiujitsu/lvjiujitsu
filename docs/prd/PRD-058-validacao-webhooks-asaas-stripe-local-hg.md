# PRD-058: Validação de Webhooks Asaas e Stripe — Local e Homologação

## Resumo do que será implementado

Guia operacional completo e verificado para testar localmente todos os eventos de webhook do Asaas e do Stripe, com checklist de prontidão para validação via Chrome MCP no ambiente de homologação (Supabase + Render HG). Este PRD não altera código — é um documento de validação e teste executável.

## Tipo de demanda

Revisão de segurança + integração externa + validação funcional

## Problema atual

- O banco local (SQLite) está vazio: 0 RegistrationOrders, 0 PreRegistrations, 0 AsaasWebhookEvents, 0 StripeWebhookEvents.
- `SITE_BASE_URL` aponta para `https://lvjiujitsu-hg.onrender.com` (Render HG), não para ngrok — o que torna a `successUrl` do Asaas inoperante em testes locais de browser real.
- A Stripe CLI não está instalada localmente, tornando a simulação de webhooks Stripe com assinatura válida impossível sem instalação.
- Não há um roteiro consolidado para validar os dois gateways em sequência, cobrindo todos os eventos mapeados no código.

## Objetivo

1. Documentar e executar a validação de tokens (Asaas + Stripe) localmente.
2. Fornecer os comandos exatos para simular cada evento de webhook localmente via `Invoke-RestMethod`.
3. Documentar o roteiro de criação de dados de teste (PreRegistration + RegistrationOrder) sem fazer um cadastro real.
4. Produzir um checklist de prontidão para validação via Chrome MCP no Render HG.

---

## Context Ledger

### Arquivos lidos integralmente

- `system/views/asaas_views.py` — `AsaasWebhookView`, auth via `asaas-access-token`
- `system/views/stripe_views.py` — `StripeWebhookView`, auth via `Stripe-Signature`
- `system/views/payment_views.py` — `PaymentSuccessView`, `_handle_pre_registration_success`
- `system/views/auth_views.py` — `PortalRegisterView`, `_create_pre_registration_plan_payment`
- `system/services/asaas_webhooks.py` — todos os eventos mapeados
- `system/services/stripe_webhooks.py` — todos os eventos mapeados
- `system/services/asaas_checkout.py` — `create_pix_charge_for_order`, `create_credit_card_charge_for_order`
- `system/services/asaas_client.py` — `verify_webhook_token`

### Arquivos adjacentes consultados

- `lvjiujitsu/settings.py` — `ASAAS_WEBHOOK_TOKEN`, `STRIPE_WEBHOOK_SECRET`, `SITE_BASE_URL`
- `system/urls.py` — rotas `/pagamentos/webhook/asaas/` e `/pagamentos/webhook/stripe/`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` — contrato do wizard público
- `docs/prd/PRD-041-stripe-recorrente.md` — Stripe Recorrente

### MCPs / ferramentas verificadas

- Django check: **0 issues** ✓
- `.venv` Python 3.12.10: **ok** ✓
- `manage.py check`: **passou** ✓
- Stripe CLI: **NÃO instalada** ⚠️ — ver Seção de Stripe abaixo

### Estado do banco local (SQLite — após validações 2026-06-10)

| Tabela | Total |
|---|---|
| `RegistrationOrder` | 0 |
| `PreRegistration` | 2 (ID=1 Carlos PIX finalized; ID=2 Ana Stripe payment_confirmed) |
| `AsaasWebhookEvent` | 2 (evt_pix_test_001 PAYMENT_CONFIRMED; segundo simulado) |
| `StripeWebhookEvent` | 11+ (checkout.session.completed, charge.updated, etc.) |

### Estado dos tokens (verificado via shell + decouple direto no .env — 2026-06-10)

| Variável | Status no `.env` | Detalhe |
|---|---|---|
| `ASAAS_WEBHOOK_TOKEN` | ✓ **Configurado** | Configurado no `.env`; webhooks Asaas retornam HTTP 200 |
| `ASAAS_API_KEY` | ✓ **Configurado** | len=166 — chamadas de saída ao Asaas funcionam |
| `ASAAS_API_URL` | ✓ **Configurado** | `https://api-sandbox.asaas.com/v3` (sandbox) |
| `STRIPE_SECRET_KEY` | ✓ **Configurado** | prefixo `sk_test`, len=107 (modo teste) |
| `STRIPE_WEBHOOK_SECRET` | ✓ **Configurado** | Stripe CLI `whsec_74ab90bc...` configurado; webhooks Stripe retornam HTTP 200 |
| `SITE_BASE_URL` | ⚠️ **Aponta para HG Render** | `https://lvjiujitsu-hg.onrender.com` — testes de browser local requerem troca para ngrok |

> **Nota sobre a leitura anterior:** Na primeira execução do preflight, os valores de `ASAAS_WEBHOOK_TOKEN` e `STRIPE_WEBHOOK_SECRET` foram lidos como `len: 49` e `whsec_m` respectivamente. Isso ocorreu porque estavam configurados como **variáveis de ambiente na sessão PowerShell** — o `python-decouple` prioriza variáveis de ambiente sobre o arquivo `.env`. A leitura direta do `.env` confirma que os valores estão vazios no arquivo. Para persistir, devem ser adicionados ao `.env`.

### Ação obrigatória antes de continuar os testes

```
1. ASAAS_WEBHOOK_TOKEN — obter no painel Asaas sandbox:
   Minha Conta → Notificações → Token de acesso ao webhook
   Adicionar no .env: ASAAS_WEBHOOK_TOKEN=<valor>

2. STRIPE_WEBHOOK_SECRET — duas opções:
   a) Stripe CLI local: stripe listen → copiar o whsec_ exibido → adicionar no .env
   b) Painel Stripe: Developers → Webhooks → endpoint HG → Signing secret
      (usar apenas para testes no HG Render, não para simulação local)
```

### Limitações encontradas

1. **`SITE_BASE_URL` aponta para HG Render**, não para ngrok. Isso afeta:
   - A `successUrl` enviada ao Asaas na criação de cobrança → o browser será redirecionado para HG Render após pagamento, não para `127.0.0.1:8000`
   - **Não afeta** a simulação direta de webhooks via `Invoke-RestMethod`

2. **Stripe CLI ausente** localmente. O `STRIPE_WEBHOOK_SECRET` estático do painel Stripe funciona com webhooks vindos dos servidores Stripe (ex: HG Render), mas a simulação local com `Invoke-RestMethod` sem assinatura HMAC válida será rejeitada com HTTP 400.

3. **Banco vazio**: os webhooks do Asaas dependem de um `RegistrationOrder` existente para ter efeito. Webhook processado para um order inexistente retorna HTTP 200 mas não grava nada relevante (comportamento correto — o service retorna `None` para order).

---

## Arquitetura dos dois fluxos de pagamento

### Fluxo A — Aluno existente (RegistrationOrder)

```
Aluno logado → pedido pendente → CreatePixChargeView / CreateCreditCardChargeView
    → Asaas cria cobrança → retorna invoice_url
    → Browser vai para Asaas → paga
    → Asaas envia webhook POST /pagamentos/webhook/asaas/
    → AsaasWebhookView → process_asaas_event → atualiza RegistrationOrder.payment_status
    → Ativa Membership do aluno
```

**Confirmação**: server-to-server via webhook Asaas. `successUrl` é URL de conveniência para o browser.

### Fluxo B — Novo aluno (wizard público / PreRegistration)

```
Visitante → wizard → PortalRegisterView (step-plan)
    → _create_pre_registration_plan_payment → Asaas cria cobrança com successUrl
    → Browser vai para Asaas/Stripe → paga
    → Browser é redirecionado para successUrl = SITE_BASE_URL + /pagamentos/sucesso/
    → PaymentSuccessView._handle_pre_registration_success
    → PreRegistration.form_snapshot["plan_paid"] = True
    → PreRegistration.status = PAYMENT_CONFIRMED
    → Volta para o wizard (step-materials)
```

**Confirmação primária**: browser via `successUrl`. O webhook Asaas server-to-server (para `RegistrationOrder`) NÃO é usado neste fluxo — a confirmação é feita pela view `payment-success`.

> **Implicação crítica**: simular o webhook Asaas não confirma pagamentos do wizard público. Para testar o wizard, é necessário chamar `PaymentSuccessView` com os parâmetros corretos.

---

## Escopo

1. Validar tokens localmente
2. Simular todos os eventos Asaas mapeados em `asaas_webhooks.py`
3. Simular todos os eventos Stripe mapeados em `stripe_webhooks.py` (via CLI ou HG)
4. Simular a confirmação de pagamento do wizard (fluxo B) via `payment-success`
5. Checar o estado do banco após cada simulação
6. Checklist de prontidão para HG Render + Chrome MCP

## Fora do escopo

- Alterar código de produção
- Criar migrações
- Testar fluxos de professor, repasse (`TRANSFER_*`) com dados reais no Asaas
- Configurar conta Asaas no painel (URL de webhook deve já estar apontando para ngrok ou HG)

---

## Plano de validação

### Passo 0 — Verificar tokens ativos

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from django.conf import settings
print('ASAAS_WEBHOOK_TOKEN set:', bool(settings.ASAAS_WEBHOOK_TOKEN), '| len:', len(settings.ASAAS_WEBHOOK_TOKEN or ''))
print('STRIPE_SECRET_KEY prefix:', (settings.STRIPE_SECRET_KEY or '')[:7])
print('STRIPE_WEBHOOK_SECRET prefix:', (settings.STRIPE_WEBHOOK_SECRET or '')[:8])
print('SITE_BASE_URL:', settings.SITE_BASE_URL)
print('ASAAS_API_URL:', settings.ASAAS_API_URL)
print('DEBUG:', settings.DEBUG)
"
```

**Resultado esperado:**
- `ASAAS_WEBHOOK_TOKEN set: True | len: 49` ✓
- `STRIPE_SECRET_KEY prefix: sk_test` ✓
- `STRIPE_WEBHOOK_SECRET prefix: whsec_m` ✓
- `SITE_BASE_URL:` valor configurado (ngrok para testes locais de browser / HG para deploy)

---

### Passo 1 — Criar dados de teste para webhook Asaas (RegistrationOrder)

O banco está vazio. Para testar os webhooks do Fluxo A, é necessário ao menos um `RegistrationOrder` com `asaas_payment_id` preenchido.

**Opção 1a — criar via shell (mais rápida para webhooks):**

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, PaymentStatus, PaymentProvider
from system.models import Person, SubscriptionPlan

# Requer ao menos um Person e SubscriptionPlan no banco
# Se o banco estiver vazio, rodar primeiro:
# .\.venv\Scripts\python.exe manage.py seed_system_initial_person_type
# .\.venv\Scripts\python.exe manage.py seed_system_initial_subscription_plans
# .\.venv\Scripts\python.exe manage.py seed_system_initial_subscription_plans_values

person = Person.objects.filter(is_active=True).first()
plan = SubscriptionPlan.objects.filter(is_active=True).first()

if person and plan:
    order = RegistrationOrder.objects.create(
        person=person,
        plan=plan,
        total=plan.price,
        payment_status=PaymentStatus.PENDING,
        provider=PaymentProvider.ASAAS,
        asaas_payment_id='pay_test_webhook_001',
    )
    print(f'RegistrationOrder criado: pk={order.pk} asaas_id={order.asaas_payment_id}')
else:
    print('ERROR: Person ou SubscriptionPlan não encontrado — rodar seeds primeiro')
"
```

**Opção 1b — via wizard + Asaas real (com ngrok ativo):**

Rodar o wizard público até o step-plan, escolher plano e pagar no Asaas sandbox. O Asaas retorna e cria o `asaas_payment_id` automaticamente via `create_pix_charge_for_order`.

---

### Passo 2 — Obter o token Asaas para os headers

```powershell
# Atribuir o token a uma variável PowerShell (sem revelar em log)
$AsaasToken = .\.venv\Scripts\python.exe manage.py shell -c "from django.conf import settings; print(settings.ASAAS_WEBHOOK_TOKEN)"
$AsaasToken = $AsaasToken.Trim()
```

---

### Passo 3 — Simular webhooks Asaas

Substituir `ORDER_PK` pelo pk real do `RegistrationOrder` obtido no Passo 1.
Cada chamada deve retornar **HTTP 200**.

#### 3.1 PAYMENT_CONFIRMED — pagamento confirmado (ativa membership)

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_confirmed_001","event":"PAYMENT_CONFIRMED","payment":{"id":"pay_test_webhook_001","status":"CONFIRMED","externalReference":"ORDER_PK"}}'
```

**Estado esperado após:** `RegistrationOrder.payment_status = PAID`, `AsaasWebhookEvent` criado.

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder
from system.models.asaas import AsaasWebhookEvent
o = RegistrationOrder.objects.get(pk=ORDER_PK)
print('Order status:', o.payment_status, '| paid_at:', o.paid_at)
print('Webhook events:', AsaasWebhookEvent.objects.filter(order=o).count())
"
```

#### 3.2 PAYMENT_RECEIVED — equivalente ao CONFIRMED (idempotente no segundo envio)

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_received_001","event":"PAYMENT_RECEIVED","payment":{"id":"pay_test_webhook_001","status":"RECEIVED","externalReference":"ORDER_PK"}}'
```

**Estado esperado:** HTTP 200, `duplicate=False` se event_id diferente, order permanece PAID.

#### 3.3 PAYMENT_OVERDUE — pagamento vencido (marca FAILED)

> Criar um novo `RegistrationOrder` com status PENDING antes de testar este evento.

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_overdue_001","event":"PAYMENT_OVERDUE","payment":{"id":"pay_test_webhook_002","externalReference":"ORDER_PK_2"}}'
```

#### 3.4 PAYMENT_REFUNDED — estorno total

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_refunded_001","event":"PAYMENT_REFUNDED","payment":{"id":"pay_test_webhook_001","refundedValue":"150.00","externalReference":"ORDER_PK"}}'
```

#### 3.5 PAYMENT_PARTIALLY_REFUNDED — estorno parcial

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_partial_001","event":"PAYMENT_PARTIALLY_REFUNDED","payment":{"id":"pay_test_webhook_001","refundedValue":"50.00","externalReference":"ORDER_PK"}}'
```

#### 3.6 Token inválido — deve retornar HTTP 401

```powershell
Invoke-WebRequest -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"="token_invalido_qualquer"} `
  -ContentType "application/json" `
  -Body '{"id":"evt_auth_test","event":"PAYMENT_CONFIRMED","payment":{"id":"x"}}' `
  | Select-Object StatusCode
# Esperado: 401
```

#### 3.7 Evento duplicado — deve retornar HTTP 200 com duplicate=True

Reenviar exatamente o mesmo body do evento 3.1 (mesmo `id`). O service deve retornar `duplicate=True` e não reprocessar.

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_confirmed_001","event":"PAYMENT_CONFIRMED","payment":{"id":"pay_test_webhook_001","status":"CONFIRMED","externalReference":"ORDER_PK"}}'
# Esperado: HTTP 200, AsaasWebhookEvent.count() não aumenta
```

---

### Passo 4 — Simular confirmação do wizard público (Fluxo B — PreRegistration)

O wizard não usa server-to-server webhook para confirmar — usa o redirect do browser para `/pagamentos/sucesso/`. A simulação é feita chamando a view diretamente.

#### 4.1 Criar PreRegistration de teste via shell

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, PreRegistrationStatus
from system.constants import CheckoutAction

pr = PreRegistration.objects.create(
    session_key='test-session-key-001',
    registration_profile='student',
    holder_cpf='00000000000',
    holder_email='teste@lvjiujitsu.com.br',
    status=PreRegistrationStatus.AWAITING_PAYMENT,
    checkout_action=CheckoutAction.ASAAS_PIX,
    form_snapshot={
        'plan_payment': {
            'asaas_payment_id': 'pay_pr_test_001',
        },
        'plan_paid': False,
    },
)
print(f'PreRegistration pk={pr.pk} status={pr.status}')
"
```

#### 4.2 Simular redirect do Asaas para payment-success (stage=plan)

> Esta chamada simula o que acontece quando o browser do usuário é redirecionado de volta pelo Asaas.
> Precisa do Django rodando em 127.0.0.1:8000.

```powershell
# Via browser: abrir http://127.0.0.1:8000/pagamentos/sucesso/?pre_registration_id=PR_PK&stage=plan
# O Django processa e marca plan_paid=True no snapshot

# Via shell (equivalente direto sem browser):
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, PreRegistrationStatus
pr = PreRegistration.objects.get(pk=PR_PK)
snap = pr.form_snapshot or {}
snap['plan_paid'] = True
pr.form_snapshot = snap
pr.status = PreRegistrationStatus.PAYMENT_CONFIRMED
pr.save(update_fields=['form_snapshot', 'status', 'updated_at'])
print('PreRegistration atualizada:', pr.pk, pr.status, 'plan_paid:', snap.get('plan_paid'))
"
```

#### 4.3 Verificar estado do wizard após confirmação

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.get(pk=PR_PK)
snap = pr.form_snapshot or {}
print('status:', pr.status)
print('plan_paid:', snap.get('plan_paid'))
print('materials_paid:', snap.get('materials_paid'))
"
```

---

### Passo 5 — Simular webhooks Stripe

#### 5.1 Verificação de status do secret

O `STRIPE_WEBHOOK_SECRET` configurado (`whsec_m*`) é o secret estático gerado pelo painel Stripe para o endpoint registrado no HG Render. **Este secret não pode ser usado para assinar manualmente um payload** — a validação do Stripe usa HMAC-SHA256 com timestamp.

**Para simulação local, instalar a Stripe CLI:**

```powershell
# Windows — via Scoop (recomendado)
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe

# Ou via download direto: https://github.com/stripe/stripe-cli/releases
# Extrair stripe.exe e colocar no PATH
```

**Verificar instalação:**

```powershell
stripe --version
stripe login
```

#### 5.2 Iniciar listener local (Stripe CLI)

```powershell
# Terminal 1 — listener (gera um whsec_ temporário para a sessão)
stripe listen --forward-to http://127.0.0.1:8000/pagamentos/webhook/stripe/

# Copiar o "webhook signing secret" exibido (whsec_xxx)
# Atualizar temporariamente no .env: STRIPE_WEBHOOK_SECRET=whsec_xxx (o da CLI)
# Reiniciar o Django para carregar o novo valor
```

#### 5.3 Disparar eventos (Terminal 2, com listener ativo)

```powershell
# checkout.session.completed — pagamento de sessão confirmado
stripe trigger checkout.session.completed

# checkout.session.expired — sessão expirada (marca order CANCELED)
stripe trigger checkout.session.expired

# payment_intent.payment_failed — falha no pagamento
stripe trigger payment_intent.payment_failed

# invoice.paid — fatura recorrente paga (Stripe Subscription)
stripe trigger invoice.paid

# invoice.payment_failed — falha em fatura recorrente
stripe trigger invoice.payment_failed

# customer.subscription.updated — plano atualizado
stripe trigger customer.subscription.updated

# customer.subscription.deleted — plano cancelado
stripe trigger customer.subscription.deleted

# charge.refunded — estorno
stripe trigger charge.refunded
```

**Estado esperado após cada evento:** HTTP 200 no terminal do listener, `StripeWebhookEvent` criado no banco.

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import StripeWebhookEvent
for e in StripeWebhookEvent.objects.order_by('-created_at')[:10]:
    print(e.created_at.strftime('%H:%M:%S'), e.event_type, 'order:', e.order_id, 'membership:', e.membership_id)
"
```

#### 5.4 Sem Stripe CLI — alternativa para HG (sem simulação local)

Se a Stripe CLI não for instalada, os eventos Stripe devem ser testados diretamente no HG Render:

1. Acessar o [Dashboard Stripe](https://dashboard.stripe.com/test/webhooks)
2. Selecionar o endpoint `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/stripe/`
3. Clicar em "Send test webhook" para cada evento da lista acima
4. Verificar o status no painel Stripe e no banco HG via `manage.py shell` com `.env.hg`

---

### Passo 6 — Verificação consolidada do banco após testes

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, StripeWebhookEvent
from system.models.asaas import AsaasWebhookEvent
from system.models import PreRegistration

print('=== ESTADO FINAL DO BANCO ===')
print()
print('RegistrationOrders:')
for o in RegistrationOrder.objects.all():
    print(f'  pk={o.pk} status={o.payment_status} asaas_id={o.asaas_payment_id}')

print()
print('PreRegistrations:')
for pr in PreRegistration.objects.all():
    snap = pr.form_snapshot or {}
    print(f'  pk={pr.pk} status={pr.status} plan_paid={snap.get(\"plan_paid\")} materials_paid={snap.get(\"materials_paid\")}')

print()
print('AsaasWebhookEvents:')
for e in AsaasWebhookEvent.objects.order_by('created_at'):
    print(f'  {e.event_type} order={e.order_id} duplicate_check: id={e.event_id[:20]}...')

print()
print('StripeWebhookEvents:')
for e in StripeWebhookEvent.objects.order_by('created_at'):
    print(f'  {e.event_type} order={e.order_id} membership={e.membership_id}')
"
```

---

## Checklist de prontidão para HG Render + Chrome MCP

### Configuração de ambiente HG

- [ ] `SITE_BASE_URL` no Render HG aponta para `https://lvjiujitsu-hg.onrender.com` ✓ (já configurado localmente)
- [ ] `ASAAS_API_URL` aponta para `https://api-sandbox.asaas.com/v3` (sandbox) ✓
- [ ] `ASAAS_WEBHOOK_TOKEN` configurado no Render HG Dashboard (mesmo valor do `.env.hg`)
- [ ] `STRIPE_SECRET_KEY` configurado no Render HG Dashboard (sk_test)
- [ ] `STRIPE_WEBHOOK_SECRET` do painel Stripe configurado para o endpoint HG

### Validação de URL de webhook no painel Asaas

- [ ] Painel Asaas sandbox → Minha Conta → Notificações → URL = `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/asaas/`
- [ ] Token configurado no painel Asaas = mesmo valor de `ASAAS_WEBHOOK_TOKEN`

### Validação de URL de webhook no painel Stripe

- [ ] Dashboard Stripe → Webhooks → endpoint = `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/stripe/`
- [ ] Eventos habilitados: `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, `charge.refunded`, `charge.refund.updated`

### Roteiro de teste via Chrome MCP no HG Render

#### Fluxo A — Aluno existente (RegistrationOrder + webhook real)

1. Logar no HG Render como aluno com pedido pendente
2. Navegar para checkout `/pagamentos/<order_id>/asaas-pix/`
3. Completar pagamento PIX no Asaas sandbox
4. Aguardar webhook chegar (1–5 segundos)
5. Verificar via shell HG que `RegistrationOrder.payment_status = PAID`

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, PaymentStatus
from system.models.asaas import AsaasWebhookEvent
print('Últimos orders:', list(RegistrationOrder.objects.filter(payment_status=PaymentStatus.PAID).values('pk', 'paid_at').order_by('-paid_at')[:5]))
print('Últimos events:', list(AsaasWebhookEvent.objects.order_by('-created_at').values('event_type', 'created_at')[:5]))
"
```

#### Fluxo B — Wizard público (PreRegistration via Chrome MCP)

1. Chrome MCP navega para `https://lvjiujitsu-hg.onrender.com/cadastro/`
2. Preencher dados → escolher plano
3. Clicar em pagar → ir para Asaas sandbox
4. No Asaas sandbox: usar cartão de teste `4111 1111 1111 1111` ou PIX fictício
5. Aguardar redirect de volta para `/pagamentos/sucesso/?pre_registration_id=X&stage=plan`
6. Verificar que o wizard avança para step-materials
7. Completar materiais e resumo
8. Finalizar → verificar `Person` criado no banco HG

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, Person
from system.models import PreRegistrationStatus
finalized = PreRegistration.objects.filter(status=PreRegistrationStatus.FINALIZED).order_by('-updated_at')[:3]
for pr in finalized:
    print(f'PR pk={pr.pk} email={pr.holder_email}')
new_persons = Person.objects.order_by('-created_at')[:3]
for p in new_persons:
    print(f'Person pk={p.pk} name={p.full_name} active={p.is_active}')
"
```

---

## Critérios de aceite

- [ ] `manage.py check` passa com 0 issues (verificável: comando)
- [ ] Webhook Asaas com token correto retorna HTTP 200 (verificável: Invoke-RestMethod)
- [ ] Webhook Asaas com token inválido retorna HTTP 401 (verificável: Invoke-WebRequest + StatusCode)
- [ ] Evento duplicado retorna HTTP 200 sem duplicar `AsaasWebhookEvent` (verificável: shell count)
- [ ] PAYMENT_CONFIRMED atualiza `RegistrationOrder.payment_status = PAID` (verificável: shell)
- [ ] PAYMENT_OVERDUE atualiza para `FAILED` (verificável: shell)
- [ ] PAYMENT_REFUNDED atualiza para `REFUNDED` e registra `refunded_at` (verificável: shell)
- [ ] Confirmação de PreRegistration via `payment-success` marca `plan_paid=True` e `status=PAYMENT_CONFIRMED` (verificável: shell)
- [ ] Webhook Stripe retorna HTTP 200 para eventos válidos (verificável: Stripe CLI ou painel)
- [ ] Webhook Stripe retorna HTTP 400 para payload sem assinatura (verificável: curl/Invoke-WebRequest)
- [ ] `StripeWebhookEvent` criado para cada evento Stripe processado (verificável: shell)
- [ ] No HG Render: `SITE_BASE_URL` configurado corretamente → successUrl válida para Asaas

---

## Riscos e edge cases

| Risco | Impacto | Mitigação |
|---|---|---|
| `SITE_BASE_URL` apontando para HG localmente | successUrl do Asaas redireciona browser para HG, não para 127.0.0.1 | Para testes de browser local, trocar temporariamente para ngrok |
| Stripe CLI ausente | Impossível simular webhooks Stripe com assinatura localmente | Instalar via Scoop ou usar painel Stripe para testar direto no HG |
| Banco vazio sem seeds | Webhooks processam sem efeito (order não encontrado) | Rodar seeds mínimas ou criar dados via shell antes dos testes |
| `AsaasWebhookEvent.event_id` único | Segundo envio do mesmo `id` retorna `duplicate=True` | Usar `id` diferente em cada teste ou verificar que o comportamento é intencional |
| Token Asaas sandbox vs produção | Webhook com token de prod não funciona em local/hg | Verificar que `ASAAS_WEBHOOK_TOKEN` corresponde ao ambiente correto do painel Asaas |

---

## Regras e restrições

- SDD antes de código — este PRD é documento de validação, sem alterações de código
- Sem hardcode — nenhum token revelado em log ou documento
- Sem migrações — este PRD não altera schema
- Leitura integral obrigatória — todos os arquivos do fluxo foram lidos antes deste PRD

---

## Validação técnica mínima

```powershell
# 1. Check Django
.\.venv\Scripts\python.exe manage.py check

# 2. Verificar tokens
.\.venv\Scripts\python.exe manage.py shell -c "
from django.conf import settings
assert settings.ASAAS_WEBHOOK_TOKEN, 'ASAAS_WEBHOOK_TOKEN vazio'
assert settings.STRIPE_SECRET_KEY, 'STRIPE_SECRET_KEY vazio'
assert settings.STRIPE_WEBHOOK_SECRET, 'STRIPE_WEBHOOK_SECRET vazio'
print('Todos os tokens configurados.')
"

# 3. Verificar que as rotas respondem (esperar 405 em GET, não 404)
Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" | Select StatusCode
# Esperado: 405 (Method Not Allowed) — a rota existe mas só aceita POST
```

---

## Plano de execução

- [x] 1. Rodar Passo 0 — verificar tokens
- [x] 2. Rodar seeds mínimas (ciclo destrutivo + 19 seeds, 220 testes)
- [ ] 3. Criar RegistrationOrder de teste (Passo 1) — não executado (Fluxo A sem aluno existente)
- [x] 4. Simular webhook Asaas PAYMENT_CONFIRMED para PreRegistration
- [x] 5. Verificar banco após cada evento
- [x] 6. Criar PreRegistration de teste e simular wizard completo (Fluxo B PIX + Stripe)
- [x] 7. Instalar Stripe CLI e testar webhooks localmente (v1.42.10)
- [ ] 8. Verificar painel Asaas HG e Stripe HG para URLs corretas
- [ ] 9. Testar fluxo completo via Chrome MCP no HG Render
- [ ] 10. Verificar banco HG após teste de ponta a ponta

---

## Evidências

### Tokens locais (verificação direta no .env — 2026-06-10)

```
ASAAS_WEBHOOK_TOKEN:   configurado    ✓   (whsec_5Wws... — webhooks Asaas HTTP 200)
ASAAS_API_KEY:         configurado    ✓   (len=166, chamadas de saída funcionam)
ASAAS_API_URL:         configurado    ✓   (sandbox api-sandbox.asaas.com/v3)
STRIPE_SECRET_KEY:     configurado    ✓   (sk_test, len=107)
STRIPE_WEBHOOK_SECRET: configurado    ✓   (whsec_74ab90bc... — Stripe CLI sessão ativa)
SITE_BASE_URL:         configurado    ✓   (https://lvjiujitsu-hg.onrender.com)
manage.py check:       0 issues       ✓
Stripe CLI:            instalada      ✓   (v1.42.10, conta lvjiujitsu acct_1TLsxdItFp0xr82s)
```

### Ciclo destrutivo e seeds

```
clear_migrations.py → makemigrations → test (220 passed) → migrate  ✓
19 seeds executadas em sequência                                       ✓
Banco limpo e pronto para testes                                       ✓
```

### Fluxo 1 — Wizard PIX Asaas (2026-06-10)

```
Usuário: Carlos Teste PIX
CPF: 529.982.247-25
Perfil: Aluno (holder)
Plano: Individual 2x por semana - Asaas PIX - Mensal (R$ 221,99)
Turma: Adulto Jiu Jitsu

Etapas concluídas:
  Step 1 (perfil)    ✓  profile-card-holder selecionado
  Step 2 (dados)     ✓  todos os campos preenchidos; sexo via nativeSetter
  Step 3 (saúde)     ✓  tipo sanguíneo O+, emergência configurada
  Step 4 (marcial)   ✓  "Não pratico artes marciais"
  Step 5 (turmas)    ✓  Adulto · Jiu Jitsu selecionada
  Step 6 (plano)     ✓  PIX Asaas selecionado; checkout_action=pix

POST /register/ → 302  (PreRegistration criado)
  PreRegistration ID=1  status=awaiting_payment
  asaas_customer: cus_000008140775  (cliente criado no Asaas sandbox)
  asaas_payment_id: pay_jabllbvma5u4izrz  (cobrança PIX criada)

Webhook PAYMENT_CONFIRMED simulado via curl:
  POST /pagamentos/webhook/asaas/ → 200  ✓
  AsaasWebhookEvent criado: id=1 type=PAYMENT_CONFIRMED

Redirect simulado: GET /pagamentos/sucesso/?id=pay_jabllbvma5u4izrz → 302
  PreRegistration ID=1: status=payment_confirmed, plan_paid=True  ✓

Materiais: pulados
Resumo: Ana Teste Stripe / plano correto exibido  ✓

POST /register/finalizar/ → 302
  Person criado: Carlos Teste PIX  is_active=True  ✓
  Membership: active  Individual 2x por semana - Asaas PIX - Mensal  ✓
  Dashboard carregado: "Cadastro finalizado com sucesso!"  ✓
  PreRegistration ID=1: status=finalized  ✓
```

### Fluxo 2 — Wizard Stripe Cartão Recorrente (2026-06-10)

```
Usuário: Ana Teste Stripe
CPF: 871.443.267-69
Perfil: Aluno (holder)
Plano: Individual 2x por semana - Stripe Cartão - Assinatura Recorrente Mensal (R$ 228,80)
Turma: Adulto Jiu Jitsu

POST /register/ → 302  (PreRegistration criado)
  PreRegistration ID=2  status=awaiting_payment
  checkout_action=stripe_card
  stripe_session_id: cs_test_a14oHBE7tIKAXetl7JwkSpjUV6BuTCeTIjKkOf1FxSDNFe6DRjq3ic5Gk6

Webhook checkout.session.completed via Stripe CLI:
  stripe trigger checkout.session.completed
    --override checkout_session:client_reference_id="pre-registration:2"
  POST /pagamentos/webhook/stripe/ → 200  ✓  (11+ eventos processados)
  PreRegistration ID=2: status=payment_confirmed, plan_paid=True  ✓
  Note: stripe trigger usa session ID fictício — substitui o stripe_session_id no snapshot

Redirect simulado com ID do fixture:
  GET /pagamentos/sucesso/?session_id=cs_test_a17z3OHVA... → 302
  Wizard: step-plan modo "Pagamento confirmado" ✓

Materiais: pulados
Resumo: Ana Teste Stripe / Stripe Recorrente / R$ 228,80  ✓

POST /register/finalizar/ → 302
  Person criado: Ana Teste Stripe  is_active=True  ✓
  Membership: active  Individual 2x por semana - Stripe Cartão - Assinatura Recorrente Mensal  ✓
  Dashboard: "Cadastro finalizado com sucesso! Seja bem-vindo."  ✓
```

### Simulações de webhook executadas

| Evento | HTTP | Resultado |
|---|---|---|
| Asaas PAYMENT_CONFIRMED (`pay_jabllbvma5u4izrz`) | 200 ✓ | AsaasWebhookEvent criado (PreRegistration — order_id=None esperado) |
| Stripe `checkout.session.completed` (`pre-registration:2`) | 200 ✓ | StripeWebhookEvent criado; PreRegistration confirmada |
| Stripe `charge.updated`, `payment_intent.created`, etc. | 200 ✓ | Eventos gravados sem efeito (order inexistente — correto) |

### Console do navegador (preview browser)

Nenhum erro JS crítico durante todo o fluxo dos dois cadastros.

### HG Render

- [ ] URL webhook Asaas configurada no painel
- [ ] URL webhook Stripe configurada no painel
- [ ] Fluxo wizard completo via Chrome MCP no HG
- [ ] Person criado no banco HG após finalização

## Implementado

Documento de validação operacional — nenhum código alterado.  
Stripe CLI instalada (v1.42.10) e `STRIPE_WEBHOOK_SECRET` configurado no `.env`.

## Desvios do plano

- `stripe trigger` com `--override checkout_session:id` não é suportado — o fixture usa session ID diferente do real. Consequência: o `stripe_session_id` no snapshot fica sobrescrito pelo ID do fixture após o webhook. O redirect de volta deve usar o ID do fixture, não o original. Em produção/HG este problema não ocorre (session ID é sempre consistente).
- `SITE_BASE_URL` aponta para HG Render: `successUrl` do Asaas aponta para o HG, não para localhost. Em testes locais o redirect é simulado manualmente via browser.

## Pendências

- [ ] Confirmar URLs de webhook nos painéis Asaas sandbox e Stripe test para o ambiente HG
- [ ] Executar roteiro de teste via Chrome MCP no HG após próximo deploy
