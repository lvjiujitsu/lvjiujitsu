# Documento de Implementacao Stripe - LV JIU JITSU

## 1. Contexto e objetivo

Este documento consolida o estado atual observavel da conta Stripe associada ao projeto **LV JIU JITSU** e traduz esse levantamento para uma documentacao de implementacao aderente ao dominio do sistema.

Ele complementa:

- `CLAUDE.md`, que define a arquitetura e as invariantes do produto;
- `AGENTS.md`, que define o protocolo operacional do agente;
- os documentos de mapeamento de models, views, templates e serializers, que ja apontam a Stripe como integracao oficial de pagamentos.

O objetivo aqui nao e apenas listar recursos da conta Stripe, mas registrar:

- o que ja esta confirmado na conta;
- como isso conversa com o dominio local da academia;
- quais integracoes o backend precisa implementar ou manter;
- quais decisoes ainda precisam ser tomadas para uma implementacao segura e auditavel.

---

## 2. Resumo executivo

### 2.1 Conta identificada

- **Stripe Account ID:** `acct_1Pgt9lHDywrdzSUo`
- **Display name atual da conta:** `Instagram`

### 2.2 Confirmacoes obtidas da conta

Foi possivel confirmar diretamente na conta Stripe:

- existencia de catalogo de produtos;
- existencia de precos recorrentes em BRL;
- existencia de assinaturas ativas;
- existencia de faturas pagas e tambem faturas em estado de inadimplencia/incobravel;
- existencia de Payment Intents bem-sucedidos e tambem pendentes de confirmacao;
- ausencia de cupons cadastrados no momento da consulta.

### 2.3 Leitura arquitetural para o projeto

Com base na conta e na spec do projeto, o sistema deve tratar a Stripe como **gateway financeiro externo**, nunca como unica fonte de verdade do estado de negocio da academia.

Isso significa:

- a Stripe confirma eventos financeiros;
- o backend do LV JIU JITSU decide o estado local da matricula;
- bloqueio de check-in, pausa de matricula, graduacao e acesso esportivo continuam governados pelo dominio local;
- webhooks e sincronizacoes precisam ser idempotentes e auditaveis.

---

## 3. Dominios impactados

Esta documentacao impacta principalmente os seguintes dominios do projeto:

- `pagamentos`
- `financeiro`
- `accounts`
- `dashboard`
- `relatorios`
- `presenca_graduacao`

### 3.1 Motivo do impacto

- `pagamentos`: checkout, webhooks, portal do cliente, conciliacao tecnica;
- `financeiro`: plano local, assinatura local, inadimplencia, pausa e politica de acesso;
- `accounts`: associacao de `Customer` Stripe com identidade unica por CPF;
- `dashboard`: exibicao de status de cobranca e orientacao de regularizacao;
- `relatorios`: auditoria e reconciliacao;
- `presenca_graduacao`: bloqueio de acesso esportivo em situacoes financeiras impeditivas.

---

## 4. Estado atual confirmado da conta Stripe

## 4.1 Produtos encontrados

Produtos observados:

- `prod_TlIMpPoIVLi9PX` - `Plano Mensal Nova Tabela`
- `prod_ReEqIm7GpANsQh` - `Mensal Cartao de Credito TON`
- `prod_Qroq1y9hdNsweV` - `Anual Credito Mensal Recorrente`
- `prod_Qkhqv2fByxKCpn` - `Mensal Bolsista`
- `prod_QfOdqBEJiw9315` - `Anual Cartao de Credito Stripe`
- `prod_QY1B0KTL0NyIEM` - `Semestral Cartao de Credito Stripe`
- `prod_QY1BH9LekrV0f6` - `Trimestral Cartao de Credito Stripe`
- `prod_QY0xqmFzwhYSbU` - `Mensal Cartao de Credito Stripe`

### 4.1.1 Leitura de negocio

Esse catalogo indica que a conta ja opera ou operou ao menos estes modelos:

- plano mensal;
- plano trimestral;
- plano semestral;
- plano anual;
- plano bolsista;
- fluxo ou legado associado a `TON`.

Tambem ha indicio de coexistencia entre tabela antiga e nova, o que exige versao explicita de planos locais no backend.

## 4.2 Precos encontrados

Precos observados:

