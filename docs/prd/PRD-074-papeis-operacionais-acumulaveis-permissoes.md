# PRD-074: Papéis operacionais acumuláveis e permissões mínimas

## Summary
Separar identidade principal da pessoa, papéis operacionais acumuláveis e permissões efetivas. Hoje `Person.person_type` é singular; quando um aluno recebe `administrative-assistant`, ele ganha acesso amplo de gestão e deixa de ser modelado como aluno por tipo. O caso Aline exige aluno que treina e apoia aula kids sem virar administrativo completo.

## Demand type
Alteração arquitetural de domínio, segurança e permissões.

## Current problem
- `Person.person_type` é único e usado para identidade, matrícula, portal e autorização.
- `PortalSessionMiddleware` deriva `portal_is_administrative`, `portal_is_instructor` e `portal_is_student` apenas de `person_type.code`.
- `PortalRoleRequiredMixin` autoriza por `allowed_codes` comparando o tipo único.
- `ADMINISTRATIVE_PERSON_TYPE_CODES` concede gestão completa; não há papel intermediário para apoio de aula.
- Aline (`920.000.011-81`) é seedada como `administrative-assistant`, mas tem matrícula/graduação e apoio em aula kids.
- Miguel (`920.000.012-62`) também é seedado como administrativo, mas sem contexto de treino no JSON atual.

## Goal
Permitir que uma pessoa tenha:
- um vínculo principal de pessoa para cadastro e faturamento;
- múltiplos papéis operacionais ativos;
- permissões derivadas de capacidades, não de um único tipo;
- escopo de apoio em turma sem acesso financeiro/cadastros completos;
- transações atômicas e testes de autorização.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/middleware.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/services/portal_auth.py`
- `system/services/administrative_training.py`
- `system/tests/test_home_dashboard.py`
- `static/initial_data/initial_administrative.json`

### Adjacent files consulted
- `system/urls.py`
- `system/selectors/person_selectors.py`
- `system/services/class_calendar.py`
- `system/tests/test_admin_hubs_contract.py`
- `system/tests/test_calendar.py`
- `docs/prd/PRD-014-painel-administrativo-como-pessoa.md`

### Internet / official documentation
- Django 5.2 auth mixins and access control: https://docs.djangoproject.com/en/5.2/topics/auth/default/
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: class-based access mixins and transaction behavior.

### Limitations found
- Mudança correta exigiu schema local. A baseline única `system/migrations/0001_initial.py` foi regenerada pelo ciclo local autorizado.
- Miguel foi tratado como aluno sem papel operacional até existir regra explícita de produto; não recebe gestão por ausência de informação.
- Consulta ORM local inicial feita pelo subagente não encontrou os CPFs; após rebuild local e seeds, os CPFs foram validados no SQLite local.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual, que pediu sistema dinâmico e escalável para aluno exercer ou não funções administrativas/treino.

## Scope
- Projetar e implementar modelo de papéis operacionais acumuláveis.
- Preservar `Person.person_type` como vínculo principal ou migrá-lo explicitamente para modelo compatível.
- Criar capacidades backend: gestão completa, apoio de turma, professor, aluno, responsável, financeiro, estoque, graduação.
- Ajustar middleware/mixins/selectors para usar capacidades.
- Atualizar seeds de Aline/Miguel conforme regra decidida no código/PRD.
- Testar aluno comum, aluno com apoio kids, administrativo completo e admin técnico.

## Out of scope
- Redesign completo de CRUD/hubs; pertence à PRD-075.
- Escrita remota.
- Pagamentos reais.

## Impacted files
- `system/constants.py`
- `system/models/person.py`
- `system/middleware.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/models/class_membership.py`
- `system/services/administrative_training.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/migrations/0001_initial.py`
- testes em `system/tests/`

## Risks and edge cases
- Permissão ampla pode continuar vazando se qualquer view seguir usando `person_type` diretamente.
- Aluno com apoio em turma não pode acessar financeiro, estoque ou gestão de perfis.
- Admin técnico sem `portal_person` precisa continuar com acesso master.
- Matrícula e apoio em turma devem ser independentes: treinar não implica gerir; apoiar aula não implica administrar.

## Rules and constraints
- Backend é a fonte de permissão; front apenas reflete.
- Múltiplas escritas em transação.
- Rotas e código em inglês; interface pt-BR.
- Test-first.

## Plan
- [x] Escrever testes de autorização para perfis críticos.
- [x] Criar serviço/selector de capacidades efetivas.
- [x] Ajustar middleware para expor flags compatíveis e novas capacidades.
- [x] Ajustar mixins para capacidades.
- [x] Ajustar modelo/seed para Aline como aluno + apoio kids, sem gestão completa.
- [x] Validar home, aulas e bloqueio financeiro para perfis permitidos/bloqueados.

## Test plan
### Tests to author
- Aline: vê área pessoal e apoio kids; não vê financeiro/estoque/perfis completos.
- Administrativo completo: vê gestão.
- Aluno comum: não acessa rotas administrativas.
- Admin técnico: mantém acesso master.
- Professor: mantém área docente sem gestão financeira completa.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard --verbosity 2` — 4 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.AdministrativeSeedCommandTestCase --verbosity 2` — 3 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation.InitialTeacherSeedGraduationTestCase.test_administrative_seed_creates_complete_person_record_with_graduation_history --verbosity 2` — OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar --verbosity 2` — 89 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms --verbosity 2` — 5 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system --verbosity 1` — 260 testes OK.
- `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` — `No changes detected`.
- `.\.venv\Scripts\python.exe manage.py migrate` — migrations aplicadas, incluindo `system.0001_initial`.
- Sequência local de seeds até catálogos/planos/feriados — OK, incluindo `seed_system_initial_administrative`, `seed_system_initial_class_categories_administrative` e `seed_system_initial_class_catalog_administrative`.
- ORM local:
  - `ALINE_TYPE=student`
  - `ALINE_ROLES=class-assistant`
  - `ALINE_MANAGE=False`
  - `ALINE_SUPPORT=True`
  - `MIGUEL_TYPE=student`
  - `MIGUEL_ROLES=`
  - `MIGUEL_MANAGE=False`
- Browser interno em `http://127.0.0.1:8000/home/`:
  - Aline desktop: sem `quick-title`, sem `financial-title`, sem `staff-area-title`, com `Apoio de turma`, com `Aluno`.
  - Aline mobile 390x844: sem overflow horizontal, sem gestão/financeiro, com `Apoio de turma`.
  - Miguel desktop: sem gestão/financeiro/quick links, com `Aluno`, sem `Apoio de turma`.
  - Miguel mobile 390x844: sem overflow horizontal, sem gestão/financeiro/quick links.

