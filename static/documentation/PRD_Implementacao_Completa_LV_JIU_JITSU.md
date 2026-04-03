# PRD - Implementacao Completa do Sistema LV JIU JITSU

## 1. Objetivo do documento

Este PRD transforma a documentacao atual do projeto em um plano de execucao integral, faseado e auditavel para construir o sistema **LV JIU JITSU** de ponta a ponta.

Ele foi consolidado a partir de:
- `CLAUDE.md`
- `AGENTS.md`
- `Documento_Unico_Mapeamento_Templates_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Models_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Views_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Forms_Serializers_LV_JIU_JITSU_v5.md`
- `Documento_Stripe_Implementacao_LV_JIU_JITSU.md`

Este documento nao e apenas uma lista de funcionalidades. Ele define:
- ordem obrigatoria de implementacao;
- dependencias entre fases;
- tarefas executaveis;
- resultado esperado por tarefa;
- criterios de aceitacao;
- validacao por revisao de codigo;
- validacao por testes;
- validacao com MCPs disponiveis;
- regra de continuidade para que a execucao nao pare no meio do sistema.

---

## 2. Meta do produto

Entregar uma plataforma web completa para operacao comercial, academica, financeira e administrativa de uma academia de Jiu-Jitsu, com:
- identidade unica por CPF;
- multi-papel no mesmo usuario;
- onboarding transacional;
- checkout recorrente via Stripe;
- pre-check de elegibilidade antes da camera;
- reserva previa de vagas;
- check-in antifraude por QR dinamico;
- motor de graduacao baseado em tempo ativo de treino;
- dashboard por perfil;
- financeiro, PDV e caixa diario;
- comunicacoes, auditoria, relatorios e exportacoes fail-fast;
- protecao LGPD e acesso sensivel controlado.

---

## 3. Regras globais de execucao

### 3.1 Regra de continuidade
- O executor deve avancar fase por fase sem interromper o projeto apos "parciais".
- Uma fase so pode ser dada como concluida quando todas as tarefas obrigatorias da fase atingirem aceite.
- Se houver bloqueio, o executor deve:
  1. registrar o bloqueio;
  2. registrar o impacto;
  3. propor a decisao minima necessaria;
  4. continuar imediatamente tudo o que for paralelizavel sem comprometer o dominio.

### 3.2 Regra de qualidade
- Nao deixar regra critica apenas no frontend.
- Nao duplicar identidade por CPF.
- Nao acoplar logica Stripe em views gigantes.
- Nao quebrar a separacao entre estado local e estado financeiro externo.
- Nao seguir em exportacao critica quando o arquivo de controle falhar.

### 3.3 Definition of Done global
Uma tarefa so esta pronta quando:
1. o codigo foi implementado;
2. a regra de dominio foi revalidada no backend;
3. os formularios/serializers aceitam apenas os campos corretos;
4. a view continua fina;
5. os efeitos colaterais foram isolados em service, manager, selector ou camada de dominio;
6. existem testes adequados ao risco;
7. a documentacao da spec foi atualizada se a tarefa revelou nova regra.

---

## 4. Checklist global de revisao de codigo

Toda revisao de codigo deste projeto deve verificar:
- identidade unica por CPF preservada;
- multi-papel preservado;
- `transaction.atomic()` em fluxos compostos;
- `select_related()` e `prefetch_related()` nas listagens e dashboards;
- nenhuma regra central escondida em template;
- nenhum `fields = '__all__'` em Forms ou Serializers;
- nenhuma regra de negocio em `save()`, `create()` ou `update()` de Serializer;
- endpoints mutaveis protegidos por `POST`;
- validacao de permissao e ownership no backend;
- webhooks idempotentes;
- estados locais de matricula independentes do status Stripe;
- check-in bloqueado antes da camera quando houver impedimento;
- exportacoes criticas com fail-fast real;
- trilha de auditoria nas acoes sensiveis.

---

## 5. Checklist global de testes

### 5.1 Testes minimos por padrao
- unitarios para regra de dominio;
- integracao para fluxos compostos;
- regressao para fluxos adjacentes;
- testes de permissao;
- testes de concorrencia quando houver reserva, caixa, webhook ou mudanca de estado critico.

### 5.2 Cobertura obrigatoria transversal
- CPF unico;
- onboarding transacional;
- dependentes e responsavel financeiro;
- professor tambem aluno;
- pre-check de elegibilidade antes da camera;
- reserva e consumo de vaga;
- Stripe checkout e webhook;
- inadimplencia e pausa de matricula;
- graduacao congelada durante pausa;
- LGPD e acesso sensivel;
- exportacao com fail-fast.

---

## 6. Protocolo de validacao por MCPs

### 6.1 GitHub MCP
Usar quando o repositorio estiver conectado para:
- organizar issues, milestones e PRs;
- revisar diffs e comentarios;
- acompanhar CI e checks;
- registrar progresso por fase.

### 6.2 Stripe MCP
Usar obrigatoriamente nas fases financeiras para:
- validar conta, produtos e prices reais;
- confirmar catalogo ativo versus legado;
- validar consistencia de assinaturas, invoices e payment intents;
- confirmar o que deve virar documentacao operacional.

