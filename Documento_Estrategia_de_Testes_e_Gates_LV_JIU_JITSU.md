# Documento de Estrategia de Testes e Gates - LV JIU JITSU

> Documento operacional para garantir que o PRD final seja executado com criterio de pronto real.
> Aqui ficam os gates objetivos que precisam ser vencidos para cada fase, fluxo e entrega.

---

## 1. Objetivo

Definir:

- o que testar;
- em que nivel testar;
- quando uma fase pode ser marcada como concluida;
- como combinar revisao de codigo, testes e MCPs;
- como evitar entregas parciais marcadas como prontas.

---

## 2. Definicao de pronto global

Uma tarefa do PRD so pode virar `[x]` quando houver simultaneamente:

- implementacao concluida;
- revisao de codigo aprovada;
- testes adequados passando;
- validacao por MCP executada quando aplicavel;
- risco residual documentado quando existir.

Se faltar um desses itens, a tarefa permanece `[ ]`.

---

## 3. Piramide de testes do projeto

### 3.1 Testes unitarios

Usar para:

- regras de dominio;
- validadores;
- services pequenos;
- calculos de graduacao;
- regras de pausa e inadimplencia;
- normalizacao de CPF e dados criticos.

### 3.2 Testes de integracao

Usar para:

- onboarding titular + dependentes;
- reserva + consumo de vaga;
- checkout + webhook + reconciliacao;
- pausa local + pausa Stripe;
- exclusao ou anonimizacao LGPD;
- exportacao fail-fast.

### 3.3 Testes de permissao

Usar para:

- admin;
- recepcao;
- professor;
- aluno titular;
- dependente com credencial;
- responsavel financeiro.

### 3.4 Smoke tests

Usar para:

- login;
- dashboard principal;
- fluxo de pagamento;
- fluxo de check-in;
- fluxo de fechamento de caixa;
- fluxo de relatorio e exportacao.

---

## 4. Matriz minima por modulo interno

### 4.1 `system.identity_access`

- [ ] CPF unico
- [ ] Multi-papel
- [ ] Recuperacao de acesso
- [ ] Permissao por papel

### 4.2 `system.student_registry`

- [ ] Criacao de titular
- [ ] Criacao de dependente
- [ ] Vinculo com responsavel financeiro
- [ ] Restricao de escopo do dependente
- [ ] Prontuario e emergencia

### 4.3 `system.class_catalog`

- [ ] Criacao de modalidade
- [ ] Criacao de turma
- [ ] Sessao com capacidade
- [ ] Regra de agenda

### 4.4 `system.attendance_qr`

- [ ] Pre-check antes da camera
- [ ] Reserva consome vaga
- [ ] QR expira
- [ ] Check-in idempotente
- [ ] Bloqueio por inadimplencia

### 4.5 `system.finance_contracts`

- [ ] Criacao de matricula
- [ ] Inadimplencia altera estado local
- [ ] Pausa local bloqueia acesso
- [ ] Retomada revalida situacao
- [ ] Caixa e PDV fecham corretamente

### 4.6 `system.payments_stripe`

- [ ] Checkout session
- [ ] Webhook assinado
- [ ] Idempotencia por evento
- [ ] Reconciliacao com matricula local
- [ ] `pause_collection` quando elegivel

### 4.7 `system.graduation_engine`

- [ ] Tempo ativo acumulado
- [ ] Pausa congela contagem
- [ ] Elegibilidade explicavel
- [ ] Promocao auditavel

### 4.8 `system.documents_lgpd`

- [ ] Log de acesso sensivel
- [ ] Anonimizacao
- [ ] Exclusao definitiva juridicamente cabivel
- [ ] Minimizacao de dados

### 4.9 `system.reports_audit`

- [ ] Dashboard sem N+1
- [ ] Exportacao fail-fast
- [ ] Log de job de exportacao
- [ ] Auditoria de acao critica

---

