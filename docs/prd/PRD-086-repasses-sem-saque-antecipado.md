# PRD-086: Repasses sem saque antecipado

## Resumo do que será implementado
Remover completamente a funcionalidade de saque antecipado e ajustar o fechamento para liberar repasses somente após a janela de 7 dias de cobertura de estorno, com abatimento proporcional de estornos em repasses futuros.

## Tipo de demanda
Correcao pontual + regra financeira.

## Problema atual
A tela individual exibe "Solicitar saque antecipado" e o backend permite `request_withdrawal()`. Esse fluxo nao faz parte do produto desejado. O repasse correto deve nascer do dinheiro que entrou e foi vinculado ao professor/administrativo, respeitando uma janela de 7 dias antes de liberar o saldo. Se houver estorno total ou parcial depois que o valor ja foi considerado em fechamento anterior, o valor proporcional deve ser descontado dos proximos repasses.

## Objetivo
Eliminar saque antecipado da UI, forms, views, services e testes; manter somente repasses por fechamento automatico. O calculo deve:
- considerar entradas pagas apenas quando a data de pagamento ja passou pela janela configurada de 7 dias;
- registrar e aplicar abatimentos proporcionais por estorno;
- exibir ao professor/administrativo historico, previsao e comprovacao das entradas vinculadas.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `docs/prd/PRD-012-modulo-financeiro-repasses.md`
- `lvjiujitsu/settings.py`
- `system/models/asaas.py`
- `system/models/registration_order.py`
- `system/forms/payroll_forms.py`
- `system/forms/__init__.py`
- `system/services/asaas_payroll.py`
- `system/services/payroll_rules.py`
- `system/services/financial_transactions.py`
- `system/services/stripe_admin_actions.py`
- `system/services/asaas_webhooks.py`
- `system/services/stripe_webhooks.py`
- `system/services/membership.py`
- `system/views/asaas_views.py`
- `templates/home/instructor/financial.html`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`

### Arquivos adjacentes consultados
- `system/views/billing_admin_views.py`
- `system/tests/test_views.py`
- `templates/billing/payout_queue.html`
- `templates/billing/payroll_list.html`

### Internet / documentacao oficial
- Procon-SP, Codigo de Protecao e Defesa do Consumidor 2025, Lei 8.078/1990, art. 49 — prazo de sete dias para direito de arrependimento em contratacao fora do estabelecimento.

### MCPs / ferramentas verificadas
- PowerShell + `.venv` — OK.
- Web/documentacao oficial — OK.
- Browser Use `iab` + Playwright — OK.

### Limitacoes encontradas
- Sem nova migracao por politica do projeto. O valor de estorno proporcional sera registrado em `RegistrationOrder.notes` com marcador JSON versionado.
- O schema atual nao tem tabela propria de ledger de abatimentos. A solucao preserva auditoria textual estruturada sem alterar banco.

## Prompt de execucao
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + MVT com services.

### Acao
Remover saque antecipado e implementar repasse elegivel apos 7 dias com abatimentos de estorno.

### Contexto
O calculo de repasses fica em `system/services/payroll_rules.py`. A criacao/disparo de pagamentos fica em `system/services/asaas_payroll.py`. A tela individual usa `TeacherFinancialView` e `templates/home/instructor/financial.html`.

### Restricoes
- sem nova migracao
- sem saque antecipado em UI ou backend
- sem mascarar estornos
- janela de 7 dias configuravel por setting
- texto final em pt-BR

### Criterios de aceite
- [x] A tela "Meu financeiro" nao deve exibir "Solicitar saque antecipado".
- [x] POST em `/me/financeiro/` nao deve criar `TeacherPayout`.
- [x] `request_withdrawal` e `WithdrawalRequestForm` devem ser removidos.
- [x] Entrada paga ha menos de 7 dias nao entra no saldo por aluno/percentual.
- [x] Entrada paga apos 7 dias entra no saldo e exibe data de liberacao ao repasse.
- [x] Estorno total de entrada ja creditada gera abatimento proporcional no proximo fechamento.
- [x] Estorno parcial gera abatimento parcial proporcional.
- [x] O fechamento nunca gera valor negativo; abatimento excedente fica evidenciado no resumo do mes.
- [x] Testes automatizados cobrem remocao do saque, janela de 7 dias e abatimento de estorno.

### Evidencias esperadas
- testes focados passando
- suite completa passando
- `manage.py check`
- `collectstatic --noinput` se template/CSS for alterado
- validacao visual da tela individual sem saque antecipado

### Formato de saida
Codigo implementado + testes + evidencias de validacao.

## Escopo
- Remocao do formulario e fluxo de saque.
- Calculo de elegibilidade por janela de 7 dias.
- Registro/parsing de estorno em `RegistrationOrder.notes`.
- Abatimento proporcional em fechamento futuro.
- Atualizacao de tela individual.

## Fora do escopo
- Nova tabela de ledger financeiro.
- Consulta juridica automatizada.
- Transferencia bancaria real em ambiente de producao.

## Arquivos impactados
- `lvjiujitsu/settings.py`
- `system/models/asaas.py`
- `system/forms/__init__.py`
- `system/forms/payroll_forms.py`
- `system/services/asaas_payroll.py`
- `system/services/payroll_rules.py`
- `system/services/stripe_admin_actions.py`
- `system/services/membership.py`
- `system/views/asaas_views.py`
- `templates/home/instructor/financial.html`
- `system/tests/test_asaas.py`
- `system/tests/test_services.py`
- `system/tests/test_views.py`

## Riscos e edge cases
- Estorno no mesmo mes antes do pagamento ao professor nao deve gerar abatimento duplicado.
- Estorno parcial precisa ser proporcional ao percentual/regra que creditou o professor.
- Estorno maior que o repasse do mes nao pode criar pagamento negativo.
- Registros antigos sem marcador estruturado devem assumir estorno total somente quando `payment_status=REFUNDED`.

## Regras e restricoes
- SDD antes de codigo
- TDD para implementacao
- sem hardcode fora de setting/default
- sem nova migracao
- validacao obrigatoria

## Plano
- [x] 1. Criar testes Red
- [x] 2. Remover saque antecipado
- [x] 3. Implementar janela de 7 dias
- [x] 4. Implementar registro e abatimento de estorno
- [x] 5. Atualizar UI individual
- [x] 6. Validar
- [x] 7. Atualizar evidencias

## Validacao visual
- Browser Use `iab`: `http://localhost:8000/me/financeiro/` renderizou `Meu financeiro`, sem `Solicitar saque antecipado`, com `Retido em cobertura`, `Abatimentos por estorno` e `Disponivel para repasse`; console sem erros.
- Playwright desktop 1366x900: sem `Solicitar saque antecipado`, com retencao/estornos/disponivel, sem overflow horizontal, console sem erros.
- Playwright mobile 390x844: sem `Solicitar saque antecipado`, com retencao/estornos/disponivel, sem overflow horizontal, console sem erros.

