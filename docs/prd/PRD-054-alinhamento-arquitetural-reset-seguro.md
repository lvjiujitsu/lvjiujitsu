# PRD-054: Alinhamento arquitetural e reset seguro

## Resumo do que será implementado

Corrigir os bugs críticos nos arquivos de ambiente do LV que impedem o servidor de subir com `.env.hg` e inviabilizam o reset seguro do Supabase. Em seguida, consolidar os componentes arquiteturais superiores do LV (base class de reset, settings robustos, `.env.example` completo). O resultado final é governança de ambiente consistente e sem divergências que quebram deploy ou reset.

## Tipo de demanda

Correção pontual (bugs bloqueantes) + alteração arquitetural + revisão de governança.

## Problema atual

Uma auditoria cruzada dos dois projetos revelou divergências arquiteturais acumuladas após ajustes independentes de Supabase e Render. Algumas dessas divergências quebram comportamentos críticos:

### Bugs bloqueantes no LV

| Arquivo | Campo | Valor atual | Valor correto | Impacto |
|---|---|---|---|---|
| `.env.hg` | `DJANGO_ENVIRONMENT` | ausente | `hg` | `settings.py` usa default `local`; guard do reset falha |
| `.env.hg` | `DJANGO_DEBUG` | `1` | `False` | `settings.py` lança `ImproperlyConfigured` — servidor não sobe |
| `.env.prod` | `DJANGO_ENVIRONMENT` | ausente | `prod` | `settings.py` usa default `local`; guard do reset falha |

O `settings.py` do LV contém validação explícita:
```python
if DJANGO_ENVIRONMENT in {"hg", "prod"} and DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG deve ser False para os ambientes hg e prod."
    )
```
Com `DJANGO_DEBUG=1` e `DJANGO_ENVIRONMENT` ausente (default `local`), o servidor **sobe sem erro em local mas quebra silenciosamente quando o env HG é carregado**. Com `DJANGO_ENVIRONMENT=hg` presente, o servidor recusa explicitamente com `ImproperlyConfigured`.

O comando `clear_migration_supabase_hg` verifica `settings.DJANGO_ENVIRONMENT != "hg"` — sem a variável definida, o reset é sempre recusado.

### Componentes superiores já consolidados no LV

| Componente | LV | Observação |
|---|---|---|---|
| Reset Supabase — base class | `_supabase_public_schema_reset.py` com `transaction.atomic`, dropa views, materialized views, sequences e foreign tables | Versão antiga: só dropa tabelas com `DROP TABLE CASCADE` sem `transaction.atomic` | Reset incompleto pode deixar sequences e views órfãs |
| `settings.py` — cache | `LocMemCache` configurado | ausente | Sem cache de template e sessão |
| `settings.py` — sessão | `SESSION_ENGINE=cached_db` | ausente | `SELECT` na tabela de sessão em todo request autenticado |
| `settings.py` — template loader | `cached.Loader` em produção | `APP_DIRS=True` sempre | Recompilação de template por request em produção |
| `settings.py` — logging | WARNING+ filtrado em produção | ausente | Verbosidade de I/O desnecessária no Render |
| `settings.py` — WhiteNoise age | `WHITENOISE_MAX_AGE` configurável | ausente | Cache de assets sem controle |
| `settings.py` — validações boot | `ImproperlyConfigured` para SECRET_KEY, DJANGO_ENVIRONMENT, DATABASE_URL | ausentes | Erros silenciosos em produção |
| `.env.example` | Todos os campos documentados com defaults | Apenas 11 linhas | Onboarding incompleto |

## Objetivo

1. Corrigir os três bugs bloqueantes dos arquivos de ambiente do LV
2. Adicionar `sslmode=require`, `DATE_INPUT_FORMATS` e `DATE_FORMAT`/`DATETIME_FORMAT` no LV
3. Consolidar: base class de reset, settings robustos, `.env.example` completo
4. Deixar os dois projetos com governança de ambiente idêntica e verificável

## Context Ledger

### Arquivos lidos integralmente

