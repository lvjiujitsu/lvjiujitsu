# PRD-115: Wizard de perfis operacionais sequenciais

## Summary
Corrigir o cadastro publico para que Professor e Administrativo continuem sendo pessoas dentro do wizard principal, usando `registration_profile=other` e etapas adicionais sequenciais. O fluxo nao deve abrir paginas publicas separadas para esses perfis. Professor informa vinculo com turma ativa existente ou proposta de novo horario em modal multi-dias, alem de condicao financeira unica. Administrativo informa areas solicitadas, se tambem treina e sua condicao financeira unica.

## Demand type
Correcao de UI/UX + ajuste de workflow Django + persistencia estruturada de solicitacoes pendentes.

## Current problem
- Em `/register/`, o card "Professor" e um link (`<a>`) separado da maquina de estados do wizard, entao ele aparece destacado pelo navegador/comentario e pula a sequencia normal de selecao.
- Nao existe card "Administrativo" na tela inicial, apesar da PRD-112 ja ter o fluxo publico de solicitacao pendente.
- Professor e Administrativo ainda nao coletam dados de recebimento/intencao suficientes para a gestao aprovar corretamente os perfis compostos descritos nas PRDs 111, 112 e 113.
- O financeiro operacional permitia combinacoes incoerentes, como permuta e recebimento PIX ao mesmo tempo.
- A proposta de horario do professor tinha apenas um select de dia da semana, impedindo proposta recorrente de segunda a sexta.
- A selecao de turma do professor considerava apenas "sem professor"; a regra correta e permitir solicitar vinculo em turma ativa, registrando no payload se existe professor atual para aprovacao posterior.
- A subopcao do Administrativo aparece com fieldset/radio nativo, fora do padrao visual do bloco de dependentes.
- Os icones de Professor e Administrativo nao comunicam o perfil corretamente.
- `/register/teacher-proposal/` e `/register/admin-access/` usam topbar administrativa, theme toggle e formulario longo em pagina unica, em vez do cadastro convencional por etapas.

## Goal
- Manter Aluno e Responsavel no wizard de matricula atual.
- Transformar Professor e Administrativo em opcoes selecionaveis do mesmo wizard, sem redirecionamento no card ou no botao `Proximo`.
- Persistir Professor e Administrativo como cadastro de pessoa (`other`) com `other_type_code` correto.
- Reutilizar as etapas de dados pessoais, saude e artes marciais para esses perfis.
- Adicionar etapas extras: horario do professor, areas administrativas e condicao financeira/recebimento.
- Redirecionar URLs publicas legadas de professor/administrativo para `/register/?profile=...`, sem renderizar o formulario antigo.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`
- `docs/prd/PRD-111-seeds-homologacao-cadastro-nn.md`
- `docs/prd/PRD-112-solicitacao-acesso-administrativo-pendente.md`
- `docs/prd/PRD-113-solicitacao-turmas-horarios-professor.md`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `system/models/request_workflows.py`
- `system/forms/access_request_forms.py`
- `system/forms/class_request_forms.py`
- `system/services/access_requests.py`
- `system/services/class_requests.py`
- `system/views/access_request_views.py`
- `system/views/class_request_views.py`
- `templates/access_requests/request_form.html`
- `templates/access_requests/request_detail.html`
- `templates/class_requests/new_teacher_form.html`
- `templates/class_requests/request_detail.html`
- `system/tests/test_register_wizard_contract.py`
- `system/tests/test_administrative_access_requests.py`
- `system/tests/test_class_catalog_requests.py`
- `system/tests/test_administrative_access_request_views.py`
- `system/tests/test_class_catalog_request_views.py`

### Adjacent files consulted
- `system/models/asaas.py`
- `system/forms/person_forms.py`
- `system/services/asaas_payroll.py`
- `system/urls.py`
- `system/tests/test_administrative_access_request_views.py`
- `system/tests/test_class_catalog_request_views.py`

### Internet / official documentation
- Django 5.2 FormView: `https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/#formview`
- Django 5.2 form validation: `https://docs.djangoproject.com/en/5.2/ref/forms/validation/`
- Django 5.2 JSONField: `https://docs.djangoproject.com/en/5.2/ref/models/fields/#jsonfield`
- MDN button element: `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/button`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `FormView`, validacao em `clean()`, erros de formulario, `TestCase`.

