# PRD-123: Modal da conta do cliente com edição e exclusão

## Summary
Transformar o modal de `Dados do cliente` em uma área de conta funcional, permitindo visualizar, editar dados cadastrais próprios e encerrar o próprio cadastro com confirmação.

## Demand type
Django MVT + UI da home autenticada.

## Current problem
O modal atual exibe apenas dados básicos, plano e dependentes. Ele não oferece ação real de edição ou exclusão/desativação do cadastro, contrariando a expectativa de gestão da própria conta.

## Goal
Adicionar ações de conta no modal da home:
- ver dados principais;
- editar dados pessoais permitidos;
- excluir/encerrar o próprio cadastro de forma segura, preservando histórico financeiro e operacional.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/views/dependent_views.py`
- `system/services/portal_auth.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `templates/dependents/dependent_edit.html`
- `templates/dependents/dependent_registration_done.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/tests/test_home_dependents_section.py`
- `system/urls.py`
- `system/forms/dependent_forms.py`

### Internet / official documentation
- Django 5.2 official documentation via Context7: form handling, class-based `View`, session handling and test client.

### Context7 / MCPs / tools verified
- Context7 Django docs resolved as `/websites/djangoproject_en_5_2`.
- Browser interno disponível para validação em `http://127.0.0.1:8000/home/`.

### Limitations found
- Exclusão física de `Person` é perigosa em autosserviço porque pode remover ou conflitar com histórico financeiro, check-ins, mensalidades, pedidos e auditoria. A ação de usuário será `encerrar cadastro`: `Person.is_active=False`, `PortalAccount.is_active=False` e logout da sessão.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`
- `browser:control-in-app-browser`

## Understanding approved
A solicitação atual autoriza implementação: “corrija a tela deve ser possivel, ver, editar e excluir o cadastro. caso queira”.

## Execution prompt
### Persona
Agente Django/UI do LV JIU JITSU.

### Action
Implementar autosserviço de conta no modal da home.

### Context
O usuário autenticado é resolvido por `request.portal_person`. A home já tem modal estático com dados do cliente e padrão de modal para dependentes.

### Constraints
- Editar somente campos cadastrais próprios permitidos.
- Não permitir alteração de CPF, tipo de pessoa, plano, mensalidade, turmas ou papéis operacionais pelo autosserviço.
- Excluir pelo usuário significa desativar cadastro e acesso, preservando histórico.
- Backend decide permissão e estado.
- Sem `innerHTML` com dados do usuário.
- Não editar `staticfiles/`.

### Acceptance criteria
- [x] Modal exibe ação de editar cadastro.
- [x] Modal exibe ação destrutiva de excluir/encerrar cadastro com confirmação.
- [x] POST de edição salva campos permitidos e retorna erros por campo quando inválido.
- [x] Usuário não consegue editar nem excluir outro cadastro.
- [x] Encerrar cadastro desativa `Person` e `PortalAccount`, limpa sessão e redireciona para login.
- [x] UI atualiza dados visíveis após salvar sem navegar para outra tela.
- [x] Testes cobrem renderização, edição e exclusão/desativação.
- [x] Navegador interno valida caminho feliz e estado destrutivo protegido.

### Expected evidence
- `python manage.py test system.tests.test_home_dependents_section...`
- `python manage.py check`
- Browser interno: modal abre, edição salva, confirmação de exclusão visível.

### Output format
Fechamento curto com implementado, evidências, limitações e status.

## Scope
- Form restrito para conta do cliente.
- Views POST autenticadas para atualizar e desativar a própria conta.
- URLs de conta do cliente.
- Contexto da home com form e URLs.
- Modal com leitura, edição e zona de exclusão.
- JS para alternar painéis, enviar edição, renderizar erros e confirmar exclusão.
- CSS responsivo/temas.
- Testes focados.

## Out of scope
- Exclusão física de `Person`.
- Cancelamento automático de assinatura Stripe/Asaas.
- Alteração de plano, mensalidade, turmas, papéis operacionais ou CPF.
- CRUD administrativo de Pessoas.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-123-modal-conta-cliente-editar-excluir.md`
- `system/forms/person_forms.py`
- `system/forms/__init__.py`
- `system/views/home_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/tests/test_home_dependents_section.py`
- `templates/home/dashboard.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

## Risks and edge cases
- Usuário com mensalidade ativa encerra acesso, mas histórico permanece para gestão.
- E-mail inválido deve retornar erro por campo.
- Duplo submit deve manter estado coerente.
- Sessão deve ser encerrada após desativação.
- A interface não deve sugerir que dados financeiros foram apagados.

## Rules and constraints
- `Person.is_active=False` torna login inválido pelo middleware.
- `PortalAccount.is_active=False` bloqueia novo login local.
- Edição autosserviço não toca `person_type`, `cpf`, `class_enrollments`, `Membership`, `RegistrationOrder` ou `OperationalRole`.

## Visual hierarchy
- Cabeçalho: avatar, nome, perfis, fechar.
- Bloco 1: dados atuais e ações de edição.
- Bloco 2: formulário de edição recolhível.
- Bloco 3: zona de exclusão com texto de impacto e confirmação.

## Wireframe
### Modal
- Header: avatar + nome + badges + fechar.
- Região `Dados atuais`: CPF, e-mail, telefone, nascimento, endereço curto, plano, dependentes.
- Ações: `Editar cadastro` secundário, `Excluir cadastro` destrutivo.
- Região `Editar cadastro`: campos em grid; botões `Salvar alterações` e `Cancelar`.
- Região `Excluir cadastro`: aviso + checkbox/confirmação textual + botão destrutivo.

## State machine
### Modal de conta
- `closed` -> `viewing` -> `editing` -> `saving` -> `saved` ou `error`.
- `viewing` -> `delete-confirm` -> `deleting` -> `logged-out` ou `error`.

## Plan
- [x] Criar testes focados.
- [x] Implementar form restrito.
- [x] Implementar views POST.
- [x] Atualizar URLs e exports.
- [x] Atualizar modal, CSS e JS.
- [x] Executar testes e browser interno.

## Test plan
### Tests to author
- Home renderiza ações de conta no modal.
- POST de edição atualiza nome/e-mail/telefone e preserva CPF.
- POST inválido retorna JSON 400 com erro de campo.
- POST de exclusão desativa pessoa e portal account e limpa sessão.

### Execution authorization
Autorizada pela solicitação operacional atual.

### Execution evidence
- Vermelho inicial: testes focados falharam por ausência de rotas/ações do modal.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_home_uses_client_profile_modal_instead_of_large_header system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_update_changes_allowed_fields_and_preserves_cpf system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_update_returns_field_errors system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_deactivate_disables_person_account_and_session` -> OK, 4 testes.
- `.\.venv\Scripts\python.exe manage.py check` -> OK, sem issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_calendar` -> OK, 111 testes.

## Visual validation
- Navegador interno em `http://127.0.0.1:8000/home/`.
- Modal abriu com `Editar cadastro` e `Excluir cadastro`.
- Edição abriu no próprio modal com campos preenchidos.
- Salvamento de telefone `(11) 97777-4455` atualizou a visualização sem navegar e sem erros de campo.
- Zona de exclusão abriu confirmação textual com `ENCERRAR`, rota local `/account/profile/deactivate/` e aviso de preservação de histórico; a exclusão real não foi executada na validação visual.
- Console do navegador interno sem erros.
- Viewport mobile `390x844`: modal visível, largura 358px, sem overflow horizontal.
- Após reinício do servidor local, a home carregou `dashboard.js?v=18`; o modal abriu com ações de editar/excluir e foi fechado sem deixar `body.modal-open`.

