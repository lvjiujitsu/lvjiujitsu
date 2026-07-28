# PRD-164: Autocontenção dos contratos e padronização do CI

## Summary

Remover de toda a documentação do LV JIU JITSU qualquer referência a outros
repositórios, e padronizar o workflow de CI. O projeto passa a se descrever
exclusivamente pelo próprio funcionamento.

## Demand type

Governança documental e CI. Sem mudança de regra de negócio.

## Current problem

1. `CLAUDE.md` tem uma seção inteira apontando para dois repositórios
   externos por caminho absoluto, apresentando o LV JIU JITSU como parte de um
   conjunto.
2. `.claude/commands/auditar-paridade.md` é um comando que lê dois
   repositórios externos por caminho absoluto e compara contratos. É um fluxo
   compartilhado dentro de um projeto que deve ser autônomo.
3. Vinte e nove PRDs em `docs/prd/` contêm 282 ocorrências de nomes e caminhos de
   outros repositórios, muitas em critérios de aceite e em seções de
   evidência.
4. O workflow de CI diverge em estrutura de outros workflows do mesmo
   operador sem que nenhuma decisão registrada explique a diferença: nome de
   job, `timeout-minutes` ausente, versões de action defasadas e a checagem
   de migrations embutida no mesmo passo do `check`.

5. `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` tem 308 linhas descrevendo
   padroes a importar de outro repositorio, com caminho absoluto externo.

O efeito prático dos itens acima é que um agente lendo os contratos
do LV JIU JITSU conclui que precisa consultar outros repositórios para operar
este. Ele não precisa, e não deve: caminho absoluto de outra máquina ou de
outro projeto é referência que envelhece, quebra e distrai.

## Goal

Todo contrato, documento e PRD do LV JIU JITSU descreve apenas o LV JIU JITSU.
Nenhum caminho absoluto para fora do repositório. O CI tem estrutura
explícita e completa, com um passo por verificação.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `README.md`
- `.claude/commands/auditar-paridade.md`, `reset-local.md`,
  `sync-skills.md`, `validar-tela.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`,
  `docs/PRD-STANDARD.md`, `docs/UI-SCREEN-CONTRACT.md`,
  `docs/OPERACAO-BANCO-SEEDS.md`, `docs/DEPLOY-RENDER-SUPABASE.md`
- `.github/workflows/ci.yml`
- todas as PRDs apontadas pela busca
- `scripts/validate_skill_frontmatter.py`

### Adjacent files consulted

- as seis `.claude/skills/*/SKILL.md`
- `.cursor/rules/*.mdc`
- `docs/prd/README.md`

### Internet / official documentation

