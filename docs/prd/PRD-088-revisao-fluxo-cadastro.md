# PRD-088: Revisão completa do fluxo de cadastro — pré-registro, pagamento sequencial e finalização explícita

> **SUPERADO PELO PRD-040 EM 2026-05-21.**
> Este PRD registrava uma solucao intermediaria com `Person(is_active=False)` antes da finalizacao.
> Essa abordagem nao e mais aceita.
> A fonte de verdade vigente e `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`: mensalidade e materiais devem ser pagos antes de qualquer criacao de `Person`, `PortalAccount`, relacionamentos, turmas ou acesso.

## Resumo do que será implementado

Reestruturação completa do fluxo de cadastro público para que:

1. O cadastro da pessoa (Person, PortalAccount, ClassEnrollment) **não seja ativado** antes do usuário clicar em "Finalizar cadastro"
2. O pagamento do **plano** ocorra primeiro (Stripe ou PIX), separado do pagamento de **materiais**
3. O pagamento de **materiais** siga o mesmo padrão do plano (checkout dedicado), não bundled
4. Uma **tela de resumo** mostre tudo que foi pago antes da finalização
5. "Finalizar cadastro" seja o único ponto que ativa o registro completo no sistema

---

## Tipo de demanda

Correção arquitetural + nova feature (fluxo de pagamento sequencial)

---

## Problema atual

### 1. Registro criado antes do pagamento

Em `PortalRegisterView.form_valid()`, a chamada `create_portal_registration()` acontece imediatamente:

```python
# system/services/registration.py — create_portal_registration()
# Person + PortalAccount + ClassEnrollment são criados HERE
result = _create_holder_registration(cleaned_data, person_types)
# DEPOIS disso, order é criada
result["order"] = create_registration_order(result["holder"], cleaned_data)
```

Consequência: se o pagamento falha ou o usuário abandona, a pessoa fica persistida no banco com CPF "tomado". Na próxima tentativa, o form retorna "CPF já cadastrado no sistema." e o cadastro quebra completamente.

### 2. Materiais pagos junto com o plano (sem fluxo próprio)

`create_registration_order()` inclui plano + produtos em um único `RegistrationOrder`. Não há tela de checkout para materiais — tudo é somado e pago de uma vez. O usuário não vê um fluxo explícito de materiais com confirmação separada.

### 3. Redirecionamentos para login incorretos

Após `PaymentSuccessView`, o fluxo redireciona de volta ao `/register/` com flag de sessão (`post_payment_complete`). Isso é frágil e causa:
- Wizard recarregado do zero sem os dados do usuário
- `DeferPaymentView` redireciona para `system:login` mesmo quando deveria ir para dashboard
- `PaymentCancelView` redireciona para login inapropriadamente

### 4. Pós-pagamento inconsistente

Após o pagamento Stripe, `PaymentSuccessView` faz auto-login e redireciona para `/register/`. O wizard carrega em "modo pós-pagamento" mas sem os dados preenchidos pelo usuário, porque:
- O formulário foi submetido e a sessão Django não preservou os dados
- O `localStorage` ainda tem o draft, mas a página recarrega do zero sem o estado do wizard

---

## Objetivo

Garantir que:
- **Antes da finalização**: apenas o registro financeiro (RegistrationOrder) existe — a pessoa está em estado `is_active=False`
- **Plano e materiais**: cada um tem seu próprio checkout (Stripe/PIX), sequential
- **Finalizar cadastro**: único ponto que ativa `Person.is_active=True` e concede acesso ao portal

---

## Context Ledger

### Arquivos lidos integralmente

- `system/forms/registration_forms.py` — 740 linhas, form completo com validações
- `system/services/registration.py` — 403 linhas, `create_portal_registration()` e sub-funções
- `system/services/registration_checkout.py` — 462 linhas, `create_registration_order()`, `create_product_only_order()`
- `system/views/auth_views.py` — 250 linhas, `PortalRegisterView.form_valid()`
- `system/views/payment_views.py` — 263 linhas, `PaymentSuccessView`, `DeferPaymentView`
- `system/views/asaas_views.py` — 278 linhas, `CreatePixChargeView`
- `system/models/registration_order.py` — 276 linhas, `RegistrationOrder.person` (NOT NULL FK)
- `system/models/person.py` — Person com `is_active = models.BooleanField(default=True)` (linha 128)
- `system/services/portal_auth.py` — 80 linhas, `resolve_portal_account_from_session` filtra por `person__is_active=True`

