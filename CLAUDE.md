# CLAUDE.md

@AGENTS.md

Contexto factual do LV Jiu Jitsu. Procedimentos de agente — como conduzir uma
mudança, quando criar PRD, como validar — pertencem ao `AGENTS.md`, às notas do
vault e às skills de ciclo em `.agents/skills/`; este arquivo só descreve o que
o projeto é e como operá-lo.

As onze seções são o núcleo factual e esgotam este arquivo. Regra de negócio,
detalhe de produto, integração externa, superfície e fluxo de tela vivem no
vault, nunca aqui.

**A documentação de contrato e de operação vive fora do repositório**, no vault
Obsidian em `C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\`, cujo
índice é `lvjiujitsu.md`. Este arquivo é o fato da plataforma; a §5 lista quem é
dono de cada assunto. A documentação raiz fica em `CLAUDE.md`, `AGENTS.md`,
`README.md` e `docs/prd/`; as ferramentas mantêm suas instruções adjacentes.

## 1. Natureza do projeto

- O LV Jiu Jitsu é um MVP descartável. Local, homologação e produção não contêm dado
  real de negócio.
- Produção é uma simulação recriável por `migrate` e pela execução explícita das
  seeds; não é a fonte de um histórico.
- É essa propriedade — e só ela — que autoriza a baseline única de migration, o
  ciclo destrutivo local sem pergunta e o reset remoto de schema descrito em
  `obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`. Sem ela,
  nenhuma dessas operações seria aceitável.
- Segredo operacional continua sendo tratado como secreto e nunca é impresso em
  saída, log ou PRD, mesmo quando a credencial for descartável. Ao ler arquivo
  de ambiente, reportar nomes de chave, não valores.
- **Toda credencial deste projeto é descartável**, gratuita e substituível:
  nenhuma protege dado real de negócio, em nenhum dos três ambientes. Disso
  decorre o regime, que vale para chave de API, token de serviço externo e senha
  de seed:
  - **continua obrigatório**: não versionar, não escrever em arquivo do
    repositório, não imprimir valor em saída, log, PRD ou evidência;
  - **não se aplica**: exigir rotação, tratar exposição como incidente, abrir
    alerta ou condicionar a entrega a uma troca de chave. Credencial que o
    operador fornece na conversa é usada por variável de ambiente da sessão, sem
    alarme e sem interromper o trabalho.
  - A troca de chaves acontece **uma vez**, ao fim do escopo, quando um ambiente
    novo subir com credenciais novas. Até lá, propor rotação é ruído, não
    segurança.
- **Condição de revogação:** no dia em que existir dado real cujo histórico
  importe, esta seção é revogada. A partir daí, reset remoto volta a exigir
  backup e plano de restauração, e migrations passam a preservar o histórico em
  vez de serem recriadas.

### O que não existe neste projeto

Declarado para que nenhum agente proponha, assuma ou "restaure" o que nunca
houve:

- sem ambiente além de `local`, `hg` e `prod`;
- sem `render.yaml`, `build.sh` ou Dockerfile — o Render é configurado pelo
  Dashboard;
- sem `requirements-dev.txt`: há um único arquivo de dependências;
- sem serviço externo além dos declarados na nota de conhecimento do produto.

O inventário do que este produto não tem por decisão de domínio vive em
`obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md`.

## 2. Produto

| Campo | Valor |
|---|---|
| Nome | LV Jiu Jitsu |
| Objetivo | `obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md` |
| App de domínio | `system/` |
| Projeto Django | `lvjiujitsu/` |
| Banco local | SQLite em `db.sqlite3` |
| HG e produção | PostgreSQL Supabase via `DATABASE_URL` |
| Deploy | Render, configurado pelo Dashboard |
| Ambiente padrão | Windows, PowerShell e `.venv` |
| Idioma da UI | Português pt-BR |
| URL local canônica | `http://localhost:8000` |

O trabalho diário acontece em `/`, entrada única que resolve o papel pela sessão
e serve conteúdo diferente por permissão. O painel do produto **não** usa
`AdminSite`.

`/health/` responde ao health check do Render. O Django Admin técnico
(`/django-admin/`) é isolado e **não** é o painel operacional do produto.

As superfícies, as rotas de entrada, o que cada uma entrega e quem acessa estão
em `obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md`. Os fluxos de tela
estão em `obsidian/projetos/lvjiujitsu/fluxos-tela-lvjiujitsu.md`.

### O teto da plataforma

O LV Jiu Jitsu roda em **plano gratuito nos dois serviços**, e isso não é detalhe de
custo: é a restrição que decide como o código pode ser escrito.

| Serviço | Teto |
|---|---|
| Render Free | 512 MB de RAM, 0.1 CPU, uma instância, spin down após 15 min ocioso, spin up de ~1 min |
| Render Free | **sem shell, sem one-off job, sem background worker, sem cron job** |
| Supabase Free | 500 MB de banco, 5 GB de egress por mês, 60 conexões diretas, pausa após 7 dias ociosos |