### 6.3 Figma MCP
Usar quando houver design oficial, necessidade de gerar base visual ou validacao de paridade visual.
Se nao houver design, nao bloquear o backend por ausencia de Figma.

### 6.4 Regra pratica
- MCP nao substitui teste automatizado.
- MCP nao substitui revisao de codigo.
- MCP serve para validar contexto real, estado externo e coerencia operacional.

---

## 7. Roadmap macro

| Fase | Nome | Prioridade | Dependencias |
|---|---|---|---|
| F0 | Fundacao tecnica e arquitetura | Critica | Nenhuma |
| F1 | Identidade, autenticacao e papeis | Critica | F0 |
| F2 | Clientes, dependentes e onboarding | Critica | F1 |
| F3 | Professores, modalidades e turmas | Critica | F1 |
| F4 | Motor de presenca, reserva e tatame | Critica | F2, F3 |
| F5 | Financeiro local e contratos operacionais | Critica | F2 |
| F6 | Pagamentos Stripe e sincronizacao | Critica | F5 |
| F7 | Dashboards por perfil | Alta | F4, F5, F6 |
| F8 | Graduacao e exames | Alta | F4 |
| F9 | Documentos, termos, LGPD e prontuario | Alta | F2, F5, F7 |
| F10 | PDV, caixa rapido e fechamento diario | Alta | F5 |
| F11 | Relatorios, auditoria e exportacoes | Alta | F4, F5, F6, F10 |
| F12 | Hardening, observabilidade e go-live | Critica | Todas |

---

## 8. Fase F0 - Fundacao tecnica e arquitetura

### Objetivo
Preparar o alicerce tecnico do monolito para que as fases seguintes nao precisem reabrir decisoes estruturais basicas.

### Tarefas

#### F0.1 - Estruturar apps, base models e convencoes transversais
- Esperado:
  - apps fisicos conforme a topologia da spec;
  - base model com UUID, timestamps e convencoes comuns;
  - separacao inicial por agregado.
- Criterios de aceitacao:
  - a estrutura do codigo reflete `core`, `accounts`, `clientes`, `professores`, `presenca_graduacao`, `financeiro`, `pagamentos`, `dashboard`, `relatorios`;
  - nenhum agregado central fica "provisoriamente" dentro de outro app sem justificativa.
- Revisao de codigo:
  - sem dependencia circular entre apps;
  - sem regra de negocio no base model.
- Testes:
  - smoke tests de import dos apps;
  - testes de migracao inicial.
- MCP:
  - GitHub MCP opcional para registrar milestone arquitetural.

#### F0.2 - Configurar ambiente, settings e infraestrutura transversal
- Esperado:
  - `settings.py` parametrizado;
  - PostgreSQL como alvo principal e SQLite apenas local;
  - Celery e Redis preparados;
  - timezone correta;
  - logging e storage definidos.
- Criterios de aceitacao:
  - nenhum segredo hardcoded;
  - ambiente sobe localmente e aceita configuracao por `.env`.
- Revisao de codigo:
  - sem branch por ambiente espalhada em views;
  - sem configuracao sensivel em template ou JS.
- Testes:
  - teste de boot do projeto;
  - teste de configuracao critica.
- MCP:
  - Nao obrigatorio.

#### F0.3 - Criar mixins, middlewares e guardrails reutilizaveis
- Esperado:
  - mixins de autenticacao e ownership;
  - middleware/timezone;
  - base de throttling e seguranca;
  - convencao de lookup por UUID.
- Criterios de aceitacao:
  - infraestrutura reutilizavel pronta antes das views de dominio.
- Revisao de codigo:
  - MVT e DRF com mecanismos separados de permissao;
  - nenhuma dependencia de `id` exposto em rotas sensiveis.
- Testes:
  - testes de middleware;
  - testes de permissao base.
- MCP:
  - Nao obrigatorio.

#### F0.4 - Configurar pipeline de qualidade
- Esperado:
  - pytest ou stack equivalente;
  - factories/fixtures base;
  - cobertura minima dos guardrails.
- Criterios de aceitacao:
  - o repositorio permite validar fases sem teste manual puro.
- Revisao de codigo:
  - organizacao de testes por dominio;
  - sem fixture global opaca demais.
- Testes:
  - execucao dos testes base;
  - health check da pipeline local.
- MCP:
  - GitHub MCP recomendado para checks quando houver CI.

### Conclusao da fase
F0 termina quando o projeto consegue receber dominio real sem retrabalho estrutural imediato.

---

## 9. Fase F1 - Identidade, autenticacao e papeis

### Objetivo
Estabelecer identidade unica por CPF e base de autorizacao acumulavel.

### Tarefas

#### F1.1 - Implementar `CustomUser` e papeis acumulaveis
- Esperado:
  - usuario central por CPF;
  - papeis acumulaveis;
  - relacao entre autenticacao e perfis de negocio.
- Criterios de aceitacao:
  - um mesmo CPF pode acumular professor, aluno e responsavel financeiro;
  - nao existe duplicacao artificial por papel.
- Revisao de codigo:
  - CPF como chave natural de login;
  - sem enum exclusivo de papel para regra de autorizacao.
- Testes:
  - criar usuario com multiplos papeis;
  - impedir duplicidade por CPF.
- MCP:
  - Nao obrigatorio.

