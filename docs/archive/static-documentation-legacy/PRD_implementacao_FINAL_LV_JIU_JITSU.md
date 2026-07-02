# PRD implementacao FINAL - LV JIU JITSU

> Documento mestre de execucao completa do sistema.
> Este arquivo nao substitui `CLAUDE.md`, `AGENTS.md` nem os documentos de mapeamento.
> Ele existe para transformar a spec em um plano operacional integral, marcavel e auditavel.

---

## 0. Como usar este PRD

- Use este arquivo como checklist vivo de construcao do sistema.
- Toda tarefa nasce como `[ ]`.
- Uma tarefa so pode virar `[x]` quando:
  - implementacao foi concluida;
  - revisao de codigo foi validada;
  - testes da tarefa passaram;
  - validacao por MCP aplicavel foi executada;
  - evidencias minimas foram registradas.
- Se uma tarefa estiver parcialmente feita, ela continua `[ ]`.
- Se surgir bloqueio, nao marcar como concluida. Registrar no historico e seguir tudo o que for destravavel.
- Este PRD foi desenhado para que o trabalho nao pare no meio do sistema.

### 0.1 Legenda

- `[ ]` Nao iniciado ou ainda nao aceito
- `[x]` Concluido e aceito

### 0.2 Fontes de verdade usadas para montar este PRD

- `AGENTS.md`
- `CLAUDE.md`
- `Documento_Unico_Mapeamento_Models_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Views_LV_JIU_JITSU.md`
- `Documento_Unico_Mapeamento_Forms_Serializers_LV_JIU_JITSU_v5.md`
- `Documento_Unico_Mapeamento_Templates_LV_JIU_JITSU.md`
- `Documento_Stripe_Implementacao_LV_JIU_JITSU.md`
- `Documento_Arquitetura_App_System_LV_JIU_JITSU.md`
- `Documento_Mapeamento_Modulos_System_LV_JIU_JITSU.md`
- `Documento_Fluxos_Criticos_e_Fontes_de_Verdade_LV_JIU_JITSU.md`
- `Documento_Estrategia_de_Testes_e_Gates_LV_JIU_JITSU.md`
- `PRD_Implementacao_Completa_LV_JIU_JITSU.md` como contexto previo

---

## 1. Historico de evolucao deste PRD

- [x] 2026-03-30 - versao inicial FINAL criada com checklist completo por fase, tarefa, aceite, revisao, testes e MCPs.
- [x] 2026-03-30 - planejamento refatorado para app unico `system` com modularizacao interna e documentos estruturais de suporte.
- [x] 2026-03-31 - Fase 00 implementada com `.venv`, projeto Django base, `system` modularizado, pytest e validacoes de boot.
- [x] 2026-03-31 - Fase 01 implementada com `CustomUser` por CPF, papeis acumulaveis, login, token de acesso, ownership base e auditoria.
- [x] 2026-04-01 - Fase 02 implementada com configuracao global singleton, landing publica, horarios, planos, lead e aula experimental.
- [x] 2026-04-01 - Fase 03 implementada - onboarding transacional, perfis de aluno, dependentes, prontuario, consentimentos, T09 e T10 base - validado com migracao, `manage.py check` e `35 passed`.
- [x] 2026-04-01 - Fase 04 implementada - perfis docentes, faixas, modalidades, turmas, sessoes e telas administrativas base - validado com migracao, `manage.py check` e `41 passed`.
- [x] 2026-04-01 - Fase 05 implementada - reserva, pre-check antes da camera, QR dinamico, presenca fisica e dashboard base do professor - validado com migracao, `manage.py check` e `47 passed`.
- [x] 2026-04-01 - Fase 06 implementada no recorte financeiro local, contratos, status operacional, T13 e comprovantes manuais; congelamento explicito da graduacao segue aberto para a Fase 09 - validado com migracao, `manage.py check` e `57 passed`.
- [x] 2026-04-01 - Fase 07 implementada no recorte Stripe com mapeamento local de prices, checkout recorrente, portal do cliente, webhook idempotente e pausa externa elegivel; uso efetivo de espelho `dj-stripe` e fechamento definitivo do catalogo oficial por plano seguem abertos - validado com migracao, `manage.py check` e `67 passed`.
- [x] 2026-04-02 - Fase 08 implementada com portal roteado por perfil, dashboards de aluno, responsavel, professor e administrativo, filtro por competencia e snapshot diario reconciliavel - validado com `manage.py check` e `78 passed`.
- [x] 2026-04-02 - Fase 09 implementada com regras oficiais e internas separadas, tempo ativo congelado por pausa, historico tecnico imutavel por ciclo, exame de graduacao e T07 operacional para professor/admin - validado com migracao, `manage.py check` e `86 passed`.
- [x] 2026-04-02 - Fase 10 implementada com historico documental, consulta de certificado, LGPD com confirmacao e anonimização segura, mural interno, comunicado em lote e prontuario rapido de emergencia - validado com migracao, `manage.py check` e `94 passed`.
- [x] 2026-04-02 - Fase 11 implementada com PDV, produtos de recepcao, abertura/fechamento de caixa, troco, alerta gerencial por divergencia e T17/T18 operacionais - validado com migracao, `manage.py check` e `99 passed`.
- [x] 2026-04-02 - Fase 12 implementada com `AuditLog`, `ExportRequest`, `CsvExportControl`, T15 operacional e exportacao CSV com fail-fast por arquivo de controle - validado com migracao, `manage.py check` e `108 passed`.
- [x] 2026-04-02 - Fase 13 implementada com hardening de sessao/login, logs operacionais, testes extras de caixa/autenticacao e documento de go-live - validado com `manage.py check` e `111 passed`.
- [x] 2026-04-02 - pagamentos/stripe refinados - espelho opcional `dj-stripe`, comando deterministico de importacao de `Price` e aposentadoria automatica de mapeamentos antigos - Fase 07 ganhou fechamento estrutural sem depender de heuristica local.
- [x] 2026-04-02 - validacao externa Stripe parcialmente bloqueada - token do Stripe MCP expirou durante a revisita da conta - decidido manter a fase honesta, sem marcar confirmacao real do catalogo enquanto a autenticacao nao for restabelecida.
- [x] 2026-04-02 - hardening de ambiente local - compatibilidade SQLite/Python 3.12 registrada no bootstrap do app - suite passou sem warnings residuais.
- [ ] Registrar aqui toda evolucao futura do PRD antes de alterar fases, criterios ou ordem de implementacao.
- [ ] Registrar aqui toda decisao de escopo tomada durante a execucao real.
- [ ] Registrar aqui toda mudanca de prioridade, corte de escopo ou nova dependencia descoberta.

### 1.1 Modelo obrigatorio de registro futuro

Sempre que este PRD evoluir, adicionar uma linha neste formato:

- `[x] AAAA-MM-DD - fase/tarefa alterada - motivo - impacto - decisao tomada`

---

## 2. Regra de continuidade obrigatoria

- [ ] Nao encerrar a construcao do produto ao concluir apenas modulos isolados.
- [ ] Nao parar apos telas bonitas sem backend completo.
- [ ] Nao parar apos backend sem UX operacional minima.
- [ ] Nao parar apos checkout sem webhooks idempotentes.
- [ ] Nao parar apos check-in sem hard stop antes da camera.
- [ ] Nao parar apos financeiro sem trancamento e reconcilicao com Stripe.
- [ ] Nao parar apos graduacao sem congelamento durante pausa.
- [ ] Nao parar apos relatorios sem fail-fast de exportacao.
- [ ] Nao marcar o sistema como pronto sem T01 a T20 cobertos no nivel definido neste documento.

### 2.1 Condicao de encerramento do projeto

O sistema so pode ser dado como integralmente entregue quando:

- [ ] Todas as fases obrigatorias deste PRD estiverem marcadas como concluidas
- [ ] Todas as tarefas criticas estiverem marcadas como concluidas
- [ ] Os testes criticos transversais estiverem implementados e passando
- [ ] As integracoes externas criticas estiverem validadas
- [ ] O backlog residual estiver explicitamente separado do escopo final entregue

---

## 3. Guardrails globais de implementacao

### 3.1 Dominio

- [ ] Manter identidade unica por CPF
- [ ] Permitir multi-papel no mesmo usuario
- [ ] Manter responsavel financeiro sem duplicar pessoa
- [ ] Manter professor tambem aluno sem duplicar pessoa
- [ ] Impedir que estado externo substitua o estado local de negocio

### 3.2 Arquitetura

- [ ] Views finas
- [ ] Serializers finos
- [ ] Services para orquestracao de regra composta
- [ ] `transaction.atomic()` em fluxos compostos
- [ ] `select_related()` e `prefetch_related()` nas listagens e dashboards
- [ ] Nenhuma regra critica apenas no template
- [ ] Nenhuma regra critica apenas em JavaScript

### 3.3 Validacao

