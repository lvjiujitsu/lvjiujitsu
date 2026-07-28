# Guia de Preenchimento e Teste de Cliente

> **Nota de portabilidade:** use o navegador interno e o adaptador de execução descritos
> em `docs/PLATFORM-ADAPTERS.md`. Use as capacidades equivalentes da ferramenta
> atual para execução, navegação e leitura do console.
>
> Roteiro operacional completo para cadastrar clientes de teste no wizard público
> usando o servidor local na porta 8000 e, quando necessário, um túnel HTTPS.
>
> Executado e validado em 2026-06-10. Atualizado em 2026-07-03.
> CPF de Ana Teste Stripe corrigido para 960.013.389-14 (matematicamente válido).
> Adicionadas seções de validação de persistência pós-pagamento e integração CSS/JS.
> Adicionada estratégia dual de teste de pagamento (Stripe simulado por hook local ×
> Asaas via navegador real com confirmação do usuário) — ver "Estratégia de teste por gateway".
> Reproduzível do zero a partir de um banco limpo.
>
> **Atualizado em 2026-07-06**: validado com sucesso o fluxo Asaas real (PIX) ponta a
> ponta **sem nenhum navegador** (nem interno, nem externo) — via túnel HTTPS (ngrok)
> + endpoint oficial de simulação do sandbox Asaas + chamadas HTTP diretas (`curl`).
> Esse é agora o método **preferencial** para validar Asaas: mais rápido, 100%
> scriptável, sem intervenção manual. Ver "Fluxo Asaas 100% via API (sem navegador)"
> logo abaixo da tabela de estratégia por gateway. O navegador (interno) continua
> útil só para uma conferência visual final, com um cliente novo — ver essa seção.
>
> **Atualizado em 2026-07-13**: o navegador interno do Codex percorreu checkout
> hospedado Stripe e retorno via ngrok. O sandbox Asaas recusou callback para domínio
> diferente do cadastrado na conta; alinhar `SITE_BASE_URL`, domínio do túnel e domínio
> cadastrado antes do teste. Nunca registrar em documentação o `whsec_...` emitido pelo
> Stripe CLI; um valor anteriormente exposto neste arquivo deve ser rotacionado.

---

## Contexto e limitações do navegador interno

A capacidade de navegar para checkout externo depende do adaptador. O navegador
interno do Codex atualmente suporta o fluxo pelo domínio público do ngrok e o checkout
hospedado Stripe; não assuma que outros adaptadores têm o mesmo comportamento. Sempre
confirme a URL final, o retorno ao LV e o estado do gateway antes de declarar sucesso.

**Limitações conhecidas:**

| Situação | Comportamento | Solução neste guia |
|---|---|---|
| URL de gateway externo (Asaas, Stripe) | Depende do adaptador e da política de navegação | Preferir o navegador interno atual; usar API/CLI somente como fallback documentado |
| `SITE_BASE_URL` não coincide com o domínio cadastrado no Asaas | O Asaas rejeita ou retorna para o ambiente errado | Alinhar `SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`, túnel e cadastro da conta sandbox antes do checkout |
| `stripe trigger` usa session ID fictício | O `stripe_session_id` no banco fica diferente do original | Ler o ID correto no banco **após** o webhook e usar no redirect |
| Selects HTML nativos | `el.value = 'x'` pode não acionar o listener JS | Usar `nativeSetter` (ver abaixo) |

### Estratégia de teste por gateway

O wizard confirma o pagamento do pré-cadastro (Fluxo B) de duas formas distintas
conforme o gateway, e isso define a estratégia de teste de cada um:

| Gateway | Como o wizard confirma o pagamento | Estratégia de teste |
|---|---|---|
| **Stripe** | Webhook `checkout.session.completed` grava `plan_paid=True` no `PreRegistration` (ver `system/services/stripe_webhooks.py`) | Preferir checkout hospedado com cartão de teste e retorno pelo túnel. `stripe trigger` é fallback para validar o handler isoladamente e não substitui a homologação visual do checkout. |
| **Asaas** | O wizard confirma via redirect `successUrl` (`/pagamentos/sucesso/`) — mas esse endpoint é um `GET` normal, chamável diretamente por HTTP sem navegador nenhum | **100% via API/`curl`, sem navegador nenhum** (interno ou externo) desde que exista um túnel HTTPS válido registrado na conta sandbox Asaas. Ver "Fluxo Asaas 100% via API (sem navegador)" abaixo — é o método **preferencial** a partir de 2026-07-06. O fluxo com navegador continua válido como alternativa/verificação visual manual. |

