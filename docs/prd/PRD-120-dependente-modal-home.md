# PRD-120: Dependente em modal na home

## Summary
Corrigir o fluxo autenticado de adicionar dependente para funcionar como popup/modal sobre a home, e não como uma tela standalone em `/dependents/add/`.

## Demand type
Correção de UX e fluxo visual autenticado com impacto em Django MVT, template, CSS, JS e testes.

## Current problem
- A ação "Adicionar dependente" leva o usuário para `/dependents/add/`, criando uma superfície separada.
- O usuário espera um popup/modal a partir da home, no padrão dos demais fluxos operacionais curtos.
- Após pagamento de pré-cadastro de dependente, o retorno também envia para `/dependents/add/`, mantendo o comportamento de tela.

## Goal
O usuário inicia, continua e conclui o cadastro de dependente como modal aberto sobre a home. A rota `/dependents/add/` fica como conteúdo do modal quando chamada com `?modal=1`; acesso direto redireciona para `/home/?dependent_modal=1`.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-118-adicionar-dependente-pos-matricula.md`
- `docs/prd/PRD-119-dependente-materiais-idempotencia-cpf.md`
- `system/views/home_views.py`
- `system/views/dependent_views.py`
- `system/views/payment_views.py`
- `system/urls.py`
- `templates/dependents/dependent_registration.html`
- `static/system/css/dependents/dependent_registration.css`
- `static/system/js/home/dashboard.js`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`

### Internet / official documentation
- Django 5.2 class-based views and test client: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/ and https://docs.djangoproject.com/en/5.2/topics/testing/tools/
  - Conclusão: a view pode diferenciar variante modal por query string e testes podem cobrir `GET` com parâmetros.
- MDN `HTMLDialogElement.showModal()`: https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal
  - Conclusão: `showModal()` exibe o dialog na camada superior, torna o restante do documento inerte e bloqueia interação de fundo.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: consultado para `TemplateView`, `get_context_data` e `Client.get(..., query_params=...)`.
- PowerShell e `rg`: funcionais.

### Limitations found
- A home atual já usa modais por overlay customizado, mas a correção usará `<dialog>` para o novo modal por ser nativo e compatível com popup de formulário longo.
- Pagamento externo real não faz parte desta correção; a validação cobre redirecionamento local para reabrir modal.
- O navegador interno havia falhado na PRD-119; nesta PRD a validação deve ser tentada novamente e registrada.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
A solicitação atual diz "deveria ser um pop up nao uma tela corrija". Isso autoriza implementar a correção visual e funcional do fluxo de dependente para modal na home.

## Execution prompt
### Persona
Agente sênior Django/MVT do LV JIU JITSU, com TDD e validação visual no navegador interno.

### Action
Transformar a experiência de adicionar dependente em modal sobre a home, preservando validação server-side, pagamentos e finalização já implementados.

### Context
PRD-118 criou `/dependents/add/` como wizard autenticado. PRD-119 adicionou materiais, idempotência e CPF pendente. O comportamento atual cumpre regra de negócio, mas viola a expectativa de UX: abrir como popup.

### Constraints
- Não remover nem reescrever a lógica de `DependentRegistrationForm` e services.
- Não criar pessoa antes dos pagamentos/condições já implementadas.
- Não mover validação para JS.
- Não editar `staticfiles/`.
- Atualizar `?v=` de assets alterados.
- Acesso direto a `/dependents/add/` não deve deixar o usuário em tela standalone.

