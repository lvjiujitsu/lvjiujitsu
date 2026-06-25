# Adaptadores de Claude, Codex e Cursor

O comportamento comum está em `AGENTS.md`.

## Skills

| Skill | Claude | Codex | Cursor |
|---|---|---|---|
| `lv-task-intake` | `/lv-task-intake` | `$lv-task-intake` | `/lv-task-intake` |
| `lv-prd` | `/lv-prd` | `$lv-prd` | `/lv-prd` |
| `lv-ui-delivery` | `/lv-ui-delivery` | `$lv-ui-delivery` | `/lv-ui-delivery` |
| `lv-django-delivery` | `/lv-django-delivery` | `$lv-django-delivery` | `/lv-django-delivery` |
| `lv-cleanup-audit` | `/lv-cleanup-audit` | `$lv-cleanup-audit` | `/lv-cleanup-audit` |

## Claude Code Desktop

- `CLAUDE.md` importa `AGENTS.md`.
- Skills: `.claude/skills/`.
- MCP: `.mcp.json`.
- Usar Plan mode para pesquisa e proposta.
- UI exige proposta aprovada e browser do Desktop.
- Não presumir produto chamado “Claude Design”.
- Testes pedem autorização; operações destrutivas são bloqueadas.
- Regras Claude são avaliadas em ordem `deny` → `ask` → `allow`; o `ask` de projeto para testes prevalece sobre allows históricos do arquivo local.

## Codex

- Fonte inicial: `AGENTS.md`.
- Fatos locais: `CLAUDE.md`.
- Skills: `.agents/skills/`.
- MCP: `.codex/config.toml`.
- UI usa in-app browser.
- Página autenticada pode exigir Chrome com sessão.

## Cursor

- Regras curtas em `.cursor/rules/`.
- Skills: `.cursor/skills/`.
- MCP: `.cursor/mcp.json`.
- Browser integrado é prioritário; Playwright é fallback.

## Context7 e browser

- Context7 é obrigatório para biblioteca, framework, SDK, API ou CLI.
- Depois, confirmar decisões materiais na documentação oficial.
- Browser interno é a primeira escolha para UI.
- Headless não substitui evidência visual quando a ferramenta oferece browser.

## Pagamentos

- Fluxos externos podem exigir Chrome, túnel, Stripe CLI ou painel do gateway.
- Usar `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e PRD-058.
- Nunca expor tokens ou copiar valores de `.env`.

## Sincronização

Ao alterar uma skill:

1. atualizar `.agents/skills/<name>/SKILL.md`;
2. sincronizar Claude e Cursor;
3. validar as três;
4. comparar hashes.