- `price_1SnllzHDywrdzSUoHLdZvLsK` - `prod_TlIMpPoIVLi9PX` - BRL 250,00 - mensal
- `price_1QkwMRHDywrdzSUoMCesWAva` - `prod_ReEqIm7GpANsQh` - BRL 200,00 - mensal
- `price_1Q05CxHDywrdzSUooVZhunKH` - `prod_Qroq1y9hdNsweV` - BRL 135,00 - recorrencia mensal por 1 intervalo
- `price_1PtCQQHDywrdzSUoB06eY5y2` - `prod_Qkhqv2fByxKCpn` - BRL 210,00 - mensal
- `price_1Po3pnHDywrdzSUoysx5gH1k` - `prod_QfOdqBEJiw9315` - BRL 1.200,00 - anual em 12 meses
- `price_1Po3nnHDywrdzSUoRs6EwAsn` - `prod_QY1B0KTL0NyIEM` - BRL 800,00 - semestral em 6 meses
- `price_1Po3mMHDywrdzSUoaUQmAuaI` - `prod_QY1BH9LekrV0f6` - BRL 400,00 - trimestral em 3 meses
- `price_1Pgv9VHDywrdzSUonYZXbUvX` - `prod_QY1B0KTL0NyIEM` - BRL 720,00 - semestral em 6 meses
- `price_1Pgv93HDywrdzSUoHEJfvaNK` - `prod_QY1BH9LekrV0f6` - BRL 390,00 - trimestral em 3 meses
- `price_1PguvxHDywrdzSUouHFmUkU3` - `prod_QY0xqmFzwhYSbU` - BRL 200,00 - mensal

### 4.2.1 Conclusoes tecnicas

- a conta opera em `BRL`;
- o modelo principal e recorrente;
- ha precos diferentes para produtos equivalentes, o que sugere historico de reajuste ou catalogo legado;
- o backend precisa tratar `Price` como referencia de cobranca, mas manter sua propria entidade de plano local.

## 4.3 Assinaturas observadas

Foi possivel confirmar a existencia de assinaturas em estado `active`.

### 4.3.1 Implicacao

O projeto nao esta diante de uma conta vazia ou apenas de configuracao preliminar. Ja existe operacao real de cobranca recorrente, o que reforca:

- necessidade de sincronizacao segura;
- necessidade de mapeamento entre aluno local e customer Stripe;
- necessidade de politicas claras para migracao de plano, pausa e regularizacao.

## 4.4 Faturas observadas

Foram observadas faturas com:

- `paid`
- `uncollectible`

### 4.4.1 Implicacao

O estado financeiro real da conta ja inclui inadimplencia ou cobranca que deixou de ser recuperavel por fluxo normal. No dominio do LV JIU JITSU isso conversa diretamente com:

- bloqueio de check-in;
- exibicao de pendencia no dashboard do aluno;
- retomada de acesso somente apos criterio financeiro definido pela academia.

## 4.5 Payment Intents observados

Foram observados Payment Intents com:

- `succeeded`
- `requires_confirmation`

### 4.5.1 Implicacao

O frontend e as paginas de retorno nao podem inferir pagamento concluido apenas por redirecionamento do checkout. O backend precisa continuar dirigindo o estado local com base no processamento confiavel do webhook e/ou da sincronizacao oficial.

## 4.6 Cupons observados

Nao foram encontrados cupons cadastrados no momento da consulta.

### 4.6.1 Implicacao

Se o projeto precisar de bolsa, desconto promocional, incentivo de matricula ou regra de retencao:

- ou isso sera modelado localmente no dominio `financeiro`;
- ou sera decidido se parte dessa politica tambem deve existir como cupom nativo na Stripe.

---

## 5. Fonte de verdade: Stripe x dominio local

## 5.1 Regra estrutural

A Stripe nao deve governar sozinha os estados centrais do negocio. A fonte de verdade deve ser separada assim:

- **Stripe:** eventos financeiros, cobranca, customer, subscription, invoice, checkout session;
- **dominio local:** status da matricula, elegibilidade de acesso, pausa academica, inadimplencia operacional, historico e auditoria.

## 5.2 Decisoes obrigatorias para a implementacao

O backend deve preservar:

- identidade unica por CPF;
- relacao de um `CustomUser` com zero ou um `Customer` Stripe principal;
- associacao de assinatura Stripe com a assinatura local da academia;
- tabela local de plano financeiro, mesmo quando houver `djstripe.Price`;
- status local `PAUSADO` independente do `subscription.status` externo.

## 5.3 Consequencia pratica

Mesmo que a Stripe informe uma assinatura ativa:

- o aluno pode estar bloqueado localmente por pausa de matricula;
- o aluno pode estar bloqueado por politica de inadimplencia da academia;
- o aluno pode nao poder fazer check-in por regra esportiva;
- o tempo de graduacao pode estar congelado.

---

## 6. Modelo recomendado de integracao

## 6.1 Camada tecnica

Conforme a spec do projeto, a integracao deve usar:

- `dj-stripe` como espelho principal dos objetos Stripe;
- `stripe-python` para fluxos especificos nao cobertos ou nao ergonomicos no pacote;
- services locais para orquestracao transacional;
- sinais do `dj-stripe` ou handlers dedicados para reagir ao espelho persistido.

## 6.2 Entidades Stripe que interessam ao projeto

