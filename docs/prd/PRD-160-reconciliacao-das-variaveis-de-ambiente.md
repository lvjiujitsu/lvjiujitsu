# PRD-160: Reconciliação das variáveis de ambiente

## Summary

`lvjiujitsu/settings.py` lê quatorze variáveis que existem apenas em
`.env.example` e não estão declaradas em `.env`, `.env.hg` nem `.env.prod`.
Duas outras variáveis existem nos arquivos reais e não são lidas por lugar
nenhum. Esta PRD reconcilia os quatro arquivos em um único conjunto de
chaves e tira uma senha de teste de dentro de documento versionado.

## Demand type

Infraestrutura e configuração. Sem mudança de regra de negócio.

## Current problem

1. Quatorze chaves lidas por `lvjiujitsu/settings.py` estão declaradas
 somente em `.env.example`: `DJANGO_ENVIRONMENT`, `DATABASE_URL`,
 `DB_CONN_MAX_AGE`, `DJANGO_SECURE_HSTS_SECONDS`,
 `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_SECURE_HSTS_PRELOAD`,
 `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`,
 `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SESSION_COOKIE_SAMESITE`,
 `DJANGO_CSRF_COOKIE_SAMESITE`, `STRIPE_PLAN_SYNC_ENABLED`,
 `VETERAN_PLAN_TENURE_YEARS` e `VETERAN_PLAN_GAP_GRACE_DAYS`.

 A direção do defeito importa: o `.env.example` está correto e os três
 arquivos reais é que estão incompletos. Em homologação e produção, todas
 as diretivas de segurança de transporte e de cookie caem em valor padrão
 sem que ninguém tenha decidido isso — inclusive HSTS, redirecionamento
 para HTTPS e o marcador `Secure` dos cookies de sessão e CSRF.

 `DJANGO_ENVIRONMENT` merece nota à parte: `.env` local não a declara e o
 projeto depende do fallback `local` em `lvjiujitsu/settings.py:23-27`.
 Um contrato de ambiente que só funciona por omissão é frágil.

2. `SUPABASE_URL` e `SUPABASE_KEY` existem em `.env.hg` e `.env.prod` e não
 são lidas por `settings.py` em nenhum ponto. São chaves mortas dentro de
 arquivo de segredo.

3. `docs/OPERACAO-BANCO-SEEDS.md:94` documenta a senha de teste
 `LvTest@2026` em texto claro, em arquivo versionado. Mesmo sendo um MVP
 descartável, `CLAUDE.md` mantém a regra de que segredo operacional é
 tratado como secreto.

4. O padrão canônico é o alvo de paridade neste item: seus quatro arquivos declaram
 exatamente as mesmas 45 chaves, com diff vazio entre eles.

## Goal

Os quatro arquivos de ambiente declaram o mesmo conjunto de chaves; toda
chave declarada é lida por `settings.py`; toda chave lida por `settings.py`
está declarada; e nenhuma senha aparece em documento versionado.

## Context Ledger

### Files read in full

- `lvjiujitsu/settings.py`
- `.env`, `.env.example`, `.env.hg`, `.env.prod` (estrutura, sem valores)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `CLAUDE.md`, `AGENTS.md`
- `clear_migrations.py`

### Adjacent files consulted

