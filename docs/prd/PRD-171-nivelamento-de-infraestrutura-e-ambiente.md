# PRD-171: Nivelamento de infraestrutura e ambiente

## Summary

Dependências, `.gitignore`, workflow de agente e conjunto de chaves de ambiente
nivelados entre os projetos do mesmo eixo. O achado de maior consequência foi no
`LOGGING`: ele existia apenas dentro de `if not DEBUG:`, então o ambiente local
rodava **sem configuração de log nenhuma**. Cinco itens de convergência de código
ficaram de fora e estão em `Pending`.

## Demand type

Configuração e dependência. Sem mudança de regra de negócio, sem mudança de
schema, sem mudança visual.

## Current problem

- `requirements.txt` fixava `PyYAML==6.0.2`, atrás do `6.0.3` já em uso nos
  projetos do eixo, e trazia comentários de agrupamento que o padrão do eixo não
  usa.
- **`LOGGING` estava dentro de `if not DEBUG:`.** Em local, com `DEBUG=True`, o
  Django caía na configuração padrão: sem formatter próprio, sem nível
  controlado e sem tratamento para `django.db.backends`. O nível também estava
  hardcoded em `'WARNING'`, sem variável de ambiente.
- `settings.py` lia `CACHE_TIMEOUT` e `WHITENOISE_MAX_AGE`, mas **nenhum dos
  quatro arquivos de ambiente declarava essas chaves**: o código dependia de
  chave que o contrato de ambiente não previa.
- `.env` declarava `DJANGO_DEBUG=1` em vez de `True`, divergindo da convenção dos
  projetos do eixo.
- `.gitignore` tinha 28 linhas e faltavam entradas que os três precisam
  (`pytest-cache-files-*/`, `tmp_*.py`, `.codex-runtime/` — as duas últimas já
  usadas aqui).
- `.github/workflows/copilot-setup-steps.yml` existia só aqui, e o comentário
  citava uma PRD deste repositório, o que impedia o espelhamento literal.
- `.env.example` não explicava por que `SUPABASE_RESET_CONFIRM` não aparece ali,
  o que convidava a "corrigir" a ausência e desarmar a guarda do reset remoto.

## Goal

Para cada pacote presente em mais de um projeto do eixo, a versão fixada é a
mesma string. `LOGGING` vale em qualquer ambiente e o nível vem do ambiente. Cada
chave de ambiente declarada é lida por alguém, e cada leitor tem chave declarada.

## Context Ledger

### Files read in full

- `requirements.txt`, `.gitignore`
- `lvjiujitsu/settings.py`
- `.env`, `.env.example`, `.env.hg`, `.env.prod` — nomes de chave e valores
  não-secretos
- `.github/workflows/ci.yml`, `.github/workflows/copilot-setup-steps.yml`

### Adjacent files consulted

- `clear_migrations.py` — comparação do encerramento de processos
- `system/services/stripe_*.py` — para confirmar que `stripe` é importado de fato
- `system/tests/test_settings_hosts.py`

### Internet / official documentation

- python-decouple, precedência e `cast`:
  https://pypi.org/project/python-decouple/
- Django 5.2, referência de `LOGGING` e `django.db.backends`:
  https://docs.djangoproject.com/en/5.2/ref/logging/

### Context7 / MCPs / tools verified

- Context7 não foi consultado: as versões vieram de `pip install` real e de
  `pip check`, que são a fonte mais confiável do que resolve neste ambiente.

### Limitations found

- `python-decouple` **não** cai no `default` quando a chave existe com valor
  vazio: devolve string vazia. Isso quebrou o boot deste projeto durante a
  execução e está em `Deviations from plan`.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: plano de seis etapas, com a Etapa 4 descrita item a item.
- User approval: "continue".
- Date: 2026-07-26.

## Execution prompt

### Persona

Engenheiro responsável pela infraestrutura local e de deploy do repositório.

### Action

Unificar dependências, `.gitignore`, workflow de agente e conjunto de chaves de
ambiente, e tornar o `LOGGING` incondicional e configurável.

### Context

MVP descartável. Ambiente local recriável. Nenhuma chave declarada pode ficar
sem leitor, e nenhum leitor pode depender de chave não declarada.

### Constraints

- versão fixada igual para pacote presente em mais de um projeto;
- só dependência direta em `requirements.txt`;
- nenhum valor de segredo escrito em arquivo de ambiente ou nesta PRD;
- `SUPABASE_RESET_CONFIRM` **não** pode ser declarada em arquivo de ambiente;
- suíte verde depois de qualquer mudança de dependência ou de logging.

### Acceptance criteria

- [x] `requirements.txt` com dependências diretas, alfabético, sem comentário;
- [x] versão idêntica para todo pacote comum ao eixo;
- [x] `pip check` limpo;
- [x] `LOGGING` definido em qualquer ambiente, com nível vindo de
      `DJANGO_LOG_LEVEL` e `django.db.backends` em `INFO`;
- [x] `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE` e `DJANGO_LOG_LEVEL` declaradas nos
      quatro arquivos;
