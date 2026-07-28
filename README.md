# LV JIU JITSU

Portal de academia. Gerencia cadastro de aluno e responsável, turmas e
presença, graduação por faixa e categoria, planos e mensalidade, loja de
materiais, financeiro e repasse de professor. Aluno, responsável, professor e
administrativo entram pela mesma home, que resolve o papel pela sessão.

## Stack

- Python 3.12.10, Django 5.2.14 LTS;
- SQLite local, PostgreSQL via Supabase em homologação e produção;
- Asaas para PIX e cartão, Stripe para assinatura recorrente;
- WhiteNoise para estáticos, Gunicorn e Render como serviço web.

## Estrutura

App único `system/`, organizado por responsabilidade: `models/`, `forms/`,
`services/`, `selectors/`, `views/`, `management/commands/`, `utils/` e
`tests/`. O projeto Django fica em `lvjiujitsu/`.

A baseline de migrations é única: `system/migrations/0001_initial.py`.

## Setup local

```powershell
cd 'C:\Users\whsf\Documents\GitHub\lvjiujitsu'
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Copie `.env.example` para `.env` e preencha os valores locais. `DATABASE_URL`
fica vazia no ambiente local, que usa SQLite.

## Ciclo local completo

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
```

Em seguida rode as 21 seeds `seed_system_initial_*` na ordem canônica de
[docs/OPERACAO-BANCO-SEEDS.md](docs/OPERACAO-BANCO-SEEDS.md), que começa em
`person_type` e termina em `plan_prices`. As seeds `seed_system_initial_test_*`
são opcionais e só entram quando o objetivo pedir telas povoadas. O equivalente
automatizado é o slash command `/reset-local`, que verifica as guardas antes de
apagar.

`clear_migrations.py` recusa a execução quando o ambiente não é
inequivocamente local — `.env.hg`, `.env.prod`, `DJANGO_ENVIRONMENT` remoto ou
`DATABASE_URL` preenchida param o script antes de qualquer remoção. As guardas
estão descritas no runbook de banco.

## Servidor e URLs

```powershell
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
```

| URL | Superfície |
|---|---|
| `http://localhost:8000/` | home única, conteúdo conforme o papel da sessão |
| `http://localhost:8000/login/` | login próprio |
| `http://localhost:8000/register/` | wizard público de cadastro |
| `http://localhost:8000/pessoas/` | pessoas e dependentes |
| `http://localhost:8000/turmas/` | turmas e catálogo |
| `http://localhost:8000/aulas/` | aulas e presença |
| `http://localhost:8000/graduacao/` | graduação e faixas |
| `http://localhost:8000/planos/` | planos, tiers e preços |
| `http://localhost:8000/materiais/` e `/loja/` | materiais e loja |
| `http://localhost:8000/financeiro/` | financeiro e repasses |
| `http://localhost:8000/pagamentos/` | retorno de checkout e webhook de gateway |
| `http://localhost:8000/administracao/` | administração do produto |
| `http://localhost:8000/django-admin/` | Django Admin técnico |
| `http://localhost:8000/health/` | health check |

As rotas têm alias em inglês além do caminho pt-BR. O Django Admin é ferramenta
técnica e não é o painel operacional do produto.

## Validação

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe scripts\build_prd_index.py --check
.\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
.\.venv\Scripts\python.exe -m pip check
```

Apontando para `.env.hg` ou `.env.prod`, rode `collectstatic` antes de
`check`, senão o manifest de estáticos faltará.

O CI em `.github/workflows/ci.yml` roda `pip check`, o validador de skills, o
verificador do índice de PRD, `manage.py check`, `makemigrations --check` e a
suíte a cada push.

## Ambientes

| Arquivo | Ambiente | Banco |
|---|---|---|
| `.env` | local | SQLite |
| `.env.hg` | homologação | PostgreSQL Supabase |
| `.env.prod` | produção | PostgreSQL Supabase |
| `.env.example` | template versionado | — |

Os quatro declaram o mesmo conjunto de chaves. `.env`, `.env.hg` e `.env.prod`
são privados e ignorados pelo Git. O procedimento de deploy está em
[docs/DEPLOY-RENDER-SUPABASE.md](docs/DEPLOY-RENDER-SUPABASE.md).

## Governança

- [AGENTS.md](AGENTS.md) — protocolo comum de agentes;
- [CLAUDE.md](CLAUDE.md) — fatos do produto e dos ambientes;
- [docs/AGENT-WORKFLOW.md](docs/AGENT-WORKFLOW.md) — ciclo de trabalho;
- [docs/PRD-STANDARD.md](docs/PRD-STANDARD.md) — formato de PRD;
- [docs/PLATFORM-ADAPTERS.md](docs/PLATFORM-ADAPTERS.md) — Claude, Codex e
  Cursor;
- [docs/UI-SCREEN-CONTRACT.md](docs/UI-SCREEN-CONTRACT.md) — contrato visual;
- [docs/OPERACAO-BANCO-SEEDS.md](docs/OPERACAO-BANCO-SEEDS.md) — banco,
  migrations e seeds;
- [docs/DEPLOY-RENDER-SUPABASE.md](docs/DEPLOY-RENDER-SUPABASE.md) — deploy;
- [docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md](docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md) — roteiro de teste manual e pagamentos;
- [docs/prd/README.md](docs/prd/README.md) — índice canônico das PRDs.

As sete skills vivem em `.claude/skills/` e são espelhadas byte a byte em
`.agents/skills/` e `.cursor/skills/`. Os slash commands `/reset-local`,
`/validar-tela` e `/sync-skills` ficam em `.claude/commands/`.

## Licença

MIT. Ver [LICENSE](LICENSE).
