# Operação de banco, migrations e seeds

## 1. Ambientes

| Arquivo/configuração | Ambiente | Banco |
|---|---|---|
| `.env` | local | SQLite `db.sqlite3` |
| `.env.hg` | homologação privada | PostgreSQL Supabase |
| variáveis do Render; `.env.prod` é referência privada | produção | PostgreSQL Supabase |

`.env.hg` e `.env.prod` são privados e ignorados pelo Git. O suporte de código a
HG não provisiona projeto Supabase nem serviço Render; esses recursos e
credenciais são configurados pelo operador.

`DJANGO_ENV_FILE` seleciona o arquivo de ambiente. Variável definida no processo
vence a do arquivo. Não misture os ciclos: o ciclo local remove `db.sqlite3` e
recria a baseline; o ciclo remoto remove objetos do schema `public` e aplica as
migrations versionadas já existentes.

## 2. Inventário de comandos

Todos os comandos de `system/management/commands/`. Arquivo que começa com `_` é
módulo compartilhado, não comando.

| Comando | Efeito | Guarda |
|---|---|---|
| `check_database_connection` | abre uma conexão e informa o alvo | somente leitura |
| `explain_perf_indexes` | mostra o plano de consulta dos índices críticos | somente leitura |
| `create_admin_superuser` | cria o superusuário a partir de `ADMIN_SUPERUSER_*` | idempotente; falha se as variáveis estiverem vazias |
| seeds de referência (§3) | catálogo, faixas, planos, produtos, cupons e feriados | explícitas, nunca em Build Command |
| seeds de demonstração (§3) | dado fictício de teste | explícitas; exigem `SEED_TEST_PORTAL_PASSWORD` |
| `seed_system_people_flow_samples` | amostra de fluxo de pessoas | explícita |
| `seed_system_initial_kanri_students_migration` | importação da base histórica | fora da primeira carga |
| `clear_test_data` | remove o dado fictício | explícita |
| `backfill_membership_timeline` | recompõe a linha do tempo de vínculo | idempotente |
| `generate_due_asaas_charges` | gera as cobranças vencidas no Asaas | escreve no gateway; exige ambiente correto |
| `clear_migration_supabase_hg` | apaga o schema `public` de **homologação** | ver §2.1 |
| `clear_migration_supabase_prod` | apaga o schema `public` de **produção** | ver §2.1 |
| `lock_supabase_api_access` | restringe o acesso à Data API do Supabase | exige ambiente remoto correto |

Fora de `management/commands/`: `clear_migrations.py` na raiz (ciclo local),
`scripts/build_prd_index.py` (índice de PRDs) e
`scripts/validate_skill_frontmatter.py` (skills nas três plataformas).

### 2.1 Protocolo do reset remoto

`clear_migration_supabase_hg` e `clear_migration_supabase_prod` **simulam por
padrão**: sem `--execute` eles listam o que seria removido e não removem nada.
Para executar, todas as condições abaixo precisam valer ao mesmo tempo:

- o ambiente carregado é o do comando (`hg` para um, `prod` para o outro);
- `DEBUG` é `False`;
- o host de `DATABASE_URL` termina em `.supabase.co` ou
  `.pooler.supabase.com`;
- `SUPABASE_PROJECT_REF` está preenchida e **corresponde ao host** da conexão —
  com dois projetos provisionados, a variável de confirmação sozinha não
  distingue o alvo;
- `SUPABASE_RESET_CONFIRM` traz o valor esperado pelo comando (`RESET_HG` ou
  `RESET_PROD`);
- `--execute` foi passado explicitamente.

Nenhum desses comandos entra em Build Command, migration ou teste.

## 3. Seeds — ordem e independência

Dado de negócio nunca é carregado implicitamente. Cada seed é independente;
nenhuma chama outra. A ordem abaixo é a fonte canônica: `/reset-local` e o
runbook a referenciam, não a duplicam.

