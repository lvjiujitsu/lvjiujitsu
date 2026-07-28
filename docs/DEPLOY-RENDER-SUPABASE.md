# Deploy oficial — Render + Supabase

Configuração manual, sem Blueprint, `render.yaml` ou Dockerfile. Esta é a
decisão vigente, registrada em `CLAUDE.md`.

Nenhum segredo aparece neste documento. Valores reais ficam em
**Service → Environment** no Render e nos arquivos `.env.hg` e `.env.prod`
locais, que são privados e ignorados pelo Git.

## 1. Serviços

| Ambiente | Web Service | Banco |
|---|---|---|
| Homologação | Render, branch de trabalho | projeto Supabase de homologação |
| Produção | Render, branch `main` | projeto Supabase de produção |

| Campo | Valor |
|---|---|
| Language | `Python 3` |
| Region | escolher a mesma do projeto Supabase, para reduzir latência |
| Root Directory | vazio |
| Instance Type | `Free` enquanto for MVP |

`.python-version` fixa Python `3.12.10`. O Render respeita esse arquivo.

## 2. Comandos exatos

### Build Command

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py lock_supabase_api_access
```

Ordem: dependências → staticfiles → migrations → bloqueio da Data API.

**Seeds não entram no Build Command.** Nenhum dado de negócio é carregado
implicitamente: as 21 seeds de referência, as seeds de teste e os resets remotos são
executados manualmente, apontando `DJANGO_ENV_FILE` para o ambiente alvo,
conforme `docs/OPERACAO-BANCO-SEEDS.md`.

`create_admin_superuser` também não entra no build. O superusuário é criado uma
vez, por execução explícita — está na tabela de seeds do `CLAUDE.md` §8 e segue
a mesma regra das demais.

### Start Command

```text
gunicorn lvjiujitsu.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

Não cadastre `PORT`; o Render fornece a variável.

## 3. Health check

| Campo | Valor |
|---|---|
| Health Check Path | `/health/` |

A rota responde `{"status": "ok"}` com HTTP 200, sem autenticação e **sem
consultar o banco**. A escolha é deliberada: em incidente de banco, o serviço
continua respondendo e o Render não reinicia a instância por engano. Para
verificar o banco, use `check_database_connection`, que é comando de operação,
não endpoint público.

## 4. Environment Variables

Cadastre em **Service → Environment**. Os arquivos `.env.hg` e `.env.prod`
locais são apenas referência privada — o Render não os lê.

Os quatro arquivos de ambiente (`.env`, `.env.example`, `.env.hg`,
`.env.prod`) declaram o mesmo conjunto de chaves. A lista canônica de nomes
está em `.env.example`, versionado e sem segredo.

Grupos de variáveis:

| Grupo | Papel |
|---|---|
| `DJANGO_ENVIRONMENT` | `hg` ou `prod`; determina as validações de `settings.py` |
| `DJANGO_SECRET_KEY` | exclusiva por ambiente, nunca reaproveitada |
| `DJANGO_DEBUG` | `False` em ambiente remoto; `settings.py` recusa `True` |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | domínio real do serviço |
| `DJANGO_SECURE_*`, `DJANGO_SESSION_COOKIE_*`, `DJANGO_CSRF_COOKIE_*` | transporte e cookies; restritivos em remoto |
| `DATABASE_URL` | session pooler do Supabase, com `sslmode=require` |
| `SUPABASE_PROJECT_REF` | referência do projeto; conferida antes de qualquer reset |
| `DB_CONN_MAX_AGE` | reuso de conexão |
| `ADMIN_SUPERUSER_*`, `SEED_INITIAL_*`, `SEED_TEST_PORTAL_PASSWORD` | seeds e acesso administrativo |
| `ASAAS_*`, `STRIPE_*` | credenciais e taxas dos gateways |
| `SITE_BASE_URL` | base dos retornos públicos usados pelos gateways |
| `DJANGO_EMAIL_*` | envio de e-mail |

Não cadastre `DJANGO_ENV_FILE`, `PORT` nem `SUPABASE_RESET_CONFIRM`, e não
suba `.env.hg` ou `.env.prod` como Secret File.

## 5. Supabase

A aplicação conecta **apenas** por `DATABASE_URL`, usando o session pooler na
porta 5432 com `sslmode=require`. Não há uso de Supabase Auth, REST ou GraphQL.

`lock_supabase_api_access` roda no fim de cada build e:

- habilita Row Level Security nas tabelas Django do schema `public`;
- revoga privilégios das roles `anon`, `authenticated` e `service_role`;
- revoga privilégios padrão para tabelas, sequences e funções.

É idempotente e ignora SQLite. Para auditar sem escrever:

```powershell
$env:DJANGO_ENV_FILE='.env.prod'
.\.venv\Scripts\python.exe manage.py lock_supabase_api_access --check
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

A saída reporta quantas tabelas Django existem, quantos grants estão expostos,
quantas tabelas estão sem RLS e quantos defaults seguem expostos.

## 6. Auto-deploy

| Ambiente | Gatilho |
|---|---|
| Homologação | push na branch de trabalho |
| Produção | push em `main` |

Antes de promover para produção: rodar a suíte local, `manage.py check`
apontando para `.env.prod`, e `collectstatic --noinput` — sem o manifest, o
`check` falha com `Missing staticfiles manifest entry`.

## 7. Reset destrutivo remoto

Nunca entra no Build Command. Exige, em conjunto:

1. `DJANGO_ENVIRONMENT` igual ao alvo do comando;
2. `DJANGO_DEBUG=False`;
3. `DATABASE_URL` apontando para host oficial Supabase;
4. `SUPABASE_PROJECT_REF` correspondente ao host — a guarda que impede
   derrubar o projeto errado quando a `DATABASE_URL` foi trocada por engano;
5. `SUPABASE_RESET_CONFIRM` igual a `RESET_HG` ou `RESET_PROD`;
6. conexão PostgreSQL real;
7. a flag `--execute`.

**Sem `--execute` o comando apenas lista o que seria removido.** Rode sempre a
simulação primeiro e confira o `Projeto Supabase confirmado` na saída antes de
executar.

```powershell
$env:DJANGO_ENV_FILE='.env.hg'
$env:SUPABASE_RESET_CONFIRM='RESET_HG'
.\.venv\Scripts\python.exe manage.py clear_migration_supabase_hg
Remove-Item Env:\SUPABASE_RESET_CONFIRM -ErrorAction SilentlyContinue
Remove-Item Env:\DJANGO_ENV_FILE -ErrorAction SilentlyContinue
```

O procedimento completo, incluindo a recarga das seeds, está em
`docs/OPERACAO-BANCO-SEEDS.md`.

## 8. Logs esperados

No deploy, confirme na ordem:

1. requirements instalados;
2. `collectstatic` concluído;
3. migrations aplicadas;
4. `Data API bloqueada`;
5. `Build successful`;
6. Gunicorn ouvindo no `$PORT`.

Nenhuma seed e nenhum reset aparecem nesse log. Se aparecerem, o Build Command
está errado.

## 9. Smoke test depois do deploy

```powershell
$baseUrl='<url pública do serviço>'
(Invoke-WebRequest "$baseUrl/login/").StatusCode
(Invoke-WebRequest "$baseUrl/register/").StatusCode
(Invoke-WebRequest "$baseUrl/").StatusCode
Invoke-RestMethod "$baseUrl/health/"
```

Validação manual:

1. login em `/login/` autentica e redireciona;
2. `/` serve o conteúdo do papel autenticado — a home é única e muda por
   permissão;
3. o wizard público `/register/` abre sem autenticação e chega ao passo de
   plano;
4. `/pessoas/`, `/turmas/`, `/aulas/`, `/graduacao/`, `/planos/` e
   `/financeiro/` respondem sem erro 500;
5. o alias em inglês de cada rota redireciona para o caminho pt-BR;
6. o retorno de checkout e o webhook de gateway respondem no domínio público
   configurado em `SITE_BASE_URL`;
7. `/django-admin/` permanece ferramenta técnica separada do painel do produto.

Antes de qualquer seed, o ambiente tem apenas o superusuário e nenhum dado de
negócio. Só depois dessa comprovação carregue as 21 seeds de referência
apontando `DJANGO_ENV_FILE` para o ambiente alvo, conforme
`docs/OPERACAO-BANCO-SEEDS.md`. As seeds `seed_system_initial_test_*` não
entram em ambiente remoto sem decisão explícita.

Pagamento em ambiente remoto segue `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`:
não declarar confirmação sem evidência do gateway e do ORM.
## 10. Referências

- [docs/OPERACAO-BANCO-SEEDS.md](OPERACAO-BANCO-SEEDS.md) — banco, migrations e
  seeds;
- [CLAUDE.md](../CLAUDE.md) — fatos do produto e ambientes;
- [README.md](../README.md) — setup e comandos locais;
- [Render — Deploying Django](https://render.com/docs/deploy-django);
- [Render — Web Services](https://render.com/docs/web-services);
- [Supabase — Connecting to your database](https://supabase.com/docs/guides/database/connecting-to-postgres);
- [Supabase — Securing your API](https://supabase.com/docs/guides/api/securing-your-api);
- [Supabase — Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security).