**Por que a diferença:** o Stripe CLI simula eventos para testar o webhook isoladamente.
O sandbox Asaas oferece um endpoint específico de confirmação de pagamento, mas o LV
ainda precisa receber o retorno da `successUrl` para concluir o estado do wizard. A
homologação completa combina estado confirmado no gateway, retorno ao LV e conferência
no ORM.

**Como o servidor é iniciado:**

Use o adaptador da ferramenta ou o comando canônico abaixo:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

Se a porta 8000 já estiver em uso, identifique o processo antes de decidir reiniciá-lo:

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

## Atualizar o domínio do túnel no painel Asaas sandbox

A Asaas rejeita a criação de cobrança (`POST /payments`) com
`{"code": "invalid_object", "description": "É necessário enviar uma URL que
use o mesmo domínio cadastrado nas suas Minha Conta na aba Informações."}`
sempre que o domínio do túnel ngrok ativo não bater com o campo **Site**
cadastrado na conta sandbox. Como o ngrok free gera um domínio novo a cada
reinício, esse campo precisa ser atualizado manualmente sempre que o túnel
mudar.

**Isso é uma ação manual do responsável pela conta Asaas — nenhum agente
(Claude, Codex, Cursor) deve tentar logar no painel Asaas, ainda que
credenciais sejam fornecidas no chat.** Login em painéis de terceiros com
usuário/senha está fora do que qualquer agente executa neste projeto,
independente de autorização explícita — é bloqueado na própria ferramenta,
não uma preferência de governança que se possa flexibilizar. As credenciais
da conta Asaas nunca devem ser gravadas em `.env`, `.env.hg` ou `.env.prod`.

Passo a passo (feito pelo humano responsável pela conta):

1. Confirmar o domínio do túnel ativo:
   ```powershell
   curl -s http://127.0.0.1:4040/api/tunnels
   # Ler o valor de "public_url" (ex.: https://xxxxx.ngrok-free.dev)
   ```
2. Logar em `https://sandbox.asaas.com/login/auth` com a conta sandbox do
   projeto.
3. Ir em **Minha Conta → Informações → Site** (`https://sandbox.asaas.com/config/index`).
4. Substituir o valor do campo **Site** pelo domínio do túnel ativo (esse
   campo aceita só um valor — anotar o valor anterior para reverter depois
   do teste, se necessário).
5. Salvar.
6. Confirmar no `.env` local que `SITE_BASE_URL` e `DJANGO_ALLOWED_HOSTS`
   já apontam para o mesmo domínio do túnel (o agente pode ajustar isso,
   é configuração local, não credencial de terceiro).
7. Repetir o fluxo de cadastro/pagamento Asaas normalmente.
8. Ao terminar os testes, reverter o campo **Site** para o domínio de
   produção/HG, se esse for o padrão da conta.

Ver também: `reference_asaas_sandbox_real_validation` na memória do agente
(passo a passo do túnel + endpoint de simulação de pagamento sandbox).

**Alternativa por API (feita pelo humano, nunca pelo agente):** a Asaas
expõe `GET`/`POST /v3/myAccount/commercialInfo/`, autenticado por
`ASAAS_API_KEY` (não por login/senha). O `POST` exige reenviar **todos**
os campos comerciais de uma vez (CPF/CNPJ, endereço, renda, telefone,
`site` etc.) — omitir um campo o apaga. Também pode disparar nova análise
de conta com bloqueio temporário. Por isso é uma ação que o responsável
pela conta deve executar e revisar diretamente, nunca delegada a um
agente. Script de leitura (`GET`, seguro) em
`scripts/asaas_get_commercial_info.ps1`.

## E-mail de teste real sem credenciais (Mailinator)

Para validar que um e-mail do sistema (senha temporária, notificação,
recibo) chega de verdade — não só que `send_mail()` foi chamado — usar uma
caixa pública descartável que **não exige login/senha para ler mensagens**.
Isso é o que um agente pode fazer sozinho, sem esbarrar no limite de nunca
autenticar em contas de terceiros.

**Opção recomendada: Mailinator** (`https://mailinator.com`) — inbox
pública, qualquer endereço `@mailinator.com` é lido só de conhecer o nome,
sem criar conta.