A linha que mais restringe é a segunda: **não há para onde mandar trabalho
pesado**. Nenhuma operação longa pode ser "movida para um job" — ela cabe em
requests sucessivos e retomáveis, ou não acontece. O timeout efetivo é o
`--timeout 120` do gunicorn no Start Command.

Disso decorre a regra: **todo trabalho é limitado por lote, nunca por volume
total.** Lentidão é aceitável; trabalho ilimitado dentro de um request não. O
orçamento por classe de rota, os padrões proibidos e o portão automatizado estão
em `obsidian/projetos/lvjiujitsu/performance-plataforma-lvjiujitsu.md`.

## 3. Stack

- Python 3.12.10, Django 5.2.16 LTS, templates server-rendered;
- SQLite local, PostgreSQL (Supabase) em homologação e produção;
- WhiteNoise para estáticos em produção, Gunicorn e Render como Web Service
  Python;
- versões exatas em `requirements.txt`, o único arquivo de dependências;
- as integrações externas deste produto estão em
  `obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md`.

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
| `system/services/` | regra de negócio e escrita transacional |
| `system/selectors/` | leitura reutilizável, fora de views |
| `system/views/` | HTTP fino |
| `system/utils/` | apoio sem estado, sem acesso ao ORM |
| `system/management/commands/` | seeds, checagens de conexão e limpeza de dado de teste |
| `system/tests/` | um arquivo por camada ou funcionalidade |
| `templates/` | apresentação |
| `static/system/` | CSS e JS editáveis |
| `staticfiles/` | saída gerada por `collectstatic`; nunca editar à mão |

Ao alterar asset versionado, atualizar o parâmetro `?v=` da referência.

A responsabilidade de cada camada como protocolo está em `AGENTS.md`. Os módulos
donos de cada assunto neste produto estão em
`obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md`.

## 5. Contratos

Um dono por assunto. Contrato define o exigido; código e testes mostram o
observado. Divergências são reconciliadas explicitamente na mesma mudança.

| Assunto | Documento |
|---|---|
| Protocolo de agente | [`AGENTS.md`](AGENTS.md) |
| Índice da documentação | `obsidian/projetos/lvjiujitsu/lvjiujitsu.md` |
| Ciclo de execução de uma demanda | `obsidian/projetos/lvjiujitsu/ciclo-execucao-lvjiujitsu.md` |
| Formato e numeração de PRD | `obsidian/projetos/lvjiujitsu/padrao-prd-lvjiujitsu.md` |
| UI, estados e evidência visual | `obsidian/projetos/lvjiujitsu/contrato-ui-lvjiujitsu.md` |
| Fluxos de tela | `obsidian/projetos/lvjiujitsu/fluxos-tela-lvjiujitsu.md` |
| Banco, migrations e seeds | `obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md` |
| Deploy Render e Supabase | `obsidian/projetos/lvjiujitsu/deploy-render-supabase-lvjiujitsu.md` |
| Teto da plataforma e orçamento de carga | `obsidian/projetos/lvjiujitsu/performance-plataforma-lvjiujitsu.md` |
| Roteiro de preenchimento para teste manual | `obsidian/projetos/lvjiujitsu/guia-teste-cliente-lvjiujitsu.md` |
| Diferenças entre Claude Code e Codex | `obsidian/projetos/lvjiujitsu/plataformas-agente-lvjiujitsu.md` |
| Conhecimento do produto | `obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md` |
| Runbook operacional dos três ambientes | `obsidian/projetos/lvjiujitsu/comandos-powershell-lvjiujitsu.md` |
| Regra de negócio do produto | `obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md` |
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
.\.venv\Scripts\python.exe manage.py check_environment_parity
.\.venv\Scripts\python.exe manage.py check_schema_parity
.\.venv\Scripts\python.exe clear_migrations.py --check
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe -m pip check
```

Comando local necessário à entrega está autorizado: teste, ORM local,
`makemigrations`, `migrate`, seeds, reset local e criação de admin. Registrar
comando e resultado. Os comandos de operação remota, com as guardas de cada um,
estão em `obsidian/projetos/lvjiujitsu/comandos-powershell-lvjiujitsu.md`.

Pareamento direto com o operador acontece na branch `stage`; `push` nela dispara
o Auto-Deploy do Render. Trabalho autônomo extenso de agente vive em
`developer`: local, auditado e testado antes de virar Pull Request
`developer → stage`, cujo merge é sempre humano. `main` recebe somente promoção
manual para produção. Commit e `git push` **não** são feitos por agente sem
ordem explícita do operador.

## 7. Banco e migrations

- O projeto adota uma única migration vigente,
  `system/migrations/0001_initial.py`.
- Não criar migration incremental por padrão.
- Mudança de schema local pode regenerar a baseline quando o objetivo pedir
  primeira carga ou reconstrução.
- Testes Django usam banco de teste isolado e não exigem apagar `db.sqlite3`.
- A política normativa e o ciclo de reconstrução estão somente em
  `obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`.
- Reset total de produção é deliberadamente protegido e nunca entra no Build
  Command.
- **Limpeza remota exige perguntar ao operador antes**, em HG e em produção,
  mesmo com a tarefa já autorizada de forma geral.

## 8. Seeds

Dado de negócio nunca é carregado por migration. Produção usa seed explícita;
homologação pode ser reconstruída com o cenário fictício em cada Build Command
aprovado. Cada seed é independente; nenhuma chama outra.

`create_admin_superuser` cria o superusuário a partir de `ADMIN_SUPERUSER_*` e
`clear_test_data` remove o dado fictício. As seeds de domínio deste produto, a
ordem canônica de execução e as variáveis que cada uma exige estão em
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`.

