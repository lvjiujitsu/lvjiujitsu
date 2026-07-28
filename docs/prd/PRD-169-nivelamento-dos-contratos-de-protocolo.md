# PRD-169: Nivelamento dos contratos de protocolo

## Summary

Os contratos de protocolo tinham título de seção igual e corpo divergente. Esta
PRD unifica `AGENTS.md`, `docs/PRD-STANDARD.md`, `docs/AGENT-WORKFLOW.md`,
`docs/PLATFORM-ADAPTERS.md`, as três regras do Cursor e os três slash commands,
adotando por eixo a redação mais completa que existia. As duas seções de
pagamento que viviam nos documentos de procedimento foram movidas para
`CLAUDE.md`, onde fato de produto tem dono, e `/reset-local` e `/sync-skills`
passam a ser de invocação manual.

## Demand type

Revisão de governança. Sem mudança de código Python, de schema ou de UI.

## Current problem

- `AGENTS.md` tinha as 14 seções com título idêntico e corpo diferente. A
  tabela de fontes de verdade não dizia quem referencia cada dono, então nada
  impedia uma regra de ser repetida em dois arquivos.
- `docs/PRD-STANDARD.md` descrevia **template diferente** de PRD. O padrão
  daqui não tinha `Visual validation` decomposto nem `ORM validation`
  separando leitura de escrita, e nada dizia o que fazer com seção que não se
  aplica.
- `docs/AGENT-WORKFLOW.md` tinha 201 linhas contra 282 do documento mais
  completo do mesmo eixo, sem o checklist de auditoria de renderização e sem a
  tabela de entrada, saída e critério por etapa.
- `docs/AGENT-WORKFLOW.md` §11 e `docs/PLATFORM-ADAPTERS.md` §6 tratavam de
  pagamento. Procedimento de gateway não é protocolo de agente: é fato de
  produto, e mantê-lo ali criava dois donos para o mesmo assunto.
- `.claude/commands/reset-local.md` e `sync-skills.md` **não tinham**
  `disable-model-invocation`. O primeiro destrói o banco local: sem a chave,
  um agente podia acionar o ciclo destrutivo por conta própria.
- `/validar-tela` não exigia auditoria de renderização, embora o workflow a
  torne obrigatória.

## Goal