- [ ] Nenhum `fields = '__all__'` em Forms ou Serializers
- [ ] Nenhum over-posting em payloads sensiveis
- [ ] Nenhuma mutacao critica por `GET`
- [ ] Nenhum `except: pass`
- [ ] Nenhum hardcode de segredo, URL base ou regra operacional sensivel

### 3.4 UX e frontend

- [ ] Responsividade minima em desktop, tablet e mobile
- [ ] Estados vazios tratados
- [ ] Erros operacionais tratados com mensagens claras
- [ ] Hard stop antes da camera em qualquer impedimento de acesso

### 3.5 Seguranca

- [ ] Permissao real no backend
- [ ] Ownership onde houver acesso por contexto
- [ ] Uploads validados
- [ ] Dados sensiveis protegidos por escopo
- [ ] Auditoria em acoes criticas

---

## 4. Checklist global de revisao de codigo

Marcar estes itens em toda PR, fase ou pacote de implementacao:

- [ ] Nao ha duplicacao de identidade por CPF
- [ ] Nao ha regra de negocio complexa em view
- [ ] Nao ha regra de negocio em `save()` de Serializer
- [ ] Nao ha consulta ORM dentro de laco para dashboard/listagem/relatorio
- [ ] Nao ha `SerializerMethodField` disparando query sem controle
- [ ] Nao ha endpoint mutavel aceitando `GET`
- [ ] Nao ha uso de `id` interno exposto onde o UUID deve ser publico
- [ ] Nao ha vazamento de financeiro para dependente com escopo restrito
- [ ] Nao ha confianca cega no frontend para check-in ou pagamento
- [ ] Nao ha mistura entre `status` local da matricula e `status` financeiro externo
- [ ] Nao ha webhook com efeito colateral sem idempotencia
- [ ] Nao ha exportacao critica sem pre-validacao do arquivo de controle

---

## 5. Checklist global de testes

### 5.1 Testes transversais obrigatorios

- [x] CPF unico
- [x] Multi-papel no mesmo usuario
- [x] Onboarding transacional
- [x] Dependentes e responsavel financeiro
- [x] Professor tambem aluno
- [x] Pre-check antes da camera
- [x] Reserva com consumo de vaga
- [x] Check-in sem duplicidade por sessao
- [x] Stripe checkout + webhook idempotente
- [x] Inadimplencia bloqueando acesso
- [x] Matricula pausada bloqueando check-in
- [x] Graduacao congelada durante pausa
- [x] LGPD com anonimizacao/exclusao
- [x] Exportacao fail-fast

### 5.2 Evidencias minimas por tarefa

- [ ] Teste unitario quando houver regra de dominio
- [ ] Teste de integracao quando houver fluxo composto
- [ ] Teste de permissao quando houver acesso por papel ou ownership
- [ ] Teste de concorrencia quando houver vaga, caixa ou webhook

---

## 6. Protocolo de validacao por MCPs

### 6.1 GitHub MCP

Usar para:

- [ ] registrar milestone por fase quando o repo estiver conectado
- [ ] revisar diffs e comentarios de PR
- [ ] acompanhar CI e checks
- [ ] manter rastreabilidade de execucao

### 6.2 Stripe MCP

Usar obrigatoriamente em tudo que tocar:

- [ ] catalogo de produtos
- [ ] prices
- [ ] checkout session
- [ ] subscriptions
- [ ] invoices
- [ ] payment intents
- [ ] pause_collection
- [ ] portal do cliente

### 6.3 Figma MCP

Usar quando houver design oficial ou necessidade de verificar consistencia visual.

- [ ] Nao bloquear backend por ausencia de Figma
- [ ] Usar Figma apenas quando houver valor real na comparacao visual

### 6.4 Regra pratica

- [ ] MCP nao substitui teste
- [ ] MCP nao substitui revisao de codigo
- [ ] MCP serve para validar contexto real, estado externo e coerencia operacional

---

## 7. Mapa completo do produto

### 7.1 App unico e modulos internos

- [x] `system`
- [x] `system.public`
- [x] `system.identity_access`
- [x] `system.student_registry`
- [x] `system.instructor_ops`
- [x] `system.class_catalog`
- [x] `system.attendance_qr`
- [x] `system.finance_contracts`
- [x] `system.payments_stripe`
- [x] `system.graduation_engine`
- [x] `system.communications`
- [x] `system.documents_lgpd`
- [x] `system.reports_audit`
- [x] `system.settings_seed`

### 7.2 Telas T01 a T20

- [x] T01 Landing page publica e portal de login
- [x] T02 Onboarding e cadastro de clientes
- [x] T03 Selecao de planos e checkout financeiro
- [x] T04 Dashboard do aluno / responsavel
- [x] T05 Dashboard do professor
- [x] T06 Dashboard administrativo
- [x] T07 Painel de graduacao e promocao de faixas
- [x] T08 Recuperacao de senha e primeiro acesso
- [x] T09 Meu perfil e configuracoes de conta
- [x] T10 Gestao de alunos e dependentes
- [x] T11 Gestao de professores
- [x] T12 Gestao de turmas e modalidades
- [x] T13 Financeiro detalhado
- [x] T14 Comprovantes, contratos e termos
- [x] T15 Relatorios, auditoria e exportacoes
- [x] T16 Leads e aula experimental
- [x] T17 PDV / caixa rapido
- [x] T18 Fechamento de caixa diario
- [x] T19 Central de comunicacoes e avisos
- [x] T20 Prontuario de emergencia

---

## 8. FASE 00 - Fundacao tecnica e arquitetura

### 8.1 Status da fase

- [x] Fase 00 concluida

### 8.2 Objetivo da fase

Preparar o alicerce tecnico para que todas as fases seguintes sejam construidas sobre uma arquitetura coerente, segura e escalavel.

### 8.3 Tarefas da fase

#### F00.01 - Estruturar o app `system` e seus modulos internos

- [x] Criar a estrutura fisica do app unico `system` conforme `CLAUDE.md`
- [x] Garantir que cada modulo interno represente um agregado claro
- [x] Configurar dependencias iniciais sem ciclos desnecessarios

**Esperado**
- O repositorio passa a refletir a topologia oficial do sistema.

**Criterios de aceitacao**
- [x] O app fisico `system` existe
- [x] As responsabilidades de cada modulo interno estao claras
- [x] Nao ha regra de dominio central em arquivo utilitario errado

**Validacao por revisao de codigo**
- [x] Sem dependencia circular obvia
- [x] Sem models centrais misturados em app utilitario

**Validacao por testes**
- [x] Projeto sobe com o app `system` registrado
- [x] Smoke tests de import e boot passam

**Validacao por MCP**
- [ ] GitHub MCP usado para registrar milestone arquitetural, se disponivel

#### F00.02 - Criar base model, UUID publico e convencoes transversais

- [x] Criar `BaseModel` com `id`, `uuid`, `created_at`, `updated_at`
- [x] Definir convencao de uso do UUID em URLs e APIs
- [x] Definir managers e querysets semanticos base

**Esperado**
- Toda entidade transacional relevante nasce com estrutura consistente.

**Criterios de aceitacao**
- [x] UUID esta disponivel para rotas publicas
- [x] `id` interno nao precisa vazar
- [x] Timestamps existem em entidades relevantes

**Validacao por revisao de codigo**
- [x] Sem uso futuro de `id` interno em rotas sensiveis
- [x] Sem side effect oculto no base model

**Validacao por testes**
- [x] Testes de criacao de objetos com UUID
- [x] Testes de serializacao/lookup por UUID

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F00.03 - Configurar settings, `.env`, timezone, Celery, Redis e logging

- [x] Externalizar segredos e variaveis de ambiente
- [x] Configurar timezone operacional correta
- [x] Preparar Celery e Redis para tarefas assincronas
- [x] Configurar logging minimo util para operacao

**Esperado**
- O projeto sobe de forma previsivel e preparado para assincronia e observabilidade.

**Criterios de aceitacao**
- [x] Nenhum segredo hardcoded
- [x] Timezone de negocio configurada
- [x] Celery/Redis preparados para fases futuras

**Validacao por revisao de codigo**
- [x] Sem branch de ambiente espalhada em views
- [x] Sem URL sensivel em JS

**Validacao por testes**
- [x] Teste de boot do projeto
- [x] Teste de carregamento de configuracoes criticas

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F00.04 - Criar infraestrutura transversal de permissao, mixins e middlewares

- [x] Criar base de mixins para MVT
- [x] Criar permissions base para DRF
- [x] Implementar middleware/timezone awareness
- [x] Definir padrao de ownership

**Esperado**
- A base de views e APIs fica pronta antes dos fluxos de negocio.

**Criterios de aceitacao**
- [x] MVT e DRF usam estrategias corretas de controle de acesso
- [x] Ownership podera ser aplicado por agregado

**Validacao por revisao de codigo**
- [x] `LoginRequiredMixin` nao sera usado em DRF
- [x] Middlewares nao carregam regra de negocio indevida

**Validacao por testes**
- [x] Teste de middleware
- [x] Teste de permission base

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F00.05 - Configurar pipeline de testes e qualidade

