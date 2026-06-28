# PRD-064: Wizard público — consolidação da máquina de estados, re-hidratação autoritativa e continuidade pós-pagamento

## Summary

Consolidar a máquina de estados do wizard público (`/register/`, `static/system/js/auth/register.js`) para eliminar a classe de bugs que os PRD-056 e PRD-057 trataram pontualmente: `state.stepSequence` e `state.classSelections` vazios após limpeza do `sessionStorage`, múltiplos steps visíveis simultaneamente e navegação retroativa inconsistente pós-pagamento. Adapta ao LV o princípio de continuidade e retorno à origem que o Visary consolidou no PRD-117 (cadeia multi-etapas que preserva contexto e volta ao ponto de início), aplicado aqui à máquina de passos de página única — não a modais aninhados.

## Demand type

Correção arquitetural de front-end (consolidação de máquina de estados) + UI. Sem alteração de regra de negócio no backend.

## Current problem

- `register.js` deriva `state.stepSequence` no cliente; quando o `sessionStorage` é limpo (entrada em `showPlanPaidMode` ou `PreRegistration` removida), a sequência fica vazia e a visibilidade de steps deixa de ser confiável.
- `step-profile` é visível por padrão no template (sem `hidden`); `showPlanPaidMode()` só oculta steps presentes em `stepSequence`, então com sequência vazia dois steps aparecem juntos (causa raiz do PRD-057).
- `state.classSelections` não é restaurado a partir dos dados iniciais renderizados pelo Django, exibindo "turma desmarcada" pós-pagamento (causa raiz do PRD-056).
- PRD-056 e PRD-057 corrigiram sintomas específicos, mas a fonte de verdade da sequência e da seleção continua sendo o estado do cliente, sem re-hidratação autoritativa a partir do servidor.
- Não há invariante explícito "exatamente um step visível" nem máquina de estados pós-pagamento documentada (estados: pré-pagamento, retorno do gateway, pago, materiais, revisão, finalização).

## Goal

1. Tornar a re-hidratação a partir dos dados iniciais renderizados pelo Django a fonte autoritativa de `stepSequence` e `classSelections` sempre que o `sessionStorage` estiver ausente ou inconsistente.
2. Garantir o invariante "exatamente um step visível", inclusive quando a sequência ainda não foi derivada (incluindo `step-profile`).
3. Formalizar a máquina de estados pós-pagamento e a continuidade: ao concluir/cancelar uma etapa, o usuário permanece no fluxo correto sem regressão a um step pago.
4. Não reintroduzir o código de desenvolvimento removido no PRD-057.
5. Validar por UI desktop/mobile, console limpo e os cenários dos PRD-056/057 como regressão.

## Context Ledger

### Files read in full

- `static/system/js/auth/register.js` (estrutura de `state`, derivação de sequência, `showPlanPaidMode`, navegação)
- `docs/prd/PRD-056-wizard-pos-pagamento-navegacao-e-re-hidratacao.md`
- `docs/prd/PRD-057-simplificacao-wizard-correcao-estados.md`

### Adjacent files consulted

- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/wizard-step-plan-aluno-titular.md`, `docs/wizard-step-plan-aluno-com-dependente.md`, `docs/wizard-step-plan-responsavel-com-aluno.md`
- template do wizard em `templates/login/` (steps e atributo `hidden`)
- `docs/UI-SCREEN-CONTRACT.md`
- Visary `docs/prd/PRD-117-fluxo-encadeado-sobre-home-clientes.md` (princípio de continuidade/retorno à origem)

### Internet / official documentation

- [MDN — Window.sessionStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage)
- [MDN — History API / popstate](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [MDN — hidden attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/hidden)

### Context7 / MCPs / tools verified

- Não há biblioteca externa nova; `register.js` é vanilla JS. Context7 não obrigatório, salvo dúvida sobre API de browser.
- Browser interno disponível em `http://127.0.0.1:8000` para validação e regressão.
- PowerShell, Git e `rg` disponíveis.

### Limitations found