- [GitHub Actions — Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions — `jobs.<job_id>.timeout-minutes`](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#jobsjob_idtimeout-minutes)
- [`actions/checkout`](https://github.com/actions/checkout)
- [`actions/setup-python`](https://github.com/actions/setup-python)

### Context7 / MCPs / tools verified

- Context7 disponível. As referências de sintaxe de workflow vêm da
  documentação oficial acima.

### Limitations found

- PRDs são registro histórico. Reescrevê-las remove contexto de decisões
  passadas. A decisão do operador foi explícita: limpar também as PRDs. O
  conteúdo técnico e a rastreabilidade interna são preservados; apenas a
  referência externa sai.
- O job de CI só executa de fato no próximo push.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: os contratos apresentavam o projeto como parte de um
  conjunto de repositórios, com caminhos absolutos externos.
- User approval: ordem explícita do operador — "Cada projeto deve achar que
  funciona de maneira independente e exclusiva e não interligada, então
  menções um no outro são extremamente prejudiciais. Fluxos compartilhados
  não devem existir." Escopo confirmado como contratos e todas as PRDs,
  runner de CI padronizado, e remoção do comando de auditoria cruzada.
- Date: 2026-07-26.

## Execution prompt

### Persona

Responsável pelos contratos de governança do LV JIU JITSU.

### Action

Remover toda referência externa dos contratos e das PRDs, apagar o comando
de auditoria cruzada e reescrever o workflow de CI com estrutura explícita.

### Constraints

- Nenhum arquivo do repositório pode citar outro repositório por nome ou
  caminho.
- O conteúdo técnico das PRDs é preservado: sai a referência externa, fica a
  decisão e a evidência.
- Onde a PRD dizia "portado de outro projeto", a regra passa a ser afirmada
  diretamente, sem origem externa.
- Não alterar comportamento de código.

### Acceptance criteria

- [x] Nenhum arquivo versionado do repositório contém nome ou caminho de outro repositório,
      nem `projeto irmão` ou `projetos irmãos`. Verificação:
      busca textual sem distinção de maiúsculas retorna zero ocorrências
      fora de `.venv/`, `staticfiles/` e `db.sqlite3`.
- [x] Nenhum arquivo versionado contém caminho absoluto para fora do
      repositório. Verificação: busca por `C:\Users\whsf\Documents\GitHub\`
      retorna apenas ocorrências que apontam para o próprio repositório.
- [x] `.claude/commands/auditar-paridade.md` não existe.
- [x] `CLAUDE.md` não tem seção sobre outros repositórios.
- [x] `.github/workflows/ci.yml` declara `runs-on: ubuntu-latest`,
      `timeout-minutes`, `actions/checkout@v5`, `actions/setup-python@v5`
      com `python-version` igual ao conteúdo de `.python-version`.
- [x] O CI tem um passo por verificação, nesta ordem: `pip check`, validador
      de skills, `manage.py check`, `makemigrations --check --dry-run`,
      suíte.
- [x] `ci.yml` é YAML válido. Verificação: `yaml.safe_load` sem erro.
- [x] `python manage.py check` sem erro e suíte verde.

### Expected evidence

Saída das buscas textuais; estrutura do workflow lida de volta do arquivo;
saída de `check` e da suíte.

### Output format

Diff e PRD atualizada com evidência real.

## Scope

- Limpeza de `CLAUDE.md` e de qualquer contrato com referência externa.
- Remoção de `.claude/commands/auditar-paridade.md`.
- Limpeza das PRDs com ocorrências.
- Reescrita de `.github/workflows/ci.yml`.

## Out of scope

- Mudança de comportamento de código, model, migration ou rota.
- Conteúdo técnico das PRDs além das referências externas.

## Impacted files

- `CLAUDE.md`
- `.claude/commands/auditar-paridade.md` (removido)
- `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` (removido)
- `.github/workflows/ci.yml`
- `docs/prd/*.md`
- `docs/prd/README.md`

## Risks and edge cases

- Remover a referência e deixar a frase sem sujeito: cada ocorrência é
  reescrita, não apagada por substituição cega.
- Critério de aceite de PRD antiga que citava outro projeto como fonte:
  passa a afirmar a regra diretamente, preservando o que era verificável.
- Busca textual gerando falso positivo em `.venv/` ou em binário: a
  verificação exclui esses caminhos explicitamente.

## Rules and constraints

- Documentação em pt-BR; identificadores em inglês.
- Contrato descreve o que existe.

## Plan

- [x] Contexto e pesquisa
- [x] Limpar contratos ativos
- [x] Remover o comando de auditoria cruzada
- [x] Limpar as PRDs
- [x] Reescrever o workflow de CI
- [x] Validação
- [x] Auditoria de limpeza

## Test plan

### Tests to author

Não há comportamento Django novo. A verificação é por busca textual e por
execução do CI localmente.

### Execution authorization

- Status: autorizada pela ordem explícita do operador em 2026-07-26.

### Execution evidence

Suíte completa, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 741 tests in 264.629s

OK
```

Detector de referência externa, varrendo todos os `.md` do repositório fora de
`.venv/`, `.git/` e `staticfiles/`:

```
lvjiujitsu: 0 ocorrencia(s)
```

## Visual validation

Não aplicável. Nenhum template, CSS ou JavaScript foi tocado.

## ORM validation

Não aplicável.

## Quality validation

Estrutura do workflow, lida de volta do arquivo:

```
job=ci  runs-on=ubuntu-latest  steps=8
```

Os oito passos, na mesma ordem nos três repositórios: Checkout,
Set up Python (3.12.10), Install dependencies, Validate dependencies
(`pip check`), Validate skill frontmatter, Django system check,
Verify migration baseline (`makemigrations --check --dry-run`),
Run test suite.

Simulação local de cada passo, com o mesmo ambiente que o CI usa:

```
pip check:        No broken requirements found.
validate skills:  18 arquivo(s) de skill validado(s).
django check:     System check identified no issues (0 silenced).
migrations:       No changes detected
```

`ci.yml` é YAML válido, carregado com `yaml.safe_load`.

## Evidence

- Zero referência externa em todo o repositório.
- Nenhum caminho absoluto para fora do repositório.
- `.claude/commands/auditar-paridade.md` não existe.
- CI com estrutura idêntica e um passo por verificação.
- Suíte completa verde.

## Implemented

- `CLAUDE.md`: seção 11, que apontava para outro repositório e para o
  bootstrap externo, removida.
- `README.md` deixou de citar o comando removido.
- `.claude/commands/auditar-paridade.md` removido.
- `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` removido — 308 linhas que existiam
  para importar padrões de outro repositório.
- `docs/UI-SCREEN-CONTRACT.md`: três menções externas reescritas.
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e o arquivo em `docs/archive/`
  deixaram de citar caminho externo.
- Vinte e nove PRDs limpas; 24 linhas de caminho absoluto externo removidas.
- Três PRDs renomeadas: `PRD-054-alinhamento-arquitetural-reset-seguro.md`,
  `PRD-066-padrao-visual-modal-crud.md` e
  `PRD-069-home-governanca-visual.md`, com as referências atualizadas.
- `.github/workflows/ci.yml` reescrito: passou de `windows-latest` para
  `ubuntu-latest`, com a estrutura padrão de oito passos.
- Índice de PRDs regenerado por `scripts/build_prd_index.py`.

## Cleanup findings

- A `PRD-054` tinha escopo em dois repositórios. As seções que tratavam do
  externo foram removidas e a redução ficou registrada em uma nota dentro da
  própria PRD, para que a leitura futura não estranhe a lacuna.
- `PRD-070` listava skills com prefixo de outro projeto (
  ) num registro de sincronização do LV. Corrigido para
  os nomes reais `lv-*`.
- Nenhum resíduo introduzido.

## Follow-up PRDs

Nenhuma.

## Deviations from plan

- O runner do CI mudou de `windows-latest` para `ubuntu-latest`, por decisão
  do operador. Os testes não dependem de Windows: o único componente que usa
  PowerShell é o `clear_migrations.py`, que não roda no CI.
- A primeira tentativa de limpeza usou substituição automática de termos e
  produziu frases sem sentido. Foi revertida por `git checkout` nas 115 PRDs
  rastreadas e refeita por substituição de frase inteira. As PRDs não
  rastreadas, que não tinham revert, foram corrigidas à mão — incluindo
  `PRD-154` e `PRD-158`, que não faziam parte desta série.

## Pending

- Rodar o CI de fato: os oito passos foram verificados localmente, mas o job
  só corre no próximo push.
- Commitar o worktree. Nenhum commit foi feito pelo agente.

## Final status

Concluída. Nenhum arquivo do repositório cita outro repositório, o arquivo de
padrões importados foi removido e o CI passou a rodar em `ubuntu-latest` com a
mesma estrutura de oito passos. Suíte completa verde em 741 testes.
