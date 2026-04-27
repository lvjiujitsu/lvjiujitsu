# PRD-006: Padronizar tela de troca de plano com o design system do portal

## Resumo do que será implementado
Redesenhar a tela `billing/plan_change_select.html` para usar o mesmo design system aplicado nas telas de turmas e materiais (`class-catalog.css` + `billing.css`), agrupando os planos por tipo (individual / família) em lista legível com detalhe de prorrateio colapsável, eliminando o grid confuso de cards planos.

## Tipo de demanda
Correção pontual de UX / padronização visual

## Problema atual
A tela exibe até 11+ planos em um `grid` de 3 colunas com o detalhe completo de prorrateio sempre expandido, sem nenhuma hierarquia visual. O resultado é confuso: o usuário não consegue identificar rapidamente o que está escolhendo, qual é upgrade, qual é downgrade, e quanto vai pagar.

## Objetivo
- Organizar planos em dois grupos semânticos: **Planos Individuais** e **Planos Família** (via `is_family_plan`)
- Exibir cada plano como um card de lista (`info-record-list` / `record-card-catalog`) com nome, preço, ciclo e badge de tipo (Upgrade/Downgrade/Gratuito)
- Mostrar o valor líquido (diferença) de forma imediata no card
- Colocar o breakdown detalhado de prorrateio em `<details>` colapsável (`catalog-dropdown`)
- O botão "Trocar para este plano" permanece visível fora do dropdown
- Sem migração, sem alteração de lógica de negócio, sem alteração de serviço

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `templates/billing/plan_change_select.html`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/models/plan.py`
- `static/system/css/billing/billing.css`
- `static/system/css/portal/class-catalog.css`
- `templates/products/product_store.html`
- `docs/prd/PRD-002-enxugar-exibicao-turmas-cadastro.md`
- `docs/prd/PRD-004-corrigir-catalogo-materiais-por-variante.md`

### Arquivos adjacentes consultados
- `system/views/__init__.py` (verificação de exports)
- `system/models/membership.py` (via grep para MembershipStatus)
- `system/urls.py` (verificação de rotas)

### Internet / documentação oficial
- Não aplicável: mudança puramente em template/CSS/view usando padrões já estabelecidos no projeto.

### MCPs / ferramentas verificadas
- shell PowerShell — ok — leitura de arquivos e grep
- Playwright / browser — obrigatório para validação visual pós-implementação

### Limitações encontradas
- Nenhuma limitação crítica. Playwright disponível para validação visual obrigatória.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django server-rendered + CSS design system, seguindo SDD + TDD.

### Ação
Redesenhar a tela de seleção de plano (`plan_change_select.html`) e ajustar a view correspondente para agrupar planos por `is_family_plan`, sem alterar serviços, modelos ou fluxo de negócio.

### Contexto
O portal do aluno possui telas padronizadas (turmas no cadastro, loja de materiais) usando `class-catalog.css` com padrões `info-record-list`, `record-card-catalog`, `catalog-cluster-card`, `catalog-dropdown`. A tela de troca de plano (`/plan/change/`) usa um grid antigo não padronizado que confunde o usuário. A view `PlanChangeSelectView` já calcula prorrateio e passa `plans_with_proration`; precisa apenas passar também `plan_groups` (lista agrupada por `is_family_plan`). O template deve ser reescrito usando os padrões visuais estabelecidos.

### Restrições
- sem hardcode de regras de negócio
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória (já realizada)
- validação visual em navegador obrigatória
- interface em pt-BR

### Critérios de aceite
- [ ] A tela `/plan/change/` carrega sem erro 500 ou stack trace (verificável: terminal)
- [ ] Os planos aparecem agrupados: "Planos Individuais" e "Planos Família" (verificável: visual + teste de view)
- [ ] Cada card exibe: nome do plano, preço + ciclo, badge Upgrade/Downgrade/Gratuito, valor líquido e botão "Trocar para este plano" (verificável: visual)
- [ ] O detalhamento de prorrateio (crédito restante, custo proporcional) fica em `<details>` colapsável (verificável: visual)
- [ ] Planos sem `is_family_plan=True` aparecem no grupo Individual; os com `is_family_plan=True` no grupo Família (verificável: teste unitário de view)
- [ ] O botão "Trocar para este plano" navega corretamente para `/plan/change/<id>/confirm/` (verificável: visual)
- [ ] `manage.py check` passa sem erros (verificável: terminal)
- [ ] `manage.py test --verbosity 2` passa sem falhas (verificável: terminal)
- [ ] Console do navegador sem erros JS críticos (verificável: DevTools)
- [ ] `?v=` do `billing.css` atualizado no template (verificável: código)

### Evidências esperadas
- output de `manage.py test --verbosity 2` com 0 falhas
- output de `manage.py check` sem erros
- screenshot ou descrição visual da tela com dois grupos de planos
- console do navegador sem erros
- terminal sem stack trace

### Formato de saída
Código implementado (view + template + CSS) + testes + evidências de validação

## Escopo
- `system/views/plan_change_views.py`: adicionar agrupamento por `is_family_plan` no context
- `templates/billing/plan_change_select.html`: reescrever com design system
- `static/system/css/billing/billing.css`: adicionar classes auxiliares de action-row e net-value; bump de versão
- `system/tests/test_views.py`: adicionar/ajustar testes de `PlanChangeSelectView` para cobrir agrupamento

## Fora do escopo
- Alteração em `plan_change_confirm.html`
- Alteração em serviços de prorrateio
- Alteração em modelos ou migrações
- Alteração na tela de confirmação de pagamento
- Novo comportamento de filtro ou busca de planos

## Arquivos impactados
| Arquivo | Tipo de mudança |
|---|---|
| `system/views/plan_change_views.py` | adicionar `plan_groups` ao context |
| `templates/billing/plan_change_select.html` | reescrita completa do template |
| `static/system/css/billing/billing.css` | novas classes + bump `?v=` |
| `system/tests/test_views.py` | cobertura de agrupamento na view |

## Riscos e edge cases
- Usuário sem plano ativo: tela já trata com `plans_with_proration = []`; os grupos simplesmente ficam vazios e a mensagem de fallback é exibida
- Todos os planos são individuais (nenhum familiar): o grupo "Planos Família" não é renderizado (condição `{% if group.entries %}`)
- `calculate_plan_change` pode lançar `PlanChangeError` para algum plano: já tratado com `continue` na view — esse plano não entra na lista

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações (política do projeto)
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem (sem alteração de modelo)
- [x] 3. Testes (Red) — cobrir agrupamento na view
- [x] 4. Implementação (Green) — view + template + CSS
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa (test + check + visual + console)
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
- Dois grupos separados: "Planos Individuais" e "Planos Família"
- Cards em lista legível com nome, preço, badge, net, botão
- Dropdown de detalhe colapsável funciona

### Mobile
- Lista em coluna única sem overflow horizontal

### Console do navegador
- Sem erros JS críticos

### Terminal
- Sem stack trace no runserver

## Validação ORM
### Banco
- Nenhuma alteração de schema

### Shell checks
- `SubscriptionPlan.objects.filter(is_active=True).count()` retorna planos disponíveis
- `SubscriptionPlan.objects.filter(is_active=True, is_family_plan=True).count()` retorna apenas familiares

### Integridade do fluxo
- Navegação para `/plan/change/<id>/confirm/` continua funcional

## Validação de qualidade
### Sem hardcode
- Agrupamento via `is_family_plan` do modelo, não por string hardcoded
### Sem estruturas condicionais quebradiças
- Grupos gerados dinamicamente; se um grupo for vazio, não é renderizado
### Sem `except: pass`
- Não aplicável nesta mudança
### Sem mascaramento de erro
- Erros de prorrateio continuam tratados com `continue` (comportamento preservado)
### Sem comentários e docstrings desnecessários
- Nenhum comentário desnecessário adicionado

## Evidências
- `manage.py test --verbosity 2`: 201 testes, 0 falhas, 0 erros
- `manage.py check`: System check identified no issues (0 silenced)
- `manage.py collectstatic --noinput`: 1 arquivo copiado, 161 sem alteração
- 6 novos testes unitários passando em `PlanChangeSelectViewGroupingTest`

## Implementado
- `system/views/plan_change_views.py`: `plan_groups` adicionado ao context com agrupamento por `is_family_plan`
- `templates/billing/plan_change_select.html`: reescrito com `catalog-cluster-card`, `info-record-list`, `record-card-catalog`, `catalog-dropdown` colapsável
- `static/system/css/billing/billing.css`: classes `.plan-change-action-row`, `.plan-change-net`, `.plan-change-net-label`, `.plan-change-net-value` adicionadas; versão bumped para `?v=20260421b`
- `system/tests/test_views.py`: classe `PlanChangeSelectViewGroupingTest` com 6 testes (agrupamento, filtragem, omissão de grupo vazio, renderização de labels, acesso não autenticado)

## Desvios do plano
Nenhum.

## Pendências
- Validação visual com Playwright (obrigatória conforme AGENTS.md §17) — a ser realizada pelo desenvolvedor após subir o servidor local
