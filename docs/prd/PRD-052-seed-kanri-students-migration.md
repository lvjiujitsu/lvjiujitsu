# PRD-052: Seed de migração de alunos Kanri

## Resumo do que será implementado
Criar um management command idempotente para popular o cadastro local a partir dos JSONs individuais extraídos do Kanri em `static/initial_data/kanri_students_migration/`.

## Tipo de demanda
Nova feature / seed de migração de dados.

## Problema atual
Os dados sanitizados da migração existem em arquivos JSON individuais, mas ainda não há uma seed auditável que os transforme em registros do sistema. O modelo local exige `Person.cpf` único, enquanto parte dos arquivos do Kanri usa CPF do responsável, repete CPF entre dependentes ou não possui documento.

## Objetivo
Popular pessoas, responsáveis, dependentes, vínculos familiares e histórico de graduação possível, preservando rastreabilidade e evitando inventar mensalidades, check-ins ou turmas sem contrato suficiente.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/models/person.py`
- `system/models/graduation.py`
- `system/models/category.py`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/membership.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/utils/person_data.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `system/management/commands/seed_system_initial_belt_ranks.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/tests/test_commands.py`
- `static/initial_data/seed_system_initial_belt_ranks.json`

### Arquivos adjacentes consultados
- `static/initial_data/kanri_students_migration/88622-elisa-candido-ungarelli.json`
- `static/initial_data/kanri_students_migration/120166-davi-rodrigues-siqueira.json`
- `static/initial_data/kanri_students_migration_review.json`

### Internet / documentação oficial
- Não aplicável. A implementação segue contratos locais de Django management commands já existentes no repositório.

### MCPs / ferramentas verificadas
- PowerShell — disponível — leitura de arquivos e estatísticas dos JSONs executadas.
- Django test runner — a validar após implementação.

### Limitações encontradas
- `Person.cpf` é obrigatório e único, mas 36 arquivos não têm documento e há documentos repetidos ou pertencentes ao responsável.
- `Person` não possui campo para UF; o endereço importável é limitado a CEP, logradouro, número, complemento, bairro e cidade.
- `Membership` exige `SubscriptionPlan`; `MembershipInvoice` é atrelada a Stripe. Os lançamentos financeiros do Kanri não devem ser importados sem mapeamento de plano/gateway.
- `ClassCheckin` exige `ClassSession` e turma/horário compatíveis. O histórico de aulas do Kanri não deve ser importado sem mapeamento de calendário.
- Há ao menos um arquivo com endereço `Carregando...`; a seed deve limpar esses campos e registrar aviso.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + seeds auditáveis.

### Ação
Implementar uma seed `seed_system_initial_kanri_students_migration` que lê os JSONs individuais da migração Kanri e cria/atualiza pessoas, responsáveis, dependentes, relacionamentos e graduações.

### Contexto
A migração precisa preservar o máximo possível dos cadastros do Kanri sem corromper documentos, sem criar dados financeiros ou check-ins sem contrato e sem exigir migração de schema.

### Restrições
- Sem migrations.
- Sem argumentos `--` na seed.
- Sem criação de `PortalAccount`, pois os JSONs não têm senha.
- Sem criação de mensalidades, faturas, turmas, matrículas ou check-ins.
- Sem `except: pass`.
- Sem mascarar documentos problemáticos: usar identificador determinístico `KANRI-<codigo>` apenas quando o CPF do aluno estiver ausente, duplicado ou for CPF do responsável, registrando aviso.
- Dados de endereço com `Carregando...` devem ser descartados campo a campo e registrados em log.

### Critérios de aceite
- [ ] A seed falha com `CommandError` claro quando os tipos `student`, `guardian` ou `dependent` não existem.
- [ ] A seed falha com `CommandError` claro quando as faixas necessárias não existem.
- [ ] Ao importar aluno com CPF próprio válido, cria/atualiza `Person` com tipo `student`.
- [ ] Ao importar aluno com responsável documentado, cria/atualiza responsável como `guardian`, aluno como `dependent` e vínculo `responsible_for`.
- [ ] Quando o documento do aluno é ausente, duplicado ou igual ao CPF do responsável, a seed usa `KANRI-<codigo>` no campo `cpf` do aluno/dependente e registra aviso.
- [ ] A execução repetida não duplica `Person`, `PersonRelationship` nem `Graduation`.
- [ ] Evolução de faixa do Kanri gera `Graduation` quando a faixa é mapeável para `BeltRank`.
- [ ] Endereço com placeholder `Carregando...` não é gravado literalmente.
- [ ] Histórico financeiro e histórico de aulas são contados no log como não importados por falta de contrato seguro.

### Evidências esperadas
- Teste automatizado direcionado passando.
- `manage.py check` passando.
- Ausência de nova migration.

### Formato de saída
Código implementado + testes + PRD/documentação atualizados + evidências de validação.

## Escopo
- Criar management command de seed.
- Criar testes automatizados focados em idempotência, vínculo responsável/dependente, CPF substituto de migração, limpeza de placeholder e graduação.
- Atualizar `CLAUDE.md` com o novo comando real.

## Fora do escopo
- Reextrair dados do Kanri.
- Criar contas de portal.
- Criar turmas, matrículas, sessões, check-ins, mensalidades, faturas ou pagamentos.
- Corrigir manualmente JSONs problemáticos.
- Alterar schema.

## Arquivos impactados
- `docs/prd/PRD-052-seed-kanri-students-migration.md`
- `system/management/commands/seed_system_initial_kanri_students_migration.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Riscos e edge cases
- Alunos com CPF de pai/mãe podem ser importados com identificador `KANRI-<codigo>` até conferência manual.
- Pessoa existente com mesmo CPF e outro tipo operacional não deve ser sobrescrita silenciosamente.
- Faixa infantil deve ir para `Graduation`, mas `Person.jiu_jitsu_belt` aceita apenas escolhas adultas.
- Dados financeiros e de presença permanecem fora do banco para evitar falsa consistência.

