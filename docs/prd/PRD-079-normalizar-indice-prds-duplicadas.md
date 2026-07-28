# PRD-079: Normalizar índice de PRDs duplicadas

## Summary
Restaurar rastreabilidade das PRDs. O diretório `docs/prd/` possui números duplicados, contrariando o padrão que exige `PRD-<NNN>` único.

## Demand type
Governança documental.

## Current problem
Há PRDs duplicadas pelos números 008, 009, 014, 015, 016, 021 e 028. Isso impede usar o número como identificador confiável de mudança.

## Goal
Criar índice canônico das PRDs, registrar duplicatas e decidir sem perda de histórico:
- renumerar documentos duplicados;
- arquivar documentos substituídos;
- ou criar aliases explícitos.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- amostras recentes de PRDs

### Adjacent files consulted
- Listagem completa de `docs/prd/PRD-*.md`

### Internet / official documentation
Não aplicável.

### Context7 / MCPs / tools verified
- PowerShell e `rg`.

### Limitations found
- Renumerar PRDs pode quebrar referências internas; exige busca e atualização controlada.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual de corrigir governança.

## Scope
- Gerar índice `docs/prd/README.md` ou equivalente.
- Identificar duplicatas e referências.
- Corrigir nomes e links quando aprovado.
- Atualizar `docs/PRD-STANDARD.md` se necessário com regra de índice.

## Out of scope
- Alterar comportamento de código.

## Impacted files
- `docs/prd/*`
- `docs/PRD-STANDARD.md`

## Risks and edge cases
- PRDs duplicadas antigas podem ser referenciadas em outras PRDs.
- Git history preserva renames, mas links Markdown precisam ser atualizados.

## Plan
- [x] Criar inventário número -> arquivos.
- [x] Marcar canônica/substituída.
- [x] Propor renumeração.
- [x] Executar renames e atualizar referências.
- [x] Validar sem duplicatas.

## Test plan
### Tests to author
Não aplicável.

### Execution authorization
Renomeação documental autorizada somente após matriz de impacto.

### Execution evidence
- `ls docs/prd | grep -oE "^PRD-[0-9]+" | sort | uniq -d` antes da execução: confirmou duplicatas em `008`, `009`, `014` (havia também `PRD-014-wizard-ui-fixes.md` não citado na auditoria original), `015`, `016`, `021`, `028`.
- `git mv` para cada arquivo duplicado renomeado, preservando histórico (status `R` no `git status --short`).
- `head -1` em cada arquivo renomeado confirmou que o título `# PRD-<NNN>:` foi atualizado para o novo número.
- `rg`/`grep -rln` por nome de arquivo antigo em todo o repositório (exceto `.git/`) após o rename: nenhuma ocorrência restante.
- `grep -n "PRD-NNN"` dentro de cada arquivo renomeado para detectar autorreferência: encontrada e corrigida uma autorreferência obsoleta em `docs/prd/PRD-087-remover-inicial-seed.md` (apontava para `PRD-016-remover-inicial-seed.md`).
- Referências externas corrigidas: `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` (apontava para `PRD-021-revisao-fluxo-cadastro.md`, agora `PRD-088`) e `docs/prd/PRD-050-modulo-planos-admin.md` (apontava para `PRD-028-crud-planos-precificacao-dinamica.md`, agora `PRD-089`).
- `ls docs/prd/*.md | xargs -n1 basename | grep -oE "^PRD-[0-9]+" | sort | uniq -d` após a execução: vazio (sem duplicatas).
- `grep -rohE "docs/prd/PRD-[0-9]+-[a-z0-9-]+\.md"` em todo `*.md` do repo, checando existência de cada arquivo referenciado: únicas ausências são `PRD-105`, `PRD-106`, `PRD-107`, `PRD-110`, `PRD-116`, `PRD-117`, todas citadas explicitamente como referências externas (fora do escopo desta PRD).
- Criado `docs/prd/README.md` com tabela completa das 90 PRDs (arquivo + título) e seção explicando a renumeração de duplicatas.
- Atualizado `docs/PRD-STANDARD.md` com regra de consultar o índice antes de escolher o próximo número.

