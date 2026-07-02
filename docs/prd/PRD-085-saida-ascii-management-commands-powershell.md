# PRD-085: Saida ASCII em management commands no PowerShell

## Summary
Garantir que management commands usados no bootstrap local não quebrem em consoles PowerShell com encoding `cp1252`.

## Demand type
Correção operacional de seeds e governança local.

## Current problem
Durante a validação da sequência local de seeds, `seed_system_initial_graduation_rules` falhou com `UnicodeEncodeError` ao imprimir o caractere `→`.

## Goal
As saídas dos management commands operacionais devem evitar símbolos Unicode fora do encoding padrão do PowerShell.

## Scope
- Remover setas Unicode de comandos de seed.
- Preservar mensagens em pt-BR quando suportadas por `cp1252`.
- Validar a sequência de seeds afetada.

## Out of scope
- Reescrever todos os textos de CLI.
- Alterar encoding global do Python, terminal ou Django.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Evidence
- Comando executado: sequência local de seeds após `migrate`.
- Falha real: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'`.
- Arquivo direto: `system/management/commands/seed_system_initial_graduation_rules.py`.

## Plan
- [x] Trocar `→` por `->` em seeds administrativas, professor/turma e graduação.
- [x] Trocar `↳` por `->` na seed Stripe para evitar falha equivalente.
- [x] Reexecutar sequência local de seeds.

## Test plan
- Reexecutar as seeds locais em PowerShell.
- Executar `manage.py check`.

## Implemented
- Saídas com `→` foram substituídas por `->` em:
  - `seed_system_initial_graduation_rules`
  - `seed_system_initial_class_catalog`
  - `seed_system_initial_class_catalog_administrative`
  - `seed_system_initial_class_categories_administrative`
  - `seed_system_initial_class_categories_teacher`
- Saídas com `↳` foram substituídas por `->` em `seed_system_initial_subscription_plans_stripe`.

## Execution evidence
- A primeira sequência local falhou em `seed_system_initial_graduation_rules` com `UnicodeEncodeError` no caractere `→`.
- Após a correção, a sequência local de seeds executou com exit code 0 até `seed_system_initial_holidays`.
- `rg -n "→|✓|×" system\management\commands` não encontrou ocorrências restantes.

## Final status
Concluída.
