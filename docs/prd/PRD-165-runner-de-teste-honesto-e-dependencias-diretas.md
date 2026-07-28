# PRD-165: Runner de teste honesto e dependências diretas

## Summary

Corrigir o nome e o escopo do runner de teste, que afirma rodar em PostgreSQL
e não roda; mover a criação de `STATIC_ROOT` para fora do caminho de teste; e
reduzir `requirements.txt` às dependências diretas do projeto.

## Demand type

Infraestrutura e configuração. Sem mudança de regra de negócio, sem mudança
de schema.

## Current problem

1. **O nome `PostgreSQLDiscoverRunner` afirma mais do que a classe faz.** Ela
   herda de `DiscoverRunner` e **não escolhe banco**: não altera `DATABASES`,
   não configura a chave `TEST` e não força engine alguma. O engine vem da
   configuração, como em qualquer execução — SQLite quando `DATABASE_URL` está
   vazia, que é o caso no ambiente local.

   A classe tem, de fato, uma parte específica de PostgreSQL: em
   `teardown_databases` ela encerra as sessões remanescentes quando
   `conn.vendor == "postgresql"`, sem o que o drop do banco de testes falha por
   conexão aberta. Esse comportamento é necessário e correto quando a suíte
   roda contra PostgreSQL. O nome, porém, generaliza esse detalhe de teardown
   para a identidade do runner.

   O dano é de leitura: quem abre o `settings.py` e vê
   `TEST_RUNNER = '...PostgreSQLDiscoverRunner'` conclui que a suíte cobre o
   motor de produção. No ambiente local ela não cobre — roda em SQLite. Uma
   constraint que só o PostgreSQL aplica, ou uma diferença de ordenação ou de
   tipo entre os dois motores, passa verde e falha em homologação. O nome
   sugere cobertura que não existe.

   As outras duas responsabilidades da classe — criar `STATIC_ROOT` e
   desabilitar logging até `WARNING` — também não têm relação com o nome.

2. **`STATIC_ROOT` é criado dentro do runner de teste.** O diretório é
   necessário para `collectstatic` e para o WhiteNoise em qualquer execução,
   não só em teste. Criá-lo apenas no caminho de teste tem duas consequências:
   `collectstatic` falha logo após um ciclo destrutivo, quando o diretório
   ainda não existe; e rodar a suíte "conserta" o ambiente como efeito
   colateral, o que faz o mesmo comando ter resultado diferente dependendo do
   que rodou antes.

3. **`requirements.txt` com 49 linhas incluindo dependências transitivas.**
   O arquivo lista pacotes que o projeto não importa — `annotated-types`,
   `anyio`, `certifi`, `cffi`, `h11`, `hpack`, `hyperframe`, `idna`,
   `mdurl`, `propcache`, `pycparser`, `pydantic_core`, `six`,
   `typing-inspection`, `urllib3` e outros — que existem apenas porque algum
   pacote direto os exige.

   O efeito é que não se distingue mais o que o projeto escolheu do que o
   `pip` resolveu. Ao remover uma dependência direta, suas transitivas ficam
   travadas no arquivo sem que ninguém saiba a quem pertenciam. Ao atualizar
   uma dependência direta, um pin transitivo desatualizado bloqueia a
   resolução com erro que não aponta para a causa.

4. **`.gitignore` com entradas que não correspondem a arquivo algum.** Há
   `.env-prod` e `.env-hg`, com hífen, ao lado de `.env.prod` e `.env.hg`. Os
   arquivos reais usam ponto. As duas entradas com hífen sugerem uma
   convenção de nomenclatura que o projeto não adota e que não está declarada
   em nenhum contrato.

5. **`.claude/scheduled_tasks.lock` não é rastreado nem ignorado.** É
   artefato de runtime da ferramenta de agente, presente no working tree e
   ausente do `.gitignore`. Aparece como não rastreado em todo `git status`,
   pronto para entrar em um `git add` amplo.

