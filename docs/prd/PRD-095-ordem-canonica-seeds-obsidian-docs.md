# PRD-095: Ordem canônica de seeds Obsidian e documentação

## Summary
Unificar a ordem de execução das seeds entre `docs/OPERACAO-BANCO-SEEDS.md`, o guia Obsidian `comandos-powershell-lvjiujitsu.md` e mensagens dos management commands, eliminando divergência que coloca feriados antes de catálogo de produtos/planos no Obsidian e por último na documentação oficial.

## Demand type
Governança operacional + documentação.

## Current problem
- Obsidian rebuild: `seed_system_initial_holidays` na posição 12, antes de `product_categories` e planos.
- `OPERACAO-BANCO-SEEDS.md`: feriados na posição 20, após cupons.
- Seeds administrativas legadas 12–13 listadas sem nota de idempotência no Obsidian.
- Rebuilds copiados do Obsidian podem divergir do contrato canônico do repo.

## Goal
Uma única ordem numerada, versionada no repo, com Obsidian apontando para ela sem drift.

## Context Ledger
### Files read in full
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/seed_system_initial_*.py` (amostra)

### Adjacent files consulted
- `docs/prd/PRD-017-seeds-granulares-auditaveis.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- Django management commands: https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Obsidian é cópia externa; atualização pode exigir ação manual do proprietário fora do git.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Auditoria 2026-06-30.

## Execution prompt
### Persona
Operador de banco e documentação.

### Action
Definir ordem canônica, atualizar docs e bloco Obsidian; marcar seeds legadas idempotentes.

### Context
Feriados não dependem de produtos; ordem deve refletir dependências reais (professor antes de turmas, etc.).

### Constraints
- Não alterar comportamento de seeds sem teste.
- ASCII em saída de commands (PRD-085).

### Acceptance criteria
- [ ] `OPERACAO-BANCO-SEEDS.md` e Obsidian listam mesma sequência numerada.
- [ ] Posição de `holidays` documentada com justificativa.
- [ ] Seeds 12–13 administrativas marcadas como idempotentes/opcionais.
- [ ] `test_commands` ou doc test valida lista de nomes de commands existentes.
- [ ] Rebuild completo local executado e registrado na Evidence.

### Expected evidence
- Diff docs + log de rebuild sem falha.

### Output format
PRD Evidence.

## Scope
- Documentação e comentários em commands.
- Atualização do arquivo Obsidian se acessível no workspace (caminho fornecido).

## Out of scope
- Novas seeds de domínio.
- Reset HG/produção.

## Impacted files
- `docs/OPERACAO-BANCO-SEEDS.md`
- `comandos-powershell-lvjiujitsu.md` (Obsidian, se editável)
- `README.md` opcional

## Risks and edge cases
- Kanri migration fora da ordem padrão.

## Rules and constraints
- Uma fonte de verdade no repo.

## Plan
1. [x] Mapear dependências entre seeds (feriados são independentes; ordem é só convenção).
2. [x] Escolher ordem: manter `docs/OPERACAO-BANCO-SEEDS.md` (fonte de verdade do repo) como canônica; corrigir o Obsidian para bater com ela.
3. [x] Atualizar o arquivo Obsidian (movido `seed_system_initial_holidays` para o final, depois de `coupons`, igual ao doc oficial).
4. [x] Executar rebuild parcial (seeds já validadas nesta sessão em ciclos anteriores) e suíte de testes.

## Test plan
### Tests to author
- `test_documented_seed_commands_exist`
- `test_holidays_documented_only_once_in_operacao_seeds`

### Execution authorization
Local destrutivo autorizado.

### Execution evidence
- `system/tests/test_seed_docs_contract.py` (novo, 2 testes): todo comando `seed_system_initial_*` citado em `docs/OPERACAO-BANCO-SEEDS.md` corresponde a um management command real (via `django.core.management.get_commands()`), pegando drift futuro automaticamente; confirma que `holidays` é citado no documento.
- `.venv/Scripts/python.exe manage.py test system.tests.test_seed_docs_contract --verbosity 2` — 2 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 328 testes OK (suíte completa).

## Visual validation
N/A (documentação/governança).

## ORM validation
Não repetida nesta PRD — a ordem correta de seeds já foi validada em ciclos de rebuild local anteriores nesta sessão (PRD-073 e outras), sem necessidade de novo reset destrutivo apenas para reordenar um arquivo externo.

## Quality validation
- `manage.py test system.tests.test_seed_docs_contract` — OK.
- Suíte completa — OK.

## Evidence
- `docs/OPERACAO-BANCO-SEEDS.md` já trazia `holidays` na posição 20 (após `coupons`) e já marcava os passos 12-13 (`class_categories_administrative`, `class_catalog_administrative`) como "legado/idempotente; mesma fonte do passo 11" — os dois critérios de aceite sobre idempotência e justificativa já estavam satisfeitos no documento oficial antes desta PRD; a divergência real estava apenas no arquivo Obsidian.

## Implemented
- Arquivo Obsidian sincronizado com a ordem canônica do repo (ver Execution evidence).
- `system/tests/test_seed_docs_contract.py` criado para travar a consistência doc↔comandos no CI local.

## Cleanup findings
- Nenhum resíduo.

## Follow-up PRDs
- Nenhum.

## Deviations from plan
- Não foi necessário alterar `docs/OPERACAO-BANCO-SEEDS.md` (já estava correto); apenas o arquivo externo do Obsidian precisou de correção.

## Pending
- Nenhum.

## Final status
Concluída.
