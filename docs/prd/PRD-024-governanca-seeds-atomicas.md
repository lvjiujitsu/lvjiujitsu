# PRD-024: Governanca de seeds atomicas e desacopladas

## Resumo do que sera implementado
Substituir o PRD-023 e remover `initial_load`/`seeding` como arquitetura oficial. Seeds passam a ser estritamente opcionais, atomicas e isoladas do runtime. Seeds de demo/teste deixam de ser chamadas em qualquer fluxo "natural" (inclui agregadores). Refatorar `seed_product_prices` para usar helper publico extraido de `registration_checkout`.

## Tipo de demanda
Alteracao arquitetural / governanca de dados iniciais.

## Problema atual
- Pacotes `system/services/initial_load` e `system/services/seeding` fazem parte da arquitetura oficial, criando acoplamento entre runtime e populacao de dados.
- Seeds chamam seeds (cadeias internas), o que fere atomicidade.
- Seeds de demo/teste criam pedidos/memberships e entram no fluxo padrao via agregador.
- `seed_product_prices` usa helper privado de checkout.
- Flags de seed em settings reforcam dependencia arquitetural desnecessaria.

## Objetivo
- Remover `initial_load` e `seeding` da arquitetura oficial e do runtime.
- Manter seeds apenas como comandos opcionais, atomicos e independentes.
- Seeds de demo/teste so executam quando chamadas explicitamente (sem agregadores no fluxo natural).
- Seeds de catalogo (produtos, turmas, precos) nao chamam outras seeds; falham explicitamente se dependencias nao foram executadas.
- `seed_product_prices` usa helper publico em modulo compartilhado.

## Context Ledger
### Arquivos lidos integralmente
- AGENTS.md
- CLAUDE.md
- docs/prd/PRD-023-seeds-env-orquestrador-dados-externos.md
- lvjiujitsu/settings.py
- .env.example
- system/services/seeding/__init__.py
- system/services/seeding/bootstrap.py
- system/services/seeding/exceptions.py
- system/services/seeding/plan_price_defaults.py
- system/services/seeding/plans.py
- system/services/seeding/product_price_defaults.py
- system/services/seeding/product_unit_prices.py
- system/services/initial_load/__init__.py
- system/services/initial_load/flags.py
- system/services/initial_load/io.py
- system/services/initial_load/parsers.py
- system/management/commands/seed_class_categories.py
- system/management/commands/seed_ibjjf_age_categories.py
- system/management/commands/seed_belts.py
- system/management/commands/seed_graduation_rules.py
- system/management/commands/seed_official_instructors.py
- system/management/commands/seed_class_catalog.py
- system/management/commands/seed_teacher_payroll_configs.py
- system/management/commands/seed_product_categories.py
- system/management/commands/seed_product_catalog.py
- system/management/commands/seed_product_inventory.py
- system/management/commands/seed_product_prices.py
- system/management/commands/seed_products.py
- system/management/commands/seed_plans.py
- system/management/commands/seed_plan_pricing.py
- system/management/commands/seed_person_type.py
- system/management/commands/seed_person_student.py
- system/management/commands/seed_person_student_with_dependent.py
- system/management/commands/seed_person_guardian.py
- system/management/commands/seed_person_guardian_with_dependent.py
- system/management/commands/seed_person_administrative.py
- system/management/commands/seed_test_personas.py
- system/management/commands/seed_holidays.py
- system/management/commands/create_admin_superuser.py
- system/management/commands/inicial_seed_test.py
- system/services/registration.py
- system/services/registration_checkout.py
- system/services/graduation.py
- system/services/payroll_rules.py
- system/constants.py
- system/tests/seed_helpers.py
- system/tests/test_commands.py

### Arquivos adjacentes consultados
- system/utils/person_data.py
- system/utils/plan_commercial.py

### Internet / documentacao oficial
- Nao aplicavel.

### MCPs / ferramentas verificadas
- Nao aplicavel.

### Limitacoes encontradas
- Analise estatica apenas, sem execucao de testes.

## Prompt de execucao
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + arquitetura MVT.

### Acao
Implementar a governanca de seeds atomicas e desacopladas conforme a spec abaixo.

### Contexto
Seeds devem ser ferramentas opcionais e isoladas do runtime. A arquitetura oficial nao deve depender de pacotes de seed e loader.

### Restricoes
- Sem hardcode de dados iniciais no runtime.
- Sem mascaramento de erro.
- Sem migracoes.
- Leitura integral obrigatoria.
- Validacao obrigatoria.

### Criterios de aceite
- [ ] `system/services/initial_load` removido e sem imports remanescentes.
- [x] `system/services/seeding` removido e sem imports remanescentes (código `.py`).
- [ ] Seeds de demo/teste nao sao chamadas por agregadores ou fluxo natural; apenas comandos explicitos.
- [ ] Seeds de catalogo (produtos/turmas/precos) nao chamam outras seeds; dependencias faltantes geram erro claro.
- [ ] `seed_product_prices` usa helper publico (ex.: `system/services/pricing.py`) reutilizado por `registration_checkout`.
- [ ] Settings e `.env.example` nao expõem `SEED_*` se o mecanismo for removido.
- [x] `manage.py test --verbosity 2` e `manage.py check` passam.

