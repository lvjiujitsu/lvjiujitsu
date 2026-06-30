# Guia de Preenchimento e Teste de Cliente

> Roteiro operacional completo para cadastrar clientes de teste no wizard público
> usando o **preview browser interno do Claude Code** (porta 8000, sem acesso a URLs externas).
>
> Executado e validado em 2026-06-10. Atualizado em 2026-06-10.
> CPF de Ana Teste Stripe corrigido para 960.013.389-14 (matematicamente válido).
> Adicionadas seções de validação de persistência pós-pagamento e integração CSS/JS.
> Reproduzível do zero a partir de um banco limpo.

---

## Contexto e limitações do preview browser

O preview browser interno do Claude Code funciona em `http://localhost:8000`.

**Limitações conhecidas:**

| Situação | Comportamento | Solução neste guia |
|---|---|---|
| URL de gateway externo (Asaas, Stripe) | Bloqueada — o browser não redireciona para fora | Simular o redirect manualmente via `window.location.href` |
| `SITE_BASE_URL` aponta para HG Render | `successUrl` do Asaas gera link para HG, não para localhost | Simular o retorno via `/pagamentos/sucesso/?id=<pay_id>` |
| `stripe trigger` usa session ID fictício | O `stripe_session_id` no banco fica diferente do original | Ler o ID correto no banco **após** o webhook e usar no redirect |
| Selects HTML nativos | `el.value = 'x'` pode não acionar o listener JS | Usar `nativeSetter` (ver abaixo) |

**Como o servidor é iniciado:**

O arquivo `.claude/launch.json` configura o servidor Django para o preview:

```json
{
  "configurations": [{
    "name": "django",
    "runtimeExecutable": "C:/Users/whsf/Documents/GitHub/lvjiujitsu/.venv/Scripts/python.exe",
    "runtimeArgs": ["manage.py", "runserver", "localhost:8000", "--noreload"],
    "port": 8000
  }]
}
```

O preview é iniciado pelo Claude via `preview_start`. Se a porta 8000 já estiver em uso, identificar e encerrar o processo:

```powershell
# Identificar PID na porta 8000
netstat -ano | findstr :8000
# Encerrar (substituir PID)
taskkill /F /PID <PID>
```

---

## Pré-requisitos antes de executar o guia

```powershell
# 1. Verificar ambiente
.\.venv\Scripts\python.exe manage.py check
# Esperado: System check identified no issues (0 silenced).

# 2. Verificar tokens obrigatórios
.\.venv\Scripts\python.exe manage.py shell -c "
from django.conf import settings
print('ASAAS_WEBHOOK_TOKEN set:', bool(settings.ASAAS_WEBHOOK_TOKEN))
print('STRIPE_WEBHOOK_SECRET set:', bool(settings.STRIPE_WEBHOOK_SECRET))
print('ASAAS_API_URL:', settings.ASAAS_API_URL)
print('SITE_BASE_URL:', settings.SITE_BASE_URL)
"
# Esperado:
# ASAAS_WEBHOOK_TOKEN set: True
# STRIPE_WEBHOOK_SECRET set: True
# ASAAS_API_URL: https://api-sandbox.asaas.com/v3
# SITE_BASE_URL: https://lvjiujitsu-hg.onrender.com
```

> **Se `STRIPE_WEBHOOK_SECRET` estiver vazio:**
> Iniciar o Stripe CLI listener em um terminal separado:
> ```
> stripe listen --forward-to http://localhost:8000/pagamentos/webhook/stripe/
> ```
> Copiar o `whsec_...` exibido e adicionar ao `.env`:
> ```
> STRIPE_WEBHOOK_SECRET=whsec_...
> ```
> Reiniciar o servidor Django para carregar o novo valor.

```powershell
# 3. Verificar que as rotas de webhook existem (esperado: 405, não 404)
curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/pagamentos/webhook/asaas/
# Esperado: 405

curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/pagamentos/webhook/stripe/
# Esperado: 405
```

---

## Utilitário JavaScript reutilizável

Todos os steps abaixo usam estas duas funções. Executar em `preview_eval` antes de começar ou incluir no início de cada bloco:

```javascript
// Define valor em input e dispara eventos (para que o JS do wizard detecte)
function setVal(id, val) {
  var el = document.getElementById(id);
  if (!el) return null;
  el.value = val;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  return el.value;
}

// Define valor em <select> contornando listeners customizados
function setSelect(id, val) {
  var el = document.getElementById(id);
  if (!el) return null;
  var setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
  setter.call(el, val);
  el.dispatchEvent(new Event('change', {bubbles: true}));
  return el.value;
}

// Verifica step atual visível
function currentStep() {
  var el = document.querySelector('[data-step]:not([hidden])');
  return el ? el.getAttribute('data-step') : 'none';
}
```

---

## Fluxo 1 — Aluno titular com PIX Asaas

### Dados do usuário de teste

| Campo | Valor |
|---|---|
| Nome | Carlos Teste PIX |
| CPF | 529.982.247-25 |
| Nascimento | 15/03/1990 |
| Sexo | Masculino (`male`) |
| Telefone | (11) 91234-5678 |
| Email | carlos.pix@teste.com |
| Senha | Senha@123 |
| CEP | 01310-100 |
| Cidade | São Paulo |
| Logradouro | Avenida Paulista |
| Número | 1000 |
| Complemento | Apto 10 |
| Bairro | Bela Vista |
| Plano | Individual 2x/semana · PIX · Mensal |
| Emergência | Maria Teste (11) 99999-0001 |
| Tipo sanguíneo | O+ |

### Step 1 — Perfil

**Objetivo:** selecionar "Aluno" e avançar.

**Elemento chave:** `#profile-card-holder` (não `.martial-has-btn` — esse é outro componente)

```javascript
// Clicar no card "Aluno"
document.getElementById('profile-card-holder').click();

// Verificar seleção
// Esperado: aria-pressed="true"
document.getElementById('profile-card-holder').getAttribute('aria-pressed');

// Avançar
document.getElementById('step-1-next').click();
```

**Comportamento esperado:**
- `id_registration_profile` (hidden input) passa a ter valor `holder`
- Página avança para step 2 (dados pessoais)
- Verificar: `currentStep()` retorna `"2"`

---

### Step 2 — Dados pessoais

```javascript
setVal('ui-s2-name',                 'Carlos Teste PIX');
setVal('ui-s2-cpf',                  '529.982.247-25');
setVal('ui-s2-birthdate',            '15/03/1990');
setSelect('ui-s2-sex',               'male');          // opções: male / female
setVal('ui-s2-phone',                '(11) 91234-5678');
setVal('ui-s2-email',                'carlos.pix@teste.com');
setVal('ui-s2-password',             'Senha@123');
setVal('ui-s2-password-confirm',     'Senha@123');
setVal('ui-s2-postal-code',          '01310-100');
setVal('ui-s2-city',                 'São Paulo');
setVal('ui-s2-address',              'Avenida Paulista');
setVal('ui-s2-address-number',       '1000');
setVal('ui-s2-address-complement',   'Apto 10');
setVal('ui-s2-address-neighborhood', 'Bela Vista');

document.getElementById('step-2-next').click();
```

> **Atenção com o campo sexo:** `setVal` não funciona para `<select>` — usar `setSelect` com `'male'` ou `'female'` (não `'M'` ou `'F'`).

**Comportamento esperado:**
- Sem erros visíveis (verificar: `[id$="-error"]:not([hidden])`)
- Avança para step `health`
- Se o CPF já existir no banco: alerta "CPF já cadastrado" e o step não avança

**Verificar ausência de erros:**
```javascript
[...document.querySelectorAll('[id$="-error"]:not([hidden])')].map(e => e.textContent).filter(Boolean)
// Esperado: []
```

---

### Step 3 — Saúde

```javascript
setSelect('ui-health-blood-type', 'O+');  // opções: A+, A-, B+, B-, O+, O-, AB+, AB-
setVal('ui-health-emergency', 'Maria Teste (11) 99999-0001');
// Alergias e lesões são opcionais

document.getElementById('step-health-next').click();
```

**Comportamento esperado:** avança para step `martial`

---

### Step 4 — Experiência marcial

```javascript
// "Não pratico" já é o padrão (martial-has-btn--active no botão "Não")
// Clicar no botão "Não" garante o estado correto
document.getElementById('martial-toggle-no').click();

document.getElementById('step-martial-next').click();
```

**Comportamento esperado:** avança para step `classes`

---

### Step 5 — Turmas

```javascript
// Selecionar o primeiro card disponível
document.querySelector('.class-card').click();

// Verificar seleção
document.querySelector('.class-card').getAttribute('aria-pressed');
// Esperado: "true"

document.getElementById('step-classes-next').click();
```