- O fluxo Asaas pós-pagamento exige túnel/ambiente HG para o retorno real; cenários podem ser reproduzidos via parâmetro `post_plan_payment_complete` no ambiente local conforme PRD-056.
- `register.js` é extenso (3059 linhas); a consolidação deve ser cirúrgica, sem reescrever o wizard.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: consolidar a máquina de estados do wizard e a re-hidratação autoritativa, adaptando o princípio de continuidade do PRD-117 do Visary.
- User approval: solicitação explícita de PRDs completos para implementação sequencial.
- Date: 2026-06-28.

## Execution prompt

### Persona

Engenheiro de front-end responsável pela máquina de estados do wizard público do LV.

### Action

Tornar a re-hidratação autoritativa, impor o invariante de step único, formalizar a máquina pós-pagamento e validar regressões, com proposta de UI aprovada antes do código.

### Context

Wizard de página única em `register.js`, com steps controlados por `hidden` e estado em `sessionStorage`. Pagamento ocorre antes da criação de `Person` (PRD-040).

### Constraints

- Não reescrever o wizard; mudança cirúrgica.
- Não reintroduzir código de desenvolvimento (DevLoad/autofill).
- Não alterar regra de negócio do backend.
- Atualizar `?v=` do asset versionado ao alterar `register.js`.
- UI exige proposta aprovada antes do código.

### Acceptance criteria

- [ ] Com `sessionStorage` vazio e dados Django presentes, `stepSequence` e `classSelections` são re-hidratados corretamente.
- [x] Em qualquer estado validado, exatamente um step fica visível (incluindo `step-profile`).
- [ ] Pós-pagamento, o usuário não regride a um step já pago e a turma aparece marcada.
- [x] Máquina de estados pós-pagamento documentada e refletida no código.
- [ ] Cenários dos PRD-056 e PRD-057 passam como regressão por UI.
- [x] Nenhum código de desenvolvimento reintroduzido.

### Expected evidence

- Screenshots dos estados-chave (pré-pagamento, retorno do gateway, pago, materiais, revisão) em desktop e mobile.
- Console sem erro.
- Diff cirúrgico de `register.js` e do template, com `?v=` atualizado.

### Output format

Resumo curto, máquina de estados, evidências, limitações e status.

## Visual hierarchy

- Cabeçalho do wizard com progresso (`wizard-step-current`/`wizard-step-total`).
- Um único cartão de step visível por vez.
- Ações primárias: Avançar/Voltar/Finalizar conforme o estado; Voltar desabilitado em estados pós-pagamento.

## Wireframe

A definir na proposta de design aprovada. Reusar o layout atual do wizard; a mudança é de comportamento de visibilidade e navegação, não de redesenho visual.

## State machine

Estados: `profile` → `dados/saúde/arte/dependentes/turmas` → `plan` → `gateway-return` → `plan-paid` → `products` → `review` → `finalize`. Transições retroativas bloqueadas a partir de `plan-paid`. Cada transição garante step único visível e estado re-hidratado.

## Scope

- `static/system/js/auth/register.js`
- template do wizard em `templates/login/` (atributo `hidden` e marcação de steps)
- versão do asset (`?v=`)
- este PRD.

## Out of scope

- Redesenho visual do wizard.
- Backend de pagamento e criação de `Person`.
- Steps de materiais/cupom além do necessário para o invariante.

## Impacted files

- `static/system/js/auth/register.js`
- template do wizard
- referência `?v=` no template que carrega o asset
- este PRD.

## Risks and edge cases

- Re-hidratação parcial pode marcar turma errada se o mapeamento Django→`classSelections` não cobrir todos os perfis (titular, dependente, responsável).
- `popstate`/botão físico do navegador pode burlar o bloqueio de Voltar.
- Sequências com múltiplos `step-classes`/`step-dep` exigem reconstrução fiel.
- `sessionStorage` corrompido (parcial) é pior que vazio; tratar como inconsistente e re-hidratar.

## Rules and constraints

- Menor mudança correta; causa raiz, não sintoma.
- Sem regra de negócio central em JS.
- Sem `innerHTML` com dado do usuário.
- Atualizar `?v=`.

