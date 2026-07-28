# PRD-156: Skills — estrutura, comando real, índice de PRD e sincronização verificável

## Summary

Padronizar as seis skills do LV com critério de parada e bloco de saída, substituir comandos genéricos pelo interpretador real, alinhar `lv-prd` à regra de índice canônico e tornar a sincronização das três cópias parte do ciclo de limpeza.

## Demand type

Revisão de governança.

## Current problem

**1. Auditoria sem saída nem parada.** `.claude/skills/lv-cleanup-audit/SKILL.md:8-15` manda "Ler o diff completo da tarefa" sem nomear comando, sem definir o que a auditoria produz e sem condição de término. Não é possível saber se a skill foi executada.

**2. Comando genérico contra contrato explícito.** `.claude/skills/lv-django-delivery/SKILL.md:38` instrui "executar `manage.py check`", e `:20-23` diz "executar testes locais" sem comando. `CLAUDE.md:59-65` define os comandos reais com `.\.venv\Scripts\python.exe`. Um agente que siga a skill roda o Python global.

**3. Numeração de PRD contradiz o padrão.** `.claude/skills/lv-prd/SKILL.md:11` manda "Encontrar o próximo número livre", enquanto `docs/PRD-STANDARD.md:7-8` proíbe confiar apenas em `ls` — que não revela gaps reservados nem duplicatas — e obriga usar e atualizar `docs/prd/README.md`.

**4. Sincronização das três cópias não é acionada por ninguém.** `docs/PLATFORM-ADAPTERS.md:66-76` exige que `.claude/`, `.agents/` e `.cursor/` sejam idênticas e comparadas por hash. Nenhuma skill do ciclo dispara essa verificação. Hoje as seis estão idênticas — por disciplina manual, não por processo.

**5. `lv-prompt-builder` fora da tabela de skills.** `docs/PRD-STANDARD.md:20-26` lista cinco skills; `AGENTS.md:178` reconhece seis.

## Goal

Depois desta PRD, executar qualquer skill do LV produz saída de formato previsível, termina em condição declarada, e comandos copiados da skill funcionam.

## Context Ledger

### Files read in full

- `.claude/skills/lv-task-intake/SKILL.md`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`
- `AGENTS.md`, `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`

### Adjacent files consulted

- `.agents/skills/`, `.cursor/skills/` — seis cópias cada, verificadas idênticas.
- `docs/prd/README.md` — índice canônico existente.
- `.claude/launch.json` — porta 8000.

### Internet / official documentation

- [Anthropic — Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — frontmatter e orientação de que a `description` declare quando acionar.

### Context7 / MCPs / tools verified

- Context7 indisponível na redação. Limitação registrada.

### Limitations found

- Nenhuma.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de governança, 2026-07-22.
- User approval: instrução explícita de gerar PRDs de correção.
- Date: 2026-07-22
- Execution approval: prompt explícito de 2026-07-25 autorizou corrigir contradições cobertas pelas PRDs 154–158.

## Execution prompt

### Persona

Mantenedor das skills do LV Jiu Jitsu.

### Action

Reestruturar as seis skills, corrigir comandos, alinhar `lv-prd` ao índice e acrescentar a verificação de sincronização em `lv-cleanup-audit`.

### Context

Estrutura obrigatória para toda `SKILL.md` do LV após esta PRD:

```md
---
name: <slug>
description: "<quando acionar + o que entrega>"
---

# <Título>

## Quando acionar
## Passos
## Saída
## Parar quando
```

`Saída` traz um bloco literal com os campos fixos daquela skill.
`Parar quando` traz condições de término, incluindo pelo menos uma de falha.

Saída obrigatória de `lv-cleanup-audit`:

```text
Diff auditado: <comando executado>
Achados corrigidos no escopo: <lista ou "nenhum">
Follow-up criado: <PRD-NNN ou "nenhum">
Cópias de skill sincronizadas: <sim | não se aplica>
Status: limpo | com follow-up
```

### Constraints

- `description` com `": "` fica entre aspas. Hoje só `lv-prompt-builder` tem esse caso e já está correto — manter.
- Todo comando em skill usa `.\.venv\Scripts\python.exe manage.py <cmd>`.
- Porta canônica `localhost:8000` escrita literalmente onde a skill mandar subir servidor.
- O guard de parada de `lv-prompt-builder:15` ("parar e fazer UMA pergunta objetiva") é o padrão de referência — replicar a ideia nas demais, não removê-lo.
- Alterar skill obriga sincronizar as três cópias na mesma entrega.

### Acceptance criteria

- [x] As seis `SKILL.md` contêm `## Quando acionar`, `## Passos`, `## Saída`, `## Parar quando`. Verificação: `grep -c "^## Parar quando" .claude/skills/*/SKILL.md` retorna 1 para cada um dos 6 arquivos.
- [x] Cada `## Parar quando` contém ao menos uma condição de falha (evidência não produzida, ferramenta indisponível, teste vermelho).
- [x] `lv-cleanup-audit` contém o bloco de saída literal acima e um comando de diff explícito nos passos.
- [x] Zero ocorrências de `manage.py` sem o interpretador do projeto. Verificação: `grep -rn "manage.py" .claude/skills/ | grep -v "venv"` retorna vazio.
- [x] `lv-django-delivery` cita literalmente `.\.venv\Scripts\python.exe manage.py check` e `.\.venv\Scripts\python.exe manage.py test --verbosity 2`.
- [x] `lv-ui-delivery` cita `localhost:8000` literalmente.
- [x] `.claude/skills/lv-prd/SKILL.md:11` passa a instruir consultar **e atualizar** `docs/prd/README.md` como índice canônico, sem depender de `ls`. Verificação: `grep -n "próximo número livre" .claude/skills/lv-prd/SKILL.md` retorna vazio.
- [x] `lv-cleanup-audit` ganha um passo que, quando o diff tocar `*/skills/*/SKILL.md`, compara as três cópias e falha a auditoria se divergirem.
- [x] `docs/PRD-STANDARD.md` tabela de skills lista as **seis**, com `lv-prompt-builder` marcado como invocação manual.
- [x] Para cada skill alterada, `diff .claude/skills/<n>/SKILL.md .agents/skills/<n>/SKILL.md` e o equivalente `.cursor/` retornam vazio.
- [ ] As seis skills continuam aparecendo na listagem da ferramenta após reload — prova de que o frontmatter não quebrou.