### Acceptance criteria
- [x] Home renderiza modal de adicionar dependente com iframe ou corpo carregável.
- [x] Botões/links "Adicionar dependente" na home abrem o modal, não navegam para uma tela standalone quando JS está ativo.
- [x] `/dependents/add/?modal=1` renderiza o wizard em modo modal.
- [x] `/dependents/add/` autenticado redireciona para `/home/?dependent_modal=1`.
- [x] `/home/?dependent_modal=1` abre o modal automaticamente.
- [x] POST inválido em modo modal re-renderiza erros dentro do modal.
- [x] POST finalizado em modo modal sinaliza conclusão para a home e recarrega a home.
- [x] Retorno de pagamento de dependente redireciona para home com modal aberto.
- [x] Modal fecha por botão, backdrop e Esc.
- [x] Testes focados cobrem home/modal, rota direta, variante modal e retorno de pagamento.
- [x] Browser interno valida desktop/mobile, tema claro/escuro e console sem erro crítico.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1`
- `.\.venv\Scripts\python.exe manage.py check`
- `node --check` no JS alterado/criado.
- Navegador interno em `/home/` e `/home/?dependent_modal=1`.

### Output format
Resumo da correção, evidências reais, validação visual, limitações e status.

## Scope
- Ajustar home para abrir modal de dependente.
- Ajustar view/template de dependente para variante modal.
- Ajustar retorno de pagamento dependente para reabrir modal na home.
- Criar JS mínimo para abrir/fechar modal e receber conclusão do iframe.
- Atualizar testes focados e PRD.

## Out of scope
- Redesenhar todo o wizard de dependente.
- Trocar gateway ou simular pagamento real.
- Reescrever a home inteira.
- Criar foundation CRUD compartilhada.

## Impacted files
| Arquivo | Mudança esperada |
|---|---|
| `system/views/home_views.py` | URLs e flag para modal aberto |
| `system/views/dependent_views.py` | Redirect de acesso direto e resposta de conclusão modal |
| `system/views/payment_views.py` | Retorno de pagamento para home com modal |
| `templates/home/dashboard.html` | Modal de dependente e links de abertura |
| `templates/dependents/dependent_registration.html` | Variante modal |
| `templates/dependents/dependent_registration_done.html` | Sinalização de sucesso para parent |
| `static/system/js/home/dashboard.js` | Abrir/fechar modal e postMessage |
| `static/system/js/dependents/dependent_registration.js` | Fechar frame e sinalizar submissão |
| `static/system/js/dependents/dependent_registration_done.js` | Notificar conclusão |
| `static/system/css/home/dashboard.css` | Layout do modal |
| `static/system/css/dependents/dependent_registration.css` | Compactação modal |
| `system/tests/test_home_dependents_section.py` | Contrato da home/modal |
| `system/tests/test_dependent_registration.py` | Contrato da rota modal |
| `docs/prd/README.md` | Índice |

## Risks and edge cases
- Se o modal concluir e a home não recarregar, dependente recém-criado não aparece.
- Se pagamento externo voltar para iframe, pode carregar home dentro do iframe; o retorno local prioriza home top-level com modal.
- Usuário sem JS ainda pode acessar `?modal=1`; regra server-side e permissões permanecem.
- Backdrop/Esc não podem perder dados por acidente sem intenção; fechamento manual apenas fecha o modal, sem apagar rascunho em sessão.

## Rules and constraints
- Modal novo usa `<dialog>` e `showModal()`.
- O iframe carrega apenas rota same-origin.
- Comunicação iframe-parent usa `postMessage` com validação de origem.
- Sem `innerHTML` com dados do usuário.
- CSS por tokens, sem `staticfiles/`.

## Plan
- [x] 1. Criar PRD-120.
- [x] 2. Escrever testes Red.
- [x] 3. Implementar view/context/modal template.
- [x] 4. Implementar JS/CSS.
- [x] 5. Executar testes/check/node.
- [x] 6. Validar no navegador interno.
- [x] 7. Auditar diff e atualizar PRD.

## Test plan
### Tests to author
- `test_student_without_dependents_can_start_dependent_registration_in_modal`
- `test_home_query_opens_dependent_modal`
- `test_direct_authenticated_get_redirects_to_home_modal`
- `test_modal_get_renders_wizard_content`
- `test_modal_family_plan_completion_returns_modal_done`
- Atualizar retorno de pagamento para esperar `/home/?dependent_modal=1`.

### Execution authorization
Autorizada pela solicitação atual. Pagamento externo real fora do escopo.

### Execution evidence
- Red inicial: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1` falhou em 7 pontos esperados: home sem modal, rota direta sem redirect, pagamentos retornando para `/dependents/add/` e wizard sem variante modal.
- Red adicional do iframe: `test_product_catalog_renders_in_dependent_wizard` falhou com `X-Frame-Options: DENY`; corrigido para `SAMEORIGIN`.
- Green final: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration --verbosity 1` -> 17 testes OK.
- Regressão completa: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` -> 450 testes OK.
- `.\.venv\Scripts\python.exe manage.py check` -> sem issues.
- `node --check static\system\js\home\dashboard.js` -> OK.
- `node --check static\system\js\dependents\dependent_registration.js` -> OK.
- `node --check static\system\js\dependents\dependent_registration_done.js` -> OK.