| # | Comando | Variável exigida |
|---:|---|---|
| 1 | `create_admin_superuser` | `ADMIN_SUPERUSER_PASSWORD` |
| 2 | `seed_system_initial_person_type` | — |
| 3 | `seed_system_initial_belt_ranks` | — |
| 4 | `seed_system_initial_ibjjf_age_categories` | — |
| 5 | `seed_system_initial_graduation_rules` | — |
| 6 | `seed_system_initial_class_categories` | — |
| 7 | `seed_system_initial_teacher` | `SEED_INITIAL_TEACHER_PASSWORD` |
| 8 | `seed_system_initial_class_categories_teacher` | — |
| 9 | `seed_system_initial_class_catalog` | — |
| 10 | `seed_system_initial_teacher_payroll_configs` | — |
| 11 | `seed_system_initial_administrative` | `SEED_INITIAL_ADMINISTRATIVE_PASSWORD` |
| 12 | `seed_system_initial_class_categories_administrative` | — |
| 13 | `seed_system_initial_class_catalog_administrative` | — |
| 14 | `seed_system_initial_product_categories` | — |
| 15 | `seed_system_initial_product_catalog` | — |
| 16 | `seed_system_initial_subscription_plans` | — |
| 17 | `seed_system_initial_subscription_plans_values` | — |
| 18 | `seed_system_initial_coupons` | — |
| 19 | `seed_system_initial_holidays` | — |
| 20 | `seed_system_initial_plan_tiers` | — |
| 21 | `seed_system_initial_plan_prices` | — |

Os passos 12 e 13 são idempotentes e legados; a fonte principal do
administrativo é o passo 11.

As seeds de demonstração são opcionais, rodam depois do passo 21 e só entram
quando o objetivo pedir telas povoadas:
`seed_system_initial_test_students`, `seed_system_initial_test_guardians`,
`seed_system_initial_test_administrative` e
`seed_system_initial_test_teachers`. Exigem `SEED_TEST_PORTAL_PASSWORD` e
**não** entram em ambiente remoto sem decisão explícita. `clear_test_data`
desfaz apenas o que elas criaram.

Rodar uma seed duas vezes não deve duplicar dado; quando duplicar, é defeito da
seed, não do runbook. `seed_system_initial_kanri_students_migration` pertence à
importação da base histórica e fica fora da primeira carga padrão.

Os nomes de comando citados nesta seção são verificados por
`system/tests/test_seed_docs_contract.py`: documentar comando inexistente quebra
a suíte.

## 4. Local — SQLite

