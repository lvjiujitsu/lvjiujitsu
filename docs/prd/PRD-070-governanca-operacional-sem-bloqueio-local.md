# PRD-070: Governanca operacional sem bloqueio local

## Summary
Remover dos contratos ativos do LV JIU JITSU a politica que bloqueava testes, ORM local, migrations, migrate, reset local e seeds ate nova autorizacao, adotando `http://localhost:8000` como URL local canonica e mantendo barreiras apenas para ambientes remotos, producao, pagamentos externos, deploy e push.

## Demand type
Governanca + Django operacional + validacao visual.

## Goal
Permitir que agentes executem o ciclo local completo necessario para entregar o objetivo solicitado, incluindo testes, migrations, seeds, criacao do admin e validacao visual autenticada.

## Context Ledger
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`
- `.claude/skills/lv-*`
- `.cursor/skills/lv-*`
- `.cursor/rules/*.mdc`
- `.claude/settings.json`
- `.claude/launch.json`

## Official documentation
- Context7 `/websites/djangoproject_en_5_2`: `migrate` aplica migrations e cria tabelas; test runner usa banco de teste separado; management commands sao via `manage.py`.

## Approval
Usuario autorizou explicitamente: seeds, migrations, qualquer comando, testes, criacao de admin e validacao visual.

## Scope
- Governanca ativa do LV.

- Execucao local do ciclo LV ate Home autenticada.

## Out of scope
- Alterar historico de PRDs antigas que registram evidencia passada.
- Deploy, push, HG/producao ou pagamentos externos reais.
- Expor segredos de `.env`.

## Acceptance criteria
- Documentos ativos nao exigem nova autorizacao para testes locais, ORM local, migrations locais, migrate local, reset local e seeds locais quando a tarefa pedir entrega operacional.
- URL local canonica documentada como `http://localhost:8000`.
- `http://lv.localhost:8000` nao renderiza a aplicacao LV como host alternativo.
- Skills LV sincronizadas entre `.agents`, `.claude` e `.cursor`.

- LV executa `makemigrations`, `migrate`, seeds necessarias, `create_admin_superuser`, testes proporcionais e validacao visual em `localhost:8000`.

## Evidence
- Context7 `/websites/djangoproject_en_5_2`: `migrate` aplica migrations e cria tabelas; test runner usa banco de teste separado.
- Busca ativa: sem `lv.localhost`, `127.0.0.1`, `testes somente`, `somente sob autorização`, `não executar testes` ou `não executado por política` nos contratos ativos fora de PRDs históricas.
- Hash das skills LV: `.agents`, `.claude` e `.cursor` sincronizados para `lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, `lv-cleanup-audit` e `lv-prompt-builder`.
- Hash das skills: `.agents`, `.claude` e `.cursor` sincronizados para `lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery` e `lv-cleanup-audit`.
- `manage.py makemigrations`: criou `system/migrations/0001_initial.py`.
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 testes OK.
- `manage.py migrate`: aplicou todas as migrations, incluindo `system.0001_initial`.
- `manage.py create_admin_superuser`: admin criado; depois restaurado pelo mesmo comando após validação visual.
- `seed_system_initial_person_type`: 5 tipos criados.
- `seed_system_initial_belt_ranks`: 13 faixas criadas.
- `seed_system_people_flow_samples`: 5 pessoas de amostra criadas/atualizadas.
- ORM local: 1 usuário, 1 superusuário, 5 tipos de pessoa, 5 pessoas, 13 faixas e 1 turma.
- `manage.py check`: 0 issues.
- `manage.py showmigrations system`: `[X] 0001_initial`.
- Browser `http://localhost:8000/login/`: login real com admin local temporário.
- Browser `http://localhost:8000/home/`: Home autenticada renderizada sem erros de console.
- `settings.ALLOWED_HOSTS`: `['127.0.0.1', 'localhost']`, sem wildcard em ambiente local.
- `manage.py test system.tests.test_settings_hosts --verbosity 2`: 2 testes OK.
- `http://localhost:8000/`: 200, titulo `LV Jiu Jitsu | Acesso`.
- `http://lv.localhost:8000/`: 400 por host invalido.
- Screenshots:
  - `test_screenshots/prd-070-home-validation/desktop-light.png`
  - `test_screenshots/prd-070-home-validation/desktop-dark.png`
  - `test_screenshots/prd-070-home-validation/mobile-light.png`
  - `test_screenshots/prd-070-home-validation/mobile-dark.png`
- Métricas visuais: desktop e mobile sem overflow horizontal; quick links `Pessoas` e `Django Admin`; badges `Branca · 4º`, `Azul · 1º`, `Preta · 1º`.
- `manage.py test --verbosity 2`: 226 testes executados; 217 OK e 9 erros por contratos antigos que ainda apontam para templates removidos fora do escopo progressivo (`calendar`, `people`, `plans`, `register`).

## Implemented
- Governança ativa LV atualizada em `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/OPERACAO-BANCO-SEEDS.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/UI-SCREEN-CONTRACT.md`, skills, regras Cursor e launch Claude.
- Governança ativa atualizada, incluindo `.claude/settings.json`.
- Bootstrap atualizado para não reintroduzir bloqueio local.
- URL local canônica documentada como `http://localhost:8000`.
- Ciclo operacional local LV executado até admin + Home autenticada.

## Cleanup findings
- PRDs históricas mantêm evidências antigas e não foram reescritas.
- Falhas da suíte completa são legadas de módulos/templates removidos fora do PRD atual; não foram mascaradas.
- Follow-up registrado em `docs/prd/PRD-071-alinhamento-suite-legada-escopo-progressivo.md`.
- Admin teve senha temporária local apenas para login visual e foi restaurado via `create_admin_superuser`.

## Final status
Concluida com achado de suíte legada fora do escopo progressivo.
