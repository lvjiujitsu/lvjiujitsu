# PRD-048: Financeiro no Dashboard — Repasse do Professor e Mensalidade do Aluno

## Resumo do que será implementado

Duas melhorias na tela `/home/` (dashboard unificado):

1. **Seção de Repasse (Professor/Instrutor)**: exibir no dashboard do professor os dados de repasse do mês atual — saldo disponível, detalhamento por método, dados bancários cadastrados e histórico dos últimos pagamentos recebidos.
2. **Seção de Mensalidade (Aluno) aprimorada**: complementar o card de mensalidade existente com o valor do plano, período de vigência (início/fim), histórico de faturas pagas e link stub para upgrade/downgrade de plano.

## Tipo de demanda

Adição de feature de leitura (sem escrita) com exibição de dados já existentes no backend.

## Problema atual

- **Professor**: não vê nenhuma informação de repasse na home. A `TeacherFinancialView` já tem toda a lógica implementada, mas sem URL registrada, sem template e sem vínculo com o dashboard.
- **Aluno**: a seção "Mensalidade" existe mas exibe apenas status + vencimento. O valor do plano, período de vigência e histórico de faturas (`recent_invoices`) estão no contexto mas não renderizados.

## Objetivo

Dar visibilidade financeira a cada perfil diretamente na home, sem navegação extra.

## Context Ledger

### Arquivos lidos integralmente

- `templates/home/dashboard.html`
- `system/views/home_views.py`
- `system/views/asaas_views.py` (TeacherFinancialView, StaffFinancialRequiredMixin)
- `system/services/payroll_rules.py` (calculate_monthly_payroll, get_staff_financial_context)
- `system/services/asaas_payroll.py` (compute_available_balance)
- `system/urls.py`
- `static/system/css/home/dashboard.css`

### Arquivos adjacentes consultados

- `system/models/asaas.py` (TeacherPayout, TeacherPayrollConfig, TeacherBankAccount, PayoutStatus)
- `system/models/membership.py` (Membership, MembershipInvoice)
- `system/models/plan.py` (SubscriptionPlan)

### Limitações encontradas

- `TeacherFinancialView` tem mixin `StaffFinancialRequiredMixin` que exige role instructor ou administrative — não será usada diretamente; os dados serão carregados no `HomeView`
- Upgrade/downgrade de plano é funcionalidade futura (stub visual apenas)

## Prompt de execução

### Persona

Agente de desenvolvimento Django seguindo SDD + protocolo AGENTS.md/CLAUDE.md.

### Ação

Adicionar contexto de repasse ao `HomeView` para instrutores e renderizar as duas seções novas no `dashboard.html`.

### Contexto

O dashboard já separa contexto por perfil (`is_instructor`, `is_student`). O `calculate_monthly_payroll` e `compute_available_balance` já existem e podem ser chamados diretamente. Os dados de `billing_tabs` para o aluno já chegam ao template mas faltam campos renderizados.

### Restrições

- Sem nova rota, sem novo template separado — tudo na home existente
- Sem lógica de escrita — apenas leitura
- Sem migrações
- Leitura integral obrigatória antes de editar
- Validação visual obrigatória

### Critérios de aceite

- [ ] Instrutor logado vê seção "Repasse" na home com: valor a receber no mês, detalhamento por método, próximo pagamento, histórico de repasses (verificável: visual)
- [ ] Instrutor sem config de repasse vê seção com estado vazio adequado (verificável: visual)
- [ ] Instrutor com dados bancários cadastrados vê chave PIX e tipo (verificável: visual)
- [ ] Aluno logado vê na seção "Mensalidade": nome do plano, valor, ciclo, período início/fim (verificável: visual)
- [ ] Aluno com faturas pagas vê lista de faturas recentes com data e valor (verificável: visual)
- [ ] Aluno em atraso vê botão "Pagar agora" (já existente — confirmar funcionamento)
- [ ] Botão "Trocar plano" aparece desabilitado como stub (verificável: visual)
- [ ] `manage.py test --verbosity 2` passa sem falhas (verificável: terminal)
- [ ] `manage.py check` passa (verificável: terminal)
- [ ] Console do navegador sem erros JS críticos (verificável: DevTools)

### Evidências esperadas

- Screenshot da seção de repasse do professor
- Screenshot da seção de mensalidade do aluno com faturas
- Terminal com testes passando

## Escopo

1. `system/views/home_views.py` — adicionar imports e bloco de contexto instructor
2. `templates/home/dashboard.html` — adicionar seção Repasse (instructor) e estender seção Mensalidade (aluno)
3. `static/system/css/home/dashboard.css` — adicionar tokens visuais das novas seções
4. Atualizar `?v=` em template e CSS

## Fora do escopo

- Implementação real de upgrade/downgrade de plano
- Tela dedicada de financeiro do professor
- Histórico de faturas com paginação
- Edição de dados bancários

## Arquivos impactados

| Arquivo | Mudança |
|---|---|
| `system/views/home_views.py` | novo bloco `if is_instructor` com dados de repasse |
| `templates/home/dashboard.html` | nova seção `#section-repasse` (instructor) + campos extras em `#section-billing` |
| `static/system/css/home/dashboard.css` | tokens e classes para os novos componentes |

## Riscos e edge cases

