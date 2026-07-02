# PRD-111: Seeds de homologacao de cadastro N:N

## Summary
Criar fixtures locais e auditaveis para homologar visualmente as combinacoes de cadastro de pessoas no LV JIU JITSU: aluno, aluno com dependente, responsavel com dependente, aluno com upgrade administrativo, aluno com upgrade administrativo com dependente, professor, professor com dependente, administrativo seco, administrativo que treina e responsavel que tambem treina.

## Demand type
Seed operacional local + roteiro de homologacao visual controlada.

## Current problem
- A cobertura manual de Pessoas depende de criar cadastros um a um pela interface.
- As combinacoes N:N de pessoa, dependente, papel operacional, turma, experiencia marcial, faixa e tipo sanguineo nao ficam disponiveis em uma carga local unica.
- O teste visual de atribuir/remover perfil administrativo, excluir aluno e alternar papeis precisa de contas secas e previsiveis.

## Goal
- Adicionar JSONs extensos em `static/initial_data` com dados ficticios e completos para homologacao.
- Criar comandos Django explicitamente manuais para carregar essas fixtures.
- Cobrir todos os tipos sanguineos, experiencias com e sem jiu jitsu, outras artes marciais, faixas adultas/kids e relacoes N:N.
- Documentar um checklist pausado, controlado e sequencial para validar cada possibilidade no navegador.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/class_membership.py`
- `system/models/graduation.py`
- `system/models/class_group.py`
- `system/services/registration.py`
- `system/services/administrative_training.py`
- `system/services/portal_capabilities.py`
- `system/utils/person_data.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/seed_system_initial_belt_ranks.json`
- `static/initial_data/seed_system_initial_class_categories.json`
- `static/initial_data/seed_system_initial_ibjjf_age_categories.json`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Adjacent files consulted
- `system/tests/test_commands.py`
- `docs/prd/README.md`
- Arquivos existentes em `static/initial_data`
- Arquivos existentes em `system/management/commands`

### Internet / official documentation
- Django 5.2 docs via Context7:
  - `https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/`
  - `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `Django`: comandos customizados devem viver em `management/commands`, modulos iniciados por `_` nao viram comandos publicos, saida testavel deve usar `self.stdout.write`, e testes podem chamar `call_command` capturando `stdout`.

### Limitations found
- Pessoa sem experiencia real em luta precisa manter campos marciais vazios ou semanticamente neutros; forcar faixa/data marcial nesses casos falsificaria o dado.
- As fixtures dependem das seeds base de tipos de pessoa, faixas, categorias IBJJF, categorias de turma, professores iniciais e catalogo de turmas.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
A solicitacao atual autoriza criar JSONs, comandos/fixtures e PRD de validacao visual para homologacao completa das possibilidades de cadastro.

## Scope
- Criar quatro arquivos JSON de homologacao em ingles:
  - `seed_system_initial_test_teachers.json`
  - `seed_system_initial_test_students.json`
  - `seed_system_initial_test_administrative.json`
  - `seed_system_initial_test_guardians.json`
- Criar quatro comandos manuais correspondentes:
  - `seed_system_initial_test_teachers`
  - `seed_system_initial_test_students`
  - `seed_system_initial_test_administrative`
  - `seed_system_initial_test_guardians`
- Criar importador comum para evitar duplicacao de logica de pessoa, conta de portal, matriculas, papeis operacionais, graduacoes, vinculos de professor auxiliar e relacionamentos.
- Criar testes focados para parse, idempotencia e cobertura critica.
- Atualizar a documentacao operacional de seeds.

