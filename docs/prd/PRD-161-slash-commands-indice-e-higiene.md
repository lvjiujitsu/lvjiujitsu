# PRD-161: Slash commands, índice de PRDs e higiene do repositório

## Summary

Fechar as lacunas de superfície de agente e de rastreabilidade do LV: o
diretório `.claude/commands/` existe vazio, o índice de 159 PRDs não tem
coluna de status, `LICENSE` não existe, `.gitattributes` cobre só shell, há
logs de execução na raiz e o `launch.json` tem caminho absoluto de máquina.
Supersede a PRD-158.

## Demand type

Governança e higiene de repositório. Sem mudança de regra de negócio.

## Current problem

1. `.claude/commands/` existe e está vazio. padrão canônico e outro repositório têm quatro
 slash commands cada — `auditar-paridade`, `reset-local`, `sync-skills` e
 `validar-tela`. A PRD-158 registrou a intenção e está como não iniciada.
2. `docs/prd/README.md` lista 159 PRDs com arquivo e título, sem coluna de
 status. Saber o estado de qualquer PRD exige abrir o arquivo e procurar a
 seção `## Final status`, que está ausente em cerca de 65 PRDs antigas. O
 índice canônico carrega a coluna e a declaração do próximo número livre.
3. Não existe declaração do próximo número livre no índice, o que já
 produziu duplicatas no passado — a PRD-079 documenta a renumeração de sete
 números duplicados.
4. `LICENSE` não existe. O padrão canônico tem MIT.
5. `.gitattributes` cobre apenas `*.sh text eol=lf`. O outro repositório tem
 `* text=auto` além da regra de shell.
6. Estão fisicamente na raiz do worktree: `runserver-codex.log` com 15 KB,
 `runserver-codex.err.log` com 26 KB, o diretório `.codex-runtime/` com
 dois logs e diretórios `__pycache__/`. São ignorados pelo git, mas
 poluem o worktree; o outro repositório mantém a raiz limpa.
7. `.claude/launch.json` aponta para um caminho absoluto de máquina
 (`C:/Users/whsf/...`), enquanto padrão canônico e outro repositório usam caminho relativo
 e o mesmo rótulo de configuração.
8. `docs/UI-SCREEN-CONTRACT.md` tem a seção `## 15.` na linha 351, antes de
 `## 14. Changelog` na linha 555.
9. `PRD-154` declara "Não iniciada" no próprio corpo, mas as PRDs 155, 156 e
 159, que dependem dela, já estão concluídas.
10. `.github/workflows/copilot-setup-steps.yml` existe e não é descrito em
 `CLAUDE.md` nem no `README.md`.

## Goal

O LV tem os mesmos artefatos de superfície dos, o índice de PRDs
responde ao estado de cada PRD sem abrir arquivo, e o worktree está limpo.

## Context Ledger

### Files read in full

- `docs/prd/README.md`
- `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-154-natureza-mvp-e-remocao-de-gates.md`
- `docs/prd/PRD-158-slash-commands-do-ciclo-repetido.md`
- `.claude/launch.json`, `.gitattributes`, `.gitignore`
- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `.github/workflows/ci.yml`, `.github/workflows/copilot-setup-steps.yml`

### Adjacent files consulted

- as seis `.claude/skills/*/SKILL.md`
- `clear_migrations.py`
- `docs/OPERACAO-BANCO-SEEDS.md`

### Internet / official documentation

