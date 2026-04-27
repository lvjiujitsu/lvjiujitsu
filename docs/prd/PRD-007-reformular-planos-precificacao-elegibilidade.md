# PRD-007: Reformular planos, precificação, elegibilidade e segmentação Adulto vs Kids/Juvenil

## Resumo do que será implementado

Reformulação completa da estrutura comercial de planos da academia, separando público (Adulto vs Kids/Juvenil), frequência (2x ou 5x por semana), tipo (Individual vs Família) e ciclo (mensal/trimestral/semestral/anual), com nova precificação que garante R$ 200 líquidos por aluno/mês e que internaliza o repasse de 50% do professor de Kids/Juvenil. Inclui regras de elegibilidade (quem vê quais planos) aplicadas no cadastro, na loja e na troca de plano.

## Tipo de demanda

Alteração arquitetural com nova feature comercial. Inclui mudança de schema, reescrita de seed, novas regras de negócio (elegibilidade), atualização de UI e ajuste em fluxos de troca de plano.

## Problema atual

A estrutura atual tem 12 planos simples (Standard/Família × Mensal/Trimestral/Anual × PIX/Cartão), sem distinção de público nem de frequência semanal. Isso gera três problemas:

1. **Empresa pode ficar abaixo do mínimo financeiro** quando o aluno é Kids/Juvenil (o professor recebe 50% por aluno, e o preço atual não absorve esse repasse).
2. **Não há ancoragem comercial 2x/5x**, que é a principal alavanca de upsell desejada.
3. **Plano família aparece para todos** indiscriminadamente, mesmo para adulto solo (sem grupo familiar) ou responsável com apenas 1 dependente.

## Objetivo

- Garantir que a empresa nunca receba menos que R$ 200,00 líquidos por aluno/mês.
- Introduzir frequência 2x e 5x como ancoragem comercial (2x = isca, 5x = principal).
- Separar Adulto e Kids/Juvenil com tabelas próprias, embutindo o repasse de professor no Kids.
- Aplicar regras claras de elegibilidade do plano Família e do Kids/Juvenil 5x.
- Manter PIX (Asaas) com desconto comercial e Cartão (Stripe) com preço cheio parcelável.

## Context Ledger

### Arquivos lidos integralmente

- [system/models/plan.py](system/models/plan.py) — modelo `SubscriptionPlan` atual
- [system/models/membership.py](system/models/membership.py) — `Membership` com FK `PROTECT` para plano (impede deleção)
- [system/models/person.py](system/models/person.py) — `Person`, `PersonRelationship`, `PersonRelationshipKind.RESPONSIBLE_FOR`
- [system/models/category.py](system/models/category.py) — `CategoryAudience` (ADULT/JUVENILE/KIDS/WOMEN), `IbjjfAgeCategory`
- [system/services/seeding.py](system/services/seeding.py) — `seed_plans()` e `SUBSCRIPTION_PLAN_DEFINITIONS` atuais
- [system/services/membership.py](system/services/membership.py) — orquestração de assinaturas, `get_active_membership`, ciclos
- [system/services/plan_change.py](system/services/plan_change.py) — cálculo proporcional de upgrade/downgrade
- [system/services/registration_checkout.py](system/services/registration_checkout.py) — `get_plan_catalog_payload()`, `get_registration_plan_multiplier()`, criação de pedidos
- [system/services/financial_transactions.py](system/services/financial_transactions.py) — provider/checkout action por plano, cálculo de taxa
- [system/services/plan_management.py](system/services/plan_management.py) — leitura simples de planos
- [system/forms/registration_forms.py](system/forms/registration_forms.py) — `_clean_plan_selection`, `_is_family_plan_allowed`
- [system/forms/plan_forms.py](system/forms/plan_forms.py) — `PlanForm` admin
- [system/services/registration_validation.py](system/services/registration_validation.py) — validação por etapa do wizard
- [system/views/plan_change_views.py](system/views/plan_change_views.py) — `PlanChangeSelectView` agrupa por `is_family_plan`
- [system/views/product_views.py](system/views/product_views.py) — loja autenticada e catálogo
- [system/views/plan_views.py](system/views/plan_views.py) — catálogo público e CRUD admin
- [system/admin.py](system/admin.py) — `SubscriptionPlanAdmin`
- [system/constants.py](system/constants.py) — `PersonTypeCode`, `RegistrationProfile`, `CheckoutAction`
- [system/tests/test_plan_models.py](system/tests/test_plan_models.py) — testes do modelo e do seed atual
- [system/tests/test_plan_views.py](system/tests/test_plan_views.py) — testes das views de plano
- [templates/billing/plan_change_select.html](templates/billing/plan_change_select.html) — UI de troca de plano
- [system/migrations/0001_initial.py](system/migrations/0001_initial.py) — schema inicial do `SubscriptionPlan`
- Trecho relevante de [static/system/js/auth/registration-wizard-clean.js](static/system/js/auth/registration-wizard-clean.js) (filtro de planos do wizard, `groupPlansForDropdown`, `getVisiblePlanCatalog`, `isFamilyPlanEligible`)