## Out of scope
- Alterar regras do wizard publico.
- Executar seed automaticamente no bootstrap canonico.
- Criar pagamentos reais, customers reais Stripe/Asaas ou dados remotos.
- Validar visualmente cada tela neste PRD; o roteiro abaixo define a homologacao posterior uma a uma.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-111-seeds-homologacao-cadastro-nn.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `static/initial_data/seed_system_initial_test_teachers.json`
- `static/initial_data/seed_system_initial_test_students.json`
- `static/initial_data/seed_system_initial_test_administrative.json`
- `static/initial_data/seed_system_initial_test_guardians.json`
- `system/services/test_seed_fixtures.py`
- `system/management/commands/seed_system_initial_test_teachers.py`
- `system/management/commands/seed_system_initial_test_students.py`
- `system/management/commands/seed_system_initial_test_administrative.py`
- `system/management/commands/seed_system_initial_test_guardians.py`
- `system/tests/test_test_seed_fixtures.py`

## Coverage matrix
### Pessoa e vinculo
- [ ] Aluno sem dependente.
- [ ] Aluno com dependente.
- [ ] Responsavel com um dependente.
- [ ] Responsavel com multiplos dependentes.
- [ ] Responsavel que tambem treina.
- [ ] Dependente com dois responsaveis.
- [ ] Aluno com upgrade administrativo.
- [ ] Aluno com upgrade administrativo e dependente.
- [ ] Administrativo seco, sem treino.
- [ ] Administrativo que treina.
- [ ] Administrativo com dependente.
- [ ] Professor.
- [ ] Professor com dependente.
- [ ] Professor com papel operacional adicional.

### Experiencia marcial
- [ ] Sem experiencia em artes marciais.
- [ ] Jiu jitsu faixa branca.
- [ ] Jiu jitsu faixa azul.
- [ ] Jiu jitsu faixa roxa.
- [ ] Jiu jitsu faixa marrom.
- [ ] Jiu jitsu faixa preta.
- [ ] Jiu jitsu faixa coral vermelha/preta.
- [ ] Jiu jitsu faixa coral vermelha/branca.
- [ ] Jiu jitsu faixa vermelha.
- [ ] Kids branca, cinza, amarela, laranja e verde.
- [ ] Muay Thai.
- [ ] Judo.
- [ ] Karate.
- [ ] Boxing.
- [ ] Wrestling.
- [ ] Outra modalidade.

### Saude e dados pessoais
- [ ] A+
- [ ] A-
- [ ] B+
- [ ] B-
- [ ] AB+
- [ ] AB-
- [ ] O+
- [ ] O-
- [ ] Sexo biologico masculino.
- [ ] Sexo biologico feminino.
- [ ] Endereco completo.
- [ ] Contato de emergencia completo.
- [ ] Alergias e lesoes preenchidas.

### Operacao e portal
- [ ] Conta de portal ativa para login local.
- [ ] Pessoa sem papel operacional.
- [ ] `academy-manager`.
- [ ] `class-assistant` escopado por turma.
- [ ] `people-support`.
- [ ] `financial-operator`.
- [ ] `stock-operator`.
- [ ] `graduation-operator`.
- [ ] Multipapeis operacionais na mesma pessoa.
- [ ] Matricula em turma adulta.
- [ ] Matricula em turma kids.
- [ ] Matricula em turma juvenil.
- [ ] Matricula em turma feminina.
- [ ] Instrutor auxiliar de turma.