Cada contrato de protocolo tem uma única redação, variando apenas nome do
projeto, nome do app e prefixo de skill. Pagamento tem um dono só. O que o
contrato afirma sobre guarda de comando é verdade no arquivo.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`
- `docs/PRD-STANDARD.md`, `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`
- `.cursor/rules/protocol.mdc`, `.cursor/rules/django.mdc`,
  `.cursor/rules/ui.mdc`
- `.claude/commands/reset-local.md`, `.claude/commands/sync-skills.md`,
  `.claude/commands/validar-tela.md`

### Adjacent files consulted

- `.claude/settings.json`, `.claude/launch.json`, `.mcp.json`,
  `.codex/config.toml`, `.cursor/mcp.json`
- `scripts/validate_skill_frontmatter.py`, `scripts/build_prd_index.py`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `docs/prd/PRD-168-guarda-de-numero-duplicado-e-higiene-de-settings.md`

### Internet / official documentation

- Claude Code, frontmatter de slash command e `disable-model-invocation`:
  https://docs.claude.com/en/docs/claude-code/slash-commands

### Context7 / MCPs / tools verified

- Context7 não foi consultado: a mudança é documental e não envolve API de
  biblioteca.

### Limitations found

- O verificador de links usado na validação trata a menção genérica
  `` `SKILL.md` `` do §14 como caminho e reporta falso positivo. O resultado foi
  conferido à mão e não há link quebrado introduzido por esta PRD.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: tabela "melhor de cada eixo" apresentada com a auditoria.
- User approval: ratificada, e a Etapa 2 autorizada com "pode dar andamento".
- Date: 2026-07-26.

## Execution prompt

### Persona

Responsável pela governança documental do repositório.

### Action

Unificar os nove contratos de protocolo, mover o conteúdo de pagamento para
`CLAUDE.md` e corrigir a guarda de invocação dos slash commands.

### Context

MVP descartável. Contrato descreve o que existe; ao divergir do arquivo, o
arquivo vence e o contrato é corrigido na mesma mudança.

### Constraints

- variar somente nome do projeto, nome do app e prefixo de skill;
- não introduzir regra que o repositório ainda não cumpre;
- **nenhuma regra de pagamento pode se perder** na movimentação;
- a proibição absoluta de comentário e docstring **não** entra agora.

### Acceptance criteria

- [x] `AGENTS.md` com uma variante e tabela de fontes com coluna
      "Quem referencia";
- [x] `docs/PRD-STANDARD.md` com uma variante e template completo;
- [x] `docs/AGENT-WORKFLOW.md` com uma variante, incluindo a tabela de
      entrada/saída/critério e o checklist de auditoria de renderização;
- [x] `docs/PLATFORM-ADAPTERS.md` com uma variante;
- [x] as três `.cursor/rules/*.mdc` com uma variante cada;
- [x] `sync-skills.md` e `validar-tela.md` com uma variante cada;
- [x] `reset-local.md` com estrutura de seções idêntica, variando apenas a
      sequência de seeds;
- [x] `/reset-local` e `/sync-skills` com `disable-model-invocation: true`;
- [x] toda regra de pagamento das duas seções removidas presente em
      `CLAUDE.md` §9;
- [x] zero vazamento de nome de projeto entre repositórios;
- [x] `check`, `makemigrations --check --dry-run`,
      `build_prd_index.py --check` e `validate_skill_frontmatter.py` verdes.

### Expected evidence

Contagem de variantes por arquivo após normalização; conferência linha a linha
do conteúdo de pagamento movido; saída dos quatro gates.

### Output format

Diff documental e PRD atualizada com evidência.

## Scope

- `AGENTS.md`
- `docs/PRD-STANDARD.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `.cursor/rules/protocol.mdc`, `django.mdc`, `ui.mdc`
- `.claude/commands/reset-local.md`, `sync-skills.md`, `validar-tela.md`
- `CLAUDE.md` §9, apenas para receber o conteúdo de pagamento movido

## Out of scope

- O restante de `CLAUDE.md`, `README.md`, `docs/OPERACAO-BANCO-SEEDS.md`,
  `docs/DEPLOY-RENDER-SUPABASE.md` e `docs/UI-SCREEN-CONTRACT.md`.
- `requirements.txt`, `.gitignore` e o conjunto de chaves de env.
- Remoção de comentários e docstrings.
- Corpo das seis skills.
- `docs/archive/static-documentation-legacy/` e os três guias de wizard.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `AGENTS.md` | 187 → 226 linhas; tabela de fontes com dono e referenciadores |
| `docs/PRD-STANDARD.md` | 105 → 164 linhas; template completo; regra de seção não aplicável |
| `docs/AGENT-WORKFLOW.md` | 201 → 333 linhas; tabela de etapas, checklist de renderização, §11 Pagamentos removida |
| `docs/PLATFORM-ADAPTERS.md` | 88 → 125 linhas; matriz por plataforma, §6 Pagamentos removida |
| `.cursor/rules/protocol.mdc` | 16 linhas; sem mudança material |
| `.cursor/rules/django.mdc` | 12 → 13 linhas |
| `.cursor/rules/ui.mdc` | 12 → 13 linhas |
| `.claude/commands/reset-local.md` | 105 → 126 linhas; ganha `disable-model-invocation`, guarda de porta, guarda de arquivos e `check` |
| `.claude/commands/sync-skills.md` | 59 → 79 linhas; ganha `disable-model-invocation` e a checagem de `openai.yaml` |
| `.claude/commands/validar-tela.md` | 55 → 65 linhas; auditoria de renderização e estados |
| `CLAUDE.md` | §9 recebe quatro regras de pagamento vindas dos documentos de procedimento |

## Risks and edge cases

- Mover pagamento para `CLAUDE.md` poderia perder a regra mais importante do
  conjunto — "não simular pagamento por inferência nem declarar confirmação sem
  evidência do gateway e do ORM". A conferência foi feita item a item e está na
  seção de evidência.
- `disable-model-invocation` em `/reset-local` e `/sync-skills` impede o modelo
  de acioná-los sozinho. É exatamente o objetivo: o primeiro é destrutivo e o
  segundo é auditoria que o operador pede.
- A guarda nova de porta encerra processo. Ela só encerra quando a linha de
  comando corresponde a `manage.py runserver localhost:8000`; para qualquer
  outro PID, aborta e reporta.
- `reset-local.md` continua com três variantes por causa da sequência de 21
  seeds. Isso é dado de produto, dono de `docs/OPERACAO-BANCO-SEEDS.md`.

## Rules and constraints

- `AGENTS.md` §2: um dono por assunto; ao divergir do arquivo, o arquivo vence.
- `AGENTS.md` §12: dívida material fora do escopo vira follow-up, não
  implementação silenciosa.

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

Nenhum. A mudança é documental e não há comportamento testável: o que se pode
verificar é paridade de conteúdo e integridade de link, feito por comando na
seção de evidência.

`system/tests/test_seed_docs_contract.py` já lê
`docs/OPERACAO-BANCO-SEEDS.md`, arquivo fora do escopo desta PRD, e foi
executado como parte da suíte.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 292.150s
OK
exit=0
```

Suíte executada nesta sessão para confirmar ausência de regressão; nenhum teste
novo.

## Visual validation

### Design approval

Não aplicável: nenhuma mudança visual.

### Routes and states

Não aplicável: nenhuma rota alterada.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

`manage.py check` sem aviso.

### Screenshot / snapshot

Não aplicável: a mudança é documental.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

Nenhuma escrita executada.

## Quality validation

```text
python manage.py check                        -> no issues, exit=0
python scripts/build_prd_index.py --check     -> Indice em dia, exit=0
python scripts/validate_skill_frontmatter.py  -> 18 arquivos validados, exit=0
python -m pip check                           -> No broken requirements, exit=0
```

## Evidence

Variantes por arquivo após normalizar nome de projeto, nome de app e prefixo de
skill, nos três repositórios do mesmo eixo:

```text
AGENTS.md                          variantes=1  linhas=226/226/226
docs/PRD-STANDARD.md               variantes=1  linhas=164/164/164
docs/AGENT-WORKFLOW.md             variantes=1  linhas=333/333/333
docs/PLATFORM-ADAPTERS.md          variantes=1  linhas=125/125/125
.claude/commands/sync-skills.md    variantes=1  linhas=79/79/79
.claude/commands/validar-tela.md   variantes=1  linhas=65/65/65
.cursor/rules/protocol.mdc         variantes=1  linhas=16/16/16
.cursor/rules/django.mdc           variantes=1  linhas=13/13/13
.cursor/rules/ui.mdc               variantes=1  linhas=13/13/13
.claude/commands/reset-local.md    variantes=3  linhas=111/126/97
```

Conferência do conteúdo de pagamento movido para `CLAUDE.md` §9:

| Regra de origem | Destino |
|---|---|
| ler o fluxo completo e os documentos de Asaas/Stripe | já coberto pela última linha do §9, que aponta o guia e a PRD-058 |
| verificar settings e ambiente sem expor segredos | já coberto por `AGENTS.md` §10 |
| separar redirect, webhook server-to-server e confirmação no banco | linha nova no §9 |
| Asaas local exige URL pública HTTPS válida | já existia no §9 |
| Stripe local pode exigir Stripe CLI e secret temporário | linha nova no §9 |
| não simular pagamento por inferência nem declarar confirmação sem evidência do gateway e do ORM | linha nova no §9, em negrito |
| fluxo externo pode exigir Chrome, túnel ou painel do gateway | linha nova no §9 |

Nenhuma regra foi perdida: três já tinham cobertura e quatro passaram a existir
explicitamente no §9.

Frontmatter dos slash commands:

```text
reset-local    disable-model-invocation: true
sync-skills    disable-model-invocation: true
validar-tela   argument-hint: "<rota>"
```

## Implemented

- `AGENTS.md` unificado, com tabela de dono e referenciadores;
- `docs/PRD-STANDARD.md` com o template completo e a regra de seção não
  aplicável;
- `docs/AGENT-WORKFLOW.md` unificado, com tabela de etapas e checklist de
  auditoria de renderização;
- `docs/PLATFORM-ADAPTERS.md` unificado;
- pagamento com um dono só: as duas seções de procedimento foram removidas e o
  conteúdo consolidado em `CLAUDE.md` §9;
- as três regras do Cursor unificadas;
- `/reset-local` e `/sync-skills` com invocação manual — a correção de maior
  consequência desta PRD, porque o ciclo destrutivo estava acionável pelo
  modelo;
- `/validar-tela` exigindo os estados e a auditoria de renderização.

## Cleanup findings

- `system/tests/test_class_catalog.py` tem 0 linhas: arquivo de teste vazio.
- `docs/archive/static-documentation-legacy/` guarda 12 documentos de
  arquitetura substituídos pelos contratos atuais.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` não é PRD numerada e obriga o
  gerador a manter uma exceção nomeada em `KNOWN_EXCEPTIONS`.
- `docs/wizard-step-plan-*.md`: três guias soltos na raiz de `docs/`.
- `settings.py` usa aspas simples enquanto os demais arquivos do eixo usam
  aspas duplas.
- `.env` declara `DJANGO_DEBUG=1` em vez de `True`.
- Não existe `seed_test_data`: dado fictício vem de quatro seeds
  `seed_system_initial_test_*`, o que quebra o par com `clear_test_data`.
- A branch local `stage` não tem remoto correspondente; o remoto é
  `origin/stage-visual`.
- `.claude/settings.local.json` duplica exatamente `settings.json`.
- `.github/workflows/copilot-setup-steps.yml` existe só aqui.

## Follow-up PRDs

Etapas seguintes já acordadas com o operador: contratos de produto,
infraestrutura e ambiente, estrutura e limpeza de comentários e docstrings.

## Deviations from plan

Duas.

O plano previa mover a proibição absoluta de comentário e docstring para o §10
nesta etapa. Foi adiada para a etapa de limpeza: proibir na Etapa 2 e remover
na Etapa 6 deixaria o contrato afirmando por quatro etapas algo que o código
não cumpre, exatamente o que o §2 proíbe.

`CLAUDE.md` estava fora do escopo declarado e recebeu quatro linhas. A
alternativa era remover as seções de pagamento dos documentos de procedimento e
confiar que a etapa seguinte recolocaria as regras — o que perderia a guarda
mais importante do conjunto no intervalo. A edição foi limitada ao §9 e está
registrada aqui.

## Pending

- Os dez achados de limpeza acima, distribuídos entre as Etapas 3, 4, 5 e 6. A
  branch sem remoto e o `settings.local.json` dependem de decisão do operador.

## Final status

Concluída. Nove dos dez arquivos com variante única; o décimo com estrutura
idêntica e sequência de seeds própria, por ser dado de produto. Pagamento com
dono único e nenhuma regra perdida. Quatro gates verdes e suíte sem regressão.