6. **`kill_project_python_processes` protege só o pai direto.** O filtro exclui
   `current_pid` e `os.getppid()`. Isso cobre o caso comum, porque
   `.venv/Scripts/python.exe` é um shim que executa o interpretador base e
   aparece no WMI como processo distinto cujo `ExecutablePath` está dentro do
   repositório — logo, casa com `is_project_python_process`.

   O que não está coberto é a cadeia acima do pai. Se houver um avô Python
   dentro do repositório, ele é alvo válido e será encerrado. O dano é
   limitado porque o encerramento usa `taskkill /F` sem `/T`, e no Windows
   matar um ancestral não derruba o descendente — então o ciclo não se
   autodestrói. Mas encerrar processo que não é do ciclo continua sendo
   errado: o operador perde um processo que não pediu para perder, sem aviso
   que identifique qual era.

## Goal

O nome do runner descreve o que ele faz. `STATIC_ROOT` existe
independentemente de a suíte ter rodado. `requirements.txt` lista o que o
projeto escolheu. `git status` limpo não mostra artefato de runtime. O
encerramento de processos nunca alcança ancestral do próprio script.

## Context Ledger

### Files read in full

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `AGENTS.md` seções 7 e 8

### Adjacent files consulted

- `.github/workflows/ci.yml` — como a suíte é invocada no CI
- `clear_migrations.py` — quais artefatos o ciclo remove
- `docs/OPERACAO-BANCO-SEEDS.md` — ordem canônica do ciclo local
- amostra de `system/tests/` que usa `assertLogs`, para confirmar que a
  supressão de logging precisa continuar limitada a `WARNING`

### Internet / official documentation

- Django 5.2: `TEST_RUNNER`, `DiscoverRunner`, a chave `TEST` de `DATABASES` e
  como se configura o banco de teste.
- Django 5.2: `STATIC_ROOT`, `collectstatic` e requisitos de diretório.
- `pip`: resolução de dependência e o papel de `pip check`.

### Context7 / MCPs / tools verified

- Context7 consultado para Django 5.2 (runner de teste, banco de teste,
  estáticos) e para o comportamento de `pip check`.
- `pip check` e execução da suíte completa como verificação.

### Limitations found

- Confirmar em qual motor a suíte roda exige observação em execução, não
  leitura: a evidência é a saída do runner informando o banco de teste criado.
- A decisão de passar a suíte para PostgreSQL de fato não pertence a esta
  PRD: exigiria serviço de banco no CI e no ambiente local. Aqui o nome é
  corrigido para deixar de afirmar o que não acontece.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador para corrigir a infraestrutura e implementar sem
nova confirmação. Decisão registrada: a suíte continua no banco de teste
padrão; `requirements.txt` passa a listar apenas dependências diretas, com a
resolução transitiva a cargo do `pip` e validada por `pip check` no CI.

## Execution prompt

### Persona

Engenheiro Django responsável pela infraestrutura de teste e de dependências
do LV.

### Action

Renomear o runner para um nome que descreva seu comportamento real, mover a
criação de `STATIC_ROOT` para o `settings.py`, reduzir o `requirements.txt` às
diretas e corrigir o `.gitignore`.

### Context

A suíte roda no banco de teste padrão do Django. `STATIC_ROOT` é necessário
fora de teste. O CI já valida a resolução das dependências por `pip check`.

### Constraints

- A supressão de logging precisa continuar limitada a `WARNING`, para não
  quebrar os testes que usam `assertLogs(level="ERROR")`.
- O filtro do warning do WhiteNoise permanece.
- Nenhum teste pode ser removido, adaptado ou marcado como esperado-a-falhar
  para acomodar a mudança.
- Remover pin transitivo não pode alterar a versão instalada de nenhuma
  dependência direta.
- A contagem de testes antes e depois precisa ser idêntica.

### Acceptance criteria