As principais entidades a mapear sao:

- `Customer`
- `Product`
- `Price`
- `Subscription`
- `Invoice`
- `Checkout Session`
- `PaymentIntent`
- `Event`
- eventualmente `Billing Portal Session`

## 6.3 Entidades locais recomendadas

O projeto ja aponta necessidade de manter, ao menos, rastros locais como:

- `PlanoFinanceiro`
- `Assinatura`
- `AssinaturaAluno`
- `FaturaMensal`
- `CheckoutSolicitacao`
- `WebhookProcessamento`

### 6.3.1 Regra de acoplamento

FKs para objetos espelhados pelo `dj-stripe` devem preferir relacoes ORM com `SET_NULL` quando a preservacao do historico local for requisito.

---

## 7. Mapeamento inicial de catalogo Stripe para planos locais

Este mapeamento ainda e preliminar e deve ser confirmado pela operacao da academia.

| Produto Stripe | Price | Hipotese de plano local |
|---|---|---|
| `Plano Mensal Nova Tabela` | `price_1SnllzHDywrdzSUoHLdZvLsK` | Plano mensal atual ou reajustado |
| `Mensal Cartao de Credito TON` | `price_1QkwMRHDywrdzSUoMCesWAva` | Legado ou canal alternativo de cobranca |
| `Anual Credito Mensal Recorrente` | `price_1Q05CxHDywrdzSUooVZhunKH` | Plano anual com parcelamento mensal |
| `Mensal Bolsista` | `price_1PtCQQHDywrdzSUoB06eY5y2` | Plano bolsista |
| `Anual Cartao de Credito Stripe` | `price_1Po3pnHDywrdzSUoysx5gH1k` | Plano anual |
| `Semestral Cartao de Credito Stripe` | `price_1Po3nnHDywrdzSUoRs6EwAsn` | Plano semestral atual |
| `Semestral Cartao de Credito Stripe` | `price_1Pgv9VHDywrdzSUonYZXbUvX` | Plano semestral legado |
| `Trimestral Cartao de Credito Stripe` | `price_1Po3mMHDywrdzSUoaUQmAuaI` | Plano trimestral atual |
| `Trimestral Cartao de Credito Stripe` | `price_1Pgv93HDywrdzSUoHEJfvaNK` | Plano trimestral legado |
| `Mensal Cartao de Credito Stripe` | `price_1PguvxHDywrdzSUouHFmUkU3` | Plano mensal legado |

### 7.1 Recomendacao

Criar no dominio local uma forma explicita de marcar:

- plano ativo para venda;
- plano legado;
- price vigente por canal;
- data de inicio e fim de vigencia;
- motivo de substituicao.

Sem isso, o sistema corre risco de matricular aluno novo em preco antigo ou de perder rastreabilidade de contratos existentes.

---

## 8. Fluxos que precisam existir na implementacao

## 8.1 Criacao de checkout de assinatura

Fluxo recomendado:

1. backend recebe intencao de checkout;
2. valida identidade unica e contexto do aluno/titular;
3. seleciona `PlanoFinanceiro` local;
4. resolve o `Price` Stripe correspondente;
5. cria ou reutiliza `Customer` Stripe vinculado ao usuario local;
6. cria `Checkout Session`;
7. persiste `CheckoutSolicitacao` local;
8. redireciona para Stripe Checkout.

### 8.1.1 Regras obrigatorias

- usar `POST`;
- registrar metadata minima para reconciliacao;
- nao ativar acesso esportivo no retorno visual de sucesso;
- confirmar liberacao apenas apos evento financeiro confiavel.

## 8.2 Processamento de webhook

Fluxo recomendado:

1. Stripe envia evento;
2. endpoint valida assinatura;
3. `dj-stripe` persiste espelho;
4. logica local reage de forma idempotente;
5. atualiza assinatura local, faturamento local e auditoria.

### 8.2.1 Regras obrigatorias

- idempotencia por evento;
- rastreio de processamento local;
- `transaction.atomic()` nos efeitos colaterais locais;
- tolerancia a reprocessamento.

## 8.3 Atualizacao de acesso do aluno

Acesso do aluno deve depender de combinacao entre:

- status financeiro confirmado;
- status local da matricula;
- politica de tolerancia da academia;
- pausa local;
- criterios esportivos adicionais.

## 8.4 Inadimplencia

Quando houver falha relevante de cobranca, o sistema local precisa:

- marcar situacao financeira;
- orientar regularizacao no dashboard;
- bloquear check-in conforme politica da academia;
- manter trilha de auditoria.

## 8.5 Pausa de matricula

Quando houver trancamento:

- o sistema local define `PAUSADO`;
- se a assinatura Stripe for elegivel, aplicar `pause_collection`;
- congelar o tempo de graduacao;
- impedir check-in;
- registrar inicio, previsao de retorno e motivo.