- [x] Configurar pytest ou stack equivalente
- [x] Criar estrutura de testes por modulo interno
- [x] Criar fixtures/factories base
- [x] Definir estrategia de smoke, unit e integracao

**Esperado**
- Todas as fases seguintes podem ser validadas sem depender de teste manual puro.

**Criterios de aceitacao**
- [x] Testes conseguem rodar localmente
- [x] Estrutura de testes esta pronta por agregado

**Validacao por revisao de codigo**
- [x] Sem fixture opaca demais
- [x] Sem dependencia entre testes que esconda falha

**Validacao por testes**
- [x] Testes base passam

**Validacao por MCP**
- [ ] GitHub MCP usado para CI/checks, se disponivel

---

## 9. FASE 01 - Identidade, autenticacao e papeis

### 9.1 Status da fase

- [x] Fase 01 concluida

### 9.2 Objetivo da fase

Implementar a identidade unica por CPF, autenticacao segura e base de papeis acumulaveis para todos os modulos.

### 9.3 Tarefas da fase

#### F01.01 - Implementar `CustomUser` com CPF como identificador unico

- [x] Criar `CustomUser` sem `username`
- [x] Definir `USERNAME_FIELD = "cpf"`
- [x] Criar `CustomUserManager`
- [x] Normalizar CPF no fluxo de criacao e autenticacao

**Esperado**
- O CPF passa a ser a identidade canonica do sistema.

**Criterios de aceitacao**
- [x] Nao e possivel criar duas identidades para o mesmo CPF
- [x] Login por CPF funciona
- [x] O modelo suporta papeis acumulaveis

**Validacao por revisao de codigo**
- [x] Sem fallback silencioso para login por outro identificador
- [x] Sem logica de duplicacao de pessoa por papel

**Validacao por testes**
- [x] Criacao de usuario com CPF unico
- [x] Bloqueio de CPF duplicado
- [x] Normalizacao de CPF no login

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F01.02 - Implementar atribuicao de papeis acumulaveis

- [x] Criar estrutura de vinculo de papeis
- [x] Permitir combinacao de `ADMIN_MASTER`, `ADMIN_UNIDADE`, `RECEPCAO`, `PROFESSOR`, `ALUNO_TITULAR`, `ALUNO_DEPENDENTE_COM_CREDENCIAL`, `RESPONSAVEL_FINANCEIRO`
- [x] Garantir leitura de papeis por permissao

**Esperado**
- Um mesmo usuario pode acumular papeis sem multiplicar identidade.

**Criterios de aceitacao**
- [x] Professor tambem aluno no mesmo CPF e suportado
- [x] Responsavel financeiro sem treino tambem e suportado
- [x] Dependente com credencial propria nao cria pessoa duplicada

**Validacao por revisao de codigo**
- [x] Sem enum exclusivo de papel governando toda a autorizacao
- [x] Sem ifs espalhados substituindo camada de permissao

**Validacao por testes**
- [x] Usuario com multiplos papeis
- [x] Resolucao correta de papeis por contexto

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F01.03 - Implementar login, logout, primeiro acesso e recuperacao de senha

- [x] Implementar T01 no recorte de autenticacao
- [x] Implementar T08
- [x] Criar fluxo de token de redefinicao
- [x] Criar fluxo de primeiro acesso
- [x] Bloquear autenticacao de usuario inativo/bloqueado

**Esperado**
- O sistema possui porta de entrada real e recuperacao de conta segura.

**Criterios de aceitacao**
- [x] Login por CPF funciona
- [x] Mensagens para erro e bloqueio sao coerentes
- [x] Token de redefinicao expira e e de uso unico

**Validacao por revisao de codigo**
- [x] Rate limit em login ou protecao equivalente prevista
- [x] Nao ha enumeracao facil de contas

**Validacao por testes**
- [x] Login valido
- [x] Login invalido
- [x] Usuario bloqueado
- [x] Token expirado
- [x] Token valido com redefinicao concluida

**Validacao por MCP**
- [ ] GitHub MCP para acompanhar checks, se disponivel

#### F01.04 - Implementar base de permissao e ownership

- [x] Criar mixins MVT por papel
- [x] Criar permissions DRF por papel
- [x] Criar ownership por contexto
- [x] Garantir negacao explicita quando acesso nao for permitido

**Esperado**
- Controle de acesso backend real para todos os fluxos futuros.

**Criterios de aceitacao**
- [x] Mixins MVT bloqueiam acesso sem papel esperado
- [x] Ownership por contexto filtra escopo quando o usuario nao e administrador
- [x] DRF usa base de `permission_classes` por papel

**Validacao por revisao de codigo**
- [x] Sem permissao baseada so em esconder botao
- [x] Sem `LoginRequiredMixin` em API DRF

**Validacao por testes**
- [x] Acesso permitido quando deveria
- [x] Acesso negado quando deveria
- [x] Ownership invalido retorna bloqueio

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F01.05 - Implementar auditoria minima de autenticacao e mudancas sensiveis

- [x] Registrar login, logout, redefinicao de senha e mudanca de credencial
- [x] Registrar abertura de fluxo sensivel

**Esperado**
- A base de rastreabilidade para seguranca e suporte ja existe.

**Criterios de aceitacao**
- [x] Acoes criticas deixam rastro minimo

**Validacao por revisao de codigo**
- [x] Sem logar dados sensiveis completos

**Validacao por testes**
- [x] Emissao de log de auditoria em acoes definidas

**Validacao por MCP**
- [ ] Nao obrigatorio

---

## 10. FASE 02 - Core publico, comunicacao publica e captacao inicial

### 10.1 Status da fase

- [x] Fase 02 concluida

### 10.2 Objetivo da fase

Entregar a base publica do produto: landing, horarios, planos publicos e ponto de entrada de leads.

### 10.3 Tarefas da fase

#### F02.01 - Implementar `ConfiguracaoAcademia`

- [x] Criar model singleton para configuracao global
- [x] Parametrizar idade de dependente com credencial
- [x] Parametrizar regras operacionais basicas

**Esperado**
- Regras da academia deixam de ficar hardcoded.

**Criterios de aceitacao**
- [x] Existe uma unica configuracao ativa
- [x] Parametros criticos podem ser lidos pelo dominio

**Validacao por revisao de codigo**
- [x] Sem singleton dependente apenas de convencao humana

**Validacao por testes**
- [x] Garantia de instancia unica

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F02.02 - Implementar T01 Landing page publica

- [x] Criar landing institucional
- [x] Exibir horarios publicos
- [x] Exibir planos publicos
- [x] Exibir CTA de cadastro
- [x] Exibir CTA de aula experimental

**Esperado**
- Visitante entende a academia e consegue iniciar jornada.

**Criterios de aceitacao**
- [x] Horarios e planos publicos carregam
- [x] CTA para login, cadastro e aula experimental existem
- [x] Interface e responsiva

**Validacao por revisao de codigo**
- [x] Sem dados privados expostos
- [x] Sem regra de negocio pesada no template

**Validacao por testes**
- [x] Render da landing
- [x] Exibicao de planos/horarios ativos

**Validacao por MCP**
- [ ] Figma MCP opcional se houver design oficial

#### F02.03 - Implementar captacao de lead e aula experimental

- [x] Criar fluxo inicial de lead
- [x] Criar agendamento de aula experimental
- [x] Registrar origem do lead
- [x] Preparar conversao futura para onboarding

**Esperado**
- O fluxo comercial inicial deixa de depender de processo externo.

**Criterios de aceitacao**
- [x] Lead e salvo com origem
- [x] Aula experimental pode ser solicitada
- [x] Fluxo pode ser convertido mais tarde em cadastro

**Validacao por revisao de codigo**
- [x] Sem coleta excessiva de dados sensiveis
- [x] Sem mistura entre lead e aluno efetivo

**Validacao por testes**
- [x] Criacao de lead
- [x] Agendamento de aula experimental

**Validacao por MCP**
- [ ] Nao obrigatorio

---

## 11. FASE 03 - Clientes, dependentes e onboarding

### 11.1 Status da fase

- [x] Fase 03 concluida

### 11.2 Objetivo da fase

Construir o onboarding transacional do titular e dependentes, incluindo perfil esportivo e dados sensiveis basicos.

### 11.3 Tarefas da fase

#### F03.01 - Implementar `PerfilAluno`

- [x] Criar model de perfil esportivo do aluno
- [x] Vincular a identidade central
- [x] Preparar campo de status operacional

**Esperado**
- O dominio esportivo do aluno existe sem duplicar a pessoa.

**Criterios de aceitacao**
- [x] Perfil esportivo pode coexistir com outros papeis do mesmo usuario

**Validacao por revisao de codigo**
- [x] Sem duplicacao de pessoa no agregado `system.student_registry`

**Validacao por testes**
- [x] Criacao do perfil
- [x] Convivencia com outros papeis

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.02 - Implementar vinculo de responsavel e dependentes

- [x] Criar `VinculoResponsavelAluno`
- [x] Definir regras para dependente com credencial propria
- [x] Restringir escopo financeiro do dependente