## ORM validation
- `manage.py shell`: `Person(email='aluno.local.stripe.445521@example.com')` persistiu telefone `(11) 97777-4455` e permaneceu `is_active=True` após validação sem exclusão.

## Quality validation
- `manage.py check`: OK.
- Teste focado de conta: OK.
- Suíte proporcional `test_home_dependents_section` + `test_calendar`: OK.

## Evidence
- Form restrito `ClientProfileForm` não inclui CPF, papéis, plano, mensalidade ou turmas.
- Views POST exigem sessão do portal e usam somente `request.portal_person`.
- Desativação autosserviço usa `Person.is_active=False`, `PortalAccount.is_active=False` e limpa a sessão.
- JS usa `textContent`/FormData/fetch e não injeta dados do usuário via `innerHTML`.

## Implemented
- Modal de conta com leitura, edição e zona de exclusão.
- Endpoints `account/profile/update/` e `account/profile/deactivate/`.
- Testes de renderização, edição válida, erro de campo e desativação/logout.
- CSS responsivo para desktop/mobile e temas.

## Cleanup findings
- Exclusão física e cancelamento automático de assinatura permanecem fora do escopo por segurança operacional.

## Follow-up PRDs
Nenhum até agora.

## Deviations from plan
Nenhuma até agora.

## Pending
- Sem pendência dentro deste escopo.
- Follow-up recomendado, se desejado: fluxo administrativo para reativar cadastro encerrado e tratar assinatura ativa após encerramento autosserviço.

## Final status
Concluída.
