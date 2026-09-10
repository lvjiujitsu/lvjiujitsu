---
name: lvjiujitsu-remote-refresh
description: "Recria HG ou produção do LV Jiu Jitsu por pedido explícito, com simulação, confirmação do projeto e seeds documentadas."
disable-model-invocation: true
---

# LV Jiu Jitsu Remote Refresh

## Quando acionar

Por pedido explícito para reconstruir HG ou produção. Ler
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md` e o runbook
`obsidian/projetos/lvjiujitsu/comandos-powershell-lvjiujitsu.md`.

## Passos

1. Confirmar autorização explícita para apagar o ambiente nomeado e que não há
   dado a preservar. Perguntar somente se essa autorização ainda não constar
   na conversa. Dado não descartável exige alternativa antes de qualquer reset.
2. Executar `manage.py check_environment_parity` antes da checagem remota.
   Selecionar `.env.hg` ou `.env.prod` em `DJANGO_ENV_FILE` e executar
   `manage.py check_database_connection`. Conferir o projeto, sem imprimir chaves.
3. Preparar o manifest com `manage.py collectstatic --noinput` sob o ambiente alvo.
4. Configurar `SUPABASE_RESET_CONFIRM=RESET_HG` ou `RESET_PROD`, conforme o alvo.
   `SUPABASE_PROJECT_REF` deve corresponder à conexão PostgreSQL Supabase;
   `DEBUG` deve ser falso. Simular com `clear_migration_supabase_hg --dry-run`
   ou `clear_migration_supabase_prod --dry-run`, sempre via `manage.py`.
5. Revisar os objetos listados e executar o mesmo comando com `--execute`.
   Em produção, repetir o projeto em `--confirm-ref <ref-conferido>`.
6. Executar `migrate`, `create_admin_superuser` e cada seed aplicável, na ordem
   da nota de banco. Conferir nomes e flags com `manage.py help <comando>`.
   Aplicar as particularidades do produto abaixo somente quando solicitadas.
7. Executar `lock_supabase_api_access` e `lock_supabase_api_access --check`.
8. Validar `check`, `showmigrations core business_rule`, `check_schema_parity` e contagens
   dos modelos efetivamente semeados. Teste local não comprova estado remoto.
9. Restaurar as variáveis de processo ao estado anterior, inclusive em falha.
   Parar no primeiro erro e registrar o passo para retomada.

## Saída

Informar ambiente autorizado, projeto conferido, simulação, reset, seeds,
proteção da Data API, schema, contagens e falhas com saída observada.

## Parar quando

- Faltar autorização, confirmação, configuração, fonte de seed ou conexão válida.
- Existir dado que precise ser preservado.
- Qualquer comando falhar, o schema divergir ou a Data API continuar exposta.

<!-- BN - business rule: particularidades do produto. -->

## Particularidades do produto

As seeds de pessoas, graduação, turmas, produtos e planos pertencem a este produto. Senhas de professores e administrativos são insumos do ciclo inicial; `SEED_TEST_PORTAL_PASSWORD` só é exigida para os cenários fictícios. Não existem os comandos `seed_test_data` e `seed_access_users` neste projeto. A ordem está na nota de banco.