**Comportamento esperado:** avança para step `plan`

> O catálogo de turmas é populado pelas seeds `seed_system_initial_class_catalog` e
> `seed_system_initial_class_catalog_administrative`. Se estiver vazio, verificar se as seeds foram executadas.

---

### Step 6 — Plano (PIX)

```javascript
// PIX já é o método ativo por padrão
// Verificar filtro ativo
[...document.querySelectorAll('[data-filter="method"]')]
  .filter(b => b.classList.contains('plan-filter-pill--active'))
  .map(b => b.textContent.trim());
// Esperado: ["PIX"]

// Selecionar o primeiro plano disponível (Individual 2x/semana Mensal)
document.querySelector('.plan-card').click();

// Verificar estado dos hidden inputs
({
  checkoutAction: document.getElementById('id_checkout_action').value,   // "pix"
  selectedPlan:   document.getElementById('id_selected_plan').value      // "4" (ou ID do plano)
})

// Avançar
document.getElementById('step-plan-next').click();
// O botão exibe "Pagar mensalidade"
```

**Comportamento esperado:**
- `POST /register/ → 302` aparece nos logs do servidor
- O preview browser fica parado (redirecionamento para Asaas bloqueado)
- `PreRegistration` criado no banco com status `awaiting_payment`

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.order_by('-created_at').first()
snap = pr.form_snapshot or {}
pp  = snap.get('plan_payment', {})
print('ID:', pr.pk)
print('Status:', pr.status)
print('asaas_payment_id:', pp.get('asaas_payment_id'))
print('asaas_customer:', snap.get('asaas_customer'))
"
```

**Saída esperada:**
```
ID: 1
Status: awaiting_payment
asaas_payment_id: pay_<id_gerado_pelo_asaas>
asaas_customer: {'id': 'cus_<id>'}
```

---

### Simular retorno do Asaas (successUrl local)

O Asaas redireciona o browser para `SITE_BASE_URL + /pagamentos/sucesso/?id=<pay_id>`.
Como `SITE_BASE_URL` aponta para HG Render, o redirect real não chega ao localhost.
Simular manualmente navegando para a URL local com o `asaas_payment_id` obtido acima:

```javascript
// Substituir <pay_id> pelo valor de asaas_payment_id do banco
window.location.href = '/pagamentos/sucesso/?id=<pay_id>';
```

**Comportamento esperado no browser:**
- Redireciona para `/register/`
- Aparece o alerta verde **"Pagamento confirmado!"**
- O wizard avança para o modo pós-pagamento:
  - Barra de progresso mostra Etapa 6 de 8
  - Step-plan exibe banner **"Pagamento confirmado"** com o nome e valor do plano
  - Botão "Continuar para materiais" visível
  - Filtros e cards de plano ocultados

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.order_by('-created_at').first()
snap = pr.form_snapshot or {}
print('Status:', pr.status)            # payment_confirmed
print('plan_paid:', snap.get('plan_paid'))  # True
"
```

> **Alternativa via webhook Asaas (Fluxo A — RegistrationOrder):**
> O webhook Asaas **não confirma** o wizard (Fluxo B). Ele serve para alunos já cadastrados
> com `RegistrationOrder`. Para o wizard, apenas o redirect via `successUrl` confirma o pagamento.

---

### Step 7 — Materiais

```javascript
// Continuar para materiais
document.getElementById('step-plan-next').click();

// A página mostra os produtos disponíveis (Faixa LV, Kimono Adulto, Kimono Infantil, Rash Guard, Patches)
// Pular materiais para ir direto ao resumo
[...document.querySelectorAll('button')]
  .find(b => b.textContent.includes('Pular'))
  .click();
```

**Comportamento esperado:**
- Avança para Etapa 8 de 8
- Heading: "Confirmar cadastro"

---

### Step 8 — Resumo e finalização

**Verificar o resumo antes de finalizar:**

O step de revisão deve exibir:
- Seção **ALUNO** com nome e email
- Seção **PLANO CONTRATADO** com nome do plano e total
- Seção **MATERIAIS** com "Nenhum material selecionado" (se pulado)
- Botão **"Finalizar cadastro e acessar o sistema"**

```javascript
// Finalizar
[...document.querySelectorAll('button')]
  .find(b => b.textContent.includes('Finalizar'))
  .click();
```