#### F1.2 - Implementar login, logout, primeiro acesso e recuperacao de senha
- Esperado:
  - T01 e T08 basicos funcionais;
  - rotas de login e redefinicao.
- Criterios de aceitacao:
  - login por CPF;
  - respostas seguras para credencial invalida e conta bloqueada;
  - fluxo de redefinicao auditavel.
- Revisao de codigo:
  - rate limit em login;
  - token de redefinicao com expira e uso unico.
- Testes:
  - login valido;
  - login invalido;
  - redefinicao com token expirado;
  - primeiro acesso.
- MCP:
  - GitHub MCP opcional para checklist da fase.

#### F1.3 - Implementar permissao por grupo/regra e ownership basico
- Esperado:
  - administracao, professor, aluno, responsavel;
  - estrutura para permissao por contexto.
- Criterios de aceitacao:
  - backend decide acesso;
  - template apenas reflete estado.
- Revisao de codigo:
  - sem permissao apenas por ocultacao de botao;
  - mixins e permissions DRF coerentes.
- Testes:
  - acesso liberado;
  - acesso negado;
  - ownership invalido.
- MCP:
  - Nao obrigatorio.

#### F1.4 - Implementar trilha inicial de auditoria de autenticacao e acoes sensiveis
- Esperado:
  - base de log auditavel para login, redefinicao, mudanca de senha e alteracoes sensiveis.
- Criterios de aceitacao:
  - acao critica produz rastro minimo.
- Revisao de codigo:
  - auditoria fora do template;
  - sem vazamento de dado sensivel no log.
- Testes:
  - emissao de log em acoes chave.
- MCP:
  - GitHub MCP opcional.

---

## 10. Fase F2 - Clientes, dependentes e onboarding

### Objetivo
Entregar cadastro transacional de titular e dependentes, perfil do aluno e dados sensiveis basicos.

### Tarefas

#### F2.1 - Implementar models de `PerfilAluno`, vinculo de responsavel e prontuario basico
- Esperado:
  - perfil do aluno;
  - vinculo responsavel-aluno;
  - historico basico e prontuario de emergencia.
- Criterios de aceitacao:
  - dependente fica vinculado a responsavel financeiro;
  - dependente com credencial propria respeita escopo restrito.
- Revisao de codigo:
  - sem duplicacao de pessoa;
  - acesso sensivel protegido.
- Testes:
  - criacao de dependente;
  - acesso restrito do dependente.
- MCP:
  - Nao obrigatorio.

#### F2.2 - Implementar wizard de onboarding do titular e dependentes
- Esperado:
  - T02 funcional;
  - cadastro em etapas;
  - persistencia transacional.
- Criterios de aceitacao:
  - erro em dependente invalida a transacao inteira;
  - aceite de termos obrigatorio;
  - CPF unico validado antes e durante persistencia.
- Revisao de codigo:
  - `transaction.atomic()` obrigatoria;
  - sem regra central no template.
- Testes:
  - onboarding de titular sozinho;
  - onboarding com dependentes;
  - rollback completo em erro.
- MCP:
  - Nao obrigatorio.

#### F2.3 - Implementar perfil e configuracoes da conta
- Esperado:
  - T09 funcional para aluno, responsavel, professor e admin em escopo proprio.
- Criterios de aceitacao:
  - CPF nao editavel sem fluxo administrativo;
  - mudancas sensiveis auditadas.
- Revisao de codigo:
  - campos mutaveis e imutaveis corretamente separados;
  - sem over-posting.
- Testes:
  - atualizacao de perfil;
  - troca de senha;
  - bloqueio de campos nao permitidos.
- MCP:
  - Nao obrigatorio.

#### F2.4 - Implementar gestao administrativa de alunos e dependentes
- Esperado:
  - T10 basica: listar, buscar, editar, ativar/desativar, vincular dependentes.
- Criterios de aceitacao:
  - admin consegue operar grupo familiar sem quebrar identidade;
  - dependente nao recebe acesso indevido ao financeiro.
- Revisao de codigo:
  - listagens sem N+1;
  - ownership e visibilidade corretos.
- Testes:
  - vinculacao e desvinculacao de dependentes;
  - edicao sem quebrar CPF unico.
- MCP:
  - GitHub MCP opcional para checklist administrativo.

---

## 11. Fase F3 - Professores, modalidades e turmas

### Objetivo
Construir a base operacional do tatame antes do check-in e da graduacao.

### Tarefas

#### F3.1 - Implementar models de professor e disponibilidade
- Esperado:
  - `PerfilProfessor`, modalidades atendidas e disponibilidade.
- Criterios de aceitacao:
  - um mesmo CPF pode ser professor e aluno;
  - professor enxerga apenas contexto permitido.
- Revisao de codigo:
  - sem duplicacao de identidade;
  - ownership e papeis acumulaveis respeitados.
- Testes:
  - professor tambem aluno;
  - disponibilidade persistida corretamente.
- MCP:
  - Nao obrigatorio.

#### F3.2 - Implementar modalidades, faixas e turmas
- Esperado:
  - `Modalidade`, `FaixaIBJJF`, `Turma` e configuracoes de lotacao e reserva.
- Criterios de aceitacao:
  - turmas suportam capacidade, horario, professor e politica de reserva.