## Visual hierarchy
- Home continua como superfície principal.
- Modal ocupa largura operacional grande, centralizado, com título compacto e botão fechar.
- Wizard dentro do iframe perde a aparência de página standalone e fica compacto.
- Ação "Adicionar dependente" permanece no cabeçalho da seção e no estado vazio.

## Wireframe
### Região: Home / Seção Dependentes
- Cabeçalho `Dependentes` ou `Meus dependentes`.
- Botão `Adicionar dependente` com classe de abertura modal.
- Estado vazio com botão primário abrindo o mesmo modal.

### Região: Modal
- `<dialog>` com cabeçalho:
  - Eyebrow: `Dependentes`
  - Título: `Adicionar dependente`
  - Botão fechar icônico.
- Corpo:
  - iframe same-origin para `/dependents/add/?modal=1`.
- Estados:
  - Carregando: iframe vazio/carregando.
  - Editando: wizard visível.
  - Erro: erros por campo dentro do iframe.
  - Sucesso: iframe envia `dependent-modal-done`; parent fecha e recarrega.

## State machine
### Modal de dependente
- `closed` -> `open`
- `open` -> `submitting`
- `submitting` -> `error`
- `submitting` -> `done`
- `done` -> `reload_home`
- `open` -> `closed`

## Visual validation
- [x] Desktop `/home/` abre modal.
- [x] Mobile `/home/` abre modal sem overflow horizontal.
- [x] `/home/?dependent_modal=1` abre modal automaticamente.
- [x] Tema claro.
- [x] Tema escuro.
- [x] Console sem erro crítico.

## ORM validation
- Não há mudança de schema ou persistência nova nesta PRD.

## Quality validation
- [x] Testes focados.
- [x] `manage.py check`.
- [x] `node --check`.
- [x] Diff revisado.

## Evidence
- Navegador interno em `http://127.0.0.1:8000/dependents/add/`: redirecionou para `http://127.0.0.1:8000/home/?dependent_modal=1`, com `title = "Início — LV Jiu Jitsu"`, `modalOpen = true`, `isStandaloneDependentPage = false`, iframe `/dependents/add/?modal=1`, wizard presente e sem erro de conexão recusada.
- Navegador interno em `http://127.0.0.1:8000/home/?dependent_modal=1`: modal abriu automaticamente, iframe carregou `Dados pessoais`, `Condição financeira` e `Materiais opcionais`.
- Layout desktop 1280x900: modal 1040x820 dentro da viewport, sem overflow horizontal.
- Layout mobile 390x844: modal dentro da viewport, sem overflow horizontal.
- Tema escuro inicial e tema claro após toggle: modal continuou abrindo com wizard.
- Console do navegador interno após navegação limpa: `errorLogs = []`.
- Fechamento validado por botão, backdrop e Esc dentro do formulário do iframe.

## Implemented
- Home renderiza `<dialog id="dependent-registration-modal">` e links `js-open-dependent-modal` para `/dependents/add/?modal=1`.
- `DependentRegistrationView` redireciona GET direto para `/home/?dependent_modal=1`, renderiza modo modal com `?modal=1`, devolve página de conclusão para o iframe e permite frame `SAMEORIGIN`.
- Retorno de pagamento de pré-cadastro de dependente reabre a home com o modal.
- JS da home abre/fecha o modal, limpa query state, valida `postMessage` por origem e recarrega a home na conclusão.
- JS do iframe fecha por botões/Esc e sinaliza conclusão.
- CSS da home e do wizard ajustado para modal responsivo.

## Cleanup findings
- O erro de iframe bloqueado por `X-Frame-Options: DENY` foi identificado apenas na validação visual e coberto por teste.
- O workspace já continha mudanças anteriores em arquivos compartilhados da home/cadastro; foram preservadas.
- Nenhuma edição em `staticfiles/`.

## Follow-up PRDs
Nenhum follow-up aberto nesta PRD.

## Deviations from plan
- A implementação precisou adicionar `xframe_options_sameorigin` na view modal para permitir iframe same-origin.

## Pending
Sem pendências conhecidas no escopo desta PRD.

## Final status
Concluída.
