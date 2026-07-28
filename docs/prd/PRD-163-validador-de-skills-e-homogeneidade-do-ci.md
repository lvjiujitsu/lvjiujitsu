# PRD-163: Validador de skills e homogeneidade do CI

## Summary

Portar `scripts/validate_skill_frontmatter.py` canônico e ligá-lo ao CI do
LV. É o último item de heterogeneidade de CI entre o projeto,
registrado como follow-up pelas PRDs 030 do outro repositório e 162 do LV.

## Demand type

Governança e CI. Sem mudança de regra de negócio.

## Current problem

padrão canônico e outro repositório validam as skills no CI: o script exige os três
diretórios de plataforma, o mesmo conjunto de skills em cada um, conteúdo
byte a byte idêntico ao de `.claude/skills/` e metadado Codex íntegro em
UTF-8 com LF.

O LV não tem o script. Seu `.github/workflows/ci.yml` roda `manage.py check`,
`makemigrations --check` e a suíte, mas nada confere as skills. A regra de
espelhamento existe em `docs/PLATFORM-ADAPTERS.md` e em
`.claude/commands/sync-skills.md`, e depende de alguém lembrar de rodar a
comparação à mão.

O risco não é hipotético: o outro repositório teve os seis `agents/openai.yaml`
corrompidos por replacement character, e a PRD-027 declarou-os "normalizados
em UTF-8" porque a checagem de então só verificava se o YAML era parseável.
A correção veio na PRD-028, e a defesa automatizada na PRD-030.

## Goal

O LV falha o build quando uma skill some de uma plataforma, diverge da fonte
ou tem metadado Codex corrompido — a mesma defesa que os dois já têm.

## Context Ledger

### Files read in full

- `.github/workflows/ci.yml`
- `.claude/commands/sync-skills.md`
- `docs/PLATFORM-ADAPTERS.md`
- as seis `.claude/skills/*/SKILL.md`
- os seis `.agents/skills/*/agents/openai.yaml`

### Adjacent files consulted

- `requirements.txt` (PyYAML)
- `.gitattributes`
- `docs/prd/PRD-162-reset-remoto-deploy-e-observabilidade.md`

### Internet / official documentation

