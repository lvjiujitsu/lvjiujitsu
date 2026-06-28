# PRD-060: Paridade de governança multiplataforma + skill lv-prompt-builder

## Summary

Levar a governança do LV JIU JITSU à paridade com o padrão multiplataforma compartilhado com o Visary, sem portar fatos de domínio do Visary. Fechar duas divergências de protocolo (a seção de Classificação ausente no `docs/AGENT-WORKFLOW.md` e a falta da skill `lv-prompt-builder`) e registrar uma decisão consciente sobre `docs/UX-SCREEN-FLOWS.md`. A skill `lv-prompt-builder` transforma um problema cru no melhor execution prompt no padrão LV e para, sem implementar.

## Demand type

Revisão de governança do agente + regeneração documental + tooling de agente.

## Current problem

- O `docs/AGENT-WORKFLOW.md` do LV não tinha uma seção de Classificação; sua `§2` era "Preflight". O padrão multiplataforma (Visary) define Classificação em `§2`, e a skill de prompt builder referencia `docs/AGENT-WORKFLOW.md §2` para as categorias de demanda — a referência ficaria quebrada sem essa seção.
- Não existia a skill `lv-prompt-builder` em nenhuma das três plataformas (`.claude`, `.agents`, `.cursor`). Transformar um problema cru em execução exige montar manualmente intake, classificação, escolha de skills, leitura e gates, e as autorizações previsíveis viram pausas dispersas.
- O Visary mantém um `docs/UX-SCREEN-FLOWS.md`; o LV não tem o arquivo, gerando uma assimetria estrutural que precisava de decisão registrada.

## Goal

1. Inserir a Classificação no `docs/AGENT-WORKFLOW.md` do LV, alinhando o protocolo ao padrão e habilitando a referência `§2` da skill, sem reescrever o que já estava correto.
2. Criar `lv-prompt-builder` nas três plataformas, semanticamente idêntica, no estilo das cinco skills `lv-*` existentes.
3. Registrar a skill na tabela de `docs/PLATFORM-ADAPTERS.md`.
4. Decidir, com motivo, sobre `docs/UX-SCREEN-FLOWS.md`.
5. Documentar contexto, escopo, evidências e status neste PRD.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md` (cabeçalho e fontes de verdade)
- `.cursor/rules/protocol.mdc`
- `.claude/skills/lv-prd/SKILL.md`, `.agents/skills/lv-prd/SKILL.md`, `.cursor/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-prd/agents/openai.yaml` (e os outros quatro `openai.yaml`)
- `docs/prd/PRD-059-governanca-agentes-multiplataforma.md`
- Referência de protocolo no Visary: `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/UX-SCREEN-FLOWS.md`, `.claude/skills/visary-prompt-builder/SKILL.md`, `docs/prd/PRD-110-prompt-builder-claude.md`

### Adjacent files consulted

- inventário de `docs/prd/` (próximo número livre = 060)
- inventário de `docs/` do LV (3 docs de wizard + UI-SCREEN-CONTRACT)
- inventário de skills nas três plataformas
- `grep` de referências a `AGENT-WORKFLOW` e a seções `§N` no repositório

### Internet / official documentation

- [Claude Code: skills](https://code.claude.com/docs/en/skills) — verificada nesta sessão.

Conclusão aplicável: `name` é opcional (default = nome do diretório) e `description` é recomendado; `description` + `when_to_use` são truncados em **1.536 caracteres** na listagem; `disable-model-invocation: true` impede o disparo automático e reserva a skill para `/nome`; skills de projeto ficam em `.claude/skills/<name>/SKILL.md`. Crítico: **frontmatter YAML malformado faz o Claude Code carregar o corpo da skill com metadata vazia** — sem `description` para casar —, o que motivou colocar a `description` entre aspas (ela contém `: `).

### Context7 / MCPs / tools verified

- Context7 não aplicável: a mudança é documental/de configuração, sem biblioteca de runtime nova. A fonte de verdade é a própria ferramenta, verificada na documentação oficial.
- PyYAML disponível via `.venv` do Visary (o LV não instala PyYAML por padrão; mesmo arranjo registrado no PRD-059).
- PowerShell, Git, `rg` e `sha256sum` disponíveis.

### Limitations found

- A descoberta runtime das skills em Claude e Cursor exige recarga das ferramentas; a execução ponta a ponta de `/lv-prompt-builder` não foi exercitada nesta sessão.
- A mudança é documental/de configuração: não há comportamento de aplicação testável, UI ou persistência.
- `.claude/settings.local.json` aparece modificado por alteração preexistente do usuário; foi preservado e está fora do escopo.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de paridade + criação da skill nas três plataformas + decisão sobre UX-SCREEN-FLOWS + PRD.
- User approval: ordem explícita de implementação, com autorizações concedidas para criar/editar governança e skills, ORM read-only e `manage.py check`.
- Date: 2026-06-26.

## Execution prompt

### Persona

Engenheiro de governança de agentes e arquitetura Django, orientado por evidência, escopo e menor mudança correta.

### Action

Fechar as divergências de protocolo do LV em relação ao padrão multiplataforma e entregar a skill `lv-prompt-builder` nas três plataformas, preservando os fatos de domínio do LV.

### Context

O LV é um monólito Django 5.2 em Windows/PowerShell, com governança em `AGENTS.md`, `CLAUDE.md` e `docs/`, cinco skills `lv-*` sincronizadas em `.claude`/`.agents`/`.cursor`, pagamentos Asaas/Stripe e wizard público. O Visary é a referência de protocolo, não de domínio.

### Constraints

- Não portar fatos do Visary (vistos, viagens, parceiros, "sem pagamento", mapeamento Principal/dependente-viagem).
- Preservar os fatos de domínio do LV.
- Menor mudança correta: atualizar só o protocolo divergente; não reescrever o que está certo.
- Não alterar código funcional, banco, migrations, seeds ou pagamentos.
- As três cópias de cada skill devem ser semanticamente idênticas.

### Acceptance criteria

- [x] `docs/AGENT-WORKFLOW.md` tem `## 2. Classificação` com as categorias de demanda, e as seções seguintes foram renumeradas até `§13` sem perda de conteúdo.
- [x] `lv-prompt-builder` existe em `.claude/skills/`, `.agents/skills/` e `.cursor/skills/` com frontmatter YAML válido.
- [x] As três cópias do `SKILL.md` são byte-idênticas.
- [x] O Codex recebe `agents/openai.yaml`, no padrão das outras cinco skills.
- [x] A skill usa `disable-model-invocation: true` e gera o execution prompt no formato de `docs/PRD-STANDARD.md`, parando sem implementar.
- [x] `docs/PLATFORM-ADAPTERS.md` registra a skill nas colunas Claude/Codex/Cursor.
- [x] A decisão sobre `docs/UX-SCREEN-FLOWS.md` está registrada com motivo.
- [x] Nenhum fato de domínio do Visary vazou para os arquivos tocados.