- [x] `.env` com `DJANGO_DEBUG=True`;
- [x] `.gitignore` com variante única após normalização;
- [x] `copilot-setup-steps.yml` idêntico nos três;
- [x] `SUPABASE_RESET_CONFIRM` ausente dos quatro arquivos, com o motivo
      documentado em `.env.example`;
- [x] `check`, `makemigrations --check --dry-run`, índice, skills, `pip check` e
      suíte completa verdes;
- [ ] convergência de `clear_migrations.py` e dos comandos de infra — **não
      entregue**, ver `Pending`.

### Expected evidence

Saída de `pip install`, `pip check`, contagem de chaves por arquivo de ambiente,
variantes por arquivo e suíte completa.

### Output format

Diff e PRD atualizada com evidência.

## Scope

- `requirements.txt`
- `.gitignore`
- `.github/workflows/copilot-setup-steps.yml`
- `lvjiujitsu/settings.py` — bloco de logging
- `.env`, `.env.example`, `.env.hg`, `.env.prod`

## Out of scope

- Convergência de `clear_migrations.py` e dos cinco comandos de infra.
- Criação de um `seed_test_data` único para fechar o par com `clear_test_data`.
- `docs/UI-SCREEN-CONTRACT.md` e tokens CSS.
- Remoção de comentários e docstrings.
- `docs/archive/static-documentation-legacy/` e os três guias de wizard.
- Troca das aspas simples de `settings.py` por aspas duplas.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `requirements.txt` | 20 linhas com comentário → 10 dependências diretas, alfabéticas; `PyYAML` 6.0.2 → 6.0.3 |
| `.gitignore` | 28 → 32 linhas, com as três entradas comuns acrescentadas |
| `.github/workflows/copilot-setup-steps.yml` | referência a PRD local removida do comentário, para permitir espelhamento literal |
| `lvjiujitsu/settings.py` | `LOGGING` sai de `if not DEBUG:` e passa a valer sempre; `LOG_LEVEL` vem de `DJANGO_LOG_LEVEL`; `django.db.backends` fixado em `INFO`; handler `null` em `DEBUG` |
| `.env`, `.env.example`, `.env.hg`, `.env.prod` | ganham `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE` e `DJANGO_LOG_LEVEL`; 68 → 71 chaves em cada |
| `.env` | `DJANGO_DEBUG=1` → `DJANGO_DEBUG=True` |
| `.env.example` | nota explicando por que `SUPABASE_RESET_CONFIRM` não é declarada |

## Risks and edge cases

- Tornar o `LOGGING` incondicional muda o comportamento **em local**, onde antes
  não havia configuração. Para não trocar silêncio por ruído, o handler em
  `DEBUG` é `null` e `django.db.backends` fica em `INFO`: o volume de saída local
  continua igual, mas agora por decisão declarada e não por ausência de
  configuração.
- `DJANGO_DEBUG=1` e `True` são equivalentes para o `cast=bool` do decouple, então
  a troca é de convenção, não de comportamento.
- Chave declarada com valor vazio quebra o boot quando há `cast`. Foi exatamente
  o que aconteceu aqui, registrado abaixo.
- `stripe==15.0.1` e `requests==2.33.1` permanecem: os dois têm importador
  confirmado no código.

## Rules and constraints

- `AGENTS.md` §10: segredo nunca impresso; ao ler env, reportar nome de chave.
- `AGENTS.md` §11: guardas do ciclo destrutivo não podem ser enfraquecidas.
- `AGENTS.md` §12: dívida material fora do escopo vira follow-up.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste novo. A suíte de 769 casos é o guarda-corpo da mudança de
dependência e de logging, e `manage.py check` foi o que revelou o erro de chave
vazia.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python -m pip install -r requirements.txt
Requirement already satisfied: Django==5.2.14
Successfully installed PyYAML-6.0.3
exit=0

python -m pip check
No broken requirements found.
exit=0

python -c "import django; print(django.get_version())"
5.2.14
```

Erro observado antes da correção do valor vazio:

```text
python manage.py check
ValueError: invalid literal for int() with base 10: ''
exit=1
```

Depois da correção:

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0

python manage.py test
Ran 769 tests in 390.727s
OK
exit=0
```

## Visual validation

### Design approval

Não aplicável: nenhuma mudança visual.

### Routes and states

Não aplicável: nenhuma rota alterada.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

`manage.py check` sem aviso. O volume de saída local não mudou, porque o handler
em `DEBUG` é `null`.

### Screenshot / snapshot

Não aplicável.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

Nenhuma escrita executada.

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
pip check                           -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Versões fixadas, iguais nos três projetos do eixo:

```text
dj-database-url==3.1.2   Django==5.2.14        gunicorn==26.0.0
psycopg2-binary==2.9.12  python-decouple==3.8  PyYAML==6.0.3
tzdata==2026.1           whitenoise==6.12.0
```

Diretas exclusivas deste projeto, com importador confirmado: `requests==2.33.1`
e `stripe==15.0.1`.

Conjunto de chaves de ambiente (`.env` / `.env.example` / `.env.hg` /
`.env.prod`):

