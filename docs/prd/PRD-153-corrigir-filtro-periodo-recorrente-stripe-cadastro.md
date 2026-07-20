# PRD-153: Corrigir filtro "Período de cobrança" para planos recorrentes Stripe no cadastro público

## Summary

No wizard de cadastro público, ao escolher forma de pagamento "Cartão", os
3 preços recorrentes Stripe (mensal, semestral, anual — aprovados e
gravados na PRD-137 como opção de fidelidade mais barata em ciclos longos)
aparecem **todos juntos**, independente de qual pílula de "Período de
cobrança" (Mensal/Trimestral/Semestral/Anual) está selecionada. Isso é
comportamento **intencional** documentado na própria PRD-137 ("o mecanismo
de exibição não está quebrado... sem alterar"), mas o usuário, ao revisar a
tela na sessão atual, considerou a apresentação confusa e pediu correção.
Perguntado se queria reverter a decisão de negócio (só recorrente mensal)
ou só corrigir a exibição, o usuário escolheu manter os 3 valores
aprovados na PRD-137 e corrigir apenas o filtro: a pílula de período deve
valer também para Stripe, mostrando 1 card por vez, batendo com o período
selecionado.

## Demand type

Correção de UI/JS (comportamento de filtro), sem mudança de catálogo/preço
nem de regra de negócio.

## Current problem

`static/system/js/auth/register.js`, função `getFilteredPlans` (linha
~1498-1506):

```js
function getFilteredPlans() {
  var filtered = getEligiblePlansForCurrentPerson().filter(function (p) {
    if (planFilter.frequency !== null && p.weekly_frequency !== planFilter.frequency) return false;

    var isStripe = p.gateway_code === 'stripe_card';
    if (!isStripe && planFilter.cycle && p.billing_cycle !== planFilter.cycle) return false;
    if (planFilter.method && p.payment_method !== planFilter.method) return false;
    return true;
  });
  ...
}
```

O `!isStripe &&` bypassa deliberadamente o filtro de `planFilter.cycle`
para qualquer `PlanPrice` com `gateway_code === 'stripe_card'` — por isso,
com "Cartão" selecionado, os 3 `PlanPrice` Stripe (mensal/semestral/anual)
do tier aparecem juntos sempre, não importa a pílula de período ativa.
Confirmado nesta sessão, ao vivo, durante a homologação de um cadastro real
(perfil "aluno Asaas", Etapa 6, forma de pagamento "Cartão").

Este comportamento foi introduzido/documentado deliberadamente na PRD-137
(seção "2. Recorrente Stripe só existe no ciclo mensal", linha 18: *"O
front-end (register.js:1470-1472) já exibe o card Stripe em qualquer aba
de ciclo selecionada... quando o filtro 'Cartão' está ativo — o mecanismo
de exibição não está quebrado."*) e reforçado como restrição explícita
("Sem alterar o mecanismo de exibição do card Stripe no front-end (já
funciona corretamente)"). Não é um bug técnico não-intencional — é uma
escolha de UX que o usuário agora quer mudar.

## Goal

Fazer a pílula "Período de cobrança" filtrar também os planos
`gateway_code === 'stripe_card'`, mostrando **1** card recorrente por vez
(o que corresponde ao período selecionado), preservando os 3 valores
comerciais aprovados na PRD-137 (mensal R$229,14, semestral R$1.195,00,
anual R$2.265,00 para Adulto 2x — e equivalentes para os demais tiers).

## Context Ledger

### Files read in full

- `docs/prd/PRD-137-recorrente-stripe-ciclos-parcelamento-asaas-catalogo-novo.md`
- `static/system/js/auth/register.js` (`getEligiblePlansForCurrentPerson`,
  `planCycles`, `planMethods`, `getFilteredPlans`, linhas 1444-1514)
- `system/tests/test_register_wizard_contract.py` (padrão de teste de
  contrato estático usado no projeto para `register.js`/`register.html`)

### Adjacent files consulted

- `system/models/plan.py` (`BillingCycle`, `PlanPrice`) — confirma que
  Stripe só tem linhas `monthly`/`semiannual`/`annual` (sem `quarterly`).

### Internet / official documentation

Não aplicável — correção de lógica de filtro JS interna, sem
dependência de API/SDK externo.

### Context7 / MCPs / tools verified

Não aplicável.

### Limitations found

- Não existe test runner de JS no projeto (sem `package.json`/Jest) — a
  cobertura de regressão é feita via teste de contrato Django
  (`SimpleTestCase` lendo o arquivo estático), no mesmo padrão já usado em
  `test_register_wizard_contract.py`, mais validação manual real no
  navegador.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery` (mudança de comportamento visual do wizard público)
- `lv-cleanup-audit`

## Understanding approved

Usuário escolheu, entre as duas opções apresentadas ("reverter para só
mensal" vs. "manter os 3, corrigir a exibição"): **manter os 3 valores
aprovados na PRD-137 e corrigir a exibição**, para que o filtro de período
valha também para Stripe.

## Scope

- `static/system/js/auth/register.js`: remover o bypass `!isStripe &&` em
  `getFilteredPlans`, para que `planFilter.cycle` filtre também planos
  Stripe.
- Bump de `?v=` do asset (`register.js`) no template e no teste de
  contrato.
- Teste de contrato novo/estendido confirmando a remoção do bypass no
  código-fonte.
- Validação manual no navegador (desktop + mobile): com "Cartão"
  selecionado, cada pílula de período mostra exatamente 1 card recorrente
  Stripe (o correspondente).

## Out of scope

- Qualquer mudança de valor/catálogo dos planos Stripe (já aprovados e
  gravados na PRD-137).
- Comportamento do filtro para Asaas (PIX/Cartão não-recorrente) — já
  funciona corretamente, não é tocado.
- PRD-117 (fidelidade contratual/carência do recorrente) — sem relação.

## Impacted files

- `static/system/js/auth/register.js`
- `templates/login/register.html` (bump `?v=`)
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases

- Se o tier não tiver `PlanPrice` Stripe para o período selecionado (ex.:
  não existe `quarterly` para Stripe), nenhum card Stripe aparece nessa
  pílula — comportamento correto (não há essa oferta), consistente com
  como Asaas já se comporta quando falta uma combinação.
- `planCycles()` continua usando `getEligiblePlansForCurrentPerson()`
  (não filtrado) para decidir quais pílulas mostrar — não muda; garante
  que a pílula "Semestral"/"Anual" continue aparecendo mesmo que só exista
  oferta Stripe ou só Asaas para aquele período.

## Rules and constraints

- Menor mudança correta: só a linha do bypass, sem refatorar
  `getFilteredPlans` além do necessário.
- Bump de versão do asset obrigatório após editar JS (`CLAUDE.md` §2).
- TDD: teste de contrato escrito/ajustado antes da edição do JS.

## Plan

1. Escrever/ajustar teste de contrato (Red) — string do bypass não deve
   mais existir; nova versão `?v=` presente.
2. Remover o bypass em `getFilteredPlans` (Green).
3. Rodar suíte completa.
4. Validar no navegador real (desktop + mobile): retomar o cadastro da
   Carla Mendes (aluno Asaas/PIX — não afetado) e testar isoladamente a
   troca de pílula com "Cartão" selecionado num cadastro adulto 2x.

## Test plan

### Tests to author

- [x] `test_register_template_and_script_contract` (estendido): assert
  que o bypass `if (!isStripe && planFilter.cycle` não existe mais no
  `register.js`; assert nova versão `?v=` no template.

### Execution authorization

Autorizada pela decisão explícita do usuário nesta sessão.

### Execution evidence

- Red: `manage.py test system.tests.test_register_wizard_contract.RegisterWizardStaticContractTestCase.test_register_template_and_script_contract`
  → falhou em `?v=57` (ainda `?v=56`) antes da edição — bypass também
  presente no arquivo, confirmando o estado antigo.
- Green (após a correção): mesmo comando → **6/6 OK** (toda a classe de
  contrato).
- Suíte completa: `manage.py test system` → **711/711 OK**.
- `manage.py check` → sem issues.

## Visual validation

Validado no navegador interno real (perfil "Aluno", tier Adulto 2x,
`registration_profile=holder`, sem finalizar o cadastro — só a etapa 6),
lendo o texto renderizado da página (captura de tela por screenshot
indisponível nesta sessão por instabilidade pontual da ferramenta —
`get_page_text`/DOM confirmam o mesmo conteúdo visível ao usuário):

| Período selecionado | Cards exibidos com "Cartão" |
|---|---|
| Mensal | R$230,00/Mensal (Asaas) + **1** RECORRENTE R$229,14/mês (Stripe) |
| Semestral | **1** RECORRENTE R$1.195,00/mês (Stripe) — valor exato aprovado na PRD-137 |
| Anual | **1** RECORRENTE R$2.265,00/mês (Stripe) — valor exato aprovado na PRD-137 |
| Trimestral | R$660,00/Trimestral (Asaas) — sem card Stripe (não existe `PlanPrice` trimestral para Stripe, correto) |

Antes da correção (Mensal + Cartão) apareciam 4 cards (1 Asaas + 3
RECORRENTE simultâneos); depois, no máximo 1 RECORRENTE por período,
batendo com a pílula selecionada. PIX conferido sem regressão
(Trimestral/PIX → R$630,00/Trimestral, 1 card, como sempre foi).

## ORM validation

Não aplicável — sem mudança de dado/catálogo. Nenhum `PreRegistration`
residual: a validação não submeteu o formulário (só navegou pelas etapas
via clique programático), confirmado por consulta ORM ao final (nenhum
registro para o CPF de teste usado).

## Quality validation

- `manage.py check` → sem issues.
- `manage.py test system` → 711/711 OK.

## Evidence

Ver "Execution evidence" e "Visual validation" acima.

## Implemented

- [x] Removido o bypass `!isStripe &&` em `getFilteredPlans`
  (`static/system/js/auth/register.js`) — o filtro `planFilter.cycle`
  agora vale para todos os `gateway_code`, incluindo `stripe_card`.
- [x] `?v=` de `register.js` incrementado (`56` → `57`) em
  `templates/login/register.html`.
- [x] Teste de contrato estendido (`system/tests/test_register_wizard_contract.py`)
  cobrindo a ausência do bypass e a nova versão do asset.
- [x] Validado no navegador real: 4 períodos de cobrança + PIX sem
  regressão.

## Cleanup findings

Nenhum resíduo — a correção foi uma remoção de 1 condição, sem código
morto introduzido. `isStripe` (variável local que só existia para o
bypass) também foi removida por não ter mais uso.

## Follow-up PRDs

Nenhuma identificada.

## Deviations from plan

Nenhum desvio — a validação visual usou leitura de DOM/texto renderizado
em vez de screenshot, por instabilidade pontual da ferramenta de captura
nesta sessão (mecanismo de leitura de página confirmado funcional e fiel
ao conteúdo real renderizado).

## Pending

Nenhuma pendência.

## Final status

**Concluída.** Bug de apresentação corrigido (filtro de período agora
vale para Stripe), testado (contrato + suíte completa 711/711 OK) e
validado ao vivo no navegador nos 4 períodos de cobrança, sem alterar
nenhum valor comercial aprovado na PRD-137 e sem regressão no fluxo Asaas
(PIX/Cartão não-recorrente).