**Comportamento esperado:**
- `POST /register/finalizar/ → 302` nos logs
- Redirect para `/home/`
- Dashboard carregado com:
  - Mensagem: **"Cadastro finalizado com sucesso! Seja bem-vindo."**
  - Heading: "Olá, Carlos …"
  - Seção MENSALIDADE: status **ATIVO** com nome do plano
  - Turmas do dia listadas

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import Person, PreRegistration
from system.models.membership import Membership

p  = Person.objects.filter(email='carlos.pix@teste.com').first()
pr = PreRegistration.objects.filter(form_snapshot__holder_email='carlos.pix@teste.com').first()
m  = Membership.objects.filter(person=p).first() if p else None

print('Person:', p.full_name if p else 'NÃO ENCONTRADO')
print('is_active:', p.is_active if p else '-')
print('PreRegistration status:', pr.status if pr else 'NÃO ENCONTRADO')
print('Membership status:', m.status if m else 'NÃO ENCONTRADO')
"
```

**Saída esperada:**
```
Person: Carlos Teste PIX
is_active: True
PreRegistration status: finalized
Membership status: active
```

---

## Fluxo 2 — Aluno titular com Stripe Cartão Recorrente

### Dados do usuário de teste

| Campo | Valor |
|---|---|
| Nome | Ana Teste Stripe |
| CPF | 960.013.389-14 |
| Nascimento | 22/07/1992 |
| Sexo | Feminino (`female`) |
| Telefone | (11) 97654-3210 |
| Email | ana.stripe@teste.com |
| Senha | Senha@123 |
| CEP | 04538-133 |
| Cidade | São Paulo |
| Logradouro | Rua Funchal |
| Número | 418 |
| Complemento | Sala 5 |
| Bairro | Vila Olímpia |
| Plano | Individual Recorrente 2x/semana · Stripe · Mensal |
| Emergência | João (11) 98888-0002 |
| Tipo sanguíneo | A+ |

### Steps 1 a 5 — idênticos ao Fluxo 1

Repetir a mesma sequência com os dados desta tabela. Trocar o email para `ana.stripe@teste.com`
e CPF para `960.013.389-14` nos campos do Step 2.

Fazer logout antes de iniciar: navegar para `/logout/` e depois para `/register/`.

---

### Step 6 — Plano (Stripe Recorrente)

```javascript
// 1. Clicar no filtro "Cartão"
[...document.querySelectorAll('[data-filter="method"]')]
  .find(b => b.getAttribute('data-value') === 'credit_card')
  .click();

// 2. Aguardar re-render dos cards (~200ms)

// 3. Verificar planos disponíveis
[...document.querySelectorAll('.plan-card')]
  .map(c => ({id: c.getAttribute('data-plan-id'), txt: c.textContent.trim().slice(0,80)}))
// Dois planos aparecem:
//   ID ~8:  "Individual R$ 212,63/Mensal 2x por semana"    → Asaas Cartão
//   ID ~52: "IndividualRecorrente R$ 212,63/mês 2x por semana" → Stripe

// 4. Selecionar o plano Stripe (tem "Recorrente" no texto)
document.querySelector('.plan-card[data-plan-id="52"]').click();
// Se o ID for diferente, buscar por conteúdo:
// [...document.querySelectorAll('.plan-card')].find(c => c.textContent.includes('Recorrente')).click()

// 5. Verificar que checkout_action mudou para stripe_card
document.getElementById('id_checkout_action').value;
// Esperado: "stripe_card"

// 6. Avançar
document.getElementById('step-plan-next').click();
```

**Comportamento esperado:**
- `POST /register/ → 302` nos logs
- `PreRegistration` criado com `checkout_action=stripe_card` e `stripe_session_id` no snapshot

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.order_by('-created_at').first()
snap = pr.form_snapshot or {}
pp  = snap.get('plan_payment', {})
print('ID:', pr.pk)
print('Status:', pr.status)
print('checkout_action:', snap.get('checkout_action'))
print('stripe_session_id:', pp.get('stripe_session_id'))
"
```

**Saída esperada:**
```
ID: 2
Status: awaiting_payment
checkout_action: stripe_card
stripe_session_id: cs_test_<id_original>
```

---

### Simular webhook Stripe `checkout.session.completed`

O Stripe CLI precisa estar em execução com `stripe listen` apontando para `localhost:8000`.