### 4.1 Criar a `.venv`

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python --version
```

Versão esperada: Python `3.12.10`.

### 4.2 Preparar e subir

```powershell
python manage.py check
python manage.py migrate
python manage.py create_admin_superuser
python manage.py test --verbosity 2
python manage.py runserver localhost:8000
```

Nesse estado existem somente o schema vazio e o superusuário. As seeds de
referência são executadas na ordem da §3.

### 4.3 Reset local completo de schema e migrations

Este fluxo é destrutivo somente no repositório local. Ele não acessa o Supabase
e valida o ambiente antes de remover qualquer arquivo.

Ele **encerra os processos Python deste repositório** antes de apagar e espera
até 8 segundos pela saída deles, porque no Windows o `runserver` aberto mantém
`db.sqlite3` bloqueado e o ciclo morre pela metade. O `taskkill` é aplicado por
PID, sem `/T`, para não derrubar árvore de processos alheia. Nunca encerra o
próprio processo, o pai direto nem os ancestrais: o `python.exe` de
`.venv/Scripts` é um shim que executa o interpretador base e aparece na
enumeração como ancestral, de modo que encerrá-lo derrubaria o próprio ciclo.

#### Guardas do ciclo destrutivo local

`clear_migrations.py` aplica as validações abaixo antes de qualquer remoção. Em
toda recusa o processo termina com código diferente de zero, imprime
`[ERRO] <motivo>` e nada é apagado.

| Condição | Mensagem |
|---|---|
| `manage.py` ausente ao lado do script | `Arquivo manage.py nao encontrado ao lado do script.` |
| Raiz Git não encontrada ao lado do script | `Raiz Git do projeto nao encontrada ao lado do script.` |
| `DJANGO_ENV_FILE` resolve para fora da raiz do projeto | `DJANGO_ENV_FILE deve apontar para um arquivo dentro do projeto.` |
| Arquivo de ambiente é `.env.hg` ou `.env.prod` | `Ciclo destrutivo local recusado: use o arquivo .env local.` |
| Arquivo de ambiente apontado não existe | `Arquivo de ambiente local nao encontrado: <caminho>` |
| `DJANGO_ENVIRONMENT` resolvido é diferente de `local` | `Ciclo destrutivo local recusado: DJANGO_ENVIRONMENT deve ser 'local'.` |
| `DATABASE_URL` preenchida | `Ciclo destrutivo local recusado: DATABASE_URL deve estar vazio para usar SQLite.` |
| Falta `ADMIN_SUPERUSER_USERNAME`, `ADMIN_SUPERUSER_EMAIL`, `ADMIN_SUPERUSER_PASSWORD`, `SEED_INITIAL_TEACHER_PASSWORD`, `SEED_INITIAL_ADMINISTRATIVE_PASSWORD` ou `SEED_TEST_PORTAL_PASSWORD` | `Configuracoes obrigatorias para o ciclo completo estao vazias: <lista>` |
| Alvo de banco resolve para fora da raiz | `Alvo de banco fora da raiz do projeto: <caminho>` |

Na checagem de seeds o script reporta o **nome** da chave vazia, nunca o valor.
As guardas remotas são cobertas por
`system/tests/test_supabase_reset_guards.py`.

#### Guarda de saída

Depois de remover, o script verifica o próprio resultado antes de declarar
sucesso e falha com `Limpeza incompleta. Veja os erros acima.` e código
diferente de zero. Sem essa verificação, uma remoção que falhasse sem levantar
passaria por sucesso e o problema só apareceria no `makemigrations` seguinte, com
baseline errada.

#### Ciclo completo

```powershell
.\.venv\Scripts\Activate.ps1
python clear_migrations.py
python manage.py makemigrations
python manage.py test --verbosity 2
python manage.py migrate
python manage.py create_admin_superuser
```

Em seguida os passos 2 a 21 da §3 e, ao final:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
```

O equivalente automatizado é o slash command `/reset-local`, que verifica as
guardas antes de apagar e para no primeiro erro.

Enquanto este for um MVP sem dado real que dependa do histórico, a baseline
única `system/migrations/0001_initial.py` é a regra. Não criar migration
incremental por padrão; mudança de schema deve terminar com o ciclo acima e uma
`0001_initial` consistente com os models atuais.

Essa regra muda no dia em que existir dado real de produção dependente do
histórico — a partir daí, o caminho normal passa a ser criar uma nova migration
a cada mudança, nunca apagar as antigas.

### 4.4 Importação da base histórica — opcional

Fora da primeira carga padrão:

```powershell
python manage.py seed_system_initial_kanri_students_migration
```

O arquivo de revisão da importação fica em `static/initial_data/` e é ignorado
pelo Git.

## 5. Homologação — Supabase

HG usa as mesmas proteções de conexão de produção, com `DJANGO_ENVIRONMENT=hg`,
`DJANGO_DEBUG=False`, `DATABASE_URL` e `SUPABASE_PROJECT_REF`.

Checagem somente leitura:

