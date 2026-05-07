# PRD-012: Modulo financeiro e repasses

## Resumo do que será implementado
Implementar uma visao financeira administrativa com KPIs ASAAS e Stripe lado a lado, historico unificado de entradas e saidas, regras de repasse por pessoa da equipe, e visao individual de repasses para professor ou administrativo.

## Tipo de demanda
Nova feature + integracao externa + alteracao arquitetural interna.

## Problema atual
O sistema ja registra pedidos, taxas, gateways, webhooks e uma folha simples de professores com valor mensal fixo. A tela financeira atual lista apenas entradas de pedidos. Nao ha consolidacao ASAAS/Stripe, historico unificado de entradas e saidas, regra proporcional por aluno/aula, nem configuracao de repasse no cadastro de pessoa.

## Objetivo
Permitir que o administrativo acompanhe valores a receber ASAAS e Stripe, veja KPIs separados e consolidados, visualize entradas e saidas vinculadas a pessoas, configure repasses para professores e administrativos, e gere fechamentos mensais com historico visivel ao professor ou administrativo.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `requirements.txt`
- `lvjiujitsu/settings.py`
- `system/constants.py`
- `system/models/__init__.py`
- `system/models/asaas.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/models/registration_order.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/calendar.py`
- `system/models/class_schedule.py`
- `system/forms/person_forms.py`
- `system/forms/payroll_forms.py`
- `system/views/__init__.py`
- `system/views/asaas_views.py`
- `system/views/billing_admin_views.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/urls.py`
- `templates/base.html`
- `templates/billing/financial_entries.html`
- `templates/billing/payroll_list.html`
- `templates/billing/payout_queue.html`
- `templates/home/instructor/financial.html`
- `templates/people/person_form.html`
- `static/system/css/billing/billing.css`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/services/asaas_payroll.py`
- `system/services/asaas_webhooks.py`
- `system/services/financial_transactions.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_sync.py`
- `system/services/stripe_webhooks.py`
- `system/services/class_calendar.py`
- `system/services/seeding.py`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`
- `system/tests/test_models.py`
- `system/tests/test_commands.py`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/schedule_monthly_payouts.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_test_personas.py`

### Arquivos adjacentes consultados
- `system/admin.py`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`

### Internet / documentacao oficial
- Stripe API Reference: `GET /v1/balance` e `Balance.retrieve()`.
- Stripe API Reference: `GET /v1/balance_transactions` e historico de balance transactions.
- Asaas API Reference: `GET /v3/finance/balance`.
- Asaas API Reference: `GET /v3/finance/payment/statistics?status=PENDING`.

### MCPs / ferramentas verificadas
- PowerShell + `.venv` — OK — `.\.venv\Scripts\python.exe --version`
- Django check — OK — `.\.venv\Scripts\python.exe manage.py check`
- Context7 — OK — consulta Django ModelForm/CBV
- Stripe skill — OK — `stripe-best-practices` consultada
- Browser Use — OK — abriu `http://localhost:8000/home/administrative/` no navegador in-app e confirmou painel administrativo.
- Playwright `.venv` — OK — validacao visual desktop/mobile em navegador isolado.

### Limitacoes encontradas
- `rg` falhou com `Acesso negado`; leitura de arquivos foi feita por PowerShell.
- Politica local proibe novas migracoes por padrao. A implementacao deve reaproveitar tabelas existentes.
- O schema atual nao tem uma tabela propria para regras de repasse por categoria; as regras variaveis serao armazenadas como JSON versionado em `TeacherPayrollConfig.notes`, validado por servico/formulario.

## Prompt de execucao
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + MVT com services/selectors.

### Acao
Implementar modulo financeiro, configuracao de repasses e seeds financeiras seguindo a spec abaixo.

### Contexto
O app `system` concentra o dominio. A tela administrativa atual `billing/financial_entries.html` sera expandida. A folha existente usa `TeacherPayrollConfig`, `TeacherBankAccount` e `TeacherPayout`; esses modelos serao preservados sem nova migracao.