### Arquivos adjacentes consultados

- [system/forms/product_forms.py](system/forms/product_forms.py)
- [system/services/plan_management.py](system/services/plan_management.py)
- [system/models/registration_order.py](system/models/registration_order.py) (FKs/PROTECT)

### Internet / documentação oficial

- Lei 13.455/2017 (diferenciação de preço por instrumento de pagamento) — base legal usada na comunicação PIX/Cartão
- Asaas (taxa PIX R$ 1,99) e Stripe Brasil (3,99% + R$ 0,39, R$ 55 contestação) — referências do documento de demanda

### MCPs / ferramentas verificadas

- `Read`, `Grep`, `Glob`, `Bash` — funcionando no ambiente Windows
- `manage.py test` — disponível via `.venv`

### Limitações encontradas

- Mudança de schema é **necessária** (campos `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization`). O `CLAUDE.md` §8 e §24 e o `AGENTS.md` §15 proíbem criar arquivo de migração à mão — a alteração de schema neste projeto se faz pelo ciclo destrutivo `clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds, que regenera `0001_initial.py` do zero. Todo o trabalho de modelo, services, seeds e testes deve estar pronto **antes** de pedir autorização para rodar o ciclo.
- Stripe Sync não será re-disparado nesta entrega — os Stripe Price IDs antigos somem junto com a `0001_initial.py` no reset; re-sincronização entra em PRD posterior.
- Política de cancelamento, reembolso e matriz N:N completa de upgrade/downgrade ficam fora desta entrega — entram em PRD-008.
- Diária avulsa ainda não tem entidade de produto/serviço dedicada e fica fora desta entrega (PRD-009).

## Prompt de execução

### Persona

Agente de desenvolvimento Django sênior trabalhando em modo control-first com SDD + TDD.

### Ação

Reformular o domínio de planos do app `system` conforme a especificação abaixo, mantendo retrocompatibilidade com `Membership` legados via desativação dos planos antigos (não deleção).

### Contexto

A academia opera com Stripe (cartão) + Asaas (PIX), tem cadastro com perfis HOLDER/GUARDIAN/OTHER e turmas Adulto/Juvenil/Kids/Feminino. A demanda separa o domínio comercial em duas tabelas (Adulto e Kids/Juvenil) com base em quem treina e qual repasse o professor recebe.

### Restrições

- sem hardcode de segredo
- sem mascaramento de erro
- **proibido** criar arquivo de migração à mão; alteração de schema ocorre via ciclo destrutivo (apenas `0001_initial.py` deve existir após o ciclo)
- leitura integral obrigatória (concluída acima)
- testes precisam continuar passando
- como o ciclo destrutivo apaga o banco, planos legados não precisam ser preservados — basta reescrever o seed para já gerar a nova matriz
- comunicação PIX/Cartão segue o documento (preço cheio cartão, desconto comercial PIX)

### Critérios de aceite

- [ ] `SubscriptionPlan` ganha campos `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization` (verificável: leitura do modelo + `showmigrations` mostrando apenas `0001_initial`)
- [ ] `seed_plans()` produz 64 planos novos com a matriz Adulto/Kids × 2x/5x × Individual/Família × 4 ciclos × 2 métodos (verificável: teste unitário sobre contagem e amostras)
- [ ] Preço de cada plano respeita a tabela do documento (verificável: testes de amostra para cada combinação)
- [ ] Após o ciclo destrutivo, apenas `0001_initial.py` existe em `system/migrations/` (verificável: `ls`)
- [ ] Adulto solo (sem dependente) só vê planos Adulto Individual no cadastro (verificável: teste de form)
- [ ] Adulto com dependente vê Adulto + Kids/Juvenil; Família só liberada se grupo tiver 2+ alunos ativos (verificável: teste de form)
- [ ] Responsável com 1 dependente Kids só vê Kids Individual (verificável: teste de form)
- [ ] Responsável com 2+ dependentes Kids vê Kids Individual + Família (verificável: teste de form)
- [ ] Plano Kids 5x não é exibido sem autorização (verificável: campo `requires_special_authorization=True` filtrado por padrão)
- [ ] `plan_change_select.html` agrupa planos por audiência e frequência (verificável: leitura do template)
- [ ] JS do wizard filtra planos pelo público correto (verificável: navegação manual + leitura do payload)
- [ ] `manage.py test --verbosity 2` passa com 0 falhas
- [ ] `manage.py check` passa sem warnings novos

### Evidências esperadas

- testes passando
- `manage.py showmigrations` mostrando apenas `system.0001_initial` (regenerada)
- console do navegador limpo na tela de cadastro e troca de plano
- terminal sem stack trace
- shell check via ORM mostrando os 64 planos novos ativos

### Formato de saída

Código + testes + relatório de evidências.

## Escopo

1. Modelo `SubscriptionPlan` ganha 4 novos campos (alteração de `code` `max_length` se necessário).
2. Reescrita do `SUBSCRIPTION_PLAN_DEFINITIONS` em `seeding.py`, gerada programaticamente a partir de matriz de preços-base e multiplicadores de ciclo (64 planos).
3. Novo selector `system/selectors/plan_eligibility.py` com função pura para filtrar planos por contexto de cadastro/portal.
4. Atualização do `_clean_plan_selection` em `registration_forms.py` para usar o novo selector e respeitar `audience`/`requires_special_authorization`.
5. Atualização de `PlanChangeSelectView` para usar o selector e agrupar por `audience` + `weekly_frequency`.
6. Atualização do `get_plan_catalog_payload()` para enriquecer payload com `audience`, `weekly_frequency`, `teacher_commission_percentage`, `requires_special_authorization`.
7. Atualização do JS do wizard para filtrar por audience/frequência conforme perfil + dependentes selecionados.
8. Atualização do template `plan_change_select.html` para nova ancoragem (5x primeiro, 2x depois; Família visível só quando elegível).
9. Atualização do `SubscriptionPlanAdmin` com novos campos.
10. Atualização do `PlanForm` admin com novos campos.
11. Ajuste de `get_registration_plan_multiplier` (remover dobra para Kids+Juvenil — repasse já está no preço novo).
12. Cobertura de teste para modelo, seed, elegibilidade, form, view e payload do wizard.
13. Ciclo destrutivo: pedir autorização e rodar `clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds.

