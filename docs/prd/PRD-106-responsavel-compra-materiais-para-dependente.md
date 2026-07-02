# PRD-106: Responsável não consegue comprar/ver materiais em nome do dependente

## Summary
A PRD-101 documentou explicitamente ("Responsável comprando para dependente precisa do seletor de pessoa") e a evidência de validação citou o seletor "Comprar para" com 7 pessoas — mas esse teste foi feito como admin técnico. Para um responsável comum (não staff), `get_material_request_recipient_queryset()` só retorna a própria pessoa, nunca os dependentes. Além disso, mesmo que o responsável conseguisse comprar em nome do dependente, o pré-pedido e o histórico de compras ficam invisíveis para ele depois, pois as listas filtram estritamente por `request.portal_person`.

## Demand type
Correção de bug funcional (feature parcialmente implementada, contradiz o escopo já documentado na PRD-101).

## Current problem
- `system/selectors/person_selectors.py:96-112` (`get_material_request_recipient_queryset`): só amplia a lista de destinatários para `CLASS_STAFF_PERSON_TYPE_CODES` (instrutor/administrativo); para qualquer outro ator (inclusive responsável com dependentes) retorna `queryset.filter(pk=actor.pk)` — só ele mesmo.
- `system/views/product_views.py:264-265` (`StudentBackorderListView.get_queryset`) e `system/views/product_views.py:309-322` (`StudentOrderHistoryView.get_queryset`): ambos filtram só pela pessoa logada (ou seu billing owner, que não ajuda no sentido guardian→dependente), então mesmo que um pré-pedido/pedido seja criado com `person=dependente`, o responsável nunca o vê nas próprias telas.
- Resultado: um responsável não consegue comprar um kimono/faixa para o filho dependente pela loja, e mesmo com um ajuste manual (ex: via admin) o pedido não apareceria no histórico do responsável.

## Goal
Um responsável com dependentes pode selecionar cada dependente em "Comprar para" na loja, criar pedidos/pré-pedidos para eles, e ver esses pedidos/pré-pedidos nas próprias telas de histórico e pré-pedidos.

## Context Ledger
### Files read in full
- `system/selectors/person_selectors.py` (`get_material_request_recipient_queryset`, `resolve_material_request_recipient`)
- `system/views/product_views.py` (`ProductStoreView._build_purchase_person_choices`, `CreateProductOrderView`, `ProductBackorderCreateView`, `StudentBackorderListView`, `StudentOrderHistoryView`)
- `system/selectors/product_backorders.py` (`get_backorders_for_person`)
- `templates/products/product_store.html` (seletor "Comprar para" dentro do mesmo `<form>` do carrinho — confirmado que `purchase_person_id` é enviado corretamente junto com qualquer botão do form, inclusive o de pré-pedido; não há bug de CSRF/campo ausente aqui)
- `docs/prd/PRD-101-loja-publica-prepedidos-historico-aluno.md` (linha 70: escopo original já previa este caso)
- `system/services/membership.py` (`get_membership_owner`, `has_dependents`)

### Adjacent files consulted
- `system/constants.py` (`CLASS_STAFF_PERSON_TYPE_CODES`, `MATERIAL_REQUEST_PERSON_TYPE_CODES`)
- `system/tests/test_product_store.py` (cobertura existente: nenhum teste cobre responsável com dependente)

### Limitations found
- Nenhuma. Duas hipóteses do agente de exploração (CSRF do botão de pré-pedido e `purchase_person_id` não enviado) foram descartadas após leitura: o botão de pré-pedido está dentro do mesmo `<form>` do carrinho, então o token CSRF e o campo `purchase_person_id` do seletor são enviados normalmente com qualquer submit desse formulário.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Achado confirmado por leitura direta do código e comparado ao escopo já registrado na PRD-101.

## Scope
- `get_material_request_recipient_queryset()`: incluir dependentes (via `PersonRelationship` `RESPONSIBLE_FOR`) na lista de destinatários quando o ator for responsável, não só quando for staff.
- `StudentBackorderListView`/`StudentOrderHistoryView`: expandir o filtro para incluir todas as pessoas que o ator pode comprar em nome de (ele mesmo + dependentes), não só a pessoa logada.