## Validacao ORM
- Shell ORM: Layon Quirino calculado com `total=400.00`, `gross_total=400.00`, `held_total=0.00`, `refund_adjustment_total=0.00`.
- Shell ORM: `hasattr(system.services.asaas_payroll, "request_withdrawal") == False`.

## Validacao de qualidade
- `manage.py test --verbosity 2`: 335 testes OK.
- `manage.py check`: sem problemas.
- `manage.py showmigrations`: apenas `system.0001_initial` aplicado; nenhuma migracao nova criada.
- `collectstatic --noinput`: nao executado porque nao houve alteracao em arquivo estatico fonte.

## Evidencias
- Focados: `manage.py test system.tests.test_services.PayrollRulesServiceTestCase system.tests.test_asaas system.tests.test_views.PortalViewTestCase.test_administrative_portal_account_can_open_own_financial_screen system.tests.test_views.PortalViewTestCase.test_staff_financial_screen_rejects_withdrawal_post --verbosity 2` — 27 testes OK.
- Suite completa: `manage.py test --verbosity 2` — 335 testes OK.
- Check: `manage.py check` — `System check identified no issues (0 silenced).`
- Migrations: `manage.py showmigrations` — `system [X] 0001_initial`.
- Visual desktop/mobile: Playwright confirmou ausencia do saque, presenca dos KPIs novos, sem overflow horizontal e sem erros de console.

## Implementado
- Removido `WithdrawalRequestForm`, `request_withdrawal`, POST de saque e item `WITHDRAWAL` do enum runtime.
- `TeacherFinancialView` passou a ser somente leitura; POST em `/me/financeiro/` retorna 405.
- `PAYROLL_REFUND_HOLD_DAYS` configuravel adicionado em settings com default 7.
- Calculo mensal passou a separar `gross_total`, `held_total`, `refund_adjustment_total`, `carryover_adjustment`, `entries`, `held_entries` e `refund_entries`.
- Estornos Stripe admin, Stripe webhook e Asaas webhook registram marcador JSON em `RegistrationOrder.notes`.
- Fechamento automatico registra absorcao de abatimentos e cria fechamento zerado quando o repasse do mes e totalmente abatido, preservando idempotencia por `TeacherPayout` mensal.
- Tela "Meu financeiro" passou a exibir retencao, abatimentos, saldo disponivel para repasse, entradas liberadas, entradas em cobertura e abatimentos por estorno.

## Desvios do plano
- Nenhuma migracao criada; por restricao do projeto, o ledger de estornos e absorcoes foi persistido em `RegistrationOrder.notes` com marcador JSON versionado.

## Pendencias
- Nenhuma pendencia bloqueante.
- Futuro recomendado: criar tabela propria de ledger financeiro quando migracoes forem liberadas, substituindo o marcador estruturado em `notes`.