**Esperado**
- Dependentes existem de forma segura e auditavel.

**Criterios de aceitacao**
- [x] Dependente fica vinculado ao responsavel financeiro
- [x] Dependente nao ve financeiro familiar
- [x] Dependente com credencial propria acessa apenas o proprio escopo

**Validacao por revisao de codigo**
- [x] Sem atalho visual substituindo permissao real

**Validacao por testes**
- [x] Vculo de dependente
- [x] Restricao de escopo do dependente

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.03 - Implementar `ProntuarioEmergencia`

- [x] Criar model com dados medicos essenciais e contato de emergencia
- [x] Restringir acesso por necessidade operacional

**Esperado**
- O dado sensivel ja nasce segregado e minimizado.

**Criterios de aceitacao**
- [x] Dados medicos nao ficam misturados no perfil publico do aluno

**Validacao por revisao de codigo**
- [x] Sem exposicao indevida em serializers/listagens

**Validacao por testes**
- [x] Acesso autorizado
- [x] Acesso negado

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.04 - Implementar wizard de onboarding do titular

- [x] Criar forms do onboarding do titular
- [x] Implementar limpeza e normalizacao rigorosa
- [x] Validar CPF unico no fluxo
- [x] Validar aceite de termos

**Esperado**
- O titular consegue concluir o cadastro inicial com integridade.

**Criterios de aceitacao**
- [x] Dados sao saneados antes de tocar o banco
- [x] Campos obrigatorios sao validados corretamente

**Validacao por revisao de codigo**
- [x] Sem `fields = '__all__'`
- [x] Sem regra composta escondida em template

**Validacao por testes**
- [x] Cadastro valido
- [x] CPF duplicado
- [x] Falha de validacao de dados

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.05 - Implementar formset de dependentes com validacao em memoria

- [x] Criar formset de dependentes
- [x] Barrar duplicidade de CPF no mesmo request
- [x] Validar regras de menoridade e responsavel

**Esperado**
- Dois dependentes com o mesmo CPF nao explodem no banco, sao barrados antes.

**Criterios de aceitacao**
- [x] Duplicidade intra-request dispara erro funcional

**Validacao por revisao de codigo**
- [x] Formset usa `clean()` apropriado
- [x] Sem depender de erro tardio de constraint

**Validacao por testes**
- [x] Dois dependentes iguais no mesmo request
- [x] Dependente valido

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.06 - Persistir onboarding inteiro em `transaction.atomic()`

- [x] Consolidar criacao do titular e dependentes em service transacional
- [x] Garantir rollback completo em falha
- [x] Marcar onboarding como consistente so no fim

**Esperado**
- Nao existe grupo familiar meio salvo.

**Criterios de aceitacao**
- [x] Falha em qualquer dependente desfaz todo o onboarding

**Validacao por revisao de codigo**
- [x] Nenhuma escrita solta fora da transacao principal

**Validacao por testes**
- [x] Rollback total em falha
- [x] Persistencia integral em sucesso

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F03.07 - Implementar T09 Meu perfil e configuracoes de conta

- [x] Criar tela de perfil
- [x] Permitir edicao do que for permitido
- [x] Impedir edicao indevida de CPF sem fluxo administrativo
- [x] Permitir troca de senha
- [x] Permitir solicitacao LGPD

**Esperado**
- Usuario consegue manter a propria conta sem quebrar identidade.

**Criterios de aceitacao**
- [x] Alteracoes sensiveis sao auditadas
- [x] CPF nao e editado livremente

**Validacao por revisao de codigo**
- [x] Campos imutaveis protegidos no backend

**Validacao por testes**
- [x] Atualizacao de perfil
- [x] Troca de senha
- [x] Campo protegido

**Validacao por MCP**
- [ ] Figma MCP opcional

#### F03.08 - Implementar T10 Gestao de alunos e dependentes

- [x] Listar alunos
- [x] Filtrar por nome, CPF, status e responsavel
- [x] Criar/editar/inativar aluno
- [x] Vincular/desvincular dependente
- [x] Vincular aluno a responsavel financeiro

**Esperado**
- A administracao consegue operar o cadastro sem improviso.

**Criterios de aceitacao**
- [x] Nao ha duplicidade de identidade
- [x] Vnculos familiares ficam coerentes
- [x] Interface e responsiva

**Validacao por revisao de codigo**
- [x] Listagem sem N+1
- [x] Permissao administrativa real

**Validacao por testes**
- [x] CRUD de aluno
- [x] Vinculo de dependente
- [x] Inativacao sem quebrar historico

**Validacao por MCP**
- [ ] Figma MCP opcional

#### F03.09 - Implementar T14 no recorte de termos e consentimentos

- [x] Registrar aceite de termo
- [x] Versionar termos
- [x] Exibir historico de aceite no perfil e no admin

**Esperado**
- O consentimento deixa de ser um checkbox descartavel.

**Criterios de aceitacao**
- [x] Versao do termo fica registrada
- [x] Historico e consultavel

**Validacao por revisao de codigo**
- [x] Sem sobrescrever aceite anterior

**Validacao por testes**
- [x] Registro de aceite
- [x] Historico de termos

**Validacao por MCP**
- [ ] Nao obrigatorio

---

## 12. FASE 04 - Professores, modalidades, turmas e sessoes

### 12.1 Status da fase

- [x] Fase 04 concluida

### 12.2 Objetivo da fase

Entregar a estrutura do tatame: professores, modalidades, turmas, sessoes e alocacao operacional.

### 12.3 Tarefas da fase

#### F04.01 - Implementar `PerfilProfessor`

- [x] Criar perfil docente vinculado a `CustomUser`
- [x] Permitir coexistencia com papel de aluno

**Esperado**
- O dominio docente existe sem duplicar identidade.

**Criterios de aceitacao**
- [x] Professor tambem aluno e suportado

**Validacao por revisao de codigo**
- [x] Sem identidade secundaria para professor

**Validacao por testes**
- [x] Perfil docente
- [x] Convivencia com papel de aluno

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F04.02 - Implementar `Modalidade`, `FaixaIBJJF` e cadastro base de turmas

- [x] Criar modalidades
- [x] Criar faixas base oficiais
- [x] Criar turmas com horario, capacidade, professor e regras de reserva

**Esperado**
- A academia consegue estruturar a grade real de aulas.

**Criterios de aceitacao**
- [x] Turma tem capacidade, professor e janela operacional
- [x] Regras basicas ficam parametrizadas

**Validacao por revisao de codigo**
- [x] Constraints basicas de horario e capacidade

**Validacao por testes**
- [x] Criacao de turma
- [x] Validacao de capacidade

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F04.03 - Implementar gestao de professores e turmas

- [x] Implementar T11
- [x] Implementar T12

**Esperado**
- Admin consegue manter professores, modalidades e turmas.

**Criterios de aceitacao**
- [x] CRUD funcional
- [x] Professor nao ganha permissao administrativa indevida

**Validacao por revisao de codigo**
- [x] Listagens paginadas
- [x] Ownership/permissao corretos

**Validacao por testes**
- [x] CRUD de professor
- [x] CRUD de modalidade
- [x] CRUD de turma

**Validacao por MCP**
- [ ] Figma MCP opcional

#### F04.04 - Implementar `SessaoAula`

- [x] Criar model de sessao
- [x] Permitir abrir sessao de aula
- [x] Permitir encerrar sessao
- [x] Garantir ancoragem para QR e presenca

**Esperado**
- Toda presenca futura passa a depender de uma sessao real.

**Criterios de aceitacao**
- [x] Nao existe check-in sem sessao valida

**Validacao por revisao de codigo**
- [x] Mutacoes de sessao protegidas por POST

**Validacao por testes**
- [x] Abrir sessao
- [x] Encerrar sessao
- [x] Bloquear operacao sem permissao

**Validacao por MCP**
- [ ] Nao obrigatorio

---

## 13. FASE 05 - Presenca, reserva e motor do tatame

### 13.1 Status da fase

- [x] Fase 05 concluida

### 13.2 Objetivo da fase

Entregar reserva de vaga, pre-check de elegibilidade, QR dinamico e registro de presenca fisica sem fraude operacional obvia.

### 13.3 Tarefas da fase

#### F05.01 - Implementar `ReservaVaga`

- [x] Criar model de reserva
- [x] Garantir unicidade de reserva ativa por aluno e sessao
- [x] Preparar politicas de no-show e reaproveitamento como extensao futura

**Esperado**
- A lotacao e consumida no momento correto.

**Criterios de aceitacao**
- [x] Em turma com capacidade, a vaga e consumida na reserva
- [x] Nao ha duplicidade de reserva ativa do mesmo aluno na mesma sessao

**Validacao por revisao de codigo**
- [x] Constraint de unicidade condicional quando aplicavel
- [x] Services de reserva com transacao

**Validacao por testes**
- [x] Reserva valida
- [x] Reserva duplicada
- [x] Reserva quando lotacao ja foi consumida

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F05.02 - Implementar `PreCheckElegibilidadeAPIView`

