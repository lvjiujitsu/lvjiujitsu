# PRD-061: Alinhamento de governança — workflow e adaptadores

## Summary

Trazer para o LV JIU JITSU as evoluções de governança ainda não absorvidas, sem copiar domínio de consultoria de vistos: o checklist de leitura Django completo em `docs/AGENT-WORKFLOW.md` e os blocos de Context7, escada de prioridade de browser e sincronização explícita de skills em `docs/PLATFORM-ADAPTERS.md`.

## Demand type

Revisão de governança + regeneração documental. Sem alteração de código funcional.

## Current problem

- `docs/AGENT-WORKFLOW.md` do LV está condensado: resume a leitura Django numa única linha e não inclui `signals`, `tasks` e `management commands` explicitamente, nem a âncora "busca textual serve para localizar, não para substituir leitura".
- `docs/PLATFORM-ADAPTERS.md` do LV não traz três blocos necessários:
  1. **Context7 obrigatório** com a lista de gatilhos (biblioteca, framework, SDK, API, CLI, config);
  2. **Escada de prioridade de browser** em quatro níveis (interno → sessão autenticada → Playwright MCP → relatório de limitação);
  3. **Sincronização de skills** com paths explícitos (`.claude/skills/...`, `.cursor/skills/...`) e verificação por hash/conteúdo.
- A LV usa um bootstrap de governança, mas não registra onde vive a fonte canônica dele, o que facilita divergência futura.

## Goal

1. Expandir `docs/AGENT-WORKFLOW.md` para o checklist Django completo e a âncora de leitura.
2. Adicionar a `docs/PLATFORM-ADAPTERS.md` os blocos de Context7, escada de browser e sincronização explícita, mantendo os nomes de skills do LV (`lv-*`).
3. Registrar em `CLAUDE.md` onde vive o bootstrap de governança, para ressincronizações futuras.
4. Não alterar `AGENTS.md` além do necessário para manter coerência de referências.

## Context Ledger