- [Claude Code — Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [GitHub Actions — `actions/setup-python`](https://github.com/actions/setup-python)

### Context7 / MCPs / tools verified

- Context7 disponível. O script usa apenas biblioteca padrão e PyYAML, já
 presente em `requirements.txt`.

### Limitations found

- O job em si só roda no próximo push; a verificação aqui é local.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de paridade do projeto e o
 follow-up registrado nas PRDs 030 e 162.
- User approval: ordem explícita do operador em 2026-07-25, que pediu
 paridade completa após a execução das PRDs.
- Date: 2026-07-26.

## Execution prompt

### Persona

Responsável pela governança multiplataforma do LV.

### Action

Portar o validador, adaptá-lo aos nomes `lv-*` e ligá-lo ao CI.

### Context

o projeto compartilham o framework de governança. Regra que ninguém
verifica volta a divergir.

### Constraints

- Não alterar o conteúdo das seis `SKILL.md`, já sincronizadas.
- O script roda em qualquer plataforma, sem dependência de PowerShell.

### Acceptance criteria

- [ ] `scripts/validate_skill_frontmatter.py` existe e valida frontmatter,
 cobertura nas três plataformas, conteúdo idêntico à fonte e integridade
 do metadado Codex.
- [ ] O script reporta 6 skills nas 3 plataformas e 18 arquivos validados.
- [ ] O script falha quando um `openai.yaml` recebe replacement character.
 Verificação: introduzir a corrupção, observar a falha, restaurar.
- [ ] `.github/workflows/ci.yml` executa o script e pina Python `3.12.10`.
- [ ] `manage.py check` sem erro e suíte de testes verde.

### Expected evidence

Saída do script; saída do teste de regressão de encoding; diff do workflow.

### Output format

Diff e PRD atualizada com evidência real.

## Scope

- `scripts/validate_skill_frontmatter.py`.
- Passo de validação no CI e pin do Python.

## Out of scope

- Conteúdo das skills.
- Qualquer mudança de produto.

## Impacted files

- `scripts/validate_skill_frontmatter.py` (novo)
- `.github/workflows/ci.yml`
- `docs/prd/README.md`

## Risks and edge cases

- Script exigindo skill que ainda não existe em uma plataforma e quebrando o
 build: as seis já existem nas três, verificado antes de ligar ao CI.
- PyYAML ausente no ambiente de CI: já está em `requirements.txt`.

## Rules and constraints

- Menor mudança correta; documentação em pt-BR.

## Plan

- [ ] Contexto e pesquisa
- [ ] Portar o script e adaptar os nomes
- [ ] Verificar que ele detecta a regressão de encoding
- [ ] Ligar ao CI e pinar o Python
- [ ] Validação
- [ ] Auditoria de limpeza

## Test plan

### Tests to author

Não há comportamento Django novo. A verificação é por execução do próprio
script, incluindo um caso negativo com corrupção introduzida e revertida.

### Execution authorization

- Status: autorizada pela ordem explícita do operador.

### Execution evidence

Execução do script:

```
[OK] 6 skill(s) nas 3 plataformas: lv-cleanup-audit, lv-django-delivery,
 lv-prd, lv-prompt-builder, lv-task-intake, lv-ui-delivery
[OK] 6 metadado(s) Codex integro(s) em UTF-8 com LF.
18 arquivo(s) de skill validado(s).
```

Caso negativo, com replacement character introduzido em
`.agents/skills/lv-prd/agents/openai.yaml` e depois revertido:

```
--- com corrupcao ---
ValueError: Replacement character (encoding corrompido): .agents\skills\lv-prd\agents\openai.yaml
--- restaurado ---
18 arquivo(s) de skill validado(s).
```

## Visual validation

Não aplicável. Nenhum template, CSS ou JavaScript foi tocado.

## ORM validation

Não aplicável.

## Quality validation

`python -m pip check` — `No broken requirements found.`

`ci.yml` continua sendo YAML válido, carregado com `yaml.safe_load`. Passos
do job, na ordem:

```
Checkout → Set up Python (3.12.10) → Install dependencies
→ Validate dependencies → Validate skill frontmatter
→ Django system check → Verify migration baseline → Run test suite
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Evidence

- Script reportando 6 skills nas 3 plataformas e 18 arquivos.
- Falha comprovada no caso de encoding corrompido.
- `pip check` limpo; `ci.yml` válido com os dois passos novos.
- `manage.py check` sem erro.

## Implemented

- `scripts/validate_skill_frontmatter.py` adotado, com
 `load_frontmatter`, `validate_platform_coverage` e
 `validate_codex_metadata`.
- `.github/workflows/ci.yml` ganhou os passos `Validate dependencies`
 (`pip check`) e `Validate skill frontmatter`.

## Cleanup findings

- O CI do LV já pinava Python `3.12.10`; nada a mudar nesse ponto.
- Com esta PRD, o projeto têm o mesmo conjunto de verificações no CI:
 `pip check`, validador de skills, `manage.py check`,
 `makemigrations --check` e a suíte. O item D13 da auditoria de paridade
 está fechado.
- Nenhum resíduo introduzido.

## Follow-up PRDs

- Continua aberto o item registrado na PRD-162: remover `lv-pessoas-2026` de
 `docs/OPERACAO-BANCO-SEEDS.md`, junto com a decisão sobre aposentar
 `seed_system_people_flow_samples`.

## Deviations from plan

- Além do validador, foi acrescentado o passo `pip check`, que o padrão canônico e o
 outro repositório já rodavam e o LV não. Sem ele a homogeneidade de CI ficaria
 incompleta, que é justamente o objetivo desta PRD.

## Pending

- Rodar o CI de fato: os passos foram verificados localmente, mas o job só
 corre no próximo push.
- Commitar o worktree. Nenhum commit foi feito pelo agente nesta série.

## Final status

Concluída. O LV falha o build quando uma skill some de uma plataforma,
diverge da fonte ou tem metadado Codex corrompido — a mesma defesa dos dois
. o projeto passam a rodar o mesmo conjunto de verificações.