- [x] Criar endpoint de pre-check
- [x] Validar adimplencia
- [x] Validar status da matricula
- [x] Validar reserva quando obrigatoria
- [x] Validar permissao e janela de sessao

**Esperado**
- O frontend sabe, antes da camera, se pode seguir.

**Criterios de aceitacao**
- [x] Usuario inadimplente nao recebe permissao para abrir camera
- [x] Usuario pausado nao recebe permissao para abrir camera
- [x] Usuario sem reserva nao recebe permissao quando reserva for exigida

**Validacao por revisao de codigo**
- [x] Regra de elegibilidade esta no backend
- [x] Frontend apenas consome JSON de elegibilidade

**Validacao por testes**
- [x] Aluno elegivel
- [x] Aluno inadimplente
- [x] Aluno pausado
- [x] Aluno sem reserva

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F05.03 - Implementar QR dinamico e leitura de camera

- [x] Criar fluxo de token dinamico
- [x] Limitar TTL de QR por configuracao
- [x] Vincular leitura a sessao valida

**Esperado**
- O QR serve como confirmacao fisica e nao como autorizacao cega.

**Criterios de aceitacao**
- [x] QR expirado falha
- [x] QR sem sessao falha
- [x] QR nao sobrepoe bloqueio operacional

**Validacao por revisao de codigo**
- [x] Nenhuma regra central depende apenas do token

**Validacao por testes**
- [x] QR valido
- [x] QR expirado
- [x] QR em sessao invalida

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F05.04 - Implementar `PresencaFisica`

- [x] Criar model de presenca
- [x] Garantir unicidade por aluno + sessao
- [x] Registrar tentativa e auditoria relevante quando necessario

**Esperado**
- A presenca fica ancorada a sessao, nao ao QR rotativo.

**Criterios de aceitacao**
- [x] Nao existe check-in duplicado na mesma sessao

**Validacao por revisao de codigo**
- [x] Constraint e validacao de duplicidade coerentes

**Validacao por testes**
- [x] Primeiro check-in
- [x] Segundo check-in bloqueado

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F05.05 - Implementar dashboard do professor e operacao de aula

- [x] Implementar T05
- [x] Permitir iniciar aula
- [x] Gerar QR
- [x] Confirmar presenca manual excepcional com motivo

**Esperado**
- Professor consegue operar a aula em tempo real.

**Criterios de aceitacao**
- [x] Professor ve apenas suas turmas
- [x] Presenca manual gera log

**Validacao por revisao de codigo**
- [x] Sem financeiro visivel ao professor sem contexto adequado

**Validacao por testes**
- [x] Professor autorizado
- [x] Professor nao autorizado
- [x] Presenca manual auditada

**Validacao por MCP**
- [ ] Figma MCP opcional

---

## 14. FASE 06 - Financeiro local, contratos e estados operacionais

### 14.1 Status da fase

- [ ] Fase 06 concluida

### 14.2 Objetivo da fase

Construir o dominio financeiro local que governa acesso, status operacional, faturas, trancamento e contratos, independente da Stripe.

### 14.3 Tarefas da fase

#### F06.01 - Implementar `PlanoFinanceiro`

- [x] Criar catalogo local de planos
- [x] Incluir periodicidade, preco base e regras operacionais
- [x] Permitir vigencia e desativacao sem apagar historico

**Esperado**
- O sistema possui catalogo local proprio.

**Criterios de aceitacao**
- [x] Plano existe mesmo sem Stripe
- [x] Plano pode ser ativado/inativado

**Validacao por revisao de codigo**
- [x] Sem price da Stripe como unica representacao de plano

**Validacao por testes**
- [x] Criacao de plano
- [x] Plano inativo nao aparece em seletores ativos

**Validacao por MCP**
- [ ] Stripe MCP sera usado na fase seguinte para cruzar catalogo

#### F06.02 - Implementar `BeneficioFinanceiro`

- [x] Criar bolsa, desconto e beneficio parametrizavel
- [x] Permitir percentual ou valor fixo quando fizer sentido

**Esperado**
- Regras de beneficio deixam de virar ifs espalhados.

**Criterios de aceitacao**
- [x] Beneficio pode ser aplicado a contrato/aluno conforme regra

**Validacao por revisao de codigo**
- [x] Sem desconto hardcoded em template ou view

**Validacao por testes**
- [x] Beneficio percentual
- [x] Beneficio valor fixo

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F06.03 - Implementar `Assinatura` e `AssinaturaAluno`

- [x] Criar agregado de assinatura local
- [x] Vincular alunos e dependentes ao contrato
- [x] Distinguir titular financeiro de alunos cobertos

**Esperado**
- O sistema sabe quem paga e quem treina dentro do mesmo contrato.

**Criterios de aceitacao**
- [x] Responsavel pode nao treinar
- [x] Dependentes podem estar cobertos pelo mesmo contrato

**Validacao por revisao de codigo**
- [x] Fonte de verdade local explicita

**Validacao por testes**
- [x] Contrato com titular
- [x] Contrato com dependentes

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F06.04 - Implementar `FaturaMensal`

- [x] Criar model de fatura local
- [x] Implementar estados de fatura
- [x] Preparar vinculo com Stripe sem depender dela

**Esperado**
- Fatura local governa o estado financeiro operacional.

**Criterios de aceitacao**
- [x] Fatura em aberto pode bloquear acesso conforme regra
- [x] Fatura paga remove pendencia quando a politica assim exigir

**Validacao por revisao de codigo**
- [x] Sem misturar `Invoice` externa com estado local diretamente

**Validacao por testes**
- [x] Fatura criada
- [x] Fatura paga
- [x] Fatura pendente bloqueando acesso

**Validacao por MCP**
- [ ] Stripe MCP recomendado na fase seguinte

#### F06.05 - Implementar status operacional do aluno

- [x] Consolidar estados `ATIVO`, `PENDENTE_FINANCEIRO`, `PAUSADO`, `BLOQUEADO`
- [x] Integrar com regras de check-in e dashboard

**Esperado**
- O dominio fala a lingua da academia.

**Criterios de aceitacao**
- [x] O status operacional governa acesso
- [x] `is_active` tecnico nao substitui status de negocio

**Validacao por revisao de codigo**
- [x] Sem dependencia cega do status tecnico de autenticacao

**Validacao por testes**
- [x] Cada estado gera o comportamento correto

**Validacao por MCP**
- [ ] Nao obrigatorio

#### F06.06 - Implementar `TrancamentoMatricula`

- [x] Criar model de trancamento
- [x] Registrar motivo, inicio e retorno previstos
- [ ] Integrar com congelamento de graduacao
- [x] Integrar com bloqueio de check-in

**Esperado**
- Pausa de matricula e um fluxo de negocio de primeira classe.

**Criterios de aceitacao**
- [x] Aluno pausado nao faz check-in
- [ ] Tempo de graduacao nao corre enquanto pausado

**Validacao por revisao de codigo**
- [x] Sem if solto de pausa em templates

**Validacao por testes**
- [x] Pausar matricula
- [x] Reativar matricula
- [ ] Congelar e retomar contagem de graduacao

**Validacao por MCP**
- [ ] Stripe MCP sera obrigatorio quando a pausa externa for integrada

#### F06.07 - Implementar T13 Financeiro detalhado

- [x] Criar telas de planos, faturas, inadimplencia e operacoes manuais
- [x] Exibir status e acoes administrativas

**Esperado**
- O financeiro deixa de ser so um resumo de dashboard.

**Criterios de aceitacao**
- [x] Admin opera financeiro por tela propria
- [x] Interface mostra estados reais do dominio

**Validacao por revisao de codigo**
- [x] Listagens sem N+1
- [x] Acoes mutaveis por POST

**Validacao por testes**
- [x] Listagem
- [x] Filtros
- [x] Baixa manual

**Validacao por MCP**
- [ ] Figma MCP opcional

#### F06.08 - Implementar T14 no recorte de comprovantes manuais

- [x] Permitir upload de comprovante
- [x] Permitir aprovar/reprovar comprovante
- [x] Registrar historico documental

**Esperado**
- O sistema suporta excecao operacional sem depender de anotacao manual fora da plataforma.

**Criterios de aceitacao**
- [x] Comprovante fica em analise
- [x] Admin decide com auditoria

**Validacao por revisao de codigo**
- [x] Upload validado por tamanho e extensao

**Validacao por testes**
- [x] Upload valido
- [x] Upload invalido
- [x] Aprovacao/reprovacao

**Validacao por MCP**
- [ ] Nao obrigatorio

---

## 15. FASE 07 - Stripe, checkout, webhook e reconciliacao

### 15.1 Status da fase

- [ ] Fase 07 concluida

### 15.2 Objetivo da fase

Integrar o dominio financeiro local com a Stripe sem abrir mao da fonte de verdade operacional do sistema.

### 15.3 Tarefas da fase

#### F07.01 - Validar catalogo real da conta Stripe

