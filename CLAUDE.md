# CLAUDE.md

@AGENTS.md

Contexto factual do LV JIU JITSU. Procedimentos de agente (como conduzir uma
mudança, quando criar PRD, como validar) pertencem ao `AGENTS.md`, aos
documentos em `docs/` e às skills em `.claude/skills/` — este arquivo só
descreve o que o projeto é e como operá-lo.

Seções 1 a 11 são o núcleo factual. Seções a partir de 12, quando existirem,
descrevem regra de negócio específica deste produto.

## 1. Natureza do projeto

- O LV JIU JITSU é um MVP descartável. Local, homologação e produção não contêm
  dado real de negócio.
- Produção é uma simulação recriável por `migrate` e pela execução explícita
  das seeds; não é a fonte de um histórico de aluno, pagamento ou graduação.
- É essa propriedade — e só ela — que autoriza a baseline única de migration, o
  ciclo destrutivo local sem pergunta e o reset remoto de schema descrito em
  `docs/OPERACAO-BANCO-SEEDS.md`. Sem ela, nenhuma dessas operações seria
  aceitável.
- Segredo operacional continua sendo tratado como secreto e nunca é impresso em
  saída, log ou PRD, mesmo quando a credencial for descartável. Ao ler arquivo
  de ambiente, reportar nomes de chave, não valores.
- **Condição de revogação:** no dia em que existir aluno real, cobrança real ou
  repasse real cujo histórico importe, esta seção é revogada. A partir daí,
  reset remoto volta a exigir backup e plano de restauração, e migrations
  passam a preservar o histórico em vez de serem recriadas.

### O que não existe neste projeto

Declarado para que nenhum agente proponha, assuma ou "restaure" o que nunca
houve:

- sem ambiente além de `local`, `hg` e `prod`;
- sem `render.yaml`, `build.sh` ou Dockerfile — o Render é configurado pelo
  Dashboard;
- sem `requirements-dev.txt`: há um único arquivo de dependências;
- sem `seed_test_data` único: dado fictício vem das seeds
  `seed_system_initial_test_*`;
- sem gateway além de Asaas e Stripe. Não adicionar terceiro provedor sem
  requisito explícito.

## 2. Produto

| Campo | Valor |
|---|---|
| Nome | LV JIU JITSU |
| Objetivo | Portal de academia para cadastro, turmas, presença, graduação, planos, materiais, financeiro e repasses |
| App de domínio | `system/` |
| Banco local | SQLite em `db.sqlite3` |
| HG e produção | PostgreSQL Supabase via `DATABASE_URL` |
| Deploy | Render, configurado pelo Dashboard |
| Ambiente padrão | Windows, PowerShell e `.venv` |
| Idioma da UI | Português pt-BR |
| URL local canônica | `http://localhost:8000` |

O trabalho diário acontece em `/`, uma home única que resolve o papel pela
sessão e serve conteúdo diferente por permissão. O painel do produto **não**
usa `AdminSite`.

| Superfície | Rotas de entrada | O que entrega | Acesso |
|---|---|---|---|
| Público | `/login/`, `/register/` | login próprio e wizard público de cadastro | público, sem sessão |
| Operação interna | `/`, `/pessoas/`, `/turmas/`, `/aulas/`, `/graduacao/`, `/planos/`, `/materiais/`, `/loja/`, `/financeiro/`, `/administracao/`, `/requests/` | gestão dos módulos do produto | interno, por papel |
| Área do aluno e do responsável | `/minha-mensalidade/`, `/meus-materiais/`, `/dependents/` | consulta do próprio vínculo, mensalidade e material | aluno, responsável |
| Pagamentos | `/pagamentos/` | retorno de checkout e webhook de gateway | público para webhook, autenticado para retorno |

As rotas têm alias em inglês além do caminho pt-BR; o redirecionamento é
coberto por `system/tests/test_url_pt_redirects.py`.

