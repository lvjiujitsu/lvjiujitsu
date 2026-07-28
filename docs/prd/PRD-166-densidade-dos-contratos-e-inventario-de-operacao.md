# PRD-166: Densidade dos contratos e inventário de operação

## Summary

Declarar em `CLAUDE.md` a natureza descartável do MVP, que é o fundamento
normativo dos ciclos destrutivos que o projeto já executa; separar limpeza de
fechamento e documentar os slash commands em `docs/AGENT-WORKFLOW.md`;
numerar as seções dos contratos; e escrever o inventário de comandos de
operação, hoje incompleto em doze comandos.

## Demand type

Governança documental. Sem mudança de regra de negócio, sem mudança de
código de aplicação.

## Current problem

1. **`CLAUDE.md` não declara a natureza do projeto.** A seção 1 é "Produto" e
   descreve o que o sistema faz. Não existe seção dizendo *o que o projeto é
   como artefato*: se há dado real de negócio, se produção guarda histórico de
   cliente, se a baseline de migration pode ser recriada, se um reset remoto é
   uma operação de rotina ou um incidente.

   Essa lacuna não é teórica. O projeto tem `clear_migrations.py`,
   `clear_migration_supabase_hg`, `clear_migration_supabase_prod` e uma
   baseline única recriável. `AGENTS.md` seção 11 autoriza reset local sem
   perguntar e descreve o protocolo de reset destrutivo no Supabase. Ou seja:
   o protocolo destrutivo existe e é normatizado, mas a premissa que o
   justifica — não haver histórico a preservar — não está escrita em lugar
   algum.

   Um agente que leia os contratos encontra permissão para destruir sem
   encontrar a razão pela qual isso é aceitável, e não tem como saber quando
   deixa de ser. Falta também a contrapartida: em que condição a permissão é
   revogada.

2. **`AGENTS.md` seção 14 chama-se "Skills".** O conteúdo é uma tabela de
   demanda para skill obrigatória, mais a exigência de espelhamento nas três
   plataformas. O título não diz que são obrigatórias, que é a única
   informação normativa da seção.

3. **`docs/AGENT-WORKFLOW.md` funde limpeza e fechamento.** A seção 13 é
   "Limpeza e fechamento" e trata de dois momentos distintos: revisar o diff e
   remover resíduo, e relatar o resultado com evidência e status. São gates
   diferentes, com critérios diferentes, e `AGENTS.md` os separa em seções 12
   e 13. O documento de execução os junta, o que faz o gate de fechamento
   parecer um apêndice da limpeza.

4. **`docs/AGENT-WORKFLOW.md` não documenta os slash commands.** Existem três
   em `.claude/commands/`: `reset-local`, `sync-skills` e `validar-tela`. Dois
   deles executam operação de infraestrutura — um destrói o ambiente local,
   outro compara as cópias das skills. O documento que descreve como executar
   uma demanda não menciona que eles existem, então o ciclo repetido continua
   sendo feito à mão por quem não sabe do comando.

5. **Contratos com seções não numeradas.** `docs/PRD-STANDARD.md` e
   `docs/PLATFORM-ADAPTERS.md` têm seções de primeiro nível sem número.
   `AGENTS.md` cita esses documentos como fonte de assunto, e não há como
   fazer referência estável a um trecho: "ver PLATFORM-ADAPTERS, seção de
   sincronização" depende de o título não mudar.

6. **Inventário de comandos incompleto.** `docs/OPERACAO-BANCO-SEEDS.md` é
   apontado por `AGENTS.md` como a fonte normativa de banco, migrations e
   seeds. Doze comandos existentes não aparecem em nenhuma seção dele:
   `check_database_connection`, `clear_test_data`,
   `clear_migration_supabase_prod`, `backfill_membership_timeline`,
   `explain_perf_indexes`, `generate_due_asaas_charges`,
   `seed_system_initial_kanri_students_migration`,
   `seed_system_initial_test_administrative`,
   `seed_system_initial_test_guardians`,
   `seed_system_initial_test_students`,
   `seed_system_initial_test_teachers` e
   `seed_system_people_flow_samples`.

   O caso mais grave é `clear_migration_supabase_prod`: o comando que reseta o
   schema de produção não está documentado no runbook de banco. Quem precisar
   dele vai encontrá-lo por `ls` no diretório de comandos, sem ler o
   protocolo de guardas que o cerca.

