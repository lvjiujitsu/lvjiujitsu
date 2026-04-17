# PRD-019: Cadastro por etapas, planos por meio de pagamento e controle financeiro
## Resumo
Revisar o cadastro público para filtrar turmas conforme sexo biológico/faixa etária, validar cada etapa antes do avanço, redesenhar a seleção de planos por PIX/cartão e criar controle financeiro administrativo com bruto, taxa operacional, líquido e status de crédito.

## Problema atual
- A etapa de turmas exibe opções incompatíveis com o aluno, como Feminino/Kids/Juvenil para titular adulto masculino.
- Validações importantes, como CPF já cadastrado e faixa de Jiu Jitsu obrigatória, só aparecem no envio final.
- A seleção de planos não diferencia visualmente PIX/cartão, não separa planos familiares conforme elegibilidade e não apresenta os novos valores comerciais.
- O administrativo não possui uma tabela simples para entender entradas, descontos de gateway, líquido esperado e se o valor já foi creditado/depositado.

## Objetivo
- Exibir ao titular adulto masculino apenas turma adulto, com horários e aviso de que pode treinar em todos os horários disponíveis.
- Exibir à titular adulta feminina turma adulto e opção de turma feminina sem custo inicial, com aviso de possível cobrança futura.
- Para crianças/dependentes, selecionar automaticamente a turma ideal por faixa etária, permitir Kids/Juvenil ou ambas e dobrar a cobrança quando ambas forem escolhidas.
- Aplicar a mesma regra para titular com dependente e para responsável.
- Impedir avanço de etapa quando houver erro mínimo obrigatório, incluindo CPF existente/duplicado e campos condicionais de arte marcial.
- Atualizar os planos comerciais solicitados, com método de pagamento e regra de visibilidade de planos familiares.
- Criar controle financeiro administrativo com aluno, plano, status, gateway, bruto, taxa, líquido, status de crédito/depósito e data prevista.

## Contexto consultado
  - Context7:
    - Django Forms: validação executa `Field.clean`, `clean_<field>()` e depois `Form.clean()`, com `ValidationError` por campo ou `add_error`.
    - Django Admin: `ModelAdmin.list_display` e `readonly_fields` podem expor campos calculados/operacionais para leitura administrativa.
  - Web:
    - Django 4.1 Form validation: https://docs.djangoproject.com/en/4.1/ref/forms/validation/
    - Django 4.1 Admin: https://docs.djangoproject.com/en/4.1/ref/contrib/admin/
    - Stripe Brasil pricing: https://stripe.com/en-br/pricing — cartão doméstico 3,99% + R$ 0,39 por transação bem-sucedida.
    - Asaas Pix: https://www.asaas.com/pix-asaas — Pix recebido com taxa fixa de R$ 1,99 após período promocional.

## Dependências adicionadas
  - nenhuma

## Escopo / Fora do escopo
### Escopo
- `SubscriptionPlan`: método de pagamento, flag de plano familiar e preço mensal de referência.
- Seed de planos com os valores PIX/cartão padrão e familiares.
- Catálogo de planos no cadastro filtrando planos familiares apenas quando elegível.
- Cards de turma no cadastro com horários, mensagens comerciais e sincronização com os selects reais.
- Endpoint de validação por etapa para impedir avanço com CPF existente, CPF duplicado, faixa/graduação ausente e turma inválida.
- Cálculo financeiro em pedidos de matrícula com taxa Asaas/Stripe, líquido, gateway e status/data de crédito.
- Tela administrativa de controle financeiro e exposição básica no Django admin.

### Fora do escopo
- Consulta real de liquidação bancária no Stripe/Asaas; o sistema registra estimativa e status operacional editável.
- Parcelamento real no gateway além do pagamento à vista informado como "1x".
- Alteração da política comercial de materiais/produtos.
- Reset destrutivo do banco local.

## Arquivos impactados
  - `system/models/plan.py`
  - `system/models/registration_order.py`
  - `system/models/class_membership.py`
  - `system/models/__init__.py`
  - `system/forms/plan_forms.py`
  - `system/forms/registration_forms.py`
  - `system/services/registration_checkout.py`
  - `system/services/registration_validation.py`
  - `system/services/financial_transactions.py`
  - `system/services/seeding.py`
  - `system/services/asaas_checkout.py`
  - `system/services/asaas_webhooks.py`
  - `system/services/stripe_checkout.py`
  - `system/services/stripe_webhooks.py`
  - `system/views/auth_views.py`
  - `system/views/billing_admin_views.py`
  - `system/views/__init__.py`
  - `system/urls.py`
  - `system/admin.py`
  - `lvjiujitsu/settings.py`
  - `.env.example`
  - `templates/login/register.html`
  - `templates/plans/plan_*.html`
  - `templates/billing/financial_entries.html`
  - `templates/base.html`
  - `static/system/js/auth/registration-wizard-clean.js`
  - `static/system/css/auth/login.css`
  - `static/system/css/billing/billing.css`
  - `system/tests/test_forms.py`
  - `system/tests/test_views.py`
  - `system/tests/test_plan_models.py`
  - `system/tests/test_services.py`
  - `system/tests/test_asaas.py`
  - `system/migrations/0002_registrationorder_administrative_fee_and_more.py`