## Regras e restrições
- SDD antes de código.
- TDD para implementação.
- Sem hardcode de credenciais.
- Sem mascaramento de erro.
- Sem migrações.
- Leitura integral obrigatória.
- Validação obrigatória.

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
Não aplicável; seed sem UI.

### Mobile
Não aplicável; seed sem UI.

### Console do navegador
Não aplicável; seed sem UI.

### Terminal
Executar teste direcionado e `manage.py check`.

## Validação ORM
### Banco
Validar por testes Django com banco temporário.

### Shell checks
Não necessário se os testes cobrirem contagens e vínculos.

### Integridade do fluxo
Seed deve ser idempotente e transacional.

## Validação de qualidade
### Sem hardcode
Sem credenciais ou dados fixos de pessoas fora dos JSONs.

### Sem estruturas condicionais quebradiças
Mapeamentos de faixa e documento ficam centralizados em funções pequenas.

### Sem `except: pass`
Erros de arquivo, JSON e dependência devem ser explícitos.

### Sem mascaramento de erro
Registros com documento problemático recebem CPF substituto rastreável e aviso.

### Sem comentários e docstrings desnecessários
Comentários só quando necessário para explicar decisão de migração.

## Evidências
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.KanriStudentsMigrationSeedCommandTestCase --verbosity 2 --keepdb` falhou porque o comando ainda não existia.
- Green parcial: o mesmo teste direcionado passou com 4 testes OK após implementação.
- Regressão de comandos: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2 --keepdb` passou com 11 testes OK.
- Check técnico: `.\.venv\Scripts\python.exe manage.py check` passou com 0 issues.
- Migrations: `system/migrations/` contém apenas `0001_initial.py` e `__init__.py`.
- Simulação transacional sem gravação permanente contra os 199 JSONs reais: `257 pessoa(s) criada(s), 15 pessoa(s) atualizada(s), 73 vínculo(s) criado(s), 675 graduação(ões) criada(s), 92 CPF substituto(s), 825 financeiro não importado(s), 10701 histórico de aulas não importado(s).`

## Implementado
- Criado `seed_system_initial_kanri_students_migration`.
- Seed lê `static/initial_data/kanri_students_migration/*.json`.
- Seed cria/atualiza `Person` para alunos, responsáveis e dependentes.
- Seed cria/atualiza `PersonRelationship` responsável por dependente.
- Seed cria `Graduation` a partir da evolução de faixa mapeável.
- Seed usa `KANRI-<codigo>` quando o documento do aluno está ausente, duplicado ou representa CPF do responsável.
- Seed remove placeholders `Carregando...` de campos de endereço.
- Seed audita financeiro e histórico de aulas no log sem criar registros financeiros ou check-ins.

## Desvios do plano
- O primeiro comando de teste sem `--keepdb` parou antes do Red porque o banco de teste `test_postgres` já existia e o runner tentou confirmação interativa. O teste foi reexecutado com `--keepdb`, sem apagar banco.

## Pendências
- Conferência humana dos cadastros que receberam CPF substituto `KANRI-<codigo>`.
- Conferência humana dos dados financeiros e histórico de aulas, que não foram importados por falta de contrato seguro de plano, fatura, turma e sessão.