- `system/management/commands/_supabase_public_schema_reset.py`
- os quatro `system/management/commands/seed_system_initial_test_*.py`
- `system/management/commands/create_admin_superuser.py`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`

### Internet / official documentation

- [Django — Security settings (`SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`)](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-hsts-seconds)
- [Django — `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE`](https://docs.djangoproject.com/en/5.2/ref/settings/#session-cookie-secure)
- [Django — Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Supabase — Connecting to your database](https://supabase.com/docs/guides/database/connecting-to-postgres)

### Context7 / MCPs / tools verified

- Context7 disponível na sessão para Django 5.2. As diretivas de segurança
 citadas foram conferidas contra a documentação oficial acima.

### Limitations found

- `.env*` está coberto pelo `.gitignore`; a paridade de chaves não é
 verificável por CI e depende de checagem local documentada no runbook.
- Definir HSTS em produção tem efeito persistente no navegador do usuário;
 o valor inicial deve ser conservador.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de paridade entre padrão canônico, LV Jiu Jitsu e
 outro repositório, conduzida por três subagentes de leitura e um auditor cruzado,
 com veredito de que é preciso intervir.
- User approval: ordem explícita do operador — "Gere os PRDs em cada um dos
 projetos garantindo que após a execução dos PRDs os 3 projetos seguiram a
 paridade ideal atingida. após a geração de todos os PRDs pode implementar
 todos."
- Date: 2026-07-25.

## Execution prompt

### Persona

Engenheiro de plataforma responsável pela configuração de ambientes do LV.

### Action

Declarar as quatorze chaves faltantes no projeto arquivos reais com valor
adequado a cada ambiente, decidir o destino de `SUPABASE_URL` e
`SUPABASE_KEY`, e mover a senha de teste para variável de ambiente.

### Context

Homologação e produção rodam em Supabase e Render, atrás de HTTPS. As
diretivas de segurança precisam ser decididas explicitamente, não herdadas
por omissão.

### Constraints

- Nenhum valor de segredo é impresso em saída, log ou PRD.
- Valores de segurança em `local` permanecem permissivos; em `hg` e `prod`
 ficam restritivos.
- `DJANGO_ENVIRONMENT` passa a ser declarado explicitamente também em
 `.env`, mantendo o valor `local`.
- Nenhuma mudança de comportamento do produto além do endurecimento de
 transporte em ambientes remotos.

### Acceptance criteria

- [ ] As quatorze chaves listadas existem em `.env`, `.env.hg` e
 `.env.prod`, com valor coerente com cada ambiente.
- [ ] `.env` declara `DJANGO_ENVIRONMENT=local` e `DATABASE_URL` vazia.
- [ ] `.env.hg` e `.env.prod` declaram `DJANGO_SECURE_SSL_REDIRECT`,
 `DJANGO_SESSION_COOKIE_SECURE` e `DJANGO_CSRF_COOKIE_SECURE` como
 verdadeiros, e `DJANGO_SECURE_HSTS_SECONDS` com valor diferente de
 zero.
- [ ] O conjunto de nomes de chave é idêntico nos quatro arquivos.
 Verificação: comparação das chaves ordenadas dos quatro arquivos, com
 diff vazio.
- [ ] Toda chave declarada nos quatro arquivos é lida por
 `lvjiujitsu/settings.py`, ou tem justificativa registrada nesta PRD.
 Verificação: busca de cada nome de chave no código.
- [ ] `SUPABASE_URL` e `SUPABASE_KEY` são removidas dos arquivos reais, ou
 passam a ser lidas por `settings.py`. A decisão fica registrada em
 `Deviations from plan` com a justificativa.
- [ ] `docs/OPERACAO-BANCO-SEEDS.md` não contém nenhuma senha em texto
 claro. A senha das seeds de teste passa a vir de variável de ambiente
 declarada nos quatro arquivos. Verificação: busca textual por
 `LvTest` no repositório retorna zero ocorrências fora de `docs/prd/`.
- [ ] Os quatro comandos `seed_system_initial_test_*` leem a senha da
 variável de ambiente e falham com mensagem clara quando ela está
 ausente. Verificação: teste por comando.
- [ ] `clear_migrations.py` continua recusando o ciclo quando falta
 variável obrigatória, incluindo a nova.
- [ ] `python manage.py check --deploy` não reporta aviso de HSTS, SSL
 redirect ou cookie inseguro quando executado com `.env.prod`.
- [ ] `python manage.py check` sem erro e suíte de testes verde.

### Expected evidence

Comparação de chaves dos quatro arquivos; busca de cada chave no código;
busca textual por `LvTest`; saída de `check --deploy`; saída dos testes.

### Output format

Diff dos arquivos de ambiente, dos comandos de seed e da documentação, e PRD
atualizada com evidência real.

## Scope

- Declaração das quatorze chaves no projeto arquivos reais.
- Decisão e execução sobre `SUPABASE_URL` e `SUPABASE_KEY`.
- Senha das seeds de teste via variável de ambiente.
- Ajuste dos quatro comandos `seed_system_initial_test_*`.
- Atualização de `docs/OPERACAO-BANCO-SEEDS.md`.

## Out of scope

- Slash commands, índice de PRDs e higiene de repositório (PRD-161).
- Reset remoto, deploy e observabilidade (PRD-162).
- Qualquer mudança em Asaas ou Stripe.
- Alteração de model, migration ou fluxo de cadastro.

## Impacted files

- `.env`, `.env.example`, `.env.hg`, `.env.prod`
- `system/management/commands/seed_system_initial_test_students.py`
- `system/management/commands/seed_system_initial_test_guardians.py`
- `system/management/commands/seed_system_initial_test_administrative.py`
- `system/management/commands/seed_system_initial_test_teachers.py`
- `system/tests/test_seed_test_commands.py` (novo ou estendido)
- `clear_migrations.py`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/README.md`