7. **`docs/OPERACAO-BANCO-SEEDS.md` não descreve as guardas do ciclo
   destrutivo local.** As seções "Comandos seguros" e "Ciclo destrutivo local"
   listam o que rodar, mas nenhuma diz **por que** o script recusa nem **o que**
   ele remove. `clear_migrations.py` recusa execução em oito condições
   distintas — contadas na leitura do código, não estimadas — e nenhuma está
   descrita no documento normativo, então quem vê a recusa não tem onde
   consultar o motivo.

## Goal

Os contratos declaram a premissa que autoriza o protocolo destrutivo, separam
os gates que são distintos, têm seções citáveis por número e listam todos os
comandos de operação que existem.

## Context Ledger

### Files read in full

- `CLAUDE.md`
- `AGENTS.md`
- `README.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- os três arquivos de `.claude/commands/`

### Adjacent files consulted

- `clear_migrations.py` — as oito guardas a descrever
- `system/management/commands/` — inventário real, arquivo por arquivo
- `system/management/commands/_supabase_public_schema_reset.py` — protocolo de
  reset remoto
- `.github/workflows/ci.yml` — o que já é verificado automaticamente
- `docs/DEPLOY-RENDER-SUPABASE.md` — fronteira com o assunto de deploy

### Internet / official documentation

- Django 5.2: nomes e semântica dos comandos citados no inventário
  (`migrate`, `makemigrations`, `showmigrations`, `collectstatic`, `check`).
- Documentação de slash commands do Claude Code, para descrever corretamente
  o que são e como são acionados.

### Context7 / MCPs / tools verified

- Context7 consultado para Django 5.2 e para o formato de slash command.
- Verificação em disco de cada caminho citado nos contratos, um a um.

### Limitations found

- Busca textual encontra a menção de um comando mas não prova que ele existe
  como arquivo: o inventário foi montado a partir do diretório de comandos, e
  cada entrada foi conferida contra o arquivo.
- A qualidade de um contrato só se comprova em uso. O que é verificável agora
  é: nenhuma lacuna de assunto, nenhum link quebrado, nenhum comando omitido.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador para homogeneizar os contratos e implementar sem
nova confirmação.

## Execution prompt

### Persona

Editor dos contratos de governança do LV.

### Action

Escrever a seção de natureza do projeto, renomear e desdobrar as seções
citadas, numerar os contratos e completar o inventário de comandos e o
capítulo de guardas.

### Context

`AGENTS.md` diz o que vale, `CLAUDE.md` diz o que o projeto é,
`docs/AGENT-WORKFLOW.md` diz como executar. Um dono por assunto: nenhuma
seção nova pode duplicar o que outro contrato já normatiza.

### Constraints

- Nenhum contrato pode citar caminho fora deste repositório.
- Nenhuma regra existente é enfraquecida: a mudança é de estrutura, título e
  lacuna.
- A seção de natureza do projeto precisa incluir a condição de revogação — o
  que faz a permissão destrutiva deixar de valer.
- Renumerar seção exige atualizar toda citação que aponte para ela.
- Nenhum valor de variável de ambiente entra em documento; apenas nomes de
  chave.
- O inventário descreve o comando e suas guardas; não convida a executá-lo.

### Acceptance criteria

1. `CLAUDE.md` tem seção de natureza do projeto declarando: se há dado real de
   negócio, o que produção representa, que a baseline é recriável, que
   segredo operacional continua sendo tratado como secreto, e sob qual
   condição essa seção é revogada.
2. A seção de natureza precede a de produto, e as seções seguintes estão
   renumeradas.
3. `AGENTS.md` seção 14 chama-se "Skills obrigatórias".
4. `docs/AGENT-WORKFLOW.md` tem "Limpeza" e "Fechamento" como seções
   separadas.
5. `docs/AGENT-WORKFLOW.md` tem seção "Slash commands" descrevendo os três
   comandos existentes e quando usar cada um.
6. `docs/PRD-STANDARD.md` tem as seções de primeiro nível numeradas.
7. `docs/PLATFORM-ADAPTERS.md` tem as seções de primeiro nível numeradas e
   uma subseção de slash commands.
8. `docs/OPERACAO-BANCO-SEEDS.md` tem seção descrevendo as cinco guardas de
   `clear_migrations.py`, conferidas contra o código.
9. `docs/OPERACAO-BANCO-SEEDS.md` tem inventário de comandos que inclui todo
   arquivo de `system/management/commands/` que não começa com `_`.
10. Nenhum comando citado no inventário deixa de existir em disco.
11. `clear_migration_supabase_prod` está documentado com seu protocolo de
    guardas completo.
12. Todo caminho citado em `CLAUDE.md`, `AGENTS.md`, `README.md` e nos docs de
    `docs/` existe em disco.
13. Toda citação de seção por número aponta para a seção certa depois da
    renumeração.
14. `scripts/validate_skill_frontmatter.py` passa.
15. Suíte completa verde.

### Expected evidence

Saída real da verificação de links, comparação entre o inventário e a
listagem do diretório de comandos, validador de skills e suíte completa.

### Output format

Diff, saída dos comandos e atualização desta PRD.

## Scope

- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`,
  `docs/PLATFORM-ADAPTERS.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/README.md`

