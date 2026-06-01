# PRD-053: Render Supabase Reset Seguro

## Resumo do que será implementado
Preparar o projeto para deploy manual no Render com Supabase HG e PROD, removendo automações frágeis de deploy, adicionando leitura explícita de arquivos de ambiente e criando comandos destrutivos seguros para limpar o schema `public` dos bancos remotos.

## Tipo de demanda
Alteração arquitetural, integração externa, revisão de segurança e regeneração documental.

## Problema atual
O deploy está parcialmente automatizado por arquivos frágeis (`render.yaml`, `build.sh`, `bootstrap.py`) que não refletem o fluxo desejado. O `bootstrap.py` mascara falhas de seeds, o `render.yaml` usa variáveis desalinhadas com `settings.py`, e o projeto não tem comandos auditáveis para reset remoto de HG/PROD.

## Objetivo
Deixar o repositório como fonte confiável do comportamento da aplicação e deixar o Render configurado manualmente no dashboard. O reset remoto deve exigir ambiente correto, confirmação explícita e validação observável antes de qualquer deploy com banco limpo.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `.env.example`
- `system/tests/test_commands.py`
- `system/management/commands/bootstrap.py`
- `system/management/commands/create_admin_superuser.py`
- `render.yaml`
- `build.sh`

### Arquivos adjacentes consultados
- `system/management/commands/`
- `docs/prd/`

### Internet / documentação oficial
- Django downloads/supported versions — Django 5.2 LTS 5.2.14 com suporte estendido ate abril de 2028.
- Django 5.2 release notes — Django 5.2 e LTS.
- Render free instances — free web service sem shell/one-off jobs.
- Render deploys — pre-deploy command disponivel para planos pagos/private/background workers.
- Supabase connect to Postgres — session pooler para trafego persistente de aplicacao.
- Supabase backups — free tier exige dumps/logical backups externos.

### MCPs / ferramentas verificadas
- Supabase skill — lida — aplicada para regras de reset e seguranca.
- Context7 — indisponivel por token OAuth expirado em verificacao anterior; fallback em documentacao oficial web.

### Limitações encontradas
- O agente nao deve inserir, exibir ou copiar segredos de `.env.hg`/`.env.prod` para Render.
- O agente nao deve executar reset destrutivo remoto sem intervencao do usuario.
- O Render free nao fornece shell/one-off jobs para rodar comandos depois do deploy.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django, Render e Supabase seguindo SDD + TDD + operacao control-first.

### Ação
Implementar o fluxo de deploy manual Render + reset seguro Supabase HG/PROD seguindo a spec abaixo.

### Contexto
O sistema deve subir como casca sem seeds obrigatorias. Dados iniciais e legados devem ser carregados apenas por comandos manuais e auditaveis.

### Restrições
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatoria
- validacao obrigatoria
- nao executar reset remoto sem autorizacao humana
- nao commitar sem autorizacao humana

### Critérios de aceite
- [x] `render.yaml`, `build.sh` e `bootstrap.py` removidos do fluxo versionado (verificavel por `git status`).
- [x] `settings.py` suporta `DJANGO_ENV_FILE` e falha se arquivo explicitamente configurado nao existir (verificavel por teste/comando).
- [x] `DJANGO_ENVIRONMENT` existe e aceita `local`, `hg` ou `prod` (verificavel por `manage.py check`).
- [x] `requirements.txt` fixa Django 5.2 LTS (verificavel por leitura e `pip show Django`).
- [x] `clear_migration_supabase_hg` recusa SQLite, `DEBUG=True`, ambiente diferente de `hg` e confirmacao ausente (verificavel por teste).
- [x] `clear_migration_supabase_prod` recusa SQLite, `DEBUG=True`, ambiente diferente de `prod` e confirmacao ausente (verificavel por teste).
- [x] Reset remoto limita a limpeza ao schema `public` e preserva schemas internos Supabase (verificavel por inspecao do SQL).
- [x] `.env.example` nao contem segredo, project ref real, senha real ou chave externa (verificavel por leitura).
- [x] `CLAUDE.md` documenta Render manual, Django 5.2 LTS e comandos de reset remoto (verificavel por leitura).

### Evidências esperadas
- `python -m pip check`
- `python manage.py check`
- `python manage.py test --verbosity 2`
- `python manage.py collectstatic --noinput`
- testes dos comandos destrutivos passando
- `git diff --stat`

### Formato de saída
Codigo implementado + testes + evidencias de validacao + pendencias de intervencao humana.

## Escopo
- Configuracao de ambiente Django.
- Governanca de deploy Render manual.
- Comandos de reset seguro Supabase HG/PROD.
- Testes de seguranca dos comandos.
- Documentacao operacional.

## Fora do escopo
- Executar reset real em HG ou PROD.
- Inserir env vars no Render.
- Acionar deploy Render.
- Criar/alterar schema de modelos.
- Criar migrations.
- Rodar seeds remotas.