## Visual validation
Executada no browser interno para Aline e Miguel em desktop e mobile. Escuro/claro não foi alternado nesta PRD porque a mudança visual foi de permissões/blocos renderizados, sem alteração de tema.

## ORM validation
Validar papéis efetivos por shell ORM local ou teste isolado.

## Quality validation
- Testes focados de permissão.
- `manage.py check`.
- Busca por usos remanescentes perigosos de `person_type.code`.

## Evidence
- `system/models/person.py`: `person_type = ForeignKey(...)`.
- `system/middleware.py`: flags de portal derivadas de um único `person_type.code`.
- `system/views/portal_mixins.py`: autorização por `allowed_codes`.
- `system/constants.py`: `ADMINISTRATIVE_PERSON_TYPE_CODES` é amplo e único.
- `system/tests/test_home_dashboard.py`: o comportamento atual espera administrativo com faixa exibindo também área de aluno, mas ainda concede área de gestão.
- `static/initial_data/initial_administrative.json`: Aline e Miguel estão versionados como administrativos por estarem na seed administrativa.
- `system/management/commands/seed_system_initial_administrative.py`: força `person_type=administrative-assistant` para todos os registros do JSON.
- `system/views/home_views.py`: `show_staff_area = is_admin or is_administrative`, liberando acesso rápido e financeiro para qualquer administrativo.
- `system/forms/person_forms.py`: edição de `person_type` muda privilégio efetivo, porque autorização depende do tipo único.
- `system/tests/test_home_dashboard.py`: testes atuais cristalizam Aline com "Minha área" + "Gestão" e Miguel com "Acesso rápido".
- `system/tests/test_calendar.py`: há cobertura de apoio/treino administrativo, mas falta matriz negativa para impedir acesso indevido a financeiro, estoque, perfis, planos e POSTs administrativos.

## Implemented
- Criados `OperationalRole` e `PersonOperationalRole` com baseline `0001_initial.py` regenerada.
- Criados `PortalCapability`, `OperationalRoleCode`, `PERSON_TYPE_CAPABILITIES` e defaults de papéis operacionais.
- Criado `system/services/portal_capabilities.py` para cálculo central de capacidades, papéis e labels.
- `PortalSessionMiddleware` passou a expor `portal_role_codes`, `portal_capabilities` e `portal_supports_classes`.
- `PortalRoleRequiredMixin` passou a suportar `required_capabilities`, preservando `allowed_codes` como fallback.
- Aline passou a ser seedada como `student` + `class-assistant` escopado à turma kids.
- Miguel passou a ser seedado como `student` sem papel operacional.
- Vínculo auxiliar de turma passou a aceitar capacidade `support-classes`, não apenas tipo Professor/Administrativo.
- Dashboard deixou de conceder área de gestão para apoio de turma.
- Rotas de professor/calendário passaram a aceitar capacidade `support-classes` com escopo validado pelos serviços de turma.
- `resolve_portal_account_from_session` passou a carregar tipo e papéis operacionais junto com a conta de portal.

## Cleanup findings
- Diff revisado no escopo de permissões/seeds.
- Não foram criados arquivos temporários.
- `staticfiles/` foi removido pelo ciclo local de limpeza; é artefato gerado e não foi editado.
- Dívidas fora do escopo permanecem em PRD-075, PRD-078, PRD-080 e PRD-081.

## Follow-up PRDs
- PRD-075 para refletir permissões no shell/CRUD visual.

## Deviations from plan
- O ciclo local revelou falha adicional de encoding em management command no PowerShell; registrada e tratada na PRD-085.

## Pending
- Regra de produto futura para Miguel, caso ele deva receber papel operacional específico.

## Final status
Concluída com limitações.