### Evidencias esperadas
- Testes passando.
- Terminal sem stack trace.

### Formato de saida
Codigo implementado + testes atualizados + evidencias de validacao.

## Escopo
- Remover pacotes `system/services/initial_load` e `system/services/seeding`.
- Reorganizar logica de seed sob `system/management/` (sem import em runtime).
- Tornar seeds atomicas: sem encadeamento interno.
- Isolar seeds de demo/teste.
- Extrair helper publico de precificacao para reutilizar em seed e checkout.
- Atualizar CLAUDE.md para refletir nova arquitetura.

## Fora do escopo
- Migracoes de schema.
- Mudancas de UI.
- Alteracoes nos modelos de negocio alem do necessario para remover acoplamentos.

## Arquivos impactados
- system/services/initial_load/** (remocao)
- system/services/seeding/** (remocao)
- system/management/commands/seed_*.py
- system/management/commands/inicial_seed_test.py (revisao ou remocao)
- system/tests/seed_helpers.py
- system/tests/test_commands.py
- system/services/registration_checkout.py
- (novo) system/services/pricing.py
- lvjiujitsu/settings.py
- .env.example
- CLAUDE.md
- docs/prd/PRD-023-seeds-env-orquestrador-dados-externos.md (marcar como substituido)

## Riscos e edge cases
- Remocao de seeds encadeadas pode exigir nova ordem manual de execucao.
- Seeds demo/teste podem deixar dados sem coerencia se executadas parcialmente.
- Mudanca no helper de precificacao pode afetar exibicao de checkout se nao houver teste.

## Regras e restricoes
- SDD antes de codigo.
- TDD para implementacao.
- Sem hardcode.
- Sem mascaramento de erro.
- Sem migracoes.
- Leitura integral obrigatoria.
- Validacao obrigatoria.

## Plano
- [ ] 1. Contexto e leitura integral
- [ ] 2. Contratos e modelagem
- [ ] 3. Testes (Red)
- [ ] 4. Implementacao (Green)
- [ ] 5. Refatoracao (Refactor)
- [ ] 6. Validacao completa
- [ ] 7. Limpeza final
- [ ] 8. Atualizacao documental

## Validacao visual
### Desktop
- Nao aplicavel.

### Mobile
- Nao aplicavel.

### Console do navegador
- Nao aplicavel.

### Terminal
- `manage.py test --verbosity 2`
- `manage.py check`

## Validacao ORM
### Banco
- `manage.py showmigrations` (sem novas migracoes)

### Shell checks
- Nao aplicavel.

### Integridade do fluxo
- Seeds executam apenas quando chamados.

## Validacao de qualidade
### Sem hardcode
### Sem estruturas condicionais quebradicas
### Sem `except: pass`
### Sem mascaramento de erro
### Sem comentarios e docstrings desnecessarios

## Evidencias

- `./.venv/Scripts/python.exe manage.py test --verbosity 2` → `Ran 379 tests` → `OK` (0 falhas, 0 erros). Antes da correcao: 335 testes + 3 modulos nao coletaveis por `ImportError` de `system.services.seeding`.
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced).`
- Grep repo-wide por `system\.services\.seeding`: nenhuma ocorrencia em codigo `.py`.

## Implementado

- Migrados os 3 modulos de teste que ainda importavam o pacote removido:
  - `system/tests/test_class_catalog.py`: import trocado para `system.management.seeders`; `setUp` passou a usar `seed_class_catalog_dependencies()` de `system/tests/seed_helpers.py` (elimina a cadeia de seeds duplicada); `seed_person_administrative` chamado com `DEFAULT_SEED_PASSWORD` (nova API exige `password`).
  - `system/tests/test_plan_eligibility.py`: import de `seed_plans` trocado para `system.management.seeders`.
  - `system/tests/test_product_views.py`: removido import morto `seed_products` (funcao inexistente na nova API e nunca chamada no arquivo).

## Desvios do plano

- Nenhum desvio. Correcao pontual escopada ao criterio "sem imports remanescentes" do PRD-024; nao houve necessidade de novo PRD nem de migracoes.

## Pendencias

- `.claude/settings.local.json` contem uma string de permissao Bash obsoleta referenciando `system.services.seeding` (allowlist local do usuario, nao executavel automaticamente, nao afeta testes). Nao alterado por estar fora do escopo de settings do usuario.
- Demais criterios de aceite do PRD-024 (remocao de `initial_load` sem imports remanescentes, atomicidade de seeds de catalogo, helper publico de precificacao, limpeza de `SEED_*` em settings/`.env.example`) nao foram auditados nesta sessao; status desta entrega cobre apenas a regularizacao dos imports de teste e a suite verde.