- Professor sem `TeacherPayrollConfig`: `calculate_monthly_payroll` retorna `_empty_calculation` — tratar no template
- Professor sem `TeacherBankAccount`: tratar ausência com estado vazio
- Aluno com `billing_tabs` de dependentes: os campos extras devem aparecer em cada aba
- `recent_invoices` pode estar vazia mesmo com membership ativa — exibir estado vazio

## Regras e restrições

- SDD antes de código
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação visual obrigatória

## Plano

- [x] 1. Leitura integral dos arquivos do fluxo
- [ ] 2. Adicionar contexto instructor no HomeView
- [ ] 3. Atualizar template: seção Repasse (instructor)
- [ ] 4. Atualizar template: seção Mensalidade (aluno) estendida
- [ ] 5. Atualizar CSS com novos componentes
- [ ] 6. Executar testes e check
- [ ] 7. Validação visual
- [ ] 8. Limpeza e atualização de versão dos assets

## Hierarquia Visual

- Padrão de leitura: F Pattern (tela de informação operacional)
- Título de seção: peso 600, token `--text`
- Rótulos de valores: peso 500, token `--text`
- Valores monetários: peso 700, token `--text`, destaque com `--brand-red` para valor total
- Help text/datas: peso 400, token `--muted`
- Ação primária (Pagar): `--brand-red`, peso 600
- Ação desabilitada (Trocar plano): borda `--border`, peso 500, `opacity 0.45`

## Wireframe

### Seção: Repasse (instrutor)

```
[▼] Repasse                          [mês referência]
┌────────────────────────────────────────────────────┐
│  [card saldo]                                      │
│   Valor a receber    R$ XXX,XX                     │
│   Pagamento previsto dd/mm                         │
├────────────────────────────────────────────────────┤
│  [detalhamento]                                    │
│   Fixo mensal        R$ XXX,XX                     │
│   Por aluno          R$ XXX,XX  (N alunos)         │
│   Ajustes/devoluções R$ -XX,XX                     │
│   ─────────────────────────────                    │
│   Total              R$ XXX,XX                     │
├────────────────────────────────────────────────────┤
│  [dados bancários]                                 │
│   Chave PIX          CPF / xxx.xxx.xxx-xx          │
├────────────────────────────────────────────────────┤
│  [histórico de repasses]                           │
│   dd/mm/aaaa   R$ XXX,XX   ● Pago                 │
│   dd/mm/aaaa   R$ XXX,XX   ● Aprovado             │
└────────────────────────────────────────────────────┘
```

### Seção: Mensalidade (aluno) — estendida

```
[▼] Mensalidade
┌────────────────────────────────────────────────────┐
│  [badge status]  Nome do plano                     │
│  Valor: R$ XX,XX / mensal                          │
│  Vigência: 01/05/2026 → 01/06/2026                 │
│  [btn Pagar agora] (se em atraso)                  │
│  [btn Trocar plano] (desabilitado — stub)          │
├────────────────────────────────────────────────────┤
│  Faturas recentes                                  │
│   dd/mm/aaaa   R$ XX,XX   ● Pago                  │
│   dd/mm/aaaa   R$ XX,XX   ● Pago                  │
└────────────────────────────────────────────────────┘
```

## Máquinas de estado

### Seção Repasse — card de saldo

- `no_config`: sem configuração cadastrada → empty-state "Configuração de repasse não cadastrada"
- `config_inactive`: config existe mas inativa → badge "Inativo"
- `active_zero`: config ativa, total = 0 → "R$ 0,00 — sem alunos vinculados no mês"
- `active_positive`: config ativa, total > 0 → valor destacado + data prevista

### Seção Mensalidade — card

- `no_plan`: sem membership → "Nenhum plano ativo"
- `pending`: pedido pendente → botão "Ir para pagamento"
- `active`: ativo → plano, valor, vigência
- `past_due`: em atraso → badge vermelho + botão "Pagar agora"
- `exempted`: isento → badge verde + sem valor monetário

## Validação visual

### Desktop

- [x] Seção repasse visível para professor logado — estado vazio correto quando sem config
- [x] Seção mensalidade com valor (R$ 228,80) e vigência (24/05/2026 → 24/06/2026) para aluno logado

### Mobile

- [ ] Não validado em viewport reduzido (ambiente de preview sem resize)

### Console do navegador

- [x] Sem erros JS críticos

### Terminal

- [x] `manage.py test --verbosity 2` — 171 testes, 0 falhas
- [x] `manage.py check` — 0 issues

## Evidências

- Professor (André): seção "Repasse" renderizada com empty-state correto (sem config de repasse cadastrada)
- Aluno (Wagner): seção "Mensalidade" com badge Ativo, plano, valor R$ 228,80/mensal, vigência 24/05–24/06/2026, botão "Trocar plano" desabilitado
- Console: sem erros JS
- 171 testes passando

## Implementado

- `system/views/home_views.py`: importes + função `_build_instructor_payroll_context` + bloco `if is_instructor` no `get_context_data` + contexto default no `_empty_context`
- `templates/home/dashboard.html`: nova seção "Repasse" para instructor + campos extras (valor, vigência, faturas) na seção "Mensalidade" + `?v=13`
- `static/system/css/home/dashboard.css`: classes `.payroll-*` e `.billing-meta`, `.billing-invoices`, `.billing-invoice-*`

## Desvios do plano

- Nenhum

## Pendências

- Implementação real de upgrade/downgrade de plano (fora de escopo)
- Validação mobile não realizada (ambiente sem resize no preview)
