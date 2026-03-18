# CLAUDE.md — Spec Arquitetural e de Domínio do projeto LV JIU JITSU

> **Fonte única de verdade técnica do projeto.**  
> Este documento descreve arquitetura, domínios, invariantes, integrações, fluxos críticos e restrições operacionais do sistema **LV JIU JITSU**.  
> Regras de comportamento do agente ficam no `AGENTS.md`.

---

## 0. Status da spec

**Projeto:** LV JIU JITSU  
**Tipo:** plataforma web para gestão de academia de Jiu-Jitsu  
**Escopo atual:** operação comercial, financeira, acadêmica e administrativa da academia, incluindo onboarding, check-in com QR, graduação, cobrança recorrente, dependentes, comunicação e relatórios.

Esta spec deve ser atualizada sempre que surgir:
- nova regra de negócio do tatame;
- nova exigência operacional da recepção;
- nova restrição legal, financeira ou de integração;
- nova decisão estrutural que afete o projeto inteiro.

---

## 1. Visão do sistema

O **LV JIU JITSU** é um monólito modular Django para academias de Jiu-Jitsu, com foco em:
- identidade única por pessoa;
- gestão de planos, pagamentos e inadimplência;
- presença antifraude por QR dinâmico;
- controle de reserva de vagas em turmas;
- motor de graduação com tempo de treino ativo;
- gestão de dependentes e responsáveis;
- comunicação operacional com alunos;
- conformidade com LGPD para dados pessoais e sensíveis.

Arquitetura alvo:
- **backend:** Django;
- **autenticação:** `django-allauth`;
- **banco principal:** PostgreSQL;
- **dev/local:** SQLite opcional, com limitações conhecidas para concorrência;
- **filas e tarefas assíncronas:** Celery + Redis;
- **frontend:** templates Django + JS progressivo;
- **pagamentos:** `dj-stripe` + `stripe-python`;
- **geração de QR:** `qrcode`;
- **leitura de QR/câmera:** `html5-qrcode` + WebRTC/MediaDevices.

---

## 2. Princípios arquiteturais

1. **Monólito modular primeiro.** Não fragmentar o domínio cedo demais.
2. **Identidade centralizada.** Pessoa é uma só; perfis de negócio se acumulam.
3. **Regras do domínio no backend.** Frontend melhora UX, mas não decide o que é permitido.
4. **Fluxos críticos são auditáveis.** Pagamento, presença, exclusão de dados, prontuário e exportação precisam de rastreabilidade.
5. **Configuração é externa ou persistida.** Nada importante deve ficar hardcoded.
6. **Segurança por camadas.** UI, permissão, validação de negócio e auditoria trabalham juntas.

---

## 3. Topologia sugerida de apps/domínios

A organização sugerida do monólito deve refletir o domínio real do negócio e os nomes físicos de app precisam ser mantidos exatamente assim para evitar ambiguidade futura:

- `core/` — landing page, home, base layout, mural e páginas públicas;
- `accounts/` — autenticação, usuário, perfis, permissões e anonimização LGPD;
- `clientes/` — perfil do aluno, dependentes, prontuário e histórico de treino;
- `professores/` — perfil docente, especialidades, agenda e alocação em turmas;
- `presenca_graduacao/` — modalidades, turmas, QR dinâmico, check-in, motor de faixas e elegibilidade;
- `financeiro/` — planos locais, descontos, bolsas, caixa, PDV, inadimplência e pausa;
- `pagamentos/` — Stripe Checkout, webhooks e comprovantes manuais;
- `dashboard/` — painéis de indicadores para admin, professor e aluno;
- `relatorios/` — auditoria, exportações fail-fast e BI.

---

## 4. Identidade, autenticação e modelo de acesso

### 4.1 Regra central de identidade
- Cada pessoa física deve ter **uma única identidade** no sistema.
- **CPF é o identificador único de autenticação**.
- O banco pode usar um identificador técnico interno como PK física; o CPF deve ser tratado como chave natural única de login e negócio.
- É proibido duplicar cadastro para a mesma pessoa só porque ela exerce mais de um papel.

### 4.2 Papéis de negócio
Os papéis podem coexistir na mesma identidade:
- `ADMIN_MASTER`
- `ADMIN_UNIDADE` / `RECEPCAO`
- `PROFESSOR`
- `ALUNO_TITULAR`
- `ALUNO_DEPENDENTE_COM_CREDENCIAL`
- `RESPONSAVEL_FINANCEIRO`