### Expected evidence

- Parse YAML estrito das cópias e dos metadados.
- SHA-256 idêntico entre as três cópias.
- Contagem de caracteres da `description` abaixo de 1.536.
- Busca textual anti-vazamento de termos do Visary.
- `git diff --check`.

### Output format

Resumo curto, evidências reais, não validado, pendências e status.

## Scope

- `.claude/skills/lv-prompt-builder/SKILL.md` (novo)
- `.agents/skills/lv-prompt-builder/SKILL.md` (novo)
- `.agents/skills/lv-prompt-builder/agents/openai.yaml` (novo)
- `.cursor/skills/lv-prompt-builder/SKILL.md` (novo)
- `docs/AGENT-WORKFLOW.md` (inserção de Classificação + renumeração)
- `docs/PLATFORM-ADAPTERS.md` (registro da skill)
- este PRD.

## Out of scope

- `docs/UX-SCREEN-FLOWS.md` (decisão de não criar — ver Cleanup findings).
- Alterar as cinco skills existentes, `AGENTS.md` ou `CLAUDE.md`.
- Código Django, templates, CSS, JavaScript, dados, migrations, seeds, pagamentos, deploy ou push.
- Executar a skill `lv-prompt-builder` ou qualquer demanda derivada.

## Impacted files

Os arquivos listados no escopo.

## Risks and edge cases

- Skill auto-invocada em contexto errado: mitigado por `disable-model-invocation: true`.
- Frontmatter malformado carregando a skill sem `description`: mitigado quotando a `description` (contém `: `); validado por PyYAML.
- Renumeração do AGENT-WORKFLOW quebrar referências: verificado por `grep` — nenhuma fonte referencia seções numeradas do documento.
- Prompt gerado que pré-aprova gate de segurança: a skill lista explicitamente os gates que não podem ser consolidados (ORM mutável, migrations, migrate, reset, seeds, cobrança/webhook real Asaas/Stripe, push, deploy).
- Vazamento de fatos do Visary: mitigado por varredura textual; o único match foi o falso positivo "categoria principal" (adjetivo pt-BR).

## Rules and constraints

- Menor mudança correta; uma fonte de verdade por responsabilidade.
- Fonte oficial antes de inferência.
- Conteúdo permanente curto; procedimento na skill.
- Falha ou limitação explícita.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [ ] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Não aplicável. A entrega é instrução/documento e configuração, sem comportamento de aplicação testável.

### Execution authorization

- Status: não solicitada.

### Execution evidence

Testes Django não executados.

## Visual validation

Não aplicável. Não há template, CSS, JavaScript ou tela.

## ORM validation

Não aplicável. Não há persistência.

## Quality validation

- Parse YAML estrito (PyYAML) das 18 cópias de `SKILL.md` (6 skills × 3 plataformas) e dos 6 `openai.yaml`: todas válidas.
- SHA-256 das três cópias de `lv-prompt-builder/SKILL.md`.
- Contagem de caracteres da `description`.
- Varredura anti-vazamento de termos do Visary.
- `git diff --check`.