```text
lvjiujitsu   71/71/71/71   conjunto identico: True
```

`SUPABASE_RESET_CONFIRM` declarada em 0 arquivos, como deve ser.

Variantes após normalização: `.gitignore` = 1 (as duas linhas de importação
histórica são cauda de projeto), `copilot-setup-steps.yml` = 1.

## Implemented

- `requirements.txt` com 10 dependências diretas, alfabético e sem comentário;
- `LOGGING` incondicional, com nível vindo do ambiente, handler `null` em
  `DEBUG` e `django.db.backends` em `INFO` — o ambiente local deixa de rodar sem
  configuração de log;
- `CACHE_TIMEOUT`, `WHITENOISE_MAX_AGE` e `DJANGO_LOG_LEVEL` declaradas nos
  quatro arquivos, fechando a lacuna entre o que o código lê e o que o contrato
  de ambiente prevê;
- `DJANGO_DEBUG=True` no `.env`;
- `.gitignore` com as três entradas comuns;
- `copilot-setup-steps.yml` espelhável e presente nos três;
- `.env.example` explicando por que `SUPABASE_RESET_CONFIRM` não mora ali.

## Cleanup findings

- `clear_migrations.py` daqui é a implementação mais segura do eixo — `taskkill
  /F` sem `/T` e espera de até 8 segundos — e deve ser a baseline da convergência
  em `Pending`.
- Não existe `seed_test_data`: o par com `clear_test_data` é feito por quatro
  seeds `seed_system_initial_test_*`, o que difere dos projetos do eixo.
- `settings.py` usa aspas simples enquanto os demais arquivos do eixo usam aspas
  duplas.
- `system/tests/test_class_catalog.py` tem 0 linhas.
- `docs/archive/static-documentation-legacy/` guarda 12 documentos substituídos,
  e `docs/prd/AUDIT-2026-06-30-master-findings.md` obriga o gerador do índice a
  manter uma exceção nomeada.
- A branch local `stage` não tem remoto correspondente; o remoto é
  `origin/stage-visual`.
- `.claude/settings.local.json` duplica exatamente `settings.json`.

## Follow-up PRDs

- Convergência de `clear_migrations.py` e dos comandos de infra
  (`_supabase_public_schema_reset`, `lock_supabase_api_access`,
  `create_admin_superuser`, `clear_test_data`, `clear_migration_supabase_*`),
  usando a implementação deste projeto como baseline do encerramento de
  processos.
- Nivelamento de `docs/UI-SCREEN-CONTRACT.md` e convergência dos tokens CSS.
- Etapas seguintes já acordadas: estrutura e limpeza de comentários e
  docstrings.

## Deviations from plan

Três.

**Acrescentar as chaves com valor vazio quebrou o boot deste projeto.**
`python-decouple` devolve string vazia quando a chave existe sem valor, em vez de
cair no `default`, e `CACHE_TIMEOUT=` com `cast=int` levantou `ValueError:
invalid literal for int() with base 10: ''`, com `manage.py check` em exit 1.
Descoberto pelo próprio gate e corrigido preenchendo valor real nos quatro
arquivos.

**A auditoria que originou esta etapa afirmava que este projeto não tinha bloco
`LOGGING`. Estava errada, e a realidade era pior:** o bloco existia, mas só
dentro de `if not DEBUG:`, então o ambiente local rodava com a configuração
padrão do Django. A busca inicial usou âncora de início de linha e não encontrou
o bloco indentado.

**A auditoria também afirmava que `SUPABASE_RESET_CONFIRM` faltava nos
`.env.example` e devia ser acrescentada. Estava errada.** Persistir o valor em
arquivo de ambiente deixaria a guarda do reset remoto permanentemente satisfeita.
A ausência é a guarda; o que faltava era a explicação.

## Pending

Cinco itens de convergência de código, todos de infraestrutura e nenhum de
regra de negócio:

1. **`clear_migrations.py`** — encerramento de processos divergente entre os
   três; a implementação deste projeto é a baseline recomendada.
2. **Cinco comandos de infra** com 2 a 3 variantes:
   `_supabase_public_schema_reset`, `lock_supabase_api_access`,
   `create_admin_superuser`, `clear_test_data`, `clear_migration_supabase_hg` e
   `_prod`.
3. **Par seed/clear** — criar `seed_test_data` aqui ou converter os projetos do
   eixo para o modelo de seeds `test_*`; é decisão de produto, não mecânica.
4. **Política de seed no `/reset-local`** — obrigatória em um projeto do eixo,
   opcional aqui.
5. Os achados de limpeza acima que dependem de decisão do operador: remoto da
   branch e `settings.local.json`.

Não foram entregues por decisão de escopo: são mudanças de comportamento no
ciclo destrutivo e nos comandos remotos, e cada uma precisa de leitura integral
das três implementações mais teste próprio.

## Final status

Concluída com limitações. Dependências, `.gitignore`, workflow de agente e
conjunto de chaves de ambiente nivelados, `LOGGING` corrigido para valer em
qualquer ambiente, e suíte de 769 casos verde. Cinco itens de convergência de
código ficaram registrados em `Pending`.
