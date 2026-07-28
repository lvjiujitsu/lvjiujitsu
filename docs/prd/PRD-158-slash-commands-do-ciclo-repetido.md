# PRD-158: Slash commands para o ciclo operacional repetido

## Summary

Preencher `.claude/commands/`, hoje vazio, com os comandos das tarefas que o operador repete a cada sessão: reset local completo, validação visual, sincronização das três cópias de skill e auditoria de paridade com os projetos.

## Demand type

Nova feature de governança.

## Current problem

`.claude/commands/` existe e está vazio. As tarefas recorrentes continuam sendo digitadas à mão ou descritas em prosa dentro de skills:

**1. Ciclo destrutivo local.** Documentado em `docs/OPERACAO-BANCO-SEEDS.md` como sequência de `clear_migrations.py` → `makemigrations` → `test` → `migrate` → 21 seeds canônicas → `runserver`. É a tarefa mais longa e mais repetida do projeto, e a mais sujeita a interrupção no meio — quando isso acontece, o banco fica apagado e o sistema fora do ar.

**2. Validação visual.** Descrita em prosa em `lv-ui-delivery`: rota real, caminho feliz, edge case, desktop, mobile, console, screenshot. Nada garante que todos aconteçam.

**3. Sincronização das três cópias de skill.** `docs/PLATFORM-ADAPTERS.md:66-76` exige comparação byte a byte entre `.claude/`, `.agents/` e `.cursor/`. Hoje as seis estão idênticas por disciplina manual. Não há comando que verifique.

**4. Auditoria de paridade entre o projeto.** Feita manualmente em 2026-07-22 com rubrica ad hoc. Vai se repetir.

## Goal

Depois desta PRD, cada uma das quatro tarefas é um comando único, com pré-condição verificada antes de qualquer ação destrutiva e saída padronizada.

## Context Ledger

### Files read in full

- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/AGENT-WORKFLOW.md`
- `.claude/skills/lv-ui-delivery/SKILL.md`
- `.claude/launch.json`, `.claude/settings.json`, `.claude/settings.local.json`

### Adjacent files consulted

- `system/management/commands/` — inventário real das seeds.
- `clear_migrations.py`.

### Internet / official documentation

- [Anthropic — Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) — formato em `.claude/commands/`, frontmatter e argumentos.

### Context7 / MCPs / tools verified

- Context7 indisponível na redação. Limitação registrada.

### Limitations found

- A lista exata das 21 seeds canônicas deve ser lida de `docs/OPERACAO-BANCO-SEEDS.md` no momento da implementação, não copiada desta PRD.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de governança, 2026-07-22.
- User approval: instrução explícita de gerar PRDs de correção.
- Date: 2026-07-22

## Execution prompt

### Persona

Mantenedor da automação de agentes do LV Jiu Jitsu.

### Action

Criar quatro arquivos em `.claude/commands/`.

### Context

| Arquivo | Invocação | O que faz |
|---|---|---|
| `.claude/commands/reset-local.md` | `/reset-local` | Ciclo destrutivo local até o servidor no ar |
| `.claude/commands/validar-tela.md` | `/validar-tela <rota>` | Validação visual com evidência obrigatória |
| `.claude/commands/sync-skills.md` | `/sync-skills` | Compara as três cópias de cada skill |
| `.claude/commands/auditar-paridade.md` | `/auditar-paridade` | Aplica a rubrica A–H de governança |

Rubrica de `/auditar-paridade`: A separação de papéis, B acionabilidade, C frontmatter, D cobertura do ciclo, E verificabilidade, F não-contradição, G especificidade, H manutenibilidade.

### Constraints

- Todo comando usa `.\.venv\Scripts\python.exe`.
- `/reset-local` lê a ordem das seeds de `docs/OPERACAO-BANCO-SEEDS.md` e não mantém uma segunda lista. Se as duas divergirem, o comando falha em vez de escolher.
- `/reset-local` verifica as variáveis exigidas pelas seeds **antes** de apagar o banco.
- `/reset-local` recusa executar quando `DJANGO_ENV_FILE` aponta para `.env.hg` ou `.env.prod`.
- `/reset-local` para no primeiro erro e informa em qual passo parou.
- `/validar-tela` não declara sucesso sem screenshot registrado.
- `/sync-skills` reporta divergência e pede a direção da cópia; não sobrescreve sozinho.
- `/auditar-paridade` usa no máximo dois subagentes, um por projeto.
- Nenhum comando pode disparar ação em gateway de pagamento.

### Acceptance criteria

- [ ] Os quatro arquivos existem em `.claude/commands/` e aparecem na listagem da ferramenta após reload.
- [ ] Cada arquivo tem frontmatter com `description`; `": "` entre aspas quando ocorrer.
- [ ] `/reset-local` aborta **sem apagar** `db.sqlite3` quando uma variável exigida por seed está vazia. Verificação: executar nessa condição e provar por `ls db.sqlite3` que o arquivo permanece.
- [ ] `/reset-local` recusa `DJANGO_ENV_FILE=.env.hg` sem executar nenhum passo.
- [ ] `/reset-local` em condição normal termina com o servidor respondendo em `http://localhost:8000/` com HTTP 200.
- [ ] `/reset-local` interrompido por erro nomeia o passo que falhou e não executa os seguintes.
- [ ] A ordem de seeds usada pelo comando é lida de `docs/OPERACAO-BANCO-SEEDS.md`; o comando não contém uma segunda cópia da lista. Verificação: inspeção do arquivo do comando.
- [ ] `/validar-tela` produz saída com cada item marcado individualmente e o caminho do screenshot.
- [ ] `/sync-skills` compara as seis skills nas três pastas e reporta `idêntico` ou `divergente` para cada uma, com o caminho de cada divergência.
- [ ] `/auditar-paridade` produz tabela com os oito critérios por projeto e lista de defeitos com `arquivo:linha`.
- [ ] `docs/AGENT-WORKFLOW.md` ganha seção listando os quatro comandos e quando usar cada um.
- [ ] `docs/PLATFORM-ADAPTERS.md` registra que slash commands são exclusivos do Claude nesta fase, com o procedimento manual equivalente para Codex e Cursor.