## Visual validation
Não aplicável.

## ORM validation
Não aplicável.

## Quality validation
- `rg` por nomes antigos.
- script/check local de duplicatas.

## Evidence
- Subagente encontrou duplicatas: 008, 009, 014, 015, 016, 021 e 028.

## Implemented
- Criado `docs/prd/README.md` como índice canônico (90 PRDs, arquivo + título), com seção dedicada explicando a renumeração desta PRD.
- Renomeados via `git mv` (sem perda de histórico) os 7 arquivos duplicados:
  - `PRD-008-consolidar-landing-remover-paginas-publicas.md` → `PRD-022-consolidar-landing-remover-paginas-publicas.md`
  - `PRD-009-checkin-com-aprovacao-do-professor.md` → `PRD-055-checkin-com-aprovacao-do-professor.md`
  - `PRD-014-wizard-ui-fixes.md` → `PRD-090-wizard-ui-fixes.md`
  - `PRD-015-repasses-sem-saque-antecipado.md` → `PRD-086-repasses-sem-saque-antecipado.md`
  - `PRD-016-remover-inicial-seed.md` → `PRD-087-remover-inicial-seed.md`
  - `PRD-021-revisao-fluxo-cadastro.md` → `PRD-088-revisao-fluxo-cadastro.md`
  - `PRD-028-crud-planos-precificacao-dinamica.md` → `PRD-089-crud-planos-precificacao-dinamica.md`
- Atualizado o título `# PRD-<NNN>:` interno de cada arquivo renomeado.
- Corrigida autorreferência obsoleta em `docs/prd/PRD-087-remover-inicial-seed.md`.
- Atualizadas referências cruzadas em `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` e `docs/prd/PRD-050-modulo-planos-admin.md` para os novos nomes/números.
- Atualizado `docs/PRD-STANDARD.md` com a regra de consultar `docs/prd/README.md` ao escolher o próximo número e de manter o índice atualizado.

## Cleanup findings
- A auditoria original do PRD-079 listava apenas os números duplicados (`008, 009, 014, 015, 016, 021, 028`), mas o caso `014` continha **dois** pares de arquivos coincidindo no mesmo número, não citados separadamente — corrigido como parte desta execução.
- Os gaps de numeração `022` e `055` (nunca usados) foram identificados e reaproveitados para renumeração antes de abrir números novos no final da sequência (evita inflar a faixa numérica desnecessariamente).
- Referências bare (`PRD-008`, `PRD-009` sem nome de arquivo) em `docs/prd/PRD-007-reformular-planos-precificacao-elegibilidade.md` e `docs/prd/PRD-019-troca-plano-padrao-plan-selector.md` foram revisadas; apontam coerentemente para os arquivos que permaneceram nos números originais (008-ajustar-paineis e 009-loja-portal), então não exigiram alteração.
- Não foi aberto follow-up PRD: o escopo desta PRD já cobre a normalização completa solicitada.

## Follow-up PRDs
Nenhum aberto. Trabalho concluído dentro do escopo desta PRD.

## Deviations from plan
- O Plan original previa "marcar canônica/substituída" e "propor renumeração" como etapas distintas de aprovação prévia antes de executar; como a auditoria já havia mapeado as duplicatas e a tarefa solicitada autorizou explicitamente a execução completa ("renomeie/anexe sufixo e atualize referências internas via rg antes de finalizar"), análise, decisão e execução foram feitas em uma única passada, documentadas nesta seção e na de Implemented.
- Identificado e corrigido um caso de duplicata adicional (`PRD-014-wizard-ui-fixes.md`) não listado na auditoria original do Context Ledger.

## Pending
Nenhuma pendência. Todos os itens do Plan foram executados e validados via `rg`/`grep` conforme Test plan.

## Final status
Concluída.
