# PRD-082: README e requirements-dev alinhados ao LV

## Summary
Corrigir onboarding e comandos documentados. `CLAUDE.md` cita `requirements-dev.txt`, mas o arquivo não existe; `README.md` descreve um kit genérico e regras Cursor que não correspondem ao repo atual.

## Demand type
Governança documental + configuração.

## Current problem
- `CLAUDE.md` recomenda `.\.venv\Scripts\pip.exe install -r requirements-dev.txt`.
- `requirements-dev.txt` não existe.
- `README.md` não descreve o produto LV nem o fluxo operacional real.

## Goal
Ter onboarding mínimo correto:
- README do LV;
- decisão explícita sobre `requirements-dev.txt`;
- comandos locais coerentes com `CLAUDE.md` e `docs/OPERACAO-BANCO-SEEDS.md`.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `requirements.txt`

### Adjacent files consulted
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`

### Internet / official documentation
Não aplicável.

### Context7 / MCPs / tools verified
- PowerShell.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual.

## Scope
- Substituir README genérico.
- Criar `requirements-dev.txt` ou remover referência de `CLAUDE.md`.
- Validar comandos documentados.

## Out of scope
- Alterar dependências de produção sem necessidade.

## Impacted files
- `README.md`
- `CLAUDE.md`
- `requirements-dev.txt`

## Risks and edge cases
- Duplicar dependências pode desalinhar ambientes.
- README não deve expor segredos ou comandos remotos destrutivos.

## Plan
- [x] Decidir se dev requirements é necessário.
- [x] Atualizar README.
- [x] Validar instalação/checks proporcionais.

## Test plan
### Tests to author
Não aplicável.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `rg -n "requirements-dev" --no-ignore -g '!staticfiles/**' -g '!docs/prd/PRD-059*' -g '!docs/prd/PRD-082*' .` → apenas `CLAUDE.md:59` e `README.md:41`, ambos referenciando o arquivo agora existente.
- `.\.venv\Scripts\python.exe manage.py check` → `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\pip.exe install -r requirements-dev.txt` → instalação concluída com sucesso (`Successfully installed PyYAML-6.0.2`), sem conflito com `requirements.txt`.

## Visual validation
Não aplicável.

## ORM validation
Não aplicável.

## Quality validation
- `rg requirements-dev`
- comando de check aplicável.

## Evidence
- Subagente confirmou referência a arquivo inexistente.
- `requirements.txt` lido integralmente: 49 dependências de produção, sem ferramenta de validação de governança (PyYAML) entre elas.
- PRD-059 já havia decidido criar `requirements-dev.txt` com PyYAML para o validador de skills, mas o arquivo nunca chegou a existir no working tree (provável perda antes do commit). Esta PRD reaplica essa decisão.

## Implemented
- Criado `requirements-dev.txt` na raiz com `-r requirements.txt` mais `PyYAML==6.0.2`, alinhado com a decisão registrada em PRD-059 (dependência usada pelo validador de skills).
- Substituído `README.md` (descrevia o kit de governança genérico/Cursor) por um README específico do LV JIU JITSU: produto, stack, estrutura `system/`, setup local, comandos úteis, governança de agentes e links de documentação coerentes com `CLAUDE.md` e `docs/OPERACAO-BANCO-SEEDS.md`.
- `CLAUDE.md` não foi alterado: a referência a `.\.venv\Scripts\pip.exe install -r requirements-dev.txt` (linha 59) agora aponta para um arquivo existente, então nenhuma correção era necessária ali.

## Cleanup findings
- Nenhum resíduo introduzido. Nenhum outro arquivo referenciava o README genérico ou dependia do conteúdo antigo.
- Não foi encontrado débito material adicional no escopo desta PRD que justifique novo PRD de follow-up.

## Follow-up PRDs
Nenhum.

## Deviations from plan
- Nenhum desvio do plano original da PRD.

## Pending
- Nenhuma pendência neste escopo. Instalação de `requirements-dev.txt` continua opcional e só necessária quando o ambiente local for executar o validador de skills (PyYAML), conforme já documentado em `docs/PLATFORM-ADAPTERS.md`.

## Final status
Concluída.