### 4.3 Dependentes
- Dependentes podem existir vinculados ao responsável financeiro.
- Acima de uma idade configurável e cumpridos os requisitos de cadastro, um dependente pode possuir credencial própria.
- O dependente com credencial acessa apenas o necessário para sua jornada esportiva.
- Dados financeiros do titular não podem ser exibidos para o dependente.

### 4.4 Professor que também é aluno
- Um professor pode treinar como aluno sem duplicar CPF.
- O mesmo usuário pode possuir perfil docente e vínculo com plano financeiro, bolsa ou desconto.

---

## 5. Regras canônicas de negócio

### 5.1 Onboarding e cadastro
- O cadastro do titular e de seus dependentes deve ser transacional.
- Não pode existir onboarding parcialmente concluído com identidade quebrada.
- O onboarding coleta dados pessoais, contatos, documentos e, quando aplicável, dados de emergência e saúde.

### 5.2 Presença e check-in
- O QR Code deve ser dinâmico e de curta duração.
- A presença é gravada contra uma **sessão de aula** específica.
- O sistema deve verificar, antes de abrir a câmera:
  - adimplência;
  - status da matrícula;
  - existência de reserva, quando exigida;
  - permissão do perfil;
  - janela válida da sessão.
- O backend repete as validações antes de persistir a presença.

### 5.3 Lotação e reserva prévia
- Capacidade máxima é consumida na reserva de vaga, não no momento do escaneamento na porta.
- O QR serve para confirmar presença física do aluno que já garantiu a vaga.
- Regras de no-show, tolerância e reaproveitamento de vaga devem ser configuráveis.

### 5.4 Inadimplência
- Inadimplência bloqueia check-in e acesso esportivo conforme política da academia.
- O bloqueio precisa aparecer na UI antes de qualquer tentativa de câmera.
- O dashboard do aluno deve oferecer rota clara para regularização.

### 5.5 Trancamento / pausa de matrícula
- O sistema deve permitir trancamento temporário de matrícula.
- Durante a pausa:
  - o aluno assume status local `PAUSADO`;
  - o check-in fica bloqueado;
  - a cobrança pode ser pausada na Stripe quando aplicável;
  - o tempo elegível de graduação congela;
  - a auditoria deve registrar início, motivo previsto e término previsto.
- Retomada de matrícula deve reativar permissões conforme situação financeira e operacional.

### 5.6 Graduação
- O motor de graduação considera presença válida e tempo de treino ativo.
- Tempo corrido sem treino efetivo não deve gerar elegibilidade artificial.
- Pausas e ausências reconhecidas precisam congelar o relógio de progressão quando a regra assim exigir.
- A academia pode configurar regras internas, mas o sistema deve preservar referência aos tempos mínimos oficiais adotados.

### 5.7 Caixa e balcão
- O sistema deve suportar vendas avulsas de recepção.
- Deve existir fluxo de PDV/caixa rápido para itens como água, açaí, aluguel de kimono e materiais.
- Fechamento de caixa diário precisa separar dinheiro físico de cobranças recorrentes digitais.

### 5.8 Comunicações
- A administração precisa conseguir publicar avisos e comunicados em massa.
- O sistema deve suportar mural interno e canais externos configurados.
- Mensagens operacionais precisam ser auditáveis.

### 5.9 Prontuário de emergência
- Contato de emergência, dados médicos essenciais e informações rápidas devem ser acessíveis em modo de emergência com forte restrição de acesso.
- Toda consulta de prontuário sensível deve gerar trilha de auditoria.

### 5.10 Relatórios e exportações
- Dashboards e exportações não podem inferir regra crítica a partir de dado inconsistente.
- Geração de CSV/extração de BI depende de pré-validação obrigatória do arquivo de controle.
- Falha no controle aborta a operação antes de leitura pesada ou escrita de saída.

---

## 6. Integrações externas

### 6.1 Stripe
A integração de pagamentos deve usar preferencialmente `dj-stripe` como camada principal de ecossistema Django, complementada por `stripe-python` quando for necessário acessar fluxos específicos da API Stripe.

O projeto pode usar Stripe para:
- Checkout de assinatura;
- cobrança recorrente;
- Customer Portal;
- PIX e cartão, conforme configuração adotada;
- tratamento de webhooks;
- pausa de cobrança por `pause_collection`, quando aplicável.

Regras:
- webhooks precisam validar assinatura do evento;
- processamento deve ser idempotente;
- o sistema precisa manter estado de negócio próprio, sem depender apenas do `status` devolvido pela Stripe;
- pausa financeira não substitui o estado local `PAUSADO` da matrícula.

### 6.2 Câmera / WebRTC
- A geração de QR no backend deve usar `qrcode`.
- A leitura no frontend deve usar `html5-qrcode` em contexto seguro para câmera em produção.
- A UI não deve solicitar câmera quando a regra de negócio já sabe que o acesso está bloqueado.