### Fato arquitetural crítico

`RegistrationOrder.person` é **NOT NULL** FK. Não é possível criar um order sem ter um Person primeiro. A solução sem nova migration é: **criar Person com `is_active=False`** — o campo já existe e já é verificado em `resolve_portal_account_from_session`.

### Sem migração nova

`Person.is_active` já existe. Nenhuma mudança de schema é necessária para implementar este PRD.

---

## Fluxo desejado completo

```
[Wizard steps 1–5]
Tipo → Dados pessoais → Jiu Jitsu → Prontuário → Turmas
         (client-side, localStorage draft)
                ↓
[Step 6: Plano]
Seleciona plano → escolhe forma de pagamento
"Pagar plano" → POST form → cria Person(is_active=False) + RegistrationOrder(plano)
                              armazena person_id na sessão
                ↓
[Checkout plano]
Stripe (cartão) ou PIX → pagamento confirmado
                ↓
[PaymentSuccessView — plano pago]
auto-login → sessão: plan_paid=True, plan_order_id=X, reg_person_id=Y
→ redirect → /register/ (wizard step: materiais)
                ↓
[Step 7: Materiais] ← NOVO STEP APÓS PLANO PAGO
Exibe badge "✓ Plano pago"
Catálogo de produtos com seleção (select Cor + select Tamanho + qty)
[Pagar materiais] ou [Finalizar sem materiais]
                ↓ (se materiais)
POST → MaterialsCheckoutView → cria RegistrationOrder(produtos, person=sessão person)
→ Stripe ou PIX → pagamento confirmado
→ PaymentSuccessView (materiais) → sessão: materials_paid=True, materials_order_id=Z
→ redirect → /register/ (wizard step: resumo/finalizar)
                ↓
[Step 8: Resumo e finalização] ← NOVO STEP
Mostra: plano pago (nome, valor) + materiais pagos (itens, total)
Botão: "Finalizar cadastro"
                ↓
POST → FinalizeRegistrationView
→ person.is_active = True
→ limpa sessão de pré-registro
→ redirect → dashboard
```

---

## Escopo

### Backend

1. **`create_portal_registration()`** (`system/services/registration.py`)
   - Criar Person com `is_active=False`
   - Criar PortalAccount (necessário para login pós-pagamento)
   - Criar ClassEnrollments normalmente (person inativo não aparece em queries sem filtro explícito)
   - Criar apenas RegistrationOrder do plano (sem produtos na primeira ordem)

2. **`PortalRegisterView.form_valid()`** (`system/views/auth_views.py`)
   - Remover produtos do order inicial (apenas plano)
   - Armazenar `person.pk` na sessão como `pending_registration_person_id`
   - Manter redirect para Stripe/PIX/deferred conforme checkout_action

3. **`_validate_single_cpf()`** (`system/forms/registration_forms.py`)
   - Se Person com CPF existe e `is_active=False`: permitir substituição (overwrite do registro inativo)
   - Se Person com CPF existe e `is_active=True`: bloquear com "CPF já cadastrado"

4. **`PaymentSuccessView`** (`system/views/payment_views.py`)
   - Detectar se é pagamento de plano ou de materiais pelo tipo do RegistrationOrder
   - Plano pago: setar sessão `post_plan_payment_complete=True`, `plan_order_id`, redirect → `/register/` (passo materiais)
   - Materiais pagos: setar sessão `post_materials_payment_complete=True`, redirect → `/register/` (passo resumo)

5. **`MaterialsCheckoutView`** — NOVA VIEW (`system/views/auth_views.py` ou novo arquivo)
   - POST com carrinho de materiais (JSON payload)
   - Recupera Person via `pending_registration_person_id` na sessão
   - Cria `RegistrationOrder` (kind=ONE_TIME) com os produtos
   - Redireciona para Stripe ou PIX

6. **`FinalizeRegistrationView`** — NOVA VIEW
   - POST (com CSRF)
   - Recupera Person via `pending_registration_person_id` na sessão
   - Valida que plano foi pago (plan_order_id com payment_status=PAID ou EXEMPTED)
   - `person.is_active = True` + `person.save()`
   - Limpa chaves de pré-registro da sessão
   - Auto-login (já está logado via PaymentSuccessView)
   - Redirect → dashboard

