# PRD-102: CRUD de categoria de material

## Summary
`ProductCategory` existe só como catálogo escolhido via FK no formulário de Product; não há tela própria de gestão (criar, listar, editar, excluir categoria), gap já documentado como pendência na PRD-077.

## Demand type
Nova feature de CRUD (módulo de domínio já existente sem UI).

## Current problem
- `ProductCategory` não tem form, view nem rota própria.
- Gestor não consegue criar/renomear/inativar categoria de material sem Django Admin.

## Goal
CRUD curto em modal para `ProductCategory`, no mesmo padrão das PRDs 075/077/078 (rotas em inglês, modal para criar/editar, diálogo de confirmação para excluir).

## Context Ledger
### Files read in full
- `system/models/product.py` (`ProductCategory`)
- `system/views/product_views.py`
- `system/forms/product_forms.py`

### Adjacent files consulted
- `templates/class_categories/*` (padrão de CRUD simples já validado nas PRDs 075/077)

### Internet / official documentation
Não aplicável (reaproveita fundação já validada).

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"), gap já documentado na PRD-077/098.

## Scope
- `ProductCategoryForm`.
- `ProductCategoryListView`/`CreateView`/`UpdateView`/`DeleteView`/`DetailView`.
- Templates seguindo o padrão `class_categories/*`.
- Rotas em inglês `/materials/categories/...`.
- Teste focado.

## Out of scope
- Alterar `Product`/`ProductForm`.

## Impacted files
- `system/forms/product_forms.py`
- `system/views/product_views.py`
- `system/urls.py`
- `templates/product_categories/*` (novo)
- `system/tests/`

## Risks and edge cases
- Excluir categoria com produtos vinculados deve bloquear (FK `on_delete=PROTECT` já existe no `Product.category`).

## Rules and constraints
- Rotas em inglês, UI pt-BR, modal para criar/editar, diálogo para excluir.

## Plan
- [x] Form.
- [x] Views.
- [x] Templates.
- [x] Rotas.
- [x] Testes.
- [x] Validação visual.

## Test plan
### Tests to author
- Rota inglesa renderiza; modal de criar funciona; excluir categoria com produto vinculado é bloqueado.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_product_category_crud.py` (4 testes): rota inglesa `/materials/categories/` renderiza; modal de criar funciona (POST válido renderiza `lv/modal_done.html`); excluir categoria com produto vinculado é bloqueado (mensagem de erro + redirect, categoria preservada); excluir categoria sem produto vinculado funciona.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_category_crud --verbosity 2` — 4 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 342 testes OK (suíte completa).
- Validação ao vivo no navegador: `/materials/categories/` renderiza as 4 categorias reais (Faixas, Kimonos, Rash Guard, Patches) com contagem real de produtos; mobile sem overflow horizontal.

## Visual validation
Executada no navegador interno: desktop com dado real, mobile sem overflow.

## ORM validation
`ProductCategory` verificado via teste focado (criação e bloqueio de exclusão).

## Quality validation
- `manage.py test system.tests.test_product_category_crud` — OK.
- `manage.py test system` — 342 testes OK.
- `manage.py check` — 0 problemas.

## Evidence
- `Product.category` já usava `on_delete=PROTECT`; o bloqueio de exclusão com produto vinculado funcionou de primeira, sem necessidade de validação extra no form.

## Implemented
- `system/forms/product_forms.py`: `ProductCategoryForm`.
- `system/views/product_views.py`: `ProductCategoryListView`/`CreateView`/`UpdateView`/`DeleteView`/`DetailView`, no mesmo padrão modal das PRDs 075/077.
- `templates/product_categories/*`: list/form/detail/confirm_delete.
- `system/urls.py`: rotas `/materials/categories/...` em inglês.
- `templates/products/product_list.html`: link "Categorias" adicionado ao cabeçalho.

## Cleanup findings
- Nenhum resíduo.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
- Nenhum desvio funcional.

## Pending
- Nenhuma.

## Final status
Concluída.