## Riscos e edge cases
  - Aluno adulto sem data de nascimento não pode ter turma validada; a etapa de dados deve bloquear antes.
  - Titular mulher adulta pode escolher Adulto + Feminino; a cobrança permanece simples inicialmente.
  - Dependente com Kids + Juvenil deve gerar cobrança dobrada tanto no resumo JS quanto no backend.
  - Plano familiar não pode ser enviado manualmente quando o cadastro não for elegível.
  - O endpoint de etapa não substitui o `PortalRegistrationForm`; o envio final continua sendo a fonte de segurança.
  - Taxas de gateway podem mudar; os valores implementados são os informados/consultados para este PRD.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
  - SDD: implementação limitada a este PRD.
  - TDD: testes de regressão antes do código para validação por etapa, planos e cálculo financeiro.
  - MTV: views finas; regras de validação/cálculo em forms/services.
  - Service Objects: cálculo financeiro e criação de pedidos em serviços transacionais quando houver escrita.
  - Segurança: CSRF mantido no POST de validação de etapa; validação server-side obrigatória no envio final.
  - Frontend: sem CSS/JS inline; arquivos namespaced existentes.

## Critérios de aceite (escritos como assertions testáveis)
  - [x] Ao preencher titular homem adulto, a etapa de turmas deve oferecer somente Adulto e informar todos os horários disponíveis.
  - [x] Ao preencher titular mulher adulta, a etapa de turmas deve oferecer Adulto e Feminino, com Feminino opcional e aviso de cobrança futura.
  - [x] Ao cadastrar criança/dependente, a turma ideal deve vir selecionada conforme idade.
  - [x] Ao selecionar Kids e Juvenil para a mesma criança, o resumo e o pedido devem dobrar o valor do plano.
  - [x] Ao tentar avançar com CPF já cadastrado, o wizard deve bloquear na etapa atual.
  - [x] Ao selecionar Jiu Jitsu sem faixa, o wizard deve bloquear na etapa de prontuário atual.
  - [x] Plano familiar só deve aparecer para titular com dependente ou responsável com 2 ou mais crianças.
  - [x] O seed deve criar os 12 planos comerciais solicitados com PIX/cartão e preços corretos.
  - [x] A tela de controle financeiro deve listar aluno, plano, status, gateway, bruto, taxa, líquido, status de crédito e data prevista.
  - [x] Pedido PIX deve calcular taxa de R$ 1,99 e líquido bruto - taxa.
  - [x] Pedido cartão deve calcular taxa de 3,99% + R$ 0,39 e líquido bruto - taxa.

## Plano (ordenado por dependência — fundações primeiro)
  - [x] 1. Models e migrações: campos de plano e controle financeiro de pedido.
  - [x] 2. Services: validação por etapa, cálculo financeiro, multiplicador Kids/Juvenil e seed de planos.
  - [x] 3. Forms: validação de plano familiar/método de pagamento e reuso das regras finais.
  - [x] 4. Views e URLs: endpoint de validação por etapa e tela de controle financeiro.
  - [x] 5. Templates e estáticos: cards de turma, planos com ícones PIX/cartão, tabela financeira.
  - [x] 6. Integrações: aplicar financeiro em criação de pedido, PIX Asaas, Stripe e webhooks.
  - [x] 7. Testes Red-Green-Refactor por forms/services/views/plans/Asaas.
  - [x] 8. Validação completa da Fase 6.

## Comandos de validação
  - `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
  - `.\.venv\Scripts\python.exe manage.py makemigrations`
  - `.\.venv\Scripts\python.exe manage.py migrate`
  - `.\.venv\Scripts\python.exe manage.py check`
  - `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms system.tests.test_services system.tests.test_plan_models system.tests.test_views system.tests.test_asaas --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py findstatic system\css\auth\login.css`
  - `.\.venv\Scripts\python.exe manage.py findstatic system\js\auth\registration-wizard-clean.js`
  - `.\.venv\Scripts\python.exe manage.py findstatic system\css\billing\billing.css`
  - `.\.venv\Scripts\python.exe manage.py showmigrations system`
  - Playwright/headless em `/register/` e `/billing/financial/`

## Implementado (preencher ao final)
- Migração `0002` com novos campos comerciais em `SubscriptionPlan` e financeiros em `RegistrationOrder`.
- Seed idempotente dos 12 planos solicitados, separando PIX/cartão, mensal/trimestral/anual e familiar.
- Wizard de cadastro com validação server-side por etapa via `register/validate-step/`, bloqueando CPF existente/duplicado, turma inválida e Jiu Jitsu sem faixa.
- Cards de turmas filtrados por sexo/idade, com Adulto para homem adulto, Adulto/Feminino opcional para mulher adulta, Kids/Juvenil para criança e cobrança dobrada quando ambas são selecionadas.
- Seleção de planos com ícones PIX/CARD, metadados de mensalidade equivalente, pagamento 1x e ocultação de planos familiares quando não elegível.
- Cálculo financeiro centralizado para Asaas PIX (R$ 1,99) e Stripe crédito (3,99% + R$ 0,39), aplicado em criação de pedido, checkout, webhooks e pagamento manual.
- Tela `/billing/financial/` com tabela administrativa de aluno, plano, status, gateway, bruto, taxa, líquido, crédito, previsão e transação.
- Exposição dos novos campos em forms/templates/admin e ajuste da sincronização automática Stripe por flag `STRIPE_PLAN_SYNC_ENABLED`.
- Testes adicionados/atualizados em forms, services, views, planos e Asaas.
- Evidências visuais geradas com Playwright:
  - `registration-holder-male-classes.png`
  - `registration-plan-standard.png`
  - `registration-plan-family.png`
  - `financial-control-table.png`

## Desvios do plano
- Sem dependências novas.
- A liquidação real em banco/gateway permanece fora do escopo; o controle registra gateway, estimativa de taxa, líquido e status operacional.
- `STRIPE_PLAN_SYNC_ENABLED` foi adicionado com default desligado para impedir chamadas externas automáticas durante seed/admin local.
- Dois pedidos artificiais `VALIDATION_PRD_019` foram criados apenas para validar a tabela financeira no navegador e removidos em seguida.