- Revisao de codigo:
  - modelagem sem duplicidades soltas;
  - parametros configuraveis fora de constantes rigidas.
- Testes:
  - criacao de turma;
  - regras basicas de capacidade.
- MCP:
  - Nao obrigatorio.

#### F3.3 - Implementar gestao administrativa de professores e turmas
- Esperado:
  - T11 e T12 operacionais no minimo administrativo.
- Criterios de aceitacao:
  - admin gerencia professores, modalidades e turmas;
  - professor nao ganha poder administrativo indevido.
- Revisao de codigo:
  - listagens com prefetch;
  - formularios aceitam apenas campos explicitos.
- Testes:
  - CRUD de professor;
  - CRUD de turma;
  - filtros administrativos.
- MCP:
  - Figma MCP opcional se houver design oficial de telas.

#### F3.4 - Implementar sessoes de aula
- Esperado:
  - `SessaoAula` pronta para iniciar, encerrar e servir de ancora para presenca.
- Criterios de aceitacao:
  - check-in so existe com sessao valida;
  - professor autorizado consegue abrir e fechar sessao.
- Revisao de codigo:
  - mutacoes por POST;
  - nenhuma regra de sessao so no frontend.
- Testes:
  - abrir sessao;
  - encerrar sessao;
  - impedir check-in sem sessao.
- MCP:
  - Nao obrigatorio.

---

## 12. Fase F4 - Motor de presenca, reserva e tatame

### Objetivo
Entregar elegibilidade, reserva de vaga e check-in com protecao antifraude.

### Tarefas

#### F4.1 - Implementar pre-check de elegibilidade
- Esperado:
  - `PreCheckElegibilidadeAPIView` funcional;
  - hard stop antes da camera.
- Criterios de aceitacao:
  - inadimplente, pausado, sem reserva ou fora da janela nao chegam a abrir camera;
  - usuario elegivel recebe permissao para seguir.
- Revisao de codigo:
  - regra de elegibilidade no backend;
  - frontend apenas consome resposta.
- Testes:
  - adimplente elegivel;
  - inadimplente bloqueado;
  - pausado bloqueado;
  - sem reserva bloqueado.
- MCP:
  - Nao obrigatorio.

#### F4.2 - Implementar reserva de vaga com controle de capacidade
- Esperado:
  - `ReservaVaga` e endpoint de reserva;
  - consumo da lotacao na reserva, nao na porta.
- Criterios de aceitacao:
  - capacidade nao estoura sob concorrencia;
  - reserva ausente impede check-in quando exigida.
- Revisao de codigo:
  - lock e/ou controle transacional adequados;
  - sem race condition obvia.
- Testes:
  - reserva ate lotacao;
  - reserva concorrente;
  - no-show e politicas posteriores, quando implementadas.
- MCP:
  - Nao obrigatorio.

#### F4.3 - Implementar QR dinamico e check-in de camera
- Esperado:
  - sessao gera token de QR;
  - aluno faz leitura com backend revalidando tudo.
- Criterios de aceitacao:
  - QR expirado falha;
  - check-in duplicado na mesma sessao falha;
  - QR sozinho nao bypassa status operacional.
- Revisao de codigo:
  - nenhuma confianca cega no token;
  - backend valida aluno + sessao + elegibilidade + duplicidade.
- Testes:
  - check-in valido;
  - duplicidade;
  - QR expirado;
  - aluno bloqueado.
- MCP:
  - Nao obrigatorio.

#### F4.4 - Implementar dashboard do professor para operar aula
- Esperado:
  - T05 funcional para iniciar aula, gerar QR e confirmar presenca excepcional.
- Criterios de aceitacao:
  - professor so enxerga suas turmas;
  - presenca manual gera auditoria com motivo.
- Revisao de codigo:
  - sem vazamento financeiro ao professor;
  - servicos separados para aula e presenca.
- Testes:
  - iniciar aula;
  - gerar QR;
  - presenca manual auditada.
- MCP:
  - Figma MCP opcional para validar interface, se houver design.

---

## 13. Fase F5 - Financeiro local e contratos operacionais

### Objetivo
Implementar plano, assinatura local, fatura, bolsa, desconto e pausa de matricula como dominio proprio.

### Tarefas

#### F5.1 - Implementar `PlanoFinanceiro`, beneficios e assinatura local
- Esperado:
  - catalogo local de planos;
  - beneficios financeiros;
  - assinatura como agregado do negocio.
- Criterios de aceitacao:
  - plano local nao depende da Stripe para existir;
  - beneficios e descontos sao configuraveis.
- Revisao de codigo:
  - separacao clara entre catalogo local e price externo;
  - nenhum calculo financeiro central em template.
- Testes:
  - criacao de plano;
  - aplicacao de beneficio;
  - vinculo da assinatura local.
- MCP:
  - Stripe MCP recomendado para cruzar catalogo, mesmo antes da integracao final.

#### F5.2 - Implementar `AssinaturaAluno`, `FaturaMensal` e estados operacionais
- Esperado:
  - relacao da assinatura com alunos e dependentes;
  - faturas mensais;
  - estados `ATIVO`, `PENDENTE_FINANCEIRO`, `PAUSADO`, `BLOQUEADO`.