### Restricoes
- sem hardcode fora de seeds e constantes tecnicas explicitas
- sem mascaramento de erro: falhas ASAAS/Stripe devem aparecer como estado indisponivel com mensagem tecnica curta
- sem novas migracoes
- leitura integral obrigatoria
- validacao obrigatoria
- UI em pt-BR
- identificadores tecnicos em ingles

### Criterios de aceite
- [x] Administrativo ve ASAAS e Stripe lado a lado com disponivel, a receber e total por gateway.
- [x] Administrativo ve KPI consolidado somando ASAAS + Stripe e total de saidas/repasses.
- [x] Historico financeiro mostra entradas de pedidos e saidas de repasses vinculadas a pessoa, gateway/status e data.
- [x] Cadastro/edicao de pessoa permite configurar repasse quando o tipo for Professor ou Administrativo.
- [x] Professor ou administrativo sem repasse obrigatorio pode ter regra inativa ou valor zero sem quebrar fechamento.
- [x] Regras aceitam fixo mensal, valor por aluno, percentual por aluno e valor por aula.
- [x] Fechamento mensal calcula valor esperado com base nas entradas pagas, alunos vinculados e aulas aprovadas.
- [x] Historico individual mostra o que entrou vinculado a pessoa, o que esta previsto e quando ira cair.
- [x] Seed inicial cria configs: Layon adulto fixo R$ 400, Layon juvenil 50%, Andre R$ 0, Vinicius R$ 400, Vanessa Ferro R$ 0.
- [x] Seed de teste cria historico financeiro passado visivel.

### Evidencias esperadas
- testes automatizados passando
- `manage.py check` sem problemas
- `collectstatic --noinput` quando CSS/template versionado for alterado
- validacao visual desktop e mobile
- console do navegador sem erro critico
- terminal sem stack trace

### Formato de saida
Codigo implementado + testes + evidencias de validacao.

## Escopo
- Servico de dashboard financeiro.
- Cliente ASAAS com estatisticas de cobrancas.
- Cliente Stripe para saldo e historico de balance transactions.
- Servico de regras e fechamentos de repasse.
- Formulario de pessoa com campos nao-model de repasse.
- Views/templates para financeiro administrativo, folha, fila e financeiro individual.
- Seeds base e teste.

## Fora do escopo
- Executar transferencias reais sem aprovacao existente.
- Criar novas tabelas ou migracoes.
- Reconciliação contabil completa por NF, split ou antecipacao.
- Webhooks novos alem dos ja existentes.

