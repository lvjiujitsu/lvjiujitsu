# PRD-119: Dependente com materiais, idempotência e CPF pendente

## Summary
Remover as pendências da PRD-118 no fluxo autenticado de adicionar dependente: incluir materiais opcionais no wizard, tornar o POST tolerante a duplo envio/refresh e bloquear CPF já usado em pré-cadastro pendente pelo mesmo responsável.

## Demand type
Follow-up funcional com impacto em Django MVT, UI de wizard, pagamento de materiais e integridade de pré-cadastro.

## Current problem
- O wizard `/dependents/add/` finaliza dependente sem oferecer materiais opcionais, embora o fluxo público já possua catálogo e pagamento de materiais antes da finalização.
- `DependentRegistrationView.post()` cria novo `PreRegistration` para cada POST válido que exige pagamento, podendo duplicar rascunhos/checkout em reenvio.
- O form só bloqueia CPF existente em `Person` ativo; um mesmo responsável pode criar outro pré-cadastro pendente para o mesmo CPF.
- Finalização repetida após criação do dependente hoje vira erro de CPF ativo em vez de resolver de forma idempotente.

## Goal
O responsável/aluno autenticado adiciona dependente com materiais opcionais dentro do mesmo wizard, sem duplicar pessoa, pedido ou pré-cadastro em reenvio, e sem conseguir abrir dois pré-cadastros pendentes para o mesmo CPF.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-118-adicionar-dependente-pos-matricula.md`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/prd/PRD-009-loja-portal-prepedido-historico.md`
- `docs/prd/PRD-106-responsavel-compra-materiais-para-dependente.md`
- `system/models/pre_registration.py`
- `system/models/registration_order.py`
- `system/models/product.py`
- `system/forms/dependent_forms.py`
- `system/forms/product_forms.py`
- `system/services/dependent_registration.py`
- `system/services/registration_checkout.py`
- `system/services/product_backorders.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/views/dependent_views.py`
- `system/views/product_views.py`
- `system/views/payment_views.py`
- `system/views/auth_views.py`
- `system/urls.py`
- `templates/dependents/dependent_registration.html`
- `templates/products/product_store.html`
- `static/system/css/dependents/dependent_registration.css`
- `static/system/js/products/store_cart.js`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_product_store.py`

### Adjacent files consulted
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`

### Internet / official documentation
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
  - Conclusão: múltiplas escritas do fluxo final devem ficar em `transaction.atomic`; exceções de banco não devem ser mascaradas dentro do bloco atômico.
- Django 5.2 form validation: https://docs.djangoproject.com/en/5.2/ref/forms/validation/
  - Conclusão: CPF pendente, materiais selecionados e pagamento de materiais precisam ser validados server-side no `Form.clean()`.
- Django 5.2 QuerySet `select_for_update`: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
  - Conclusão: consistência de estoque e reutilização de pré-cadastro dependem de transações/locks quando houver escrita concorrente.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: consultado para `transaction.atomic`, `select_for_update`, `Form.clean()` e `FormView`/POST.
- PowerShell e `rg`: funcionais.

### Limitations found
- O fluxo de materiais de pré-cadastro atual usa Asaas, não Stripe, em `create_pre_registration_materials_payment`.
- Não haverá gateway externo real nesta implementação sem nova autorização operacional; testes usam mocks/retornos locais.
- A PRD não altera schema nem `RegistrationOrderItem`; a variante segue resolvida pelo snapshot textual já existente.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
A solicitação atual enumera exatamente as três pendências registradas na PRD-118. O escopo está autorizado como follow-up da implementação anterior: materiais opcionais no wizard, idempotência de reenvio e bloqueio de CPF pendente.

## Execution prompt
### Persona
Agente sênior Django/MVT do LV JIU JITSU, com TDD, services transacionais e validação visual no navegador interno.

### Action
Implementar o follow-up do wizard autenticado de dependente, mantendo o contrato de pagamento antes da pessoa e sem reescrever a loja pública/autenticada.

### Context
O sistema já possui `PreRegistration`, pagamento de plano por pré-cadastro, pagamento de materiais por pré-cadastro, catálogo de produtos por variante e loja autenticada. O wizard de dependente deve reaproveitar esses contratos em uma etapa própria.

### Constraints
- Não criar `Person` antes de plano/material obrigatório estar resolvido.
- Não duplicar `PreRegistration` pendente do mesmo responsável para o mesmo CPF.
- Não duplicar dependente em duplo POST ou refresh.
- Não baixar estoque sem pagamento confirmado.
- Não mover regra de negócio para template/JS.
- Não editar `staticfiles/`.
- Atualizar `?v=` se asset versionado mudar.