- Criterios de aceitacao:
  - status operacional local governa acesso;
  - dependente nao recebe visao financeira indevida.
- Revisao de codigo:
  - fonte de verdade local explicita;
  - sem mistura de estado local com `subscription.status` externo.
- Testes:
  - fatura em aberto bloqueando acesso;
  - fatura paga regularizando acesso;
  - dependente com escopo restrito.
- MCP:
  - Stripe MCP recomendado para comparar semantica de invoice real.

#### F5.3 - Implementar `TrancamentoMatricula`
- Esperado:
  - pausa local auditavel;
  - motivo, inicio e retorno previstos.
- Criterios de aceitacao:
  - aluno pausado nao faz check-in;
  - graduacao congela durante pausa.
- Revisao de codigo:
  - status local manda no dominio;
  - reativacao exige fluxo controlado.
- Testes:
  - pausar matricula;
  - bloquear acesso;
  - reativar matricula.
- MCP:
  - Stripe MCP obrigatorio na validacao da fase seguinte, mas opcional aqui.

#### F5.4 - Implementar T13 basica de financeiro detalhado
- Esperado:
  - listagem de planos, faturas, inadimplentes, comprovantes e acoes manuais.
- Criterios de aceitacao:
  - admin visualiza e opera financeiro sem gambiarra de dashboard;
  - hard stop de inadimplencia fica coerente com o estado da fatura.
- Revisao de codigo:
  - listagens paginadas e sem N+1;
  - mutacoes por POST.
- Testes:
  - baixa manual;
  - listagem de inadimplentes;
  - alteracao de status auditada.
- MCP:
  - Figma MCP opcional;
  - Stripe MCP recomendado para consistencia de linguagem operacional.

---

## 14. Fase F6 - Pagamentos Stripe e sincronizacao

### Objetivo
Conectar o dominio financeiro local ao ciclo real de checkout, assinatura e webhook da Stripe.

### Tarefas

#### F6.1 - Mapear catalogo local para produtos e prices Stripe
- Esperado:
  - associacao clara entre `PlanoFinanceiro` e `djstripe.Price`;
  - definicao de prices vigentes e legados.
- Criterios de aceitacao:
  - nenhum aluno novo entra em price legado por acidente;
  - catalogo local e externo ficam reconciliaveis.
- Revisao de codigo:
  - sem armazenar apenas IDs textuais quando FK do `dj-stripe` for suficiente;
  - versao e vigencia de price tratadas explicitamente.
- Testes:
  - resolucao do price correto por plano;
  - bloqueio de plano sem price valido.
- MCP:
  - Stripe MCP obrigatorio para validar produtos, prices e catalogo real.

#### F6.2 - Implementar criacao de checkout e rastreio local
- Esperado:
  - `CheckoutSolicitacao`;
  - criacao de `Checkout Session`;
  - redirecionamento seguro.
- Criterios de aceitacao:
  - sessao nasce com metadata minima;
  - acesso so libera apos confirmacao confiavel.
- Revisao de codigo:
  - view fina;
  - service de checkout isolado;
  - idempotencia visual respeitada.
- Testes:
  - iniciar checkout;
  - falha de criacao;
  - retorno sem ativacao prematura.
- MCP:
  - Stripe MCP obrigatorio para confirmar coerencia com a conta real.

#### F6.3 - Implementar webhooks idempotentes e sincronizacao local
- Esperado:
  - endpoint validando assinatura;
  - `WebhookProcessamento`;
  - reacao local apos espelho consistente do `dj-stripe`.
- Criterios de aceitacao:
  - reprocessamento nao duplica efeitos;
  - pagamento confirmado altera estado local correto.
- Revisao de codigo:
  - nada de logica de negocio grande no webhook cru;
  - `transaction.atomic()` nos efeitos locais.
- Testes:
  - webhook repetido;
  - invoice paga;
  - invoice falha;
  - assinatura cancelada ou pausada.
- MCP:
  - Stripe MCP obrigatorio para validar tipos de objeto e semantica externa.

#### F6.4 - Implementar portal do cliente e pausa com `pause_collection`
- Esperado:
  - sessao de portal sob demanda;
  - pausa financeira refletindo contrato operacional local.
- Criterios de aceitacao:
  - `pause_collection` nunca substitui o estado local `PAUSADO`;
  - reativacao reconcilia mundo local e mundo Stripe.
- Revisao de codigo:
  - separacao entre estado local e externo;
  - ownership na abertura do portal.
- Testes:
  - abrir portal;
  - pausar cobranca;
  - reativar contrato.
- MCP:
  - Stripe MCP obrigatorio.

---

## 15. Fase F7 - Dashboards por perfil

### Objetivo
Consolidar a experiencia operacional do aluno, responsavel, professor e administrador.

### Tarefas

#### F7.1 - Implementar T04 Dashboard do aluno e responsavel
- Esperado:
  - visao de acesso, graduacao, reservas, financeiro e dependentes.
- Criterios de aceitacao:
  - hard stop antes da camera funcionando;
  - responsavel alterna dependentes sem novo login;
  - dependente com credencial propria nao ve financeiro familiar.
- Revisao de codigo:
  - dashboards sem regra inventada;
  - prefetch em dados agregados.