### Limitations found
- `AdministrativeAccessRequest` nao tinha payload JSON antes desta PRD; precisa de campo estruturado para nao misturar intencao operacional em texto livre.
- O modelo existente de conta bancaria de professor (`TeacherBankAccount`) armazena PIX; conta bancaria tradicional sera guardada no payload da solicitacao para decisao manual, sem transferencia automatica nesta entrega.
- A regra completa de pagamento/permuta do administrativo ainda depende de desenho financeiro posterior; esta entrega registra a intencao para aprovacao, nao cria folha/repasse automatico.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitacao atual: "implemente as correcoes e vamos seguir".

## Design proposal
- Objetivo: manter a tela como questionario de perfil e continuar o cadastro convencional por etapas.
- Hierarquia: quatro cards de mesma familia visual em uma coluna: Aluno, Responsavel, Professor, Administrativo.
- Estados:
  - Aluno: revela a pergunta existente sobre dependentes.
  - Responsavel: revela o resumo existente sobre aluno(s) sob responsabilidade.
  - Professor: revela nota curta e segue para dados pessoais, saude, artes marciais, horario e financeiro.
  - Administrativo: revela a escolha inicial de treino/compensacao e segue para dados pessoais, saude, artes marciais, areas administrativas e financeiro.
- Professor:
  - pode selecionar uma ou mais turmas ativas existentes;
  - turmas com professor atual registram `approval_scope=admin_and_current_teacher`;
  - turmas sem professor registram `approval_scope=admin_only`;
  - pode criar proposta de horario por modal na propria etapa, com checklist de dias da semana.
- Financeiro operacional:
  - usa uma condicao unica: `pays_monthly`, `barter`, `volunteer`, `paid_fixed`, `paid_per_student` ou `paid_mixed`;
  - `barter`, `pays_monthly` e `volunteer` nao aceitam dados de recebimento;
  - condicoes pagas exigem valor/percentual conforme o caso e PIX ou conta bancaria.
- Desktop/mobile: manter largura e ritmo do wizard atual, com uma coluna principal e sem formularios administrativos largos.

## Acceptance criteria
- [x] O card Professor em `/register/` nao e mais `<a>` nem redireciona ao clique no card.
- [x] Professor e Administrativo usam o mesmo estado visual (`aria-pressed`, check circular, botao `Proximo`) de Aluno/Responsavel.
- [x] Selecionar Professor e clicar `Proximo` abre a etapa de dados pessoais do mesmo wizard.
- [x] Selecionar Administrativo e clicar `Proximo` abre a etapa de dados pessoais do mesmo wizard.
- [x] Professor e Administrativo submetem `registration_profile=other` com `other_type_code` correto.
- [x] Professor e Administrativo reutilizam dados pessoais, saude e artes marciais.
- [x] Professor possui etapa para escolher turma ativa existente ou criar proposta em modal.
- [x] Turma ativa com professor atual aparece na selecao e registra revisao por gestao e professor atual.
- [x] Modal de proposta de horario usa checklist de dias da semana e aceita segunda a sexta no mesmo payload.
- [x] Administrativo possui etapa de areas administrativas solicitadas.
- [x] Ambos possuem etapa de condicao financeira unica, sem permitir permuta com PIX/conta bancaria.
- [x] Condicoes pagas exigem meio de recebimento e os campos de valor/percentual correspondentes.
- [x] As URLs `/register/teacher-proposal/` e `/register/admin-access/` redirecionam para o cadastro principal com perfil preselecionado.
- [x] O template/JS `request_wizard` publico antigo nao faz parte do contrato de cadastro.
- [x] Solicitacao administrativa publica salva payload com `training_intent`, `compensation_preference` e dados PIX quando aplicavel.
- [x] Proposta publica de professor salva payload com `payout_method` e dados de PIX/conta bancaria.
- [x] Aprovar professor novo com PIX cria/atualiza `TeacherBankAccount` do professor aprovado.

## Expected evidence
- Teste estatico do contrato do wizard.
- Testes de formulario/servico de solicitacao administrativa.
- Testes de formulario/servico de proposta de professor.
- `manage.py check`.
- Teste focado ou suite proporcional.
- Validacao visual desktop/mobile no navegador interno.

## Scope
- `templates/login/register.html`, `static/system/js/auth/register.js`, `static/system/css/auth/register.css`.
- `PortalRegistrationForm`, validacao leve e criacao de `other`.
- Redirecionamento das rotas publicas legadas.
- Forms, services e templates das solicitacoes de professor/administrativo ja existentes.
- Modelo/migration para payload estruturado em `AdministrativeAccessRequest`.
- Testes proporcionais nos contratos afetados.

## Out of scope
- Criar cobranca, mensalidade, folha ou repasse automatico para administrativo permuta/PIX.
- Resolver todo o contrato financeiro de conta bancaria tradicional.
- Mudar checkout de aluno/responsavel.