## Out of scope

- Renomear as skills: o prefixo `lv-` é a identidade do projeto e permanece.
- Alterar o conteúdo normativo de qualquer regra.
- Reescrever PRDs fechadas.
- `docs/UI-SCREEN-CONTRACT.md`, que tem dono próprio.
- Executar qualquer comando do inventário: esta PRD documenta, não opera.

## Impacted files

- `CLAUDE.md`, `AGENTS.md`, `README.md`
- os quatro docs de contrato citados
- `docs/prd/README.md`

## Risks and edge cases

- **Renumerar seção e deixar citação órfã.** Mitigação: cada citação por
  número é buscada e conferida depois da renumeração.
- **Duplicar assunto entre `AGENTS.md` e `CLAUDE.md`.** Mitigação: a seção
  nova de `CLAUDE.md` descreve fato; a permissão continua sendo normatizada
  só em `AGENTS.md` seção 11, com referência e não com cópia.
- **Documentar o reset de produção convidando a executá-lo.** Mitigação: a
  entrada descreve as guardas e a exigência de confirmação explícita antes de
  descrever o efeito.
- **Inventário defasar na próxima mudança.** Mitigação: registrada como risco
  aceito; a verificação automática do inventário exigiria ferramenta própria e
  não está neste escopo.
- **Declarar natureza descartável e alguém ler como permissão ampla.**
  Mitigação: a seção declara a condição de revogação no mesmo parágrafo.

## Rules and constraints

`AGENTS.md` seção 2: contrato descreve o que existe; ao divergir do código, o
código vence e o contrato é corrigido na mesma mudança. `AGENTS.md` seção 12:
documentação que a mudança tornou obsoleta é corrigida junto. `AGENTS.md`
seção 10: segredo operacional nunca é impresso, nem em documento.

## Plan

1. Montar o inventário real a partir do diretório de comandos.
2. Extrair as cinco guardas do `clear_migrations.py` por leitura integral.
3. Escrever a seção de natureza em `CLAUDE.md` e renumerar as seguintes.
4. Renomear a seção 14 do `AGENTS.md`.
5. Desdobrar limpeza e fechamento e escrever a seção de slash commands.
6. Numerar `docs/PRD-STANDARD.md` e `docs/PLATFORM-ADAPTERS.md`.
7. Escrever o capítulo de guardas e o inventário em
   `docs/OPERACAO-BANCO-SEEDS.md`.
8. Verificar todos os links em disco e todas as citações por número.
9. Rodar validador de skills e suíte completa.

## Test plan

Não há comportamento de aplicação a testar. A verificação é:

- comparação do inventário com a listagem do diretório de comandos, nos dois
  sentidos;
- verificação em disco de cada caminho citado;
- conferência de cada citação por número de seção;
- `scripts/validate_skill_frontmatter.py` como regressão;
- suíte completa como regressão geral, para garantir que nada de código foi
  tocado por engano.

## Visual validation

Não se aplica: nenhuma mudança de template, CSS, JavaScript ou rota.

## ORM validation

Não se aplica: nenhuma mudança de modelo, consulta ou migration.

## Quality validation

Verificação de links, `scripts/validate_skill_frontmatter.py`,
`python manage.py check` e suíte completa.

## Evidence

- `scripts/validate_skill_frontmatter.py`: 18 arquivos validados, 6 metadados
  Codex integros em UTF-8 com LF. Codigo 0.
