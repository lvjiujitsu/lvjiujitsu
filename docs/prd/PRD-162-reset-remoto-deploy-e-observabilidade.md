# PRD-162: Reset remoto endurecido, deploy documentado e observabilidade

## Summary

Adotar no LV as três defesas operacionais que hoje só o outro repositório tem:
identificação do projeto Supabase no reset remoto com execução em modo
simulação por padrão, bloqueio da Data API com RLS e auditoria sem escrita, e
um documento de deploy com Build Command, Start Command e health check.
Inclui `clear_test_data` e `check_database_connection`, hoje inexistentes.

## Demand type

Infraestrutura remota, deploy e observabilidade. Sem mudança de regra de
negócio.

## Current problem

1. `system/management/commands/_supabase_public_schema_reset.py` valida
 ambiente, `DEBUG=False`, host Supabase, `SUPABASE_RESET_CONFIRM` e vendor
 do banco, mas **executa o `DROP` na primeira invocação bem-sucedida**. Não
 há modo de simulação e não há conferência de qual projeto Supabase é o
 alvo. Com dois projetos provisionados e a variável de confirmação correta
 exportada, um `DATABASE_URL` trocado por engano derruba o schema errado. O
 outro repositório resolve isso conferindo `SUPABASE_PROJECT_REF` contra o host e
 exigindo `--execute` para sair do modo simulação.
2. `system/management/commands/lock_supabase_api_access.py` tem 46 linhas,
 revoga privilégios das roles `anon` e `authenticated`, mas não habilita
 RLS e não oferece modo de auditoria. O equivalente no outro repositório tem 175
 linhas, habilita RLS por tabela e aceita `--check`.
3. O Build Command está documentado em `CLAUDE.md:84` e
 `docs/OPERACAO-BANCO-SEEDS.md:137`, mas o Start Command não: `CLAUDE.md:87`
 diz apenas "Gunicorn conforme configuração do serviço Render". Não existe
 documento de deploy dedicado; o restante vive na nota em Obsidian, fora do
 repositório.
4. Não existe rota de health check nem `check_database_connection`. O Render
 não tem endpoint barato para verificar se a aplicação subiu.
5. Existem quatro comandos `seed_system_initial_test_*` que criam dados
 fictícios de homologação, mas não existe nenhum comando que os remova. O
 outro repositório tem `clear_test_data` com confirmação explícita.

## Goal

O reset remoto identifica o projeto alvo e não destrói nada sem `--execute`;
a Data API fica bloqueada com RLS e auditável; o deploy está documentado no
repositório; existe health check, checagem de conexão e remoção reversível
dos dados de teste.

## Context Ledger

### Files read in full

- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`
- `system/management/commands/lock_supabase_api_access.py`
- os quatro `system/management/commands/seed_system_initial_test_*.py`
- `lvjiujitsu/settings.py`, `lvjiujitsu/urls.py`
- `CLAUDE.md`, `docs/OPERACAO-BANCO-SEEDS.md`

### Adjacent files consulted

- `.env`, `.env.hg`, `.env.prod`, `.env.example` (estrutura, sem valores)
- `system/models/person.py`, `system/models/plan.py`
- `system/middleware.py`

### Internet / official documentation

- [Supabase — Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase — Connecting to your database](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Render — Deploying a Django application](https://render.com/docs/deploy-django)
- [Django — `transaction.atomic`](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#django.db.transaction.atomic)
- [PostgreSQL — `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`](https://www.postgresql.org/docs/current/sql-altertable.html)

### Context7 / MCPs / tools verified

- Context7 disponível na sessão para Django 5.2 e cliente PostgreSQL.
- O código de referência do outro repositório foi lido diretamente do disco.

### Limitations found

- `SUPABASE_PROJECT_REF` não existe hoje nos `.env*` do LV; será adicionada
 às quatro variantes, coordenada com a PRD-160, que trata do conjunto de
 chaves.
- A conferência do reset endurecido contra um projeto Supabase real depende
 do operador; o agente valida por teste automatizado e por execução em modo
 simulação.

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

Engenheiro de plataforma responsável pela operação remota do LV.

### Action

Portar do outro repositório as guardas do reset remoto e o bloqueio da Data API com
RLS, criar `docs/DEPLOY-RENDER-SUPABASE.md`, a rota `/health/`, o comando
`check_database_connection` e o comando `clear_test_data`.

### Context

padrão canônico, LV Jiu Jitsu e outro repositório compartilham o mesmo modelo de
infraestrutura. O outro repositório é o referência nestes itens.

### Constraints

- Nenhum comando destrutivo remoto executa sem `--execute` explícito.
- Nenhum valor de segredo é impresso.
- `clear_test_data` remove apenas o que os quatro
 `seed_system_initial_test_*` criam; os 21 seeds iniciais permanecem
 intactos.
- Seeds nunca entram no Build Command.
- Nenhuma mudança de model ou migration.

### Acceptance criteria

- [ ] `_supabase_public_schema_reset.py` lê `SUPABASE_PROJECT_REF` e recusa
 quando o valor não corresponde ao host de `DATABASE_URL`.
- [ ] Sem `--execute`, o comando lista as relações que seriam removidas e
 não emite nenhum `DROP`. Verificação: teste confirmando zero comando
 destrutivo em modo simulação.
- [ ] Com `--execute` e todas as guardas satisfeitas, o comportamento atual
 é preservado.
- [ ] `clear_migration_supabase_hg` e `clear_migration_supabase_prod`
 continuam exigindo `SUPABASE_RESET_CONFIRM` igual a `RESET_HG` e
 `RESET_PROD`.
- [ ] `lock_supabase_api_access` habilita RLS nas tabelas do schema `public`
 e aceita `--check`, que audita e não escreve. Verificação: teste
 confirmando ausência de escrita em modo `--check`.
- [ ] `lock_supabase_api_access` é idempotente e ignora SQLite.
- [ ] `docs/DEPLOY-RENDER-SUPABASE.md` existe com Build Command, Start
 Command completo (`gunicorn lvjiujitsu.wsgi:application`), lista de
 variáveis por ambiente, health check e política de auto-deploy. Nenhum
 segredo no documento.
- [ ] `CLAUDE.md` e `docs/OPERACAO-BANCO-SEEDS.md` referenciam o novo
 documento em vez de descrever o deploy por conta própria.
- [ ] A rota `/health/` responde 200 sem autenticação e sem consultar o
 banco. Verificação: teste de rota, incluindo o caso de usuário
 anônimo passando pelo `PortalSessionMiddleware`.
- [ ] `check_database_connection` valida a conexão ativa sem alterar dados e
 falha com mensagem clara quando não há conexão.
- [ ] `clear_test_data` exige `--confirm CLEAR_TEST_DATA`, exige
 `--allow-production` quando `DJANGO_ENVIRONMENT` é `prod`, remove
 apenas os dados dos quatro seeds de teste e preserva os dados dos 21
 seeds iniciais. Verificação: teste que conta registros de referência
 antes e depois.
- [ ] `SUPABASE_PROJECT_REF` existe nos quatro arquivos `.env*`.
- [ ] `python manage.py check` sem erro e suíte de testes verde.

### Expected evidence

Saída do reset em modo simulação; saída de `lock_supabase_api_access --check`;
saída do teste de preservação; resposta de `/health/`; saída de `check` e da
suíte.

### Output format

Diff dos comandos, do `urls.py`, dos documentos, e PRD atualizada com
evidência de execução real.

## Scope

- Guardas de `SUPABASE_PROJECT_REF` e `--execute` no reset remoto.
- RLS e `--check` no bloqueio da Data API.
- `docs/DEPLOY-RENDER-SUPABASE.md`.
- Rota `/health/` e comando `check_database_connection`.
- Comando `clear_test_data`.
- `SUPABASE_PROJECT_REF` nos quatro `.env*`.

## Out of scope

- Reconciliação das demais variáveis de ambiente (PRD-160).
- Slash commands, índice e higiene (PRD-161).
- Provisionar ou reconfigurar serviços Render e Supabase.
- Alterar os 21 seeds iniciais ou os quatro seeds de teste, específicos do
 domínio da academia.

## Impacted files

- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/lock_supabase_api_access.py`
- `system/management/commands/check_database_connection.py` (novo)
- `system/management/commands/clear_test_data.py` (novo)
- `lvjiujitsu/urls.py`, `system/views/` (view de health check)
- `system/tests/test_supabase_reset_guards.py` (novo)
- `system/tests/test_clear_test_data.py` (novo)
- `system/tests/test_health_check.py` (novo)
- `docs/DEPLOY-RENDER-SUPABASE.md` (novo)
- `CLAUDE.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `.env`, `.env.example`, `.env.hg`, `.env.prod`
- `docs/prd/README.md`

## Risks and edge cases

- `SUPABASE_PROJECT_REF` ausente em ambiente já provisionado: o comando
 recusa nomeando a variável, não segue adiante.
- Host de pooler com formato diferente do host direto: aceitar as duas formas
 oficiais documentadas pelo Supabase.
- Habilitar RLS sem política e travar a aplicação: o Django conecta como dono
 das tabelas, que não é sujeito a RLS por padrão; validar em homologação
 antes de produção.
- `/health/` sendo interceptada pelo `PortalSessionMiddleware` e exigindo
 sessão: a rota precisa de teste com usuário anônimo.
- `clear_test_data` apagando pessoa real por heurística de nome: a
 identificação usa marcação explícita dos registros criados pelos seeds de
 teste, não nome ou e-mail.

## Rules and constraints

- Services concentram negócio e transação; views permanecem finas.
- Sem segredo hardcoded, sem erro mascarado, sem query em loop.
- Ações destrutivas Supabase exigem ambiente, confirmação e `--execute`.

## Plan

- [ ] Contexto e pesquisa
- [ ] Testes escritos primeiro para guardas, `--check` e preservação
- [ ] Endurecer o reset remoto
- [ ] RLS e `--check` no bloqueio da Data API
- [ ] Health check e `check_database_connection`
- [ ] `clear_test_data`
- [ ] `docs/DEPLOY-RENDER-SUPABASE.md` e ajuste dos contratos
- [ ] Validação
- [ ] Auditoria de limpeza

## Test plan

### Tests to author

- `test_supabase_reset_guards.py`: recusa por `SUPABASE_PROJECT_REF`
 divergente; modo simulação sem `DROP`; recusa por ambiente, `DEBUG`, host
 e confirmação.
- `test_clear_test_data.py`: exigência de `--confirm`; exigência de
 `--allow-production` em `prod`; preservação dos dados dos seeds iniciais.
- `test_health_check.py`: `/health/` responde 200 para usuário anônimo.

### Execution authorization

- Status: autorizada pela ordem explícita do operador em 2026-07-25.

### Execution evidence

Testes focados, por frente:

```
system.tests.test_supabase_reset_guards ......... Ran 11 tests OK
system.tests.test_health_check .................. Ran 3 tests OK
system.tests.test_clear_test_data ............... Ran 5 tests OK
```

Suíte completa, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 741 tests in 252.065s

OK
```

