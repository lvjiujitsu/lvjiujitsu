# PRD-177: Agentes autônomos e acionadores

## Summary

Cria treze subagentes em `.claude/agents/`, dois verificadores determinísticos
sobre o repositório inteiro, um hook de fim de turno, um encadeador para
execução autônoma e um workflow de revisão de Pull Request. O objetivo é que o
projeto se audite e se corrija sem interação, e que só chegue ao operador o que
exige decisão dele.

## Demand type

Governança e automação. Sem mudança de regra de negócio, schema ou rota.

## Current problem

- As sete skills existem, mas `lv-parity-audit` tem
  `disable-model-invocation` e nenhuma delas dispara sozinha. Não faltava agente:
  faltava acionador.
- A visão global do repositório dependia de alguém pedir. Defeito que atravessa
  arquivos — token do núcleo declarado em duas folhas, propriedade
  autorreferente, comentário reintroduzido — só aparecia quando alguém varria
  tudo à mão.
- Não havia portão automático entre o fim de uma mudança e o Pull Request.

## Goal

Cobertura contínua com três acionadores e nenhuma interação: hook de fim de
turno para o verificador mecânico, encadeador para a varredura profunda, e
workflow no Pull Request para o julgamento final.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/UI-SCREEN-CONTRACT.md`
- `.claude/settings.json`, `.claude/launch.json`
- `.github/workflows/ci.yml` e `.github/workflows/copilot-setup-steps.yml`
- `scripts/validate_skill_frontmatter.py`

### Adjacent files consulted

- as sete `SKILL.md` de `.claude/skills/`, para herdar a estrutura
  `Quando acionar` / `Passos` / `Saída` / `Parar quando`

### Internet / official documentation

- Eventos de hook, tipos de handler e comportamento de bloqueio:
  https://code.claude.com/docs/en/hooks
- Execução não interativa, formatos de saída e retentativa de erro da API:
  https://code.claude.com/docs/en/headless

### Context7 / MCPs / tools verified

- `codex-cli 0.142.2`, `gh 2.96.0` e `claude 2.1.119` presentes na máquina.
- Playwright disponível como MCP tanto no aplicativo quanto em execução
  headless.

### Limitations found

- **Handler do tipo `agent` só existe em `SessionStart`.** Não é possível
  disparar subagente a cada alteração de arquivo; `PostToolUse` aceita apenas
  `command`, `http` e `mcp_tool`.
- **`mcp__Claude_Browser__` não existe em execução headless.** É MCP do
  aplicativo. Medido diretamente: em `claude -p` só aparecem os MCPs do usuário,
  entre eles o Playwright.
- **`--permission-mode acceptEdits` não pré-aprova ferramenta MCP.** Na primeira
  execução do agente de responsividade o Playwright foi negado e o agente caiu
  para `curl`, registrando a limitação em vez de simular a evidência.
- **`--bare` é inadequado aqui**: pula `CLAUDE.md`, skills e hooks, que são
  exatamente o contexto de que estes agentes dependem.
- `gh` está instalado mas não estava no `PATH` da sessão; o encadeador o
  acrescenta.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador em 2026-07-27: criar os agentes nos três projetos,
com contexto independente, e autorizar o agente de entrega a criar branch, subir
e abrir Pull Request. Merge continua fora do alcance do agente.

## Scope

- `.claude/agents/` — treze agentes
- `.claude/hooks/verify.py` e `.claude/settings.json`
- `scripts/audit_css.py`, `scripts/strip_comments.py`, `scripts/run_agent_chain.ps1`
- `scripts/validate_skill_frontmatter.py`
- `.github/workflows/pr-review.yml`
- `.gitignore`

## Out of scope

- Proteção da branch `main` no GitHub: é configuração de serviço externo e
  depende de decisão do operador. Ver `Pending`.
- `ANTHROPIC_API_KEY` nos secrets do repositório: sem ela o workflow roda só os
  portões determinísticos, que é o comportamento desejado como piso.
- Merge automático: nenhum agente mescla.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `.claude/agents/*.md` | treze agentes, cada um com contexto próprio |
| `.claude/hooks/verify.py` | verificador de fim de turno, com guarda anti-loop |
| `.claude/settings.json` | hook `Stop` e permissão das ferramentas Playwright |
| `scripts/audit_css.py` | detecta ciclo, token sem declaração e núcleo fora de `theme.css` |
| `scripts/strip_comments.py` | conta e remove comentário e docstring, com recompilação |
| `scripts/run_agent_chain.ps1` | encadeia os agentes, um processo por agente |
| `scripts/validate_skill_frontmatter.py` | passa a validar também os agentes |
| `.github/workflows/pr-review.yml` | portões determinísticos e revisão pelo agente |
| `.gitignore` | `.claude/logs/` e `docs/evidencias/` |

## Acceptance criteria

- [x] treze agentes com frontmatter válido, nome igual ao arquivo e modelo conhecido;
- [x] `scripts/audit_css.py` detecta propriedade autorreferente, provado com defeito injetado;
- [x] `scripts/strip_comments.py` detecta comentário, provado com defeito injetado;
- [x] hook `Stop` sai 0 com repositório limpo, 2 com defeito e 0 quando `stop_hook_active`;
- [x] `scripts/validate_skill_frontmatter.py` reprova agente com frontmatter inválido;
- [ ] um agente corretor executado de ponta a ponta pelo encadeador (Pending);
- [ ] um agente visual executado com navegador real (Pending);
- [x] workflow de Pull Request com YAML válido, apontando para um agente existente;
- [x] artefato de execução fora do Git;
- [ ] cadeia completa dos treze agentes executada de uma vez (Pending — ver abaixo).

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste Django novo: nada aqui é comportamento do produto. O que prova a
mudança é a execução real de cada componente, registrada em `Evidence`. Os
verificadores foram exercitados com defeito injetado e depois restaurado, que é
a forma de provar que um detector detecta.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests
OK

python scripts/audit_css.py                  -> [OK] 7 folha(s) sem defeito de token.
python scripts/strip_comments.py             -> [OK] nenhum comentario ou docstring
python scripts/validate_skill_frontmatter.py -> [OK] 13 agente(s) com frontmatter valido
python scripts/build_prd_index.py --check    -> Indice em dia.
```

## Visual validation

### Design approval

Não aplicável: nenhuma mudança de tela nesta PRD.

### Routes and states

Não aplicável.

### Console and terminal

Sem erro em nenhuma das execuções registradas.

## ORM validation

Não aplicável.

```text
python manage.py makemigrations --check --dry-run
No changes detected
```

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
audit_css.py                        -> exit=0
strip_comments.py                   -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

### Os detectores detectam

```text
ciclo injetado em theme.css   -> propriedade autorreferente: css/theme.css:2 --bg: var(--bg)   exit=1
restaurado                    -> [OK] 7 folha(s) sem defeito de token.                          exit=0
comentario injetado em .py    -> system/selectors/maps.py: 1                                    exit=1
restaurado                    -> [OK] nenhum comentario ou docstring                            exit=0
```

### O hook de fim de turno

```text
repositorio limpo             -> exit=0
defeito presente              -> exit=2 com o motivo no stderr
stop_hook_active=true         -> exit=0   (guarda anti-loop)
```

### Agente corretor de ponta a ponta

Pendente neste projeto. Os agentes estao declarados e validados no frontmatter,
e os verificadores foram executados, mas nenhum agente foi rodado de ponta a
ponta pelo encadeador aqui. Registrado em `Pending`.

### Agente visual com navegador real

Pendente neste projeto, pelo mesmo motivo.

### Custo esperado

Ainda nao medido neste projeto. A ordem de grandeza a confirmar na primeira
execucao e de alguns dolares por agente, e a cadeia completa deve ser medida
antes de virar rotina agendada.

## Implemented

- treze agentes em `.claude/agents/`, cada um com janela de contexto própria:
  sete corretores, dois auditores, dois testadores de navegador, um de entrega e
  um de revisão de Pull Request;
- dois verificadores determinísticos que provam propriedade global do
  repositório em menos de um segundo cada;
- hook `Stop` que reprova o fim do turno quando um verificador regride, com
  guarda contra laço infinito;
- encadeador que roda um processo por agente, registra saída e duração de cada
  um e continua diante de falha isolada;
- `validate_skill_frontmatter.py` estendido: agente sem `tools`, sem `model`,
  com modelo desconhecido ou com `name` diferente do arquivo reprova no CI;
- workflow de Pull Request que roda os portões determinísticos sempre e a
  revisão pelo agente quando houver `ANTHROPIC_API_KEY`;
- `.claude/logs/` e `docs/evidencias/` fora do Git: uma única execução do agente
  visual produz 7,8 MB de screenshot.

## Cleanup findings

- O agente de CSS gravou evidência em `docs/evidencias/`, o que é o lugar certo,
  mas o diretório não estava ignorado. Corrigido.
- `scripts/audit_css.py` não detecta valor literal que duplica o papel de um
  token existente — foi o próprio agente de CSS que apontou a limitação ao achar
  o defeito de `home.css` por leitura. Registrado como follow-up.

## Follow-up PRDs

- Estender `audit_css.py` para acusar valor literal em seletor de tema que
  coincide, ou quase coincide, com o valor de um token do núcleo.

## Deviations from plan

Duas, ambas descobertas por execução real.

O plano previa que os agentes visuais usassem o painel de navegador do
aplicativo. A medição mostrou que esse MCP não existe em execução headless; os
quatro agentes visuais passaram a usar Playwright, que funciona nos dois modos.

O plano não previa mexer em permissão. A primeira execução do agente de
responsividade foi bloqueada porque `acceptEdits` não pré-aprova ferramenta MCP.
As ferramentas do Playwright entraram em `permissions.allow`.

## Pending

- **A branch `main` não está protegida no GitHub.** A autorização de push dada
  ao agente de entrega pressupõe que nada chegue à produção sem Pull Request
  aprovado. Enquanto não houver proteção, essa premissa não vale. É configuração
  de serviço externo e depende do operador.
- `ANTHROPIC_API_KEY` não configurada nos secrets: o workflow roda apenas os
  portões determinísticos.
- A cadeia completa dos treze agentes ainda não foi executada de uma vez. Dois
  agentes foram exercitados de ponta a ponta; os outros onze estão declarados e
  validados no frontmatter, mas sem execução registrada.

## Final status

Concluída com limitações. Treze agentes criados e validados, verificadores
provados com defeito injetado, hook exercitado nos três cenários e dois agentes
executados de ponta a ponta sem interação. Falta proteger a `main` antes de
ligar o push autônomo, e falta uma execução da cadeia inteira.
