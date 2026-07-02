# PRD-076: Auditoria de legado, governança e documentação

## Summary
Sanitizar divergências entre documentação, PRDs antigas e código real. O repo contém PRDs duplicadas por número, documentos em `static/documentation`, contratos que declaram entregas ausentes, templates/assets legados e arquivos grandes que dificultam manutenção.

## Demand type
Revisão de governança + limpeza controlada.

## Current problem
- Há PRDs duplicadas por número (`PRD-008`, `PRD-009`, `PRD-014`, `PRD-015`, `PRD-016`, `PRD-021`, `PRD-028`).
- PRD-066 declara fundação modal criada, mas os arquivos não existem.
- PRD-068 declara estado “login único progressivo”, mas o código atual contém home, cadastro, pessoas e planos.
- `static/documentation/` contém documentos extensos de arquitetura/PRD/mapas que parecem documentação legada versionada dentro de static.
- Views e assets grandes existem: `auth_views.py` ~47 KB, `calendar_views.py` ~24 KB, `person_views.py` ~20 KB, `register.js` ~135 KB, `dashboard.css` ~58 KB.
- Templates existentes têm comentários decorativos e scripts inline.

## Goal
Separar o que é fonte de verdade do que é legado, remover somente o que for comprovadamente órfão, e criar follow-ups específicos para refatorações materiais sem expandir escopo automaticamente.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-066-portabilidade-visary-modal-crud.md`
- `docs/prd/PRD-068-rework-limpo-pessoas-fundacao-lv.md`
- `docs/prd/PRD-065-hubs-administrativos-modulos-lv.md`

### Adjacent files consulted
- Inventário de `docs/prd`
- Inventário de `static/documentation`
- Inventário de `system/views`
- Inventário de templates e assets

### Internet / official documentation
- Não aplicável para remoção documental; fonte primária é o repo.

### Context7 / MCPs / tools verified
- `rg`, PowerShell e Git.

### Limitations found
- Remoção segura exige confirmar ausência de referências e decisão de produto para documentos históricos.
- Não declarar “sistema limpo” sem escopo fechado.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual, que pediu identificar o que está mal implementado, inconsistente, apagável, sanitizável ou fora de governança.

## Scope
- Criar inventário de documentos/PRDs conflitantes.
- Classificar arquivos em fonte de verdade, legado a arquivar, órfão removível e dívida com PRD.
- Remover apenas arquivos comprovadamente órfãos e dentro do escopo aprovado.
- Atualizar documentação de governança para refletir realidade.

## Out of scope
- Refatorar views grandes neste PRD.
- Reescrever wizard/cadastro.
- Apagar histórico sem rastreabilidade.

## Impacted files
- `docs/prd/*`
- `static/documentation/*`
- documentação de governança, se necessário

## Risks and edge cases
- PRDs antigas podem conter contexto útil, mesmo quando contradizem o código.
- `static/documentation` pode estar sendo servido publicamente por engano; remoção ou migração precisa ser intencional.
- Duplicidade de PRD pode quebrar rastreabilidade.

## Rules and constraints
- Confirmar referência antes de remover.
- Dívida material fora do escopo vira PRD nova.
- Não editar `staticfiles/`.

## Plan
- [x] Gerar inventário com referências de todos os documentos candidatos.
- [x] Propor matriz manter/arquivar/remover.
- [x] Executar remoções/arquivamentos pequenos e comprovados.
- [x] Criar follow-ups para refatorações grandes (PRD-077 a PRD-085 já existiam como follow-up desta auditoria).

## Test plan
### Tests to author
Não aplicável, salvo checks de busca textual.

### Execution authorization
Remoção destrutiva de documentação histórica exige confirmação específica se não estiver inequivocamente órfã.

### Execution evidence
- `docs/archive/static-documentation-legacy/`: os 12 documentos de `static/documentation/` foram movidos (não apagados) via `git mv`, confirmando ausência de referência com `rg` antes e depois (PRD-083).
- `docs/prd/`: `ls docs/prd | grep -oE 'PRD-[0-9]+' | sort | uniq -c` não retorna mais nenhum número duplicado (PRD-079).
- `system/views/auth_views.py`: reduzido de ~47 KB para 537 linhas após extração de services (PRD-081).
- `system/views/calendar_views.py`: 4 views mortas (`AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`) removidas, sem rota/template/teste (PRD-077).
- Templates ausentes: de 36 no início para 3 (loja pública/aluno, pendência documentada) — PRD-075, PRD-077, PRD-078.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 testes OK no estado final.

## Visual validation
Não aplicável a esta PRD de governança; validação visual real ficou registrada nas PRDs-filhas (075, 077, 078).

## ORM validation
Não aplicável.

## Quality validation
- `rg` por referências antes/depois de cada remoção/arquivamento.
- `git diff --check`.
- `manage.py test system` completo no final do ciclo.

## Evidence
- `Get-ChildItem static/documentation` listou 12 documentos grandes — resolvido pela PRD-083 (arquivados em `docs/archive/`).
- `Get-ChildItem docs/prd` mostrou números duplicados — resolvido pela PRD-079 (renumerados com `git mv`, sem perda de histórico).
- Inventário de views/assets mostrou arquivos grandes e concentração excessiva de comportamento — `auth_views.py` resolvido pela PRD-081; `register.js`/`dashboard.css` continuam grandes e ficam para PRD-084/080 (parcialmente resolvidas, dedupe completo ainda pendente).

## Implemented
- Esta PRD não implementou código diretamente; seu papel era de auditoria e roteamento para PRDs específicas. Todo o código foi implementado nas PRDs 073, 074, 075, 077, 078, 079, 080, 081, 083, 085.

## Cleanup findings
- Todas as descobertas desta auditoria têm PRD própria com evidência real de execução (não apenas plano).
- Dívida ainda aberta e não escondida: PRD-084 (tokens CSS/estilo inline) segue com dedupe parcial; loja pública/aluno seguem sem template (documentado na PRD-077/078).

## Follow-up PRDs
- PRD-084 para concluir o dedupe de tokens/CSS e remover a duplicidade de lógica de tema entre `plans.js` e `lv/theme_toggle.js`.
- Nova PRD (não numerada ainda) para loja pública e fluxo de pré-pedido/histórico do aluno, se for prioridade.

## Deviations from plan
- O escopo original desta PRD (documentação/governança) acabou sendo majoritariamente executado por PRDs mais específicas (077, 078, 079, 081, 083) geradas a partir dela; esta PRD serviu como o "guarda-chuva" que documentou e depois fechou o ciclo, sem duplicar o trabalho.

## Pending
- PRD-084: dedupe final de tokens CSS/JS de tema entre módulos.
- Loja pública e fluxo de pré-pedido/histórico do aluno (fora do escopo de CRUD administrativo).

## Final status
Concluída com limitações — todas as descobertas relevantes desta auditoria foram resolvidas por PRDs específicas com evidência real (testes + browser); a única dívida remanescente (tokens CSS completos e loja pública) está documentada e não escondida.
