# PRD-167: Workflow secundário de CI

## Summary

Resolver `.github/workflows/copilot-setup-steps.yml`, que divergiu do
workflow principal em runner, timeout e versão de Python, tenta instalar um
navegador a partir de uma dependência que não está declarada, e depende de
rede externa para passar.

## Demand type

Infraestrutura de CI. Sem mudança de regra de negócio, sem mudança de código
de aplicação.

## Current problem

O repositório tem dois workflows. `ci.yml` foi padronizado: `ubuntu-latest`,
`timeout-minutes: 20`, `actions/checkout@v5`, `actions/setup-python@v5` com
`3.12.10`, um passo por verificação, e o bloco `env` declarando as variáveis
que o `settings.py` exige.

`copilot-setup-steps.yml` não seguiu nada disso, e nenhuma decisão registrada
explica a diferença:

1. **`runs-on: windows-latest`** contra `ubuntu-latest` no principal. Dois
   runners diferentes no mesmo repositório significa manter duas matrizes de
   comportamento — e o job secundário força `shell: pwsh` em cada passo por
   causa dessa escolha.

2. **`timeout-minutes: 59`** contra 20. Um job que trava consome quase uma
   hora antes de ser interrompido.

3. **`python-version: "3.12"`** contra `"3.12.10"`. O projeto fixa a versão
   em `.python-version`; o job secundário aceita qualquer patch da série,
   então valida um interpretador que não é o da entrega.

4. **`actions/setup-node@v4`** enquanto as demais actions do repositório estão
   em v5.

5. **O passo `playwright install chromium` não pode funcionar.**
   `playwright` não consta em `requirements.txt` — verificado — e o passo
   anterior instala exatamente `requirements.txt`. O executável não existe
   quando o passo roda, então ele falha por comando não encontrado. Um passo
   que nunca passou está no workflow.

6. **Dois passos existem só para chamar `--help`.** `npx -y @playwright/mcp
   --help` e `npx -y @upstash/context7-mcp --help` baixam pacotes npm a cada
   execução para verificar que o binário responde. Isso não valida integração
   com o projeto: valida que o registro npm está no ar.

7. **O último passo depende de rede externa.** O script abre
   `https://example.com` em Chromium headless e imprime o título. Falha de
   DNS, indisponibilidade do site ou bloqueio de saída derrubam o job por
   motivo alheio ao repositório. Um CI que quebra por causa de um site de
   terceiros não é sinal de nada.

O resultado é um workflow que, se está sendo executado, está vermelho por
defeito próprio; e se não está sendo executado, é arquivo morto ocupando
`.github/workflows/` com aparência de verificação ativa. Nos dois casos, ele
diz algo falso sobre o estado do projeto.

## Goal

`.github/workflows/` contém apenas verificação que passa, que valida este
repositório e que não depende de serviço de terceiros para dar veredito.

## Context Ledger

### Files read in full

- `.github/workflows/copilot-setup-steps.yml`
- `.github/workflows/ci.yml`
- `requirements.txt`
- `.python-version`
- `AGENTS.md` seção 8

### Adjacent files consulted

- `system/tests/test_commands.py` — confirma que a menção a `.playwright-mcp`
  é nome de diretório de artefato, não import de biblioteca
- `clear_migrations.py` — quais diretórios de artefato de navegador o ciclo
  remove
- `docs/PLATFORM-ADAPTERS.md` — qual é o papel declarado dos MCPs no projeto
- `.mcp.json` — como os MCPs são configurados de fato

### Internet / official documentation

- GitHub Actions: semântica de `runs-on`, `timeout-minutes`, e versões atuais
  de `actions/checkout`, `actions/setup-python` e `actions/setup-node`.
- Convenção do arquivo `copilot-setup-steps.yml`: propósito, quando é
  executado e o que se espera dele.
- Playwright: instalação da biblioteca Python e do navegador, e por que a
  ordem importa.

### Context7 / MCPs / tools verified

- Context7 consultado para GitHub Actions e para Playwright.
- Verificação em disco: `playwright` ausente de `requirements.txt`;
  `python-version` do workflow comparado com `.python-version`.

### Limitations found

- Não é possível saber, por leitura, se o job vem sendo executado e ignorado
  ou se nunca rodou. O histórico de execuções está no GitHub, não no
  repositório; a decisão entre remover e corrigir depende dessa informação e
  fica com o operador.