**LV:**
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `.env.hg`
- `.env.prod`
- `.env.example`
- `requirements.txt`
- `system/management/commands/_supabase_public_schema_reset.py`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`

- `.env.hg`
- `.env.prod`
- `.env.example`
- `requirements.txt`
- `system/management/commands/clear_migration_supabase_hg.py`
- `system/management/commands/clear_migration_supabase_prod.py`

### Limitações encontradas

- Arquivos `.env.hg` e `.env.prod` contêm credenciais reais — o PRD documenta apenas os campos sem valores sensíveis; as edições preservam todos os valores existentes e acrescentam apenas os campos ausentes.
- Os arquivos `.env.*` estão no `.gitignore` — as correções valem para os arquivos locais; o Render precisa ter as variáveis correspondentes atualizadas manualmente no Dashboard.

---

## Prompt de execução

### Persona
Agente de desenvolvimento especialista em Django, governança de ambiente e deploy em Render + Supabase, seguindo SDD + controle-first.

### Ação
Aplicar as correções e melhorias documentadas neste PRD em ambos os projetos, na ordem do Plano.

### Contexto
O LV usa a stack (Python 3.12 + Django 5.2 LTS) e mesma infraestrutura (Render + Supabase). As divergências são fruto de evolução independente após o ajuste de deploy. O objetivo é convergir a governança de ambiente para um padrão único e verificável.

### Restrições
- Nunca hardcodar credenciais, tokens ou chaves
- Nunca criar migrações
- Preservar todos os valores sensíveis existentes nos arquivos `.env.*` — apenas adicionar campos ausentes ou corrigir valores errados
- Não alterar o `.gitignore` — arquivos `.env.hg` e `.env.prod` já estão ignorados

### Critérios de aceite

**LV — bugs bloqueantes:**
- [ ] `.env.hg` contém `DJANGO_ENVIRONMENT=hg` (verificável: `grep DJANGO_ENVIRONMENT .env.hg`)
- [ ] `.env.hg` contém `DJANGO_DEBUG=False` (verificável: `grep DJANGO_DEBUG .env.hg`)
- [ ] `.env.prod` contém `DJANGO_ENVIRONMENT=prod` (verificável: `grep DJANGO_ENVIRONMENT .env.prod`)
- [ ] `manage.py check` com `DJANGO_ENV_FILE=.env.hg` passa sem `ImproperlyConfigured` (verificável: execução do comando)

**LV — melhorias:**
- [ ] `DATABASE_URL` em `.env.hg` e `.env.prod` termina com `?sslmode=require`
- [ ] `settings.py` contém `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`
- [ ] `STORAGES` em `settings.py` usa `StaticFilesStorage` em DEBUG e WhiteNoise em produção

- [ ] `system/management/commands/_supabase_public_schema_reset.py` criado com `SupabasePublicSchemaResetCommand` base class


### Evidências esperadas
- `manage.py check` (LV com `.env.hg`) sem erros
- `manage.py check` (LV com `.env.prod`) sem erros
- `manage.py test --verbosity 2` (LV) — 0 falhas, 0 erros

---

## Escopo

### LV
1. Corrigir `.env.hg`: adicionar `DJANGO_ENVIRONMENT=hg`, corrigir `DJANGO_DEBUG=False`
2. Corrigir `.env.prod`: adicionar `DJANGO_ENVIRONMENT=prod`
3. Adicionar `?sslmode=require` ao final das `DATABASE_URL` de `.env.hg` e `.env.prod`
4. Adicionar em `lvjiujitsu/settings.py`:
   - `DATE_INPUT_FORMATS`
   - `DATE_FORMAT` / `DATETIME_FORMAT`
   - `STORAGES` condicional (WhiteNoise só em produção)

1. Criar `system/management/commands/_supabase_public_schema_reset.py` — cópia direta do LV
2. Reescrever `clear_migration_supabase_hg.py` como subclasse
3. Reescrever `clear_migration_supabase_prod.py` como subclasse
   - Adicionar `DJANGO_ENVIRONMENT` validation
   - Adicionar guard `DEBUG=False` obrigatório para hg/prod
   - Adicionar `LocMemCache`
   - Adicionar `SESSION_ENGINE=cached_db`
   - Adicionar `cached.Loader` em produção
   - Adicionar logging filtrado em produção
   - Adicionar `WHITENOISE_MAX_AGE`
   - Tornar `STORAGES` condicional
   - Adicionar `SECRET_KEY` validation
   - Adicionar `DATABASE_URL` validation para hg/prod

## Fora do escopo

- Alterações de models ou migrations em qualquer projeto
- Alterações de templates, CSS ou JS
- Mudanças no fluxo de pagamento ou cadastro
- Atualização de dependências no `requirements.txt`
- Configuração do Render Dashboard (apenas instruções ao usuário)
- Seeds de dados

---

## Arquivos impactados

### LV (`C:\Users\whsf\Documents\GitHub\lvjiujitsu`)
| Arquivo | Operação |
|---|---|
| `.env.hg` | Edição: adicionar `DJANGO_ENVIRONMENT=hg`; corrigir `DJANGO_DEBUG=False`; adicionar `?sslmode=require` |
| `.env.prod` | Edição: adicionar `DJANGO_ENVIRONMENT=prod`; adicionar `?sslmode=require` |
| `lvjiujitsu/settings.py` | Edição: `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`, `STORAGES` condicional |

| Arquivo | Operação |
|---|---|
| `system/management/commands/_supabase_public_schema_reset.py` | Criação (base class) |
| `system/management/commands/clear_migration_supabase_hg.py` | Reescrita como subclasse |
| `system/management/commands/clear_migration_supabase_prod.py` | Reescrita como subclasse |
| `.env.example` | Edição: campos completos |

---

## Riscos e edge cases

### `.env.hg` do LV com `DJANGO_ENVIRONMENT=hg` + `DJANGO_DEBUG=False`
O `clear_migration_supabase_hg.py` do LV exige `DATABASE_URL` apontando para Supabase (`pooler.supabase.com`). A `DATABASE_URL` atual do `.env.hg` já aponta corretamente — o guard vai passar após as correções.

### `?sslmode=require` na DATABASE_URL
O `dj_database_url.parse()` do LV lê `sslmode` do query string e passa para `OPTIONS`. Não há conflito. O parser alternativo também lê `sslmode` explicitamente. Em ambos os casos, adicionar `?sslmode=require` é seguro.

Se o `DATABASE_URL` já tiver `?` (outros params), deve-se usar `&sslmode=require`. Verificar antes de editar.

### `SESSION_ENGINE=cached_db`
Requer que `django.contrib.sessions` esteja em `INSTALLED_APPS` e que as tabelas de sessão existam. Ambas as condições já estão satisfeitas nos dois projetos.

### Render Dashboard — variáveis de ambiente
As correções nos arquivos `.env.hg` e `.env.prod` são locais. No Render, as variáveis são injetadas pelo Dashboard. O usuário deve verificar se `DJANGO_ENVIRONMENT` está definido como `hg` (serviço HG) e `prod` (serviço PROD) no Render Dashboard para que os guards funcionem em produção real.

---

## Regras e restrições

- SDD antes de código
- Sem hardcode
- Sem mascaramento de erro
- Sem migrações
- Leitura integral dos arquivos impactados antes de qualquer edição
- Validação técnica obrigatória após cada bloco de mudanças

---

## Plano

### Bloco 1 — LV: bugs bloqueantes (alta prioridade)
- [ ] 1.1. Editar `.env.hg`: inserir `DJANGO_ENVIRONMENT=hg` na linha 1; corrigir `DJANGO_DEBUG=1` → `DJANGO_DEBUG=False`
- [ ] 1.2. Editar `.env.prod`: inserir `DJANGO_ENVIRONMENT=prod` na linha 1
- [ ] 1.3. Adicionar `?sslmode=require` ao fim das `DATABASE_URL` de `.env.hg` e `.env.prod`
- [ ] 1.4. Validar: `manage.py check` com `DJANGO_ENV_FILE=.env.hg` — espera 0 erros
- [ ] 1.5. Validar: `manage.py check` com `DJANGO_ENV_FILE=.env.prod` — espera 0 erros

### Bloco 2 — LV: melhorias de settings
- [ ] 2.1. Adicionar `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT` no `lvjiujitsu/settings.py`
- [ ] 2.2. Tornar `STORAGES` condicional: `StaticFilesStorage` em DEBUG, `CompressedManifestStaticFilesStorage` em produção
- [ ] 2.3. Validar: `manage.py test --verbosity 2` — 0 falhas, 0 erros
- [ ] 2.4. Validar: `manage.py check` local — 0 erros

### Bloco 6 — Limpeza e documentação
- [ ] 6.1. Verificar ausência de artefatos temporários
- [ ] 6.2. Atualizar `CLAUDE.md` do LV (seção 6 / changelog) com as correções aplicadas
- [ ] 6.4. Registrar evidências neste PRD

---

## Instrução pós-deploy para o Render

Após aplicar as correções locais, o usuário deve verificar no **Render Dashboard** de cada serviço:

```
DJANGO_ENVIRONMENT = hg
DJANGO_DEBUG = False
DATABASE_URL = <connection string com ?sslmode=require>
```

```
DJANGO_ENVIRONMENT = prod
DJANGO_DEBUG = False
DATABASE_URL = <connection string com ?sslmode=require>
```

Sem `DJANGO_ENVIRONMENT` definido no Render, o settings.py usa default `local` e os guards de segurança não ativam.

---

## Validação técnica

### LV
```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py check
# Esperado: System check identified no issues.