## Evidence

- `git status --short`: novos `.claude/`, `.agents/` e `.cursor/skills/lv-prompt-builder/`; modificados `docs/AGENT-WORKFLOW.md` e `docs/PLATFORM-ADAPTERS.md`. `.claude/settings.local.json` permanece como mudança preexistente do usuário, não tocada.
- SHA-256 idêntico nas três cópias do `SKILL.md`: `371a7aa9bb0928661bddd2155799c120a3bb830b58e12c5c06ab6fcce4b2224b`.
- Parse YAML estrito: 18 `SKILL.md` + 6 `openai.yaml` reportados como válidos; `lv-prompt-builder` com `name`, `description`, `argument-hint` e `disable-model-invocation: true`.
- `description` da skill com 354 caracteres, abaixo do limite de 1.536 da listagem.
- `docs/AGENT-WORKFLOW.md` com seções `## 1` a `## 13`, sendo `## 2. Classificação` a nova; `grep` confirmou que nenhuma fonte referencia seções numeradas do documento.
- Varredura anti-Visary (`visto|viagem|consular|parceiro|assessor|mysql|viacep|sem pagamento|dependente.*viagem|Aluno.*Principal`) sem correspondência nos arquivos tocados.
- `git diff --check`: sem erro de whitespace; apenas avisos de normalização LF→CRLF do Windows.
- Fonte oficial confirmada nesta sessão: [Claude Code: skills](https://code.claude.com/docs/en/skills) — cap de 1.536 caracteres, `disable-model-invocation`, localização `.claude/skills/` e comportamento de frontmatter malformado.

## Implemented

- Inserida `## 2. Classificação` em `docs/AGENT-WORKFLOW.md`, com as categorias de demanda do padrão multiplataforma, e renumeradas as seções Preflight→ORM→Limpeza para `§3`–`§13`, preservando o texto original e os fatos do LV (incluindo a seção de Pagamentos).
- Criada a skill `lv-prompt-builder` nas três plataformas, semanticamente idêntica, no estilo das cinco skills `lv-*`, com etapas Receber, Classificar, Decidir gates, Gerar o prompt, Parar e Restringir, em modo só-prompt (`disable-model-invocation: true`).
- Criado `agents/openai.yaml` do Codex para a skill, no padrão das demais.
- `description` quotada para garantir frontmatter YAML válido apesar do `: ` interno.
- `docs/PLATFORM-ADAPTERS.md` registra a skill nas três colunas, com nota sobre invocação manual.

## Cleanup findings

- Diff reauditado: seis arquivos no escopo aprovado, mais este PRD; `.claude/settings.local.json` preexistente preservado.
- Todas as referências da skill (`AGENTS.md`, `CLAUDE.md`, contratos `docs/` e skills `lv-*`) existem; nenhuma rota, arquivo, comando ou fonte inventada.
- **Decisão sobre `docs/UX-SCREEN-FLOWS.md`: não criar agora.** Motivo: o LV já governa padrões genéricos de tela, estados, papéis e hierarquia de ação em `docs/UI-SCREEN-CONTRACT.md`, e os fluxos concretos vivem nos três `docs/wizard-step-plan-*.md` e nos PRDs de tela; criar um documento espelhando o Visary duplicaria conteúdo correto e arriscaria portar fatos de domínio do Visary. A própria skill `lv-prompt-builder` (e o `SKILL.md` fornecido) já omite `UX-SCREEN-FLOWS` da lista de contratos, refletindo essa decisão. Reabrir quando houver fluxo de tela transversal não coberto pelos contratos atuais.
- O `visary-prompt-builder` original existe apenas em `.claude`; o LV fecha o gap entregando a skill nas três plataformas de uma vez (supera a paridade pendente registrada no PRD-110 do Visary).
- Sem código morto, hardcode, duplicação, placeholder solto ou documentação divergente no escopo.

## Follow-up PRDs

Nenhum. A paridade multiplataforma da skill foi entregue nesta PRD; não restou débito material.

## Deviations from plan

- "Test authored first" e "Refactor" não se aplicam: a entrega é documento de instrução e configuração, sem comportamento de aplicação testável.
- A `description` precisou ser quotada (não estava no `SKILL.md` literal fornecido) para satisfazer o critério "frontmatter válido"; o texto foi integralmente preservado.

## Pending

- Recarregar Claude Code, Codex e Cursor para descoberta runtime da skill; a execução ponta a ponta de `/lv-prompt-builder` não foi exercitada nesta sessão.

## Final status

**Concluída com limitações**: a Classificação no AGENT-WORKFLOW, a skill `lv-prompt-builder` nas três plataformas, o registro no adaptador, a decisão sobre UX-SCREEN-FLOWS e este PRD foram implementados e validados estruturalmente; a ativação runtime das skills depende de recarga das ferramentas.
