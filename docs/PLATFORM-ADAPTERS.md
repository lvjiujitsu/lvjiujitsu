# Adaptadores de Claude, Codex e Cursor

O protocolo comum está em `AGENTS.md`; este documento registra somente
diferenças de descoberta e ferramenta.

## 1. Skills

| Skill | Claude | Codex | Cursor |
|---|---|---|---|
| `lv-task-intake` | `/lv-task-intake` | `$lv-task-intake` | `/lv-task-intake` |
| `lv-prd` | `/lv-prd` | `$lv-prd` | `/lv-prd` |
| `lv-django-delivery` | `/lv-django-delivery` | `$lv-django-delivery` | `/lv-django-delivery` |
| `lv-ui-delivery` | `/lv-ui-delivery` | `$lv-ui-delivery` | `/lv-ui-delivery` |
| `lv-cleanup-audit` | `/lv-cleanup-audit` | `$lv-cleanup-audit` | `/lv-cleanup-audit` |
| `lv-prompt-builder` | `/lv-prompt-builder` | `$lv-prompt-builder` | `/lv-prompt-builder` |
| `lv-parity-audit` | `/lv-parity-audit` | `$lv-parity-audit` | `/lv-parity-audit` |

`lv-prompt-builder` e `lv-parity-audit` têm `disable-model-invocation: true`:
no Claude só são acionadas por invocação manual do operador. Isso rege como a
skill é disparada e **não dispensa** o espelho nas outras plataformas.

## 1.1. Slash commands

Três comandos em `.claude/commands/`, para o ciclo que se repete. Eles não
substituem as skills: executam uma sequência já decidida.

| Comando | O que faz |
|---|---|
| `/reset-local` | ciclo destrutivo local até o servidor no ar, com as guardas verificadas antes de apagar |
| `/validar-tela <rota>` | valida uma rota em desktop e mobile, nos dois temas, com screenshot obrigatório |
| `/sync-skills` | compara as sete skills nas três plataformas e reporta divergência sem sobrescrever |

`/reset-local` e `/sync-skills` mantêm `disable-model-invocation: true`: a
invocação é manual, porque o primeiro destrói o ambiente local e o segundo é
uma auditoria que o operador pede.

## 2. Claude

- Fonte inicial: `CLAUDE.md` → `AGENTS.md`.
- Skills: `.claude/skills/` — é a fonte de edição das três cópias.
- MCP de projeto: `.mcp.json` (Context7 e Playwright).
- Comandos repetíveis: `.claude/commands/` — `/reset-local`,
  `/validar-tela`, `/sync-skills`.
- Permissões: `.claude/settings.json`, versionado;
  `.claude/settings.local.json` é pessoal e fica no `.gitignore`.
- Servidor de desenvolvimento: `.claude/launch.json`, porta 8000.
- UI usa o browser do Desktop; Playwright é complemento, não substituto.

## 3. Codex

- Fonte inicial: `AGENTS.md`; fatos em `CLAUDE.md`.
- Skills e metadados: `.agents/skills/`.
- Cada skill tem `agents/openai.yaml` com `display_name`,
  `short_description` e `default_prompt`. O arquivo existe **só** aqui — é
  metadado da plataforma, não cópia de skill, e sua ausência em `.claude` e
  `.cursor` é esperada.
- Os sete `openai.yaml` são UTF-8 com LF. `.gitattributes` fixa `*.yaml` em LF
  e o validador falha se a corrupção por replacement character voltar.
- MCP: `.codex/config.toml`.
- UI usa o in-app browser; sessão pessoal pode usar Chrome.

## 4. Cursor

- Regras curtas: `.cursor/rules/` — `protocol.mdc`, `django.mdc`, `ui.mdc`.
  São ponteiros para `AGENTS.md`, `CLAUDE.md` e as skills, não uma segunda
  cópia do protocolo.
- Skills: `.cursor/skills/`; MCP: `.cursor/mcp.json`.
- Browser integrado é prioritário; Playwright é fallback.
- Cursor é plataforma ativa. Nenhum contrato deve declará-la como "não se
  aplica".

## 5. Context7

Context7 é obrigatório, antes da documentação oficial e sempre antes de decidir
por memória, quando a demanda envolver:

- Django ou outra biblioteca;
- SDK ou API;
- CLI;
- configuração de framework;
- comportamento atual de ferramenta.

Depois do Context7, confirmar em documentação oficial da versão em uso quando a
decisão for material.

## 6. Browser

Prioridade:

1. navegador interno da ferramenta;
2. navegador com sessão autenticada da ferramenta;
3. Playwright MCP para inspeção automatizada;
4. relatório explícito de limitação.

Validação visual prioriza rota real, desktop e mobile, os dois temas e
screenshot. Headless não substitui evidência visual quando a ferramenta oferece
browser interno; quando não há browser disponível, a validação é declarada
incompleta, nunca presumida.

## 7. Sincronização

`.claude/skills/<nome>/SKILL.md` é a fonte de edição; `.agents/skills/` e
`.cursor/skills/` são espelhos byte a byte. Um dono só: `/sync-skills` e este
documento concordam, e nenhum outro contrato declara fonte diferente.

As sete skills existem nas três plataformas. Ausência em qualquer uma é
divergência a corrigir, não exceção conhecida.

Ao alterar:

1. sincronizar o mesmo conteúdo para `.agents` e `.cursor`;
2. manter `agents/openai.yaml` na cópia Codex, em UTF-8 com LF;
3. validar frontmatter e YAML;
4. comparar SHA-256 das três cópias;
5. atualizar esta matriz quando uma skill for adicionada.

Os cinco passos são executados de uma vez por:

```powershell
.\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
```

O script exige os três diretórios, o mesmo conjunto de skills em cada um,
conteúdo idêntico ao de `.claude/skills/` e metadado Codex íntegro. Falha
quebra o CI. `/sync-skills` faz a mesma comparação de forma interativa e
reporta sem sobrescrever.