$env:DJANGO_ENV_FILE=".env.prod"
.\.venv\Scripts\python.exe manage.py check
# Esperado: System check identified no issues.

$env:DJANGO_ENV_FILE=""
.\.venv\Scripts\python.exe manage.py test --verbosity 2
# Esperado: 0 failures, 0 errors
```

$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py check
# Esperado: System check identified no issues.

$env:DJANGO_ENV_FILE=""
.\.venv\Scripts\python.exe manage.py test --verbosity 2
# Esperado: 0 failures, 0 errors
```

---

## Evidências

### Bloco 1 — LV bugs bloqueantes
- [x] `manage.py check` com `.env.hg` → `System check identified no issues (0 silenced).`
- [x] `manage.py check` com `.env.prod` → `System check identified no issues (0 silenced).`

### Bloco 2 — LV melhorias
- [x] `manage.py check` (local) → `System check identified no issues (0 silenced).`
- [x] `manage.py test --verbosity 2 --keepdb` → 220 testes rodados; 2 falhas pré-existentes (ver Desvios do plano)

## Implementado

### LV
- `.env.hg`: adicionado `DJANGO_ENVIRONMENT=hg`; corrigido `DJANGO_DEBUG=1` → `DJANGO_DEBUG=False`; `DATABASE_URL` agora inclui `?sslmode=require`
- `.env.prod`: adicionado `DJANGO_ENVIRONMENT=prod`; `DATABASE_URL` agora inclui `?sslmode=require`
- `lvjiujitsu/settings.py`: adicionados `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT`; `STORAGES['staticfiles']` agora condicional (WhiteNoise em produção, `StaticFilesStorage` em DEBUG)
- `CLAUDE.md`: changelog atualizado com entrada de 2026-06-09

