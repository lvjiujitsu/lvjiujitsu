# PRD-147: Homologação funcional pós-cadastro

## Summary

Homologar, com dados locais e integrações sandbox, os fluxos posteriores aos cadastros
criados na PRD-145: aula/check-in, operação do professor, pausa e retomada temporal,
troca de plano e cartão, ciclo completo de dependente e histórico das mudanças. A
validação combina interface real, ORM, simulação controlada de datas, testes Django e
renderização desktop/mobile.

## Demand type

Homologação funcional ponta a ponta + auditoria de regressão + correção condicionada a
falha comprovada.

## Current problem

- Os nove usuários da PRD-145 foram cadastrados e autenticados, mas os fluxos de uso
  posterior ainda não foram reexecutados com essas contas.
- As PRDs 131 a 134 declaram aula, pausa, plano, cartão e timeline concluídos, porém as
  evidências são de rodadas anteriores e não comprovam o estado atual do worktree e do
  banco local.
- A PRD-121 permanece formalmente com status `Não concluída`, apesar de PRDs posteriores
  cobrirem parte de seu escopo.
- A PRD-118 deixou limitações explícitas de idempotência e materiais; a remoção e o
  histórico familiar precisam ser exercitados no fluxo atual.
- Não existe uma evidência única que relacione ação visual, transição persistida e evento
  de timeline para todos os cenários solicitados.

## Goal

Comprovar que as contas criadas conseguem usar os fluxos solicitados sem regressão e,
quando uma falha dentro do escopo for reproduzida, corrigi-la com TDD, revalidar o caminho
afetado e registrar a evidência real.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-116-home-aluno-permissoes-cronograma-fidelidade.md`
- `docs/prd/PRD-118-adicionar-dependente-pos-matricula.md`
- `docs/prd/PRD-121-home-cliente-dependentes-mensalidades-crud.md`
- `docs/prd/PRD-123-modal-conta-cliente-editar-excluir.md`
- `docs/prd/PRD-130-migrar-troca-plano-catalogo-plantier-planprice.md`
- `docs/prd/PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md`
- `docs/prd/PRD-132-transicao-livre-planos-pausa-mensalidade.md`
- `docs/prd/PRD-133-indicador-pagamento-trocar-cartao-stripe.md`
- `docs/prd/PRD-134-historico-eventos-assinatura-familia-cliente-admin.md`
- `docs/prd/PRD-145-auditoria-operacional-cadastros-documentacao.md`
- `docs/prd/PRD-146-professor-publico-vinculo-turmas-existentes.md`

### Adjacent files consulted

- `system/urls.py`
- models, forms, services, selectors, views, templates, assets e testes dos fluxos de
  calendário, mensalidade, pausa, plano, cartão, dependente e timeline, conforme
  detalhados durante a execução.

### Internet / official documentation

- Django 5.2 testing: https://docs.djangoproject.com/en/5.2/topics/testing/overview/
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Stripe Customer Portal: https://docs.stripe.com/customer-management
- Stripe update payment details: https://docs.stripe.com/payments/checkout/subscriptions/update-payment-details
- Stripe subscription plan changes: https://docs.stripe.com/billing/subscriptions/change-price

Conclusões: testes de banco devem permanecer isolados; múltiplas escritas de domínio
devem ser atômicas; o Billing Portal é o caminho oficial para atualização do método de
pagamento; trocar preço exige substituir o item atual da assinatura e pode gerar
proração.

### Context7 / MCPs / tools verified

- Context7: `/websites/djangoproject_en_5_2` e `/websites/stripe`.
- Browser interno disponível em `http://127.0.0.1:8000`.
- Stripe test-mode, listener local e túnel informados como ativos pelo usuário.
- PowerShell, `rg`, Python/Django e ORM local disponíveis.

### Limitations found

- Nenhuma escrita em HG ou produção está autorizada; gateway é somente sandbox/test-mode.
- Simulação temporal deve usar data controlada em teste/ORM, sem alterar o relógio do
  sistema operacional.
- O Billing Portal é hospedado pelo Stripe e não pode ser validado em iframe; a entrada,
  o redirect e a confirmação via API/webhook são as evidências adequadas.
- A PRD-146 permanece fora deste escopo por depender de decisões de produto sobre vínculo
  de professor a turmas existentes.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `browser:control-in-app-browser`
- `lv-cleanup-audit`

## Understanding approved

A solicitação atual autoriza executar os testes locais/sandbox até a conclusão, operar as
contas criadas, simular datas de forma controlada e corrigir falhas comprovadas dentro
dos fluxos listados. Mudança de produto, HG/produção ou ampliação para a decisão pendente
da PRD-146 não está autorizada.

## Execution prompt

### Persona

