# PRD-159: Hardening da infraestrutura local e CI

## Summary

Remover um script temporário perigoso, restringir o reset destrutivo ao próprio projeto, validar ambiente/alvos antes da exclusão, fixar a versão Python declarada e adicionar CI Django sem credenciais externas.

## Demand type

Correção arquitetural e revisão de segurança operacional.

## Current problem

- `tmp_homolog_register.py` estava rastreado apesar de declarar que não deveria ser commitado, continha senha fixa e acionava sandboxes Asaas/Stripe.
- `clear_migrations.py` encerrava todos os processos Python do Windows e só validava a presença de `manage.py` antes da destruição.
- `.python-version` não fixava o patch declarado nos contratos.
- O único workflow existente preparava ferramentas do Copilot, sem validar a aplicação.

## Goal

Tornar o ciclo local seguro por construção e garantir que cada push/PR execute checks Django, verificação de migrations e testes.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `clear_migrations.py`
- `system/tests/test_commands.py`
- `.github/workflows/copilot-setup-steps.yml`
- `.python-version`
- `.gitignore`

### Adjacent files consulted

- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/PRD-154` a `PRD-158`
- `requirements.txt`
- `lvjiujitsu/settings.py`

### Internet / official documentation

- Não necessária: a mudança usa APIs locais da biblioteca padrão, Django e GitHub Actions já adotados no repositório.

### Context7 / MCPs / tools verified

- Não aplicável ao comportamento alterado.

### Limitations found

- O workflow novo não pode ser executado localmente como GitHub Actions; seus comandos são validados localmente.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

O prompt de 2026-07-25 autorizou explicitamente as quatro correções locais, testes proporcionais e documentação. Push, deploy, seeds remotas e operações externas foram proibidos.

## Execution prompt

### Persona

Mantenedor de infraestrutura e segurança operacional do LV.

### Action

Remover o temporário, endurecer o reset, cobrir os guards com testes e adicionar CI mínimo.

### Context

O ciclo destrutivo local usa SQLite, `.env` local e seeds explícitas.

### Constraints

- Nunca encerrar processo Python de outro projeto.
- Nunca aceitar `DJANGO_ENVIRONMENT` remoto ou `DATABASE_URL` no reset SQLite.
- Validar todas as pré-condições antes de qualquer exclusão.
- Não executar gateway, seed remota, push ou deploy.

### Acceptance criteria

- [x] `tmp_homolog_register.py` removido e `tmp_*.py` ignorado.
- [x] Processos Python só são encerrados quando executável ou linha de comando pertencem à raiz do LV.
- [x] Reset recusa env fora do projeto, ambiente não local, `DATABASE_URL`, settings obrigatórios vazios e alvo fora da raiz.
- [x] Testes unitários cobrem filtro de processos e guards destrutivos.
- [x] `.python-version` contém `3.12.10`.
- [x] `.github/workflows/ci.yml` executa install, `check`, migration dry-run e suíte.
- [x] `manage.py check`, migration dry-run e testes passam localmente.

### Expected evidence

Diff, testes focados, suíte, parser YAML e busca por resíduos.

### Output format

PRD atualizada e fechamento em pt-BR.

## Scope

- `clear_migrations.py`
- `system/tests/test_commands.py`
- `.github/workflows/ci.yml`
- `.python-version`
- `.gitignore`
- remoção de `tmp_homolog_register.py`

## Out of scope

- HG, produção, pagamentos externos, seeds remotas, push e deploy.
- Relaxamento de gates remotos da PRD-154.

## Impacted files

Os arquivos listados em `Scope`, esta PRD e o índice.

## Risks and edge cases

- Processo do LV iniciado com Python global: aceito quando a linha de comando contém a raiz do projeto.
- Processo de outro projeto usando Python: recusado pelo filtro de raiz.
- `.env` local incompleto: reset para antes da destruição e lista apenas nomes das chaves ausentes.

## Rules and constraints

- Menor mudança correta.
- Nenhum segredo real em código, logs ou workflow.
- TDD para os guards destrutivos.

## Plan

- [x] Context and research
- [x] Tests authored
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- Filtro positivo e negativo de processo do projeto.
- Garantia de que apenas o PID do LV recebe `taskkill`.
- Aceite de `.env` local completo.
- Recusa de ambiente remoto, configuração incompleta e target traversal.

### Execution authorization

- Status: authorized pelo prompt atual.

### Execution evidence

- `ClearMigrationsCleanupTestCase`: 9 testes, todos OK.
- Suíte completa: 719 testes em 226,840 s, todos OK.
- `manage.py check`: sem issues.
- `makemigrations --check --dry-run`: `No changes detected`.
- `py_compile clear_migrations.py`: sucesso.

## Visual validation

Não aplicável.

## ORM validation

Não aplicável.

## Quality validation

- Parser YAML do workflow confirmou `name` e job `django`.
- Preflight real, sem destruição: `OK local=.env`.
- `git diff --check`: sem erro de whitespace.

## Evidence

- Script temporário rastreado removido e padrão `tmp_*.py` ignorado.
- Reset filtra processos pela raiz, valida `.env` local/SQLite/settings/alvos antes de destruir e aguarda apenas PIDs do LV.
- CI Django mínimo criado para push e pull request.
- Python fixado em `3.12.10`.
- Runbooks local e Obsidian atualizados com o novo preflight.

## Implemented

- Script temporário rastreado removido e padrão `tmp_*.py` ignorado.
- Reset restrito aos processos e alvos do LV, com preflight local completo.
- Nove testes de segurança do reset.
- CI Django mínimo e pin Python `3.12.10`.
- Documentação local e runbook Obsidian alinhados.

## Cleanup findings

Nenhum segredo do temporário permaneceu. Nenhuma chamada externa, seed remota, push ou deploy foi executado.

## Follow-up PRDs

Nenhum previsto.

## Deviations from plan

PRD-154 não foi implementada porque flexibiliza ambientes remotos e está fora do hardening local autorizado.

## Pending

Execução do workflow no GitHub depende do próximo push/PR e não foi realizada localmente.

## Final status

**Concluída com limitação**: todos os comandos do workflow passaram localmente; execução hospedada aguarda um push/PR futuro.
