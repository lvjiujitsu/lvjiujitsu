# PRD-102: Material category CRUD

## Summary
`ProductCategory` exists only as a catalog chosen through an FK in the Product form; there is no dedicated management screen (create, list, edit, delete a category), a gap already documented as a pending item in PRD-077.

## Demand type
A new CRUD feature (an existing domain module with no UI).

## Current problem
- `ProductCategory` has no form, view, or route of its own.
- The manager cannot create/rename/deactivate a material category without the Django Admin.

## Goal
Short CRUD in a modal for `ProductCategory`, in the same pattern as PRDs 075/077/078 (English routes, a modal for create/edit, a confirmation dialog for delete).

## Context Ledger
### Files read in full
- `system/models/product.py` (`ProductCategory`)
- `system/views/product_views.py`
- `system/forms/product_forms.py`

### Adjacent files consulted
- `templates/class_categories/*` (the simple CRUD pattern already validated in PRDs 075/077)

### Internet / official documentation
Not applicable (it reuses the already validated foundation).

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"), a gap already documented in PRD-077/098.

## Scope
- `ProductCategoryForm`.
- `ProductCategoryListView`/`CreateView`/`UpdateView`/`DeleteView`/`DetailView`.
- Templates following the `class_categories/*` pattern.
- The English routes `/materials/categories/...`.
- A focused test.

## Out of scope
- Changing `Product`/`ProductForm`.

## Impacted files
- `system/forms/product_forms.py`
- `system/views/product_views.py`
- `system/urls.py`
- `templates/product_categories/*` (new)
- `system/tests/`

## Risks and edge cases
- Deleting a category with linked products must be blocked (the `on_delete=PROTECT` FK already exists on `Product.category`).

## Rules and constraints
- English routes, a Brazilian Portuguese UI, a modal for create/edit, and a dialog for delete.

## Plan
- [x] The form.
- [x] The views.
- [x] The templates.
- [x] The routes.
- [x] The tests.
- [x] Visual validation.

## Test plan
### Tests to author
- The English route renders; the create modal works; deleting a category with a linked product is blocked.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_product_category_crud.py` (4 tests): the English route `/materials/categories/` renders; the create modal works (a valid POST renders `lv/modal_done.html`); deleting a category with a linked product is blocked (an error message + a redirect, with the category preserved); deleting a category with no linked product works.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_category_crud --verbosity 2` — 4 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 342 tests OK (the full suite).
- Live validation in the browser: `/materials/categories/` renders the 4 real categories (Belts, Gis, Rash Guard, Patches) with a real product count; mobile with no horizontal overflow.

## Visual validation
Run in the internal browser: desktop with real data, mobile with no overflow.

## ORM validation
`ProductCategory` verified through the focused test (creation and the deletion block).

## Quality validation
- `manage.py test system.tests.test_product_category_crud` — OK.
- `manage.py test system` — 342 tests OK.
- `manage.py check` — 0 problems.

## Evidence
- `Product.category` already used `on_delete=PROTECT`; blocking a deletion with a linked product worked on the first try, with no need for extra validation in the form.

## Implemented
- `system/forms/product_forms.py`: `ProductCategoryForm`.
- `system/views/product_views.py`: `ProductCategoryListView`/`CreateView`/`UpdateView`/`DeleteView`/`DetailView`, in the same modal pattern as PRDs 075/077.
- `templates/product_categories/*`: list/form/detail/confirm_delete.
- `system/urls.py`: the `/materials/categories/...` routes in English.
- `templates/products/product_list.html`: a `Categorias` (`Categories`) link added to the header.

## Cleanup findings
- No residue.

## Follow-up PRDs
- None.

## Deviations from plan
- No functional deviation.

## Pending
- None.

## Final status
Completed.