Executar o ciclo destrutivo local é a autorização explícita para rodar as seeds
na sequência.

## 9. Ambientes

| Arquivo | Uso | `DJANGO_ENVIRONMENT` | Banco |
|---|---|---|---|
| `.env` | local | `local` | SQLite `db.sqlite3` |
| `.env.hg` | homologação | `hg` | PostgreSQL Supabase |
| `.env.prod` | produção | `prod` | PostgreSQL Supabase |
| `.env.example` | contrato versionado | — | — |

Os quatro declaram o mesmo conjunto de chaves, conferido por
`manage.py check_environment_parity`, que imprime nome de chave e nunca valor.

**Os três arquivos reais moram fora do repositório**, no diretório compartilhado
do operador. Existe uma cópia só: `settings.py` procura primeiro em `BASE_DIR` e
depois no compartilhado, então nenhum comando do runbook muda e não há duplicata
para divergir.

**O arquivo do repositório vence o do compartilhado**, e essa ordem é
deliberada: máquina nova ou ambiente sem o Drive montado funciona só baixando o
`.env` para a raiz. O reverso é a armadilha — cópia esquecida no checkout
passaria a mandar em silêncio sobre a do Drive.

**Configuração ausente derruba o boot, de propósito.** `load_config` recusa e
diz onde procurou. A exceção é a plataforma: quando `DJANGO_ENVIRONMENT` está no
ambiente do processo, as variáveis do Dashboard bastam e nenhum arquivo é
exigido, que é o caso do Render.

`DJANGO_ENV_FILE` seleciona o ambiente; no Render as variáveis ficam no Dashboard
e não existe `.env` no deploy. O significado de cada chave está em
`obsidian/projetos/lvjiujitsu/deploy-render-supabase-lvjiujitsu.md`.

## 10. UI e validação

Mudança que toca template, CSS, JavaScript ou fluxo visual apresenta hierarquia,
wireframe e estados antes do código, e só fecha com a rota real aberta em
desktop e mobile, nos dois temas, com console limpo e screenshot registrado. O
contrato está em `obsidian/projetos/lvjiujitsu/contrato-ui-lvjiujitsu.md`; o roteiro
rápido é `/validar-tela <rota>`.

Rota interna é validada com a conta do papel que ela atende, não com a primeira
disponível: a entrada é única e o conteúdo muda por permissão.

**A interface é do produto, nunca do navegador.** Lista de valores, sugestão,
confirmação e aviso são HTML, CSS e JavaScript deste projeto, com os tokens do
tema. `<datalist>`, `alert`, `confirm`, `prompt` e qualquer widget que o agente
de usuário desenhe por conta própria estão proibidos. A exceção é o que só o
dispositivo entrega, como teclado virtual e seletor de arquivo. Componente
equivalente já existente é reaproveitado.

"Implementado" não significa "validado": sem execução observável, o item vai
para `Pending` na PRD.

## 11. Referências

No repositório:

- [README.md](README.md) — visão geral e setup;
- [AGENTS.md](AGENTS.md) — protocolo de agente;
- [docs/prd/README.md](docs/prd/README.md) — índice canônico das PRDs e próximo
  número livre;
- [docs/prd/](docs/prd/) — todas as PRDs numeradas, uma por mudança relevante.

No vault Obsidian, em `C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\`:

- `lvjiujitsu.md` — índice da documentação;
- `ciclo-execucao-lvjiujitsu.md` — ciclo de execução;
- `padrao-prd-lvjiujitsu.md` — formato padrão de PRD;
- `contrato-ui-lvjiujitsu.md` — contrato visual;
- `fluxos-tela-lvjiujitsu.md` — fluxos de tela;
- `operacao-banco-seeds-lvjiujitsu.md` — banco, migrations e seeds;
- `deploy-render-supabase-lvjiujitsu.md` — deploy;
- `performance-plataforma-lvjiujitsu.md` — teto da plataforma e orçamento de carga;
- `guia-teste-cliente-lvjiujitsu.md` — roteiro de teste manual;
- `plataformas-agente-lvjiujitsu.md` — Claude Code e Codex;
- `conhecimento-lvjiujitsu.md` — por que cada decisão é a que é, e o que morde;
- `comandos-powershell-lvjiujitsu.md` — runbook operacional dos três ambientes;
- `regras-negocio-lvjiujitsu.md` — regra de negócio específica do produto.
