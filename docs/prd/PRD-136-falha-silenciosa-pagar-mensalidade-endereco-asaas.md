# PRD-136: Falha silenciosa no botão "Pagar mensalidade" + confirmação do fluxo de endereço no Asaas

## Summary

Durante validação manual do cadastro público no Render HG (cliente Asaas cartão), o botão
"Pagar mensalidade" falhou repetidas vezes sem nenhum erro visível na tela — a página
simplesmente "reiniciava" a Etapa 6 com a forma de pagamento voltando para PIX. A causa raiz
foi isolada por eliminação: `PortalRegistrationForm.is_valid()` retorna `False`
(validação de `holder_class_groups`/`checkout_action` falha) e a view chama
`form_invalid()`, que re-renderiza a mesma página com HTTP 200 — mas o template
`templates/login/register.html` nunca renderiza `form.errors` para nenhum campo, então o
usuário (e o agente investigando) não recebe nenhum sinal de que algo falhou. Só foi possível
diagnosticar lendo `system/forms/registration_forms.py` e inspecionando `sessionStorage`
diretamente via DevTools.

Nesta mesma investigação, também foi observado (uma única vez, não reproduzido de novo após
limpeza) um valor corrompido no campo oculto `holder_class_groups`:
`"['1::Jiu Jitsu']"` (repr Python de lista, em vez do valor limpo `"1::Jiu Jitsu"`) — string
que nenhum `choices` reconhece, disparando a validação nativa `MultipleChoiceField` do Django
e reproduzindo o mesmo sintoma de "reset silencioso". A causa exata de como esse valor chegou
ao campo não foi confirmada; o sintoma sumiu depois que uma `PreRegistration` "draft" órfã e
referenciada pela sessão do navegador (`session["pending_pre_registration_id"]`, cookie
`HttpOnly`, não limpável via `document.cookie`) foi apagada do banco.

Por fim, esta PRD documenta que o mecanismo de "Endereço (opcional — pré-preenche o
pagamento)" do wizard **está de fato implementado** no backend
(`ensure_pre_registration_asaas_customer` repassa `holder_postal_code`/`holder_address`/etc.
para `asaas_client.create_customer`), mas **nunca foi confirmado ponta a ponta** neste
projeto — em todos os cadastros de teste reais feitos até agora o campo de endereço foi
deixado em branco (é opcional), então a página de checkout hospedada do Asaas sempre pediu o
endereço de novo, sem nunca provar que o pré-preenchimento funciona quando o campo é
preenchido no wizard.

## Demand type

Descoberta/documentação de bug — sem correção nesta PRD (autorização explícita do usuário:
"apenas para memory, claude e agents terem documentação"). PRD registrada para servir de
base a uma implementação futura, com aprovação separada.

## Current problem

1. **Falha silenciosa do formulário de cadastro público**: quando `PortalRegistrationForm`
   falha na validação de campos ocultos gerenciados por JS (`holder_class_groups`,
   `checkout_action`), a view (`PublicRegisterView.form_invalid`, herdado do
   `FormView` padrão do Django) re-renderiza a mesma página com HTTP 200 e nenhuma mensagem
   de erro visível — nem no template (`templates/login/register.html` não tem
   `{{ form.errors }}` em lugar nenhum), nem via `django.contrib.messages` (que só é usado
   nos blocos `except ValueError` / `except asaas_client.AsaasClientError` dentro de
   `form_valid`, nunca em `form_invalid`). O usuário final veria a "Etapa 6 de 8" resetar sem
   explicação, sem qualquer forma de saber o que corrigir.
