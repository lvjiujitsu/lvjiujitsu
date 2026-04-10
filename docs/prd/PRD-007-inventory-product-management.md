# PRD-007: Controle de Estoque e Produtos (Materiais)

## Resumo

Implementar um módulo CRUD completo de **Produtos** e **Controle de Estoque** dentro da app `system`, permitindo cadastrar materiais da academia (kimonos, rashguards, faixas, patches) com controle de quantidade em estoque, variantes (tamanho, cor) e preço de referência. O módulo será acessível via menu lateral como **"Materiais"** abaixo de "Horários", e visível para perfis administrativos e técnicos. Um seed inicial populará os produtos reais da loja SumUp da LV Jiu Jitsu.

---

## Problema atual

Não existe nenhuma superfície no sistema para gerenciar os produtos vendidos pela academia. O controle é feito manualmente ou via a própria plataforma SumUp, sem integração com o portal de gestão interna.

---

## Objetivo

- Cadastrar produtos com nome, categoria, preço, variantes (tamanho/cor) e quantidade em estoque
- CRUD completo (Listar, Criar, Visualizar, Editar, Excluir)
- Seed inicial com dados reais da loja SumUp (1 unidade de cada para teste)
- Menu "Materiais" integrado ao drawer e dashboards existentes
- Interface responsiva mobile-first (padrão card existente)

---

## Contexto consultado

### Produtos da loja SumUp (lvjiujitsu.sumupstore.com)

**Faixas (R$ 75,00 cada):**
| Cor | SKU sugerido |
|---|---|
| Branca | belt-white |
| Cinza | belt-gray |
| Amarela | belt-yellow |
| Laranja | belt-orange |
| Verde | belt-green |
| Azul | belt-blue |
| Roxa | belt-purple |
| Marrom | belt-brown |
| Preta | belt-black |

**Kimonos:**
| Produto | Preço | SKU sugerido |
|---|---|---|
| Kimono Premium Competition LV | R$ 520,00 | gi-premium-comp |
| Kimono Tradicional Trançado LV Branco | R$ 480,00 | gi-trad-white |
| Kimono Tradicional Trançado LV Branco Feminino | R$ 480,00 | gi-trad-white-fem |
| Kimono Tradicional Trançado LV Preto Feminino | R$ 480,00 | gi-trad-black-fem |
| Kimono Trançado Competition LV Preto c/ Vermelho | R$ 480,00 | gi-comp-black-red |
| Kimono Trançado Competition LV Preto c/ Vermelho Fem. | R$ 480,00 | gi-comp-black-red-fem |
| Kimono Trançado Competition LV Preto c/ Vermelho Infantil | R$ 450,00 | gi-comp-black-red-kids |

**Rash Guard (R$ 150,00 cada):**
| Produto | SKU sugerido |
|---|---|
| Rash Guard LV | rash-lv |

**Patches (R$ 45,00 cada):**
| Produto | SKU sugerido |
|---|---|
| Kit 3 Patch's Kimono | patch-kit-3 |

> **Nota:** Mensalidades (Plano Mensal, Trimestral, etc.) NÃO são materiais — ficam fora deste escopo.

---

## Dependências adicionadas

Nenhuma. Usa apenas Django ORM e patterns já existentes no projeto.

---

## Escopo

### Dentro do escopo
- Model `ProductCategory` (Faixas, Kimonos, Rash Guard, Patches)
- Model `Product` (nome, SKU, categoria, preço, descrição, is_active)
- Model `ProductVariant` (produto, tamanho, cor, estoque, is_active)
- CRUD completo de Product com variantes inline
- Listagem de materiais pública para alunos (somente visualização)
- Seed com todos os produtos da loja SumUp (1 unidade de cada)
- Integração no drawer menu e dashboards
- Testes unitários (models, services, views)

### Fora do escopo
- Venda / carrinho / checkout (fica na SumUp)
- Integração API com SumUp
- Upload de imagens de produto
- Mensalidades e planos financeiros
- Controle de pedidos / histórico de vendas

---

## Arquivos impactados

### Novos
| Arquivo | Responsabilidade |
|---|---|
| `system/models/product.py` | Models: ProductCategory, Product, ProductVariant |
| `system/forms/product_forms.py` | Forms de CRUD |
| `system/views/product_views.py` | Views CRUD (List, Create, Detail, Update, Delete) |
| `system/services/product_management.py` | Service layer para operações de negócio |
| `system/management/commands/seed_products.py` | Seed dos produtos reais |
| `templates/products/product_list.html` | Lista de produtos (cards) |
| `templates/products/product_detail.html` | Detalhe do produto com variantes |
| `templates/products/product_form.html` | Form de criação/edição |
| `templates/products/product_confirm_delete.html` | Confirmação de exclusão |
| `system/tests/test_product_models.py` | Testes de model |
| `system/tests/test_product_views.py` | Testes de views |

### Modificados
| Arquivo | Mudança |
|---|---|
| `system/models/__init__.py` | Exportar novos models |
| `system/admin.py` | Registrar ProductCategory, Product, ProductVariant |
| `system/urls.py` | Rotas `/products/` |
| `system/views/__init__.py` | Exportar novas views |
| `system/forms/__init__.py` | Exportar novos forms |
| `system/services/seeding.py` | Dados de seed dos produtos |
| `system/management/commands/inicial_seed.py` | Incluir `seed_products` |
| `templates/base.html` | Link "Materiais" no drawer menu |
| `templates/home/admin/dashboard.html` | Card "Materiais" no dashboard |
| `templates/home/administrative/dashboard.html` | Card "Materiais" no dashboard |