```powershell
# Executar em terminal separado (se ainda não estiver rodando):
stripe listen --forward-to http://localhost:8000/pagamentos/webhook/stripe/

# Em outro terminal, disparar o evento:
stripe trigger checkout.session.completed `
  --override checkout_session:client_reference_id="pre-registration:<PR_PK>"
# Substituir <PR_PK> pelo pk do PreRegistration obtido no passo anterior (ex: 2)
```

**Comportamento esperado:**
- Terminal do `stripe listen`: `[200] POST http://localhost:8000/pagamentos/webhook/stripe/`
- `StripeWebhookEvent` criado no banco
- `PreRegistration.status` muda para `payment_confirmed`
- `form_snapshot["plan_paid"]` muda para `True`
- **Atenção:** o `stripe trigger` usa um session ID de fixture diferente do original.
  O webhook sobrescreve o `stripe_session_id` no snapshot com o ID fictício do fixture.

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
from system.models.registration_order import StripeWebhookEvent
pr = PreRegistration.objects.order_by('-created_at').first()
snap = pr.form_snapshot or {}
pp  = snap.get('plan_payment', {})
print('Status:', pr.status)                          # payment_confirmed
print('plan_paid:', snap.get('plan_paid'))            # True
print('stripe_session_id atual:', pp.get('stripe_session_id'))  # ID do fixture

print()
print('Último StripeWebhookEvent:')
ev = StripeWebhookEvent.objects.order_by('-created_at').first()
print('  type:', ev.event_type)
print('  event_id:', ev.event_id[:40])
"
```

---

### Simular retorno do Stripe (successUrl local)

Usar o `stripe_session_id` **atual** (após o webhook — ID do fixture, não o original):

```javascript
// Substituir <stripe_session_id_atual> pelo valor obtido no banco acima
window.location.href = '/pagamentos/sucesso/?session_id=<stripe_session_id_atual>';
```

**Comportamento esperado no browser:**
- Redireciona para `/register/`
- Aparece o alerta verde **"Pagamento confirmado!"**
- Step-plan em modo pós-pagamento com:
  - Banner **"Pagamento confirmado"**
  - Plano: "Individual 2x por semana - Stripe Cartão - Assinatura Recorrente Mensal"
  - Total: R$ 228,80
  - Botão **"Continuar para materiais"**

> **Por que usar o ID do fixture:**
> O `stripe trigger` gera um evento com `checkout.session.id` próprio (diferente do
> `stripe_session_id` original criado pelo backend). O webhook handler atualiza o snapshot
> com esse novo ID. A view `PaymentSuccessView` busca o PreRegistration pelo `stripe_session_id`
> do snapshot — portanto usa-se o ID atual (pós-webhook).
>
> Em produção/HG este problema não ocorre: o Stripe envia o evento com o ID real da sessão,
> que é o mesmo gravado pelo backend.

---

### Steps 7 e 8 — Materiais e Finalização

Idênticos ao Fluxo 1. Pular materiais e clicar em "Finalizar cadastro e acessar o sistema".

**Comportamento esperado no dashboard:**
- Mensagem: **"Cadastro finalizado com sucesso! Seja bem-vindo."**
- Heading: "Olá, Ana …"
- MENSALIDADE status **ATIVO** — "Individual 2x por semana - Stripe Cartão - Assinatura Recorrente Mensal"

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import Person, PreRegistration
from system.models.membership import Membership

p  = Person.objects.filter(email='ana.stripe@teste.com').first()
pr = PreRegistration.objects.filter(form_snapshot__holder_email='ana.stripe@teste.com').first()
m  = Membership.objects.filter(person=p).first() if p else None

print('Person:', p.full_name if p else 'NÃO ENCONTRADO')
print('is_active:', p.is_active if p else '-')
print('PreRegistration status:', pr.status if pr else 'NÃO ENCONTRADO')
print('Membership status:', m.status if m else 'NÃO ENCONTRADO')
"
```

**Saída esperada:**
```
Person: Ana Teste Stripe
is_active: True
PreRegistration status: finalized
Membership status: active
```

---

## Verificação consolidada do banco após ambos os fluxos

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, Person
from system.models.membership import Membership, MembershipStatus
from system.models.asaas import AsaasWebhookEvent
from system.models.registration_order import StripeWebhookEvent

print('=== PESSOAS CADASTRADAS ===')
for p in Person.objects.order_by('created_at'):
    m = Membership.objects.filter(person=p).order_by('-created_at').first()
    m_status = m.status if m else 'sem membership'
    print(f'  {p.full_name} | active={p.is_active} | membership={m_status}')