- [Claude Code — Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Claude Code — Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [Git — `gitattributes`](https://git-scm.com/docs/gitattributes)
- [Open Source Initiative — MIT License](https://opensource.org/license/mit)

### Context7 / MCPs / tools verified

- Context7 disponível na sessão. O formato de slash command foi conferido
 contra a documentação oficial acima e contra os quatro arquivos reais do
 padrão canônico, lidos do disco.

### Limitations found

- A extração automática de status exige que cada PRD tenha a seção
 `## Final status`. Cerca de 65 PRDs antigas não têm. Elas ficam com status
 `—`, conforme o padrão canônico, sem reescrita retroativa do conteúdo.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de paridade entre o projeto.
- User approval: ordem explícita do operador em 2026-07-25.
- Date: 2026-07-25.

## Execution prompt

### Persona

Responsável pela superfície de agente e pela higiene do repositório LV.

### Action

Criar os quatro slash commands adaptados ao LV, acrescentar coluna de status
e próximo número livre ao índice de PRDs, criar `LICENSE`, ampliar
`.gitattributes`, limpar o worktree, tornar o `launch.json` relativo e
corrigir as inconsistências de documentação apontadas.

### Context

o projeto compartilham o framework de governança. O padrão canônico é o alvo
de paridade em slash commands e índice de PRDs; o outro repositório é o alvo em
`.gitattributes` e limpeza de raiz.

### Constraints

- Cada slash command usa comandos que existem de fato no LV: o
 `clear_migrations.py` local, os 21 comandos `seed_system_initial_*` e a
 porta 8000.
- O índice não é reescrito à mão: o status vem do arquivo.
- Não apagar arquivo rastreado sem conferir o histórico.
- Não reescrever retroativamente o conteúdo das PRDs antigas.

### Acceptance criteria

- [ ] `.claude/commands/` contém `auditar-paridade.md`, `reset-local.md`,
 `sync-skills.md` e `validar-tela.md`, cada um com frontmatter
 `description` válido, passos e critério de parada.
- [ ] `reset-local.md` descreve o ciclo real do LV: `clear_migrations.py`,
 `migrate`, `create_admin_superuser` e os 21 seeds na ordem canônica de
 `docs/OPERACAO-BANCO-SEEDS.md`, na porta 8000. Verificação: cada
 comando citado existe em `system/management/commands/`.
- [ ] `sync-skills.md` compara as três plataformas e as seis skills, e
 concorda com `docs/PLATFORM-ADAPTERS.md` sobre qual diretório é a
 fonte canônica.
- [ ] `docs/prd/README.md` ganha coluna Status por PRD, extraída da seção
 `## Final status` do arquivo, com `—` quando ausente.
- [ ] `docs/prd/README.md` declara "Próximo número livre" em linha própria,
 com o valor 162 após esta série.
- [ ] O número de linhas de dados da tabela é igual ao número de arquivos
 `PRD-*.md` em `docs/prd/`. Verificação: contagem comparada.
- [ ] `LICENSE` existe com o texto MIT.
- [ ] `.gitattributes` declara `* text=auto`, `*.sh text eol=lf` e
 `*.yaml text eol=lf`.
- [ ] `runserver-codex.log`, `runserver-codex.err.log` e `.codex-runtime/`
 não estão no worktree e continuam cobertos pelo `.gitignore`.
 Verificação: listagem da raiz.
- [ ] `.claude/launch.json` usa caminho relativo para o interpretador da
 `.venv`, rótulo `Django Dev Server` e `autoPort: false`, alinhado a
 padrão canônico e outro repositório.
- [ ] `docs/UI-SCREEN-CONTRACT.md` tem as seções em ordem numérica
 crescente, com o Changelog por último.
- [ ] `docs/prd/PRD-154-*.md` tem status coerente com o fato de 155, 156 e
 159 estarem concluídas, ou a dependência declarada nessas PRDs é
 corrigida. A decisão fica registrada.
- [ ] `README.md` descreve os dois workflows de `.github/workflows/`.
- [ ] `docs/prd/PRD-158-*.md` é marcada como superada por esta PRD.
- [ ] `python manage.py check` sem erro e suíte de testes verde.

### Expected evidence

Listagem de `.claude/commands/`; contagem comparada de linhas do índice e de
arquivos de PRD; listagem da raiz; saída de `check` e da suíte.

### Output format

Diff e PRD atualizada com evidência real.

## Scope

- Quatro slash commands em `.claude/commands/`.
- Coluna de status e próximo número livre no índice de PRDs.
- `LICENSE` e `.gitattributes`.
- Limpeza de resíduos da raiz.
- `launch.json` relativo.
- Correção da ordem de seções do contrato de UI, do status da PRD-154 e da
 descrição dos workflows.

## Out of scope

- Reconciliação das variáveis de ambiente (PRD-160).
- Reset remoto, deploy e observabilidade (PRD-162).
- Reescrita das PRDs antigas sem seção de status.
- Qualquer mudança de model, migration ou fluxo de produto.

## Impacted files

- `.claude/commands/auditar-paridade.md` (novo)
- `.claude/commands/reset-local.md` (novo)
- `.claude/commands/sync-skills.md` (novo)
- `.claude/commands/validar-tela.md` (novo)
- `.claude/launch.json`
- `.gitattributes`, `LICENSE` (novo)
- `docs/prd/README.md`
- `docs/prd/PRD-154-natureza-mvp-e-remocao-de-gates.md`
- `docs/prd/PRD-158-slash-commands-do-ciclo-repetido.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `README.md`

## Risks and edge cases

- Introduzir `* text=auto` e provocar renormalização em massa: conferir o
 diff resultante e registrar como desvio se for amplo.
- Slash command citando comando que não existe: cada nome é conferido contra
 `system/management/commands/` antes de fechar.
- Reordenar seções do contrato de UI e quebrar âncora usada por outra PRD:
 buscar referências às âncoras antes de mover.
- Remover os logs da raiz e perder informação de diagnóstico: são logs de
 execução antiga de servidor de desenvolvimento, sem valor de histórico.

## Rules and constraints

- Documentação em pt-BR; identificadores em inglês.
- Menor mudança correta; não editar `staticfiles/`.
- Contrato descreve o que existe, não o desejado.

## Plan

- [ ] Contexto e pesquisa
- [ ] Criar os quatro slash commands
- [ ] Reformular o índice de PRDs com status e próximo número livre
- [ ] `LICENSE` e `.gitattributes`
- [ ] Limpar a raiz e ajustar o `launch.json`
- [ ] Corrigir contrato de UI, status da PRD-154 e descrição dos workflows
- [ ] Validação
- [ ] Auditoria de limpeza

## Test plan

### Tests to author

Não há comportamento Django novo. A verificação é por comando de inspeção:
contagem comparada entre linhas do índice e arquivos de PRD, existência de
cada comando citado nos slash commands, e listagem da raiz.

### Execution authorization

- Status: autorizada pela ordem explícita do operador em 2026-07-25.

### Execution evidence

Suíte completa, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 722 tests in 224.415s

OK
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Visual validation

Não aplicável. Nenhum template, CSS ou JavaScript foi alterado. A renumeração
de seções do `UI-SCREEN-CONTRACT.md` é documental e não muda nenhuma tela.

## ORM validation

Não aplicável.

## Quality validation

Slash commands criados, com frontmatter válido:

```
auditar-paridade.md ok
reset-local.md ok
sync-skills.md ok
validar-tela.md ok
```

Cada comando `seed_system_initial_*` citado em `reset-local.md` foi conferido
contra `system/management/commands/`; nenhum nome inexistente.

Índice de PRDs regenerado a partir dos arquivos:

```
162 PRD(s) indexada(s). Proximo numero livre: 163.
 —: 71
 concluída: 55
 concluída com limitações: 28
 não iniciada: 4
 não concluída: 3
 superada: 1
```

Contagem cruzada entre índice e disco:

```
linhas da tabela completa: 162
arquivos PRD: 162
```

Seções do contrato de UI em ordem crescente, com o Changelog por último:

```
## 13. Critério de parada
## 14. Princípios de UX para interfaces geradas por IA
## 15. Changelog
```

Raiz limpa: `runserver-codex.log`, `runserver-codex.err.log` e
`.codex-runtime/` não existem mais no worktree. `git ls-files` confirmou que
nenhum deles estava rastreado.

## Evidence

- Quatro slash commands com frontmatter válido e comandos reais conferidos.
- Índice com 162 linhas para 162 arquivos, status extraído do disco.
- `LICENSE` e `.gitattributes` presentes.
- Contrato de UI com seções em ordem.
- Raiz sem resíduos; suíte de 722 testes verde.

## Implemented

- `.claude/commands/` ganhou `reset-local.md`, `sync-skills.md`,
 `validar-tela.md` e `auditar-paridade.md`, adaptados ao LV: os 21 seeds na
 ordem canônica, as quatro variáveis obrigatórias do ciclo, a porta 8000 e
 `http://localhost:8000/login/` como confirmação.
- `scripts/build_prd_index.py` criado: regenera a tabela de
 `docs/prd/README.md` extraindo o status da seção `## Final status` de cada
 arquivo e calculando o próximo número livre.
- `docs/prd/README.md` regenerado com coluna Status e a linha de próximo
 número livre isolada. O bloco de renumeração da PRD-079 foi preservado.
- `LICENSE` MIT criado.
- `.gitattributes` passou a declarar `* text=auto`, `*.sh`, `*.yaml` e `*.yml`.
- `.gitignore` passou a cobrir `.codex-runtime/`.
- `.claude/launch.json` usa caminho relativo, rótulo `Django Dev Server` e
 `autoPort: false`, igual a padrão canônico e outro repositório.
- `docs/UI-SCREEN-CONTRACT.md`: a seção de princípios de UX virou 14 e o
 Changelog virou 15.
- `docs/prd/PRD-158-*.md` marcada como superada por esta PRD, com a
 justificativa de por que a dependência da PRD-154 deixou de bloquear.
- `README.md` descreve os dois workflows, os slash commands, o espelhamento
 de skills e como regenerar o índice.

## Cleanup findings

- **O achado da auditoria sobre a PRD-154 não se confirmou.** A leitura dos
 arquivos mostrou que `PRD-155:211` e `PRD-159:203` declaram explicitamente
 "PRD-154 não foi implementada" e a colocam fora de escopo. Elas não
 dependem dela como pré-requisito satisfeito; excluíram-na de propósito. O
 status "Não iniciada" está correto e nada foi alterado.
- **Divergência real encontrada fora do escopo:** `CLAUDE.md` e `AGENTS.md`
 do LV não declaram a natureza de MVP descartável, que padrão canônico e outro repositório
 declaram. É exatamente o objetivo da PRD-154, ainda aberta. Não foi
 implementada aqui — está fora do escopo desta PRD e tem dono.
- `.gitattributes` com `* text=auto` não provocou renormalização em massa.
- Backup do índice foi feito antes da regeneração e descartado após a
 verificação.

## Follow-up PRDs

- PRD-162 — reset remoto endurecido, deploy documentado e observabilidade.
- PRD-154 continua aberta e permanece o lugar certo para declarar a natureza
 de MVP descartável nos contratos do LV.

## Deviations from plan

- O plano previa acrescentar a coluna de status ao índice. A implementação
 criou um script (`scripts/build_prd_index.py`) em vez de editar a tabela à
 mão, porque o critério exigia que o status fosse extraído do arquivo e
 "nunca digitado à mão" — com 162 PRDs, edição manual não sobrevive à
 próxima PRD.
- O plano tratava a inconsistência da PRD-154 como defeito a corrigir. A
 verificação refutou o achado; nada foi alterado e a refutação ficou
 registrada em `Cleanup findings`.
- A contagem de linhas do índice precisou de padrão mais específico que
 `^| [0-9]`: o bloco de renumeração da PRD-079 também tem linhas nesse
 formato. Com o padrão correto, 162 linhas para 162 arquivos.

## Pending

- Commitar o worktree. Nenhum commit foi feito pelo agente nesta série.
- Rodar `scripts/build_prd_index.py` no CI para impedir que o índice
 envelheça. Não foi feito aqui para não misturar com o escopo de
 infraestrutura da PRD-162.

## Final status

Concluída. Os quatro slash commands existem e citam apenas comandos reais, o
índice de PRDs responde ao estado de cada uma sem abrir arquivo e é
regenerável, os artefatos de base estão em paridade com os e a raiz do
worktree está limpa. Suíte completa verde em 722 testes.