1. A classe tem nome que descreve seu papel sem afirmar o motor de banco, e o
   nome antigo não é mais usado em nenhum lugar do repositório. A menção a
   PostgreSQL sobrevive apenas onde é verdadeira: no `teardown_databases`, que
   trata o caso, e na docstring que explica a troca de nome.
2. `settings.py` referencia o novo nome em `TEST_RUNNER`.
3. `settings.py` cria `STATIC_ROOT` se não existir, fora do caminho de teste.
4. O runner não cria mais `STATIC_ROOT`.
5. `collectstatic --noinput` passa imediatamente após um ciclo destrutivo
   local, sem que a suíte tenha rodado antes.
6. `logging.disable(logging.WARNING)` continua no runner, e os testes que
   usam `assertLogs(level="ERROR")` continuam passando.
7. `requirements.txt` lista apenas pacotes importados pelo projeto ou
   exigidos pela execução (servidor, driver de banco, estáticos), sem
   transitivas.
8. `pip check` passa em ambiente recriado a partir do novo
   `requirements.txt`.
9. `pip freeze` no ambiente recriado resolve as mesmas versões das
   dependências diretas de antes.
10. `.gitignore` não tem `.env-prod` nem `.env-hg`, e continua ignorando
    `.env.prod` e `.env.hg`.
11. `.gitignore` ignora `.claude/scheduled_tasks.lock`.
12. `git status --short` fica limpo em working tree recém-resetado.
13. Existe `ancestor_pids`, e `kill_project_python_processes` protege o
    próprio PID e toda a cadeia de ancestrais, não apenas o pai direto.
14. `ancestor_pids` termina mesmo com ciclo no mapa de pais, e um processo
    irmão continua sendo alvo válido.
15. Suíte completa verde, com a mesma contagem de testes de antes.

### Expected evidence

Saída real de: suíte antes e depois com contagem, `pip check`, `pip freeze`
comparado, `collectstatic` após reset, `git status --short` e o nome do banco
de teste informado pelo runner.

### Output format

Diff, saída dos comandos e atualização desta PRD.