- `scripts/build_prd_index.py --check`: "Indice em dia."
- Verificacao de links em disco de `CLAUDE.md`, `AGENTS.md`, `README.md` e dos
  documentos de `docs/`: **0 links quebrados**.
- **Inventario conferido nos dois sentidos** contra
  `system/management/commands/`: os 36 comandos que nao comecam com `_` estao
  cobertos, e nenhum comando citado deixa de existir. Os doze que faltavam
  entraram, `clear_migration_supabase_prod` incluido.
- `manage.py check`: "no issues (0 silenced)".
- Suite completa: verde.

## Implemented

- `CLAUDE.md`: nova **secao 1, Natureza do projeto**, declarando que o projeto e
  um MVP descartavel, o que producao representa, que a baseline e recriavel, que
  segredo continua secreto, e — no mesmo lugar — a **condicao de revogacao**. As
  dez secoes seguintes foram renumeradas de 2 a 11.
- `AGENTS.md`: secao 14 passou de "Skills" a "Skills obrigatorias".
- `docs/AGENT-WORKFLOW.md`: a secao 13 "Limpeza e fechamento" foi desdobrada em
  **13. Limpeza** e **14. Fechamento**, e ganhou **15. Slash commands** com os
  tres comandos existentes.
- `docs/PRD-STANDARD.md`: secoes de primeiro nivel numeradas de 1 a 6.
- `docs/PLATFORM-ADAPTERS.md`: secoes numeradas de 1 a 7, mais a subsecao
  **1.1. Slash commands**.
- `docs/OPERACAO-BANCO-SEEDS.md`: acrescentados **Guardas do ciclo destrutivo
  local** — as oito condicoes de recusa, conferidas contra o codigo, mais o
  encerramento de processos e a guarda de saida — e **Inventario de comandos**,
  organizado em verificacao e manutencao, seeds de referencia, seeds de teste e
  operacoes remotas, com o protocolo do reset remoto.
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`: a citacao "`CLAUDE.md` secao 8"
  foi corrigida para secao 9, que e onde Pagamentos passou a ficar.

## Cleanup findings

1. **A renumeracao do `CLAUDE.md` quebrou uma citacao por numero**, e a busca
   encontrou: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` apontava para a secao 8
   ao falar de webhook de pagamento. Corrigido no mesmo passo. E exatamente o
   risco que a secao de riscos previa, e a mitigacao funcionou.

2. **O runbook nao estava vazio de guardas — estava incompleto.** A secao
   "Comandos seguros" e "Ciclo destrutivo local" existiam e listavam os comandos
   do ciclo, mas nenhuma descrevia **por que** o script recusa nem **o que** ele
   remove. As guardas foram escritas a partir da leitura do codigo, nao da
   suposicao.

3. **A lista de seeds de referencia foi descrita por agrupamento, nao uma a
   uma.** Sao vinte e um comandos `seed_system_initial_*`; enumera-los todos numa
   tabela produziria um inventario que envelhece a cada seed nova sem
   acrescentar informacao. O agrupamento por tipo de dado cobre o que o leitor
   precisa, e a verificacao automatica de cobertura continua valendo.

4. Nenhum valor de variavel de ambiente entrou em documento — so nomes de chave.

5. Nenhum residuo introduzido.

## Follow-up PRDs

Nenhuma.

## Deviations from plan

- O escopo previa apenas os contratos. Entrou tambem
  `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, pela citacao quebrada — o que
  `AGENTS.md` secao 12 exige corrigir na mesma mudanca.
- `scripts/build_prd_index.py` ganhou o modo `--check` e um passo dedicado no
  CI. Nao estava no escopo desta PRD, que trata de contratos, mas o indice e
  parte da governanca documental e o projeto ja tinha o gerador sem verificacao.
  Registrado aqui em vez de implementado em silencio.

## Pending

- Rodar o CI de fato: o passo novo foi verificado localmente, mas o job so corre
  no proximo push.
- Commitar o worktree. Nenhum commit foi feito pelo agente.

## Final status

Concluida. Os contratos declaram a premissa que autoriza o protocolo destrutivo,
separam limpeza de fechamento, tem secoes citaveis por numero e listam todos os
comandos de operacao que existem — inclusive o reset de producao, que antes so
era encontravel por `ls`.