7. **`DeferPaymentView`** (`system/views/payment_views.py`)
   - Após defer: NÃO redirecionar para login
   - Setar `post_plan_payment_complete=True` (plano "pago" via trial/deferred)
   - Redirect → `/register/` (passo materiais) ou direto para finalização

8. **`PaymentCancelView`** (`system/views/payment_views.py`)
   - Redirect para `/register/` (reexibir step de pagamento do plano), NÃO para login

### URLs novas

```python
# system/urls.py
path("register/materials-checkout/", MaterialsCheckoutView.as_view(), name="materials-checkout"),
path("register/finalize/", FinalizeRegistrationView.as_view(), name="finalize-registration"),
```

### Frontend — Wizard JS (`static/system/js/auth/registration-wizard-clean.js`)

1. **Step 6 (Plano)**: botão de ação muda para "Pagar plano" (não mais "Avançar") — aciona submit do form completo

2. **Step 7 (Materiais) — NOVO no pós-pagamento**:
   - Badge "✓ Plano pago" (badge verde já implementado)
   - Catálogo de produtos com select-based UI (já implementado)
   - Botão "Pagar materiais" → POST para `/register/materials-checkout/` (form com `action` apontando para a nova URL)
   - Botão "Continuar sem materiais" → vai direto para step resumo

3. **Step 8 (Resumo/Finalizar) — NOVO**:
   - Lê `plan_order_data` e `materials_order_data` da sessão (injetados via JSON no template)
   - Exibe: plano selecionado + valor; itens de materiais + total
   - Botão "Finalizar cadastro" → POST para `/register/finalize/`

### CSS (`static/system/css/auth/login.css`)

- Estilos do step de resumo (já tem padrão visual)
- Step de materiais já tem estilos (catalog-product-*)

### Template (`templates/login/register.html`)

- Injetar JSON de contexto pós-pagamento: `plan_order_json` e `materials_order_json`
- Injetar URLs das novas views como dados JSON (não hardcodar no JS)

---

## Fora do escopo

- Mudança no modelo de Membership / assinatura Stripe
- Alteração no painel administrativo de pedidos
- Relatórios financeiros
- Reenvio de e-mail de boas-vindas (pode ser adicionado depois)
- Cancelamento / estorno de materiais (fluxo de pós-compra)

---

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `system/services/registration.py` | Criar Person com is_active=False |
| `system/forms/registration_forms.py` | Permitir overwrite de Person inativo no CPF check |
| `system/views/auth_views.py` | form_valid revisado + novas views (Materials, Finalize) |
| `system/views/payment_views.py` | PaymentSuccessView, DeferPaymentView, PaymentCancelView |
| `system/urls.py` | Novas rotas |
| `system/services/registration_checkout.py` | create_registration_order → só plano; create_product_only_order já existe |
| `templates/login/register.html` | Novos JSON contexts, versão do asset atualizada |
| `static/system/js/auth/registration-wizard-clean.js` | Steps 7 e 8, lógica pós-pagamento revisada |
| `static/system/css/auth/login.css` | Estilos do step resumo |

---

## Riscos e edge cases

| Risco | Mitigação |
|---|---|
| Pessoa inativa com CPF "tomado" se usuário abandonar | _validate_single_cpf permite overwrite de Person com is_active=False |
| Usuário paga plano mas fecha o browser antes dos materiais | Sessão persiste; ao retornar para /register/, wizard retoma do step correto via flags de sessão |
| Materiais com estoque insuficiente entre seleção e pagamento | apply_order_variant_stock (já existe) aplica deduction atômica no webhook de sucesso |
| Webhook de pagamento chega antes do redirect | Order já existe com payment_status=PENDING; webhook atualiza para PAID; redirect apenas seta flag de sessão |
| Usuário autenticado acessando /register/ sem sessão de pré-registro | Se person.is_active=True e sessão sem pending_registration: redirecionar para dashboard |
| Double-submit de finalização | FinalizeRegistrationView idempotente: se person.is_active já True, apenas redireciona para dashboard |
| Plano pago via "pagar depois" (trial) | DeferPaymentView seta plan_paid=True na sessão, permite avançar para materiais |