## Arquivos impactados
- `lvjiujitsu/settings.py`
- `requirements.txt`
- `.gitignore`
- `.env.example`
- `CLAUDE.md`
- `system/tests/test_commands.py`
- `system/management/commands/`
- `docs/prd/`
- `render.yaml`
- `build.sh`

## Riscos e edge cases
- Limpeza remota pode apagar dados irreversivelmente; exige confirmacao explicita.
- Free tier Supabase exige backup externo antes de reset se os dados importarem.
- Render free nao permite shell remoto, entao comandos pos-deploy devem rodar localmente contra Supabase.
- URLs de banco via pooler devem ser conferidas por ambiente para evitar reset cruzado.

## Regras e restrições
- SDD antes de codigo
- TDD para implementacao
- sem hardcode
- sem mascaramento de erro
- sem migracoes
- leitura integral obrigatoria
- validacao obrigatoria

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementacao (Green)
- [x] 5. Refatoracao (Refactor)
- [x] 6. Validacao completa
- [x] 7. Limpeza final
- [x] 8. Atualizacao documental

## Validação visual
### Desktop
Nao aplicavel nesta entrega; nao ha alteracao de UI.

### Mobile
Nao aplicavel nesta entrega; nao ha alteracao de UI.

### Console do navegador
Nao aplicavel nesta entrega; nao ha alteracao de UI.

### Terminal
Validar com checks, testes e collectstatic.

## Validação ORM
### Banco
Local usa SQLite para testes. HG/PROD nao serao tocados ate intervencao humana.

### Shell checks
Validar leitura de settings e contratos dos comandos sem executar reset remoto.

### Integridade do fluxo
Deploy deve migrar e subir a casca sem seeds.

## Validação de qualidade
### Sem hardcode
Sem segredos, hosts reais ou project refs em codigo/documentacao exemplo.

### Sem estruturas condicionais quebradiças
Comandos usam guard clauses e validacao explicita.

### Sem `except: pass`
Nao introduzir tratamento silencioso de erro.

### Sem mascaramento de erro
Remover `bootstrap.py`, que mascarava falhas de seed.

### Sem comentários e docstrings desnecessários
Comentarios apenas para alertas destrutivos e decisao operacional.

## Evidências
- `.\.venv\Scripts\python.exe --version` — Python 3.12.10.
- `.\.venv\Scripts\python.exe -m pip show Django` — Django 5.2.14.
- `.\.venv\Scripts\python.exe -m pip check` — `No broken requirements found.`
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py check` — `System check identified no issues (0 silenced).`
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py test --verbosity 2` — 220 testes, OK.
- `$env:DATABASE_URL=''; .\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 374 arquivos estaticos reconhecidos, 847 post-processados.
- `manage.py check --deploy` com variaveis PROD simuladas — apenas `security.W021` sobre `SECURE_HSTS_PRELOAD`; mantido desligado por padrao por ser decisao explicita de dominio/preload.
- Recorte Red inicial dos comandos destrutivos — 12 testes, 9 falhas esperadas antes da implementacao.
- Recorte Green dos comandos destrutivos — 12 testes, OK.

## Implementado
- Removidos `render.yaml`, `build.sh` e `system/management/commands/bootstrap.py`.
- `settings.py` passa a suportar `DJANGO_ENV_FILE`, `DJANGO_ENVIRONMENT`, bloqueio de HG/PROD com `DEBUG=True` e bloqueio de HG/PROD sem `DATABASE_URL`.
- `settings.py` usa `DB_CONN_MAX_AGE=0` e `DISABLE_SERVER_SIDE_CURSORS=True` para compatibilidade segura com Supabase Transaction Pooler.
- `requirements.txt` fixado em `Django==5.2.14`; `.python-version` fixado em `3.12.10`.
- `.env.example` sanitizado e alinhado com local/HG/PROD.
- `.gitignore` ignora `.env.hg`, `.env.prod`, config local Claude e dados pessoais da migracao Kanri.
- Criados `clear_migration_supabase_hg` e `clear_migration_supabase_prod`, com base compartilhada e guardas destrutivas.
- `CLAUDE.md` atualizado com Render manual, Supabase HG/PROD, comandos de reset e regra de seeds fora do deploy.

## Desvios do plano
- `HSTS_PRELOAD` nao foi ativado por padrao. O check de deploy continua emitindo `security.W021`, mas essa configuracao exige decisao explicita de dominio e submissao a preload list.
- `.claude/settings.local.json` foi adicionado ao `.gitignore`, mas nao foi removido do indice nesta etapa porque isso exige stage/commit controlado.

## Pendências
- Usuario configurar env vars no Render.
- Usuario autorizar stage/commit.
- Usuario autorizar reset remoto HG/PROD.
- Usuario acionar deploy manual ou fornecer logs do Render.
