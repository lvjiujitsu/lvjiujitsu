# LV JIU JITSU

Plataforma Django server-rendered, MVP descartável, operada em três ambientes:
local, homologação e produção. O que o produto faz está em
`obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md`; os fatos de plataforma
estão em [CLAUDE.md](CLAUDE.md).

## Stack

- Python 3.12.10, Django 5.2.16 LTS;
- SQLite local, PostgreSQL via Supabase em homologação e produção;
- WhiteNoise para estáticos, Gunicorn e Render como Web Service Python;
- versões exatas em `requirements.txt`, o único arquivo de dependências;
- as integrações externas deste produto estão em
  `obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md`.

## Estrutura

App único `system/`, organizado por responsabilidade: `models/`, `forms/`,
`services/`, `selectors/`, `views/`, `management/commands/`, `utils/` e
`tests/`. `templates/` e `static/` ficam na raiz do repositório. O projeto
Django fica em `lvjiujitsu/`.

A baseline de migrations é única: `system/migrations/0001_initial.py`.

A documentação raiz do repositório é `CLAUDE.md`, `AGENTS.md`, `README.md`
e `docs/prd/`; as ferramentas de agente têm instruções junto de seus scripts.
Todo contrato de ciclo, PRD, UI, banco, deploy e operação vive no vault
Obsidian.

## Setup local

```powershell
cd C:\Users\whsf\Documents\GitHub\lvjiujitsu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

O `.env` local não é versionado. `.env.example` é o contrato de chaves; os
arquivos reais moram no diretório compartilhado do operador, e `settings.py` os
encontra sozinho.

## Ciclo local completo

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
```

Depois do superusuário, executar as seeds de domínio na ordem canônica de
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`, que também lista
as variáveis de ambiente que cada uma exige. `clear_test_data` remove o dado
fictício.

Invocar o ciclo destrutivo local é a autorização explícita para rodar as seeds.

## Servidor e URLs

```powershell
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
```

| Rota | Papel |
|---|---|
| `/` | entrada única: autenticação quando anônimo, conteúdo do papel quando há sessão |
| `/health/` | health check do Render |
| `/django-admin/` | Django Admin técnico, isolado; **não** é o painel do produto |

As demais rotas, o que cada superfície entrega e quem acessa estão em
`obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md`.

## Validação

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe -m pip check
```

O CI em `.github/workflows/ci.yml` roda os mesmos gates em push para `stage` e
`developer` e em Pull Request para `stage`.

Mudança visual não fecha sem a rota real aberta em desktop e mobile, nos dois
temas, com console limpo e screenshot registrado.

## Ambientes

| Arquivo | Uso | `DJANGO_ENVIRONMENT` | Banco |
|---|---|---|---|
| `.env` | local | `local` | SQLite `db.sqlite3` |
| `.env.hg` | homologação | `hg` | PostgreSQL Supabase |
| `.env.prod` | produção | `prod` | PostgreSQL Supabase |
| `.env.example` | contrato versionado | — | — |

Os quatro declaram o mesmo conjunto de chaves, conferido por
`manage.py check_environment_parity`, que imprime nome de chave e nunca valor.
No Render as variáveis ficam no Dashboard e não existe `.env` no deploy.

## Governança

No repositório:

- [AGENTS.md](AGENTS.md) — protocolo comum de agentes;
- [CLAUDE.md](CLAUDE.md) — fatos do produto e dos ambientes;
- [docs/prd/README.md](docs/prd/README.md) — índice canônico das PRDs.

Os contratos de ciclo, PRD, UI, fluxos, banco, deploy, performance, teste manual
e plataformas vivem no vault Obsidian do operador, em
`C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\`, com índice em
`lvjiujitsu.md`:

- `ciclo-execucao-lvjiujitsu.md` — ciclo de trabalho;
- `padrao-prd-lvjiujitsu.md` — formato de PRD;
- `contrato-ui-lvjiujitsu.md` — contrato visual;
- `fluxos-tela-lvjiujitsu.md` — fluxos de tela;
- `operacao-banco-seeds-lvjiujitsu.md` — banco, migrations e seeds;
- `deploy-render-supabase-lvjiujitsu.md` — deploy;
- `performance-plataforma-lvjiujitsu.md` — teto da plataforma e orçamento de carga;
- `guia-teste-cliente-lvjiujitsu.md` — roteiro de teste manual;
- `plataformas-agente-lvjiujitsu.md` — Claude Code e Codex;
- `comandos-powershell-lvjiujitsu.md` — runbook dos três ambientes;
- `conhecimento-lvjiujitsu.md` — por que cada decisão é a que é, e o que morde;
- `regras-negocio-lvjiujitsu.md` — regra de negócio específica do produto.

Quem clona o repositório sem o vault tem código, PRDs e os dois arquivos de
protocolo; os contratos acima ficam inalcançáveis.

As três skills de ciclo autônomo são canônicas em `.agents/skills/`, com
referências, scripts e testes de contrato; `.claude/skills/` guarda um adaptador
fino de cada uma, mais `lvjiujitsu-remote-refresh`, de invocação manual. O slash
commands `/validar-tela` e `/reset-local` ficam em `.claude/commands/`.
O hook `Stop` verifica CSS, qualidade e índice de PRDs sem alterar arquivos.

## Licença

Ver [LICENSE](LICENSE).