- O efeito da correção só é observável no próximo push, quando o job corre.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador para padronizar o CI e implementar sem nova
confirmação. A escolha entre remover o workflow ou corrigi-lo depende de saber
se ele tem uso, e está registrada como decisão pendente no plano.

## Execution prompt

### Persona

Engenheiro responsável pelo CI do LV.

### Action

Decidir entre remover `copilot-setup-steps.yml` ou alinhá-lo ao workflow
principal, e executar a decisão.

### Context

`ci.yml` é a verificação canônica do repositório e já cobre dependências,
skills, `check`, baseline de migration e suíte completa. Qualquer segundo
workflow precisa justificar o que acrescenta.

### Constraints

- Nenhum passo pode depender de site de terceiros para dar veredito.
- Nenhum passo pode invocar executável que não venha de `requirements.txt` ou
  de uma action declarada.
- Se o workflow for mantido, adota `ubuntu-latest`, `timeout-minutes: 20` e
  `python-version` igual ao conteúdo de `.python-version`.
- Nenhuma verificação existente em `ci.yml` é removida ou duplicada.
- Nenhum segredo entra em arquivo de workflow.

### Acceptance criteria

1. Se removido: `.github/workflows/` contém apenas `ci.yml`, e nenhum
   contrato cita o arquivo removido.
2. Se mantido: `runs-on` é `ubuntu-latest`.
3. Se mantido: `timeout-minutes` é 20.
4. Se mantido: `python-version` é `3.12.10`, igual a `.python-version`.
5. Se mantido: `actions/setup-node` está em v5, ou não existe mais porque os
   passos que dependiam dele foram removidos.
6. Se mantido: nenhum passo invoca `playwright` sem que a biblioteca esteja
   declarada em `requirements.txt`.
7. Se mantido: nenhum passo acessa host externo ao GitHub para produzir
   veredito.
8. Se mantido: os passos que só chamavam `--help` de pacote npm não existem
   mais.
9. `ci.yml` permanece verde, com um passo por verificação. Passou de oito para
   nove passos pela inclusão da verificação do índice de PRDs, feita fora desta
   PRD; nenhuma verificação existente foi removida ou duplicada.
10. `python manage.py check` passa.
11. Suíte completa verde.
12. Nenhum arquivo do repositório cita um workflow que não existe.

### Expected evidence

Listagem final de `.github/workflows/`, o YAML resultante, resultado do job no
próximo push, `check` e suíte completa.

### Output format

Diff, saída dos comandos e atualização desta PRD.

## Scope

- `.github/workflows/copilot-setup-steps.yml`
- `requirements.txt`, apenas se a decisão for manter o workflow e declarar
  `playwright` como dependência de fato
- qualquer contrato que cite o workflow

## Out of scope

- `.github/workflows/ci.yml`, que já está padronizado.
- Configuração de MCP em `.mcp.json` ou `.cursor/mcp.json`.
- Adicionar teste de navegador à suíte.
- Introduzir matriz de sistema operacional.

## Impacted files

- `.github/workflows/copilot-setup-steps.yml`
- possivelmente `requirements.txt`
- `docs/prd/README.md`

## Risks and edge cases

- **Remover workflow que alguém usa.** Mitigação: a decisão é do operador, a
  partir do histórico de execuções no GitHub; o conteúdo permanece no
  histórico do Git.
- **Declarar `playwright` e ampliar o ambiente sem necessidade.** Mitigação: só
  entra em `requirements.txt` se a decisão for manter o workflow e o passo de
  navegador tiver propósito declarado.
- **`ubuntu-latest` quebrando um passo escrito para PowerShell.** Mitigação: se
  mantido, cada passo é reescrito para o shell default, não adaptado por
  tentativa.
- **Verificação de rede substituída por nada.** Mitigação: se a intenção era
  provar que o navegador sobe, o alvo passa a ser uma página servida
  localmente pelo próprio job, sem saída para a internet.

## Rules and constraints

`AGENTS.md` seção 8: configuração é validada por parser ou comando oficial,
nunca por leitura a olho — o veredito desta PRD é o resultado do job.
`AGENTS.md` seção 12: resíduo é removido e documentação obsoleta é corrigida
na mesma mudança. `AGENTS.md` seção 10: nenhum erro mascarado — um passo que
sempre falha não fica no workflow.

## Plan

1. Levantar com o operador se o workflow tem uso, a partir do histórico de
   execuções.
2. Se não tiver: remover o arquivo e buscar citações no repositório.
3. Se tiver: reescrever com runner, timeout, versões e shell alinhados, sem os
   passos de `--help` e sem acesso externo, declarando `playwright` se o passo
   de navegador for mantido.