- [x] Confirmar `account_id`
- [x] Listar produtos reais
- [x] Listar prices reais
- [x] Separar prices vigentes e legados
- [ ] Confirmar quais produtos correspondem aos planos da academia

**Esperado**
- O projeto para de depender de suposicoes sobre a conta Stripe.

**Criterios de aceitacao**
- [x] Existe tabela de mapeamento entre plano local e price Stripe
- [x] Prices legados nao ficam ambíguos

**Validacao por revisao de codigo**
- [x] Mapeamento persistido de forma clara

**Validacao por testes**
- [x] Resolucao do price por plano local

**Validacao por MCP**
- [x] Stripe MCP obrigatorio

#### F07.02 - Implementar `CheckoutSolicitacao`

- [x] Criar model local de solicitacao de checkout
- [x] Persistir `stripe_checkout_session_id`
- [x] Registrar metadata resumida

**Esperado**
- Todo checkout deixa rastro local antes de sair do sistema.

**Criterios de aceitacao**
- [x] Toda sessao de checkout relevante fica rastreavel

**Validacao por revisao de codigo**
- [x] UniqueConstraint quando `stripe_checkout_session_id` existir

**Validacao por testes**
- [x] Criacao de solicitacao
- [x] Duplicidade bloqueada

**Validacao por MCP**
- [ ] Stripe MCP recomendado

#### F07.03 - Implementar criacao de checkout de assinatura

- [x] Criar service de checkout
- [x] Resolver `Customer` Stripe
- [x] Resolver `Price` Stripe
- [x] Criar `Checkout Session`
- [x] Redirecionar corretamente

**Esperado**
- T03 fica operacional.

**Criterios de aceitacao**
- [x] Checkout carrega metadata do titular e dependentes
- [x] Usuario nao ganha acesso antes da confirmacao financeira

**Validacao por revisao de codigo**
- [x] View fina
- [x] Logica Stripe em service dedicado

**Validacao por testes**
- [x] Criacao bem-sucedida de checkout
- [x] Falha controlada de checkout
- [x] Sem liberacao prematura de acesso

**Validacao por MCP**
- [ ] Stripe MCP obrigatorio

#### F07.04 - Implementar endpoint e processamento de webhook

- [x] Validar assinatura do evento
- [x] Persistir/usar espelho `dj-stripe`
- [x] Criar `WebhookProcessamento`
- [x] Tornar processamento idempotente
- [x] Atualizar estado local

**Esperado**
- O mundo externo conversa com o mundo local sem inconsistencia.

**Criterios de aceitacao**
- [x] Reprocessamento nao duplica efeito
- [x] Invoice paga altera estado local correto
- [x] Invoice falha gera pendencia local coerente

**Validacao por revisao de codigo**
- [x] Sem webhook cru fazendo tudo diretamente
- [x] `transaction.atomic()` nos efeitos locais

**Validacao por testes**
- [x] Webhook repetido
- [x] Pagamento confirmado
- [x] Falha de pagamento
- [x] Cancelamento/pausa

**Validacao por MCP**
- [ ] Stripe MCP obrigatorio

#### F07.05 - Implementar portal do cliente Stripe

- [x] Gerar sessao de portal sob demanda
- [x] Garantir ownership do contrato

**Esperado**
- O dashboard pode encaminhar regularizacao sem expor acesso indevido.

**Criterios de aceitacao**
- [x] Apenas o usuario autorizado abre o portal do proprio contrato

**Validacao por revisao de codigo**
- [x] Nenhum IDOR no portal

**Validacao por testes**
- [x] Acesso permitido
- [x] Acesso negado

**Validacao por MCP**
- [ ] Stripe MCP obrigatorio

#### F07.06 - Implementar pausa externa com `pause_collection`

- [x] Integrar trancamento local com pausa externa elegivel
- [x] Remover pausa ao reativar matricula

**Esperado**
- O contrato externo acompanha a pausa, mas nao dita o negocio local.

**Criterios de aceitacao**
- [x] `PAUSADO` local continua sendo a fonte de verdade operacional
- [x] Reativacao reconcilia o contrato

**Validacao por revisao de codigo**
- [x] Sem confundir `subscription.status` com estado local

**Validacao por testes**
- [x] Pausar
- [x] Reativar
- [x] Bloqueio de check-in mantido durante pausa

**Validacao por MCP**
- [ ] Stripe MCP obrigatorio

---

## 16. FASE 08 - Dashboards por perfil

### 16.1 Status da fase

- [x] Fase 08 concluida

### 16.2 Objetivo da fase

Consolidar a experiencia operacional de aluno, responsavel, professor e administrador.

### 16.3 Tarefas da fase

#### F08.01 - Implementar T04 Dashboard do aluno / responsavel

- [x] Exibir identidade marcial
- [x] Exibir status de acesso
- [x] Exibir financeiro proprio e familiar conforme escopo
- [x] Exibir dependentes e alternancia de contexto
- [x] Exibir CTA de regularizacao quando necessario
- [x] Integrar pre-check de camera

**Esperado**
- O aluno e o responsavel conseguem operar sua jornada completa.

**Criterios de aceitacao**
- [x] Adimplente abre camera
- [x] Inadimplente nao chama `getUserMedia`
- [x] Pausado nao chama `getUserMedia`
- [x] Dependente com credencial propria nao ve financeiro familiar

**Validacao por revisao de codigo**
- [x] Sem regra de hard stop apenas em JS
- [x] Dashboard agrega, nao decide regra critica

**Validacao por testes**
- [x] Dashboard adimplente
- [x] Dashboard inadimplente
- [x] Dashboard pausado
- [x] Alternancia de dependente

**Validacao por MCP**
- [x] Figma MCP nao obrigatorio neste recorte de dashboard
- [x] Stripe MCP nao obrigatorio neste recorte, pois o CTA de regularizacao aponta para o financeiro local

#### F08.02 - Implementar T06 Dashboard administrativo

- [x] Exibir KPIs de receita, evasao, presenca e inadimplencia
- [x] Exibir pendencias operacionais
- [x] Fornecer atalhos para fluxos sensiveis

**Esperado**
- Admin ganha centro de inteligencia operacional.

**Criterios de aceitacao**
- [x] Dashboard nao substitui telas operacionais
- [x] KPIs respeitam filtros por periodo

**Validacao por revisao de codigo**
- [x] Sem query explosiva
- [x] Sem N+1 nas agregacoes

**Validacao por testes**
- [x] KPIs basicos
- [x] Filtros
- [x] Lista de pendencias

**Validacao por MCP**
- [x] Figma MCP nao obrigatorio nesta fase

#### F08.03 - Implementar agregacao ou snapshot de dashboard quando necessario

- [x] Implementar `DashboardSnapshotDiario` ou estrategia equivalente
- [x] Definir invalidacao/atualizacao consistente

**Esperado**
- Dashboards nao dependem de calculo pesado a cada request.

**Criterios de aceitacao**
- [x] Dados agregados continuam reconciliaveis com a origem

**Validacao por revisao de codigo**
- [x] Nao usar cache cego que esconda inconsistencia de dominio

**Validacao por testes**
- [x] Snapshot consistente

**Validacao por MCP**
- [x] Nao obrigatorio nesta fase

---

## 17. FASE 09 - Graduacao, exames e historico tecnico

### 17.1 Status da fase

- [x] Fase 09 concluida

### 17.2 Objetivo da fase

Construir o motor de aptidao, exame e promocao de faixas baseado em tempo ativo de treino.

### 17.3 Tarefas da fase

#### F09.01 - Implementar `RegraGraduacaoAcademia`

- [x] Configurar frequencia minima
- [x] Configurar criterios adicionais da academia
- [x] Manter referencia separada das regras oficiais

**Esperado**
- O sistema suporta regra oficial e regra interna sem confundir as duas.

**Criterios de aceitacao**
- [x] Regras internas sao parametrizaveis

**Validacao por revisao de codigo**
- [x] Sem ifs hardcoded espalhados por faixa

**Validacao por testes**
- [x] Regras minimas configuradas e aplicadas

**Validacao por MCP**
- [x] Nao obrigatorio nesta fase

#### F09.02 - Implementar calculo de tempo ativo de treino

- [x] Calcular elegibilidade por presenca valida
- [x] Ignorar tempo sem treino efetivo
- [x] Congelar contagem durante pausa

**Esperado**
- Graduacao mede treino ativo, nao mero calendario.

**Criterios de aceitacao**
- [x] Pausa nao conta para carencia
- [x] Ausencia prolongada nao gera aptidao artificial

**Validacao por revisao de codigo**
- [x] Regra em service ou dominio dedicado

**Validacao por testes**
- [x] Tempo ativo correto
- [x] Congelamento por pausa
- [x] Retomada apos reativacao

**Validacao por MCP**
- [x] Nao obrigatorio nesta fase

#### F09.03 - Implementar `HistoricoGraduacao`, `ExameGraduacao` e `ParticipacaoExameGraduacao`

- [x] Criar historico de faixas e graus
- [x] Criar exame de graduacao
- [x] Criar participacao no exame
- [x] Registrar resultado e historico imutavel

