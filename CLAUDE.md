# CLAUDE.md

@AGENTS.md

Contexto factual do projeto LV JIU JITSU. Procedimentos pertencem ao `AGENTS.md`, aos documentos em `docs/` e às skills.

## 1. Produto

| Campo | Valor |
|---|---|
| Nome | LV JIU JITSU |
| Objetivo | Portal de academia para cadastro, turmas, presença, graduação, planos, materiais, financeiro e repasses |
| Stack | Python 3.12.10, Django 5.2.14 LTS, templates server-rendered |
| App de domínio | `system/` |
| Banco local | SQLite em `db.sqlite3` |
| HG/produção | Supabase PostgreSQL via `DATABASE_URL` |
| Deploy | Render configurado pelo Dashboard |
| Ambiente padrão | Windows, PowerShell e `.venv` |
| Idioma da UI | Português pt-BR |
| Pagamentos ativos | Asaas PIX/cartão e Stripe recorrente |

## 2. Arquitetura

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

- Domínio concentrado em `system/`.
- Regra de negócio e integrações em `services/`.
- Views finas e validação server-side.
- Templates públicos e de autenticação em `templates/login/`.
- CSS/JS editável em `static/system/`.
- `staticfiles/` é saída gerada.
- Wizard público ativo: `static/system/js/auth/register.js`.
- Atualizar o parâmetro `?v=` quando um asset versionado for alterado.

## 3. Contratos locais

- UI: `docs/UI-SCREEN-CONTRACT.md`.
- Cadastro público: `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`.
- Guias do wizard: `docs/wizard-step-plan-aluno-titular.md`, `docs/wizard-step-plan-aluno-com-dependente.md` e `docs/wizard-step-plan-responsavel-com-aluno.md`.
- Pagamentos e webhooks: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`.
- Banco, migrations e seeds: `docs/OPERACAO-BANCO-SEEDS.md`.
- PRDs: `docs/prd/`.
- Governança: `docs/AGENT-WORKFLOW.md`.
- Padrão de PRD: `docs/PRD-STANDARD.md`.
- Plataformas: `docs/PLATFORM-ADAPTERS.md`.

## 4. Comandos locais

```powershell
.\.venv\Scripts\pip.exe install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py shell -c "<CHECK>"
```

`manage.py test` e ORM potencialmente mutável só são executados após autorização.

## 5. Ambientes e deploy

| Arquivo | Uso |
|---|---|
| `.env` | Local |
| `.env.hg` | Homologação |
| `.env.prod` | Produção |
| `.env.example` | Contrato versionável |

No Render, variáveis são configuradas no Dashboard. Não existem `render.yaml` ou `build.sh`.

Build:

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py lock_supabase_api_access
```

Start: Gunicorn conforme configuração do serviço Render.

`lock_supabase_api_access` é idempotente.

## 6. Banco e schema

- O projeto adota uma única migration vigente `system/migrations/0001_initial.py`.
- Não criar migrations incrementais por padrão.
- Mudança de schema exige decisão e ciclo destrutivo executado pelo usuário.
- O agente não executa reset, `makemigrations`, `migrate` ou seeds sem autorização.
- Testes Django usam banco isolado e não exigem apagar `db.sqlite3`.
- Operação completa: `docs/OPERACAO-BANCO-SEEDS.md`.

## 7. Cadastro público

Fonte principal: PRD-040.

Fluxo obrigatório:

1. selecionar perfil e preencher dados;
2. selecionar plano;
3. pagar mensalidade;
4. retornar ao wizard com pagamento confirmado;
5. pagar ou pular materiais;
6. revisar;
7. finalizar;
8. somente então criar `Person`, `PortalAccount`, relações, turmas e acesso.

Antes da finalização, o estado pertence a `PreRegistration`.

## 8. Pagamentos

- Asaas: PIX, cartão, webhooks e repasses.
- Stripe: assinatura recorrente, checkout e webhooks.
- Configuração vem de settings e `.env`.
- `SITE_BASE_URL` gera retornos públicos.
- O fluxo Asaas local exige túnel HTTPS válido e domínio aceito pelo provedor.
- O browser interno opera na URL local canônica; callbacks externos usam a URL pública configurada.
- Detalhes, simulações e limitações estão no guia de teste e no PRD-058.

## 9. UI e validação

- URL local canônica: `http://127.0.0.1:8000`.
- Tema claro e escuro são obrigatórios.
- Alteração visual exige proposta aprovada antes do código.
- Após implementação, usar o navegador interno disponível.
- Validar desktop, mobile, caminho feliz, edge case, console e evidência visual.
- Testes podem ser escritos no TDD, mas só são executados após autorização.

## 10. Ambientes remotos

- HG e produção usam Supabase PostgreSQL.
- Reset remoto exige comando específico, variável de confirmação e autorização.
- Produção não é ambiente de experimentação.
- Deploy, painel Asaas, painel Stripe e Render exigem autorização explícita.

## 11. Projeto irmão

`Visary` pode fornecer governança, shell, tokens de UI, auth e padrões de wizard.

O bootstrap canônico de governança reutilizável vive no Visary em `docs/agent-bootstrap/`; ressincronizações devem partir dele e substituir placeholders pelo domínio LV.

Não portar domínio de consultoria de vistos.