### 6.3 Mensageria
- E-mail, push ou integração com WhatsApp devem ser tratados como canais desacoplados.
- Falha de entrega de mensagem não pode quebrar fluxo principal de cadastro, cobrança ou presença.

---

## 7. Segurança, LGPD e dados sensíveis

### 7.1 Base de proteção
O sistema lida com:
- dados cadastrais;
- dados financeiros;
- selfies/biometria facial;
- dados médicos;
- dados de crianças e adolescentes.

### 7.2 Regras obrigatórias
- coletar apenas o mínimo necessário;
- restringir acesso por papel e necessidade operacional;
- registrar auditoria de acesso a dados sensíveis;
- proteger exclusão lógica e exclusão definitiva como fluxos distintos.

### 7.3 Exclusão definitiva
Quando juridicamente cabível e respeitadas obrigações de retenção:
- apagar ou anonimizar dados pessoais identificáveis;
- remover selfie/biometria e dados médicos que não precisem ser preservados;
- manter apenas o mínimo técnico/financeiro necessário para integridade histórica e contábil.

---

## 8. Mapeamento macro de telas e domínios

O sistema cobre, no mínimo, estes macroblocos funcionais:
- T01 Landing, login e acesso;
- T02 Cadastro e onboarding;
- T03 Checkout e assinaturas;
- T04 Dashboard do aluno;
- T05 Dashboard do professor;
- T06 Dashboard administrativo/master;
- T07 Graduação e exame;
- T08 Recuperação de senha e credenciais;
- T09 Meu perfil e LGPD;
- T10 Gestão de alunos/dependentes;
- T11 Gestão de professores;
- T12 Turmas, modalidades e reservas;
- T13 Financeiro;
- T14 Pagamentos, comprovantes e integrações;
- T15 Relatórios, auditoria e exportações;
- T16 Leads/aula experimental;
- T17 PDV / caixa rápido;
- T18 Fechamento de caixa diário;
- T19 Central de comunicações e avisos;
- T20 Prontuário de emergência.

Se uma feature nova não se encaixar claramente em um desses domínios, a modelagem precisa ser revisitada antes da implementação.

---

## 9. Fluxos críticos que exigem cuidado extra

1. criação de usuário com CPF já existente;
2. professor que também é aluno;
3. dependente com login próprio e escopo restrito;
4. reserva de vaga + check-in simultâneo;
5. inadimplência com tentativa de escanear QR;
6. pausa de matrícula com Stripe e graduação;
7. processamento repetido de webhook;
8. exclusão definitiva sob LGPD;
9. consulta emergencial de prontuário;
10. exportação de BI com arquivo de controle inválido.

---

## 10. Armadilhas conhecidas

- usar CPF como duplicador de papel em vez de identidade única;
- confiar só no frontend para bloquear acesso;
- misturar `status` local da matrícula com `status` financeiro externo;
- consumir capacidade da turma apenas na porta;
- deixar regra de graduação espalhada em várias telas;
- expor boletos/planos para dependente com credencial;
- guardar selfie e dado médico sem política clara de retenção;
- seguir com exportação mesmo após falha de controle;
- testar concorrência só em SQLite e assumir que produção está coberta.

---

## 11. Definição mínima de pronto para mudanças sensíveis

Uma mudança é considerada pronta quando:
1. respeita esta spec e o `AGENTS.md`;
2. não quebra identidade única;
3. não abre brecha de permissão indevida;
4. não deixa regra crítica apenas na UI;
5. possui validação/tela/estado coerentes de backend e frontend;
6. possui trilha de auditoria quando necessário;
7. foi coberta por testes adequados ao risco.

---

## 12. Changelog da spec

- **[2026-03-17]** Consolidação da identidade única por CPF com papéis acumuláveis.
- **[2026-03-17]** Formalização de dependente com credencial própria e escopo restrito.
- **[2026-03-17]** Reserva prévia como mecanismo oficial de consumo de lotação.
- **[2026-03-17]** Hard stop antes da câmera para inadimplência, pausa e ausência de reserva.
- **[2026-03-17]** Inclusão do estado local `PAUSADO` com integração financeira e congelamento de graduação.
- **[2026-03-17]** LGPD reforçada com fluxo de solicitação de exclusão definitiva e anonimização.
- **[2026-03-17]** Inclusão dos módulos operacionais de PDV, caixa diário, comunicações e prontuário de emergência.
- **[2026-03-17]** Exportações críticas reforçadas com fail-fast obrigatório do arquivo de controle.