## Arquivos impactados
- `system/services/financial_dashboard.py` novo
- `system/services/payroll_rules.py` novo
- `system/services/asaas_client.py`
- `system/services/asaas_payroll.py`
- `system/forms/person_forms.py`
- `system/forms/payroll_forms.py`
- `system/views/billing_admin_views.py`
- `system/views/asaas_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/views/__init__.py`
- `templates/billing/financial_entries.html`
- `templates/billing/payroll_list.html`
- `templates/billing/payout_queue.html`
- `templates/home/instructor/financial.html`
- `templates/home/administrative/dashboard.html`
- `templates/people/person_form.html`
- `static/system/css/billing/billing.css`
- `system/services/seeding.py`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`

## Riscos e edge cases
- Dependente pago pelo responsavel precisa ser vinculado ao professor pela turma do dependente.
- Planos familia com mais de um dependente nao devem duplicar o valor integral para cada aluno; o valor deve ser rateado entre alunos vinculados.
- Chaves/API ausentes nao podem derrubar a tela administrativa.
- Regras com valor zero devem ser exibidas sem gerar repasse automatico.
- Pessoas administrativas podem receber repasse mesmo sem turma vinculada.

## Regras e restricoes
- SDD antes de codigo
- TDD para implementacao
- sem hardcode fora de seed
- sem mascaramento de erro
- sem migracoes
- leitura integral obrigatoria
- validacao obrigatoria

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem sem migracao
- [x] 3. Testes (Red)
- [x] 4. Implementacao (Green)
- [x] 5. Refatoracao (Refactor)
- [x] 6. Validacao completa
- [x] 7. Limpeza final
- [x] 8. Atualizacao documental

## Validacao visual
### Desktop
OK — Playwright validou `/billing/financial/`, `/billing/payroll/`, `/billing/payouts/` e `/me/financeiro/` em 1366x900.
### Mobile
OK — Playwright validou `/billing/financial/` em 390x844 com `financial-mobile-overflow=False`.
### Console do navegador
OK — Playwright retornou `console_errors=0`.
### Terminal
OK para a rodada final — as rotas financeiras renderizaram sem stack trace durante a validacao Playwright.

## Validacao ORM
### Banco
OK — `inicial_seed_test` executou e criou 8 personas de teste, administrativo de teste, configs de repasse e historico de repasses.
### Shell checks
OK — configs confirmadas:
- Andre Oliveira: base `0.00`, total atual `0.00`, 0 regra.
- Lauro Viana: base `0.00`, total atual `0.00`, 0 regra.
- Layon Quirino: base `400.00`, total atual `400.00`, 2 regras.
- Vanessa Ferro: base `0.00`, total atual `0.00`, 0 regra.
- Vinicius Antonio: base `400.00`, total atual `400.00`, 1 regra.
- `TeacherPayout.objects.count() == 6`.
- Dashboard local com `history_rows=12`, `local_net_inflows=904.00`, `local_outflows=1798.00`.
### Integridade do fluxo
OK — cadastro de pessoa salva config de repasse para professor; repasse zero nao gera pagamento automatico; folha e tela individual usam calculo mensal dinamico.

## Validacao de qualidade
### Sem hardcode
OK — valores fixos solicitados ficaram restritos a seeds; regras operacionais ficam no JSON versionado de `TeacherPayrollConfig.notes`.
### Sem estruturas condicionais quebradicas
OK — calculos concentrados em `system/services/payroll_rules.py` e dashboard em `system/services/financial_dashboard.py`.
### Sem `except: pass`
OK — nenhum `except: pass` introduzido.
### Sem mascaramento de erro
OK — ASAAS/Stripe indisponiveis retornam estado de provider indisponivel com mensagem na tela, sem derrubar a view.
### Sem comentarios e docstrings desnecessarios
OK — comentarios/docstrings nao foram adicionados sem necessidade.

## Evidencias
Comandos executados:
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 305 testes, OK.
- `.\.venv\Scripts\python.exe manage.py check` — sem problemas.
- `.\.venv\Scripts\python.exe manage.py showmigrations` — `system [X] 0001_initial`, sem nova migracao.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 0 copiados, 164 inalterados.
- `.\.venv\Scripts\python.exe manage.py inicial_seed_test` — seed de teste concluida.
- Playwright `.venv` — `checks=financial-desktop,payroll-desktop,payouts-desktop,own-financial-desktop,financial-mobile-overflow=False`, `console_errors=0`.

## Implementado
- Dashboard financeiro administrativo com ASAAS e Stripe lado a lado, KPIs separados, total consolidado e total local a receber.
- Historico financeiro unificado com entradas de pedidos e saidas de repasses.
- Regras de repasse fixo mensal, valor por aluno, percentual por aluno e valor por aluno/aula.
- Fechamento mensal dinamico usado na folha, fila de pagamentos e tela individual.
- Configuracao de repasse no cadastro/edicao de pessoa para Professor e Administrativo.
- Suporte a financeiro individual para professor e administrativo.
- Seed inicial e seed de teste com configs e historico financeiro visivel.

## Desvios do plano
- Nao foram criadas migracoes, conforme politica do projeto.
- As regras variaveis foram persistidas em JSON versionado dentro de `TeacherPayrollConfig.notes` para respeitar o schema existente.
- O Playwright MCP nao conseguiu abrir nova instancia por perfil Chromium ocupado; a validacao visual foi executada com Playwright da `.venv` em navegador isolado.

## Pendencias
Nenhuma pendencia funcional identificada.
