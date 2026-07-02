# Padrão de PRD

Toda mudança relevante usa `docs/prd/PRD-<NNN>-<slug>.md`.

## Regras

- Verificar o próximo número sem duplicar, usando `docs/prd/README.md` como índice canônico (não confiar apenas em `ls`, que não revela gaps reservados ou duplicatas).
- Atualizar `docs/prd/README.md` ao criar uma PRD nova.
- Criar antes do código.
- Declarar skills.
- Usar critérios comportamentais e verificáveis.
- Incluir fonte oficial externa relevante.
- Usar Context7 quando houver biblioteca, framework, SDK, API ou CLI.
- Separar teste escrito de teste executado.
- Não marcar item sem evidência.
- Atualizar implementação, evidências, limpeza, desvios, pendências e status.

## Skills

| Demanda | Skill |
|---|---|
| Toda mudança | `lv-task-intake` |
| PRD | `lv-prd` |
| Django | `lv-django-delivery` |
| UI | `lv-ui-delivery` |
| Fechamento | `lv-cleanup-audit` |

## Template

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
### Context7 / MCPs / tools verified
### Limitations found

## Required skills
## Understanding approved

## Execution prompt
### Persona
### Action
### Context
### Constraints
### Acceptance criteria
### Expected evidence
### Output format

## Scope
## Out of scope
## Impacted files
## Risks and edge cases
## Rules and constraints
## Plan

## Test plan
### Tests to author
### Execution authorization
### Execution evidence

## Visual validation
## ORM validation
## Quality validation
## Evidence
## Implemented
## Cleanup findings
## Follow-up PRDs
## Deviations from plan
## Pending
## Final status
```

## UI

PRD visual inclui:

- `## Visual hierarchy`
- `## Wireframe`
- `## State machine`
- aprovação do design;
- disabled/loading/error/success;
- erro por campo;
- desktop/mobile e temas;
- permissões;
- console e evidência visual.

## Evidência

Válidos: comando e saída, teste autorizado, screenshot, console, terminal, ORM, link oficial e diff.

“Implementado” não significa “validado”.

## Follow-up

Auditoria pode criar nova PRD para dívida material. A próxima PRD não é implementada automaticamente.