`/health/` responde ao health check do Render. O Django Admin técnico
(`/django-admin/`) é isolado e **não** é o painel operacional do produto.

Templates públicos e de autenticação ficam em `templates/login/`.

## 3. Stack

- Python 3.12.10, Django 5.2.14 LTS, templates server-rendered;
- SQLite local, PostgreSQL (Supabase) em homologação e produção;
- Asaas para PIX e cartão, Stripe para assinatura recorrente;
- WhiteNoise para estáticos em produção; Render como Web Service Python;
- versões exatas em `requirements.txt`, o único arquivo de dependências.

## 4. Arquitetura em camadas

```text
system/
├── models/
├── forms/
├── services/
├── selectors/
├── views/
├── tests/
├── management/commands/
└── utils/
```

| Caminho | Responsabilidade |
|---|---|
| `system/models/` | persistência e invariantes |
| `system/forms/` | validação server-side |
| `system/services/` | regra de negócio, integração de gateway e escrita transacional |
| `system/selectors/` | leitura reutilizável, fora de views |
| `system/views/` | HTTP fino |
| `system/middleware.py` | `PortalSessionMiddleware` |
| `system/constants.py`, `system/runtime_config.py` | constantes e configuração derivada |
| `system/management/commands/` | seeds, checagens de conexão e limpeza de dado de teste |
| `system/tests/` | um arquivo por camada ou funcionalidade |
| `templates/` | apresentação; público e autenticação em `templates/login/` |
| `static/system/` | CSS e JS editáveis; wizard público em `static/system/js/auth/register.js` |
| `staticfiles/` | saída gerada por `collectstatic`; nunca editar à mão |

Ao alterar asset versionado, atualizar o parâmetro `?v=` da referência.

A responsabilidade de cada camada como protocolo está em `AGENTS.md` §9.

## 5. Contratos locais

Um dono por assunto. Ao divergir do código, o código vence e o contrato é
corrigido na mesma mudança.

| Assunto | Documento |
|---|---|
| Protocolo de agente | [`AGENTS.md`](AGENTS.md) |
| Ciclo de execução de uma demanda | [`docs/AGENT-WORKFLOW.md`](docs/AGENT-WORKFLOW.md) |
| Formato e numeração de PRD | [`docs/PRD-STANDARD.md`](docs/PRD-STANDARD.md) |
| UI, estados e evidência visual | [`docs/UI-SCREEN-CONTRACT.md`](docs/UI-SCREEN-CONTRACT.md) |
| Banco, migrations e seeds | [`docs/OPERACAO-BANCO-SEEDS.md`](docs/OPERACAO-BANCO-SEEDS.md) |
| Deploy Render e Supabase | [`docs/DEPLOY-RENDER-SUPABASE.md`](docs/DEPLOY-RENDER-SUPABASE.md) |
| Roteiro de preenchimento para teste manual | [`docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`](docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md) |
| Diferenças entre Claude, Codex e Cursor | [`docs/PLATFORM-ADAPTERS.md`](docs/PLATFORM-ADAPTERS.md) |
| Índice e próximo número de PRD | [`docs/prd/README.md`](docs/prd/README.md) |