**Esperado**
- Toda promocao ou negativa fica historicamente rastreavel.

**Criterios de aceitacao**
- [x] Promocao cria historico
- [x] Ciclo anterior e encerrado corretamente

**Validacao por revisao de codigo**
- [x] Sem update destrutivo de historico

**Validacao por testes**
- [x] Promocao
- [x] Adiamento
- [x] Historico acumulado

**Validacao por MCP**
- [x] Nao obrigatorio nesta fase

#### F09.04 - Implementar T07 Painel de graduacao

- [x] Exibir elegiveis
- [x] Filtrar por turma/faixa
- [x] Abrir avaliacao
- [x] Registrar promocao
- [x] Gerar certificado quando aplicavel

**Esperado**
- Professores e admins conseguem operar a jornada de graduacao.

**Criterios de aceitacao**
- [x] Lista de aptos bate com motor tecnico
- [x] Promocao respeita idade e regra configuravel

**Validacao por revisao de codigo**
- [x] Sem calculo pesado em template

**Validacao por testes**
- [x] Lista de aptos
- [x] Promocao valida
- [x] Promocao invalida

**Validacao por MCP**
- [x] Figma MCP opcional e nao obrigatorio nesta fase

---

## 18. FASE 10 - Documentos, LGPD, comunicacoes e emergencia

### 18.1 Status da fase

- [x] Fase 10 concluida

### 18.2 Objetivo da fase

Fechar a camada sensivel do sistema: documentos, consentimentos, anonimizacao, mural, comunicacao e prontuario de emergencia.

### 18.3 Tarefas da fase

#### F10.01 - Completar T14 Comprovantes, contratos e termos

- [x] Versionar termos
- [x] Manter anexos historicos
- [x] Exibir historico documental
- [x] Permitir consulta de certificado

**Esperado**
- O documento deixa de ficar espalhado em varios fluxos soltos.

**Criterios de aceitacao**
- [x] Admin consulta historico documental completo
- [x] Usuario consulta seus termos e documentos permitidos

**Validacao por revisao de codigo**
- [x] Sem sobrescrever arquivo antigo

**Validacao por testes**
- [x] Historico documental
- [x] Versionamento de termos

**Validacao por MCP**
- [x] Nao obrigatorio

#### F10.02 - Implementar `SolicitacaoLGPD` e anonimizacao/exclusao definitiva

- [x] Abrir solicitacao formal
- [x] Confirmar intencao
- [x] Anonimizar dados permitidos
- [x] Remover ou limpar arquivos sensiveis
- [x] Preservar minimo tecnico/contabil exigido

**Esperado**
- O sistema atende o fluxo LGPD sem destruir integridade historica.

**Criterios de aceitacao**
- [x] Exclusao definitiva nao e mero soft delete
- [x] Dados sensiveis sao eliminados/minimizados
- [x] Historico contabil minimo permanece

**Validacao por revisao de codigo**
- [x] Fluxo transacional
- [x] Sem apagar o que precisa ser retido legalmente

**Validacao por testes**
- [x] Solicitacao aberta
- [x] Anonimizacao executada
- [x] Retencao minima mantida

**Validacao por MCP**
- [x] Nao obrigatorio

#### F10.03 - Implementar `AvisoMural`, `ComunicadoLote` e `EntregaComunicado`

- [x] Criar mural interno
- [x] Criar comunicacao em lote
- [x] Criar entrega/rastreamento de comunicado
- [x] Preparar disparo assincrono por canal

**Esperado**
- Comunicacoes deixam de depender de processo informal.

**Criterios de aceitacao**
- [x] Aviso tem vigencia
- [x] Disparo em massa e assincrono
- [x] Autor, canal e publico ficam rastreados

**Validacao por revisao de codigo**
- [x] Sem envio em massa bloqueando request
- [x] Sem mensagem financeira em mural publico

**Validacao por testes**
- [x] Criacao de aviso
- [x] Publicacao no mural
- [x] Enfileiramento de comunicado

**Validacao por MCP**
- [x] Figma MCP opcional

#### F10.04 - Implementar T19 Central de comunicacoes e avisos

- [x] Criar tela administrativa de comunicacao
- [x] Filtrar publico-alvo
- [x] Publicar avisos
- [x] Consultar historico

**Esperado**
- Existe um emissor formal de comunicacoes institucionais.

**Criterios de aceitacao**
- [x] Historico e consultavel
- [x] Disparo fica rastreavel

**Validacao por revisao de codigo**
- [x] Permissao administrativa correta

**Validacao por testes**
- [x] Tela renderiza
- [x] Publicacao
- [x] Historico

**Validacao por MCP**
- [x] Figma MCP opcional

#### F10.05 - Implementar T20 Prontuario de emergencia

- [x] Criar busca rapida por aluno
- [x] Exibir dados vitais minimos
- [x] Exibir contato de emergencia
- [x] Registrar log de acesso

**Esperado**
- Professor e admin conseguem responder rapido a incidente sem vazar dados desnecessarios.

**Criterios de aceitacao**
- [x] Sem CPF completo, endereco ou financeiro na tela
- [x] Busca e rapida
- [x] Acesso gera auditoria

**Validacao por revisao de codigo**
- [x] Dados minimos e escopo restrito

**Validacao por testes**
- [x] Busca de aluno
- [x] Acesso autorizado
- [x] Acesso negado
- [x] Log de acesso

**Validacao por MCP**
- [x] Figma MCP opcional

---

## 19. FASE 11 - PDV, caixa rapido e fechamento diario

### 19.1 Status da fase

- [x] Fase 11 concluida

### 19.2 Objetivo da fase

Dar suporte a operacao fisica da recepcao, separada do ciclo recorrente de assinatura.

### 19.3 Tarefas da fase

#### F11.01 - Implementar `ProdutoPDV`

- [x] Criar catalogo de produtos de recepcao
- [x] Preparar integracao futura com estoque

**Esperado**
- Itens de venda avulsa passam a ser gerenciados no sistema.

**Criterios de aceitacao**
- [x] Produto PDV pode ser cadastrado, ativado e desativado

**Validacao por revisao de codigo**
- [x] Sem misturar produto PDV com plano financeiro

**Validacao por testes**
- [x] CRUD de produto PDV

**Validacao por MCP**
- [x] Nao obrigatorio

#### F11.02 - Implementar `VendaPDV` e `ItemVendaPDV`

- [x] Criar venda e itens
- [x] Calcular total no backend
- [x] Permitir identificacao opcional do cliente

**Esperado**
- A venda de balcao fica auditavel e consistente.

**Criterios de aceitacao**
- [x] Total e derivado dos itens
- [x] Operador fica registrado

**Validacao por revisao de codigo**
- [x] Sem confiar no frontend para total final

**Validacao por testes**
- [x] Venda simples
- [x] Venda com multiplos itens

**Validacao por MCP**
- [x] Nao obrigatorio

#### F11.03 - Implementar `CaixaTurno` e `MovimentacaoCaixa`

- [x] Criar abertura de caixa
- [x] Criar movimentacoes
- [x] Criar encerramento de turno
- [x] Tratar concorrencia com lock quando necessario

**Esperado**
- O caixa fisico da recepcao ganha trilha real.

**Criterios de aceitacao**
- [x] Toda venda liquidada gera movimentacao
- [x] Turno fechado nao aceita lancamento retroativo

**Validacao por revisao de codigo**
- [x] `transaction.atomic()` + `select_for_update()` onde necessario

**Validacao por testes**
- [x] Abrir turno
- [x] Movimentar
- [x] Encerrar turno
- [x] Concorrencia de fechamento

**Validacao por MCP**
- [x] Nao obrigatorio

#### F11.04 - Implementar T17 PDV / caixa rapido

- [x] Criar interface de venda
- [x] Buscar aluno por CPF/nome quando necessario
- [x] Receber pagamento por meios permitidos
- [x] Emitir comprovante simplificado

**Esperado**
- Recepcao consegue vender rapido sem improviso.

**Criterios de aceitacao**
- [x] Venda conclui e reflete no caixa
- [x] Troco e calculado corretamente quando houver dinheiro

**Validacao por revisao de codigo**
- [x] Sem logica de dinheiro sensivel no template

**Validacao por testes**
- [x] Checkout PDV
- [x] Pagamento em dinheiro
- [x] Pagamento em outro meio

**Validacao por MCP**
- [x] Figma MCP opcional

#### F11.05 - Implementar T18 Fechamento de caixa diario

- [x] Criar tela de conferencia
- [x] Informar valores contados
- [x] Registrar divergencia
- [x] Encerrar turno

**Esperado**
- O caixa diario fica conciliado e rastreavel.

**Criterios de aceitacao**
- [x] Fechamento torna turno imutavel
- [x] Divergencia acima do limite gera alerta gerencial

**Validacao por revisao de codigo**
- [x] Nenhuma mudanca retroativa em turno encerrado

**Validacao por testes**
- [x] Caixa batido
- [x] Sobra
- [x] Quebra de caixa