- Testes:
  - dashboard adimplente;
  - dashboard inadimplente;
  - alternancia de dependente.
- MCP:
  - Figma MCP opcional para consistencia visual.

#### F7.2 - Implementar T06 Dashboard administrativo
- Esperado:
  - KPIs, pendencias, atalhos operacionais e visao financeira resumida.
- Criterios de aceitacao:
  - dashboard agrega e nao substitui telas operacionais;
  - acao critica sai para fluxo proprio auditavel.
- Revisao de codigo:
  - queries explicitas;
  - sem N+1 em cartoes e tabelas resumo.
- Testes:
  - carregamento de KPIs;
  - filtros por periodo;
  - visao de pendencias.
- MCP:
  - GitHub MCP opcional para rastrear criterios do dashboard.

#### F7.3 - Implementar snapshots e agregacoes quando necessario
- Esperado:
  - `DashboardSnapshotDiario` opcional ou estrategia equivalente de agregacao.
- Criterios de aceitacao:
  - dashboards nao dependem de query explosiva para cada abertura.
- Revisao de codigo:
  - estrategia de agregacao clara;
  - sem cache opaco que esconda bug de regra.
- Testes:
  - consistencia entre snapshot e dado de origem.
- MCP:
  - Nao obrigatorio.

#### F7.4 - Implementar T16 de leads e aula experimental
- Esperado:
  - captura de lead pela landing;
  - agendamento de aula experimental;
  - conversao futura para onboarding.
- Criterios de aceitacao:
  - origem do lead fica registrada;
  - lead nao se perde fora do sistema.
- Revisao de codigo:
  - fluxo comercial separado do onboarding, mas reutilizavel;
  - nenhum dado sensivel sem necessidade.
- Testes:
  - criar lead;
  - agendar aula experimental;
  - converter lead para cadastro.
- MCP:
  - Figma MCP opcional para validar UX publica, se houver design.

---

## 16. Fase F8 - Graduacao e exames

### Objetivo
Entregar o motor tecnico de aptidao, promocao e historico de graduacao.

### Tarefas

#### F8.1 - Implementar regras base IBJJF e configuracoes da academia
- Esperado:
  - `FaixaIBJJF`, `RegraGraduacaoAcademia`, validacoes por faixa/idade.
- Criterios de aceitacao:
  - regras oficiais e internas coexistem sem se confundir.
- Revisao de codigo:
  - criterio oficial separado de criterio local.
- Testes:
  - idade minima;
  - faixa possivel;
  - carencia configuravel.
- MCP:
  - Nao obrigatorio.

#### F8.2 - Implementar calculo de tempo ativo de treino
- Esperado:
  - algoritmo considera presencas validas e congela em pausa.
- Criterios de aceitacao:
  - pausa nao conta para elegibilidade;
  - ausencia de treino nao gera promocao artificial.
- Revisao de codigo:
  - regra central em service ou dominio;
  - sem calculo espalhado em templates.
- Testes:
  - tempo ativo;
  - pausa congelando contagem;
  - reativacao retomando contagem.
- MCP:
  - Nao obrigatorio.

#### F8.3 - Implementar exames e historico de graduacao
- Esperado:
  - `ExameGraduacao`, participacao e historico imutavel.
- Criterios de aceitacao:
  - promocao cria historico;
  - ciclo anterior encerra corretamente.
- Revisao de codigo:
  - sem update destrutivo de historico;
  - auditoria em promocao e negacao.
- Testes:
  - promocao concluida;
  - promocao adiada;
  - historico preservado.
- MCP:
  - Figma MCP opcional para T07.

#### F8.4 - Implementar T07 Painel de graduacao
- Esperado:
  - listagem de elegiveis, filtros, avaliacao e promocao.
- Criterios de aceitacao:
  - professor e admin operam o painel conforme escopo;
  - elegibilidade bate com motor tecnico.
- Revisao de codigo:
  - listagem sem N+1;
  - permissoes corretas.
- Testes:
  - filtro de aptos;
  - promocao com efeitos corretos.
- MCP:
  - Figma MCP opcional.

---

## 17. Fase F9 - Documentos, termos, LGPD e prontuario

### Objetivo
Fechar a camada sensivel do sistema: comprovantes, termos, certificados, LGPD e emergencia.

### Tarefas

#### F9.1 - Implementar T14 de comprovantes, contratos e termos
- Esperado:
  - upload, aprovacao, reprovacao e historico documental.
- Criterios de aceitacao:
  - anexos antigos nao sao sobrescritos;
  - aceite de termo e versionado.
- Revisao de codigo:
  - validacao universal de upload;
  - nada de arquivo grande ou tipo indevido passar.
- Testes:
  - upload valido;
  - upload invalido;
  - aprovacao e reprovacao.
- MCP:
  - Stripe MCP recomendado quando documento afetar comprovante manual de pagamento.

#### F9.2 - Implementar solicitacao LGPD e fluxo de anonimizaao
- Esperado:
  - `SolicitacaoLGPD`;
  - fluxo formal de exclusao/anonimizacao.
- Criterios de aceitacao:
  - exclusao definitiva nao quebra historico contabil;
  - dados sensiveis sao minimizados corretamente.