1. Escolher um endereço único (evitar reutilizar entre sessões, é público):
   `algumnome-teste-<data>@mailinator.com`.
2. Apontar o campo `email` da `Person` de teste para esse endereço:
   ```powershell
   .\.venv\Scripts\python.exe manage.py shell -c "
   from system.models import Person
   p = Person.objects.get(cpf='<CPF_DE_TESTE>')
   p.email = 'algumnome-teste-<data>@mailinator.com'
   p.save(update_fields=['email'])
   "
   ```
3. Disparar a ação que envia o e-mail (ex.: `/password-reset/` no
   navegador, ou chamando o service diretamente).
4. Ler a caixa pública, sem login, em:
   `https://www.mailinator.com/v4/public/inboxes.jsp?to=<nome-escolhido>`
5. Restaurar o `email` da `Person` de teste ao valor original depois de
   confirmar.

**Alternativas** (mesma característica de inbox pública sem login) — nem
sempre disponíveis, testar antes de depender:
`1secmail.com` (API REST pública, `GET /api/v1/?action=getMessages`),
`guerrillamail.com`. Evitar `mail.tm` e qualquer serviço que exija criar
conta/senha para ler a caixa — isso um agente não pode fazer.

**Nunca usar** um domínio real de terceiro (ex.: Gmail do usuário) como
destinatário de teste sem que o próprio usuário confirme e leia a caixa —
o agente não deve presumir acesso a caixas de e-mail reais de ninguém.

---

## Utilitário JavaScript reutilizável

Todos os steps abaixo usam estas duas funções. Execute no console controlado do
navegador quando o adaptador permitir ou inclua no início de cada bloco:

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

### Fluxo Asaas 100% via API (sem navegador)

**Método preferencial desde 2026-07-06.** Validado ponta a ponta (Person criado, ativo,
`Membership` ativa) usando só `curl`/chamadas HTTP diretas — nenhum navegador, interno
ou externo, é necessário. A chave é que `/pagamentos/sucesso/` é um `GET` HTTP normal:
ele não precisa ser "clicado" por um navegador, só recebido por qualquer cliente HTTP
que carregue os mesmos cookies de sessão da etapa anterior.

**Pré-requisitos (únicos passos que ainda exigem ação humana, uma vez só por sessão de teste):**

1. Um túnel HTTPS rodando e apontando para `localhost:8000` (`ngrok http 8000` — ver
   `curl http://127.0.0.1:4040/api/tunnels` para pegar a URL pública sem precisar
   parsear log). Pode já estar rodando em segundo plano de um teste anterior.
2. Esse domínio do túnel cadastrado no campo **"Site"** de Minha Conta → Informações no
   painel sandbox da Asaas (esse campo só aceita um valor — se já estiver ocupado pelo
   domínio do HG, o usuário precisa trocar temporariamente e reverter depois).
3. `.env` local ajustado (com confirmação do usuário, é config compartilhada com HG/prod):
   `SITE_BASE_URL=https://<dominio-do-tunel>` e `DJANGO_ALLOWED_HOSTS` incluindo esse
   domínio. Reiniciar o servidor Django para carregar o novo valor.

**Passo 1 — Buscar a página, extrair CSRF token e IDs do catálogo:**

```bash
curl -s -c cookies.txt -b cookies.txt "http://localhost:8000/register/" -o register_page.html

# CSRF token (pegar só o PRIMEIRO — a página tem 3 forms, cada um com seu próprio token)
grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' register_page.html | head -1

# Plano adulto PIX mensal do catálogo novo (PlanTier/PlanPrice, PRD-127/129)
grep -o '"id": "pp:[0-9]*", "code": "[^"]*"' register_page.html | head -5
# Ex.: "id": "pp:1", "code": "adult-2x-asaas_pix-monthly"  ← este é o que queremos

# Turma adulta (id composto "<pk>::<nome>")
grep -o '"id": "[0-9]*::[^"]*"[^}]*"category_audience": "adult"' register_page.html | head -1
```

> **Atenção ao extrair o CSRF token via shell**: usar sempre `head -1` — os três `<form>`
> da página (cadastro, materiais, produtos) embutem o mesmo token, e sem o `head -1` o
> `grep -o` retorna as três ocorrências concatenadas por quebra de linha, gerando um
> valor corrompido ("CSRF token from POST has incorrect length").

**Passo 2 — Submeter o cadastro completo num único POST (o wizard é uma SPA que só
envia UM POST no fim, não um por etapa):**