Agente Django/MVT sênior responsável por homologação funcional e regressão do LV JIU
JITSU.

### Action

Executar a matriz ponta a ponta, correlacionar cada ação visual com persistência e
timeline, corrigir somente defeitos reproduzidos no escopo e entregar evidências
desktop/mobile.

### Context

As contas, mensalidades e a turma `Jiu Jitsu Auditoria` já existem no banco local. O
professor `Auditoria Professor` possui horários terça e quinta às 20:30.

### Constraints

- Usar interface real para as ações disponíveis ao usuário.
- Usar ORM/teste controlado somente para inspeção, preparação proporcional e simulação
  temporal impossível de realizar em tempo real.
- Preservar histórico e evitar deleção física de pessoa.
- Não expor segredo, chave ou token nas evidências.
- TDD antes de qualquer correção de comportamento.
- Não editar `staticfiles/`.

### Acceptance criteria

- [x] Aluno faz check-in na aula do professor criado e o professor aprova a presença.
- [x] Professor confirma presença, indica/altera professor substituto e a transição fica
  persistida e visível.
- [x] Professor cancela e restaura a aula sem deixar o check-in travado indevidamente.
- [x] Pausa é solicitada, aprovada e bloqueia check-in durante a janela.
- [x] Simulação temporal comprova retomada/destrancamento depois do término e cota por
  aniversário da matrícula.
- [x] Troca de plano é executada e a mensalidade reflete o plano resultante sem assinatura
  duplicada.
- [x] Troca de cartão Stripe entra pelo Billing Portal e a alteração é confirmada no
  ambiente test-mode sem apagar a vigência.
- [x] Dependente é adicionado, tem o plano alterado e depois é removido sem deleção física.
- [x] Timeline do cliente e auditoria administrativa registram adição, plano e remoção sem
  vazamento de dado técnico para o cliente.
- [x] Funcionalidades adjacentes esquecidas são inventariadas e classificadas como
  funcionais, defeito reproduzido ou dívida documentada.
- [x] Caminhos principais e estados de erro renderizam em desktop e mobile, temas claro e
  escuro, sem overflow nem erro crítico no console.
- [x] Testes focados, `manage.py check` e suíte proporcional passam no estado final.

### Expected evidence

- Antes/depois em ORM para sessões, check-ins, pausa, membership, dependente e timeline.
- IDs de sandbox apenas quando necessários para rastreabilidade, sem segredos.
- Screenshots desktop/mobile dos principais estados.
- Comandos e resultados reais de testes/check.

### Output format

Fechamento pt-BR: implementado/corrigido, evidências reais, não validado com motivo,
pendências/desvios e status final.

## Scope

- Check-in de aluno e aprovação do professor.
- Presença, substituição, cancelamento e restauração da aula.
- Pausa médica/trancamento, aprovação e retomada temporal.
- Troca de plano entre opções elegíveis e troca de cartão Stripe.
- Adição, troca de plano e remoção de dependente.
- Timeline do cliente e auditoria administrativa.
- Correções estritamente necessárias para defeitos reproduzidos nesses caminhos.
- Atualização desta PRD, índice e documentação diretamente afetada por achados reais.

## Out of scope

- Deploy, HG/produção ou cobrança real.
- Decisão/implementação do modo `existing` da PRD-146.
- Redesign geral da home ou quitação integral da crítica frontend/backend das PRDs
  138 a 144.
- Deleção física de pessoa dependente.
- Mudança de regra comercial ou preço sem contrato já existente.

## Impacted files

- `docs/prd/PRD-147-homologacao-funcional-pos-cadastro.md`
- `docs/prd/README.md`
- Evidências em `docs/prd/evidence/`.
- Arquivos de código/teste/documentação somente se uma falha for comprovada e corrigida;
  serão registrados na seção `Implemented`.

## Risks and edge cases

- Sessão de aula lazy ainda inexistente no dia.
- Professor substituto pendente versus confirmado.
- Aula cancelada durante check-in pendente.
- Pausas sobrepostas, período retroativo e limite de 30 dias.
- Plano Stripe em carência e troca para outro gateway.
- Checkout abandonado não pode alterar a membership ativa.
- Evento real `customer.subscription.updated` não pode zerar vigência.
- Dependente removido deve permanecer como pessoa histórica e desaparecer apenas do grupo
  familiar ativo.
- Timeline deve manter isolamento entre famílias.

## Rules and constraints

- Backend é a autoridade de permissão e transição.
- Escritas compostas usam `transaction.atomic`.
- Datas simuladas usam mock/fixtures controladas e timezone aware.
- Ações destrutivas usam POST/CSRF e confirmação visual.
- Screenshots não devem exibir segredo.

## Plan

