# Operação de banco, migrations e seeds

Este documento separa testes Django, ciclo destrutivo local e operação Supabase.

## Regras

- Usar `.\.venv\Scripts\python.exe`.
- Testes só são executados após autorização.
- Testes usam banco isolado e não exigem apagar `db.sqlite3`.
- O agente não executa reset destrutivo.
- Não usar `clear_migrations.py` contra HG/produção.
- Não usar `makemigrations` em HG/produção.
- Seeds são independentes, manuais e explícitas.
- `lock_supabase_api_access` deve rodar após migrate/seeds em Supabase.
- Não incluir credenciais em comandos, PRDs ou logs.

## Schema

- Baseline esperado: `system/migrations/0001_initial.py`.
- Não criar migrations incrementais por padrão.
- Mudança de model que exige schema deve parar para decisão.
- O ciclo local pode regenerar a baseline somente com autorização e execução do usuário.

## Comandos seguros

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
```

`collectstatic`, shell ORM e testes dependem do escopo e das autorizações definidas em `AGENTS.md`.

## Ciclo destrutivo local

Somente o usuário executa:

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
```

Depois, executar as seeds necessárias em ordem.

## Seeds de referência

1. `create_admin_superuser`
2. `seed_system_initial_person_type`
3. `seed_system_initial_belt_ranks`
4. `seed_system_initial_ibjjf_age_categories`
5. `seed_system_initial_graduation_rules`
6. `seed_system_initial_class_categories`
7. `seed_system_initial_class_categories_teacher`
8. `seed_system_initial_class_categories_administrative`
9. `seed_system_initial_class_catalog`
10. `seed_system_initial_class_catalog_administrative`
11. `seed_system_initial_product_categories`
12. `seed_system_initial_product_catalog`
13. `seed_system_initial_subscription_plans`
14. `seed_system_initial_subscription_plans_values`
15. `seed_system_initial_subscription_plans_stripe`
16. `seed_system_initial_coupons`
17. `seed_system_initial_holidays`
18. `seed_system_initial_teacher`
19. `seed_system_initial_administrative`
20. `seed_system_initial_teacher_payroll_configs`

Seeds específicas, como migração Kanri, devem ser executadas somente quando o objetivo exigir.

## Supabase HG

Reset destrutivo exige:

- `.env.hg`;
- `DJANGO_ENVIRONMENT=hg`;
- `DJANGO_DEBUG=False`;
- `DATABASE_URL` Supabase;
- confirmação definida pelo comando;
- autorização explícita.

Comando existente:

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py clear_migration_supabase_hg
```

Após reset: `collectstatic`, `check`, `migrate`, seeds, `lock_supabase_api_access`, `showmigrations`.

## Supabase produção

Produção exige comando próprio, confirmação mais forte e autorização explícita. Nunca reutilizar o fluxo HG por substituição textual.

## Render

Build atual:

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py lock_supabase_api_access
```

Seeds não devem ser adicionadas ao build automaticamente.
