# Padrão de PRD

Toda mudança relevante usa `docs/prd/PRD-<NNN>-<slug>.md`.

## 1. Regras

- O número vem de `docs/prd/README.md`, o índice canônico, não de `ls` — a
  listagem não revela gap reservado nem número duplicado. Ao criar ou fechar
  uma PRD, regenerar o índice no mesmo passo com
  `python scripts/build_prd_index.py`, que recusa colisão de número.
- Criar antes do código e registrar a autorização em `Understanding approved`;
  ordem explícita do operador autoriza o escopo descrito.
- Usar critérios comportamentais e verificáveis.
- Declarar as skills requeridas.
- Usar Context7 quando houver biblioteca, framework, SDK, API ou CLI, e
  registrar ao menos uma fonte oficial externa relevante.
- Separar teste escrito de teste executado.
- Manter checkbox desmarcado até existir evidência; inferência não fecha
  critério.
- Atualizar `Implemented`, `Evidence`, `Cleanup findings`,
  `Deviations from plan`, `Pending` e `Final status` **durante** a execução.
- Guardar log de sessão na PRD; contratos contêm apenas fato estável.

## 2. Skills

Selecionar:

| Demanda | Skill |
|---|---|
| Toda mudança | `lv-task-intake` |
| PRD | `lv-prd` |
| Django | `lv-django-delivery` |
| UI | `lv-ui-delivery` |
| Fechamento | `lv-cleanup-audit` |
| Gerar prompt de execução | `lv-prompt-builder` (invocação manual) |
| Auditoria de coerência | `lv-parity-audit` (invocação manual) |

## 3. Template

```md
# PRD-<NNN>: <Título>

## Summary
## Demand type
## Current problem
## Goal

## Context Ledger
### Files read in full
### Adjacent files consulted
### Internet / official documentation
- [Fonte](https://...)
### Context7 / MCPs / tools verified
### Limitations found

## Required skills
- `lv-task-intake`
- `lv-prd`
- <skills específicas>
- `lv-cleanup-audit`

## Understanding approved
- Summary presented:
- User approval:
- Date:

## Execution prompt
### Persona
### Action
### Context
### Constraints
### Acceptance criteria
- [ ] When X, the system must Y.
### Expected evidence
### Output format

## Scope
## Out of scope
## Impacted files
## Risks and edge cases
## Rules and constraints

## Plan
- [ ] Context and research
- [ ] Test authored first, when applicable
- [ ] Implementation
- [ ] Refactor
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan
### Tests to author
### Execution authorization
- Status: not requested | requested | authorized | denied
### Execution evidence

## Visual validation
### Design approval
### Routes and states
### Desktop
### Mobile
### Console and terminal
### Screenshot / snapshot

## ORM validation
### Read-only checks
### Mutating checks and authorization

## Quality validation
## Evidence
## Implemented
## Cleanup findings
## Follow-up PRDs
## Deviations from plan
## Pending
## Final status
```

Seção que não se aplica à mudança é preenchida com "Não aplicável" e o motivo,
nunca apagada — a ausência da seção não distingue "não se aplica" de
"esqueci".

## 4. UI adicional

PRD de UI inclui:

```md
## Visual hierarchy
## Wireframe
## State machine
```

Critérios mínimos:

- hierarquia e agrupamento;
- affordance e feedback;
- estados `disabled`, `loading`, `error` e `success`;
- erro por campo;
- desktop e mobile;
- tema claro e escuro;
- permissões reais;
- comportamento preservado;
- console sem erro crítico.

## 5. Evidência

Evidência válida:

- comando e saída;
- teste executado e resultado;
- screenshot ou snapshot;
- console e terminal;
- ORM;
- link oficial;
- diff verificável.

"Implementado" não significa "validado": sem execução observável, o item vai
para `Pending`, não para `Evidence`.

## 6. Follow-up

Dívida material fora do escopo vira PRD de follow-up com número reservado em
`docs/prd/README.md`, e não é implementada sem autorização. Ampliar escopo sem
registro é tão ruim quanto deixar a dívida.
