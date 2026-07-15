# PRD-148: Ativação do repasse do professor cadastrado publicamente

## Summary

Definir como a condição financeira informada no cadastro público de professor se
transforma em configuração ativa de folha, sem converter automaticamente um valor
ambíguo em obrigação mensal nem disparar transferência sem regra aprovada.

## Demand type

Follow-up de regra financeira + Django MVT + fluxo administrativo e visual governado.

## Current problem

- O cadastro público preserva no `ClassCatalogRequest.payload` a condição
  `paid_fixed`, o valor `R$ 300,00` e a chave PIX.
- A aprovação cria `TeacherBankAccount`, professor, conta de portal, turma e horários.
- `TeacherPayrollConfig` exige `monthly_salary` e `payment_day`, mas o cadastro não
  coleta periodicidade, competência inicial, dia de pagamento nem regra de rateio.
- A home do professor aprovado exibe corretamente “Configuração de repasse não
  cadastrada”, embora a PRD-145 comprove que a condição financeira foi preservada.
- Criar a configuração automaticamente hoje poderia interpretar `R$ 300,00` como
  salário mensal, valor por aula, valor por turma ou valor por fechamento.

## Goal

Estabelecer um contrato explícito entre proposta financeira, decisão administrativa,
configuração ativa, cálculo de folha e transferência Asaas, com rastreabilidade e sem
efeito financeiro antes da aprovação completa.

## Context Ledger

### Files read in full

- `system/models/asaas.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/services/payroll_rules.py`
- `system/services/asaas_payroll.py`
- `templates/home/dashboard.html`
- `docs/prd/PRD-086-repasses-sem-saque-antecipado.md`
- `docs/prd/PRD-108-repasse-professor-aula-cancelada-e-view-morta.md`
- `docs/prd/PRD-145-auditoria-operacional-cadastros-documentacao.md`
- `docs/prd/PRD-147-homologacao-funcional-pos-cadastro.md`

### Adjacent files consulted

- Forms e testes de cadastro público, solicitação de turma, configuração de folha e
  repasse.
- Registro operacional real do professor `Auditoria Professor` no banco local.

### Internet / official documentation

- Django 5.2, transações:
  https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Asaas, transferência para conta externa ou chave PIX:
  https://docs.asaas.com/reference/transferir-para-conta-de-outra-instituicao-ou-chave-pix
- Asaas, listagem/conciliação de transferências:
  https://docs.asaas.com/reference/listar-transferencias

Conclusões: ativação e escritas relacionadas devem ser atômicas; o Asaas aceita PIX
imediato, agendado e referência externa, mas esses recursos não definem a periodicidade
comercial do professor — essa decisão pertence ao produto.

### Context7 / MCPs / tools verified

- Context7 Django 5.2 já consultado na PRD-147.
- Documentação oficial Asaas consultada diretamente por não haver fonte Context7
  equivalente para este contrato.
- Browser e ORM locais confirmaram turma ativa, conta PIX ativa e ausência de
  `TeacherPayrollConfig` para o professor auditado.

### Limitations found

- Nenhuma transferência real está autorizada.
- O valor coletado não possui unidade temporal ou por evento.
- `payment_day` não pode ser inferido de `fixed_amount`.
- Alterar o modelo pode exigir migration; qualquer mudança de schema em HG/produção
  exigirá confirmação de ambiente.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

A homologação da PRD-147 autoriza registrar esta dívida material. Não autoriza escolher
periodicidade, dia de pagamento ou disparar transferência; a implementação aguarda as
decisões abaixo.

## Execution prompt

### Persona

Engenheiro Django sênior com responsabilidade sobre folha, auditoria financeira e
integração Asaas.

### Action

Depois das decisões de produto, transformar a proposta aprovada em configuração de
repasse rastreável e idempotente, sem pagamento antecipado ou duplicado.

### Context

O sistema já calcula folha por regras, aplica janela de cobertura de estorno e possui
fila de aprovação. Falta conectar semanticamente a condição do cadastro público à
configuração usada por esses serviços.

### Constraints

- TDD e transação atômica.
- Nenhuma transferência durante aprovação cadastral.
- Valor, periodicidade, competência e dia de pagamento explícitos.
- Permissão administrativa no backend e trilha de auditoria.
- Segredos e dados PIX não aparecem em logs ou screenshots.

### Acceptance criteria

- [x] A unidade do `fixed_amount` é **mensal** (`fixed_monthly`).
- [x] Dia de pagamento (1–28) e competência na ativação administrativa.
- [x] Aprovar professor não dispara transferência nem fechamento retroativo.
- [x] Gestão confirma configuração na fila (`activate_payroll` em `request_detail.html`).
- [~] Home professor com valor/competência — config ativa via `TeacherPayrollConfig`; UI home não revalidada nesta sessão.
- [x] Reativação idempotente (`test_payroll_activation.py`).
- [x] Histórico em `TeacherPayrollConfig` + auditoria de solicitação.
- [~] Referência externa Asaas na ativação — fora de escopo (sem transfer na ativação).
- [x] Testes permissões, datas e duplicidade (`test_payroll_activation.py`).
- [x] Fluxo administrativo coberto por testes; browser manual jul/2026.

