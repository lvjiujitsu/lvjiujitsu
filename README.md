# LV JIU JITSU

Portal de academia para cadastro, turmas, presença, graduação, planos, materiais, financeiro e repasses.

## Stack

- Python 3.12.10
- Django 5.2.14 LTS, templates server-rendered
- SQLite local (`db.sqlite3`); Supabase PostgreSQL em homologação e produção
- Pagamentos: Asaas (PIX/cartão) e Stripe (assinatura recorrente)
- Deploy: Render

## Estrutura

```text
system/
├── models/
├── forms/
├── services/
├── selectors/
├── views/
├── tests/
└── management/commands/
```

Domínio concentrado em `system/`. Regra de negócio em `services/`, leituras em `selectors/`, validação em `forms/`, views finas.

## Ambiente local

Pré-requisitos: Python 3.12, PowerShell, `.venv` na raiz do repo.

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
```

Instalar dependências de desenvolvimento (ferramentas de validação de governança, como o validador de skills) somente quando necessário:

```powershell
.\.venv\Scripts\pip.exe install -r requirements-dev.txt
```

Variáveis de ambiente locais ficam em `.env`. Ver `.env.example` para o contrato versionável.

## Comandos úteis

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py shell -c "<CHECK>"
```

Operação de banco, migrations e seeds: `docs/OPERACAO-BANCO-SEEDS.md`.

## Governança e agentes

Este repositório segue um protocolo de governança para agentes de desenvolvimento (Claude Code, Codex, Cursor):

- `AGENTS.md` — protocolo comum entre ferramentas.
- `CLAUDE.md` — contexto factual do projeto LV.
- `docs/AGENT-WORKFLOW.md` — fluxo detalhado de execução.
- `docs/PRD-STANDARD.md` — padrão de PRD.
- `docs/PLATFORM-ADAPTERS.md` — diferenças por ferramenta e skills.
- `docs/prd/` — PRDs do projeto.

Mudanças relevantes exigem uma PRD em `docs/prd/PRD-<NNN>-<slug>.md` antes da implementação.

## Documentação

- UI: `docs/UI-SCREEN-CONTRACT.md`.
- Cadastro público: `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`.
- Pagamentos e webhooks: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`.
- Banco, migrations e seeds: `docs/OPERACAO-BANCO-SEEDS.md`.