---

## Regras e restrições

- SDD antes de código
- TDD para implementação
- Sem hardcode
- Sem mascaramento de erro
- **Sem novas migrações** — Person.is_active já existe e é suficiente
- Leitura integral obrigatória antes de qualquer edição
- Validação em navegador obrigatória

---

## Plano

- [ ] 1. Contexto e leitura integral (concluído)
- [ ] 2. Testes Red: criar testes para o novo fluxo em `system/tests/test_views.py` e `test_services.py`
- [ ] 3. `_validate_single_cpf`: permitir overwrite de Person inativo
- [ ] 4. `create_portal_registration()`: Person com is_active=False
- [ ] 5. `create_registration_order()`: separar produtos (order de materiais vira exclusividade de create_product_only_order)
- [ ] 6. `PortalRegisterView.form_valid()`: armazenar person_id na sessão; redirect correto
- [ ] 7. `PaymentSuccessView`: diferenciar plano vs materiais; setar sessão correta
- [ ] 8. `DeferPaymentView` + `PaymentCancelView`: corrigir redirects
- [ ] 9. `MaterialsCheckoutView`: nova view
- [ ] 10. `FinalizeRegistrationView`: nova view
- [ ] 11. URLs novas
- [ ] 12. Wizard JS: steps 7 e 8, lógica pós-pagamento
- [ ] 13. Template: novos JSON contexts + versão de asset
- [ ] 14. CSS: estilos do step resumo
- [ ] 15. Testes Green: todos passando
- [ ] 16. Validação `manage.py test --verbosity 2`
- [ ] 17. Validação visual em navegador
- [ ] 18. Limpeza de artefatos temporários (`_patch_buildProductCard.py`)
- [ ] 19. Atualização documental

---

## Critérios de aceite

- [ ] Ao submeter o wizard até o plano, Person é criado com is_active=False — verificável via shell: `Person.objects.filter(cpf=X).first().is_active == False`
- [ ] CPF de uma Person inativa pode ser reutilizado no wizard sem erro "CPF já cadastrado" — verificável por teste
- [ ] Após plano pago (Stripe/PIX), redirect vai para wizard no passo de materiais, NÃO para login
- [ ] "Pagar materiais" cria um novo RegistrationOrder separado do order do plano — verificável via ORM
- [ ] "Finalizar cadastro" seta person.is_active=True — verificável via shell
- [ ] Após finalização, redirect vai para dashboard (nunca para login)
- [ ] "Pagar depois" (trial) segue mesmo fluxo: vai para materiais, não para login
- [ ] Cancelar pagamento retorna para o step de plano no wizard, não para login
- [ ] Console do navegador sem erros JS críticos
- [ ] Terminal sem stack trace

---

## Evidências esperadas

- `manage.py test --verbosity 2` — 0 falhas, 0 erros
- `manage.py check` — sem issues
- Screenshot: wizard step plano → submit → Person inativo criado
- Screenshot: wizard step materiais → pagar → materials order criado
- Screenshot: step resumo → finalizar → Person ativo + dashboard

---

## Correção 2026-05-11 — Pagamento do plano confundido com materiais

**Causa:** `create_checkout_session_for_order` persistia `order.kind = OrderKind.ONE_TIME` para todo checkout Stripe. `PaymentSuccessView` tratava `ONE_TIME` como pedido só de materiais, setando `post_materials_payment_complete` e pulando a etapa de materiais no wizard.

**Correção:** Em `PaymentSuccessView`, classificar por `order.plan_id is None` (pedido só de produtos) vs presença de plano no pedido, em vez de confiar apenas em `order.kind`.

**UX:** Wizard pós-plano passou a incluir etapa explícita **Resumo** entre materiais e finalizar (`registration-wizard-clean.js` + `register.html`).

**UX (indicadores pré-pagamento):** Para fluxos com etapa de plano, o progresso passa a listar **Materiais**, **Resumo** e **Finalizar** desde o início, em estado bloqueado (`phaseLocked`) até o pagamento do plano, alinhando a expectativa do usuário ao caminho completo.

---

## Implementado

_A preencher após implementação_

## Desvios do plano

_A preencher se necessário_

## Pendências

_A preencher após validação_