1. Baseline de banco, rotas, contratos e testes focados.
2. Aula: check-in, aprovação, confirmação/substituição, cancelamento/restauração.
3. Pausa: solicitação, aprovação, bloqueio e retomada temporal.
4. Financeiro: troca de plano e cartão.
5. Família: adicionar, alterar plano, remover e auditar timeline.
6. Inventário adjacente, correções comprovadas e regressão.
7. Validação desktop/mobile/temas/console e limpeza final.

## Test plan

### Tests to author

- Somente quando uma falha não coberta for reproduzida: escrever o menor teste de
  regressão antes do fix.
- Reexecutar os testes existentes de calendário, pausa, plano, cartão, dependente e
  timeline como baseline.
- Simular datas de pausa com `mock.patch`/data de referência, sem esperar o calendário
  real.

### Execution authorization

Testes, ORM e gateways sandbox autorizados pela solicitação atual. HG/produção não.

### Execution evidence

- `system.tests.test_calendar`: 107 testes, `OK`, 48,193 s.
- `system.tests.test_dependent_registration`: 31 testes, `OK`, 24,672 s na repetição
  pós-cleanup.
- `system.tests.test_membership_pause`, `test_membership_card_update` e
  `test_membership_timeline`: 61 testes, `OK`, 20,493 s.
- `system.tests.test_dependent_cancellation_lock`, `test_home_dependents_section` e
  `test_home_dashboard`: 27 testes, `OK`, 24,414 s.
- quatro módulos de troca de plano: 40 testes, `OK`, 6,492 s.
- `manage.py check`: nenhum problema.
- `makemigrations --check --dry-run`: nenhuma mudança detectada.
- `compileall` e `node --check` dos dois JavaScripts alterados: sem erro.
- Suíte integral `system`: 689 testes, `OK`, 304,461 s; banco de teste criado e destruído
  isoladamente.

## Visual hierarchy

- Home do aluno/responsável: aula do dia, mensalidade, dependentes e histórico.
- Home do professor: aula do dia, presença, substituição, cancelamento e check-ins.
- Administração: filas de pausa e histórico técnico.
- Ações primárias permanecem próximas ao estado que alteram; mensagens explicam o estado
  seguinte.

## Wireframe

### Aula

- Cabeçalho da turma e horário.
- Estado da aula/professor.
- Ações permitidas: check-in, confirmar/cancelar presença, indicar substituto,
  cancelar/restaurar aula.
- Lista de check-ins pendentes/aprovados.

### Mensalidade

- Plano e gateway atuais.
- Vigência/pausa.
- Ações: trocar plano, pausar, trocar cartão quando aplicável.
- Histórico de alterações.

### Dependente

- Card com vínculo, plano, graduação e ações.
- Modal de adição/edição.
- Confirmação de remoção.

## State machine

- Aula: `scheduled` -> `teacher_absent` ou `substitute_pending` -> `confirmed`; `scheduled`
  -> `canceled` -> `scheduled`.
- Check-in: `absent` -> `pending` -> `approved`; cancelável apenas enquanto pendente.
- Pausa: `pending` -> `approved` ou `rejected`; `approved_in_window` ->
  `ended_unlocked` pela data.
- Plano: `current` -> `order_pending` -> `paid/applied` ou `abandoned`.
- Dependente: `not_linked` -> `linked` -> `plan_changed` -> `unlinked`, preservando pessoa
  e eventos históricos.

## Visual validation

- Navegador real: home do professor, check-in aprovado, presença confirmada, substituto,
  cancelamento/restauração, plano do dependente e timelines do cliente/admin.
- Desktop: 1440x900/1425x891; mobile: 375x812; temas claro e escuro.
- Timeline administrativa mobile corrigida para empilhar o card e quebrar nome/descrição,
  sem elipse irrecuperável nem overflow horizontal.
- Medição DOM em 390 px confirmou `flex-direction: column`, `white-space: normal`,
  `text-overflow: clip` e ausência de overflow horizontal.
- Console do navegador interno: zero erros e zero warnings da aplicação. O Chrome exibiu
  ruído de uma extensão Méliuz; a sobreposição foi fechada e a captura contaminada foi
  removida das evidências.
- Evidências: `prd-147-instructor-class-desktop.png`,
  `prd-147-instructor-class-mobile-dark.png`, `prd-147-admin-timeline-desktop.png`,
  `prd-147-admin-timeline-mobile-light.png`, `prd-147-admin-timeline-mobile-dark.png` e
  `prd-147-dependent-plan-mobile-dark.png`.

## ORM validation

- Aula `ClassSession.id=1`: `scheduled`, professor presente, sem substituto residual;
  check-in do aluno `Person.id=8` aprovado por `Person.id=16`.
