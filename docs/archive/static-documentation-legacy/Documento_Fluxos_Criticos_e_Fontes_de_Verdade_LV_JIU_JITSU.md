# Documento de Fluxos Criticos e Fontes de Verdade - LV JIU JITSU

> Documento para travar os fluxos que mais facilmente quebram quando o sistema cresce.
> Cada fluxo abaixo define quem manda no estado, em que ordem gravar, o que auditar e como validar.

---

## 1. Regra central

Sempre perguntar:

1. qual modulo interno e fonte de verdade;
2. qual modulo apenas reflete ou sincroniza;
3. qual evento deve ser idempotente;
4. qual evidencia minima precisa ser registrada.

Se isso nao estiver claro, o fluxo ainda nao esta pronto para implementacao.

---

## 2. Fluxo de identidade e multi-papel

### Fonte de verdade

- `system.identity_access`

### Ordem de escrita

1. localizar identidade por CPF normalizado;
2. criar identidade se ela nao existir;
3. anexar papeis necessarios;
4. criar perfis complementares em `student_registry` ou `instructor_ops`;
5. registrar auditoria de criacao ou alteracao.

### Regras inviolaveis

- CPF unico;
- professor pode ser aluno;
- responsavel financeiro pode nao ser aluno;
- dependente com credencial continua sendo a mesma pessoa.

---

## 3. Fluxo de onboarding de titular e dependentes

### Fonte de verdade

- `system.student_registry`

### Modulos participantes

- `identity_access`
- `student_registry`
- `finance_contracts`

### Ordem de escrita

1. validar CPF e identidade do titular;
2. criar ou vincular identidade do titular;
3. criar responsavel financeiro se diferente;
4. criar dependentes;
5. criar vinculos familiar e financeiro;
6. criar perfis esportivos;
7. abrir contrato ou matricula local quando aplicavel;
8. registrar auditoria.

### Regras inviolaveis

- tudo em `transaction.atomic()`;
- falha em uma parte aborta o onboarding inteiro;
- nenhum dependente fica orfao;
- nenhum perfil esportivo existe sem pessoa valida.

---

## 4. Fluxo de matricula, plano local e status operacional

### Fonte de verdade

- `system.finance_contracts`

### Ordem de escrita

1. criar plano local ou vincular plano existente;
2. criar contrato ou matricula;
3. marcar status inicial;
4. criar ledger local de cobranca ou recebivel;
5. expor situacao para dashboard e attendance.

### Regras inviolaveis

- `ACTIVE`, `PAUSED`, `DELINQUENT` e `CANCELLED` sao estados locais;
- Stripe nao decide sozinha o acesso;
- pausa precisa congelar impacto esportivo;
- inadimplencia precisa propagar bloqueio operacional.

---

## 5. Fluxo de checkout Stripe e reconciliacao

### Fonte de verdade

- `system.payments_stripe` como espelho tecnico;
- `system.finance_contracts` como estado de negocio local.

### Ordem de escrita

1. selecionar plano local valido;
2. resolver mapeamento para product ou price Stripe;
3. criar ou vincular customer;
4. criar checkout session;
5. aguardar webhook assinado;
6. processar evento de forma idempotente;
7. reconciliar com matricula local;
8. registrar log de evento e reconciliacao.

### Regras inviolaveis

- webhook com assinatura valida;
- idempotencia por `event_id`;
- status externo nunca escreve acesso de forma cega;
- divergencia entre Stripe e local precisa ser rastreavel.

---

## 6. Fluxo de reserva e pre-check antes da camera

### Fonte de verdade

- `system.attendance_qr`

### Ordem de escrita

1. localizar sessao de aula;
2. validar janela da sessao;
3. validar status da matricula;
4. validar regra de reserva;
5. validar capacidade;
6. validar papel do usuario;
7. somente entao permitir abrir camera;
8. emitir QR dinamico ou habilitar leitura.

### Regras inviolaveis

- se houver bloqueio, nao chamar camera;
- vaga e consumida na reserva, nao na porta;
- elegibilidade precisa ser recalculada no backend no momento do check-in.

---

## 7. Fluxo de check-in e presenca valida

### Fonte de verdade

- `system.attendance_qr`

### Ordem de escrita

1. validar QR, token ou janela;
2. revalidar elegibilidade;
3. verificar se ja existe presenca na sessao;
4. gravar presenca;
5. gravar tentativa e auditoria;
6. publicar efeito derivado para dashboards e graduacao.

### Regras inviolaveis

- uma presenca valida por sessao e aluno;
- tentativa negada tambem pode ser auditada;
- token curto e expira;
- leitura duplicada nao duplica presenca.

---

## 8. Fluxo de graduacao por tempo ativo

### Fonte de verdade

- `system.graduation_engine`

### Modulos participantes

- `attendance_qr`
- `finance_contracts`
- `student_registry`

### Ordem de escrita

1. consumir presencas validas;
2. excluir periodos pausados ou inelegiveis;
3. calcular tempo ativo;
4. aplicar regras de faixa;
5. gerar elegibilidade;
6. registrar exame ou decisao de promocao.

### Regras inviolaveis

- tempo corrido sozinho nao vale;
- pausa congela progressao;
- presenca invalida nao conta;
- decisao de promocao e auditavel.

---

## 9. Fluxo de prontuario, emergencia e LGPD

### Fonte de verdade

- `system.student_registry`
- `system.documents_lgpd`

### Ordem de escrita

1. controlar acesso por papel;
2. registrar acesso sensivel;
3. aplicar consulta minima necessaria;
4. responder emergencia com trilha;
5. em exclusao, anonimizar ou eliminar conforme regra legal;
6. registrar conclusao do procedimento.

### Regras inviolaveis

- prontuario nao pode ficar aberto por conveniencia;
- dependente nao enxerga financeiro do titular;
- dado medico exige auditoria;
- exclusao definitiva nao e soft delete disfarado.

---

## 10. Fluxo de PDV e caixa diario

### Fonte de verdade

- `system.finance_contracts`

### Ordem de escrita

1. abrir caixa do dia;
2. registrar venda avulsa;
3. registrar forma de pagamento;
4. atualizar saldo esperado;
5. fechar caixa;
6. registrar divergencia se houver.

### Regras inviolaveis

- caixa fisico nao se mistura com recorrencia Stripe;
- fechamento precisa ser auditavel;
- movimento manual precisa de operador responsavel.

---

## 11. Fluxo de relatorios, exportacao e fail-fast

### Fonte de verdade

- `system.reports_audit`

### Ordem de escrita

1. validar arquivo de controle;
2. abortar imediatamente se a pre-condicao falhar;
3. montar dataset via selectors;
4. registrar job;
5. gerar saida;
6. registrar sucesso ou falha.

### Regras inviolaveis

- nada de leitura pesada antes da validacao de controle;
- exportacao critica nao prossegue sem trilha;
- dashboard nao vira dono da regra.

---

## 12. Chaves de revisao para qualquer fluxo critico

- [ ] Fonte de verdade definida
- [ ] Modulo refletor definido
- [ ] Ordem de escrita definida
- [ ] Idempotencia definida
- [ ] Auditoria definida
- [ ] Condicoes de bloqueio definidas
- [ ] Criterio de aceite definido

---

## 13. Resultado esperado

Este documento existe para impedir que o sistema seja implementado com:

- estado duplicado sem dono;
- integracao externa mandando mais que o dominio local;
- efeitos colaterais escondidos;
- PRD bonito, mas sem fonte de verdade clara para os fluxos mais sensiveis.