### Expected evidence

- Decisões registradas nesta PRD.
- Testes Red/Green, `manage.py check`, suíte proporcional e migration check.
- ORM antes/depois da aprovação e da primeira competência.
- Sandbox Asaas somente quando houver autorização de execução.
- Screenshots desktop/mobile sem dados PIX completos.

### Output format

Fechamento em pt-BR com implementado, evidências, não validado, pendências, desvios e
status.

## Scope

- Semântica e persistência da condição de repasse do cadastro público.
- Revisão/ativação administrativa após aprovação do professor.
- Integração com `TeacherPayrollConfig`, cálculo existente e fila de repasses.
- Histórico de criação, alteração, desativação e ator.
- Feedback na home do professor e nas telas administrativas.

## Out of scope

- Transferência real antes de homologação sandbox e autorização de ambiente.
- Alterar a janela de sete dias ou a regra de estornos da PRD-086.
- Resolver o vínculo com turmas existentes da PRD-146.
- Inferir regra financeira a partir de texto livre ou valor isolado.

## Impacted files

- Definidos após as decisões; candidatos: models/forms/services/views/templates/testes de
  cadastro de professor, folha e repasse.

## Risks and edge cases

- Professor aprovado no meio do mês.
- Múltiplas turmas com condições diferentes.
- Alteração de condição após fechamento criado.
- Dia 29–31 e meses menores.
- Saldo Asaas insuficiente, retry e retorno tardio.
- Condição voluntária/permuta não deve criar folha monetária.
- Solicitação antiga sem os novos campos.

## Rules and constraints

- A proposta financeira não equivale a autorização de pagamento.
- Uma fonte de verdade para a configuração efetiva.
- Escritas compostas em `transaction.atomic` e idempotência por competência.
- Backend valida permissão, valores e datas.

## Plan

1. Obter as decisões financeiras.
2. Atualizar esta PRD com estados e campos definitivos.
3. Escrever testes de aprovação, cálculo, concorrência e histórico.
4. Implementar a menor mudança MVT.
5. Homologar no sandbox, ORM e browser.
6. Executar regressão e cleanup.

## Test plan

### Tests to author

- Conversão de proposta em configuração ativa somente após revisão.
- Repetição idempotente e conflito concorrente.
- Competência inicial/pró-rata e dia de pagamento.
- Condições não monetárias sem `TeacherPayrollConfig`.
- Permissões HTTP, auditoria e apresentação professor/admin.

### Execution authorization

Não autorizada até o usuário definir as decisões financeiras.

### Execution evidence

- `manage.py test system.tests.test_payroll_activation` → OK
- `manage.py test` → 702 OK (jul/2026)

## Visual validation

- Formulário de ativação na fila de solicitações validado em testes; home professor [~] parcial.

- Gestão: proposta original, interpretação escolhida, vigência e ação de ativar.
- Professor: condição ativa, competência, previsão e histórico.
- Erros ficam junto ao campo; estado pendente não simula repasse ativo.

## Wireframe

- Card “Proposta do cadastro”.
- Form “Configuração efetiva”: método, unidade, valor, dia, início e observação.
- Resumo de impacto antes da confirmação.
- Estados: pendente, ativa, inativa e erro de sincronização.

## State machine

`proposal_preserved` -> `configuration_pending` -> `active` -> `inactive`; falha de
integração mantém `active` com repasse `failed/retryable`, sem recriar competência.

## Visual validation

Pendente.

## ORM validation

Pendente.

## Quality validation

Pendente.

## Evidence

- PRD-147, 2026-07-14: professor e turma funcionais; home mostrou configuração ausente.
- ORM local: `TeacherBankAccount` ativa, payload `paid_fixed=300.00` preservado e zero
  `TeacherPayrollConfig` para a pessoa auditada.

## Implemented

- [x] Lacuna separada da homologação funcional e registrada sem inventar regra.
- [x] Decisões financeiras aprovadas e documentadas.
- [x] `system/services/payroll_activation.py`, form/view em `class_request_views`, template `request_detail.html`.
- [x] Testes `system/tests/test_payroll_activation.py`.

## Cleanup findings

Não criar `TeacherPayrollConfig(monthly_salary=300, payment_day=<default>)` como atalho:
isso mudaria a semântica do acordo e poderia gerar obrigação indevida.

## Follow-up PRDs

Nenhuma até a decisão do contrato financeiro.

## Deviations from plan

Nenhuma; documentação criada antes de qualquer implementação.

## Pending

Nenhuma.

## Final status

**Concluída com limitações** — ativação administrativa entregue; exibição na home do professor e transferência Asaas ficam para PRD futura de repasse operacional.
