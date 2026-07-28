# PRD-073: Seeds administrativas e bootstrap consistente

## Summary
Corrigir a ordem e a atomicidade das seeds iniciais que criam professores, administrativos e vínculos de treino. O erro relatado (`ClassCategory matching query does not exist`) ocorre porque `seed_system_initial_administrative` tenta sincronizar `class_category`, matrículas e apoio em turmas antes de as categorias/turmas existirem no ciclo do arquivo externo de comandos.

## Demand type
Correção de bootstrap local + governança de seeds.

## Current problem
- `seed_system_initial_administrative.py` cria pessoa/portal e também chama `sync_administrative_training_links`, que exige `ClassCategory` e `ClassGroup` existentes.
- As seeds legadas `seed_system_initial_class_categories_administrative` e `seed_system_initial_class_catalog_administrative` dependem da pessoa administrativa já criada; quando a seed principal falha, ambas falham com CPF não encontrado.
- `docs/OPERACAO-BANCO-SEEDS.md` também precisa ser reconciliado: a ordem atual documentada ainda posiciona vínculos de professor antes da criação do professor.

## Goal
Ter um ciclo local reproduzível, idempotente e transacional para primeira carga:
- categorias antes de vínculos por categoria;
- professores antes de turmas;
- turmas antes de vínculos de treino administrativo;
- administrativos criados sem deixar estado parcial quando vínculo dependente falta;
- comandos e documentação alinhados.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/management/commands/seed_system_initial_class_categories.py`
- `system/management/commands/seed_system_initial_class_categories_administrative.py`
- `system/management/commands/seed_system_initial_class_catalog_administrative.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_class_categories_teacher.py`
- `system/services/administrative_training.py`
- `system/tests/test_commands.py`
- `static/initial_data/initial_administrative.json`

### Adjacent files consulted
- `system/models/person.py`
- `system/models/category.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `docs/prd/PRD-024-governanca-seeds-atomicas.md`
- `docs/prd/PRD-031-padronizar-json-seeds.md`

### Internet / official documentation
- Django 5.2 custom management commands: https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `CommandError`, `transaction.atomic`, `call_command`.
- `.venv\Scripts\python.exe manage.py check`: passou, 0 issues.
- Testes existentes executados: `system.tests.test_admin_hubs_contract`, `system.tests.test_home_dashboard`.

### Limitations found
- `system/migrations/0001_initial.py` já estava modificado antes deste ciclo apenas por timestamp.
- O arquivo de comandos do Obsidian fica fora do repo Git do LV; alteração nele deve ser registrada como arquivo externo.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual do usuário, que pediu corrigir de maneira consistente os erros de seeds e reorganizar o sistema antes da implementação final.

## Scope
- Corrigir ordem documentada em `docs/OPERACAO-BANCO-SEEDS.md`.
- Corrigir o arquivo externo de comandos PowerShell, se mantido como fonte operacional.
- Adicionar testes focados reproduzindo a falha de ordem e o ciclo correto.
- Ajustar seeds para mensagens de pré-requisito claras e sem estado parcial.

## Out of scope
- Escrever em HG, produção ou Render.
- Criar dados remotos.
- Redesenhar papéis/permissões; isso pertence à PRD-074.

## Impacted files
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/tests/test_commands.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/services/administrative_training.py`

## Risks and edge cases
- Seed administrativa atual junta criação de pessoa e vínculos dependentes; uma dependência ausente deve abortar sem pessoa parcialmente criada.
- JSON compartilhado por múltiplas seeds mantém acoplamento oculto.
- Reordenar sem teste pode apenas mover a falha para professor, turma ou payroll.

## Rules and constraints
- Usar `CommandError` explícito para pré-requisito ausente.
- Manter `transaction.atomic` em múltiplas escritas.
- Testar com banco isolado Django.
- Não mascarar exceções.

## Plan
- [x] Criar teste que reproduz a falha quando administrativo roda antes de categorias/turmas.
- [x] Criar teste do ciclo correto de seeds administrativas com vínculos de treino.
- [x] Ajustar documentação e comandos.
- [x] Ajustar mensagens/validações das seeds se necessário.
- [x] Executar teste focado e `manage.py check`.
- [x] Executar cleanup audit.

## Test plan
### Tests to author
- `seed_system_initial_administrative` falha com mensagem clara quando `ClassCategory`/`ClassGroup` dependente não existe.
- Ciclo correto cria Aline, portal, graduação, matrículas adultas e apoio kids de forma idempotente.
- Seeds legadas administrativas permanecem idempotentes após a seed principal.

### Execution authorization
Autorizada localmente pela solicitação atual.

### Execution evidence
- Red real: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.AdministrativeSeedCommandTestCase --verbosity 2` falhou em 2 testes porque as mensagens não continham `seed_system_initial_class_categories` nem `seed_system_initial_class_catalog`.
- Green real: o mesmo comando passou com 3 testes OK após validar dependências antes da escrita.
- Regressão focada: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` passou com 23 testes OK.

## Visual validation
Não aplicável.

## ORM validation
Validar em banco de teste e, se necessário, shell ORM local read-only após seeds locais.

## Quality validation
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py check`

## Evidence
- `seed_system_initial_administrative.py` chama `sync_administrative_training_links` dentro de `transaction.atomic`.
- `system/services/administrative_training.py` busca `ClassCategory.objects.get(code=...)` e `ClassGroup.objects.get(class_category__code=..., main_teacher__cpf=...)`.
- `initial_administrative.json` define `class_category`, `class_enrollments` e `class_instructor_assignments` para CPF `920.000.011-81`.
- Inventário local mostrou a ordem externa chamando administrativo antes de categorias/turmas.
- Subagente confirmou que o CPF inexistente nas seeds legadas era consequência provável do rollback da seed principal.
- `docs/OPERACAO-BANCO-SEEDS.md` tinha `seed_system_initial_class_categories_teacher` antes de `seed_system_initial_teacher`; corrigido.

## Implemented
- `system/services/administrative_training.py`: adicionada validação explícita de categoria e turma, com mensagens indicando `seed_system_initial_class_categories` e `seed_system_initial_class_catalog`.
- `system/management/commands/seed_system_initial_administrative.py`: dependências de treino são validadas antes de criar/atualizar `Person`.
- `system/tests/test_commands.py`: adicionada `AdministrativeSeedCommandTestCase` cobrindo falta de categorias, falta de catálogo e idempotência das seeds legadas após a seed principal.
- `docs/OPERACAO-BANCO-SEEDS.md`: ordem de referência corrigida.

## Cleanup findings
- Diff revisado no escopo da PRD-073.
- Arquivos alterados relidos integralmente.
- Não foram encontrados resíduos temporários, imports mortos ou expansão indevida no escopo.
- Dívida fora do escopo já separada: PRD-074 para papéis/permissões acumuláveis; PRD-079 para PRDs duplicadas; PRD-083 para documentação legada.

## Follow-up PRDs
- PRD-074 para papéis/permissões acumuláveis.

## Deviations from plan
- Nenhum desvio funcional. A correção também atualizou o arquivo PowerShell externo do Obsidian porque ele era a fonte operacional reproduzindo o erro.

## Pending
- PRD-074 continua pendente para corrigir o modelo de papéis acumuláveis; esta PRD não altera permissões.

## Final status
Concluída com limitações.
