# PRD-149: Requirements único — eliminar `requirements-dev.txt`

## Summary
Consolidar dependências em um único `requirements.txt` (incluindo `PyYAML`) e remover `requirements-dev.txt`, alinhando onboarding local e build do Render ao mesmo arquivo. A decisão baseia-se em evidência oficial: no Free do Render, o custo de instalar PyYAML é desprezível frente aos 512 MB RAM.

## Demand type
Configuração de dependências + governança documental.

## Current problem
- Existiam dois arquivos: `requirements.txt` (produção / Render) e `requirements-dev.txt` (`-r requirements.txt` + `PyYAML==6.0.2`).
- A separação foi introduzida por PRD-059 / PRD-082 para isolar PyYAML (validador de skills) do deploy.
- Isso gerava atrito de onboarding (`CLAUDE.md` e `README.md` pediam caminhos diferentes) sem benefício mensurável no Free do Render.
- Havia dúvida se PyYAML no Free “enfraquecia” o serviço.

## Goal
- Um único arquivo de dependências: `requirements.txt`.
- Documentação e comandos locais/deploy referenciando apenas esse arquivo.
- Decisão registrada com fontes oficiais sobre impacto no Render Free.
- Remover `requirements-dev.txt` sem regressão no validador de skills (PyYAML permanece via `requirements.txt`).

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `requirements.txt`
- `requirements-dev.txt`
- `docs/PRD-STANDARD.md`
- `docs/prd/PRD-082-readme-requirements-dev-governanca.md` (decisão anterior)
- trechos relevantes de `docs/prd/PRD-059-governanca-agentes-multiplataforma.md`

### Adjacent files consulted
- `docs/OPERACAO-BANCO-SEEDS.md` (build Render)
- `docs/prd/README.md` (número 149)
- `.github/workflows/copilot-setup-steps.yml` (já usava só `requirements.txt`)
- busca `requirements-dev` / `PyYAML` / `import yaml` no repo

