# PRD-004: Ajuste de MCP (Playwright + Context7) e validação headless
## Resumo
Garantir que Playwright MCP e Context7 MCP estejam operacionais no ambiente de agente e validar o navegador headless.

## Problema atual
- Uso de MCP não estava padronizado no ambiente do agente.
- Não havia setup steps do Copilot para preparar ferramentas MCP de forma determinística.

## Objetivo
- Deixar o ambiente do agente pronto com dependências de MCP.
- Validar localmente comandos dos MCPs e execução headless do Chromium.

## Contexto consultado
  - Skill: `customizing-copilot-cloud-agents-environment` (copilot-setup-steps.yml).
  - Web:
    - Context7 repository (modos CLI/MCP e comandos).
      - https://github.com/upstash/context7
    - Context7 website (referência da plataforma).
      - https://context7.com

## Dependências adicionadas
  - nenhuma no `requirements.txt` (somente preparação de ambiente via workflow e validações locais).

## Escopo / Fora do escopo
- **Escopo:** criar workflow de setup do Copilot e validar execução dos MCPs + headless.
- **Fora do escopo:** alterar lógica de negócio de cadastro.

## Arquivos impactados
  - `.github/workflows/copilot-setup-steps.yml`

## Riscos e edge cases
  - Context7 MCP pode operar em modo básico sem API key; com chave, há modo autenticado com menos limitação.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- Mudança de infraestrutura de ambiente; não altera camadas MTV.
- Segurança: segredo deve ser injetado por Environment Secret (`copilot`), nunca hardcode.

## Critérios de aceite (escritos como assertions testáveis)
  - [x] `@playwright/mcp` responde com `--help`.
  - [x] `@upstash/context7-mcp` responde com `--help`.
  - [x] Playwright abre Chromium em headless e navega para página externa.
  - [x] Existe workflow `copilot-setup-steps.yml` com job `copilot-setup-steps`.

## Plano (ordenado por dependência — fundações primeiro)
  - [x] 1. Levantar contexto de setup steps e Context7.
  - [x] 2. Validar comandos MCP localmente.
  - [x] 3. Validar browser headless com Playwright.
  - [x] 4. Criar workflow de setup para ambiente Copilot.

## Comandos de validação
  - `npx -y @playwright/mcp --help`
  - `npx -y @upstash/context7-mcp --help`
  - `.\.venv\Scripts\python.exe -c "<script playwright headless>"`

## Implementado (preencher ao final)
- MCP Playwright validado por CLI (`--help`).
- MCP Context7 validado por CLI (`--help`).
- Chromium headless validado com Playwright (`TITLE=Example Domain`).
- Workflow de setup do Copilot criado para instalar dependências Python, instalar Chromium e validar MCPs no bootstrap.

## Desvios do plano
- Nenhum.
