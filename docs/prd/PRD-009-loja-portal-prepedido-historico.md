# PRD-009: Loja no portal autenticado com pré-pedido, fila por chegada e histórico do aluno

## Resumo do que será implementado

Levar a loja autenticada (`/store/`) para um lugar acessível no portal de qualquer perfil autenticado (aluno/professor/admin) via link discreto no menu lateral, e adicionar três capacidades novas:

1. **Pré-pedido** quando o aluno clica em variante sem estoque — registra interesse sem cobrança imediata.
2. **Fila por ordem de chegada** quando o produto repõe estoque — sistema aloca automaticamente as reservas.
3. **Notificação por badge no portal** quando há produto disponível para confirmação, e tela do aluno para **confirmar** (gera pedido + checkout PIX/Cartão à vista) ou **desistir**.
4. **Histórico** próprio do aluno.
5. **Tela administrativa** para gerenciar a fila por variante e marcar reposição.

Pagamento avulso segue o mesmo princípio da mensalidade: PIX à vista pelo Asaas, Cartão à vista (1x) pelo Stripe.

## Tipo de demanda

Feature nova com schema novo, lógica de negócio (alocação de fila, expiração), nova UI (3 telas + badge + 1 botão na loja) e integração com checkout existente.

## Problema atual

1. Aluno abre `/store/`, encontra um kimono esgotado em sua numeração e fica sem caminho — só pode tentar entrar em contato pelo WhatsApp.
2. Não há trilha do que o aluno comprou (`RegistrationOrder` existe mas o aluno não tem tela de leitura própria).
3. Admin não tem visibilidade da demanda reprimida (quantos alunos querem qual produto/variante).
4. Loja `/store/` está acessível, mas alunos comuns não têm sequer o link no menu.

## Objetivo

- Loja acessível no menu para qualquer perfil autenticado.
- Cobrir o caso "produto sem estoque" com lista de espera transparente.
- Dar autonomia ao aluno para confirmar/cancelar e acompanhar histórico.
- Dar ao admin uma fila acionável (saber quem espera o quê e por quanto tempo).

## Context Ledger

### Arquivos lidos integralmente

- [system/models/product.py](system/models/product.py) — `Product`, `ProductVariant`, `ProductCategory`
- [system/models/registration_order.py](system/models/registration_order.py) — fluxo de `RegistrationOrder`/`RegistrationOrderItem`
- [system/views/product_views.py](system/views/product_views.py) — `ProductStoreView`, `CreateProductOrderView`
- [system/services/registration_checkout.py](system/services/registration_checkout.py) — `create_product_only_order`, `apply_order_variant_stock`
- [templates/products/product_store.html](templates/products/product_store.html)
- [templates/base.html](templates/base.html) — drawer/menu lateral
- [system/views/payment_views.py](system/views/payment_views.py) — `PaymentMethodChoiceView`, `CreateCheckoutSessionView`, `CreatePixChargeView`
- [system/services/financial_transactions.py](system/services/financial_transactions.py) — `apply_order_financials`, `resolve_payment_provider_for_plan`

### Arquivos adjacentes consultados

- [system/admin.py](system/admin.py) — admin atual de Product/ProductVariant
- [system/services/membership.py](system/services/membership.py) — referência de fluxo de assinatura (proration)
- [system/forms/product_forms.py](system/forms/product_forms.py)

### Internet / documentação oficial

- N/A para esta entrega (sem libs novas).

### MCPs / ferramentas verificadas

- `Glob`, `Read`, `Grep`, `Edit`, `Write`, `Bash` — funcionando.

### Limitações encontradas

- Cobrança parcelada no cartão (Stripe) precisaria de conta com contrato customizado para parcelar com X% diferente. Por isso a entrega trata cartão avulso como **1x à vista** — alinhado com a tarifa pública padrão (3,99% + R$ 0,39).
- Notificação por e-mail ficou **fora do escopo** (decisão item 4 da revisão). Apenas badge no portal.
- Decisão item 6 ainda exige confirmação do usuário sobre parcelamento de cartão (default proposto: 1x).

## Prompt de execução

### Persona

Agente Django sênior em modo control-first com SDD + TDD.

### Ação

Criar o domínio de pré-pedido (`ProductBackorder`), atualizar a loja existente (`/store/`) com botão "Avise-me quando chegar" para variantes esgotadas, criar telas de gerenciamento (aluno e admin), badge de notificação no menu, histórico do aluno, e management command para expirar reservas.

### Contexto