2. **Corrupção observada em `holder_class_groups`**: em uma tentativa de cadastro (cliente de
   teste "Cliente Render Asaas Credito Dois"), o hidden input `holder_class_groups` foi
   submetido com o valor `"['1::Jiu Jitsu']"` — string com colchetes e aspas simples
   literais, formato que só é produzido por `str()` de uma lista Python, não por nenhum
   caminho JS identificado em `static/system/js/auth/register.js`. Esse valor não corresponde
   a nenhuma turma real, então `MultipleChoiceField.clean()` do Django rejeita a submissão
   silenciosamente (ver problema 1). O `PreRegistration` (pk=2, status `draft`) tinha
   `holder_class_groups` limpo no banco (`['1::Jiu Jitsu']` como lista Python válida, não como
   string corrompida) — ou seja, a corrupção não estava persistida no snapshot salvo; ela só
   apareceu no `sessionStorage` do navegador (chave `lv-wiz-v1`) durante a tentativa
   subsequente, junto com uma cópia limpa (`"ids":["['1::Jiu Jitsu']","1::Jiu Jitsu"]"` — os
   dois valores coexistindo no mesmo array). Apagar o `PreRegistration` órfão referenciado
   pela sessão do servidor e recarregar a página com `localStorage`/`sessionStorage` limpos
   resolveu o sintoma nas duas tentativas seguintes, mas a causa exata de como o valor
   corrompido nasceu (JS ou dado servido pelo backend) **não foi confirmada**.
3. **Endereço opcional do wizard nunca testado ponta a ponta com o Asaas**: o código
   (`system/services/registration_checkout.py::ensure_pre_registration_asaas_customer`,
   linhas 667-694) já lê `holder_postal_code`/`holder_address`/`holder_address_number`/
   `holder_address_complement`/`holder_address_neighborhood`/`holder_city` do snapshot e os
   envia para `asaas_client.create_customer` (`system/services/asaas_client.py`, linhas
   73-110, que monta `postalCode`/`address`/`addressNumber`/`complement`/`province`/`city` no
   payload do Asaas). Isso deveria fazer a página de checkout hospedada do Asaas pré-preencher
   o endereço do titular do cartão. Porém, em nenhum dos cadastros de teste reais realizados
   nesta sessão (nem em sessões anteriores documentadas no histórico do projeto) o campo de
   endereço do wizard foi preenchido — sempre foi deixado em branco por ser opcional — então
   esse comportamento nunca foi observado funcionando na prática.

## Goal

Registrar, para consumo futuro por agentes (Claude/Codex/Cursor) e pelo time, os três achados
acima com evidência suficiente para que uma implementação futura não precise redescobrir a
causa raiz do zero. Não implementar correção nesta PRD.

## Context Ledger

### Files read in full

- `system/views/auth_views.py` (função `form_valid`, linhas 60-230 lidas)
- `system/forms/registration_forms.py` (trechos relevantes: `checkout_action` field
  definição linha 281-286, `_clean_plan_selection` linha 587-628, `_has_invalid_class_group_selection`
  linha 691-698)
- `system/services/registration_checkout.py` (função `create_pre_registration_plan_payment`
  linhas 749-913, `ensure_pre_registration_asaas_customer` linhas 667-694,
  `resolve_catalog_plan` linhas 99-119)
- `system/services/financial_transactions.py` (`resolve_checkout_action_for_plan` linhas 26-35)
- `system/services/pre_registration.py` (`_build_pre_registration_snapshot` linhas 40-60,
  `build_wizard_form_snapshot` linhas 63-76, `normalize_snapshot_for_form` linhas 447-472,
  `build_pending_summary_from_pre_registration` linhas 294-319,
  `build_snapshot_class_group_summary` linhas 357-364)
- `system/services/asaas_client.py` (`create_customer` linhas 73-110, `create_credit_card_payment`
  linhas 141+)
- `static/system/js/auth/register.js` (`selectClassGroup` linha 2381-2400,
  `_syncClassGroupInputs` linha 947-961, `syncClassesToForm` linha 963+,
  `readHiddenValuesByName` linha 3561-3569, `normalizeIdList` linha 354-363,
  `selectPlan`/`resolvePlanCheckoutAction`/`validatePlan` linhas 1654-1711)
