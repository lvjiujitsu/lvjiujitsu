# PRD-017: Seeds Granulares Auditáveis

## Resumo do que será implementado
Separar seeds que hoje fazem múltiplas escritas de domínio e melhorar os logs de auditoria para listar explicitamente o que cada comando cadastrou ou atualizou.

## Tipo de demanda
Refatoração de governança de seeds.

## Problema atual
Algumas seeds ainda acumulam responsabilidades:

- `seed_belts` cria faixas e regras de graduação.
- `seed_class_catalog` chama outras seeds, cria professores, cria turmas, horários e configura repasses.
- `seed_products` cria categorias de produto, produtos e variantes.
- `seed_plans` só informa quantidade total.
- `seed_holidays` só informa quantidade total.

Isso impede auditoria visual durante o reset local e torna a sequência real de subida menos previsível.

## Objetivo
Cada seed deve atuar apenas sobre seu próprio objetivo e deve imprimir logs suficientes para auditoria manual durante a subida do sistema.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/management/commands/seed_person_type.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_test_personas.py`
- `system/management/commands/seed_person_administrative.py`
- `system/tests/test_commands.py`
- `system/tests/test_class_catalog.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_models.py`
- `system/tests/test_product_models.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/test_plan_models.py`
- `system/models/category.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/class_membership.py`
- `system/models/graduation.py`
- `system/models/product.py`
- `system/models/plan.py`
- `system/models/calendar.py`
- `system/models/person.py`
- `system/models/__init__.py`
- `system/constants.py`

### Arquivos adjacentes consultados
- `system/services/registration.py`
- comandos existentes em `system/management/commands/`
- PRDs existentes em `docs/prd/`

### Internet / documentação oficial
- Não aplicável. A demanda é governança interna de comandos Django já existentes.

### MCPs / ferramentas verificadas
- PowerShell — OK — leitura de arquivos e status do Git.
- Python da `.venv` — OK — `.\.venv\Scripts\python.exe --version`.
- Django management — OK — `manage.py help seed_belts`.
- Git — OK — `git status --short`.

### Limitações encontradas
- A worktree já possui muitas alterações pré-existentes. A implementação deve preservar esse estado e alterar apenas os arquivos necessários.
- `seed_test_personas` ainda é uma seed de validação manual; a sequência base deve ser granular, e o comando de teste pode continuar orquestrando cenários manuais.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + MVT com services.

### Ação
Separar as seeds base em comandos granulares e auditar o output de cada uma.

### Contexto
O reset local passou a rodar as seeds uma por uma. Cada comando precisa deixar claro o que fez, sem executar outra seed por baixo.

### Restrições
- sem hardcode de segredo
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória
- não reverter alterações pré-existentes da worktree

### Critérios de aceite
- [x] `seed_belts` deve criar apenas faixas, sem regras de graduação.
- [x] `seed_graduation_rules` deve criar apenas regras de graduação e exigir faixas já existentes.
- [x] `seed_class_categories` deve criar apenas categorias de turma.
- [x] `seed_ibjjf_age_categories` deve criar apenas categorias etárias IBJJF.
- [x] `seed_official_instructors` deve criar professores oficiais e suas contas de portal.
- [x] `seed_class_catalog` não deve chamar nenhuma outra seed e deve listar turmas, professores e horários vinculados.
- [x] `seed_teacher_payroll_configs` deve configurar repasses separadamente do catálogo de turmas.
- [x] `seed_product_categories` deve criar apenas categorias de produto.
- [x] `seed_products` deve exigir categorias existentes, criar produtos/variantes e listar produtos.
- [x] `seed_plans` deve listar os planos cadastrados.
- [x] `seed_holidays` deve listar os feriados cadastrados.
- [x] `inicial_seed_test` deve refletir a sequência granular.
- [x] `CLAUDE.md` deve documentar a sequência real de subida.

### Evidências esperadas
- testes Red falhando antes da implementação
- testes Green passando depois da implementação
- `manage.py check` sem erros
- `manage.py test --verbosity 2` sem falhas
- execução observável dos comandos principais sem stack trace

### Formato de saída
Código implementado + testes + evidências de validação + sequência correta de execução.

## Escopo
- Serviços de seed em `system/services/seeding.py`.
- Comandos Django em `system/management/commands/`.
- Testes de comandos e serviços.
- Documentação operacional em `CLAUDE.md`.

## Fora do escopo
- Alterar schema.
- Criar migrações.
- Alterar UI.
- Mudar dados de negócio das seeds, salvo separação de responsabilidade e logs.

## Arquivos impactados
- `docs/prd/PRD-017-seeds-granulares-auditaveis.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_class_categories.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_graduation_rules.py`
- `system/management/commands/seed_ibjjf_age_categories.py`
- `system/management/commands/seed_official_instructors.py`
- `system/management/commands/seed_product_categories.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/seed_teacher_payroll_configs.py`
- novos comandos granulares de seed
- `system/tests/test_commands.py`
- `system/tests/test_class_catalog.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_models.py`
- `system/tests/test_product_models.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/seed_helpers.py`

## Riscos e edge cases
- Comandos dependentes podem falhar se executados fora da ordem correta; a falha deve ser explícita.
- `seed_test_personas` depende da base já semeada e deve continuar funcional no fluxo de validação manual.
- Logs muito curtos prejudicam auditoria; logs excessivamente aninhados dificultam leitura no terminal.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode de segredo
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementação (Green)
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Não aplicável.

### Mobile
Não aplicável.

### Console do navegador
Não aplicável.

### Terminal
Validar via comandos de management.

## Validação ORM
### Banco
Validar em banco de teste e, quando seguro, via comandos idempotentes.

### Shell checks
Não obrigatório para esta etapa.

### Integridade do fluxo
Sequência base deve funcionar sem comando oculto.

## Validação de qualidade
### Sem hardcode
Não introduzir segredos ou credenciais.

### Sem estruturas condicionais quebradiças
Pré-requisitos devem ser validados por helper explícito.

### Sem `except: pass`
Não introduzir.

### Sem mascaramento de erro
Seeds fora de ordem devem falhar com mensagem explícita.

### Sem comentários e docstrings desnecessários
Não adicionar comentários de código desnecessários.

## Evidências
- Red observado: `manage.py test system.tests.test_commands.SeedAuditLogCommandTestCase system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` falhou antes da implementação porque os novos comandos não existiam e as seeds ainda acumulavam responsabilidades.
- Green parcial: `manage.py test system.tests.test_commands.SeedAuditLogCommandTestCase system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` passou com 15 testes.
- Green de regressão afetada: `manage.py test system.tests.test_commands system.tests.test_class_catalog system.tests.test_class_portal_views system.tests.test_forms system.tests.test_graduation.GraduationSeedTestCase system.tests.test_graduation.InitialGraduationRegistrationTestCase system.tests.test_graduation.TestPersonaInitialGraduationTestCase system.tests.test_models system.tests.test_product_models.SeedProductsTestCase system.tests.test_services system.tests.test_views --verbosity 2` passou com 153 testes.
- Suíte completa: `manage.py test --verbosity 2` passou com 329 testes.
- Check Django: `manage.py check` retornou `System check identified no issues (0 silenced).`
- Migrações: `manage.py showmigrations` confirmou `system.0001_initial` aplicado sem novas migrações.
- Limpeza: removidos 15 diretórios temporários `cleanup-artifacts-*` criados pela suíte.

## Implementado
- Removida a responsabilidade de regras de graduação de `seed_belts`.
- Criado `seed_graduation_rules` para regras de graduação.
- Criados comandos separados para categorias de turma, categorias etárias IBJJF, professores oficiais, repasses de professores e categorias de produto.
- `seed_class_catalog` passou a exigir pré-requisitos e a criar somente turmas/horários.
- `seed_products` passou a exigir categorias existentes e a criar somente produtos/variantes.
- Logs de auditoria passaram a listar turmas, professores, horários, repasses, categorias, produtos, planos e feriados.
- Testes legados que precisam de catálogo completo passaram a usar helper explícito de dependências.
- `CLAUDE.md` passou a documentar a sequência granular correta.

## Desvios do plano
- Nenhum desvio de escopo. Não foram criadas migrações.

## Pendências
- Nenhuma pendência técnica identificada nesta entrega.