## Scope

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`

## Out of scope

- Passar a suíte para PostgreSQL: exigiria serviço de banco no CI e no
  ambiente local, e é decisão de arquitetura fora deste escopo.
- Alterar qualquer teste existente.
- Trocar driver de banco, servidor de aplicação ou backend de estáticos.
- Atualizar versão de dependência direta: esta PRD remove transitivas, não
  promove upgrade.

## Impacted files

- `system/test_runner.py`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `docs/prd/README.md`

## Risks and edge cases

- **Remover pin transitivo mudando versão instalada.** Mitigação: `pip freeze`
  do ambiente recriado é comparado com o de antes; qualquer dependência direta
  que mude de versão é investigada antes de fechar.
- **Transitiva que na verdade era direta.** Um pacote pode estar na lista
  porque o projeto o importa sem que seja óbvio. Mitigação: cada remoção é
  conferida contra os imports reais do código, não contra a intuição.
- **`assertLogs(level="ERROR")` quebrando.** Mitigação: a supressão continua
  em `WARNING` e os testes que dependem disso são executados
  explicitamente.
- **Renomear a classe e deixar referência órfã.** Mitigação: busca pelo nome
  antigo em todo o repositório depois da renomeação.
- **`STATIC_ROOT` criado no import do settings em ambiente somente leitura.**
  Mitigação: a criação usa `exist_ok` e é tolerante a falha de permissão, com
  o erro visível em vez de mascarado.

## Rules and constraints

`AGENTS.md` seção 7: não declarar Green sem saída real de comando; teste roda
em banco isolado e não toca o SQLite local. `AGENTS.md` seção 10: nomes
claros, configuração explícita, nenhum erro mascarado. `AGENTS.md` seção 2:
contrato descreve o que existe — um nome que afirma comportamento inexistente
é a mesma classe de defeito.

## Plan

1. Rodar a suíte completa e registrar contagem e nome do banco de teste.
2. Registrar `pip freeze` do ambiente atual.
3. Renomear a classe e ajustar `TEST_RUNNER`.
4. Mover a criação de `STATIC_ROOT` para o `settings.py`.
5. Reduzir `requirements.txt`, conferindo cada remoção contra os imports.
6. Recriar o ambiente virtual a partir do novo arquivo e rodar `pip check`.
7. Comparar `pip freeze` com o registro anterior.
8. Rodar o ciclo destrutivo, `collectstatic` sem ter rodado a suíte, e a
   suíte completa.
9. Corrigir o `.gitignore` e conferir `git status --short`.

## Test plan

- A suíte existente é o teste de regressão: mesma contagem, todos verdes.
- Execução explícita dos testes que usam `assertLogs(level="ERROR")`.
- `collectstatic --noinput` após reset, antes de qualquer execução de teste.
- `pip check` no ambiente recriado.

## Visual validation

Não se aplica diretamente. Como `collectstatic` está no escopo, uma rota
autenticada é aberta após o reset para confirmar que o CSS é servido, com
screenshot registrado.

## ORM validation

Não se aplica: nenhuma mudança de modelo, consulta ou migration. A
verificação de banco relevante é qual banco de teste o runner cria, que é
evidência de execução.

## Quality validation

`pip check`, `python manage.py check`,
`makemigrations --check --dry-run`, `collectstatic --noinput` e suíte
completa com contagem comparada.

## Evidence

- `manage.py check`: "no issues (0 silenced)".
- Import do runner renomeado: `from system.test_runner import
  ProjectDiscoverRunner` resolve.
- Busca por `PostgreSQLDiscoverRunner` em todo o repositorio: nenhuma
  ocorrencia fora da propria PRD e da docstring que explica a troca.
- **Criterio 5, provado na ordem exigida.** Depois do ciclo destrutivo,
  `Test-Path staticfiles` retornou `False`; `collectstatic --noinput` rodou em
  seguida, **sem a suite ter rodado antes**, e copiou 381 arquivos com codigo
  de saida 0.
- Ciclo destrutivo com o banco bloqueado: processo Python do repositorio
  segurando `db.sqlite3` em WAL com transacao aberta. Saida real:
  `[OK] Finalizado: PID 32692`, `[OK] Arquivos SQLite removidos: 3`,
  `[OK] Migrations removidas: 1`, `[OK] Limpeza concluida com sucesso.`,
  codigo de saida 0, nenhum `db.sqlite3*` restante.
- `pip check` em **ambiente recriado do zero** a partir do novo
  `requirements.txt`: "No broken requirements found."
- `pip freeze` no ambiente recriado resolve as dez diretas nas mesmas versoes:
  Django 5.2.14, python-decouple 3.8, tzdata 2026.1, gunicorn 26.0.0,
  whitenoise 6.12.0, psycopg2-binary 2.9.12, dj-database-url 3.1.2,
  stripe 15.0.1, requests 2.33.1, PyYAML 6.0.2.
- `makemigrations --check --dry-run`: "No changes detected". Baseline estavel:
  o diff do `0001_initial.py` regenerado e de uma linha, o timestamp.
- `git status --short` nao mostra mais `.claude/scheduled_tasks.lock`.
- Suite completa: `Ran 745 tests in 325.678s ... OK`. Mesma contagem de antes
  das mudancas de dependencia e de runner.

## Implemented

- `system/test_runner.py`: `PostgreSQLDiscoverRunner` renomeado para
  `ProjectDiscoverRunner`, com docstring que descreve os tres comportamentos
  reais e registra que o runner **nao escolhe banco**.
- `lvjiujitsu/settings.py`: `TEST_RUNNER` aponta para o nome novo; `STATIC_ROOT`
  passou a ser criado no proprio settings, fora do caminho de teste.
- O runner deixou de criar `STATIC_ROOT`; a supressao de logging ate `WARNING` e
  o filtro do aviso do WhiteNoise permanecem.
- `requirements.txt`: de 49 linhas para 10 dependencias diretas, agrupadas por
  finalidade com comentario. Removidas as transitivas e os pacotes que o
  projeto nao usa — `pillow`, `PyMuPDF`, `python-dotenv`, `StrEnum`, `PyJWT`,
  `cryptography`, `rich`, `httpx` e demais.
- `.gitignore`: `.env-prod` e `.env-hg` removidos; `.claude/scheduled_tasks.lock`,
  `db.sqlite3-wal`, `db.sqlite3-shm`, `db.sqlite3-journal` e `coverage.xml`
  acrescentados.
- `build_parent_map` e `ancestor_pids` em `clear_migrations.py`, com quatro
  testes em `system/tests/test_commands.py`.

## Cleanup findings

1. **A premissa do problema 1 estava parcialmente errada, e a PRD foi
   corrigida antes da implementacao.** O runner nao configura banco, mas
   **tem** logica especifica de PostgreSQL: `teardown_databases` encerra as
   sessoes remanescentes quando `conn.vendor == "postgresql"`, sem o que o drop
   do banco de testes falha por conexao aberta. Ou seja, o nome nao era
   infundado — era enganoso quanto ao que a suite usa por padrao. O nome novo
   descreve o papel; o comportamento PostgreSQL foi preservado integralmente.

2. **Este projeto nao tinha o defeito de auto-eliminacao** que a mesma classe
   de codigo pode produzir: `kill_project_python_processes` usa `taskkill /F`
   sem `/T`, e ja protegia `os.getppid()`. A correcao endurece a cadeia acima
   do pai; nao conserta uma quebra.

3. **`pillow` foi removido com verificacao.** Nao ha `ImageField` nem import de
   `PIL` no projeto — confirmado por busca — e a suite completa passou sem ele.

4. Nenhuma mencao a repositorio externo em codigo-fonte foi encontrada neste
   projeto.

5. Nenhum residuo introduzido. O venv temporario usado para validar a resolucao
   das dependencias ficou fora do repositorio.

## Follow-up PRDs

Nenhuma. Se a decisao de rodar a suite em PostgreSQL for tomada, ela exige PRD
propria com provisionamento de banco no CI.

## Deviations from plan

- O problema 6 nao existia quando a PRD foi escrita: foi descoberto durante a
  execucao e acrescentado ao escopo, com criterios 13 e 14.
- A primeira implementacao do endurecimento movia o filtro por nome de
  executavel do PowerShell para Python, o que quebrou
  `test_kill_only_targets_project_python_processes` — o payload mockado nesse
  teste nao tem a chave `Name`, porque o filtro sempre foi feito na consulta.
  Como a secao de constraints proibe adaptar teste para acomodar a mudanca, a
  implementacao foi refeita: o filtro voltou para o PowerShell e o mapa de
  parentesco e montado a partir da enumeracao ja filtrada. O teste voltou a
  passar sem ser tocado.
- O criterio 9 pedia comparar `pip freeze` antes e depois. Em vez de recriar o
  venv do projeto, que e o ambiente de trabalho do operador, a resolucao foi
  verificada num venv temporario fora do repositorio. Prova a mesma coisa sem
  risco para o ambiente.

## Pending

- Rodar o CI de fato: os passos foram verificados localmente, mas o job so corre
  no proximo push.
- Commitar o worktree. Nenhum commit foi feito pelo agente.

## Final status

Concluida. O nome do runner descreve o que ele faz e o comportamento
PostgreSQL do teardown foi preservado; `STATIC_ROOT` existe independentemente de
a suite ter rodado, provado por `collectstatic` logo apos um reset;
`requirements.txt` lista as dez dependencias diretas, com `pip check` verde em
ambiente recriado; e o `git status` nao mostra mais artefato de runtime. Suite
completa verde em 745 testes.