## Executed evidence
- `node --check static/system/js/auth/register.js`: OK.
- `python manage.py test system.tests.test_register_wizard_contract system.tests.test_administrative_access_request_views system.tests.test_class_catalog_request_views system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests`: 42 testes, OK.
- `python manage.py check`: OK, sem issues.
- `python manage.py makemigrations --check --dry-run`: OK, sem migrations pendentes.
- `python manage.py test system.tests.test_models.PersonModelTestCase.test_other_registration_creates_single_selected_type`: 1 teste, OK.
- `python manage.py test`: 425 testes, OK.
- `python manage.py test system.tests.test_register_wizard_contract.RegisterWizardStaticContractTestCase system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_requires_schedule_weekdays system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_accepts_multi_day_schedule_and_paid_pix system.tests.test_models.PersonModelTestCase.test_teacher_operational_registration_accepts_active_class_with_current_teacher_payload system.tests.test_models.PersonModelTestCase.test_paid_operational_registration_requires_payout_target system.tests.test_models.PersonModelTestCase.test_barter_operational_registration_clears_payout_fields system.tests.test_models.PersonModelTestCase.test_administrative_operational_registration_requires_requested_role`: 9 testes, OK.
- Navegador interno em `/register/?profile=teacher_request`: `register.css?v=24`, `register.js?v=47`, card Professor dentro do wizard, 4 turmas ativas renderizadas, turmas com professor atual mostrando aprovacao por gestao e professor atual, sem overflow.
- Navegador interno em Professor: modal `Criar horario` abriu com 7 checkboxes de dias, sem `#ui-teacher-schedule-weekday`; payload salvo com `weekdays=["monday","tuesday","wednesday","thursday","friday"]`.
- Navegador interno em Professor financeiro: `paid_mixed` exibiu valor fixo, percentual, PIX e ocultou banco; `barter` limpou PIX/valor/percentual e ocultou recebimento.
- Navegador interno em `/register/?profile=administrative_request`: card Administrativo dentro do wizard, subopcao sem fieldset nativo, 6 areas administrativas, payload `["people-support"]`, permuta sem PIX e sem overflow.
- Navegador interno em Aluno/Responsavel: Aluno com dependente ativou contador e total 12 etapas; Responsavel ativou contador e total 11 etapas; sem overflow.
- Navegador interno mobile 390x844: Administrativo no perfil sem overflow; Professor chegou em `step-teacher-schedule` com 4 cards e sem overflow.
- Navegador interno em `/register/teacher-proposal/`: redirecionou para `/register/?profile=teacher_request`, `register.css?v=24`, `register.js?v=47`, card Professor selecionado, sem `request-wizard-form`.
- Navegador interno desktop em Professor: avancou ate `step-teacher-schedule`, abriu modal `Criar horario`, salvou payload de horario e abriu `step-operational-finance`; alternar PIX exibiu campos de chave PIX e manteve conta bancaria oculta.
- Navegador interno em `/register/admin-access/?training_intent=none&compensation_preference=none`: redirecionou para `/register/?profile=administrative_request`, `register.css?v=24`, `register.js?v=47`, card Administrativo selecionado, sem `request-wizard-form`.
- Navegador interno desktop em Administrativo: avancou ate `step-administrative-access`, mostrou 6 areas, salvou payload `["people-support"]` e abriu `step-operational-finance`.
- Navegador interno mobile 390x844 em `/register/?profile=administrative_request`: sem overflow horizontal, `fieldsets=0`, `segmentCount=5`.
- Navegador interno mobile 390x844 na etapa `step-administrative-access`: sem overflow horizontal, 6 areas visiveis, cards com largura ajustada.
- Console do navegador interno: sem logs de erro.

## Cleanup / follow-up
- Template publico antigo `templates/class_requests/new_teacher_form.html` removido por estar orfao.
- Template/JS `request_wizard` removidos porque o contrato correto e o wizard principal.
- Views publicas legadas de professor/administrativo reduzidas a redirecionamentos puros para evitar metodos mortos e referencias a template removido.
- Debito fora do escopo: aprovacao operacional unificada a partir de `PreRegistration` ainda precisa de fluxo de gestao dedicado; esta entrega registra a solicitacao como pre-cadastro pendente e preserva os payloads para decisao.
- Debito fora do escopo: notificacao persistente para professor atual e administradores sobre troca de turma deve virar PRD propria, conectando `PreRegistration`, fila administrativa e historico de decisao sem ativar a pessoa antes da aprovacao.