## 6. Comandos locais

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py check_database_connection
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe scripts\build_prd_index.py --check
.\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
.\.venv\Scripts\python.exe -m pip check
```

Comando local necessário à entrega está autorizado: teste, ORM local,
`makemigrations`, `migrate`, seeds, reset local e criação de admin. Registrar
comando e resultado.

Pareamento direto com o operador acontece na branch `stage`; `push` nela
dispara o Auto-Deploy do Render. Trabalho autônomo extenso de agente — a
implementação de uma PRD inteira, não uma correção pontual em conversa direta
— vive em `developer`: local, auditado e testado antes de virar Pull Request
`developer → stage`, cujo merge é sempre humano. `main` recebe somente
promoção manual para produção. Commit e `git push` **não** são feitos por
agente sem ordem explícita do operador — `push` em `stage` ou `main` é ação
irreversível fora do repositório (`docs/AGENT-WORKFLOW.md` §7). Nenhum agente
mescla em `stage` ou `main`, nem faz force push.

O inventário completo dos comandos de operação, com as guardas de cada um, está
em [`docs/OPERACAO-BANCO-SEEDS.md`](docs/OPERACAO-BANCO-SEEDS.md). O ciclo
destrutivo automatizado é `/reset-local`.

## 7. Banco e migrations

- O projeto adota uma única migration vigente,
  `system/migrations/0001_initial.py`.
- Não criar migration incremental por padrão.
- Mudança de schema local pode regenerar a baseline quando o objetivo pedir
  primeira carga ou reconstrução.
- Testes Django usam banco de teste isolado e não exigem apagar `db.sqlite3`.
- A política normativa e o ciclo de reconstrução estão somente em
  `docs/OPERACAO-BANCO-SEEDS.md`.
- Reset total de produção é deliberadamente protegido e nunca entra no Build
  Command.

## 8. Seeds

Dado de negócio nunca é carregado implicitamente por migration ou Build
Command — só por seed explícita. Cada seed é independente; nenhuma chama outra.

| Comando | Papel |
|---|---|
| `create_admin_superuser` | cria o superusuário a partir de `ADMIN_SUPERUSER_*` |
| `seed_system_initial_person_type` | tipos de pessoa |
| `seed_system_initial_belt_ranks` | faixas |
| `seed_system_initial_ibjjf_age_categories` | categorias de idade IBJJF |
| `seed_system_initial_graduation_rules` | regras de graduação |
| `seed_system_initial_class_categories` | categorias de turma |
| `seed_system_initial_teacher` | professores (`SEED_INITIAL_TEACHER_PASSWORD`) |
| `seed_system_initial_class_catalog` | catálogo de turmas |
| `seed_system_initial_teacher_payroll_configs` | configuração de repasse |
| `seed_system_initial_administrative` | administrativo (`SEED_INITIAL_ADMINISTRATIVE_PASSWORD`) |
| `seed_system_initial_product_categories`, `seed_system_initial_product_catalog` | loja |
| `seed_system_initial_subscription_plans`, `_values`, `seed_system_initial_plan_tiers`, `seed_system_initial_plan_prices` | planos e preços |
| `seed_system_initial_coupons`, `seed_system_initial_holidays` | cupons e feriados |
| `seed_system_initial_test_*` | dado fictício de demonstração (`SEED_TEST_PORTAL_PASSWORD`) |
| `clear_test_data` | remove o dado fictício |

A ordem canônica, com as 21 seeds de referência na sequência correta, é a de
`docs/OPERACAO-BANCO-SEEDS.md`. Invocar `/reset-local` é a autorização
explícita para executar as seeds do ciclo.

## 9. Ambientes

| Arquivo | Uso | `DJANGO_ENVIRONMENT` | Banco |
|---|---|---|---|
| `.env` | local | `local` | SQLite `db.sqlite3` |
| `.env.hg` | homologação | `hg` | PostgreSQL Supabase |
| `.env.prod` | produção | `prod` | PostgreSQL Supabase |
| `.env.example` | contrato versionado | — | — |

Os quatro declaram o mesmo conjunto de chaves. Os arquivos reais são privados e
ignorados pelo Git; os recursos Supabase e Render são provisionados pelo
operador. `DJANGO_ENV_FILE` seleciona o ambiente; no Render as variáveis ficam
no Dashboard e não existe `.env` no deploy.

`SITE_BASE_URL` gera os retornos públicos usados pelos gateways.

## 10. UI e validação

Mudança que toca template, CSS, JavaScript ou fluxo visual apresenta
hierarquia, wireframe e estados antes do código, e só fecha com a rota real
aberta em desktop e mobile, nos dois temas, com console limpo e screenshot
registrado. O contrato está em
[`docs/UI-SCREEN-CONTRACT.md`](docs/UI-SCREEN-CONTRACT.md); o roteiro rápido é
`/validar-tela <rota>`.

Rota interna é validada com a conta do papel que ela atende, não com a primeira
disponível: a home é única e o conteúdo muda por permissão.

"Implementado" não significa "validado": sem execução observável, o item vai
para `Pending` na PRD.

## 11. Referências

- [README.md](README.md) — visão geral e setup;
- [AGENTS.md](AGENTS.md) — protocolo de agente;
- [docs/AGENT-WORKFLOW.md](docs/AGENT-WORKFLOW.md) — ciclo de execução;
- [docs/PRD-STANDARD.md](docs/PRD-STANDARD.md) — formato padrão de PRD;
- [docs/UI-SCREEN-CONTRACT.md](docs/UI-SCREEN-CONTRACT.md) — contrato visual;
- [docs/OPERACAO-BANCO-SEEDS.md](docs/OPERACAO-BANCO-SEEDS.md) — banco e seeds;
- [docs/DEPLOY-RENDER-SUPABASE.md](docs/DEPLOY-RENDER-SUPABASE.md) — deploy;
- [docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md](docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md) — roteiro de teste manual e pagamentos;
- [docs/PLATFORM-ADAPTERS.md](docs/PLATFORM-ADAPTERS.md) — Claude, Codex e
  Cursor;
- [docs/prd/README.md](docs/prd/README.md) — índice canônico das PRDs e próximo
  número livre;
- [docs/prd/](docs/prd/) — todas as PRDs numeradas, uma por mudança relevante;
- `obsidian/projetos/conhecimento-lvjiujitsu.md` — conhecimento do produto: por que
  cada decisão é a que é e o que morde. Fora do repositório, e é onde a
  documentação de contexto vive;
- `obsidian/projetos/comandos-powershell-lvjiujitsu.md` — runbook operacional.

## 12. Cadastro público

Fonte principal: `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`.
Guias por perfil: `docs/wizard-step-plan-aluno-titular.md`,
`docs/wizard-step-plan-aluno-com-dependente.md` e
`docs/wizard-step-plan-responsavel-com-aluno.md`.

Fluxo obrigatório:

1. selecionar perfil e preencher dados;
2. selecionar plano;
3. pagar mensalidade;
4. retornar ao wizard com pagamento confirmado;
5. pagar ou pular materiais;
6. revisar;
7. finalizar;
8. somente então criar `Person`, `PortalAccount`, relações, turmas e acesso.

Antes da finalização, o estado pertence a `PreRegistration`. Nenhum registro
definitivo é criado até o passo 8.

## 13. Pagamentos

- Asaas: PIX, cartão, webhooks e repasses.
- Stripe: assinatura recorrente, checkout e webhooks.
- Configuração vem de settings e do arquivo de ambiente.
- `SITE_BASE_URL` gera os retornos públicos.
- O fluxo Asaas local exige túnel HTTPS válido e domínio aceito pelo provedor.
- O fluxo Stripe local pode exigir Stripe CLI e secret temporário.
- O browser interno opera na URL local canônica; callbacks externos usam a URL
  pública configurada.
- Fluxo externo pode exigir Chrome com sessão, túnel ou painel do gateway.
- Redirect do browser, webhook server-to-server e confirmação no banco são três
  coisas distintas e são verificados separadamente.
- **Não simular pagamento por inferência nem declarar confirmação sem evidência
  do gateway e do ORM.**
- Detalhes, simulações e limitações estão em
  `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e em
  `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`.

## 14. Graduação, planos e repasses

- Graduação segue as regras de `seed_system_initial_graduation_rules` e as
  categorias IBJJF; tempo de faixa e presença são entrada, não decisão manual.
- Plano tem tier e preço próprios; preço de família e de veterano derivam de
  configuração, não de valor digitado na tela.
- Repasse de professor deriva de `seed_system_initial_teacher_payroll_configs`;
  ativação e período de retenção são configuráveis por ambiente.
