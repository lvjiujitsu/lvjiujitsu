# PRD-084: Tokens CSS e remoção de estilo inline

## Summary
Consolidar tokens visuais e remover cores/estilos inline em templates e CSS. O contrato exige tokens e proíbe exceções visuais soltas.

## Demand type
Refatoração UI/UX + governança visual.

## Current problem
- CSS contém cores literais além dos tokens.
- Templates usam `style=`.
- Há JS inline de tema em páginas standalone.
- Pessoas, Planos, Home, Wizard e Calendário usam fundações visuais divergentes.

## Goal
Unificar o sistema visual:
- tokens em um arquivo base;
- sem `style=` em templates funcionais;
- sem tema inline duplicado;
- assets versionados corretamente.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `static/system/css/auth/register.css`
- `static/system/css/home/dashboard.css`
- `static/system/css/people/people.css`
- `static/system/css/plans/plans.css`
- templates principais existentes

### Adjacent files consulted
- PRD-075
- PRD-080

### Internet / official documentation
Não aplicável.

### Context7 / MCPs / tools verified
- PowerShell e `rg`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual.

## Scope
- Inventariar cores literais e `style=`.
- Consolidar tokens em fundação compartilhada.
- Migrar módulos por prioridade.

## Out of scope
- Redesign de produto fora dos módulos tocados.

## Impacted files
- `static/system/css/*`
- templates existentes
- `static/system/js/lv/theme.js`

## Risks and edge cases
- Alterar CSS amplo sem browser pode causar regressão visual.
- Alguns estilos inline podem ser dados dinâmicos legítimos e precisam de alternativa segura.

## Plan
- [ ] Inventário e classificação.
- [ ] Remover tema inline via PRD-075.
- [ ] Migrar CSS por módulo.
- [ ] Validar desktop/mobile/temas.

## Test plan
### Tests to author
- Testes visuais manuais por browser.
- `node --check` se JS for alterado.

### Execution authorization
Autorizada localmente.

### Execution evidence
Pendente.

## Visual validation
Obrigatória.

## ORM validation
Não aplicável.

## Quality validation
- `rg "style=|#[0-9a-fA-F]{3,8}|rgba\\("` com exceções justificadas.
- Browser interno.

## Evidence
- Subagente confirmou hardcodes em CSS e inline styles em templates.

## Implemented
Pendente.

## Cleanup findings
Pendente.

## Follow-up PRDs
Pendente.

## Deviations from plan
Pendente.

## Pending
Pendente.

## Final status
Não concluída.