- `templates/login/register.html` (busca completa por `messages`, `form.errors`,
  `holder_class_groups` — confirmado: bloco de mensagens existe em `wizard-system-messages`
  linha 52-58, mas nenhum campo renderiza `.errors`)

### Adjacent files consulted

- `system/models/pre_registration.py` (campo `form_snapshot`, `status`)

### Internet / official documentation

Não aplicável — investigação interna de código, sem dependência de biblioteca/SDK externo.

### Context7 / MCPs / tools verified

- `mcp__claude-in-chrome__javascript_tool` usado para inspecionar `sessionStorage`,
  `localStorage`, hidden inputs e `FormData` do formulário em tempo real no navegador contra
  `https://lvjiujitsu-hg.onrender.com/register/`.
- Django shell local com `DJANGO_ENV_FILE=.env.hg` (somente leitura + uma exclusão pontual de
  `PreRegistration` draft órfã) usado para inspecionar `form_snapshot` real no Supabase HG.

### Limitations found

- A causa exata de como `holder_class_groups` recebeu o valor `"['1::Jiu Jitsu']"` não foi
  confirmada — foi observada uma vez, não reproduzida numa segunda tentativa limpa. Hipóteses
  não confirmadas: (a) alguma rota client-side em `register.js` faz `String(algumaLista)` em
  vez de tratar cada elemento individualmente; (b) o valor veio de dado já corrompido servido
  pelo backend via `pending_person_json`/`context["registration_initial_step"]` quando a
  sessão referenciava um `PreRegistration` obsoleto. Nenhuma das duas hipóteses foi validada
  com certeza.
- O comportamento de pré-preenchimento de endereço no checkout do Asaas foi confirmado apenas
  por leitura de código (`ensure_pre_registration_asaas_customer` → `create_customer`), nunca
  observado funcionando na prática (nenhum teste real preencheu o campo de endereço do
  wizard).

## Required skills

- `lv-task-intake`
- `lv-prd`

## Understanding approved

Autorizado explicitamente pelo usuário nesta sessão: "registre um novo PRD para corrigir e
para que documentemos o que foi corrigido e mal implementado na descoberta do acionamento do
botao problematico. apenas para memory, claude e agents terem documentação." — ou seja,
autoriza a criação desta PRD como registro; não autoriza implementação de código nesta PRD.

## Execution prompt

Não aplicável nesta PRD (documentação apenas). Uma PRD de implementação futura deve reler
este documento antes de propor a correção.

## Scope

Fora desta PRD — apenas registro dos achados acima em `docs/prd/` e atualização de
`docs/prd/README.md`.

## Out of scope

- Implementar renderização de `form.errors` no template do wizard.
- Investigar/corrigir a origem exata da corrupção de `holder_class_groups`.
- Testar e confirmar o pré-preenchimento de endereço no Asaas com dado real preenchido no
  wizard.
- Qualquer mudança de código em `system/` ou `static/`.

## Impacted files

Nenhum arquivo de código alterado por esta PRD (apenas a própria PRD e o índice).

## Risks and edge cases

- Falha silenciosa do formulário afeta **qualquer** cliente real tentando se cadastrar no
  Render HG/produção que caia em uma validação de campo oculto (`checkout_action`,
  `holder_class_groups`, `dependent_class_groups`, `student_class_groups`,
  `extra_dependents_payload`) — o cliente veria a etapa "resetar" sem explicação e poderia
  desistir do cadastro sem que a equipe soubesse o motivo.
- Sessões de navegador com `pending_pre_registration_id` apontando para um
  `PreRegistration` "draft" antigo (nunca finalizado, ex.: usuário abandonou o cadastro na
  etapa de pagamento) podem contaminar tentativas futuras com dado obsoleto lido via
  `pending_person_json`, mesmo depois do usuário limpar `localStorage`/`sessionStorage` (o
  cookie de sessão do Django é `HttpOnly`, portanto não é limpo por `document.cookie` nem por
  `localStorage.clear()`).

## Rules and constraints

Nenhuma regra de negócio nova nesta PRD — apenas documentação.

## Plan