## 5. Gate de revisao de codigo

Antes de aceitar qualquer fase:

- [ ] Sem `except: pass`
- [ ] Sem regra central em view
- [ ] Sem query em loop
- [ ] Sem `fields = "__all__"` em fluxo sensivel
- [ ] Sem confundir Stripe com estado local
- [ ] Sem quebrar identidade unica
- [ ] Sem expor dado medico ou financeiro fora do escopo
- [ ] Sem mutacao critica por `GET`
- [ ] Sem hardcode de regra operacional sensivel

---

## 6. Gate de testes por tipo de fluxo

### 6.1 Fluxo simples

Minimo exigido:

- [ ] teste unitario
- [ ] revisao de codigo

### 6.2 Fluxo composto

Minimo exigido:

- [ ] teste unitario
- [ ] teste de integracao
- [ ] revisao de codigo

### 6.3 Fluxo critico com integracao externa

Minimo exigido:

- [ ] teste unitario
- [ ] teste de integracao
- [ ] validacao MCP da integracao
- [ ] revisao de codigo
- [ ] registro de risco residual

### 6.4 Fluxo critico com dado sensivel

Minimo exigido:

- [ ] teste unitario
- [ ] teste de permissao
- [ ] teste de integracao
- [ ] revisao de codigo
- [ ] evidencia de auditoria

---

## 7. Gate por fase do PRD

### 7.1 Fase 00 a F02

- [ ] projeto sobe
- [ ] arquitetura fisica coerente
- [ ] seeds e configuracoes minimas existem
- [ ] autenticacao basica e landing funcionam

### 7.2 Fase 03 a F05

- [ ] onboarding transacional validado
- [ ] turmas e sessoes operacionais
- [ ] pre-check antes da camera validado
- [ ] reserva e presenca validadas

### 7.3 Fase 06 a F07

- [ ] matricula local validada
- [ ] estados financeiros locais coerentes
- [ ] checkout Stripe validado
- [ ] webhook idempotente validado

### 7.4 Fase 08 a F10

- [ ] dashboards por perfil validados
- [ ] graduacao por tempo ativo validada
- [ ] LGPD e prontuario auditavel validados

### 7.5 Fase 11 a F13

- [ ] PDV e caixa diario validados
- [ ] relatorios e exportacoes fail-fast validados
- [ ] observabilidade minima validada
- [ ] go-live checklist validado

---

## 8. Gate de MCPs

### 8.1 GitHub MCP

Usar quando houver repo conectado para:

- [ ] revisar diff relevante
- [ ] verificar CI
- [ ] acompanhar milestone

### 8.2 Stripe MCP

Obrigatorio para:

- [ ] product ou price
- [ ] customer
- [ ] subscription
- [ ] invoice
- [ ] payment intent
- [ ] webhook
- [ ] portal
- [ ] `pause_collection`

### 8.3 Figma MCP

Usar quando houver design oficial ou validacao visual com valor real.

---

## 9. Gate de evidencias minimas

Toda fase concluida precisa deixar ao menos:

- [ ] referencia de teste executado
- [ ] lista de risco residual, se houver
- [ ] criterio de aceite marcado
- [ ] observacao de MCP, quando aplicavel

---

## 10. Politica de regressao

Ao tocar fluxos abaixo, executar obrigatoriamente regressao adjacente:

- identidade -> onboarding + permissao
- financeiro -> attendance + graduation + dashboard
- Stripe -> financeiro local + portal + webhook
- attendance -> reserva + graduacao
- LGPD -> student_registry + auditoria
- relatorios -> exportacao + arquivo de controle

---

## 11. Resultado esperado

Com estes gates, o PRD final deixa de ser apenas um cronograma e passa a ser um plano executavel com:

- criterio de pronto verificavel;
- travas reais contra entrega superficial;
- relacao clara entre codigo, teste e operacao;
- continuidade ate o sistema inteiro ficar realmente concluido.
