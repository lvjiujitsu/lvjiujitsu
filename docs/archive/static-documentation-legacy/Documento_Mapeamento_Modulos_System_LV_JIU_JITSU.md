# Documento de Mapeamento dos Modulos Internos do `system` - LV JIU JITSU

> Documento de fronteiras internas do app unico `system`.
> O objetivo aqui e deixar explicito o que cada modulo interno possui, do que ele depende e o que ele nao pode fazer.

---

## 1. Regra base

Todos os modulos abaixo vivem fisicamente dentro do app `system`, mas devem ser tratados como agregados internos com responsabilidade propria.

Cada modulo deve responder:

- quais modelos possui;
- quais services orquestram seus fluxos;
- quais views expoe;
- qual e sua fonte de verdade;
- de quais modulos pode depender.

---

## 2. Mapa mestre

### 2.1 `system.public`

**Responsabilidade**

- landing;
- paginas abertas;
- home institucional;
- mural publico;
- paginas de ajuda e acesso inicial.

**Pode depender de**

- `system.settings_seed`
- `system.communications`

**Nao pode possuir**

- regra financeira;
- decisao de permissao de negocio;
- logica de check-in.

---

### 2.2 `system.identity_access`

**Responsabilidade**

- identidade central por CPF;
- credenciais;
- papeis;
- permissao;
- sessao;
- recuperacao de acesso.

**Modelos esperados**

- `SystemUser`
- `RoleAssignment`
- `PermissionProfile`
- `AccessAudit`

**Fonte de verdade**

- identidade unica;
- relacao entre pessoa e papeis.

**Pode depender de**

- `system.settings_seed`

---

### 2.3 `system.student_registry`

**Responsabilidade**

- titular;
- dependentes;
- responsavel financeiro;
- cadastro;
- prontuario;
- contatos;
- documentos;
- dados de emergencia.

**Modelos esperados**

- `Person`
- `StudentProfile`
- `GuardianRelationship`
- `EmergencyContact`
- `MedicalNote`
- `DocumentRecord`
- `ConsentTerm`

**Pode depender de**

- `system.identity_access`
- `system.documents_lgpd`

**Nao pode depender de**

- `system.payments_stripe` para criar pessoa.

---

### 2.4 `system.instructor_ops`

**Responsabilidade**

- perfil docente;
- especialidades;
- agenda de professor;
- disponibilidade;
- alocacao em turma.

**Pode depender de**

- `system.identity_access`
- `system.class_catalog`

---

### 2.5 `system.class_catalog`

**Responsabilidade**

- modalidades;
- turmas;
- sessoes;
- calendario;
- capacidade;
- grade.

**Modelos esperados**

- `MartialArtProgram`
- `ClassTemplate`
- `ClassSession`
- `ClassCapacityRule`
- `ClassReservationPolicy`

**Fonte de verdade**

- oferta planejada de treino.

**Pode depender de**

- `system.instructor_ops`
- `system.settings_seed`

---

### 2.6 `system.attendance_qr`

**Responsabilidade**

- reserva;
- pre-check de elegibilidade;
- emissao de QR;
- leitura;
- presenca;
- antifraude basico.

**Modelos esperados**

- `ClassReservation`
- `CheckinAttempt`
- `DynamicQrToken`
- `AttendanceRecord`
- `AttendanceAudit`

**Fonte de verdade**

- direito de tentar entrar;
- reserva valida;
- presenca efetivamente confirmada.

**Pode depender de**

- `system.class_catalog`
- `system.student_registry`
- `system.finance_contracts`

**Nao pode depender de**

- `system.payments_stripe` para autorizar presenca.

---

### 2.7 `system.finance_contracts`

**Responsabilidade**

- plano local;
- contrato;
- matricula;
- desconto;
- bolsa;
- inadimplencia;
- pausa;
- PDV;
- caixa diario.

**Modelos esperados**

- `MembershipPlan`
- `EnrollmentContract`
- `EnrollmentStatusHistory`
- `DiscountGrant`
- `ScholarshipGrant`
- `Receivable`
- `ManualPaymentRecord`
- `CashRegister`
- `CashMovement`