## Out of scope
- Mudar a lógica de billing owner (`get_membership_owner`) usada no financeiro.
- Qualquer alteração no fluxo de staff (instrutor/administrativo), que já funciona.

## Impacted files
- `system/selectors/person_selectors.py`
- `system/views/product_views.py`
- `system/tests/test_product_store.py`

## Risks and edge cases
- Responsável sem dependentes: comportamento inalterado (só ele mesmo).
- Dependente que também é responsável de outro dependente (encadeamento): fora de escopo, tratar só um nível como o resto do sistema já faz (`has_dependents`/`_build_dependents` também só olham um nível).

## Rules and constraints
- Reaproveitar `has_dependents`/`PersonRelationship` já usados na PRD-105, sem duplicar lógica.

## Plan
- [x] Ajustar `get_material_request_recipient_queryset`.
- [x] Ajustar `StudentBackorderListView`/`StudentOrderHistoryView`.
- [x] Testes focados.
- [x] Validação visual.

## Test plan
### Tests to author
- Responsável com dependente vê o dependente no seletor "Comprar para".
- Pré-pedido criado para o dependente aparece na lista de pré-pedidos do responsável.
- Pedido pago criado para o dependente aparece no histórico do responsável.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_product_store.py` (`GuardianBuysForDependentTestCase`, 3 testes novos): responsável vê o dependente no seletor "Comprar para"; pré-pedido criado para o dependente aparece na lista de pré-pedidos do responsável; pedido pago do dependente aparece no histórico do responsável.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_store --verbosity 2` — 8 testes OK (5 existentes + 3 novos).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 351 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Validação ao vivo no navegador (responsável demo + Aline como dependente, criados via ORM e removidos após o teste; servidor reiniciado por rodar com `--noreload`): seletor "Comprar para" em `/store/` mostra "Responsavel Demo PRD106" e "Aline Blanch Freiria" corretamente.

## Visual validation
Loja e telas de pré-pedido/histórico com responsável logado e dependente real.

## ORM validation
`ProductBackorder`/`RegistrationOrder` com `person` = dependente.

## Quality validation
- `manage.py test system.tests.test_product_store` e suíte completa.
- `manage.py check`.

## Evidence
- `StudentOrderHistoryView` usava `get_membership_owner()` (conceito de dono financeiro de mensalidade) para decidir de quem mostrar pedidos — um uso indevido desse helper, já que `RegistrationOrder.person` é sempre a pessoa real do pedido (`create_product_only_order`), não o pagador de mensalidade. Trocado por `person__in=recipients`, consistente com o pré-pedido.
- Duas hipóteses do agente de exploração (bug de CSRF e `purchase_person_id` ausente no botão de pré-pedido) foram descartadas: ambas falsas, o botão está dentro do mesmo `<form>` do carrinho e envia todos os campos normalmente.

## Implemented
- `system/selectors/person_selectors.py`: `get_material_request_recipient_queryset()` agora inclui dependentes (via `PersonRelationship` `RESPONSIBLE_FOR`) para qualquer responsável, não só para staff.
- `system/selectors/product_backorders.py`: `get_backorders_for_person()` passou a aceitar um conjunto de pessoas (`person__in`) em vez de uma única pessoa.
- `system/views/product_views.py`: `StudentBackorderListView` e `StudentOrderHistoryView` agora filtram por todas as pessoas que o ator pode comprar em nome de (via `get_material_request_recipient_queryset`); removido o import órfão `get_membership_owner`.
- `system/tests/test_product_store.py`: nova classe `GuardianBuysForDependentTestCase` (3 testes).

## Cleanup findings
- Nenhum resíduo; dados demo (responsável + relação) removidos do banco local após a validação visual.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
_Nenhum até o momento._

## Pending
_Nenhuma até o momento._

## Final status
Concluída.
