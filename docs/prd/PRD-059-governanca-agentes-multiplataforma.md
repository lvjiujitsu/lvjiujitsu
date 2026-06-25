# PRD-059: Governança enxuta para Claude, Codex e Cursor

## Summary

Aplicar ao LV JIU JITSU uma governança curta e verificável, separando protocolo universal, fatos do projeto, operação de banco/pagamentos e adaptações de Claude, Codex e Cursor.

## Demand type

Revisão de governança do agente + regeneração documental.

## Current problem

- `AGENTS.md` e `CLAUDE.md` repetem procedimentos e histórico.
- Comandos Claude e regras Cursor duplicam o protocolo.
- Testes são descritos como execução automática, contra a política atual do usuário.
- Asaas aparece dentro do protocolo universal.
- `CLAUDE.md` declara Stripe como legado, mas código, settings, seed e PRD-058 confirmam Stripe recorrente ativo.
- Não existem skills equivalentes e sincronizadas para as três ferramentas.

## Goal

Consolidar um fluxo que:

1. obtenha contexto integral e pesquisa atual antes da mudança;
2. confirme entendimento de forma mínima;
3. use SDD e autoria test-first;
4. execute testes somente após autorização;
5. exija proposta aprovada e browser interno para UI;
6. preserve operações especiais de Asaas/Stripe, banco e seeds em documentos próprios;
7. audite o escopo ao final sem expandi-lo automaticamente.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/*.md`
- `.claude/settings.json`
- todas as regras em `.cursor/rules/`
- `mcp.json`
- `lvjiujitsu/settings.py`
- `clear_migrations.py`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/GUIA-PREENCHIMENTO-CLAUDE-MD.md`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/prd/PRD-054-alinhamento-arquitetural-lv-visary.md`
- `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`
- `system/services/stripe_checkout.py`
- `system/views/stripe_views.py`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `system/services/asaas_checkout.py`
- `system/views/asaas_views.py`

### Adjacent files consulted

- inventário de `system/management/commands/`
- `requirements.txt`
- wizard guides em `docs/wizard-step-*.md`
- bootstrap reutilizável do Visary.

### Internet / official documentation

- [Claude Code: project memory](https://code.claude.com/docs/en/memory)
- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code Desktop](https://code.claude.com/docs/en/desktop)
- [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex: Agent Skills](https://developers.openai.com/codex/skills)
- [Codex: in-app browser](https://developers.openai.com/codex/app/browser)
- [Cursor: Rules](https://cursor.com/docs/rules)
- [Cursor: Agent Skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [Django 5.2 testing](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)
- [Django transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)

### Context7 / MCPs / tools verified

- Pesquisa Context7 de Django e Playwright registrada no PRD-106 do Visary.
- PowerShell 7.6.0, Python 3.12.10, Git e `rg` disponíveis.
- Browser interno disponível em `http://localhost:8000/`, mas não aplicável a arquivos documentais/configuração.

### Limitations found

- `.claude/settings.local.json` já contém mudança do usuário e será preservado.
- `system/migrations/0001_initial.py` já está excluído na worktree e não será restaurado nem alterado.
- A descoberta runtime das skills em Claude e Cursor exige recarga das ferramentas.
- Testes Django não foram autorizados e não são necessários para esta mudança.

## Required skills

- `visary-task-intake`
- `visary-prd`
- `skill-creator`
- `visary-cleanup-audit`

Após a implementação:

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: aplicar o bootstrap de governança ao LV, preservando fatos e alterações preexistentes.
- User approval: solicitação explícita de implementação.
- Date: 2026-06-25.

## Execution prompt

### Persona

Engenheiro de governança, Django e integrações de pagamento.

### Action

Reorganizar instruções e configurações do LV, criar skills equivalentes e remover duplicação legada.

### Context

O LV é um monólito Django 5.2 com app `system`, pagamentos Asaas e Stripe, Render/Supabase, wizard público e operação local em Windows/PowerShell.

### Constraints

- Não alterar código funcional.
- Não tocar nas mudanças preexistentes do usuário.
- Não executar testes, ORM mutável, migrations, reset ou seeds.
- Não inventar estado de gateway.
- Manter Asaas/Stripe fora do protocolo universal.
- Não declarar validação visual para mudança documental.

### Acceptance criteria

- [x] `AGENTS.md` deve conter somente protocolo comum e referências.
- [x] `CLAUDE.md` deve conter somente fatos atuais do LV.
- [x] Asaas e Stripe devem ser documentados como integrações ativas.
- [x] Procedimentos detalhados devem estar separados por responsabilidade.
- [x] Testes devem ser escritos antes do código quando aplicável, mas executados somente após autorização.
- [x] UI deve exigir proposta aprovada e validação no navegador interno.
- [x] Cinco skills equivalentes devem existir em Claude, Codex e Cursor.
- [x] Regras Cursor redundantes e comandos Claude substituídos devem ser removidos.
- [x] Configurações MCP devem usar as convenções de cada ferramenta.
- [x] Alterações preexistentes devem permanecer intactas.

### Expected evidence

- Validação das 15 cópias de skills.
- Comparação de hashes entre plataformas.
- Parse de JSON/TOML.
- Busca textual das políticas críticas.
- `git diff --check`.

### Output format

Resumo curto, evidências, limitações, pendências e status.

## Scope

- `AGENTS.md`
- `CLAUDE.md`
- `requirements-dev.txt`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/`
- `.claude/skills/`
- `.claude/commands/`
- `.claude/settings.json`
- `.mcp.json`
- `.codex/config.toml`
- `.cursor/mcp.json`
- `.cursor/rules/`
- `.cursor/skills/`
- este PRD.

## Out of scope

- Código Django, templates, CSS e JavaScript.
- Dados, migrations e seeds.
- Validação real de pagamentos.
- Deploy, push ou configuração de painéis externos.

## Impacted files

As fontes e adaptadores listados no escopo.

## Risks and edge cases

- Bloquear testes apenas em documentação e deixar permissão ampla em configuração.
- Remover detalhes de Asaas/Stripe sem manter referência operacional.
- Copiar fatos do Visary para o LV.
- Divergência entre cópias de skills.
- Sobrescrever mudanças locais do usuário.

## Rules and constraints

- Menor mudança correta.
- Uma fonte de verdade por responsabilidade.
- Conteúdo permanente curto.
- Evidência antes de conclusão.

## Plan

- [x] Context and research
- [x] Reescrever fontes comuns
- [x] Criar documentos operacionais
- [x] Criar e sincronizar skills
- [x] Simplificar adaptadores
- [x] Validar estrutura
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Não aplicável.

### Execution authorization

- Status: não solicitada.

### Execution evidence

Testes Django não executados.

## Visual validation

Não aplicável. Nenhuma tela será alterada.

## ORM validation

Não aplicável.

## Quality validation

- Validador de skills.
- Parse de configurações.
- Busca de conflitos.
- Revisão integral do diff.

## Evidence

- `AGENTS.md`: 179 linhas / 6.246 bytes.
- `CLAUDE.md`: 147 linhas / 5.214 bytes.
- 15 cópias de skills validadas por `quick_validate.py`: 15 resultados `Skill is valid!`.
- SHA-256 idêntico entre `.agents`, `.claude` e `.cursor` para as cinco skills.
- `.claude/settings.json`, `.mcp.json` e `.cursor/mcp.json` carregados como JSON.
- `.codex/config.toml` carregado como TOML.
- Arquivos novos lidos como UTF-8 e sem whitespace final.
- `git diff --check` sem erro bloqueante.
- Busca não encontrou placeholders de template no LV nem declaração de Stripe como legado nas fontes novas.
- Referências de wizard, pagamentos, PRD-040, PRD-058 e serviços Asaas/Stripe existem.
- `.claude/settings.local.json` mantém allows históricos de teste, mas o `ask` de projeto prevalece porque Claude avalia regras em `deny` → `ask` → `allow`.
- A mudança preexistente em `.claude/settings.local.json` e a exclusão de `system/migrations/0001_initial.py` permaneceram fora do escopo.

## Implemented

- `AGENTS.md` reduzido a protocolo comum.
- `CLAUDE.md` reduzido a contexto factual, com Asaas e Stripe ativos.
- Criados workflow, padrão de PRD, adaptadores e operação de banco/seeds.
- Política visual alinhada ao browser interno e testes sob autorização.
- Criadas cinco skills em Claude, Codex e Cursor.
- Metadados Codex `agents/openai.yaml` criados em UTF-8.
- Comandos Claude redundantes removidos.
- Regras Cursor reduzidas a protocolo, Django e UI.
- MCPs separados por convenção de ferramenta.
- `requirements-dev.txt` criado com PyYAML para validação de skills.
- Guia legado de preenchimento do `CLAUDE.md` removido.

## Cleanup findings

- Removida duplicação entre fontes, comandos e regras.
- Removida localização ambígua `mcp.json`.
- Nenhum TODO, placeholder, segredo, arquivo temporário ou cópia divergente permaneceu no escopo.
- O conflito documental Stripe legado × Stripe ativo foi corrigido com base no código, settings, seed e PRD-058.
- Não foi encontrado débito material adicional que justifique novo PRD.

## Follow-up PRDs

Nenhum.

## Deviations from plan

- O gerador oficial de skills escreveu inicialmente `openai.yaml` no encoding do console Windows; os cinco arquivos foram substituídos por UTF-8 e revalidados.
- PyYAML não foi instalado na `.venv` do LV; o validador foi executado com a `.venv` do Visary, que já contém a dependência aprovada.
- Não houve forward-test com subagente porque a tarefa não autorizou delegação.

## Pending

- Recarregar Claude Code, Codex e Cursor para redescobrir skills e configurações.
- Instalar `requirements-dev.txt` no LV somente quando o ambiente local precisar executar o validador.

## Final status

**Concluída com limitações**: governança e skills foram implementadas e validadas estruturalmente; a ativação runtime em Claude e Cursor depende de recarga.
