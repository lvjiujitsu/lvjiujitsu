---
description: "Reconstrói o ambiente local do LV JIU JITSU, aplica as seeds explícitas e sobe a porta 8000 depois de validar todas as guardas."
disable-model-invocation: true
---

# /reset-local

Executa o ciclo destrutivo **somente local** na ordem canônica de
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md` e para no primeiro erro, informando em qual passo
parou. A invocação manual deste comando é a autorização explícita para executar
as seeds do ciclo.

## Guardas antes de apagar

`clear_migrations.py` já recusa ambiente remoto por conta própria. Estas
verificações são o aviso antecipado, para o operador não descobrir o problema
depois de dez comandos.

1. Recusar qualquer indicação de ambiente remoto:

```powershell
if (($env:DJANGO_ENV_FILE -match 'hg|prod') -or ($env:DJANGO_ENVIRONMENT -match 'hg|prod')) {
    Write-Error "RECUSADO: /reset-local é somente local."
    exit 1
}
```

2. Confirmar que `.venv\Scripts\python.exe`, `manage.py` e
   `static\initial_data\` existem.

3. Verificar, **sem imprimir valores**, a configuração exigida pelo ciclo:

```powershell
.\.venv\Scripts\python.exe -c "from decouple import AutoConfig; import sys; c=AutoConfig(search_path='.'); miss=[k for k in ['ADMIN_SUPERUSER_PASSWORD','SEED_INITIAL_TEACHER_PASSWORD','SEED_INITIAL_ADMINISTRATIVE_PASSWORD','SEED_TEST_PORTAL_PASSWORD'] if not str(c(k, default='')).strip()]; print('MISSING: ' + ', '.join(miss) if miss else 'OK'); sys.exit(1 if miss else 0)"
```

   Se retornar `MISSING`, **parar aqui**: não rodar `clear_migrations.py`, não
   apagar `db.sqlite3`. Informar quais variáveis faltam.

4. Rodar `manage.py check`. Se qualquer guarda falhar, parar sem executar
   `clear_migrations.py`; `db.sqlite3` deve permanecer intocado.

5. Se a porta `8000` já estiver ocupada, consultar o PID. Encerrar somente
   quando a linha de comando corresponder a `manage.py runserver
   localhost:8000`; para qualquer outro processo, abortar e reportar o PID.
   Depois de encerrar o runserver identificado, confirmar que a porta foi
   liberada antes do reset.

## Sequência (parar no primeiro erro)

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py seed_system_initial_person_type
.\.venv\Scripts\python.exe manage.py seed_system_initial_belt_ranks
.\.venv\Scripts\python.exe manage.py seed_system_initial_ibjjf_age_categories
.\.venv\Scripts\python.exe manage.py seed_system_initial_graduation_rules
.\.venv\Scripts\python.exe manage.py seed_system_initial_class_categories
.\.venv\Scripts\python.exe manage.py seed_system_initial_teacher
.\.venv\Scripts\python.exe manage.py seed_system_initial_class_categories_teacher
.\.venv\Scripts\python.exe manage.py seed_system_initial_class_catalog
.\.venv\Scripts\python.exe manage.py seed_system_initial_teacher_payroll_configs
.\.venv\Scripts\python.exe manage.py seed_system_initial_administrative
.\.venv\Scripts\python.exe manage.py seed_system_initial_class_categories_administrative
.\.venv\Scripts\python.exe manage.py seed_system_initial_class_catalog_administrative
.\.venv\Scripts\python.exe manage.py seed_system_initial_product_categories
.\.venv\Scripts\python.exe manage.py seed_system_initial_product_catalog
.\.venv\Scripts\python.exe manage.py seed_system_initial_subscription_plans
.\.venv\Scripts\python.exe manage.py seed_system_initial_subscription_plans_values
.\.venv\Scripts\python.exe manage.py seed_system_initial_coupons
.\.venv\Scripts\python.exe manage.py seed_system_initial_holidays
.\.venv\Scripts\python.exe manage.py seed_system_initial_plan_tiers
.\.venv\Scripts\python.exe manage.py seed_system_initial_plan_prices
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py showmigrations
```

A ordem das seeds é a de `obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`; não manter segunda
cópia da lista fora dela — ao divergir, o runbook vence e este arquivo é
corrigido.

## Dados fictícios de homologação (opcional)

Só quando o objetivo pedir telas povoadas. Exige `SEED_TEST_PORTAL_PASSWORD`
configurada:

```powershell
.\.venv\Scripts\python.exe manage.py seed_system_initial_test_students
.\.venv\Scripts\python.exe manage.py seed_system_initial_test_guardians
.\.venv\Scripts\python.exe manage.py seed_system_initial_test_administrative
.\.venv\Scripts\python.exe manage.py seed_system_initial_test_teachers
```

## Subir e confirmar

```powershell
$serverProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList @("manage.py", "runserver", "localhost:8000", "--noreload") -PassThru -WindowStyle Hidden
$response = Invoke-WebRequest "http://localhost:8000/login/" -UseBasicParsing
$response.StatusCode
$serverProcess.Id
```

Se a primeira tentativa ocorrer antes de o servidor subir, repetir a
requisição por até 15 segundos. Informar o PID para o operador poder encerrar
o processo.

## Saída

```text
Guardas: ambiente local | arquivos ok | variáveis de seed ok | check ok
Passo que falhou: nenhum | <nome do passo>
Seeds: <resultado>
Testes: <quantidade e resultado>
Servidor: http://localhost:8000/login/ -> <status> (PID <id>)
```

## Parar quando

- Uma guarda recusar: parar antes de qualquer remoção e informar a causa.
- Qualquer passo da sequência falhar: parar no passo, sem mascarar a saída.
- O HTTP não responder em 15 segundos: reportar falha e o PID.
- HTTP 200 confirmado: entregar a saída e deixar o PID explícito.