print()
print('=== PREREGISTRATIONS ===')
for pr in PreRegistration.objects.order_by('created_at'):
    snap = pr.form_snapshot or {}
    print(f'  pk={pr.pk} | status={pr.status} | plan_paid={snap.get(\"plan_paid\")} | action={snap.get(\"checkout_action\")}')

print()
print('=== ASAAS WEBHOOK EVENTS ===')
for ev in AsaasWebhookEvent.objects.order_by('created_at'):
    print(f'  {ev.event_type} | order_id={ev.order_id} | event_id={ev.event_id[:25]}...')

print()
print('=== STRIPE WEBHOOK EVENTS (últimos 5) ===')
for ev in StripeWebhookEvent.objects.order_by('-created_at')[:5]:
    print(f'  {ev.event_type} | order_id={ev.order_id} | membership_id={ev.membership_id}')
"
```

**Saída esperada após ambos os fluxos:**
```
=== PESSOAS CADASTRADAS ===
  Carlos Teste PIX | active=True | membership=active
  Ana Teste Stripe | active=True | membership=active

=== PREREGISTRATIONS ===
  pk=1 | status=finalized | plan_paid=True | action=pix
  pk=2 | status=finalized | plan_paid=True | action=stripe_card

=== ASAAS WEBHOOK EVENTS ===
  PAYMENT_CONFIRMED | order_id=None | event_id=evt_pix_test_001...

=== STRIPE WEBHOOK EVENTS (últimos 5) ===
  checkout.session.completed | order_id=None | membership_id=None
  charge.updated | ...
  ...
```

> `order_id=None` é esperado para eventos de webhook que chegaram para PreRegistrations
> (Fluxo B) — o código não tenta associar a um `RegistrationOrder` inexistente.

---

## Validação de persistência de dados pós-pagamento

Após o redirect de `/pagamentos/sucesso/?id=<pay_id>` (ou `?session_id=<...>`), o wizard deve
voltar ao step-plan **com todos os dados das etapas anteriores intactos**.
Esta seção verifica que o `sessionStorage` e o DOM refletem corretamente o estado preenchido.

### 1. Verificar que a sessão JavaScript está completa

```javascript
// Ler o estado completo do wizard no sessionStorage
var state = JSON.parse(sessionStorage.getItem('lv-wiz-v1') || '{}');

// Verificar campos obrigatórios presentes
({
  profile:         state.profile,                          // "holder"
  name:            state.fields?.holder_name,              // "Carlos Teste PIX" ou "Ana Teste Stripe"
  cpf:             state.fields?.holder_cpf,               // CPF preenchido
  email:           state.fields?.holder_email,             // email preenchido
  classSelections: state.classSelections?.length,          // ≥ 1
  planSelections:  state.planSelections?.length,           // ≥ 1
  planPaid:        state.planPaid,                         // true
})
```

**Saída esperada (Fluxo 1 — PIX):**
```json
{
  "profile": "holder",
  "name": "Carlos Teste PIX",
  "cpf": "529.982.247-25",
  "email": "carlos.pix@teste.com",
  "classSelections": 1,
  "planSelections": 1,
  "planPaid": true
}
```

> Se `planPaid` for `false` ou `undefined`, o wizard voltou ao estado inicial — o redirect
> não carregou corretamente ou a sessão Django `post_plan_payment_complete` não está setada.

### 2. Verificar que os steps 1–5 estão marcados como concluídos na barra de progresso

```javascript
// Verificar ícones/classes de steps concluídos
[...document.querySelectorAll('[data-step-indicator]')]
  .map(el => ({
    step: el.getAttribute('data-step-indicator'),
    done: el.classList.contains('step-done') || el.querySelector('.step-check') !== null
  }))
```

**Esperado:** steps 1, 2, 3, 4, 5 com `done: true`; step 6 (plan) ativo ou também marcado.

> Se nenhum step estiver marcado como concluído, a barra de progresso não está recebendo
> o estado do sessionStorage. Verificar se o JS `register.js` chamou `updateProgressBar()` após
> restaurar o estado.

### 3. Verificar que o banner de pagamento confirmado está visível no step-plan

```javascript
// Deve estar visível: o bloco de "Pagamento confirmado"
var banner = document.querySelector('[data-post-payment-section]') ||
             document.querySelector('[id*="post-plan"]');