### Expected evidence

- Diff das seis skills e dos espelhos.
- Saída dos `grep` de estrutura e de comando.
- Saída dos `diff` de sincronização.
- Listagem de skills reconhecidas.

### Output format

Diff + saídas de comando na seção `Evidence`.

## Scope

- Seis `SKILL.md` em `.claude/skills/` e espelhos em `.agents/` e `.cursor/`.
- `docs/PRD-STANDARD.md` — tabela de skills.

## Out of scope

- Criar skill nova.
- Gate condicional de autorização (`PRD-155`).
- Desduplicação de regra entre camadas (`PRD-157`).
- Slash commands (`PRD-158`).

## Impacted files

| Arquivo | Natureza |
|---|---|
| `.claude/skills/lv-task-intake/SKILL.md` | reestruturação |
| `.claude/skills/lv-prd/SKILL.md` | reestruturação + regra de índice |
| `.claude/skills/lv-django-delivery/SKILL.md` | reestruturação + comandos reais |
| `.claude/skills/lv-ui-delivery/SKILL.md` | reestruturação + porta real |
| `.claude/skills/lv-cleanup-audit/SKILL.md` | reestruturação + saída + sync |
| `.claude/skills/lv-prompt-builder/SKILL.md` | reestruturação |
| `.agents/skills/*`, `.cursor/skills/*` | espelhamento |
| `docs/PRD-STANDARD.md` | tabela de skills |

## Risks and edge cases

| Risco | Mitigação |
|---|---|
| Quebrar o YAML e a skill sumir da listagem | Critério exige confirmar as seis na listagem após reload; regra de aspas explicitada. |
| A verificação de sincronização virar ruído em todo diff | O passo só dispara quando o diff toca `*/skills/*/SKILL.md`. |
| `## Parar quando` virar texto decorativo | Critério exige condição de falha, não só de sucesso. |
| Perder o guard de `lv-prompt-builder` na reestruturação | Constraint explícita de preservá-lo. |

## Rules and constraints

- pt-BR no conteúdo; identificadores em inglês.
- Skill não recebe regra de governança nova; regra vai para o dono definido em `PRD-157`.

## Plan

- [x] Context and research
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste Django. Verificação por `grep`, `diff` e listagem de skills.

### Execution authorization

- Status: authorized

### Execution evidence

- As seis skills têm exatamente quatro seções operacionais.
- Busca de `manage.py` sem `.\.venv\Scripts\python.exe` nas três árvores: vazia.
- Parser PyYAML validou os 18 `SKILL.md`.
- Hashes SHA-256 confirmaram cópias idênticas por skill.

## Visual validation

Não aplicável.

## ORM validation

Não aplicável.

## Quality validation

`grep` de estrutura e comando, `diff` de espelhos, listagem de skills.

## Evidence

- Seis skills reestruturadas com acionamento, passos, saída e parada.
- Comandos Django usam o interpretador real.
- `lv-prd` usa e atualiza o índice canônico.
- `lv-cleanup-audit` executa diff explícito e valida sincronização.
- `docs/PRD-STANDARD.md` inclui `lv-prompt-builder` manual.

## Implemented

As 18 cópias estão sincronizadas e com frontmatter válido. Nenhum comando Django genérico permaneceu.

## Cleanup findings

PRD-155 foi implementada na mesma entrega para evitar uma sincronização intermediária contraditória.

## Follow-up PRDs

- `PRD-157` — desduplicação e higiene do `CLAUDE.md`.
- `PRD-158` — slash commands.

## Deviations from plan

Reload/listagem da ferramenta não está disponível dentro desta sessão já iniciada; validação substituta feita por parse YAML estrito das 18 cópias.

## Pending

Reload/listagem das skills na ferramenta após reinício da sessão.

## Final status

**Concluída com limitação**: todos os critérios de arquivo/comando/hash passaram; reload da ferramenta não foi observável nesta sessão.
