# PRD-023: Seeds opcionais, `.env` orquestrador, dados iniciais em JSON

> Substituido por PRD-024-governanca-seeds-atomicas. Este PRD nao deve guiar novas mudancas.

## Resumo do que será implementado

Orquestração via `.env` (`SEED_DATA_ROOT`, `SEED_STRICT`, `SEED_ENABLE_*`), dados volumosos em `config/initial_data/*.json`, carregamento em `system/services/initial_load/`, comandos `seed_*` com no-op quando desligados. Runtime (views/services) continua só no ORM; sem seeds o sistema sobe vazio e cadastros manuais funcionam.

## Tipo de demanda

Alteração arquitetural / governança de dados iniciais.

## Problema atual

`bootstrap.py` concentra tuplos gigantes; preços de plano/produto já usam `.env`, mas o restante do conteúdo inicial permanece em código Python.

## Objetivo

- `.env` define **onde** e **se** carregar dados iniciais.
- JSON versionado é a fonte de conteúdo (não listas no `.env`).
- Seeds são **opcionais**; `migrate` + app sem seeds não quebra fluxos atômicos existentes.

## Context Ledger

### Arquivos lidos integralmente

- [system/services/seeding/bootstrap.py](c:/Users/whsf/Documents/GitHub/lvjiujitsu/system/services/seeding/bootstrap.py) (trechos de definições e funções `seed_*`)
- [lvjiujitsu/settings.py](c:/Users/whsf/Documents/GitHub/lvjiujitsu/lvjiujitsu/settings.py)
- [system/services/registration.py](c:/Users/whsf/Documents/GitHub/lvjiujitsu/system/services/registration.py) (`ensure_default_person_types`)

### Limitações

- `seed_person_types` continua em `registration` + `constants` (fora do escopo deste PRD se não houver JSON dedicado).
- Migrações: sem novas salvo necessidade explícita.

## Critérios de aceite

- [ ] `SEED_ENABLE_CLASS_CATEGORIES=0` → `seed_class_categories` imprime skip e não grava.
- [ ] Com `SEED_STRICT=1` e ficheiro JSON em falta → comando falha com mensagem clara.
- [ ] Com defaults, `config/initial_data/` presente no repo e seeds produzem o mesmo resultado funcional que antes (testes).
- [ ] `manage.py check` e `manage.py test system.tests` passam.
- [ ] `.env.example` documenta `SEED_DATA_ROOT` e toggles.

## Escopo

- Pacote `initial_load`, JSONs, settings, refatoração de `bootstrap` para ler JSON e normalizar enums.
- Comandos `seed_*` com guard no início.
- Atualização de [CLAUDE.md](c:/Users/whsf/Documents/GitHub/lvjiujitsu/CLAUDE.md).

## Fora do escopo

- Mover `DEFAULT_PERSON_TYPE_DEFINITIONS` para JSON.
- Validação visual completa do wizard (smoke manual opcional).

## Plano de execução (resumo)

1. Gerar JSON a partir do estado atual (script one-shot versionado ou equivalente).
2. Implementar loaders + normalização de strings para `CategoryAudience`, `WeekdayCode`, `TrainingStyle`.
3. Externalizar `teacher_payroll` para JSON.
4. Remover tuplos de `bootstrap.py`; manter funções transacionais.
5. Toggles + PRD + CLAUDE + testes.

## Evidências esperadas

- Testes automatizados verdes.
- Lista de chaves `.env` no `.env.example`.