## Plan

- [x] Context and research
- [x] Proposta de UI/estado aprovada
- [x] Re-hidratação autoritativa a partir do Django
- [x] Invariante de step único
- [x] Máquina de estados pós-pagamento
- [ ] Validação por UI e regressão 056/057
- [x] Cleanup audit (sem DevLoad)
- [x] Documentation

## Test plan

### Tests to author

- Testes Django são limitados para JS de cliente; priorizar validação por browser. Se houver lógica server-side de re-hidratação (contexto inicial), cobrir o contexto renderizado por teste de view.

### Execution authorization

- Status: não autorizada nesta execução. Testes server-side escritos, não executados por política.

### Execution evidence

Teste escrito, não executado por política. Não há declaração de Red/Green.

## Visual validation

- Browser interno em `http://localhost:8000/register/`, desktop `1365x900`: `register.js?v=36`, sentinel ausente, `visibleSteps=["step-profile"]`, progresso `1 de 11`.
- Browser interno em `http://localhost:8000/register/`, mobile `390x844`: `visibleSteps=["step-profile"]`, `bodyScrollWidth=390`, `viewportWidth=390`, console errors `[]`.
- Screenshots desktop/mobile capturados no navegador interno durante a validação.
- Retorno pós-pagamento real não reproduzido porque exige sessão com pré-cadastro/pagamento pendente; não foi criada mutação local sem autorização.

## ORM validation

Não aplicável (sem mutação de dados nesta mudança).

## Quality validation

- `manage.py check`.
- `node --check static/system/js/auth/register.js`.
- Revisão do diff e da máquina de estados.
- `git diff --check`.

## Evidence

- `node --check static/system/js/auth/register.js` retornou exit code 0.
- `python manage.py check` retornou `System check identified no issues (0 silenced).`
- `python -m py_compile system/tests/test_person_delete.py system/tests/test_register_wizard_contract.py` retornou exit code 0.
- Browser interno desktop: um único step visível (`step-profile`), asset `register.js?v=36`, sentinel ausente.
- Browser interno mobile: um único step visível (`step-profile`), sem overflow horizontal e console errors `[]`.
- `system/tests/test_register_wizard_contract.py` criado para contrato de template/JS e `pending_person_json`, não executado por política.

## Implemented

- `pending_person_json` agora inclui `class_group_ids` e `class_group_name` para titular, alunos/dependentes e dependentes adicionais no snapshot de `PreRegistration`.
- `register.js` ganhou `showOnlyWizardStep()` e passou a ocultar todos os `.wizard-step` antes de exibir o destino.
- `register.js` ganhou `rehydratePendingWizardState()` para reconstruir perfil, contagem, dependentes e `classSelections` a partir do JSON Django.
- Inicialização sem `sessionStorage` preserva o snapshot de hidden inputs antes de chamar `selectProfile()` e reidrata turmas de titular, dependente, responsável e extras.
- Estados pós-pagamento escondem o botão Voltar do cabeçalho para evitar regressão a etapa já paga.
- `templates/login/register.html` removeu `SENTINEL_TEST_XZ99` e atualizou o asset para `register.js?v=36`.

## Cleanup findings

- Nenhum código `DevLoad`/autofill foi adicionado.
- Nenhuma regra de negócio de pagamento, plano ou criação de `Person` foi alterada.
- Nenhuma mutation de banco foi executada.

## Follow-up PRDs

Nenhum previsto.

## Deviations from plan

- A validação visual cobriu a tela pública inicial em desktop/mobile, mas não reproduziu sessão real pós-pagamento por falta de autorização para criar/usar pré-cadastro de teste.
- Testes escritos não foram executados por política.

## Pending

- Autorização para executar `system.tests.test_register_wizard_contract`.
- Autorização para criar um pré-cadastro de teste com aluno normal e aluno com dependente e validar retorno pós-pagamento/material/revisão no browser.

## Final status

**Concluída com limitações** — implementação, checagens e validação visual inicial concluídas; regressão pós-pagamento real e testes automatizados permanecem pendentes por política de autorização.