---

## Riscos e edge cases

1. **SKU duplicado** — constraint unique no campo `sku` do Product
2. **Estoque negativo** — validação no model (PositiveIntegerField)
3. **Produto sem variantes** — permitido (produto simples sem tamanho/cor)
4. **Categoria sem produtos** — estado válido, exibir "Nenhum produto" na listagem
5. **Variante com estoque zero** — exibir como "Esgotado" na interface

---

## Regras e restrições (SDD, TDD, MTV, Design Patterns)

- **MTV:** Lógica de negócio em `services/product_management.py`, não nas views
- **TDD:** Testes primeiro para models e services, depois views
- **Service Pattern:** `@transaction.atomic` em operações com variantes
- **Seed Pattern:** Seguir o padrão de `seed_class_catalog` com `update_or_create`
- **Anti-smell:** Máximo 25 linhas/método, 300 linhas/arquivo
- **Templates:** Herdar `base.html`, usar blocos `extra_css`, `extra_js`
- **Estáticos:** Namespace `system/css/portal/` e `system/js/`

---

## Critérios de aceite (assertions testáveis)

1. `ProductCategory.objects.count() == 4` após seed (Faixas, Kimonos, Rash Guard, Patches)
2. `Product.objects.count() == 10` após seed (todos os itens materiais da loja)
3. `ProductVariant.objects.filter(product__category__code="belts").count() == 9` (uma faixa de cada cor)
4. Navegar para `/products/` retorna status 200 e lista todos os produtos
5. Criar produto via form com variantes persiste no banco
6. Drawer menu exibe "Materiais" abaixo de "Horários" para admin/administrativo
7. Dashboard admin e administrativo exibem card "Materiais"
8. Deletar produto exige confirmação
9. Estoque zero exibe tag "Esgotado"
10. Todos os testes passam com 0 falhas

---

## Plano (ordenado por dependência)

### Fase 1 — Models
1. Criar `system/models/product.py` com:
   - `ProductCategory(TimeStampedModel)` — code, display_name, display_order, is_active
   - `Product(TimeStampedModel)` — sku (unique), display_name, category (FK), unit_price, description, is_active
   - `ProductVariant(TimeStampedModel)` — product (FK), size, color, stock_quantity (PositiveIntegerField), is_active
2. Atualizar `system/models/__init__.py` com exports
3. Registrar no `system/admin.py` com inlines

### Fase 2 — Forms
4. Criar `system/forms/product_forms.py` com:
   - `ProductForm(ModelForm)` — campos do Product
   - `ProductVariantForm(ModelForm)` — campos de variante
   - `get_product_variant_formset()` — inline formset factory (padrão schedule)

### Fase 3 — Services
5. Criar `system/services/product_management.py`:
   - `save_product_with_variants(form, variant_formset)` — `@transaction.atomic`
   - `get_product_list_cards()` — queryset otimizado com aggregations
   - `get_product_card_by_pk(pk)` — detalhe com variantes

### Fase 4 — Views
6. Criar `system/views/product_views.py`:
   - `ProductListView(AdministrativeRequiredMixin, ListView)`
   - `ProductCreateView(AdministrativeRequiredMixin, CreateView)` com variant formset
   - `ProductDetailView(AdministrativeRequiredMixin, DetailView)`
   - `ProductUpdateView(AdministrativeRequiredMixin, UpdateView)` com variant formset
   - `ProductDeleteView(AdministrativeRequiredMixin, DeleteView)`
7. Atualizar `system/views/__init__.py`
8. Atualizar `system/urls.py` com rotas `/products/`

### Fase 5 — Templates
9. Criar templates:
   - `templates/products/product_list.html` — cards responsivos (padrão class_group_list)
   - `templates/products/product_detail.html` — detalhe com tabela de variantes
   - `templates/products/product_form.html` — form com inline formset de variantes
   - `templates/products/product_confirm_delete.html`
10. Atualizar `templates/base.html` — link "Materiais" no drawer
11. Atualizar dashboards (admin + administrativo) com card "Materiais"

### Fase 6 — Seed
12. Adicionar dados em `system/services/seeding.py`:
    - `PRODUCT_CATEGORY_DEFINITIONS` — 4 categorias
    - `PRODUCT_DEFINITIONS` — 10 produtos com variantes
    - `seed_products()` — cria categorias, produtos e variantes
13. Criar `system/management/commands/seed_products.py`
14. Atualizar `system/management/commands/inicial_seed.py`

### Fase 7 — Testes
15. Criar `system/tests/test_product_models.py`
16. Criar `system/tests/test_product_views.py`

### Fase 8 — Reset e validação
17. Executar ciclo de reset destrutivo completo
18. Verificar testes, menu, dashboard, CRUD funcional

---

## Comandos de validação

```powershell
# Reset destrutivo
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# Validações específicas
.\.venv\Scripts\python.exe manage.py test system.tests.test_product_models
.\.venv\Scripts\python.exe manage.py test system.tests.test_product_views
.\.venv\Scripts\python.exe manage.py shell -c "from system.models import Product; print(Product.objects.count())"
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

---

## Implementado

_(a preencher ao final)_

---

## Desvios do plano

_(a preencher ao final)_