A loja já existe em `/store/` (`ProductStoreView`) e gera `RegistrationOrder` via `create_product_only_order`. O checkout (PIX/Cartão) já está pronto. O que falta é o tijolo do pré-pedido + fila + telas.

### Restrições

- sem hardcode
- sem mascaramento de erro
- proibido criar arquivo de migração à mão (vai pelo ciclo destrutivo `clear_migrations.py` → `makemigrations`)
- leitura integral obrigatória (concluída acima)
- testes obrigatórios (modelo, service, view, command)
- estoque consumido apenas no momento do pagamento, **não** na criação do pré-pedido
- reservas expiram em **7 dias** após notificação para liberar estoque ao próximo da fila
- aluno só pode ter 1 backorder ativo por (`person`, `variant`)
- pagamento avulso: PIX à vista, Cartão **1x à vista** (default — confirmar com usuário)
- notificação apenas por badge (sem e-mail)

### Critérios de aceite

- [ ] Modelo `ProductBackorder` criado com choices de status `PENDING`, `READY`, `CONFIRMED`, `CANCELED`, `EXPIRED` (verificável: leitura do modelo + teste)
- [ ] Tela `/store/` mostra botão "Avise-me quando chegar" para variantes com `stock_quantity == 0` e `is_active=True` (verificável: teste de view + visual)
- [ ] POST em `/store/backorders/create/` cria backorder com status `PENDING` (verificável: teste)
- [ ] Não permite criar backorder duplicado para a mesma (person, variant) com status ativo (verificável: teste)
- [ ] Quando `restock_variant(variant, quantity)` é chamado, marca `quantity` backorders PENDING como READY em ordem cronológica (verificável: teste)
- [ ] Reserva READY tem `expires_at = notified_at + 7 days` (verificável: teste)
- [ ] Aluno autenticado vê badge no drawer com contagem de pré-pedidos READY (verificável: teste de template)
- [ ] Tela `/store/pedidos/` lista pré-pedidos do aluno com botão Confirmar/Cancelar nos READY (verificável: teste de view)
- [ ] Confirmar pré-pedido READY gera `RegistrationOrder` + redireciona para `payment-checkout` (verificável: teste)
- [ ] Pagamento confirmado marca backorder como `CONFIRMED` e decrementa `stock_quantity` (via `apply_order_variant_stock`) (verificável: teste integrado)
- [ ] Cancelar pré-pedido READY libera estoque e tenta promover próximo da fila (verificável: teste)
- [ ] Tela `/store/historico/` lista todos `RegistrationOrder` pagos do aluno (verificável: teste)
- [ ] Tela `/billing/backorders/` (admin/professor) lista fila por variante com idade (verificável: teste)
- [ ] Comando `manage.py expire_backorders` marca READY com `expires_at < now` como EXPIRED, promovendo a fila (verificável: teste do comando)
- [ ] Drawer mostra link "Loja" para qualquer perfil autenticado (verificável: teste do template)
- [ ] Drawer mostra link "Meus pedidos" para aluno (verificável: teste do template)
- [ ] Drawer mostra link "Pré-pedidos" para administrativo/admin (verificável: teste do template)
- [ ] `manage.py test --verbosity 2` passa com 0 falhas
- [ ] `manage.py check` passa sem warnings novos

### Evidências esperadas

- testes passando
- sequência manual no navegador: criar pré-pedido como aluno A; admin repõe estoque; aluno A vê badge; aluno A confirma; checkout abre; pagamento simulado; ordem aparece no histórico.
- shell check: `ProductBackorder.objects.filter(status="ready", expires_at__lt=now())` deve estar vazio após `expire_backorders`.

### Formato de saída

Código + testes + relatório.

## Escopo

### Modelos
1. `ProductBackorderStatus` (TextChoices): `PENDING`, `READY`, `CONFIRMED`, `CANCELED`, `EXPIRED`.
2. `ProductBackorder(TimeStampedModel)`:
   - `person` (FK Person, `related_name="product_backorders"`)
   - `variant` (FK ProductVariant, `related_name="backorders"`)
   - `status` (default PENDING)
   - `notified_at` (null)
   - `confirmed_at` (null)
   - `canceled_at` (null)
   - `expires_at` (null)
   - `confirmed_order` (FK RegistrationOrder, null, on_delete=SET_NULL)
   - `notes` (TextField blank)
   - **constraint**: `UniqueConstraint(person, variant)` filtrado em status ativo (PENDING ou READY) — implementação via `condition=Q(status__in=...)`.
   - **ordering**: `("created_at",)`