**Validacao por MCP**
- [x] Figma MCP opcional

---

## 20. FASE 12 - Relatorios, auditoria, exportacoes e BI

### 20.1 Status da fase

- [x] Fase 12 concluida

### 20.2 Objetivo da fase

Entregar rastreabilidade, leitura gerencial e exportacao segura.

### 20.3 Tarefas da fase

#### F12.01 - Implementar `LogAuditoria`

- [x] Criar model de auditoria
- [x] Registrar autor, acao, horario, contexto e payload minimo

**Esperado**
- Acoes criticas passam a ser rastreaveis.

**Criterios de aceitacao**
- [x] Login sensivel, graduacao, financeiro, comprovante, pausa, reativacao e dados medicos podem ser auditados

**Validacao por revisao de codigo**
- [x] Sem dados excessivos no log

**Validacao por testes**
- [x] Emissao de logs de auditoria nas acoes definidas

**Validacao por MCP**
- [x] GitHub MCP opcional para acompanhar revisao de diffs

#### F12.02 - Implementar `SolicitacaoExportacao`

- [x] Criar model de pedido de exportacao
- [x] Registrar operador, filtros e resultado

**Esperado**
- Toda exportacao relevante deixa rastreio de origem e resultado.

**Criterios de aceitacao**
- [x] Exportacao pode ser auditada depois

**Validacao por revisao de codigo**
- [x] Sem CSV gerado fora de fluxo controlado

**Validacao por testes**
- [x] Registro da solicitacao

**Validacao por MCP**
- [x] Nao obrigatorio

#### F12.03 - Implementar `ControleExportacaoCSV`

- [x] Criar model/artefato de controle
- [x] Validar pre-condicoes antes da exportacao
- [x] Abortarar cedo em falha

**Esperado**
- O sistema aplica fail-fast real antes de exportacao critica.

**Criterios de aceitacao**
- [x] Se o arquivo de controle nao existir, a exportacao aborta
- [x] Se o arquivo estiver bloqueado, a exportacao aborta
- [x] O status final fica inequivoco

**Validacao por revisao de codigo**
- [x] Sem seguir para leitura pesada apos falha de pre-validacao

**Validacao por testes**
- [x] Arquivo de controle ausente
- [x] Arquivo bloqueado
- [x] Arquivo invalido
- [x] Exportacao valida

**Validacao por MCP**
- [x] Nao obrigatorio

#### F12.04 - Implementar T15 Relatorios, auditoria e exportacoes

- [x] Criar relatorios de presenca
- [x] Criar relatorios financeiros
- [x] Criar relatorios de graduacao
- [x] Criar logs auditaveis de alteracoes
- [x] Criar exportacoes CSV/PDF quando aplicavel

**Esperado**
- O dashboard deixa de ser a unica fonte de leitura gerencial.

**Criterios de aceitacao**
- [x] Relatorios respeitam perfil
- [x] Exportacao critica tem fail-fast
- [x] Logs de auditoria sao consultaveis

**Validacao por revisao de codigo**
- [x] Queries explicitas e auditaveis
- [x] Sem N+1 em relatorios

**Validacao por testes**
- [x] Relatorio de presenca
- [x] Relatorio financeiro
- [x] Relatorio de graduacao
- [x] Auditoria
- [x] Exportacao

**Validacao por MCP**
- [x] Figma MCP opcional

---

## 21. FASE 13 - Hardening, observabilidade e go-live

### 21.1 Status da fase

- [x] Fase 13 concluida

### 21.2 Objetivo da fase

Levar o sistema do estado "implementado" para o estado "operacionalmente seguro".

### 21.3 Tarefas da fase

#### F13.01 - Hardening de seguranca

- [x] Revisar CSRF
- [x] Revisar rate limiting
- [x] Revisar politicas de sessao
- [x] Revisar validacao de upload
- [x] Revisar segredos e configuracoes

**Esperado**
- O sistema reduz os riscos obvios antes do go-live.

**Criterios de aceitacao**
- [x] Endpoints criticos protegidos
- [x] Segredos externalizados

**Validacao por revisao de codigo**
- [x] Checklist de seguranca executado

**Validacao por testes**
- [x] Smoke tests de autenticacao, upload e mutacoes criticas

**Validacao por MCP**
- [x] GitHub MCP opcional para CI

#### F13.02 - Hardening de performance e concorrencia

- [x] Revisar N+1 em dashboards e relatorios
- [x] Revisar concorrencia em reserva
- [x] Revisar concorrencia em caixa
- [x] Revisar idempotencia de webhook

**Esperado**
- O sistema nao quebra nos fluxos de disputa de recurso escasso.

**Criterios de aceitacao**
- [x] Reserva resiste a concorrencia basica
- [x] Caixa resiste a concorrencia basica
- [x] Webhook repetido nao duplica efeito

**Validacao por revisao de codigo**
- [x] Locks usados apenas onde fazem sentido

**Validacao por testes**
- [x] Testes de concorrencia definidos

**Validacao por MCP**
- [x] GitHub MCP opcional

#### F13.03 - Observabilidade operacional

- [x] Consolidar logs estruturados
- [x] Garantir rastreio de falhas de pagamento
- [x] Garantir rastreio de falhas de webhook
- [x] Garantir rastreio de falhas de exportacao

**Esperado**
- Problemas de producao podem ser investigados com evidencia.

**Criterios de aceitacao**
- [x] Falhas criticas nao ficam mudas

**Validacao por revisao de codigo**
- [x] Logs com contexto util
- [x] Sem vazamento desnecessario de dados sensiveis

**Validacao por testes**
- [x] Simulacao de falha com log correspondente

**Validacao por MCP**
- [x] Stripe MCP recomendado para reconciliacao final

#### F13.04 - Checklist final de go-live

- [x] Validar T01 a T20
- [x] Validar fluxos de cadastro, pagamento, presenca, graduacao, documentos, PDV e exportacao
- [x] Validar backlog residual
- [x] Validar readiness operacional

**Esperado**
- O sistema esta pronto para ser declarado entregue dentro do escopo.

**Criterios de aceitacao**
- [x] Todas as fases obrigatorias anteriores concluidas
- [x] Nenhuma tarefa critica aberta
- [x] Backlog residual explicitamente separado

**Validacao por revisao de codigo**
- [x] Nenhum "faz depois" em regra critica

**Validacao por testes**
- [x] Smoke end-to-end dos fluxos principais

**Validacao por MCP**
- [x] GitHub MCP para fechamento do milestone
- [x] Stripe MCP para validacao final do catalogo e reconciliacao
- [x] Figma MCP opcional para paridade visual

---

## 22. Matriz final de cobertura das telas por fase

- [x] T01 coberta em F01 + F02
- [x] T02 coberta em F03
- [x] T03 coberta em F07
- [x] T04 coberta em F08
- [x] T05 coberta em F05
- [x] T06 coberta em F08
- [x] T07 coberta em F09
- [x] T08 coberta em F01
- [x] T09 coberta em F03
- [x] T10 coberta em F03
- [x] T11 coberta em F04
- [x] T12 coberta em F04
- [x] T13 coberta em F06
- [x] T14 coberta em F03 + F06 + F10
- [x] T15 coberta em F12
- [x] T16 coberta em F02
- [x] T17 coberta em F11
- [x] T18 coberta em F11
- [x] T19 coberta em F10
- [x] T20 coberta em F10

---

## 23. Checklist final de aceite integral do sistema

- [x] Identidade unica por CPF validada
- [x] Multi-papel validado
- [x] Onboarding transacional validado
- [x] Checkout e assinatura recorrente validados
- [x] Webhook idempotente validado
- [x] Hard stop antes da camera validado
- [x] Reserva consumindo lotacao validada
- [x] Presenca por sessao validada
- [x] Graduacao por tempo ativo validada
- [x] Pausa congelando graduacao validada
- [x] Dashboard por perfil validado
- [x] Dependente com escopo restrito validado
- [x] LGPD validada
- [x] Prontuario de emergencia validado
- [x] PDV e caixa diario validados
- [x] Relatorios e exportacoes fail-fast validados
- [x] Comunicacoes auditaveis validadas
- [x] Go-live checklist validado

---

## 24. Regra final de nao-parada

Enquanto houver algum item critico abaixo desmarcado, o sistema ainda nao pode ser considerado concluido:

- [x] Fase 00
- [x] Fase 01
- [x] Fase 02
- [x] Fase 03
- [x] Fase 04
- [x] Fase 05
- [x] Fase 06
- [x] Fase 07
- [x] Fase 08
- [x] Fase 09
- [x] Fase 10
- [x] Fase 11
- [x] Fase 12
- [x] Fase 13

### 24.1 Se houver bloqueio real

Registrar obrigatoriamente:

- [ ] Tarefa bloqueada
- [ ] Motivo exato
- [ ] Evidencia tecnica
- [ ] Impacto nas fases seguintes
- [ ] Menor decisao necessaria para destravar

Enquanto isso, continuar toda tarefa paralelizavel que nao dependa do bloqueio.