## Fora do escopo

- Política completa de cancelamento, reembolso e chargeback (PRD-008).
- Matriz N:N de upgrade/downgrade entre todos os 64 planos (PRD-008).
- Diária avulsa como produto (PRD-009).
- Re-sincronização Stripe (Price archival, novos Prices) — fica para PRD-010.
- Tela administrativa de visualização de "elegibilidade do aluno X".

## Arquivos impactados

- [system/models/plan.py](system/models/plan.py)
- [system/models/__init__.py](system/models/__init__.py) (exporta novos enums)
- [system/migrations/0001_initial.py](system/migrations/0001_initial.py) — regenerada pelo ciclo destrutivo
- [system/services/seeding.py](system/services/seeding.py)
- [system/services/registration_checkout.py](system/services/registration_checkout.py) (`get_plan_catalog_payload`, `get_registration_plan_multiplier`)
- [system/selectors/plan_eligibility.py](system/selectors/plan_eligibility.py) (novo)
- [system/forms/registration_forms.py](system/forms/registration_forms.py)
- [system/forms/plan_forms.py](system/forms/plan_forms.py)
- [system/views/plan_change_views.py](system/views/plan_change_views.py)
- [system/views/plan_views.py](system/views/plan_views.py) (catálogo público pode precisar de novo agrupamento)
- [system/admin.py](system/admin.py)
- [static/system/js/auth/registration-wizard-clean.js](static/system/js/auth/registration-wizard-clean.js)
- [templates/billing/plan_change_select.html](templates/billing/plan_change_select.html)
- [system/tests/test_plan_models.py](system/tests/test_plan_models.py)
- [system/tests/test_plan_eligibility.py](system/tests/test_plan_eligibility.py) (novo)
- [system/tests/test_forms.py](system/tests/test_forms.py)
- [system/tests/test_services.py](system/tests/test_services.py) (se necessário)

## Riscos e edge cases