### Expected evidence

- Conteúdo dos quatro arquivos.
- Saída de `/reset-local` bem-sucedido, com o HTTP 200 final.
- Saída de `/reset-local` nas duas recusas, com prova de que `db.sqlite3` sobreviveu.
- Saída de `/sync-skills` com as seis skills avaliadas.
- Diff de `docs/AGENT-WORKFLOW.md` e `docs/PLATFORM-ADAPTERS.md`.

### Output format

Conteúdo dos comandos + saídas de execução na seção `Evidence`.

## Scope

- Quatro arquivos novos em `.claude/commands/`.
- Registro em `docs/AGENT-WORKFLOW.md` e `docs/PLATFORM-ADAPTERS.md`.

## Out of scope

- Comandos equivalentes em outros repositórios — fora do escopo deste projeto.
- Alterar `clear_migrations.py` ou qualquer management command.
- Alterar a ordem das seeds.
- Automatizar fluxo de pagamento em sandbox.

## Impacted files

| Arquivo | Natureza |
|---|---|
| `.claude/commands/reset-local.md` | criação |
| `.claude/commands/validar-tela.md` | criação |
| `.claude/commands/sync-skills.md` | criação |
| `.claude/commands/auditar-paridade.md` | criação |
| `docs/AGENT-WORKFLOW.md` | edição |
| `docs/PLATFORM-ADAPTERS.md` | edição |

## Risks and edge cases

| Risco | Mitigação |
|---|---|
| Apagar o banco e falhar na seed por variável ausente | Pré-condição verificada antes do `clear`, com critério de aceite dedicado que prova a sobrevivência do arquivo. |
| Disparo contra HG ou prod | Recusa por `DJANGO_ENV_FILE`, com critério próprio. |
| Lista de seeds do comando divergir do runbook | O comando lê do runbook; manter segunda cópia é proibido por constraint e verificado por inspeção. |
| Comando tocar em cobrança | Constraint explícita; nenhum dos quatro comandos invoca fluxo de pagamento. |
| `/auditar-paridade` estourar contexto | Limite de dois subagentes com leitura restrita aos contratos. |

## Rules and constraints

- pt-BR no conteúdo; identificadores em inglês.
- Comandos orquestram o que já está nos contratos; não introduzem regra nova.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

Nenhum teste Django. A verificação é a execução real, incluindo os dois caminhos de recusa.

### Execution authorization

- Status: authorized

### Execution evidence

Pendente.

## Visual validation

`/validar-tela` validado contra uma rota real do LV, com screenshot desktop e mobile.

## ORM validation

Não aplicável.

## Quality validation

Execução dos quatro comandos, incluindo caminhos de erro.

## Evidence

Pendente.

## Implemented

Pendente.

## Cleanup findings

Pendente.

## Follow-up PRDs

- Nenhum previsto.

## Deviations from plan

Pendente.

## Pending

Pendente.

## Final status

Superada pela `PRD-161`, que criou os quatro slash commands em
`.claude/commands/`: `reset-local`, `sync-skills`, `validar-tela` e
`auditar-paridade`.

A dependência de `PRD-154` deixou de ser bloqueante. O receio original era o
comando carregar gates de ambiente que a `PRD-154` pretendia relaxar; o
`/reset-local` entregue não carrega gate próprio — apenas antecipa ao operador
as guardas que `clear_migrations.py` já aplica por conta própria. Se a
`PRD-154` mudar a política de ambientes remotos, o comando não precisa mudar.
