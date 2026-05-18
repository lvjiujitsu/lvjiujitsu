# PRD-032: Seed de repasses dos professores

## Resumo do que será implementado
Implementar `seed_system_initial_teacher_payroll_configs` para criar configurações iniciais de repasse em `TeacherPayrollConfig`, carregando dados de `static/initial_data/seed_system_initial_teacher_payroll_configs.json`.

## Tipo de demanda
Correção pontual.

## Problema atual
Existe `teacher_payroll_configs.json`, mas não existe comando ativo que consuma esse arquivo. O JSON antigo usa `class_group_code`, campo removido do modelo `ClassGroup`.

## Objetivo
Criar uma seed idempotente para repasses de professores, usando chaves atuais e sem depender de `ClassGroup.code`.

## Context Ledger
### Arquivos lidos integralmente
- `system/models/asaas.py`
- `system/models/class_group.py`
- `system/models/category.py`
- `system/models/class_membership.py`
- `system/services/payroll_rules.py`
- `static/initial_data/teacher_payroll_configs.json`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Arquivos adjacentes consultados
- `CLAUDE.md`
- `system/tests/test_services.py`
- `system/management/commands/`
- `docs/prd/PRD-031-padronizar-json-seeds.md`

### Internet / documentação oficial
- Não aplicável. Mudança interna em Django management command.

### MCPs / ferramentas verificadas
- PowerShell — OK
- ripgrep — OK
- Django — OK com limitação da suíte completa preexistente

### Limitações encontradas
- `system/migrations/0001_initial.py` já estava alterado antes desta tarefa e não será tocado.
- A suíte completa já falha por templates/rotas fora do escopo.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD.

### Ação
Implementar seed atomizada de configurações de repasse de professores.

### Contexto
O módulo financeiro calcula repasses a partir de `TeacherPayrollConfig`. As regras ficam em JSON versionado dentro de `TeacherPayrollConfig.notes`.

### Restrições
- sem migrações
- sem argumentos `--`
- sem `ClassGroup.code`
- sem mascarar dependência ausente
- seed idempotente

### Critérios de aceite
- [x] `manage.py seed_system_initial_teacher_payroll_configs` existe.
- [x] A seed lê `seed_system_initial_teacher_payroll_configs.json`.
- [x] A seed falha com `CommandError` claro se professor, categoria ou turma não existir.
- [x] As regras persistidas usam `class_group_id`, não `class_group_code`.
- [x] Rodar a seed duas vezes não duplica configurações.
- [x] A ordem final de bootstrap inclui a seed após `seed_system_initial_class_catalog`.

### Evidências esperadas
- teste automatizado da seed
- `manage.py check`
- carregamento real do JSON

### Formato de saída
Código + JSON ajustado + testes + ordem final de comandos.

## Escopo
- Criar comando em `system/management/commands/`.
- Renomear/ajustar JSON.
- Atualizar documentação local.
- Adicionar teste focado.

## Fora do escopo
- Criar contas bancárias de professores.
- Alterar cálculo de repasse.
- Alterar models ou migrations.

## Arquivos impactados
- `system/management/commands/seed_system_initial_teacher_payroll_configs.py`
- `static/initial_data/seed_system_initial_teacher_payroll_configs.json`
- `system/tests/test_commands.py`
- `CLAUDE.md`
- `docs/prd/PRD-032-seed-repasses-professores.md`

## Riscos e edge cases
- `ClassGroup` é resolvido por `(class_category__code, main_teacher__cpf)`; múltiplos registros devem gerar erro explícito.
- Regras com escopo `all` não precisam de turma.
- Regras com escopo `class_group` exigem `class_group_category` e `class_group_teacher_cpf`.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem migrações
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Teste focado da seed
- [x] 4. Implementação da seed
- [x] 5. Ajuste do JSON
- [x] 6. Validação completa
- [x] 7. Atualização documental

## Validação visual
Não aplicável.

## Validação ORM
### Banco
Sem alteração de schema.
### Shell checks
Executar a seed em banco de teste via teste automatizado.
### Integridade do fluxo
Confirmar criação de 5 `TeacherPayrollConfig`.

## Validação de qualidade
### Sem hardcode
Dados de repasse ficam no JSON.
### Sem estruturas condicionais quebradiças
Resolução de turma centralizada em helper.
### Sem `except: pass`
Não permitido.
### Sem mascaramento de erro
Dependências ausentes geram `CommandError`.
### Sem comentários e docstrings desnecessários
Não adicionar comentários supérfluos.

## Evidências
- `.\.venv\Scripts\python.exe manage.py check` — passou: `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\python.exe manage.py help seed_system_initial_teacher_payroll_configs` — comando registrado.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.TeacherPayrollSeedCommandTestCase --verbosity 2` — passou: 1 teste OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` — passou: 5 testes OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — falhou com 5 failures e 109 errors, mantendo falhas preexistentes como `TemplateDoesNotExist: home/student/dashboard.html`, `TemplateDoesNotExist: home/admin/dashboard.html` e `NoReverseMatch: person-list`.

## Implementado
- Criado `seed_system_initial_teacher_payroll_configs`.
- Renomeado e ajustado o JSON para `seed_system_initial_teacher_payroll_configs.json`.
- Substituída a ligação antiga por `class_group_code` pela ligação atual por `class_group_category` + `class_group_teacher_cpf`.
- Regras persistidas em `TeacherPayrollConfig.notes` com `class_group_id`.

## Desvios do plano
- Nenhum.

## Pendências
- Rodar a suíte completa continua pendente de correções fora deste escopo, já que há falhas preexistentes de templates e rotas.