**Fonte de verdade**

- estado local da matricula e seus efeitos operacionais.

**Pode depender de**

- `system.student_registry`
- `system.settings_seed`

**Nao pode depender de**

- `system.payments_stripe` como fonte primaria de status.

---

### 2.8 `system.payments_stripe`

**Responsabilidade**

- catalogo Stripe;
- checkout;
- customer portal;
- assinatura;
- invoices;
- payment intents;
- webhooks;
- reconciliacao.

**Modelos esperados**

- `StripeCatalogMap`
- `StripeCustomerLink`
- `StripeSubscriptionLink`
- `StripeWebhookEventLog`
- `StripeReconciliationRun`

**Fonte de verdade**

- espelho tecnico da integracao externa.

**Pode depender de**

- `system.finance_contracts`
- `system.identity_access`

---

### 2.9 `system.graduation_engine`

**Responsabilidade**

- tempo ativo;
- regras de faixa;
- elegibilidade;
- exame;
- promocao;
- historico tecnico.

**Pode depender de**

- `system.attendance_qr`
- `system.finance_contracts`
- `system.student_registry`

**Fonte de verdade**

- progresso tecnico e decisao de promocao.

---

### 2.10 `system.communications`

**Responsabilidade**

- mural;
- comunicados;
- campanhas operacionais;
- notificacoes por evento;
- historico de envio.

**Pode depender de**

- `system.student_registry`
- `system.instructor_ops`
- `system.settings_seed`

**Nao pode quebrar**

- cadastro;
- pagamento;
- check-in;
- graduacao.

---

### 2.11 `system.documents_lgpd`

**Responsabilidade**

- consentimentos;
- retencao;
- anonimizacao;
- exclusao definitiva;
- trilha de acesso a dado sensivel.

**Pode depender de**

- `system.student_registry`
- `system.identity_access`

---

### 2.12 `system.reports_audit`

**Responsabilidade**

- dashboards;
- auditoria;
- relatorios;
- exportacoes;
- BI;
- arquivo de controle fail-fast.

**Pode depender de**

- todos os modulos como leitura.

**Nao pode**

- virar fonte primaria de regra critica;
- escrever estado de dominio central sem service explicito.

---

### 2.13 `system.settings_seed`

**Responsabilidade**

- parametros operacionais;
- seeds;
- catalogos;
- configuracoes da academia;
- valores default;
- cargas iniciais.

---

## 3. Mapa de dependencias permitido

```text
identity_access <- student_registry <- finance_contracts <- payments_stripe
                       ^                   ^
                       |                   |
                attendance_qr --------> graduation_engine
                       ^
                       |
                  class_catalog <- instructor_ops

communications -> leitura de student_registry / instructor_ops
reports_audit -> leitura de todos
documents_lgpd -> student_registry + identity_access
settings_seed -> base para todos
```

### Regras de dependencia

- `payments_stripe` consome e sincroniza `finance_contracts`; nunca o contrario como fonte primaria.
- `graduation_engine` depende de presenca valida e estado local da matricula.
- `reports_audit` pode ler todos, mas nao deve reescrever regra central.
- `communications` e lateral; falha de envio nao bloqueia dominio central.

---

## 4. Checklist de uso correto deste documento

- [ ] Todo model novo entra no modulo interno certo
- [ ] Todo service novo declara claramente de qual modulo e
- [ ] Nenhuma view cruza dominios sem service
- [ ] Nenhuma regra de Stripe invade `finance_contracts`
- [ ] Nenhuma regra de graduacao invade `attendance_qr` sem contrato claro
- [ ] Nenhum dashboard vira dono do dado

---

## 5. Resultado esperado

Com este mapeamento, o app unico `system` continua simples de operar e, ao mesmo tempo, forte o suficiente para:

- sustentar o PRD inteiro;
- evitar caos estrutural;
- permitir evolucao por fases;
- manter clareza de ownership, teste e revisao de codigo.