```bash
CSRF="<token do passo 1>"
curl -s -c cookies.txt -b cookies.txt -o post_result.html -w "HTTP_STATUS:%{http_code}\n" \
  -X POST "http://localhost:8000/register/" \
  -H "Referer: http://localhost:8000/register/" \
  --data-urlencode "csrfmiddlewaretoken=$CSRF" \
  --data-urlencode "registration_profile=holder" \
  --data-urlencode "holder_name=Ana Teste API" \
  --data-urlencode "holder_cpf=960.013.389-14" \
  --data-urlencode "holder_birthdate=22/07/1992" \
  --data-urlencode "holder_biological_sex=female" \
  --data-urlencode "holder_phone=(11) 97654-3210" \
  --data-urlencode "holder_email=ana.teste.api@example.com" \
  --data-urlencode "holder_password=Senha@123" \
  --data-urlencode "holder_password_confirm=Senha@123" \
  --data-urlencode "holder_class_groups=1::Jiu Jitsu" \
  --data-urlencode "holder_has_martial_art=no" \
  --data-urlencode "selected_plan=pp:1" \
  --data-urlencode "checkout_action=pix"
# Esperado: HTTP_STATUS:302
```

Isso já dispara `create_pre_registration_plan_payment` no servidor, que chama a API
real da Asaas e cria o pagamento de verdade (`POST /payments`).

**Passo 3 — Localizar o `PreRegistration` e o `asaas_payment_id` gerado:**

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.filter(holder_cpf='960.013.389-14').order_by('-created_at').first()
snap = pr.form_snapshot or {}
print('ID:', pr.pk)
print('asaas_payment_id:', snap.get('plan_payment', {}).get('asaas_payment_id'))
"
```

**Passo 4 — Confirmar o pagamento via endpoint oficial de simulação do sandbox Asaas**
(documentado em `docs.asaas.com/reference/confirm-payment` — funciona só no sandbox,
não existe em produção; não precisa entrar no painel nem escanear PIX de verdade):

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.services.asaas_client import _request
result = _request('POST', '/sandbox/payment/<asaas_payment_id>/confirm', json_body={})
print('status:', result.get('status'))  # esperado: RECEIVED
"
```

> Sem nenhum navegador visitando a `invoiceUrl`, o redirect automático da página
> hospedada da Asaas **não acontece** (o polling que detecta o pagamento e redireciona
> roda como JS na própria página da Asaas — só existe se alguém abrir a página). Isso é
> esperado e não é um problema: o Passo 5 substitui esse redirect manualmente.

**Passo 5 — Refletir a confirmação na mesma sessão (substitui o redirect que o
navegador faria), usando o MESMO cookie jar do Passo 2:**

```bash
curl -s -c cookies.txt -b cookies.txt -w "HTTP_STATUS:%{http_code}\nREDIRECT_TO:%{redirect_url}\n" \
  "http://localhost:8000/pagamentos/sucesso/?pre_registration_id=<PR_PK>&stage=plan"
# Esperado: HTTP_STATUS:302, REDIRECT_TO:.../register/
```

