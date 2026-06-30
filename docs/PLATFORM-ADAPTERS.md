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
| `lv-prompt-builder` | `/lv-prompt-builder` | `$lv-prompt-builder` | `/lv-prompt-builder` |

> `lv-prompt-builder` usa `disable-model-invocation: true`: é de invocação manual e não dispara sozinha. Gera o execution prompt de uma demanda e para, sem implementar.

## Claude Code Desktop

- `CLAUDE.md` importa `AGENTS.md`.
- Skills: `.claude/skills/`.
- MCP: `.mcp.json`.
- Usar Plan mode para pesquisa e proposta.
- UI exige proposta aprovada e browser do Desktop.
- Não presumir produto chamado “Claude Design”.
- Testes locais, migrations locais, reset local e seeds locais são permitidos quando necessários ao objetivo solicitado.
- Regras Claude devem permitir o ciclo local; HG, produção, deploy, push e pagamentos externos continuam exigindo confirmação explícita.

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

- Context7 é obrigatório quando a demanda envolver biblioteca, framework, SDK, API, CLI, configuração de ferramenta, protocolo de integração ou comportamento de browser/plataforma.
- Depois, confirmar decisões materiais na documentação oficial ou fonte primária equivalente.
- Pesquisa irrelevante não preenche checklist de PRD.

Prioridade de validação visual:

1. browser interno da ferramenta com a rota real;
2. Chrome ou superfície autenticada do usuário quando a sessão for necessária;
3. Playwright/MCP/headless apenas como fallback ou complemento;
4. relatório explícito de limitação quando nenhuma superfície visual estiver disponível.

Headless não substitui evidência visual quando a ferramenta oferece browser interno.

## Pagamentos

- Fluxos externos podem exigir Chrome, túnel, Stripe CLI ou painel do gateway.
- Usar `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e PRD-058.
- Nunca expor tokens ou copiar valores de `.env`.

## Sincronização

Ao alterar uma skill:

1. atualizar `.agents/skills/<name>/SKILL.md`;
2. sincronizar `.claude/skills/<name>/SKILL.md`;
3. sincronizar `.cursor/skills/<name>/SKILL.md`;
4. validar frontmatter e conteúdo das três cópias;
5. comparar hashes ou conteúdo byte a byte;
6. atualizar `docs/PLATFORM-ADAPTERS.md` quando uma skill nova for adicionada.