- **Banco regenerado:** ciclo destrutivo apaga `db.sqlite3` e reescreve `0001_initial.py`. Ambiente local volta limpo; nenhum dado de produção é tocado pois banco prod não está aqui.
- **Adulto que também é responsável (titular + dependente):** elegível para Adulto Individual + Adulto Família + Kids Individual + (Kids Família se 2+ kids).
- **Família com 1 adulto + 1 dependente Kids:** elegível para Adulto 2x/5x Família e Kids 2x Individual. Não é elegível para Kids Família (precisa de 2+ kids).
- **Kids 5x:** sai do payload por padrão. Será exibido somente se for marcado como autorizado (campo no plano + autorização do aluno; nesta entrega, fica oculto sempre — autorização administrativa fica em PRD-010 mas o gating já existe no campo `requires_special_authorization`).
- **`get_registration_plan_multiplier`:** hoje multiplica preço por 2 quando KIDS+JUVENILE no mesmo grupo de matrícula. Com a nova precificação Kids embutindo 50% repasse, esta lógica vira **redundante e prejudicial** (cobrança em dobro). Remover/zerar.

## Regras e restrições

- SDD antes de código
- TDD para implementação (testes primeiro de modelo/seed/elegibilidade)
- sem hardcode
- sem mascaramento de erro
- **proibido** criar migração à mão; uso obrigatório do ciclo destrutivo descrito em `CLAUDE.md` §24
- leitura integral obrigatória (concluída)
- validação obrigatória

## Plano

- [x] 1. Contexto e leitura integral
- [x] 2. Atualizar modelo `SubscriptionPlan` (campos + enums + exports)
- [ ] 3. Atualizar testes do modelo (Red → Green)
- [ ] 4. Reescrever `seed_plans` (Red → Green)
- [ ] 5. Criar selector `plan_eligibility` (Red → Green)
- [ ] 6. Atualizar formulário do wizard
- [ ] 7. Atualizar view de troca de plano
- [ ] 8. Ajustar `get_registration_plan_multiplier` (sem dobra Kids)
- [ ] 9. Atualizar JS do wizard
- [ ] 10. Atualizar templates
- [ ] 11. Atualizar admin/PlanForm
- [ ] 12. Refatorar onde fizer sentido (DRY na geração da matriz)
- [ ] 13. Pedir autorização e rodar ciclo destrutivo (`clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds)
- [ ] 14. `manage.py check` e `collectstatic` se necessário
- [ ] 15. Validação visual em navegador
- [ ] 16. Limpeza final
- [ ] 17. Atualização documental (este PRD + relatório)

## Validação visual

### Desktop

- Tela de cadastro (`/portal/cadastro`) — etapas plano e checkout, com perfis Adulto/Responsável + dependente
- Tela de troca de plano (`/portal/financeiro/trocar-plano`) — agrupamento por audiência/frequência
- Catálogo público de planos (`/planos`) — exibição com nova ancoragem

### Mobile

- Mesmas três telas em viewport ≤ 480px

### Console do navegador

- Sem erros JS na carga e na seleção de plano
- Sem 404 de assets (cache-busting `?v=` atualizado)

### Terminal

- `runserver` sem stack trace
- Sem `DeprecationWarning` novo

## Validação ORM

### Banco

- 76 planos no total: 64 ativos (novos) + 12 inativos (legados)

### Shell checks

```python
from system.models import SubscriptionPlan
SubscriptionPlan.objects.filter(is_active=True).count()  # 64
SubscriptionPlan.objects.filter(is_active=False).count() # 12
SubscriptionPlan.objects.filter(audience="kids_juvenile", weekly_frequency=5).count()  # 16
```

### Integridade do fluxo

- `Membership.objects.filter(plan__is_active=False).count()` retorna número esperado se houver memberships antigos.

## Validação de qualidade

### Sem hardcode

Preços vivem em uma matriz dicionário em `seeding.py`, multiplicadores de ciclo são constantes nomeadas. Nenhum segredo.

### Sem estruturas condicionais quebradiças

Selector usa guard clauses curtas; nada com >2 níveis de aninhamento.

### Sem `except: pass`

Não introduzido.

### Sem mascaramento de erro

Validações lançam `ValidationError` com mensagens claras.

### Sem comentários e docstrings desnecessários

Nomes auto-explicativos. Comentário só em decisões não óbvias (tabela legal, repasse 50%).

## Evidências

(a preencher após implementação)

## Implementado

(a preencher após implementação)

## Desvios do plano

(a preencher após implementação)

## Pendências

- PRD-008: política de cancelamento, reembolso, chargeback, matriz completa upgrade/downgrade
- PRD-009: diária avulsa como produto
- PRD-010: autorização administrativa de Kids 5x e re-sincronização Stripe