```powershell
$env:DJANGO_ENV_FILE='.env.hg'
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py check_database_connection --require-postgresql
.\.venv\Scripts\python.exe manage.py showmigrations
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

Rode `collectstatic` antes de `check`: com `DEBUG=False` o manifest de
staticfiles é obrigatório.

Simulação do reset:

```powershell
$env:DJANGO_ENV_FILE='.env.hg'
$env:SUPABASE_RESET_CONFIRM='RESET_HG'
.\.venv\Scripts\python.exe manage.py clear_migration_supabase_hg
Remove-Item Env:\SUPABASE_RESET_CONFIRM -ErrorAction SilentlyContinue
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

Ciclo de primeira carga depois do reset ou em projeto vazio:

```text
collectstatic -> check -> migrate -> passos 1 a 21 da §3
-> lock_supabase_api_access -> check -> showmigrations
```

Não use `clear_migrations.py` e não rode `makemigrations` contra HG. Não rode as
seeds de demonstração em HG sem decisão explícita.

A execução com `--execute` é destrutiva e exige confirmação explícita do
operador, igual à produção.

## 6. Produção — Supabase

O Django usa somente conexão PostgreSQL privada pela `DATABASE_URL`. Não usa
Supabase Auth, REST, GraphQL nem chaves `NEXT_PUBLIC_*`.

Configuração:

- session pooler `aws-….pooler.supabase.com:5432`;
- `sslmode=require`;
- `DB_CONN_MAX_AGE=0`;
- `DISABLE_SERVER_SIDE_CURSORS=True`;
- `SUPABASE_PROJECT_REF` confirma o projeto em operação destrutiva.

### 6.1 Checagem segura, sem escrita

```powershell
$env:DJANGO_ENV_FILE='.env.prod'
python manage.py collectstatic --noinput
python manage.py check --deploy
python manage.py check_database_connection --require-postgresql
python manage.py lock_supabase_api_access --check
python manage.py showmigrations
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

### 6.2 Bloquear a Data API depois das migrations

```powershell
$env:DJANGO_ENV_FILE='.env.prod'
python manage.py lock_supabase_api_access
python manage.py lock_supabase_api_access --check
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

O comando recusa SQLite, habilita RLS nas tabelas Django em `public`, revoga
`anon`, `authenticated` e `service_role` dessas tabelas e sequências, revoga os
privilégios padrão do owner para futuras tabelas, sequências e funções, é
idempotente e possui `--check` somente leitura.

O papel gerenciado `supabase_admin` não pode ter seus defaults alterados pelo
usuário `postgres` hospedado. Como o projeto não usa a Data API, ela também deve
permanecer desativada no Dashboard.

### 6.3 Reset de produção — somente incidente controlado

Antes de qualquer reset:

1. confirme que `SUPABASE_PROJECT_REF` identifica o projeto descartável
   correto;
2. execute primeiro a simulação e revise a lista de objetos.

Simulação segura:

```powershell
$env:DJANGO_ENV_FILE='.env.prod'
$env:SUPABASE_RESET_CONFIRM='RESET_PROD'
python manage.py clear_migration_supabase_prod
Remove-Item Env:\SUPABASE_RESET_CONFIRM -ErrorAction SilentlyContinue
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

Execução destrutiva, somente após aprovação humana explícita: repetir o bloco
acima com `--execute`.

O comando lista e remove somente tabelas Django do schema `public` (`auth_*`,
`django_*`, `system_*`). Ele preserva schemas internos e objetos não
pertencentes ao Django. Nunca coloque esse comando no Render. Depois do reset,
publique o serviço: o Build recria somente o schema.

Reset de produção não recria o estado dos gateways: cobrança e assinatura já
criadas no Asaas e no Stripe continuam existindo lá. Conferir os painéis antes e
depois, e não declarar consistência sem evidência do gateway e do ORM.

### 6.4 Seed descartável em produção

Somente depois de validar o serviço limpo, e com autorização explícita: repetir
o ciclo de primeira carga apontando `DJANGO_ENV_FILE` para `.env.prod` e
finalizar com `lock_supabase_api_access`.

As seeds de demonstração em produção só com decisão operacional registrada; para
remover apenas o dado fictício, use `clear_test_data`.