### Selectors / Services
3. `system/selectors/product_backorders.py`:
   - `get_active_backorder(person, variant)`
   - `get_ready_backorders_for_person(person)`
   - `get_backorder_queue_for_variant(variant)` (PENDING + READY ordenados por created_at)
   - `count_ready_for_person(person)` — para o badge
4. `system/services/product_backorders.py`:
   - `create_backorder(person, variant)` — valida duplicidade
   - `restock_variant(variant, quantity_added)` — promove fila
   - `confirm_backorder(backorder)` — gera RegistrationOrder com 1 item, retorna order
   - `cancel_backorder(backorder)` — marca CANCELED, dispara `restock_variant(variant, 1)` se era READY
   - `expire_pending_reservations()` — para o cron

### Views (HTTP)
5. `ProductBackorderCreateView` — POST `/store/backorders/create/` (autenticado, perfil aluno/admin/professor)
6. `StudentBackorderListView` — GET `/store/pedidos/`
7. `StudentBackorderConfirmView` — POST `/store/pedidos/<int:pk>/confirmar/`
8. `StudentBackorderCancelView` — POST `/store/pedidos/<int:pk>/cancelar/`
9. `StudentOrderHistoryView` — GET `/store/historico/`
10. `AdminBackorderQueueView` — GET `/billing/backorders/` (administrativo + admin)

### Templates
11. `templates/products/product_store.html` — botão "Avise-me quando chegar" inline na variante esgotada.
12. `templates/products/student_backorder_list.html` — lista do aluno com READY no topo.
13. `templates/products/student_order_history.html` — histórico do aluno.
14. `templates/billing/admin_backorder_queue.html` — fila administrativa.
15. `templates/base.html` — adicionar links "Loja", "Meus pedidos" e "Pré-pedidos" no drawer + badge.

### Context processor
16. `system/context_processors.py` (novo) ou middleware: expor `pending_backorder_count` no template a partir de `request.portal_person`. Registrar em `settings.TEMPLATES`.

### Management command
17. `system/management/commands/expire_backorders.py` — chama `expire_pending_reservations()`.

### Sinais / hook
18. Em `system/signals.py` (ou novo): `post_save` em `ProductVariant` que detecta aumento de `stock_quantity` e chama `restock_variant`. Implementação atômica usando `pre_save` + `post_save` para detectar delta. Evitar loop com flag em `_meta`.

### Testes
19. `system/tests/test_product_backorders.py` (novo): modelo, services, comando.
20. `system/tests/test_product_views.py` (atualizar): novas views (criar, listar, confirmar, cancelar, histórico, fila admin).
21. `system/tests/test_signals.py` (atualizar ou criar): signal de restock.

### Cache-busting + estilo
22. Bumpar `?v=` em `product-store.js` (porque o botão novo + UX em cards esgotados pode pedir JS extra).
23. Adicionar CSS para badge no drawer (`.drawer-badge`), botão "Avise-me", e cards de pré-pedido.

## Fora do escopo

- Notificação por e-mail.
- Limite de quantos backorders um aluno pode ter ao mesmo tempo (sem limite — apenas regra de não duplicar mesma variante).
- Reembolso pós-confirmação (passa a ser RegistrationOrder normal).
- Estatísticas de demanda reprimida (relatório admin).
- Parcelamento de cartão > 1x — pendente de decisão final.

## Arquivos impactados

- `system/models/product.py` (alterar) ou novo `system/models/product_backorder.py`
- `system/models/__init__.py`
- `system/migrations/0001_initial.py` (regenerada via ciclo destrutivo)
- `system/admin.py` (registrar `ProductBackorder`)
- `system/selectors/__init__.py`
- `system/selectors/product_backorders.py` (novo)
- `system/services/product_backorders.py` (novo)
- `system/views/product_views.py`
- `system/views/billing_admin_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/signals.py`
- `system/context_processors.py` (novo)
- `lvjiujitsu/settings.py` (registrar context processor)
- `system/management/commands/expire_backorders.py` (novo)
- Templates: `product_store.html`, `student_backorder_list.html` (novo), `student_order_history.html` (novo), `admin_backorder_queue.html` (novo), `base.html`
- CSS: `static/system/css/portal/portal.css` (badge), e/ou novo `static/system/css/portal/store.css`
- JS: `static/system/js/products/product-store.js` (atualizar)
- Testes: `test_product_backorders.py` (novo), `test_product_views.py`, `test_signals.py` ou similar

## Riscos e edge cases

