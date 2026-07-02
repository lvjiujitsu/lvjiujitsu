# PRD-104: Remoção de código morto no wizard de cadastro (onEnterCheckout)

## Summary
`static/system/js/auth/register.js` registra `onEnterCheckout()` para disparar quando `stepId === 'step-checkout'`, mas esse passo nunca existe na sequência real do wizard (`TRAILING_STEPS = ['step-plan', 'step-products', 'step-review']`). A função inteira (81 linhas) e seu único consumidor auxiliar (`getSelectedPlan()`) são inalcançáveis.

## Demand type
Limpeza de código morto (achado em reauditoria do wizard público, PRD-081 follow-up).

## Current problem
- `register.js:396` registra a chamada `if (stepId === 'step-checkout') onEnterCheckout();`, mas nenhum elemento `id="step-checkout"` existe no template nem na sequência de steps.
- `onEnterCheckout()` (linhas 1605-1685) e `getSelectedPlan()` (linhas 1600-1603) nunca executam.
- A lógica real de resumo/pagamento de checkout já foi migrada para `onEnterPlan()` e para o fluxo pós-pagamento — a função antiga ficou órfã.

## Goal
Remover o código morto sem alterar nenhum comportamento observável do wizard.

## Context Ledger
### Files read in full
- `static/system/js/auth/register.js` (trecho das linhas 1480-1690 e declaração de `TRAILING_STEPS`/dispatcher de step)

### Adjacent files consulted
- `templates/login/register.html` (confirmado: não existe `id="step-checkout"`)
- `system/tests/test_register_wizard_contract.py` (confirmado: não referencia `step-checkout` nem `onEnterCheckout`)

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"); achado de reauditoria do wizard confirmado manualmente antes da abertura desta PRD (7 dos 8 achados do agente de exploração foram descartados por serem falsos positivos ou comportamento já correto).

## Scope
- Remover `onEnterCheckout()`, `getSelectedPlan()` e a linha de dispatcher que os invoca em `register.js`.

## Out of scope
- Qualquer outra mudança no wizard (os demais 7 achados da reauditoria foram descartados por não serem bugs reais).

## Impacted files
- `static/system/js/auth/register.js`
- `templates/login/register.html` (bump do `?v=` do asset, por convenção do projeto)

## Risks and edge cases
- Nenhum: código comprovadamente inalcançável (nenhum elemento `step-checkout` existe para disparar o dispatcher).

## Rules and constraints
- Atualizar `?v=` do script conforme convenção (`CLAUDE.md` seção 2).

## Plan
- [x] Remover código morto.
- [x] Bump de versão do asset.
- [x] Suíte de testes completa.
- [x] Validação visual do wizard (fluxo feliz não regressivo).

## Test plan
### Tests to author
- Nenhum teste novo (remoção de código inalcançável não muda comportamento testável). Suíte existente (`test_register_wizard_contract.py` e afins) serve de regressão.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 346 testes OK (suíte completa, incluindo `test_register_wizard_contract.py` atualizado para `?v=38`).
- Validação ao vivo no navegador: `/register/` carrega normalmente, sem erros de console; step 1 (seleção de perfil) responde ao clique sem exceções de referência indefinida (confirmando que a remoção de `getSelectedPlan`/`onEnterCheckout`/`selectedPlanId` não introduziu quebra em `selectPlan`/`onEnterPlan`/`resolvePlanCheckoutAction`, que permanecem intactos e são os únicos caminhos reais usados pelo wizard).

## Visual validation
Wizard público percorrido no navegador interno até o step de plano/pagamento.

## ORM validation
Não aplicável (mudança client-side).

## Quality validation
- `manage.py test system` — suíte completa.

## Evidence
- Além de `onEnterCheckout()`/`getSelectedPlan()`, a variável `selectedPlanId` ficou write-only (sem leitor) após a remoção — removida na mesma limpeza por ser a mesma causa raiz (única consumidora era a função morta).

## Implemented
- `static/system/js/auth/register.js`: removidos `onEnterCheckout()`, `getSelectedPlan()`, a variável `selectedPlanId` (e suas 2 atribuições), e a linha de dispatcher `if (stepId === 'step-checkout') onEnterCheckout();`.
- `templates/login/register.html`: bump `register.js?v=37` → `?v=38`.
- `system/tests/test_register_wizard_contract.py`: assert atualizado para `?v=38`.

## Cleanup findings
- Reauditoria completa do wizard (`system/views/auth_views.py`, `register.js`, `templates/login/register.html`, services de pre-registration/checkout/validation) via agente de exploração; dos 8 achados reportados, apenas este (código morto) se confirmou como bug real após verificação manual linha a linha. Os demais 7 foram descartados:
  - Validação de CPF: normalização é determinística (`ensure_formatted_cpf`), sem divergência real.
  - Snapshot de materiais em falha de pagamento: preserva o estado do usuário corretamente (comportamento correto, não um bug).
  - Multi-plano no checkout: `validatePlan()` já bloqueia métodos de pagamento mistos antes de prosseguir — não há bug.
  - `selected_plans_payload` fora do form: é uma decisão arquitetural válida (snapshot de POST bruto para dados dinâmicos de lista, consumido por `registration_checkout.py`), não uma inconsistência quebrada.
  - Mensagem de turma ambígua, `person_type_code` vs `registration_profile`, URL de cupom hardcoded: nitpicks de baixo impacto sem evidência de bug concreto, não justificam PRD própria agora.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
_Nenhum até o momento._

## Pending
_Nenhuma até o momento._

## Final status
Concluída.
