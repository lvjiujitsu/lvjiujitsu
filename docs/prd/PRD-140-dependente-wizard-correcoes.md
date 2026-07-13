# PRD-140: Correções do wizard de "Adicionar dependente"

## Summary
Corrigir o wizard de "Adicionar dependente" (reimplementado nesta mesma sessão para reaproveitar o visual de `auth/register.css`) em cinco pontos concretos apontados pelo usuário: cabeçalho do popup, filtro de turmas por idade/sexo, filtro de planos por idade, espaçamento dentro do popup e ausência de etapa de revisão antes da confirmação final.

## Demand type
Correção de UX + regra de negócio + Django MVT.

## Current problem
1. O cabeçalho do popup não exibe o nome da ação ("Adicionar dependente") abaixo da linha de etapas; o fechar está como link de texto à esquerda, não como ícone "X" à direita.
2. A etapa "Escolha a turma" lista todas as turmas do catálogo, sem filtrar por idade/sexo do dependente — quebra a regra de negócio de elegibilidade por categoria (`CategoryAudience`) já aplicada no wizard público (`register.js: filterGroupsByPerson`).
3. A etapa "Escolha o plano do dependente" também não filtra por idade (`PlanAudience`) nem por elegibilidade de plano familiar — mostra planos adulto para dependentes kids/juvenil e vice-versa.
4. O conteúdo do wizard encosta nas bordas do popup em alguns pontos; falta padding consistente dentro do modal.
5. Não existe etapa de revisão final: ao confirmar a última etapa (materiais), o formulário é enviado direto, sem uma tela de "Revisar e confirmar" antes da submissão real — diferente do wizard público, que tem `step-review`.

## Goal
O wizard de "Adicionar dependente" replica fielmente o comportamento e as regras de negócio do wizard público de cadastro (`/register/`): cabeçalho com ação identificada e fechar por ícone, turmas e planos elegíveis filtrados por idade/sexo do dependente, espaçamento consistente dentro do popup, e uma etapa de revisão antes da submissão final.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`
- `templates/dependents/dependent_registration.html` (versão reimplementada nesta sessão)
- `templates/login/register.html` (referência de layout, `step-dep`, `step-health`, `step-martial`, `step-classes`, `step-plan`, `step-review`)
- `static/system/js/auth/register.js` (`filterGroupsByPerson`, `resolveAudience`, `calcAgeYears`, `getEligiblePlansForCurrentPerson`)
- `static/system/css/auth/register.css`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/services/class_catalog.py` (`get_ibjjf_age_category_payload`)
- `system/services/class_overview.py` (`get_registration_catalog_payload`)
- `system/services/registration_checkout.py` (`get_plan_catalog_payload`)

### Adjacent files consulted
- `static/system/js/dependents/dependent_registration.js` (nova versão desta sessão)
- `static/system/css/dependents/dependent_registration.css` (nova versão desta sessão)
- `templates/home/dashboard.html` (dialog `dependent-registration-modal`)

### Limitations found
- O wizard público resolve elegibilidade de turma/plano inteiramente no cliente (JS), usando `ibjjf_categories_json` para mapear idade → audiência. O wizard de dependente precisa do mesmo catálogo injetado no contexto da view.
- Não existe hoje nenhuma etapa de revisão no fluxo de dependente; será necessário construir um resumo client-side (nome, CPF, turma, plano, materiais) a partir dos mesmos campos já preenchidos, sem duplicar estado em `sessionStorage` (o formulário já é um único POST).

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
O usuário revisou o resultado da reimplementação anterior e listou objeções específicas, pedindo "CORRIJA ESPECIFICAMENTE TUDO ISSO. gere um prd novo. e corrija isso." — autoriza implementação imediata do escopo abaixo.

## Scope
- Cabeçalho do wizard de dependente: ícone "X" fixo à direita para fechar; texto da ação ("Adicionar dependente") abaixo da barra de progresso.
- Filtro de turmas por idade/sexo do dependente na etapa 4, usando o mesmo catálogo IBJJF do wizard público.
- Filtro de planos por idade do dependente (e elegibilidade de plano familiar) na etapa 5.
- Ajuste de padding/espaçamento do `.wizard-shell` dentro do iframe modal.
- Nova etapa 7 "Revisar e confirmar" antes do envio real do formulário.

## Out of scope
- Alterar o fluxo de edição de dependente (`dependent_edit.html`), que permanece página única sem paginação.
- Alterar a lógica de pagamento/gateway já validada (Stripe/Asaas).
- Alterar o wizard público `/register/`.

## Impacted files
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`
- `system/views/dependent_views.py`
- `system/tests/test_dependent_registration.py`

## Plan
1. Injetar `ibjjf_categories_json` no contexto de `DependentRegistrationView`.
2. Reescrever o cabeçalho do template (X à direita, título de ação abaixo da barra).
3. Implementar `resolveAudience`/`calcAgeYears` no JS do dependente e filtrar turmas por `category_audience` (mesma regra do público).
4. Filtrar planos por `audience` e por elegibilidade de plano familiar (contagem de pessoas não se aplica aqui — dependente é 1 pessoa; plano familiar exige `family_plan_available` do form, já existente).
5. Ajustar CSS de padding do `.wizard-shell` em modo modal.
6. Adicionar etapa de revisão (nova seção `data-step="7"`) que lê os campos já preenchidos via JS e monta um resumo; o botão final desta etapa é que efetivamente submete o formulário.
7. Testes: ajustar/():adicionar cobertura para o novo total de etapas e contexto `ibjjf_categories_json`.
8. `manage.py check`, `node --check`, suíte focada, validação visual no navegador interno.

## Test plan
### Tests to author/adjust
- Contexto da view inclui `ibjjf_categories_json`.
- Suíte existente de `test_dependent_registration` continua verde (não deve quebrar payload/HTML core).

### Execution authorization
Autorizada pelo pedido atual.

## Visual hierarchy
- Cabeçalho: logo central, "Etapa X de Y" à direita, "X" fechar à direita (topo), "Voltar" à esquerda quando etapa > 1.
- Abaixo da barra de progresso: título fixo da ação ("Adicionar dependente").
- Abaixo: badge da etapa (ex. "Turma") + heading específico.
- Última etapa antes do envio: resumo revisável (Revisar e confirmar).

## Evidence
- Pendente.

## Implemented
- Pendente.

## Final status
Não concluída.