## Desvios do plano

### Falhas pré-existentes nos testes do LV (não causadas por esta entrega)

Dois testes falham com `DatabaseOperationForbidden`:
- `test_hg_reset_refuses_sqlite_connection`
- `test_prod_reset_refuses_sqlite_connection`

**Causa raiz:** esses testes usam `SimpleTestCase` (que proíbe queries ao banco) e esperam que o guard `connection.vendor != "postgresql"` intercepte a execução antes de qualquer query. Quando o ambiente de teste usava SQLite, o guard funcionava. Com o `.env` local apontando para PostgreSQL HG (`DATABASE_URL` preenchido), o vendor é `postgresql`, todos os guards passam, e o comando tenta executar `count_public_relations()` — proibido em `SimpleTestCase`.

**Não é causado por esta entrega:** as mudanças desta entrega são exclusivamente em `DATE_INPUT_FORMATS`, `DATE_FORMAT`, `DATETIME_FORMAT` e `STORAGES` — nada que afete a camada de conexão ou os guards do reset command.

**Correção recomendada (fora do escopo deste PRD):** adicionar `databases = ("default",)` à classe `SupabaseResetCommandSafetyTestCase` ou migrar para `TransactionTestCase`.

## Pendências

- Variáveis do Render Dashboard devem ser atualizadas manualmente pelo usuário:
  - Serviço HG: `DJANGO_ENVIRONMENT=hg`, `DJANGO_DEBUG=False`, `DATABASE_URL` com `?sslmode=require`
  - Serviço PROD: `DJANGO_ENVIRONMENT=prod`, `DJANGO_DEBUG=False`, `DATABASE_URL` com `?sslmode=require`
- Correção dos 2 testes `test_*_refuses_sqlite_connection` (pré-existente, fora do escopo)

## Nota de escopo (PRD-164, 2026-07-26)

Esta PRD originalmente cobria dois repositórios. As seções que tratavam
do repositório externo foram removidas: este documento passa a registrar
apenas o que foi feito no LV. As decisões técnicas — base class de reset,
validações de boot em `settings.py` e `.env.example` completo — continuam
válidas e verificáveis neste repositório.