## 8.6 Portal do cliente

Se o projeto expuser Customer Portal:

- a sessao deve ser criada sob demanda;
- o backend deve verificar se o usuario logado pode abrir o portal daquele contrato;
- alteracoes feitas no portal ainda precisam refletir no estado local via webhook/sincronizacao.

---

## 9. Webhooks e eventos prioritarios

Os nomes exatos dos eventos devem ser confirmados na configuracao final da conta, mas o projeto deve se preparar ao menos para eventos equivalentes a:

- conclusao de checkout;
- criacao ou atualizacao de assinatura;
- cancelamento de assinatura;
- pagamento de fatura bem-sucedido;
- falha de pagamento;
- mudanca de status de invoice;
- eventos de customer relevantes para conciliacao.

### 9.1 Regras de implementacao

- nao duplicar processamento concorrendo com o endpoint do `dj-stripe`;
- reagir preferencialmente apos espelho consistente;
- manter tabela local de auditoria/processamento;
- permitir reprocessamento seguro.

---

## 10. Variaveis e configuracoes que precisam existir

O documento nao expoe segredos, mas a implementacao precisa prever ao menos:

- chave publica Stripe;
- chave secreta Stripe;
- segredo de assinatura do webhook;
- URLs de sucesso e cancelamento do checkout;
- URL de retorno do customer portal;
- chave/flag de ambiente;
- politicas locais de bloqueio por inadimplencia;
- politicas locais de pausa e retomada.

### 10.1 Regra de configuracao

Nada disso deve ficar hardcoded em view, template ou JavaScript de pagina.

---

## 11. Lacunas que ainda precisam de confirmacao humana

Os itens abaixo ainda nao podem ser inferidos com seguranca apenas pela leitura da conta:

- qual produto/preco deve ser considerado oficial para novas vendas;
- se o catalogo `TON` continua valido ou e apenas legado;
- qual regra exata define inadimplencia bloqueadora na academia;
- quais planos aceitam `pause_collection`;
- quais meios de pagamento devem compor a experiencia final do aluno;
- se existe conta separada para teste e para producao;
- quais webhooks ja estao configurados no dashboard;
- se o `display_name` atual da conta deve ser alterado.

---

## 12. Checklist de implementacao recomendada

- mapear cada `Price` ativo a um `PlanoFinanceiro` local;
- marcar planos legados versus planos vigentes;
- vincular `CustomUser` a `Customer` Stripe sem duplicar identidade;
- criar service de checkout com persistencia local de solicitacao;
- processar webhook via `dj-stripe` com reacao local idempotente;
- manter assinatura local separada da assinatura externa;
- implementar politica de bloqueio por inadimplencia no backend;
- integrar trancamento com `pause_collection` quando elegivel;
- registrar auditoria financeira e operacional;
- cobrir com testes os cenarios de idempotencia, inadimplencia e pausa.

---

## 13. Sugestao de testes minimos

Os testes de maior valor para esta integracao sao:

- criacao de checkout para usuario com identidade unica por CPF;
- reutilizacao do mesmo `Customer` Stripe para a mesma pessoa;
- criacao idempotente de assinatura local apos webhook repetido;
- invoice paga desbloqueando o estado financeiro local;
- invoice inadimplente bloqueando acesso conforme politica;
- pausa local aplicando `pause_collection` quando houver assinatura elegivel;
- retorno visual de checkout sem ativacao prematura do acesso;
- seguranca de acesso ao customer portal;
- preservacao do historico local mesmo quando o espelho externo mudar.

---

## 14. Recomendacao de proximo passo documental

O proximo artefato ideal para este repositorio e uma tabela oficial de mapeamento:

- `PlanoFinanceiro local`
- `Product Stripe`
- `Price Stripe`
- status de vigencia
- canal de cobranca
- elegibilidade para pausa
- regra de inadimplencia associada

Esse artefato eliminara ambiguidade entre catalogo legado e catalogo atual.

---

## 15. Conclusao

A conta Stripe ja fornece informacao suficiente para sair de uma documentacao abstrata e partir para uma documentacao de implementacao realista. Ja esta confirmado que ha operacao recorrente, catalogo financeiro ativo, assinaturas em uso e cenarios reais de pagamento e inadimplencia.

O ponto mais importante e manter o alinhamento com a arquitetura do LV JIU JITSU:

- Stripe como integracao financeira externa;
- dominio local como fonte de verdade operacional;
- webhooks idempotentes;
- pausa academica separada do status financeiro externo;
- bloqueios de acesso sempre revalidados no backend.

## 16. Referencias internas

- `CLAUDE.md`
- `AGENTS.md`
- `Documento_Unico_Mapeamento_Models_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Templates_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Views_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Forms_Serializers_LV_JIU_JITSU_v5.md`