banner ? banner.hidden : 'elemento não encontrado';
// Esperado: false (não está oculto)
```

```javascript
// Deve estar oculto: o grid de filtros e cards de plano
var grid = document.querySelector('[data-plan-selection-grid]') ||
           document.querySelector('.plan-filters-row');
grid ? grid.hidden : 'elemento não encontrado';
// Esperado: true (está oculto)
```

### 4. Verificar que os dados do step 2 são re-preenchíveis

O wizard deve restaurar os valores do sessionStorage nos campos hidden do formulário:

```javascript
// Os campos hidden que o servidor processa são preenchidos pelo JS antes do submit
({
  holder_name: document.getElementById('id_holder_name')?.value  ||
               document.querySelector('[name="holder_name"]')?.value,
  holder_cpf:  document.querySelector('[name="holder_cpf"]')?.value,
  holder_email:document.querySelector('[name="holder_email"]')?.value,
})
```

**Esperado:** todos os valores correspondentes ao que foi preenchido no step 2.

---

## Validação de integração CSS/JS

Esta seção verifica que nenhum erro de console bloqueia o fluxo e que os estilos estão
carregando corretamente em cada transição de step.

### Verificar console em cada transição de step

Após cada `click()` de avançar, inspecionar o console antes de continuar:

```javascript
// Executar após cada transição
(function checkConsole() {
  // Esta função não captura erros passados — usar preview_console_logs no fluxo
  // Para verificar ausência de erros no DOM:
  return document.querySelectorAll('[id$="-error"]:not([hidden])').length === 0
    ? 'OK — sem erros visíveis'
    : [...document.querySelectorAll('[id$="-error"]:not([hidden])')].map(e => e.textContent);
})()
```

**Checklist de integração CSS/JS por step:**

| Step | O que verificar | Sinal de erro |
|---|---|---|
| 1 → 2 | Card selecionado muda para `aria-pressed="true"` + borda ativa | Card sem borda colorida |
| 2 → 3 | Sem erros `[id$="-error"]` visíveis; CPF formatado como `000.000.000-00` | Erro "CPF inválido" ou campo em vermelho |
| 3 → 4 | Step health sem erros | — |
| 4 → 5 | — | — |
| 5 → 6 | Card de turma com `aria-pressed="true"` | Card não muda de estado |
| step-plan carregado | Filtros PIX/Cartão responsivos; cards com preço correto | Cards sem preço ou filtro sem resposta |
| Pós-payment redirect | Banner confirmado visível; filtros ocultos | Filtros ainda visíveis |
| 6 → 7 | Step materials carregado com lista de produtos | Página em branco |
| Pular materiais | Avança para step 8 com resumo | Fica no step 7 |
| Finalizar | POST + redirect para `/home/` com mensagem de sucesso | 500 ou loop de login |

### Verificar ausência de erros de console críticos

Usar `preview_console_logs` ou o seguinte snippet **a cada step** para detectar erros JS:

```javascript
// Verificar se há erros de importação de módulo ou sintaxe fatal
// (erros desse tipo travam o wizard inteiro)
typeof initWizard === 'function' ? 'OK — wizard carregado' : 'ERRO — wizard não inicializado';
```

```javascript
// Verificar que o sessionStorage está sendo escrito corretamente
(function() {
  var key = 'lv-wiz-v1';
  var state = JSON.parse(sessionStorage.getItem(key) || '{}');
  return {
    exists: Object.keys(state).length > 0,
    keys: Object.keys(state)
  };
})()
```

**Saída esperada (após step 2):**
```json
{ "exists": true, "keys": ["profile", "fields", "classSelections", "planSelections", "planPaid"] }
```

### Verificar que o CSS de estilos versionado está carregando

```javascript
// Verificar que o CSS do wizard está no DOM (confirma que o cache-busting está correto)
[...document.querySelectorAll('link[rel="stylesheet"]')]
  .filter(l => l.href.includes('register'))
  .map(l => l.href);
