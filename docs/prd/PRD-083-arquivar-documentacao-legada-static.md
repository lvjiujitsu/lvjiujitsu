# PRD-083: Arquivar documentação legada em static

## Summary
Avaliar e mover/remover documentos Markdown versionados em `static/documentation`, que não são fonte de verdade atual e podem ser servidos como assets públicos.

## Demand type
Governança documental + limpeza.

## Current problem
`static/documentation/` contém 12 arquivos Markdown extensos com PRDs/mapas antigos. As fontes de verdade atuais são `AGENTS.md`, `CLAUDE.md`, `docs/` e `docs/prd/`.

## Goal
Remover fonte paralela de documentação:
- arquivar em `docs/archive/` se houver valor histórico;
- remover se comprovadamente obsoleto;
- ou atualizar referência se algum documento ainda for canônico.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- inventário de `static/documentation`

### Adjacent files consulted
- `docs/`
- `docs/prd/`

### Internet / official documentation
Não aplicável.

### Context7 / MCPs / tools verified
- PowerShell e `rg`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Diagnóstico autorizado; remoção final exige confirmação se não houver prova de órfão.

## Scope
- Inventariar referências.
- Classificar cada documento.
- Mover para arquivo ou remover após decisão.

## Out of scope
- Reescrever documentação de produto.

## Impacted files
- `static/documentation/*`
- possível `docs/archive/*`

## Risks and edge cases
- Documentos podem conter contexto histórico útil.
- Manter docs em `static` pode expor informação operacional.

## Plan
- [x] `rg` por cada filename.
- [x] Matriz manter/mover/remover.
- [x] Executar decisão aprovada.

## Test plan
### Tests to author
Não aplicável (mudança documental, sem comportamento de código).

### Execution authorization
Autorizado pela solicitação atual (executar o Plan da PRD-083).

### Execution evidence
- `rg -l --hidden -g '!.git' -g '!static/documentation/*' "<filename>" .` para cada um dos 12 arquivos: nenhuma ocorrência fora de `static/documentation/` para nenhum dos nomes de arquivo. Resultado: todos órfãos (sem referência em código, templates, docs ou settings).
- `rg -l --hidden -g '!.git' "static/documentation|documentation/" .` antes da movimentação: só retornou `docs/prd/PRD-076-...md` e `docs/prd/PRD-083-...md` (auditoria/PRD que descrevem o achado, não consumo real).
- Inspeção de conteúdo (`Documento_Go_Live_e_Hardening_LV_JIU_JITSU.md` e outros): citam `pytest`, modelo `AuditLog`, módulo `PDV` e variável `CRITICAL_EXPORT_CONTROL_FILE`. `rg -l "class AuditLog|class PDV|CRITICAL_EXPORT_CONTROL_FILE" system/` não encontrou nenhuma ocorrência no código atual — confirma que os 12 documentos descrevem uma fase anterior do sistema, hoje obsoleta.
- Após `git mv` dos 12 arquivos: `rg -l --hidden -g '!.git' "static/documentation" .` voltou a retornar apenas os dois PRDs de auditoria (esperado, é o registro histórico da decisão).
- `git diff --check` → saída sem erros de whitespace nas linhas adicionadas pelo rename (apenas avisos de LF/CRLF pré-existentes em arquivos não tocados por esta tarefa).

## Visual validation
Não aplicável.

## ORM validation
Não aplicável.

## Quality validation
- `rg` referências antes/depois.
- `git diff --check`.

## Evidence
- Subagente identificou 12 `.md` em `static/documentation` com 5.415 linhas.

## Implemented
- Classificação dos 12 arquivos de `static/documentation/`: todos órfãos (sem referência em código, templates, settings ou outros docs além da própria trilha de auditoria PRD-076/PRD-083) e todos descrevendo uma fase anterior do produto (citam `pytest`, `AuditLog`, `PDV`, `CRITICAL_EXPORT_CONTROL_FILE` — nenhum existe no código atual).
- Decisão: arquivar (não remover), por valor histórico potencial e por estarem hoje sendo servidos como asset público dentro de `static/`, o que era o risco identificado na PRD.
- Movidos via `git mv` os 12 arquivos de `static/documentation/` para `docs/archive/static-documentation-legacy/`, preservando histórico de arquivo no git:
  - `Documento_Arquitetura_App_System_LV_JIU_JITSU.md`
  - `Documento_Estrategia_de_Testes_e_Gates_LV_JIU_JITSU.md`
  - `Documento_Fluxos_Criticos_e_Fontes_de_Verdade_LV_JIU_JITSU.md`
  - `Documento_Go_Live_e_Hardening_LV_JIU_JITSU.md`
  - `Documento_Mapeamento_Modulos_System_LV_JIU_JITSU.md`
  - `Documento_Stripe_Implementacao_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Forms_Serializers_LV_JIU_JITSU_v5.md`
  - `Documento_Unico_Mapeamento_Models_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Templates_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Views_LV_JIU_JITSU.md`
  - `PRD_Implementacao_Completa_LV_JIU_JITSU.md`
  - `PRD_implementacao_FINAL_LV_JIU_JITSU.md`
- `static/documentation/` ficou vazio (diretório removido implicitamente, git não versiona diretório vazio).

## Cleanup findings
- Nenhum resíduo de código aponta para `static/documentation/`; nenhuma rota Django serve esse caminho explicitamente (era servido apenas como estático genérico via `staticfiles`/`static/`).
- Nenhuma duplicação criada: os arquivos movidos não colidem com nomes já existentes em `docs/` ou `docs/archive/`.

## Follow-up PRDs
Nenhum follow-up identificado no escopo desta PRD. Não há necessidade de nova PRD; a movimentação encerra o achado da PRD-076 relativo a `static/documentation`.

## Deviations from plan
- O Plan original não especificava o destino exato dentro de `docs/archive/`; foi criado o subdiretório `docs/archive/static-documentation-legacy/` para isolar este lote de documentos legados sem misturar com outros arquivos de `docs/archive/` futuros.

## Pending
- Nenhuma pendência técnica. Recomenda-se ao proprietário revisar se algum dos 12 documentos arquivados ainda tem valor de referência para decidir descarte definitivo em ciclo futuro (fora do escopo desta PRD, que exigia apenas tirar a fonte paralela de `static/`).

## Final status
Concluída.