## Acceptance criteria
- [x] Os quatro JSONs existem em `static/initial_data` e usam chaves em ingles.
- [x] Cada entrada possui dados pessoais completos; excecoes semanticas de "sem experiencia" ficam vazias apenas nos campos marciais correspondentes.
- [x] As fixtures cobrem todos os tipos sanguineos, faixas previstas, modalidades previstas e relacoes N:N planejadas.
- [x] Os quatro comandos sao manuais, idempotentes e nao entram em fluxo automatico de seed.
- [x] Os comandos criam/atualizam `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, `PersonOperationalRole`, `ClassInstructorAssignment` e `PersonRelationship` conforme o JSON.
- [x] Falhas de dependencia de turma/faixa geram `CommandError` claro antes de escrita parcial.
- [x] Teste focado valida parse, cobertura minima, idempotencia e vinculos criticos.
- [x] `manage.py check` passa.

## Test plan
### Tests to author
- `system.tests.test_test_seed_fixtures`:
  - valida que todos os JSONs parseiam;
  - valida cobertura de tipos sanguineos, modalidades, faixas e tags principais;
  - executa dependencias base e roda os quatro comandos duas vezes;
  - confere contas de portal, relacoes N:N, papeis operacionais e matriculas.

### Execution authorization
Local, banco de teste isolado do Django.

### Expected evidence
- `.venv/Scripts/python.exe manage.py test system.tests.test_test_seed_fixtures --verbosity 2`
- `.venv/Scripts/python.exe manage.py check`

## Visual validation checklist
Executar somente depois de carregar as seeds base e as seeds de homologacao no ambiente local desejado.

### Preparacao
1. Rodar seeds canonicas de dependencia:
   - `seed_system_initial_person_type`
   - `seed_system_initial_belt_ranks`
   - `seed_system_initial_ibjjf_age_categories`
   - `seed_system_initial_class_categories`
   - `seed_system_initial_teacher`
   - `seed_system_initial_class_catalog`
2. Rodar seeds de homologacao:
   - `seed_system_initial_test_students`
   - `seed_system_initial_test_guardians`
   - `seed_system_initial_test_administrative`
   - `seed_system_initial_test_teachers`
3. Usar a senha local de fixture documentada no JSON/command.
4. Validar um item por vez, registrando screenshot e resultado antes de prosseguir.

### Rodada 1: login e areas
1. Login como aluno simples: deve cair na area de aluno sem gestao.
2. Login como aluno com dependente: deve exibir dados proprios e relacao com dependente.
3. Login como responsavel com dependente: deve permitir visualizar dependente.
4. Login como responsavel que treina: deve manter area propria de aluno e relacao de responsavel.
5. Login como professor: deve exibir area de professor.
6. Login como professor com dependente: deve manter area de professor e relacao familiar.
7. Login como administrativo seco: deve exibir gestao, sem matricula propria.
8. Login como administrativo que treina: deve exibir gestao e matricula/area propria quando aplicavel.

### Rodada 2: Pessoas e N:N
1. Abrir lista de Pessoas e filtrar por cada tipo de vinculo.
2. Abrir detalhe do dependente com dois responsaveis.
3. Abrir detalhe do aluno com dependente.
4. Abrir detalhe do professor com dependente.
5. Abrir detalhe do administrativo com dependente.
6. Conferir graduacao, turma, contato de emergencia e endereco.

### Rodada 3: upgrade administrativo
1. Escolher o aluno seco marcado para upgrade administrativo.
2. Atribuir papel operacional administrativo pela interface.
3. Fazer logout/login com a mesma conta.
4. Confirmar que a area de gestao apareceu.
5. Remover o papel operacional.
6. Fazer logout/login novamente.
7. Confirmar que a area de gestao deixou de aparecer e que a area de aluno permaneceu.

### Rodada 4: exclusao controlada
1. Escolher o aluno marcado como candidato de exclusao.
2. Abrir detalhe, confirmar dependencias exibidas.
3. Excluir pela interface.
4. Confirmar que nao aparece mais na lista.
5. Tentar login na conta excluida ou removida, conforme comportamento esperado do fluxo atual.
6. Validar que dependentes/responsaveis relacionados permaneceram consistentes.

### Rodada 5: cobertura marcial e saude
1. Filtrar/abrir pessoas com cada tipo sanguineo.
2. Abrir pessoas sem experiencia marcial e confirmar que nao exibem faixa indevida.
3. Abrir pessoas com outras modalidades e confirmar modalidade/graduacao textual.
4. Abrir pessoas com faixas kids, adultas, coral e vermelha.
5. Conferir que alergias, lesoes, contato de emergencia e endereco aparecem completos.

## Risks and edge cases
- Rodar os comandos fora da ordem pode falhar por ausencia de turma ou target de relacionamento.
- Pessoas sem experiencia nao devem receber graduacao falsa apenas para preencher campo.
- Papeis operacionais acumulaveis podem alterar a home conforme PRDs recentes; o roteiro visual deve registrar o comportamento observado com data.

## Plan
1. [x] Ler contratos, modelos, seeds base e fonte oficial Django.
2. [x] Criar importador comum e comandos.
3. [x] Criar JSONs de homologacao.
4. [x] Criar teste focado.
5. [x] Atualizar documentacao de seeds.
6. [x] Executar validacoes locais.
7. [x] Revisar diff e registrar limpeza.

## Execution evidence
- Criado `system/services/test_seed_fixtures.py` com importador comum idempotente.
- Criados comandos manuais:
  - `seed_system_initial_test_students`
  - `seed_system_initial_test_guardians`
  - `seed_system_initial_test_administrative`
  - `seed_system_initial_test_teachers`
- Criados JSONs:
  - `static/initial_data/seed_system_initial_test_students.json` com 13 entradas.
  - `static/initial_data/seed_system_initial_test_guardians.json` com 6 entradas.
  - `static/initial_data/seed_system_initial_test_administrative.json` com 6 entradas.
  - `static/initial_data/seed_system_initial_test_teachers.json` com 6 entradas.
- Atualizado `docs/OPERACAO-BANCO-SEEDS.md` com comandos locais de homologacao e senha fake `LvTest@2026`.
- Atualizado `docs/prd/README.md` com a PRD-111.

## Visual validation
- Pendente para execucao posterior uma a uma, conforme checklist acima.
- Os cadastros foram carregados no banco local em 2026-07-01 para habilitar a validacao no navegador.

## ORM validation
- Comando local executado:
  - `.venv/Scripts/python.exe manage.py shell -c "..."`
- Resultado:
  - `people 31`
  - `enrollments 17`
  - `relationships 11`
  - `roles 17`
  - `assignments 9`

## Quality validation
- `.venv/Scripts/python.exe manage.py test system.tests.test_test_seed_fixtures --verbosity 2` — 2 testes OK.
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Execucao local dos comandos novos:
  - `seed_system_initial_test_students` — 13 criados, 13 contas, 2 relacionamentos.
  - `seed_system_initial_test_guardians` — 6 criados, 6 contas, 7 relacionamentos.
  - `seed_system_initial_test_administrative` — 6 criados, 6 contas, 13 papeis, 1 relacionamento.
  - `seed_system_initial_test_teachers` — 6 criados, 6 contas, 6 apoios de turma, 1 relacionamento.

## Evidence
- Evidencia real registrada em Execution evidence, ORM validation e Quality validation.

## Implemented
- JSONs extensos de fixtures locais cobrindo 31 pessoas ficticias.
- Importador comum com `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, `PersonOperationalRole`, `ClassInstructorAssignment` e `PersonRelationship`.
- Quatro comandos Django manuais e idempotentes.
- Teste automatizado de contrato e idempotencia.
- Roteiro de validacao visual pausada e controlada.

## Cleanup findings
- Diff do escopo revisado: serviço, comandos, JSONs, teste focado, PRD e documentação de seeds.
- Ajuste de limpeza aplicado: quebra de linhas longas em `system/services/test_seed_fixtures.py` e `system/tests/test_test_seed_fixtures.py`.
- Achado residual fora do escopo: `docs/prd/README.md` ja existia como arquivo nao rastreado e nao listava PRD-101 a PRD-110 na tabela; esta tarefa apenas adicionou a PRD-111 sem normalizar entradas preexistentes.

## Follow-up PRDs
- Pendente apenas se a validacao visual encontrar falha de UX ou regra fora do escopo das fixtures.

## Deviations from plan
- Nenhum desvio funcional. A nomenclatura usa `guardians` em vez de `responsaveis` para manter nomes de arquivo e comando em ingles e alinhados ao dominio `guardian`.

## Pending
- Validacao visual manual no navegador, uma possibilidade por vez, conforme checklist.

## Final status
Concluida com limitacoes.