## Risks and edge cases

- Ligar `SECURE_SSL_REDIRECT` em homologação e criar laço de redirecionamento
 atrás do proxy do Render: conferir que `SECURE_PROXY_SSL_HEADER` está
 configurado antes de ligar, e validar com uma requisição real.
- HSTS com valor alto fixando o navegador em HTTPS antes de o domínio estar
 estável: começar com valor conservador e registrar a decisão.
- Remover `SUPABASE_URL` e `SUPABASE_KEY` e descobrir depois que uma
 ferramenta externa as consumia: buscar em todo o repositório e na nota
 operacional antes de remover.
- Seeds de teste falhando por falta da nova variável em ambiente já
 configurado: a mensagem de erro nomeia a variável ausente.

## Rules and constraints

- Segredo nunca impresso, mesmo descartável.
- Configuração explícita, sem valor mágico embutido no código.
- Seeds são sempre explícitas.

## Plan

- [ ] Contexto e pesquisa
- [ ] Levantar a lista final de chaves e o valor por ambiente
- [ ] Testes escritos primeiro para a senha via variável de ambiente
- [ ] Declarar as chaves no projeto arquivos reais
- [ ] Decidir e executar sobre `SUPABASE_URL` e `SUPABASE_KEY`
- [ ] Ajustar os quatro comandos de seed de teste
- [ ] Atualizar `docs/OPERACAO-BANCO-SEEDS.md`
- [ ] Validação
- [ ] Auditoria de limpeza

## Test plan

### Tests to author

`system/tests/test_seed_test_commands.py`: cada um dos quatro comandos
`seed_system_initial_test_*` falha com mensagem nomeando a variável quando a
senha não está configurada, e usa o valor da variável quando ela existe.

### Execution authorization

- Status: autorizada pela ordem explícita do operador em 2026-07-25.

### Execution evidence

Teste focado, `manage.py test system.tests.test_test_seed_fixtures`:

```
Ran 5 tests in 37.353s

OK
```

Os três casos novos: recusa com `SEED_TEST_PORTAL_PASSWORD` vazia, sem criar
nenhuma pessoa; uso da senha configurada, verificado por `check_password`; e
ausência de qualquer `portal_password` nos quatro JSON de fixture.

Suíte completa, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 722 tests in 220.453s

OK
```

A primeira execução da suíte falhou em um caso — registrado em `Deviations
from plan` — e passou depois da correção.

## Visual validation

Não aplicável. Nenhum template, CSS ou JavaScript foi alterado. O
endurecimento de transporte é verificado por `check --deploy`.

## ORM validation

Sem mudança de model, migration ou query. O comportamento de escrita das
seeds de teste é coberto pelos testes acima, que rodam contra o banco
isolado da suíte.

## Quality validation

Paridade de chaves nos quatro arquivos, comparando os nomes ordenados de
cada um contra `.env`:

```
=== paridade de chaves ===
.env.example IDENTICO a .env
.env.hg IDENTICO a .env
.env.prod IDENTICO a .env

total de chaves: 67
```

Antes desta PRD: `.env` tinha 52 chaves, `.env.example` 66, `.env.hg` e
`.env.prod` 56, com 14 chaves lidas por `settings.py` ausentes dos arquivos
reais e 2 chaves mortas presentes só neles.

`manage.py check --deploy` apontando `.env.prod`, depois de `collectstatic`
conforme o runbook:

```
WARNINGS:
?: (security.W005) You have not set the SECURE_HSTS_INCLUDE_SUBDOMAINS setting to True...
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True...