1. Redigir esta PRD com o achado completo (concluído).
2. Atualizar `docs/prd/README.md` com a entrada (concluído).
3. Aguardar priorização/aprovação futura para abrir uma PRD de implementação que:
   - torne visível qualquer falha de `form.is_valid()` no wizard (mínimo: mensagem genérica
     de erro renderizada, idealmente listando os campos problemáticos sem expor detalhe
     técnico ao usuário final);
   - investigue com reprodução controlada (ex.: teste automatizado que force submissão dupla
     do `holder_class_groups` com valores distintos) a origem da corrupção observada;
   - decida uma política explícita para `pending_pre_registration_id` obsoleto (ex.: expirar
     por tempo, ou oferecer ao usuário um botão "recomeçar cadastro" que limpa a sessão
     server-side);
   - realize um teste real preenchendo o endereço opcional no wizard e confirme visualmente
     que a página de checkout hospedada do Asaas chega com CEP/Rua/Número/Bairro/Cidade já
     preenchidos.

## Test plan

### Tests to author

Nenhum nesta PRD — ficam para a PRD de implementação futura.

### Execution authorization

Não aplicável.

### Execution evidence

Não aplicável — evidência desta PRD é a investigação já registrada acima (leitura de código
+ inspeção ao vivo via `javascript_tool` + consulta ao Django shell contra HG).

## Visual validation

Não aplicável.

## ORM validation

Consulta somente leitura executada durante a investigação (registrada como evidência, não
como parte desta PRD):

```powershell
$env:DJANGO_ENV_FILE = ".env.hg"
python manage.py shell -c "
from system.models.pre_registration import PreRegistration
prs = PreRegistration.objects.order_by('-pk')[:5]
for pr in prs:
    snap = pr.form_snapshot or {}
    print('PK', pr.pk, 'name', snap.get('holder_name'))
    print('  holder_class_groups repr:', repr(snap.get('holder_class_groups')))
"
```

Resultado observado: `PK 2` (`Cliente Render Asaas Credito`, status `draft`) tinha
`holder_class_groups` = `['1::Jiu Jitsu']` (lista Python limpa no banco — a corrupção não
estava persistida ali).

## Quality validation

Não aplicável (documentação).

## Evidence

- Trecho de `sessionStorage` (`lv-wiz-v1`) capturado ao vivo mostrando o valor duplicado:
  `"classSelections":[{"ids":["['1::Jiu Jitsu']","1::Jiu Jitsu"]}]`.
- `FormData` do `#wizard-form` capturado ao vivo mostrando a submissão real:
  `holder_class_groups=['1::Jiu Jitsu']` (um único valor, malformado).
- Confirmação de que, após apagar `PreRegistration` pk=2 (`draft`, órfã) e recarregar com
  storage limpo, o mesmo fluxo (Etapa 1→6, mesma turma, mesmo plano Asaas cartão) completou
  com sucesso e redirecionou para `https://sandbox.asaas.com/i/...` (checkout real do Asaas).

## Implemented

Nada implementado nesta PRD (documentação apenas).

## Cleanup findings

- `PreRegistration` pk=2 (draft, órfã, CPF de teste `444.777.222-14`) foi removida do banco
  HG durante a investigação para destravar o teste — ação de limpeza de dado de teste próprio,
  não uma mudança de schema ou comportamento.

## Follow-up PRDs

Uma PRD futura de implementação deve ser aberta cobrindo os 4 itens do plano acima, mediante
nova aprovação explícita do usuário.

## Deviations from plan

Nenhum — escopo desta PRD sempre foi só documentação, conforme solicitado.

## Pending

- Confirmar (ou descartar) a hipótese de origem da corrupção de `holder_class_groups`.
- Testar ponta a ponta o pré-preenchimento de endereço no Asaas.
- Implementar exibição de erro de formulário no wizard.

## Final status

**Concluída** (como documentação/descoberta) — nenhuma correção de código foi escopada ou
autorizada nesta PRD.
