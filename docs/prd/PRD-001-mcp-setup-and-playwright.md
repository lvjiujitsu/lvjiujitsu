# PRD-001: Corrigir MCPs de Figma, Context7 e Playwright
## Resumo
Corrigir a inicializacao de MCPs do ambiente Codex, restabelecendo o acesso do Figma, adicionando os servidores `context7` e `playwright`, e garantindo `playwright` + Chromium headless instalados na `.venv`.

## Problema atual
- O startup do MCP reporta falha no `figma`.
- `codex mcp list` mostra apenas `figma`.
- `figma_whoami` retorna `401: Unauthorized. Manual reauthentication required.`
- `codex mcp login figma` falha com `No authorization support detected`.
- `requirements.txt` ja exige `playwright==1.52.0`, mas a instalacao inicial pela sandbox nao encontrou a versao no indice acessivel.

## Objetivo
- Reconfigurar os MCPs do Codex para que `figma`, `context7` e `playwright` fiquem registrados.
- Restabelecer a autenticacao do `figma` ou registrar com evidencia o bloqueio exato remanescente.
- Garantir `playwright` e Chromium headless instalados dentro da `.venv`.

## Contexto consultado
  - Context7: indisponivel no inicio da tarefa; nao havia MCP configurado para consulta.
  - Web:
    - Context7 installation: https://context7.com/docs/installation
    - Figma MCP overview: https://help.figma.com/hc/en-us/articles/35280968300439-Figma-MCP-collection-What-is-the-Figma-MCP-server
    - PyPI Playwright release history: https://pypi.org/project/playwright/

## Dependências adicionadas
  - nenhuma no `requirements.txt`; `playwright==1.52.0` ja estava declarado e foi alinhado na `.venv`

## Escopo / Fora do escopo
## Escopo
- Ajustar configuracao local do Codex MCP.
- Instalar dependencias locais necessarias para Playwright headless.
- Validar os comandos exigidos por `AGENTS.md` e `CLAUDE.md` que se aplicam a esta demanda.

## Fora do escopo
- Alteracoes funcionais no produto Django.
- Automacoes Figma alem da recuperacao da autenticacao/configuracao.

## Arquivos impactados
  - docs/prd/PRD-001-mcp-setup-and-playwright.md
  - C:\Users\whsf\.codex\config.toml
  - requirements.txt (somente se houver ajuste real de versao)

## Riscos e edge cases
  - `codex mcp login figma` pode continuar indisponivel se a autenticacao exigida for do conector remoto e nao do CLI.
  - Escrita em `C:\Users\whsf\.codex\config.toml` exige permissao fora do workspace.
  - Instalacao de `playwright` e pacotes npm pode depender de acesso de rede fora da sandbox.
  - A sessao atual pode nao recarregar novos MCPs sem reinicio do Codex.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
  - Seguir `AGENTS.md` e `CLAUDE.md`.
  - Registrar toda decisao e bloqueio com evidencia real.
  - Nao fingir sucesso de autenticacao ou instalacao.
  - Atualizar `requirements.txt` apenas se a versao instalada precisar mudar de verdade.

## Critérios de aceite (escritos como assertions testáveis)
  - [x] `codex mcp list` lista `figma`, `context7` e `playwright`.
  - [x] `figma` deixou o estado `Auth Unsupported` e concluiu `codex mcp login figma` com sucesso.
  - [x] `.\.venv\Scripts\python.exe -c "from playwright.sync_api import sync_playwright; print('OK')"` imprimiu `OK` durante a instalacao.
  - [x] `.\.venv\Scripts\playwright.exe install chromium` concluiu sem erro.
  - [x] O PRD final registra comandos, resultados e desvios reais.

## Plano (ordenado por dependência — fundações primeiro)
  - [x] 1. Registrar estado inicial e documentacao consultada
  - [x] 2. Ajustar configuracao de MCP no Codex
  - [x] 3. Instalar e validar Playwright Python na `.venv`
  - [x] 4. Instalar e validar Chromium headless
  - [x] 5. Executar validacoes finais
  - [x] 6. Atualizar este PRD com implementado e desvios

## Comandos de validação
  - codex mcp list
  - codex mcp get figma
  - .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  - .\.venv\Scripts\playwright.exe install chromium
  - .\.venv\Scripts\python.exe -c "from playwright.sync_api import sync_playwright; print('OK')"

## Implementado (preencher ao final)
- `docs/prd/PRD-001-mcp-setup-and-playwright.md` criado.
- `codex mcp add context7 --url https://mcp.context7.com/mcp` executado com sucesso; OAuth concluido com sucesso.
- `codex mcp add playwright -- "C:\Program Files\nodejs\npx.cmd" -y @playwright/mcp@latest` executado com sucesso.
- `codex mcp login figma` executado com sucesso apos re-registro do servidor `figma`.
- `C:\Users\whsf\.codex\config.toml` passou a conter `figma`, `context7` e `playwright`.
- `playwright==1.52.0` reinstalado na `.venv`, substituindo a instalacao local anterior `1.58.0`.
- Chromium e Chromium Headless Shell baixados com sucesso para `C:\Users\whsf\AppData\Local\ms-playwright`.
- Smoke test real fora da sandbox confirmou browser headless abrindo e retornando titulo `ok`.
- Validacoes adicionais executadas:
  - `codex mcp list`
  - `.\.venv\Scripts\pip.exe show playwright`
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py showmigrations`
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 2`

## Desvios do plano
- `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` falhou por permissao no caminho `C:\Users\whsf\Documents\PowerShell`; a sessao atual foi mantida em UTF-8 e a tarefa prosseguiu com evidencia real.
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` falhou na sandbox ao resolver `playwright==1.52.0`; a instalacao foi refeita fora da sandbox com sucesso.
- O smoke test inicial do Playwright falhou na sandbox com `PermissionError: [WinError 5] Acesso negado` ao criar subprocesso; repetido fora da sandbox com sucesso.
- `.\.venv\Scripts\python.exe manage.py findstatic css/base.css` retornou `No matching file found for 'css/base.css'`; o projeto hoje usa arquivos namespaced em `static/system/...`, entao este item do checklist geral nao e atendido pelo estado atual do repositorio.