- Pausa da `Membership.id=1`: 14/07/2026 a 16/07/2026, aprovada; período prorrogado em
  três dias. Testes temporais confirmaram bloqueio durante a janela, liberação no primeiro
  dia posterior e reinício da cota no aniversário.
- Aluno Asaas: troca para `PlanPrice.id=12`/Adulto 5x, ordem 5 paga, R$ 36,47.
- Aluno Stripe: exatamente um evento `card_updated`; método padrão remoto mudou para o
  Mastercard de teste final 4444, sem encerrar a membership.
- Dependente de ciclo `Person.id=17`: adicionado com `Membership.id=5`, trocado de Adulto
  2x Stripe para Adulto 5x Asaas, assinatura Stripe anterior cancelada, ordem 7 paga em
  sandbox e vínculo familiar removido. A pessoa e a membership permanecem ativas.
- Timeline do dependente preservou, em ordem, `dependent_added`, `payment_confirmed`,
  `membership_canceled`, `plan_changed` e `dependent_removed`.

## Quality validation

- Correções escritas com teste de regressão antes do código.
- Autorização de check-in validada no backend e resposta HTTP 403 para turma alheia.
- Atualização de cartão só registra histórico depois de confirmar mudança real na Stripe;
  abrir o portal ou retornar sem alteração não produz evento falso.
- Erro de checkout Asaas do dependente volta ao formulário; retry da mesma sessão reutiliza
  o pré-cadastro, enquanto outra sessão não captura o registro pendente.
- `git diff --check` sem erro; varredura do diff sem segredo real, `except: pass`, TODO,
  `innerHTML` novo ou log de depuração.
- Nenhuma migration, edição em `staticfiles/`, escrita HG/produção ou cobrança real.

## Evidence

- Interface real e ORM correlacionados para cada transição solicitada.
- Stripe em test-mode: Billing Portal real, cartão de teste Mastercard e cancelamento da
  assinatura anterior do dependente confirmados remotamente.
- Asaas sandbox: pagamentos 5 e 7 confirmados pelo endpoint oficial e webhooks assinados
  recebidos pelo LV com HTTP 200.
- Screenshots versionados em `docs/prd/evidence/` nos seis arquivos listados em
  `Visual validation`.

## Implemented

- PRD de homologação criada antes de qualquer mutação dos fluxos.
- Sessão criada por check-in agora herda o estado padrão de professor presente.
- Check-in direto em turma sem matrícula ativa é bloqueado no serviço e na view.
- Contadores de presença da home do professor são atualizados após aprovação assíncrona.
- Evento de troca de cartão passou de “portal aberto” para “método remoto realmente
  alterado”.
- Checkout de dependente trata erro Asaas sem HTTP 500, redireciona checkout externo fora
  do iframe, retoma senha após pagamento e recupera retry apenas da mesma sessão.
- Timeline administrativa mobile ganhou stylesheet próprio e conteúdo integral legível.
- Teste temporal explícito garante check-in após o fim da pausa.

## Cleanup findings

- Evidência com popup de extensão removida; somente capturas limpas foram mantidas.
- Não foram encontrados resíduos, código morto, duplicação ou hardcode novo material no
  fluxo alterado.
- A condição financeira do professor foi preservada, mas não virou configuração ativa
  porque faltam unidade, competência, dia de pagamento e pró-rata. A dívida foi separada
  na PRD-148 sem inferir obrigação financeira.
- Esta auditoria cobre o escopo da PRD-147; não declara o sistema inteiro livre das dívidas
  catalogadas nas PRDs 138 a 144.

## Follow-up PRDs

- PRD-146: decidir se professor aprovado publicamente cria turma nova ou pode vincular
  turmas existentes.
- PRD-148: definir e ativar a configuração de repasse do professor cadastrado publicamente.

## Deviations from plan

- A conta sandbox Asaas recusou callback para o domínio ngrok porque o domínio cadastrado
  era o de HG. Para homologação local, o pagamento foi confirmado no endpoint oficial do
  sandbox e entregue ao webhook local com assinatura válida; nenhuma configuração HG foi
  alterada.
- O backend de screenshot do navegador interno ficou indisponível na parte final. As
  capturas finais foram feitas no Chrome controlado, em sessão local e viewports reais.
- A primeira tentativa da suíte integral excedeu o timeout de 5 minutos do runner sem
  concluir; foi reiniciada com janela ampliada e não é contabilizada como resultado.

## Pending

- Decisões de produto das PRDs 146 e 148; nenhuma delas impede os fluxos homologados nesta
  PRD.

## Final status

**Concluída com limitações** — todos os fluxos solicitados e a regressão integral foram
homologados localmente/sandbox. Permanecem apenas decisões de produto nas PRDs 146 e 148
e a divergência externa do domínio de callback Asaas, sem bloqueio dos fluxos validados.