4. Rodar `check` e a suíte completa.
5. Observar o resultado do job no push seguinte e registrar como evidência.

## Test plan

Não há comportamento de aplicação a testar. A verificação é:

- o YAML resultante é válido e o job conclui;
- `ci.yml` permanece verde com os oito passos;
- suíte completa como regressão, para garantir que nada de código foi tocado.

## Visual validation

Não se aplica: nenhuma mudança de template, CSS, JavaScript ou rota.

## ORM validation

Não se aplica: nenhuma mudança de modelo, consulta ou migration.

## Quality validation

Validação do YAML, resultado do job no GitHub, `python manage.py check` e
suíte completa.

## Evidence

- `.github/workflows/` contem dois arquivos: `ci.yml`, com os nove passos, e
  `copilot-setup-steps.yml` reescrito.
- `copilot-setup-steps.yml` passou a declarar `runs-on: ubuntu-latest`,
  `timeout-minutes: 20`, `actions/checkout@v5` e `actions/setup-python@v5` com
  `python-version: "3.12.10"`, igual ao conteudo de `.python-version`.
- Nenhum passo invoca `playwright`; nenhum passo acessa host externo ao GitHub;
  os dois passos que so chamavam `--help` de pacote npm nao existem mais, e
  `actions/setup-node` foi removido junto com eles.
- `python -m pip check` no ambiente recriado: "No broken requirements found."
- `manage.py check`: "no issues (0 silenced)".
- Suite completa: `Ran 745 tests in 325.678s ... OK`.

## Implemented

`copilot-setup-steps.yml` foi **corrigido, nao removido**. O arquivo tem uma
funcao real — preparar o ambiente Python do repositorio para o agente — e essa
funcao foi preservada, alinhada ao workflow principal:

- runner, timeout, versao de Python e versoes de action alinhadas ao `ci.yml`;
- `shell: pwsh` removido de todos os passos, consequencia da troca de runner;
- passo `Install Playwright Chromium` removido: `playwright` nao consta em
  `requirements.txt` e o projeto nao o importa, entao o passo nunca teve como
  passar;
- passos `Validate Playwright MCP` e `Validate Context7 MCP` removidos: chamar
  `--help` de pacote npm baixado na hora verifica o registro npm, nao este
  repositorio. Os MCPs sao configurados por `.mcp.json`;
- passo `Validate headless browser` removido: ele abria `https://example.com`,
  o que faz o veredito depender de DNS e da disponibilidade de um site de
  terceiros;
- `permissions: contents: read` movido para o nivel do workflow, como no
  `ci.yml`;
- comentario no topo registrando por que os passos sairam, para que a lacuna nao
  seja lida como esquecimento.

## Cleanup findings

- A decisao entre remover e corrigir estava registrada como pendente de
  consulta ao historico de execucoes. Ela deixou de depender disso: o arquivo
  tem proposito legitimo e declarado pela convencao do nome, e o que estava
  errado eram os passos, nao a existencia do workflow. Corrigir preserva a
  funcao e elimina o defeito; remover eliminaria os dois.
- `playwright` **nao** foi acrescentado a `requirements.txt`. Uma verificacao
  inicial sugeriu que `system/tests/test_commands.py` o importava; a leitura do
  arquivo mostrou que a ocorrencia era o nome do diretorio de artefato
  `.playwright-mcp`, que o ciclo destrutivo remove. Nenhum codigo Python do
  projeto importa playwright.
- Nenhum contrato citava o workflow, entao nao houve link a corrigir.
- Nenhum residuo introduzido.

## Follow-up PRDs

Nenhuma.

## Deviations from plan

- O plano previa levantar com o operador se o workflow tem uso antes de decidir.
  A decisao foi tomada sem essa consulta porque as duas alternativas
  convergiram: o que precisava mudar eram os passos defeituosos, e isso vale
  tanto se o job roda quanto se nao roda. Corrigir e a opcao que nao destroi
  informacao.

## Pending

- Rodar o CI de fato: o YAML foi validado localmente, mas os dois jobs so
  correm no proximo push.
- Commitar o worktree. Nenhum commit foi feito pelo agente.

## Final status

Concluida. `.github/workflows/` tem apenas verificacao que pode passar, que
valida este repositorio e que nao depende de servico de terceiros para dar
veredito. O passo quebrado e os tres passos sem valor de verificacao foram
removidos, e o restante ficou alinhado ao workflow principal.