### Acceptance criteria
- [x] Wizard `/dependents/add/` exibe etapa "Materiais opcionais" com catálogo de variantes em estoque.
- [x] Se nenhum material for selecionado, o fluxo segue para finalização sem cobrança de material.
- [x] Se material for selecionado, o wizard exige PIX/cartão Asaas para materiais e só finaliza após `materials_paid`.
- [x] Pagamento de material de dependente grava `materials_payment` no `PreRegistration.form_snapshot`.
- [x] Retorno `payment-success?stage=materials` de fluxo dependente volta para `/dependents/add/` e marca `materials_paid`.
- [x] CPF ativo já vinculado ao mesmo responsável torna o POST idempotente e redireciona para home, sem erro e sem duplicar.
- [x] CPF ativo sem vínculo com o responsável continua bloqueado.
- [x] CPF em pré-cadastro pendente do mesmo responsável bloqueia novo POST quando não é o mesmo rascunho da sessão.
- [x] Reenvio de POST com pagamento de plano pendente reutiliza o `PreRegistration` existente da sessão/responsável.
- [x] Testes focados cobrem materiais selecionados, materiais pulados, retorno de material, CPF pendente e finalização idempotente.
- [ ] Browser interno valida desktop/mobile, tema claro/escuro e console sem erro crítico.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store`
- `.\.venv\Scripts\python.exe manage.py check`
- ORM local para `PreRegistration.form_snapshot["materials_paid"]`, pessoa criada uma vez e ausência de duplicidade.
- Navegador interno em `/dependents/add/` e `/home/`.

### Output format
PRD atualizada, testes e checks reais, validação visual, resumo de implementação, pendências e status.

## Scope
- Estender `DependentRegistrationForm` com seleção opcional de materiais por variante.
- Reaproveitar o catálogo de produtos já existente.
- Estender o service de dependente para buscar/reusar pré-cadastro pendente e aplicar idempotência de finalização.
- Estender `PaymentSuccessView` para estágio `materials` do fluxo de dependente.
- Ajustar template/CSS do wizard de dependente.
- Atualizar testes focados.

## Out of scope
- Redesign amplo da loja `/store/`.
- Histórico de compras e mensalidades fora do que já existe.
- Backorder dentro do wizard de dependente.
- Pagamento externo real em Asaas/Stripe.
- Nova migration/schema.

## Impacted files
| Arquivo | Mudança esperada |
|---|---|
| `system/forms/dependent_forms.py` | Validação de CPF pendente e materiais |
| `system/services/dependent_registration.py` | Reuso de pré-cadastro, snapshot de materiais e idempotência |
| `system/views/dependent_views.py` | Orquestração de plano/material/finalização |
| `system/views/payment_views.py` | Retorno de materiais do fluxo dependente |
| `templates/dependents/dependent_registration.html` | Etapa de materiais opcionais |
| `static/system/css/dependents/dependent_registration.css` | Layout dos materiais no wizard |
| `system/tests/test_dependent_registration.py` | Testes de contrato |
| `docs/prd/README.md` | Índice da PRD |

## Risks and edge cases
- Duplo clique simultâneo pode chegar antes da sessão salvar; mitigação adicional busca por rascunho pendente do mesmo owner/CPF.
- Produto pode ficar sem estoque entre renderização e POST; mitigação via validação server-side em `resolve_selected_product_items`.
- Pagamento de materiais pode ser confirmado antes do retorno visual; `PaymentSuccessView` deve aceitar idempotência de snapshot.
- CPF ativo de pessoa vinculada ao mesmo responsável deve ser tratado como sucesso idempotente, não como erro.

## Rules and constraints
- `transaction.atomic` em finalização e criação/reuso de pré-cadastro.
- Validação server-side manda; UI só coleta.
- Mensagens em pt-BR.
- Sem `innerHTML` novo.
- Sem hardcode de produto/plano/CPF.

## Plan
- [x] 1. Criar PRD-119.
- [x] 2. Adicionar testes Red.
- [x] 3. Implementar form/service/view.
- [x] 4. Atualizar template/CSS.
- [x] 5. Executar testes e `check`.
- [ ] 6. Validar no navegador interno.
- [x] 7. Auditar diff e atualizar PRD.

## Test plan
### Tests to author
- `test_materials_selected_after_plan_payment_redirects_to_materials_payment`
- `test_materials_success_returns_to_dependent_flow`
- `test_paid_resume_with_materials_paid_finalizes_once`
- `test_same_owner_pending_pre_registration_blocks_duplicate_cpf`
- `test_existing_owned_dependent_submission_is_idempotent`
- `test_product_catalog_renders_in_dependent_wizard`

### Execution authorization
Autorizada localmente. Pagamento externo real fora do escopo.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration --verbosity 2`
  - Red inicial: falhas esperadas para catálogo de materiais ausente, retorno `stage=materials`, CPF pendente e idempotência.
  - Green após implementação: 11 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store --verbosity 2`
  - 19 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_stripe_webhook_view --verbosity 1`
  - 28 testes OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 1`
  - 446 testes OK em 95.739s.
- `.\.venv\Scripts\python.exe manage.py check`
  - `System check identified no issues (0 silenced).`
- `git diff --check -- docs/prd/PRD-119-dependente-materiais-idempotencia-cpf.md docs/prd/README.md system/forms/dependent_forms.py system/services/dependent_registration.py system/views/dependent_views.py system/views/payment_views.py templates/dependents/dependent_registration.html static/system/css/dependents/dependent_registration.css system/tests/test_dependent_registration.py`
  - Sem erro de whitespace; apenas avisos de CRLF em arquivos já tocados.

## Visual hierarchy
- Wizard mantém topo atual, etapas numeradas e CTA final.
- Materiais aparecem depois da condição financeira, como etapa 5.
- Cada produto fica em bloco simples: nome, preço, variantes/estoque e quantidade.
- A escolha de pagamento de materiais fica próxima do catálogo.

## Wireframe
### Região: Etapa 5 — Materiais opcionais
- Título: `Materiais opcionais`
- Subtítulo: `Selecione materiais para o dependente ou deixe tudo zerado para comprar depois.`
- Lista:
  - Produto
  - Preço
  - Variante/tamanho/cor
  - Campo quantidade com máximo do estoque
- Pagamento:
  - `Comprar depois`
  - `PIX`
  - `Cartão`
- Erro por campo/lista quando estoque inválido.

### Região: Ações
- Cancelar
- `Finalizar dependente`, `Pagar materiais` ou `Ir para pagamento`, conforme estado.

## State machine
### Dependente
- `draft` -> `plan_payment_pending`
- `plan_payment_pending` -> `plan_paid`
- `plan_paid` -> `materials_pending`
- `materials_pending` -> `materials_paid`
- `plan_paid` -> `materials_skipped`
- `materials_paid|materials_skipped|family_plan` -> `finalized`
- `finalized` + novo POST -> `already_finalized`

## Visual validation
- [x] Renderização autenticada via Django Client em `/dependents/add/`.
- [x] HTML contém etapa `Materiais opcionais`.
- [x] HTML contém campo dinâmico `material_variant_<id>` para variante ativa em estoque.
- [x] HTML contém opções `Comprar depois`, `PIX` e `Cartão`.
- [x] POST autenticado com material selecionado e `Comprar depois` retorna erro server-side correto.
- [ ] Desktop `/dependents/add/` no navegador interno.
- [ ] Mobile `/dependents/add/` no navegador interno.
- [ ] Tema claro no navegador interno.
- [ ] Tema escuro no navegador interno.
- [ ] Console sem erro crítico no navegador interno.

Limitação: o plugin do navegador interno foi conectado e a documentação foi lida, mas as chamadas `browser.tabs.list()` e `browser.tabs.selected()` travaram até timeout mesmo após reconectar e ler `browser-troubleshooting`. Não foi usado navegador externo.

## ORM validation
- [x] Mesmo owner/CPF não cria dois `PreRegistration` ativos.
- [x] `materials_payment` e `materials_paid` ficam no snapshot.
- [x] `Person` de dependente é criada uma vez.

## Quality validation
- [x] Testes focados.
- [x] `manage.py check`.
- [x] Diff revisado.

## Evidence
- Testes focados e suíte completa executados localmente com sucesso.
- Renderização autenticada por Django Client retornou:
  - `get_status: 200`
  - `has_materials_step: True`
  - `has_variant_field: True`
  - `has_materials_checkout_options: True`
  - `post_status: 200`
  - `has_material_payment_error: True`
  - `default_cta_requires_payment: True`
  - `pending_count_for_validation_cpf: 0`
- O navegador interno não foi validado visualmente por falha do plugin de controle.

## Implemented
- `DependentRegistrationForm` agora monta campos dinâmicos para variantes ativas em estoque, valida quantidades, exige PIX/cartão quando há material selecionado e bloqueia CPF em pré-cadastro pendente do mesmo responsável.
- O mesmo CPF ativo já vinculado ao responsável é tratado como sucesso idempotente.
- `dependent_registration` reutiliza `PreRegistration` pendente do mesmo owner/CPF, persiste seleção de materiais no snapshot, preserva estados de pagamento e finaliza com `select_for_update`.
- Retorno de pagamento `stage=materials` para fluxo dependente marca `materials_paid` e volta para `/dependents/add/`.
- Ao finalizar dependente com materiais pagos, o sistema cria pedido de produto pago uma única vez, aplica financeiro e baixa estoque.
- Template/CSS adicionam a etapa `Materiais opcionais` no wizard e ajustam o CTA para depender da escolha real de plano familiar ou pagamento confirmado.

## Cleanup findings
- Nenhum código morto ou arquivo temporário introduzido no escopo.
- `staticfiles/` não foi alterado.
- `git diff --check` sem erro de whitespace nos arquivos do follow-up.

## Follow-up PRDs
- Não há novo follow-up funcional aberto por esta PRD.

## Deviations from plan
- A validação visual no navegador interno não pôde ser executada porque o plugin travou ao listar/selecionar abas. A validação substituta foi feita por Django Client autenticado, testes focados e suíte completa.

## Pending
- Validar visualmente desktop/mobile/tema/console no navegador interno quando o plugin voltar a responder.

## Final status
Concluída com limitação de validação visual no navegador interno.