- Revisao de codigo:
  - sem soft delete disfarcado de cumprimento LGPD;
  - service transacional de anonimizaao.
- Testes:
  - abrir solicitacao;
  - anonimizar dados permitidos;
  - preservar minimo tecnico exigido.
- MCP:
  - Nao obrigatorio.

#### F9.3 - Implementar T20 de prontuario de emergencia
- Esperado:
  - visao rapida para professor e admin com dados vitais minimos.
- Criterios de aceitacao:
  - sem CPF completo, endereco ou financeiro;
  - acesso gera log de auditoria.
- Revisao de codigo:
  - restricao de escopo;
  - dados minimos expostos.
- Testes:
  - acesso autorizado;
  - acesso negado;
  - log gerado.
- MCP:
  - Figma MCP opcional.

---

## 18. Fase F10 - PDV, caixa rapido e fechamento diario

### Objetivo
Cobrir operacao presencial da recepcao fora do ciclo recorrente de assinatura.

### Tarefas

#### F10.1 - Implementar catalogo de produtos e venda PDV
- Esperado:
  - `ProdutoPDV`, `VendaPDV`, `ItemVendaPDV`.
- Criterios de aceitacao:
  - venda conclui com itens, total e operador;
  - opcionalmente associa cliente.
- Revisao de codigo:
  - totais calculados no backend;
  - sem logica de estoque no template.
- Testes:
  - venda avulsa;
  - venda vinculada a aluno;
  - calculo do total.
- MCP:
  - Nao obrigatorio.

#### F10.2 - Implementar `CaixaTurno` e `MovimentacaoCaixa`
- Esperado:
  - abertura, operacao e encerramento de turno.
- Criterios de aceitacao:
  - toda venda liquidada gera movimentacao;
  - turno fechado nao aceita lancamento retroativo.
- Revisao de codigo:
  - `select_for_update()` quando houver disputa de saldo;
  - trilha de operador.
- Testes:
  - abrir caixa;
  - movimentar;
  - fechar caixa;
  - concorrencia de fechamento.
- MCP:
  - Nao obrigatorio.

#### F10.3 - Implementar T17 PDV e T18 fechamento diario
- Esperado:
  - recepcao opera venda e conciliacao no mesmo ecossistema.
- Criterios de aceitacao:
  - troco e divergencia tratados corretamente;
  - alerta em quebra de caixa fora da tolerancia.
- Revisao de codigo:
  - mutacoes por POST;
  - operacoes monetarias em service.
- Testes:
  - checkout PDV;
  - fechamento com sobra;
  - fechamento com quebra.
- MCP:
  - Figma MCP opcional para UX operacional.

#### F10.4 - Implementar T19 Central de comunicacoes e avisos
- Esperado:
  - emissao de mural, avisos e comunicacoes por publico-alvo.
- Criterios de aceitacao:
  - avisos possuem vigencia;
  - disparos em massa sao assincronos;
  - autor, canal e publico ficam auditados.
- Revisao de codigo:
  - nenhum envio em massa bloqueando request web;
  - mensagens financeiras nao vazam para mural publico.
- Testes:
  - criar aviso;
  - publicar mural;
  - enfileirar campanha;
  - historico auditado.
- MCP:
  - Figma MCP opcional para a tela;
  - GitHub MCP opcional para rastrear backlog de canais externos.

---

## 19. Fase F11 - Relatorios, auditoria e exportacoes

### Objetivo
Entregar leitura gerencial, rastreabilidade e exportacao segura.

### Tarefas

#### F11.1 - Implementar `LogAuditoria` e trilha de acoes criticas
- Esperado:
  - log de mudancas operacionais relevantes.
- Criterios de aceitacao:
  - autor, horario, acao e contexto minimo registrados.
- Revisao de codigo:
  - sem auditoria solta em print/log textual sem estrutura.
- Testes:
  - registro de log nas acoes criticas.
- MCP:
  - GitHub MCP opcional para cruzar revisoes com mudancas.

#### F11.2 - Implementar `SolicitacaoExportacao` e `ControleExportacaoCSV`
- Esperado:
  - infraestrutura de exportacao com fail-fast.
- Criterios de aceitacao:
  - CSV critico nao inicia sem validar o arquivo de controle;
  - status final inequívoco: `SUCESSO`, `ABORTADA_PRE_VALIDACAO`, `ERRO_PROCESSAMENTO`.
- Revisao de codigo:
  - pre-validacao antes de leitura pesada;
  - logs tecnicos de falha.
- Testes:
  - exportacao valida;
  - arquivo de controle ausente;
  - arquivo bloqueado ou invalido.
- MCP:
  - Nao obrigatorio.

#### F11.3 - Implementar T15 relatorios operacionais e gerenciais
- Esperado:
  - relatorios de presenca, financeiro, graduacao, evasao e auditoria.
- Criterios de aceitacao:
  - filtros por periodo;
  - escopo por perfil;
  - exportacao segura.
- Revisao de codigo:
  - queries auditaveis;
  - paginacao e agregacao adequadas.
- Testes:
  - cada relatorio principal;
  - permissao de acesso;
  - exportacao correspondente.
- MCP:
  - Figma MCP opcional para interfaces;
  - GitHub MCP opcional para registrar backlog de BI futuro.

---