- **Race condition na alocação**: dois admins reabastecendo ao mesmo tempo. Mitigação: `select_for_update` no `restock_variant` envolto em `transaction.atomic`.
- **Aluno confirma e o pagamento falha**: a `RegistrationOrder` permanece pendente; backorder permanece READY até pagamento ou expiração. Após expiração, libera fila. Nenhum estoque foi tocado.
- **Aluno cancela um READY**: precisa reverter para próximo da fila → `restock_variant(variant, 1)`.
- **Variante desativada**: backorders pendentes/ready dessa variante devem ser marcados como CANCELED automaticamente. Implementar no signal `pre_save` quando `is_active` muda para False.
- **Person inativo**: backorder fica órfão. Aceitável (admin pode limpar).
- **Histórico do aluno respeita o owner financeiro**: usar `get_membership_owner` para responsável-aluno.
- **Drawer link "Loja"**: deve aparecer também para administrativo/admin (eles também podem comprar) — tratar como link comum, não condicionado a tipo.

## Regras e restrições

- SDD antes de código (PRD aqui)
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- proibido criar arquivo de migração à mão (ciclo destrutivo)
- leitura integral obrigatória (concluída)
- validação obrigatória

## Plano

- [x] 1. Contexto e leitura integral
- [ ] 2. Confirmar com usuário: parcelamento de cartão (1x default proposto)
- [ ] 3. Modelo `ProductBackorder` + status + constraints + export
- [ ] 4. Selector `product_backorders`
- [ ] 5. Service `product_backorders` (criar, restock, confirm, cancel, expire)
- [ ] 6. Signal: `post_save` em `ProductVariant` detectando aumento de estoque
- [ ] 7. Signal: desativar variant cancela backorders ativos
- [ ] 8. Context processor `pending_backorder_count`
- [ ] 9. Views (Create, List, Confirm, Cancel, History, Admin Queue)
- [ ] 10. URLs novas
- [ ] 11. Templates novos + drawer + product_store botão "Avise-me"
- [ ] 12. CSS badge + botão
- [ ] 13. Management command `expire_backorders`
- [ ] 14. Testes (modelo + service + view + command + signal)
- [ ] 15. Atualizar `test_product_views.py`
- [ ] 16. Bumpar cache CSS/JS
- [ ] 17. Pedir autorização e rodar ciclo destrutivo (`clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds)
- [ ] 18. `manage.py check` final + `collectstatic`
- [ ] 19. Validação visual em navegador
- [ ] 20. Limpeza final
- [ ] 21. Atualização documental

## Validação visual

### Desktop
- Drawer com novos links ("Loja", "Meus pedidos" para aluno; "Pré-pedidos" para admin)
- Loja `/store/` com botão "Avise-me quando chegar" em variantes esgotadas
- `/store/pedidos/` com READY no topo + botões Confirmar/Cancelar
- `/store/historico/` listando RegistrationOrders pagos
- `/billing/backorders/` para admin com fila por variante
- Badge no drawer com contagem visível

### Mobile
- Drawer responsivo, badge visível em ≤480px

### Console
- Sem 404 de assets (cache-busting bumpado)
- Sem erro JS

## Validação ORM

### Banco
- Tabela `system_productbackorder` criada após `migrate`.
- `system_productvariant.stock_quantity` sem alteração.

### Shell checks
```python
from system.models import ProductBackorder, ProductBackorderStatus
ProductBackorder.objects.filter(status=ProductBackorderStatus.PENDING).count()
ProductBackorder.objects.filter(status=ProductBackorderStatus.READY, expires_at__lt=timezone.now()).count()  # 0 após expire_backorders
```

### Integridade do fluxo
- 1 backorder por (person, variant) com status ativo.
- READY sempre tem `expires_at` preenchido.
- CONFIRMED sempre tem `confirmed_order` preenchido.

## Validação de qualidade

### Sem hardcode
- `BACKORDER_RESERVATION_DAYS = 7` em `settings.py` (não no código).

### Sem estruturas condicionais quebradiças
- Service usa guard clauses + `transaction.atomic`.

### Sem `except: pass`
- Nada introduzido.

### Sem mascaramento de erro
- Nada.

### Sem comentários e docstrings desnecessários
- Nada.

## Evidências

(a preencher após implementação)

## Implementado

(a preencher após implementação)

## Desvios do plano

(a preencher após implementação)

## Pendências

- Confirmação do parcelamento de cartão avulso (default 1x).
- PRD futuro: notificação por e-mail e relatório de demanda reprimida.