**Verificar no banco:**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.get(pk=<PR_PK>)
print('Status:', pr.status)        # payment_confirmed
print('plan_paid:', (pr.form_snapshot or {}).get('plan_paid'))  # True
"
```

**Passo 6 — Conferir que a página renderiza o estado pós-pagamento (sem abrir nada, só
lendo o HTML retornado):**

```bash
curl -s -c cookies.txt -b cookies.txt "http://localhost:8000/register/" -o register_after_payment.html
grep -o "Pagamento confirmado" register_after_payment.html   # deve aparecer
grep -o '"reg-post-plan-json">[a-z]*' register_after_payment.html  # esperado: true
```

**Passo 7 — Finalizar o cadastro (POST simples, sem corpo além do CSRF — a view lê
`pending_pre_registration_id` da sessão, não de campos do formulário):**

```bash
CSRF=$(grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' register_after_payment.html | head -1 | sed 's/.*value="//;s/"$//')
curl -s -c cookies.txt -b cookies.txt -w "HTTP_STATUS:%{http_code}\nREDIRECT:%{redirect_url}\n" \
  -X POST "http://localhost:8000/register/finalizar/" \
  -H "Referer: http://localhost:8000/register/" \
  --data-urlencode "csrfmiddlewaretoken=$CSRF"
# Esperado: HTTP_STATUS:302, REDIRECT:.../dashboard/
```

**Verificação final no banco (mesmo formato do Fluxo 1):**
```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import Person, PreRegistration
from system.models.membership import Membership
p  = Person.objects.filter(email='ana.teste.api@example.com').first()
pr = PreRegistration.objects.filter(holder_cpf='960.013.389-14').first()
m  = Membership.objects.filter(person=p).first() if p else None
print('Person:', p.full_name if p else 'NAO ENCONTRADO')
print('is_active:', p.is_active if p else '-')
print('PreRegistration status:', pr.status if pr else 'NAO ENCONTRADO')
print('Membership status:', m.status if m else 'NAO ENCONTRADO')
print('Membership plan_price_id:', m.plan_price_id if m else '-')
"
```

**Saída esperada:**
```
Person: Ana Teste API
is_active: True
PreRegistration status: finalized
Membership status: active
Membership plan_price_id: 1
```

**Sobre o webhook Asaas neste fluxo:** o webhook `/pagamentos/webhook/asaas/` (visto na
seção "Estratégia de teste por gateway") não participa da confirmação do wizard — ele
serve para o Fluxo A (`RegistrationOrder` de clientes já cadastrados), não para
`PreRegistration`. Não é necessário aguardar nem verificar entrega de webhook para este
fluxo funcionar; o Passo 5 (`GET /pagamentos/sucesso/`) é autossuficiente.

**Depois de validar**: se só este fluxo API era necessário, pode reverter `.env`
(`SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`) e encerrar o túnel. Se quiser também uma
conferência visual, seguir para a seção seguinte usando o **navegador interno** (não é
necessário trocar de navegador quando o adaptador acessa a URL externa, já que a confirmação de
pagamento não depende mais de abrir a `invoiceUrl`) — criar um **cliente novo** (CPF
inédito) para não colidir com o registro já criado por este fluxo via API.

---

### Confirmar pagamento Asaas — navegador interno e sandbox

O Asaas não oferece um gerador de eventos idêntico ao `stripe trigger`, mas o sandbox
possui o endpoint oficial `POST /sandbox/payment/{id}/confirm`. Depois de confirmar o
pagamento no gateway, o wizard ainda precisa receber a `successUrl`. O domínio dessa
URL deve coincidir com o domínio cadastrado na conta sandbox.

**Passo 1 — Obter a `invoiceUrl` real sem duplicar o redirect do browser:**

Chamar o serviço diretamente pelo shell (mesma função que a view usa) para capturar
a URL da fatura sandbox sem depender do POST do formulário:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.pre_registration import PreRegistration
from system.services.registration_checkout import create_pre_registration_plan_payment
from system.constants import CheckoutAction
pr = PreRegistration.objects.get(pk=<PR_PK>)
url = create_pre_registration_plan_payment(pr, CheckoutAction.PIX)
print('invoiceUrl:', url)
"
```

> Trocar `CheckoutAction.PIX` por `CheckoutAction.ASAAS_CARD` para o fluxo de cartão Asaas.

**Passo 2 — Abrir a `invoiceUrl` no navegador disponível:**

Preferir o navegador interno definido em `docs/PLATFORM-ADAPTERS.md`. Se o adaptador
não permitir domínio externo, usar o Chrome conectado ou confirmar o pagamento pelo
endpoint oficial do sandbox.

Depois de abrir a página:
1. Perguntar ao usuário se ele quer pagar com o cartão de teste sandbox da Asaas ou
   escanear o PIX de teste (a Asaas sandbox aceita cartões e chaves fictícias — consultar
   a documentação da Asaas para os valores atuais de teste, pois eles mudam).
2. Confirmar o estado no próprio sandbox ou consultar a API antes de prosseguir. Não
   inferir sucesso apenas pelo redirect.

**Passo 3 — Refletir a confirmação no wizard local:**

Se `SITE_BASE_URL` apontar para outro ambiente, o redirect não chega ao servidor local.
Corrija a configuração antes do checkout ou, somente em homologação local, acesse o
retorno manual com o `asaas_payment_id` gravado no snapshot:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.get(pk=<PR_PK>)
snap = pr.form_snapshot or {}
print('asaas_payment_id:', snap.get('plan_payment', {}).get('asaas_payment_id'))
"
```

```javascript
// No navegador interno — substituir <pay_id> pelo valor acima
window.location.href = '/pagamentos/sucesso/?id=<pay_id>';
```

**Comportamento esperado no navegador:**
- Redireciona para `/register/`
- Aparece o alerta verde **"Pagamento confirmado!"**
- O wizard avança para o modo pós-pagamento:
  - Barra de progresso avança para o estado pós-pagamento
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

> **Ajuste de domínio para testes ponta a ponta reais (opcional):** para que o
> redirect da Asaas chegue de fato ao `localhost` sem o passo manual acima, é preciso
> um túnel HTTPS público (ex: `cloudflared`, `ngrok`) apontando para `localhost:8000`,
> com `SITE_BASE_URL` local ajustado para a URL do túnel e esse mesmo domínio
> cadastrado em "Minha Conta → Informações" no painel sandbox da Asaas (ver
> `CLAUDE.md` seção 9 e `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`).
> Essa mudança de configuração **exige decisão e confirmação do usuário** antes de
> qualquer alteração no `.env` local — não fazer isso silenciosamente.

> **Sobre o webhook Asaas (Fluxo A — RegistrationOrder):**
> O webhook Asaas **não confirma** o wizard (Fluxo B). Ele serve para alunos já cadastrados
> com `RegistrationOrder`. Para o wizard, apenas o redirect via `successUrl` (ou a
> simulação manual do Passo 3) confirma o pagamento.

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

### Hook de simulação Stripe (100% local, sem navegador externo)

Este é o único gateway que se testa inteiramente pelo preview interno — o Stripe CLI
simula o webhook que a Stripe enviaria em produção, sem precisar abrir
`checkout.stripe.com`.

**Passo 1 — Autenticar o Stripe CLI (uma vez por máquina, expira em 90 dias):**

```powershell
stripe login
```

Saída esperada:
```
Your pairing code is: wowed-freed-witty-fluent
This pairing code verifies your authentication with Stripe.
Press Enter to open the browser or visit https://dashboard.stripe.com/stripecli/confirm_auth?t=... (^C to quit)> Done! The Stripe CLI is configured for LV Academy with account id acct_1TLsxdItFp0xr82s
```

**Passo 2 — Manter o listener rodando em terminal separado durante todo o teste:**

```powershell
stripe listen --forward-to http://127.0.0.1:8000/pagamentos/webhook/stripe/
```

Saída esperada (o `whsec_...` deve bater com `STRIPE_WEBHOOK_SECRET` no `.env`):
```
> Ready! You are using Stripe API Version [versão atual]. Your webhook signing secret is whsec_... (^C to quit)
2026-06-10 18:58:58   --> checkout.session.completed [evt_1Tgu9HItFp0xr82sDBRv8AsX]
2026-06-10 18:58:58  <--  [200] POST http://127.0.0.1:8000/pagamentos/webhook/stripe/ [evt_1Tgu9HItFp0xr82sDBRv8AsX]
```

> Se `STRIPE_WEBHOOK_SECRET` no `.env` não corresponder ao `whsec_...` impresso aqui,
> copiar o valor exibido, atualizar o `.env` e reiniciar o servidor Django
> (`--noreload` exige encerrar o processo na porta 8000 e iniciar o comando novamente).

**Passo 3 — Disparar o evento `checkout.session.completed` (em outro terminal):**

```powershell
stripe trigger checkout.session.completed `
  --override checkout_session:client_reference_id="pre-registration:<PR_PK>"
# Substituir <PR_PK> pelo pk do PreRegistration obtido no passo anterior (ex: 2)
```

**Comportamento esperado no terminal do `stripe listen`:**
```
2026-06-10 18:58:58   --> checkout.session.completed [evt_1Tgu9HItFp0xr82sDBRv8AsX]
2026-06-10 18:58:58  <--  [200] POST http://127.0.0.1:8000/pagamentos/webhook/stripe/ [evt_1Tgu9HItFp0xr82sDBRv8AsX]
```

**Comportamento esperado no banco:**
- `StripeWebhookEvent` criado
- `PreRegistration.status` muda para `payment_confirmed`
- `form_snapshot["plan_paid"]` muda para `True`
- **Atenção:** o `stripe trigger` usa um session ID de fixture diferente do original.
  O webhook sobrescreve o `stripe_session_id` no snapshot com o ID fictício do fixture.

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
  // Esta função não captura erros passados — consultar os logs do console no fluxo
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

Use a leitura de console do navegador ou o seguinte snippet **a cada step** para detectar erros JS:

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