## 20. Fase F12 - Hardening, observabilidade e go-live

### Objetivo
Levar o sistema de "funciona" para "opera com seguranca".

### Tarefas

#### F12.1 - Hardening de seguranca
- Esperado:
  - rate limit, CSRF, protecao de upload, politicas de sessao, secrets externos.
- Criterios de aceitacao:
  - login e endpoints criticos protegidos;
  - nenhum segredo no codigo.
- Revisao de codigo:
  - checklist de seguranca concluido;
  - protecao de acoes mutaveis por POST.
- Testes:
  - smoke security tests;
  - regressao de login e upload.
- MCP:
  - Nao obrigatorio.

#### F12.2 - Hardening de performance e concorrencia
- Esperado:
  - ajustes de indice, agregacao, locks e N+1 eliminados.
- Criterios de aceitacao:
  - reservas, caixa e webhooks suportam concorrencia minima segura;
  - dashboards e listagens nao degradam por desenho obvio.
- Revisao de codigo:
  - prefetch/select_related presentes;
  - locks apenas onde agregam seguranca real.
- Testes:
  - concorrencia em reserva;
  - concorrencia em caixa;
  - reprocessamento de webhook.
- MCP:
  - GitHub MCP opcional para acompanhar bugs de performance.

#### F12.3 - Observabilidade e operacao
- Esperado:
  - logs estruturados, rastreio minimo e alertas para falhas criticas.
- Criterios de aceitacao:
  - erro de webhook, exportacao e pagamento fica rastreavel;
  - falha operacional nao fica muda.
- Revisao de codigo:
  - logs com contexto;
  - sem dados sensiveis excessivos no log.
- Testes:
  - simulacao de falha com log correspondente.
- MCP:
  - Stripe MCP recomendado para verificar reconciliacao final;
  - GitHub MCP recomendado para CI/checks.

#### F12.4 - Go-live checklist e aceite final do sistema
- Esperado:
  - checklist final por dominio;
  - validacao cruzada de regras centrais;
  - documentacao final de operacao.
- Criterios de aceitacao:
  - T01 a T20 cobertos conforme escopo;
  - fases F0 a F12 concluidas com evidencia;
  - backlog residual separado do escopo concluido.
- Revisao de codigo:
  - nenhuma fase com "ajuste depois" em regra critica.
- Testes:
  - smoke end-to-end dos fluxos principais;
  - regressao dos fluxos criticos.
- MCP:
  - GitHub MCP recomendado para fechamento do milestone;
  - Stripe MCP obrigatorio para check final do catalogo e sincronizacao;
  - Figma MCP opcional para validacao de paridade visual, se houver design.

---

## 21. Matriz de cobertura das telas

| Tela | Fase principal |
|---|---|
| T01 Landing e login | F1 |
| T02 Onboarding | F2 |
| T03 Checkout e assinatura | F6 |
| T04 Dashboard aluno/responsavel | F7 |
| T05 Dashboard professor | F4/F7 |
| T06 Dashboard admin | F7 |
| T07 Graduacao | F8 |
| T08 Recuperacao de senha | F1 |
| T09 Meu perfil | F2 |
| T10 Gestao de alunos/dependentes | F2 |
| T11 Gestao de professores | F3 |
| T12 Gestao de turmas/modalidades | F3 |
| T13 Financeiro detalhado | F5 |
| T14 Comprovantes, contratos e termos | F9 |
| T15 Relatorios e auditoria | F11 |
| T16 Leads e aula experimental | F7 |
| T17 PDV | F10 |
| T18 Fechamento de caixa | F10 |
| T19 Comunicacoes e avisos | F10 |
| T20 Prontuario de emergencia | F9 |

---

## 22. Tarefas que nao podem ser empurradas para "depois"

- CPF unico e multi-papel;
- pre-check antes da camera;
- reserva consumindo lotacao;
- webhook idempotente;
- pausa de matricula congelando graduacao;
- fail-fast de exportacao;
- permissao backend real;
- trilha de auditoria em acoes sensiveis;
- separacao entre estado local e Stripe;
- responsividade minima das telas operacionais.

---

## 23. Protocolo de execucao do agente para nao parar antes do sistema inteiro

1. Concluir a fase atual.
2. Validar aceite funcional.
3. Validar revisao de codigo.
4. Validar testes.
5. Validar MCPs aplicaveis.
6. Atualizar documentacao da spec se houver nova regra.
7. Abrir imediatamente a proxima fase.

O agente so pode encerrar o trabalho integral do sistema quando:
- todas as fases obrigatorias estiverem concluidas; ou
- existir bloqueio externo real, documentado e nao contornavel sem decisao do usuario.

Se houver bloqueio, o retorno minimo obrigatorio deve conter:
- tarefa bloqueada;
- motivo exato;
- evidencias;
- impacto nas fases seguintes;
- menor decisao necessaria para destravar.

---

## 24. Entregavel final esperado

Ao fim deste PRD, o sistema deve existir como produto operacional completo, com:
- dominio coerente;
- implementacao faseada;
- aceite verificavel;
- testes suficientes para os fluxos centrais;
- integracao Stripe reconciliada;
- operacao administrativa, academica e financeira funcional;
- backlog residual claramente separado do escopo entregue.