// Esperado: array com ao menos um href contendo "register" e "?v="
```

---

## Erros comuns e soluções

### O wizard não avança ao clicar "Próximo"

**Causa:** campo obrigatório sem valor ou select sem seleção.

```javascript
// Inspecionar erros visíveis
[...document.querySelectorAll('[id$="-error"]:not([hidden])')].map(e => ({id: e.id, msg: e.textContent}))
```

Erro mais comum: campo `ui-s2-sex` com valor vazio. Solução: usar `setSelect` com `'male'` ou `'female'`.

### "CPF já cadastrado" ao tentar avançar no Step 2

O CPF de teste já existe no banco da sessão atual. Usar outro CPF de teste válido ou limpar o banco:

```powershell
# Apenas se o banco for local/descartável:
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import Person, PreRegistration
from system.models.membership import Membership
Person.objects.filter(email__in=['carlos.pix@teste.com','ana.stripe@teste.com']).delete()
PreRegistration.objects.all().delete()
print('Dados de teste removidos.')
"
```

### O redirect para `/pagamentos/sucesso/` vai para a tela de login

Ocorre quando o `id` ou `session_id` na URL não corresponde a nenhum PreRegistration no banco.
Verificar o valor correto:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.order_by('-created_at').first()
snap = pr.form_snapshot or {}
pp  = snap.get('plan_payment', {})
print('asaas_payment_id:', pp.get('asaas_payment_id'))
print('stripe_session_id:', pp.get('stripe_session_id'))
"
```

Usar o valor exato retornado na URL de simulação.

### Stripe `stripe trigger` falha com "unknown parameter"

```
"message": "Received unknown parameter: id"
```

O override `--override checkout_session:id` não é suportado. Usar apenas:

```powershell
stripe trigger checkout.session.completed `
  --override checkout_session:client_reference_id="pre-registration:<PR_PK>"
```

### O Step 6 exibe os filtros em vez do banner "Pagamento confirmado"

O wizard não detectou `regPostPlan=true`. Verificar se o servidor injetou o JSON correto:

```javascript
document.getElementById('reg-post-plan-json').textContent
// Esperado: "true"
```

Se for `"false"`, a sessão Django não tem `post_plan_payment_complete=True`.
Refazer o redirect para `/pagamentos/sucesso/?id=<pay_id>`.

---

## Referências rápidas — IDs e seletores do wizard

| Elemento | ID / Seletor | Step |
|---|---|---|
| Card "Aluno" | `#profile-card-holder` | 1 |
| Card "Responsável" | `#profile-card-guardian` | 1 |
| Botão Próximo step 1 | `#step-1-next` | 1 |
| Campo nome | `#ui-s2-name` | 2 |
| Campo CPF | `#ui-s2-cpf` | 2 |
| Campo data de nascimento | `#ui-s2-birthdate` | 2 |
| Select sexo | `#ui-s2-sex` (valores: `male`, `female`) | 2 |
| Campo telefone | `#ui-s2-phone` | 2 |
| Campo email | `#ui-s2-email` | 2 |
| Campo senha | `#ui-s2-password` | 2 |
| Campo confirmar senha | `#ui-s2-password-confirm` | 2 |
| Campo CEP | `#ui-s2-postal-code` | 2 |
| Campo cidade | `#ui-s2-city` | 2 |
| Campo logradouro | `#ui-s2-address` | 2 |
| Campo número | `#ui-s2-address-number` | 2 |
| Campo complemento | `#ui-s2-address-complement` | 2 |
| Campo bairro | `#ui-s2-address-neighborhood` | 2 |
| Botão Próximo step 2 | `#step-2-next` | 2 |
| Select tipo sanguíneo | `#ui-health-blood-type` | 3 |
| Campo contato emergência | `#ui-health-emergency` | 3 |
| Botão Próximo saúde | `#step-health-next` | 3 |
| Botão "Não pratico" marcial | `#martial-toggle-no` | 4 |
| Botão Próximo marcial | `#step-martial-next` | 4 |
| Card de turma | `.class-card` | 5 |
| Botão Próximo turmas | `#step-classes-next` | 5 |
| Filtro método PIX | `[data-filter="method"][data-value="pix"]` | 6 |
| Filtro método Cartão | `[data-filter="method"][data-value="credit_card"]` | 6 |
| Card de plano | `.plan-card[data-plan-id="<ID>"]` | 6 |
| Hidden checkout_action | `#id_checkout_action` | 6 |
| Hidden selected_plan | `#id_selected_plan` | 6 |
| Botão Pagar mensalidade | `#step-plan-next` | 6 |
| JSON pós-pagamento plano | `#reg-post-plan-json` | 6 |
| Botão Continuar materiais | `#step-plan-next` (após paid mode) | 6→7 |
| Botão Pular materiais | `button` com texto "Pular" | 7 |
| Botão Finalizar cadastro | `button` com texto "Finalizar" | 8 |