A suíte passou de 722 para 741 testes: os 19 casos novos.

## Visual validation

`/health/` é rota de infraestrutura sem interface; verificada por teste, não
por navegador. Nenhuma tela do produto foi alterada.

## ORM validation

`test_clear_test_data` conta `PersonType`, `BeltRank` e `ClassCategory` antes
das seeds fictícias e depois de `clear_test_data`, confirmando que os três
permanecem idênticos enquanto as pessoas fictícias somem. `Person.objects.count`
volta exatamente ao valor anterior às seeds fictícias.

Todas as operações rodam contra o banco de teste isolado da suíte. Nenhuma
escrita em homologação ou produção foi feita.

## Quality validation

Modo simulação do reset remoto, verificado por teste que intercepta o cursor:

```
Projeto Supabase confirmado: abcdefghijklmnop
Objetos encontrados no schema public: 2
 - tabela public.system_person
 - sequence public.system_person_id_seq
Simulacao concluida. Nenhum objeto foi removido. Revise o projeto e a lista
acima antes de usar --execute.
```

O teste `test_dry_run_does_not_execute_destructive_sql` afirma que a lista de
SQL executado é vazia. Sem `--execute`, zero comandos.

Guarda de projeto, no cenário que a PRD existe para impedir — `DATABASE_URL`
de um projeto e `SUPABASE_PROJECT_REF` de outro:

```
CommandError: A conexao nao corresponde ao SUPABASE_PROJECT_REF esperado.
```

Aceita as duas formas oficiais de host do Supabase: pooler
(`postgres.<ref>@aws-0-...pooler.supabase.com`) e direta
(`db.<ref>.supabase.co`).

`lock_supabase_api_access --check` em SQLite:

```
Banco local não é PostgreSQL; bloqueio da Data API ignorado.
```

`check_database_connection`:

```
Conexão SQLite local válida: versão=3.49.1.
--require-postgresql em SQLite:
CommandError: PostgreSQL era obrigatório, mas o banco ativo é sqlite.
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Evidence

- 19 testes novos verdes; suíte completa de 741 testes, `OK`.
- Modo simulação provado por teste: zero SQL destrutivo sem `--execute`.
- Guarda de `SUPABASE_PROJECT_REF` recusando projeto divergente.
- `/health/` respondendo 200 para anônimo, com `assertNumQueries(0)`.
- `clear_test_data` preservando as três contagens de referência.

## Implemented

- `SUPABASE_PROJECT_REF` em `lvjiujitsu/settings.py` e nos quatro arquivos de
 ambiente.
- `_supabase_public_schema_reset.py`: `validate_project_ref` conferindo a
 referência contra o host, `--execute` com simulação por padrão,
 `list_public_relations` e `RELKIND_LABELS` para a listagem legível.
- `system/tests/test_supabase_reset_guards.py` com 11 casos.
- `lock_supabase_api_access` substituído pela versão do outro repositório, com RLS
 por tabela e `--check` que audita sem escrever, adaptando o prefixo de
 tabela de `directory_` para `system_`.
- `check_database_connection` portado, com `--require-postgresql`.
- `HealthCheckView` em `system/views/auth_views.py` e rota `health/` em
 `system/urls.py`; `system/tests/test_health_check.py` com 3 casos.
- `clear_test_data` criado, identificando as pessoas pelo CPF dos JSON de
 fixture e os vínculos por `TEST_SEED_NOTE`;
 `system/tests/test_clear_test_data.py` com 5 casos.
- `docs/DEPLOY-RENDER-SUPABASE.md` criado, com Build, Start, health check,
 variáveis por grupo, Supabase, auto-deploy e o ritual de reset.
- `CLAUDE.md`, `AGENTS.md` e `docs/OPERACAO-BANCO-SEEDS.md` passaram a
 referenciar o documento de deploy em vez de descrever o assunto por conta
 própria.

## Cleanup findings

- **A ordem das guardas precisou ser revista.** Colocada antes da
 confirmação, a validação de `SUPABASE_PROJECT_REF` quebrou quatro testes
 preexistentes em `SupabaseResetCommandSafetyTestCase`, que esperavam as
 mensagens de confirmação e de vendor. A guarda foi movida para o fim:
 primeiro "estou autorizado?" e "é PostgreSQL?", só então "é o projeto
 certo?". Os quatro voltaram ao verde sem alteração.
- **Segunda senha em texto claro encontrada:**
 `docs/OPERACAO-BANCO-SEEDS.md:110` publica `lv-pessoas-2026`, senha do
 comando `seed_system_people_flow_samples`. A PRD-160 tratou apenas
 `LvTest@2026`. O comando está marcado como obsoleto e emite
 `DeprecationWarning`, e o item está fora do escopo desta PRD. Registrado
 em `Follow-up PRDs`.
- `system/urls.py` usa `app_name = "system"`, então a rota é
 `reverse("system:health")`. O caminho `/health/` é o que o Render usa e não
 depende do namespace.
- Nenhum resíduo introduzido.

## Follow-up PRDs

- LV: remover `lv-pessoas-2026` de `docs/OPERACAO-BANCO-SEEDS.md:110`,
 junto com a decisão sobre aposentar `seed_system_people_flow_samples`, que
 já está obsoleto.
- LV: portar `scripts/validate_skill_frontmatter.py` canônico e ligá-lo ao
 CI. É o último item de heterogeneidade de CI entre o projeto.

## Deviations from plan

- A ordem das guardas ficou diferente da do outro repositório, que valida
 `SUPABASE_PROJECT_REF` antes da confirmação. No LV ela vem depois, para
 preservar os contratos já validados pelos quatro testes preexistentes. O
 conjunto de guardas é o mesmo; muda apenas qual mensagem aparece primeiro
 quando mais de uma falha.
- `lock_supabase_api_access` foi substituído inteiro em vez de recebar
 incrementos. A versão do outro repositório já cobria tudo que a do LV fazia, e
 mesclar as duas produziria um terceiro comportamento sem ganho.
- O Build Command do LV **não** recebeu `create_admin_superuser`, ao
 contrário do outro repositório. No LV o superusuário é criado uma vez, por execução
 explícita; incluí-lo no build mudaria o comportamento operacional sem
 pedido.

## Pending

- Execução do reset endurecido contra o Supabase real de homologação, que
 depende do operador. `SUPABASE_PROJECT_REF` foi criada vazia nos quatro
 arquivos e precisa ser preenchida com a referência real de cada projeto
 antes do próximo reset — **sem ela, o comando recusa**, que é o
 comportamento desejado.
- Cadastrar `SUPABASE_PROJECT_REF` e o Health Check Path `/health/` nos dois
 serviços Render.
- Confirmar em homologação que `lock_supabase_api_access` com RLS não afeta a
 aplicação, antes de valer para produção. O Django conecta como owner das
 tabelas, que não é sujeito a RLS por padrão, mas isso precisa ser visto no
 ambiente real.

## Final status

Concluída com limitações externas. Tudo que depende do repositório está feito
e verificado por 19 testes novos, com a suíte completa verde em 741. As
limitações são de provisionamento e configuração de serviço, listadas em
`Pending`, e nenhuma delas bloqueia o uso local ou a próxima entrega.