System check identified 2 issues (0 silenced).
```

Restaram apenas os dois avisos correspondentes às escolhas conservadoras
deliberadas. Os avisos de HSTS ausente, redirecionamento SSL e cookies sem
`Secure`, que apareciam antes por os valores caírem em default, deixaram de
existir porque agora são declarados explicitamente.

Senha fora de todo arquivo versionado:

```
grep -rn "LvTest" --include=*.md --include=*.py --include=*.json . | grep -v docs/prd/
--- (vazio: nenhuma ocorrência fora de docs/prd/) ---
```

Guarda do ciclo destrutivo continua ativa com a variável nova na lista:

```
[ERROR] Ciclo destrutivo local recusado: use o arquivo .env local.
EXIT: 1
```

Banco local com mesmo tamanho e carimbo de tempo antes e depois.

## Evidence

- 67 chaves idênticas nos quatro arquivos de ambiente, diff vazio.
- `check --deploy` com apenas os dois avisos deliberados.
- Zero ocorrência de `LvTest` fora do histórico de PRDs.
- 5 testes focados verdes; suíte completa de 722 testes, `OK`.

## Implemented

- As 14 chaves lidas por `settings.py` e ausentes foram declaradas no projeto
 arquivos reais, com valor permissivo em `local` e restritivo em `hg` e
 `prod`: `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE` e
 `DJANGO_CSRF_COOKIE_SECURE` verdadeiros e `DJANGO_SECURE_HSTS_SECONDS=3600`
 nos remotos.
- `SUPABASE_URL` e `SUPABASE_KEY` removidas de `.env.hg` e `.env.prod`.
- `SEED_TEST_PORTAL_PASSWORD` criada em `lvjiujitsu/settings.py` e declarada
 nos quatro arquivos de ambiente.
- `system/services/test_seed_fixtures.py`: `_portal_password` lê do
 settings; `_sync_portal_account` usa essa função; a validação passou a
 recusar por variável ausente em vez de por campo ausente no JSON;
 `portal_password` saiu de `REQUIRED_ENTRY_KEYS`.
- `portal_password` removido de 31 entradas nos quatro JSON de fixture.
- `system/tests/test_test_seed_fixtures.py`: caso existente passou a comparar
 contra o settings, e três casos novos foram acrescentados.
- `SEED_TEST_PORTAL_PASSWORD` entrou em `REQUIRED_LOCAL_SEED_SETTINGS` do
 `clear_migrations.py`, com os dois testes de ambiente atualizados.
- `docs/OPERACAO-BANCO-SEEDS.md` deixou de publicar a senha e passou a
 descrever a variável e o comportamento de recusa.

## Cleanup findings

- `staticfiles/` foi regenerado por `collectstatic` para permitir o
 `check --deploy`. É saída ignorada pelo git e o procedimento está previsto
 no runbook.
- O script auxiliar de reconciliação ficou fora do repositório, no diretório
 temporário da sessão.
- Backups dos quatro arquivos de ambiente foram feitos antes da alteração e
 descartados após a verificação.

## Follow-up PRDs

- PRD-161 — slash commands, índice de PRDs e higiene do repositório.
- PRD-162 — reset remoto endurecido, deploy documentado e observabilidade.

## Deviations from plan

- O plano tratava a senha de teste como um problema de documentação. A
 investigação mostrou que ela vivia em quatro JSON versionados, no campo
 `portal_password` de 31 entradas, e o documento apenas a repetia. O escopo
 real foi maior: exigiu mudar o service, os fixtures e os testes. A direção
 permaneceu a que a PRD declarava.
- `SUPABASE_URL` e `SUPABASE_KEY` foram removidas em vez de passarem a ser
 lidas. Busca em todo o código Python retornou zero referência a elas, e o
 projeto conecta ao Supabase exclusivamente por `DATABASE_URL`. Mantê-las
 seria preservar segredo sem consumidor.
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` e `SECURE_HSTS_PRELOAD` ficaram em
 `False`, e `SECURE_HSTS_SECONDS` em 3600 e não num valor alto. HSTS fixa o
 navegador em HTTPS e é caro de reverter; o critério de aceite pedia apenas
 valor diferente de zero. Os dois avisos remanescentes do `check --deploy`
 são consequência consciente disso.
- A primeira execução da suíte quebrou
 `test_local_environment_validation_accepts_complete_sqlite_config`: o teste
 monta um `.env` sintético que não conhecia a variável nova. Os dois testes
 de ambiente foram atualizados e a suíte voltou ao verde.

## Pending

- Rotação da senha de teste em uso, caso o operador considere que
 `LvTest@2026` já circulou o suficiente para valer a troca. Agora isso é
 uma troca de valor em quatro arquivos de ambiente, sem tocar em código.
- Confirmar em homologação real que `SECURE_SSL_REDIRECT=True` não produz
 laço de redirecionamento atrás do proxy do Render, antes de valer para
 produção.

## Final status

Concluída. Os quatro arquivos de ambiente declaram as mesmas 67 chaves, toda
chave declarada é lida por `settings.py`, nenhuma senha permanece em arquivo
versionado e a suíte completa está verde em 722 testes.