### Files read in full

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/PRD-059-governanca-agentes-multiplataforma.md`
- `CLAUDE.md`
- `AGENTS.md`

### Adjacent files consulted

### Internet / official documentation

- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Cursor: Rules](https://cursor.com/docs/rules)
- [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Agent Skills specification](https://agentskills.io/specification)

### Context7 / MCPs / tools verified

- Mudança documental; Context7 não aplicável a conteúdo de governança.
- PowerShell, Git e `rg` disponíveis.
- Browser interno disponível, não aplicável a arquivos documentais.

### Limitations found

- Não há alteração funcional que justifique teste Django ou validação visual.
- A sincronização das skills `lv-*` em Claude/Codex/Cursor exige recarga das ferramentas após a edição.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: alinhar a governança documental do LV ao padrão canônico, sem portar domínio externo.
- User approval: solicitação explícita de PRDs completos para implementação sequencial.
- Date: 2026-06-28.

## Execution prompt

### Persona

Engenheiro de governança de agentes em monólito Django.

### Action

Editar dois documentos de governança do LV e adicionar uma referência factual no `CLAUDE.md`, preservando os fatos e nomes de skills do LV.

### Context

O LV é um monólito Django 5.2 (MVT, `services/`, `selectors/`) operados em Windows/PowerShell, Render e Supabase, com governança comum versionada.

### Constraints

- Não alterar código funcional, templates, CSS ou JS.
- Não copiar fatos de outro domínio (clientes, vistos, viagens, processos) para o LV.
- Manter os nomes de skills do LV (`lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`).
- Uma fonte de verdade por responsabilidade; conteúdo permanente curto.

### Acceptance criteria

- [x] `docs/AGENT-WORKFLOW.md` lista explicitamente models, forms, services, selectors, views, URLs, templates, CSS/JS, testes, settings, signals, tasks e management commands no checklist de leitura.
- [x] `docs/AGENT-WORKFLOW.md` inclui a âncora "busca textual serve para localizar, não para substituir leitura".
- [x] `docs/PLATFORM-ADAPTERS.md` contém bloco Context7 com gatilhos.
- [x] `docs/PLATFORM-ADAPTERS.md` contém escada de prioridade de browser em quatro níveis.
- [x] `docs/PLATFORM-ADAPTERS.md` contém bloco de sincronização com paths explícitos das três cópias de skill e verificação por hash/conteúdo.
- [x] `CLAUDE.md` referencia o bootstrap canônico.
- [x] Nenhuma referência nova a domínio de vistos foi introduzida no LV.

### Expected evidence

- Diff dos dois documentos e do `CLAUDE.md`.
- Busca textual confirmando os termos exigidos.
- Busca confirmando ausência de termos de domínio externo (cliente/visto/viagem/processo) nas fontes novas.

### Output format

Resumo curto, evidências, limitações e status.

## Scope

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `CLAUDE.md` (apenas §11)
- este PRD.

## Out of scope

- Código Django, templates, CSS, JS.
- Skills em si (conteúdo dos `SKILL.md`) — paridade de skills é o PRD-060 já existente.
- Banco, migrations, seeds, deploy, pagamentos.

## Impacted files

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `CLAUDE.md`
- este PRD.

## Risks and edge cases

- Copiar verbatim texto de outro repositório e arrastar nomes ou termos de domínio.
- Inflar os documentos além do princípio de conteúdo curto.
- Divergência entre a escada de browser documentada e as ferramentas realmente disponíveis no LV.

## Rules and constraints

- Menor mudança correta.
- Manter coerência com `AGENTS.md` e com o PRD-059.
- Não declarar validação visual para mudança documental.

## Plan

- [ ] Context and research
- [ ] Expandir `AGENT-WORKFLOW.md`
- [ ] Expandir `PLATFORM-ADAPTERS.md`
- [ ] Referenciar bootstrap canônico no `CLAUDE.md`
- [ ] Validar termos e ausência de domínio externo
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

Não aplicável.

### Execution authorization

- Status: não solicitada.

### Execution evidence

Testes Django não executados.

## Visual validation

Não aplicável. Nenhuma tela será alterada.

## ORM validation

Não aplicável.

## Quality validation

- Busca textual dos termos exigidos.
- Busca de termos de domínio externo indevidos.
- `git diff --check`.
- Revisão integral do diff.

## Evidence

- `rg -n "models, forms, services, selectors|Busca textual localiza|Context7 é obrigatório|Prioridade de validação visual|\\.claude/skills|bootstrap canônico" docs\AGENT-WORKFLOW.md docs\PLATFORM-ADAPTERS.md CLAUDE.md` confirmou os termos exigidos.
- `rg -n -i "\b(cliente|visto|vistos|viagem|viagens|processo de visto|consultoria de vistos)\b" docs\AGENT-WORKFLOW.md docs\PLATFORM-ADAPTERS.md CLAUDE.md` encontrou somente referências já existentes no LV: `GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, PRD-058 e a proibição "Não portar domínio de consultoria de vistos".
- `git diff --check -- docs/AGENT-WORKFLOW.md docs/PLATFORM-ADAPTERS.md CLAUDE.md` não reportou erro de whitespace; apenas avisos de normalização LF/CRLF.

## Implemented

- `docs/AGENT-WORKFLOW.md` recebeu a etapa de classificação, a âncora de busca textual e checklist Django ampliado com `signals`, `tasks` e `management commands`.
- `docs/PLATFORM-ADAPTERS.md` recebeu o bloco de gatilhos Context7, a prioridade de validação visual em quatro níveis e a sincronização explícita de skills entre `.agents`, `.claude` e `.cursor`.
- `CLAUDE.md` agora referencia onde vive o bootstrap canônico.

## Cleanup findings

- Nenhum resíduo funcional introduzido.
- Avisos LF/CRLF permanecem como característica do workspace no Windows.

## Follow-up PRDs

Nenhum previsto.

## Deviations from plan

Nenhum até o momento.

## Pending

- Recarregar as ferramentas para refletir governança atualizada.

## Final status

**Concluída com limitações** — mudança documental aplicada e validada por busca textual/diff; recarga das ferramentas fica fora do escopo da edição de arquivos.
