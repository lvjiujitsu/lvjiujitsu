# PRD-096: Encoding UTF-8 do template de cronograma

## Summary
Corrigir `templates/calendar/calendar.html` e o teste de contrato para garantir leitura UTF-8 em Windows, eliminando o ERROR na suíte (`UnicodeDecodeError` cp1252 na posição 3727).

## Demand type
Correção de qualidade + teste.

## Current problem
- `test_calendar_template_loads_external_script_without_inline_logic` usa `Path.read_text()` sem encoding no Windows.
- Template contém byte(s) fora de ASCII/cp1252 (provável caractere Unicode em comentário ou texto).
- Suíte: 262 testes, 1 ERROR.

## Goal
Arquivo salvo UTF-8 válido; teste passa em Windows e Linux; conteúdo pt-BR preservado.

## Context Ledger
### Files read in full
- `templates/calendar/calendar.html`
- `system/tests/test_register_wizard_contract.py`
- Saída `manage.py test --verbosity 2` 2026-06-30

### Adjacent files consulted
- `static/system/js/calendar/calendar.js`

### Internet / official documentation
- Python pathlib read_text encoding: https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Corrigir só o teste sem normalizar o template deixa risco em editores Windows.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Evidência de teste local na auditoria.

## Execution prompt
### Persona
Engenheiro de qualidade cross-platform.

### Action
Normalizar template para UTF-8; ajustar teste para `encoding="utf-8"` como defesa.

### Context
PRD-080 proíbe innerHTML inseguro no JS do calendário.

### Constraints
- Sem alterar comportamento visual.
- Atualizar `?v=` se JS alterado.

### Acceptance criteria
- [ ] `manage.py test system.tests.test_register_wizard_contract` verde no Windows.
- [ ] Arquivo sem BOM problemático; caracteres pt-BR corretos no browser.
- [ ] Nenhum `.innerHTML` no JS do calendário (contrato existente).

### Expected evidence
- Comando teste e saída OK.

### Output format
PRD Evidence.

## Scope
- `calendar.html`
- `test_register_wizard_contract.py`
- Revisão pontual de caracteres especiais.

## Out of scope
- Redesign do cronograma.

## Impacted files
- `templates/calendar/calendar.html`
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases
- Git autocrlf alterando bytes.

## Rules and constraints
- Preferir entidades HTML ou ASCII em comentários se necessário.

## Plan
1. [x] Reproduzir a falha original.
2. [x] Confirmar estado atual do template.
3. [x] Adicionar `encoding="utf-8"` explícito em todas as leituras de arquivo do teste (defesa cross-platform).
4. [x] Green full suite proporcional.

## Test plan
### Tests to author
- Manter teste existente (ajuste encoding).

### Execution authorization
Local.

### Execution evidence
- Ao reproduzir localmente, `manage.py test system.tests.test_register_wizard_contract --verbosity 2` já passou (4 testes OK) mesmo antes da correção — o `UnicodeDecodeError` original ocorreu em um estado anterior de `templates/calendar/calendar.html` (já corrigido organicamente durante a PRD-080/077).
- Correção defensiva aplicada mesmo assim: as 5 chamadas `Path.read_text()` em `system/tests/test_register_wizard_contract.py` (linhas 15, 16, 26, 55, 56) passaram a usar `encoding="utf-8"` explícito, eliminando a dependência do locale do SO (cp1252 no Windows) para qualquer regressão futura.
- `.venv/Scripts/python.exe manage.py test system.tests.test_register_wizard_contract --verbosity 2` — 4 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 testes OK.

## Visual validation
`/calendar/` renderiza corretamente com acentuação pt-BR no navegador interno (validado durante PRD-077).

## ORM validation
N/A.

## Quality validation
- `manage.py test --verbosity 2` — 0 failures.

## Evidence
- O byte problemático original não está mais presente no `calendar.html` atual (já reescrito durante PRD-080/077); a causa raiz historicamente reportada não é mais reproduzível, mas a defesa (encoding explícito) foi aplicada para não depender de um estado de arquivo específico.

## Implemented
- `system/tests/test_register_wizard_contract.py`: `encoding="utf-8"` explícito em todas as leituras de arquivo.

## Cleanup findings
- Nenhum resíduo.

## Follow-up PRDs
- Nenhum.

## Deviations from plan
- Não foi necessário identificar/substituir um byte específico, pois o arquivo atual já não reproduz o erro; a correção aplicada foi puramente defensiva conforme os critérios de aceite.

## Pending
- Nenhum.

## Final status
Concluída.