### Internet / official documentation
| Fonte | Conclusão | Limitação |
|---|---|---|
| [Render — Deploy for Free](https://render.com/docs/free) | Free web service: **512 MB RAM / 0.1 CPU**; spin-down 15 min; limites de bandwidth e pipeline minutes. Doc **não** cita PyYAML nem restrição a pacotes Python específicos. | Problemas de OOM no Free são genéricos (heap da app, seeds pesadas, workers múltiplos), não atribuídos a um pacote leve. |
| [Render — Instance Types](https://render.com/docs/compute-plans) / [Pricing](https://render.com/pricing) | Confirma Free = 512 MB / 0.1 CPU. | Não detalha footprint por dependência pip. |
| [PyPI — PyYAML](https://pypi.org/project/PyYAML/) | Wheel `PyYAML 6.0.2` ≈ **184 KB**; `6.0.3` ≈ 184 KB. Pacote mínimo. | Tamanho do wheel ≠ RSS em runtime se o código fizer `yaml.load` de arquivos enormes. |
| [SO — MemoryError com PyYAML](https://stackoverflow.com/questions/40422307/python-yaml-returns-memoryerror) | Consumo alto ocorre ao **parsear YAML grande** (ordem de dezenas de MB de arquivo → GB de RAM). | Irrelevante se PyYAML só está instalado e o runtime Django/Gunicorn **não** importa/parseia YAML em produção. |
| Relatos comunitários OOM no Free | OOM típico: LangChain/ONNX, seeds no boot, múltiplos workers — stacks centenas de MB. | Nenhum relato encontrado ligando OOM do Free à **mera instalação** de PyYAML. |

**Síntese para decisão:** no LV, PyYAML serve ao validador de skills (tooling local). Não há uso de YAML no path de request de `system/`. Instalar PyYAML no build do Render **não faz diferença material** em RAM/CPU do Free; o risco do Free continua sendo o envelope 512 MB da app (Django + Gunicorn + Pillow etc.), não esse pacote ~184 KB.

### Context7 / MCPs / tools verified
- Context7 `/yaml/pyyaml`: PyYAML ≥ Python 3.8; instalação via pip; uso tipicamente `yaml.safe_load` / `safe_dump`.
- Shell local: `PyYAML 6.0.2` presente na `.venv`.
- WebSearch + WebFetch da doc Render Free.

### Limitations found
- Não foi medido RSS do processo Gunicorn no Render Free antes/depois (exigiria deploy e Dashboard; fora do escopo local).
- PRD-059/082 permanecem históricas; esta PRD substitui a decisão operacional de separar prod/dev.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Solicitação atual autorizou: pesquisa + PRD + unificar em um único `requirements.txt` e atualizar referências.

## Execution prompt
### Persona
Agente de configuração/governança LV.
### Action
Mover `PyYAML==6.0.2` para `requirements.txt`; apagar `requirements-dev.txt`; atualizar `CLAUDE.md`, `README.md` e índice de PRDs.
### Context
Render build já usa `pip install -r requirements.txt`. CI Copilot já usa só esse arquivo.
### Constraints
Não alterar outras pins; não tocar HG/produção além do próximo deploy; não introduzir ferramentas extras neste escopo.
### Acceptance criteria
Arquivo único; docs alinhados; checks locais ok; `rg` limpo fora de PRDs históricas.
### Expected evidence
Diff, `pip install` / `pip check`, `manage.py check`, `rg requirements-dev`.
### Output format
PRD atualizada + arquivos tocados.

## Scope
- Adicionar `PyYAML==6.0.2` a `requirements.txt`.
- Remover `requirements-dev.txt`.
- Atualizar comandos em `CLAUDE.md` e `README.md`.
- Indexar esta PRD em `docs/prd/README.md`.
- Registrar decisão e pesquisa Render Free / PyYAML.

## Out of scope
- Mudar pin de qualquer outra dependência.
- Adicionar suite de lint/test tools ao requirements.
- Deploy / alteração no Dashboard Render.
- Reescrever PRD-059 / PRD-082.
- Medição de RSS em HG/produção.

## Impacted files
- `requirements.txt`
- `requirements-dev.txt` (removido)
- `CLAUDE.md`
- `README.md`
- `docs/prd/PRD-149-requirements-unico-sem-dev.md`
- `docs/prd/README.md`

## Risks and edge cases
- Se no futuro o runtime passar a parsear YAML grande via PyYAML sob Gunicorn no Free, o risco deixa de ser “só instalação” — hoje isso não ocorre.
- Referências órfãs → mitigadas; só PRDs históricas citam `requirements-dev`.

## Rules and constraints
- Menor mudança correta.
- Uma fonte de verdade de deps para local e Render.
- Pin explícita `PyYAML==6.0.2`.

## Plan
- [x] Pesquisar Render Free + PyYAML (fontes oficiais/PyPI).
- [x] Mover PyYAML para `requirements.txt`.
- [x] Remover `requirements-dev.txt`.
- [x] Atualizar `CLAUDE.md` e `README.md`.
- [x] Atualizar índice `docs/prd/README.md`.
- [x] Validar com `pip install` / `manage.py check` / `rg`.
- [x] Auditoria de limpeza (`lv-cleanup-audit`).

## Test plan
### Tests to author
Não aplicável (sem mudança de comportamento Django).

### Execution authorization
Comandos locais autorizados pelo prompt atual.

### Execution evidence
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` → todas as deps satisfied, inclusive `PyYAML==6.0.2` (linha 37).
- `.\.venv\Scripts\python.exe -m pip check` → `No broken requirements found.`
- `.\.venv\Scripts\python.exe manage.py check` → `System check identified no issues (0 silenced).`
- `Test-Path requirements-dev.txt` → `False`.
- Nota: `pip.exe` direto bloqueado por App Control no Windows; uso de `python -m pip` como workaround válido.
- `rg requirements-dev` → apenas PRDs históricas (059, 082, 139, AUDIT) + esta PRD + entrada de índice; `CLAUDE.md`/`README.md` limpos.

## Visual validation
Não aplicável.

## ORM validation
Não aplicável.

## Quality validation
- Diff: +`PyYAML==6.0.2` em `requirements.txt`; remoção de `requirements-dev.txt`; docs apontam só `requirements.txt`.

## Evidence
### Pesquisa
- Render Free: 512 MB / 0.1 CPU — [docs/free](https://render.com/docs/free).
- PyYAML wheel ≈ 184 KB — [PyPI](https://pypi.org/project/PyYAML/).
- Conclusão: **não faz diferença prática** instalar PyYAML no Free; OOM do Free vem de apps/pesos grandes, não deste pacote.

### Implementação
- `git diff --stat`: `CLAUDE.md`, `README.md`, `docs/prd/README.md`, `requirements.txt` (+1), `requirements-dev.txt` (deleted).

## Implemented
- `PyYAML==6.0.2` em `requirements.txt`.
- `requirements-dev.txt` removido.
- `CLAUDE.md` e `README.md` usam apenas `requirements.txt`.
- Índice PRD atualizado com PRD-149.
- Obsidian `projetos/comandos-powershell-lvjiujitsu.md` alinhado (matriz 04, A00, B04, §E, paridade, fontes).
- Claude MEMORY: entrada `feedback_requirements_unico.md` + link no `MEMORY.md`.

## Cleanup findings
- Nenhuma referência ativa órfã a `requirements-dev.txt` fora de documentação histórica (PRDs 059/082/139).
- Skills `lv-*` e Cursor rules não citavam `requirements-dev` — sem alteração necessária.
- Documentação externa (Obsidian + MEMORY) corrigida após lacuna identificada.

## Follow-up PRDs
Nenhum.

## Deviations from plan
- `pip.exe` bloqueado por política App Control; validação via `python -m pip` (mesmo efeito).

## Pending
Nenhuma.

## Final status
**Concluída** (com limitação: RSS no Render Free não medido pós-deploy; irrelevante para a decisão dada o tamanho do pacote e ausência de parse YAML no runtime).
