# CLAUDE.md — Spec arquitetural e de domínio (LV JIU JITSU)

> **Fonte única de verdade técnica do produto.** Descreve arquitetura, domínios, invariantes, integrações, fluxos críticos e restrições operacionais do sistema **LV JIU JITSU**.
> Este arquivo guarda **o que o agente precisa saber sobre o projeto**, não como se comportar — para protocolo (fases, PRD, VMP, validação), leia `AGENTS.md` primeiro.

---

## Perfil do projeto

- **Produto:** plataforma web para gestão de academia de Jiu-Jitsu (escopo: operação comercial, financeira, acadêmica e administrativa).
- **Stack:** Python + Django (MTV); app único `system` com modularização interna.
- **Banco:** PostgreSQL em produção; **dev/local:** SQLite descartável no perfil VMP (ciclo em `AGENTS.md`).
- **Ambiente Python:** `.venv` local **obrigatória** — proibido atender o repositório com instalações no Python global.
- **Assíncrono:** Celery + Redis (quando em uso no ambiente).
- **Frontend:** templates Django + JS progressivo; validação visual preferencialmente **headless + MCP Playwright** (ou equivalente no ambiente).
- **Pagamentos:** `dj-stripe` + `stripe-python`.
- **QR / câmera:** `qrcode`; `html5-qrcode` + WebRTC/MediaDevices.
- **Paradigmas de trabalho:** SDD (spec/PRD), TDD, padrões só quando simplificarem.
- **Artefatos temporários:** preferir diretórios dentro do workspace do projeto.

### Regra de ambiente

- Todo `manage.py`, teste, `pip` e script operacional deve rodar com o interpretador da `.venv` (Windows: `.\.venv\Scripts\python.exe`).
- Se a `.venv` existir, comandos fora dela são erro operacional para este repositório.

---

## Arquitetura Django no repositório

| Camada | Local | Responsabilidade |
|--------|--------|------------------|
| Domínio | `system/models/` | Persistência e invariantes de domínio |
| Negócio | `system/services/` | Orquestração e regras (não em views) |
| Leitura | `system/selectors/` (quando houver) | Consultas, dashboards, listagens |
| HTTP | `system/views/` | Orquestração — views finas |
| Validação | `system/forms/` | Entrada server-side |
| Rotas | `system/urls.py` + raiz do projeto | Namespaces conforme organização atual |
| Apresentação | `templates/` (e segmentação por jornada) | Herdam `base.html`; blocos: `content`, `extra_css`, `extra_js` |
| Estáticos | `static/system/` | CSS/JS do produto |
| Testes | `system/tests/` | Por fluxo e domínio |
| Automação | `system/management/commands/` | Seeds, `create_admin_superuser`, etc. |

### Regras estruturais

- View não vira God Object; template não carrega regra de negócio complexa.
- Design pattern só entra quando simplifica (KISS; ver também `AGENTS.md`).
- `transaction.atomic()` em fluxos compostos (onboarding, vínculos, pagamento + efeitos).
- `select_related()` / `prefetch_related()` em listagens — proibido N+1 deliberado.
- Signals só quando acoplamento implícito for aceitável; regra central no serviço.
- Padrões aceitáveis quando úteis: Service Layer, Factory, Strategy, Repository, Adapter, Command.

### Seeds operacionais

- `inicial_seed`: catálogos base e configurações mínimas.
- `inicial_seed_test`: dados navegáveis para validação manual; cenários determinísticos e simples; um único `PersonType` por identidade; sem matriz N:N de tipos por pessoa.

---

## Sequência canônica de comandos (perfil VMP — desenvolvimento local)

Ordem de referência; ajustar prefixo da `.venv` ao SO:

```bash
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

### Regras críticas

- **Nunca** criar ou editar migration manualmente; corrigir models e regenerar.
- **Nunca** migrar incrementalmente sobre banco existente neste perfil — o banco nasce do zero a cada ciclo de reset.
- Não subir segundo servidor se já houver um na mesma porta.
- Se qualquer etapa falhar, corrigir e recomeçar do `clear_migrations.py`.
- Se um comando não existir no projeto, reportar — não simular sucesso.

### Cláusula de escape

Só se aplica com banco descartável e política alinhada ao time. Ambiente compartilhado ou banco persistente exige migração convencional e decisão explícita.

---

## PRD — estrutura mínima

Criar em `docs/prd/PRD-<NNN>-<slug>.md` quando a tarefa não for trivial:

```md
# PRD-<NNN>: <Título>
## Resumo
## Problema atual
## Objetivo
## Contexto consultado
## Escopo / Fora do escopo
## Regras e restrições
## Critérios de aceite
## Plano
- [ ] Etapa 1
- [ ] Etapa 2
## Implementado (preencher ao final)
## Desvios do plano
```

---

## Estrutura esperada do repositório (referência)

```
lvjiujitsu/
├── docs/prd/
├── system/
│   ├── models/
│   ├── views/
│   ├── forms/
│   ├── services/
│   ├── tests/
│   ├── migrations/          # após ciclo VMP: tipicamente 0001_initial.py
│   ├── management/commands/
│   └── urls.py
├── templates/
├── static/system/
├── clear_migrations.py
├── manage.py
├── CLAUDE.md
└── AGENTS.md
```

---

## Critérios de falha obrigatória

Marcar tarefa como **NÃO CONCLUÍDA** quando: implementou sem spec/PRD quando era necessário; alterou UI sem validação visual automatizada quando exigida; não verificou logs/console; declarou feito sem evidência; aplicou política VMP indevida a ambiente não descartável.

---

## Manutenção deste arquivo

- Manter conciso nas partes operacionais; não duplicar o passo a passo que já está em `AGENTS.md`.
- Decisões estruturais do produto entram na spec de domínio abaixo e no changelog (formato sugerido: `- **[YYYY-MM-DD]** Descrição`).

---

# Spec de domínio e visão do sistema

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

O **LV JIU JITSU** é um monólito Django com app único `system` e modularização interna forte, com foco em:

- identidade única por pessoa;
- tipo de pessoa único por cadastro na fase atual;
- gestão de planos, pagamentos e inadimplência;
- presença antifraude por QR dinâmico;
- controle de reserva de vagas em turmas;
- motor de graduação com tempo de treino ativo;
- gestão de dependentes e responsáveis;
- comunicação operacional com alunos;
- conformidade com LGPD para dados pessoais e sensíveis.

Arquitetura alvo:

- **backend:** Django;
- **autenticação do portal:** conta local do domínio, persistida no app `system`, com sessão própria;
- **admin técnico:** `django.contrib.admin` + `django.contrib.auth`, restritos à operação técnica e manutenção do projeto;
- **banco principal:** PostgreSQL;
- **dev/local:** SQLite opcional, com limitações conhecidas para concorrência;
- **ambiente Python:** `.venv` local obrigatória e isolada do Python global;
- **filas e tarefas assíncronas:** Celery + Redis;
- **frontend:** templates Django + JS progressivo;
- **pagamentos:** `dj-stripe` + `stripe-python`;
- **geração de QR:** `qrcode`;
- **leitura de QR/câmera:** `html5-qrcode` + WebRTC/MediaDevices.

---

## 2. Princípios arquiteturais

0. **Fase MVP de teste.** O sistema está em estágio inicial. Dados locais são descartáveis. O fluxo padrão de trabalho assume destruição e recriação completa do banco a cada ciclo via `clear_migrations.py`. Não há preocupação com integridade de dados existentes.
1. **App único `system` primeiro.** Não fragmentar o domínio físico cedo demais; modularizar internamente com disciplina.
2. **Identidade centralizada.** Pessoa é uma só; na fase atual, cada cadastro opera com um único `PersonType`.
3. **Autenticação do produto é do domínio.** O portal da academia não deve depender do modelo `User` do Django para operar.
4. **Regras do domínio no backend.** Frontend melhora UX, mas não decide o que é permitido.
5. **Fluxos críticos são auditáveis.** Pagamento, presença, exclusão de dados, prontuário e exportação precisam de rastreabilidade.
6. **Configuração é externa ou persistida.** Nada importante deve ficar hardcoded.
7. **Segurança por camadas.** UI, permissão, validação de negócio e auditoria trabalham juntas.
8. **Planejamento orientado a agregado.** Toda mudança deve deixar claro qual domínio é fonte de verdade e qual domínio apenas reflete ou consome estado.
9. **Política de idioma dual.** Código, identificadores técnicos, arquivos e rotas em inglês; texto visível ao usuário final em pt-BR.
10. **Qualidade linguística de interface é regra de produto.** Título, label, placeholder, CTA, ajuda contextual, estado vazio e mensagem exibidos ao usuário final devem estar em português correto, com acentuação adequada e revisão final antes da entrega.
11. **Qualidade visual faz parte do produto.** Interface, hierarquia de informação, estados vazios e responsividade não são acabamento opcional.
12. **Ambiente isolado é regra estrutural.** Toda execução Python, instalação de dependência, teste e comando Django deve ocorrer apenas dentro da `.venv` do repositório.
13. **Artefatos temporários ficam no workspace.** Testes, exports temporários e arquivos auxiliares não devem depender implicitamente de diretórios globais do sistema quando isso criar risco de permissão ou poluição operacional.
14. **Validação visual automatizada é obrigatória em interface.** Mudanças em rotas, templates, CSS e jornadas visuais só podem ser dadas como prontas após conferência por navegador automatizado, preferencialmente via Playwright MCP no Codex CLI.

### 2.1 Regra operacional de ambiente

- O projeto deve possuir e usar uma `.venv` local.
- É proibido instalar dependências no Python global para atender este repositório.
- `manage.py`, testes e scripts operacionais devem ser executados com o interpretador da `.venv`.
- Se a `.venv` existir, comandos fora dela devem ser tratados como erro operacional.
- Durante a fase atual de desenvolvimento, o banco local e as migrations do app `system` devem ser tratados como descartáveis em qualquer refatoração estrutural de modelagem.
- Se houver incoerência de relacionamento, mudança de cardinalidade, ou refatoração de identidade/cadastro, a ação correta é executar `clear_migrations.py` e reconstruir o ambiente, sem tentar preservar SQLite inconsistente.
- Artefatos temporários de teste devem ser gerados preferencialmente dentro do workspace do projeto.

### 2.2 Fluxo obrigatório de reset — critério principal de trabalho

- O projeto está em **fase MVP de teste**. Dados locais são descartáveis e não há preocupação com integridade de dados existentes.
- O script oficial de reset do ambiente local é `clear_migrations.py`.
- Esse script deve remover banco SQLite, migrations do projeto, `__pycache__`, artefatos locais e encerrar outros processos Python ativos antes da recriação do ambiente.
- **Toda correção ou implementação** no perfil VMP **deve** alinhar-se ao ciclo definido em `AGENTS.md` (incluindo `clear_migrations.py` antes de alterar código quando aplicável).
- Após implementar mudanças, o ambiente deve ser reconstruído na ordem documentada na seção **Sequência canônica** deste arquivo.
- **Nunca** tentar migrar incrementalmente sobre banco existente neste perfil. O banco sempre nasce do zero.
- **Nunca** preservar migrations intermediárias, dados ou estado do banco entre ciclos de trabalho.
- Se qualquer etapa falhar após a implementação, corrigir o código e recomeçar do `clear_migrations.py`.
- Para validação visual de interface: configuração preferencial Playwright MCP — `codex mcp add playwright npx "@playwright/mcp@latest"`. Sem essa etapa quando exigida, a interface não deve ser considerada validada.

---

## 3. Topologia de app único e módulos internos

A organização física do monólito deve usar **um único app Django chamado `system/`**.
O crescimento do produto deve acontecer por **módulos internos, pacotes e fronteiras de domínio**, não por multiplicação precoce de apps.

Estrutura-alvo:

- `system/` — app único contendo domínio, autenticação, operações, integrações, auditoria e entrega web/API;
- `system/models/` — modelos agrupados por domínio e arquivo temático;
- `system/views/` — views separadas por jornada e contexto operacional;
- `system/forms/` — forms HTML por fluxo;
- `system/serializers/` — serializers explícitos para API e integrações;
- `system/services/` — orquestrações e regras compostas;
- `system/selectors/` — consultas de leitura e montagem de dashboards/listagens;
- `system/tests/` — testes por módulo interno e por nível de validação;
- `system/management/commands/` — comandos operacionais e seeds;
- `templates/` — templates por jornada (organização atual do repositório);
- `static/system/` — assets e comportamento frontend do sistema.

### 3.1 Módulos internos obrigatórios dentro de `system/`

- `public` — landing, páginas abertas, mural e recuperação de acesso.
- `identity_access` — autenticação, usuário, papéis, permissões e trilhas de acesso.
- `student_registry` — aluno titular, dependentes, responsável financeiro, prontuário e documentos.
- `instructor_ops` — perfil docente, agenda, especialidades e alocação em turma.
- `class_catalog` — modalidades, turmas, sessões, agenda e capacidade.
- `attendance_qr` — reserva, elegibilidade, QR dinâmico, leitura e presença.
- `finance_contracts` — plano local, matrícula, desconto, bolsa, inadimplência, pausa, PDV e caixa.
- `payments_stripe` — checkout, customer portal, webhook, invoices, subscriptions e reconciliação.
- `graduation_engine` — tempo ativo, critérios técnicos, exames e promoção.
- `communications` — mural, comunicados, notificações e trilha de envio.
- `documents_lgpd` — consentimentos, anonimização, exclusão e retenção.
- `reports_audit` — dashboards, relatórios, exportações e evidências operacionais.
- `settings_seed` — parâmetros operacionais, catálogos internos e carga inicial.

### 3.1.1 Seeds operacionais

- `inicial_seed` deve carregar apenas catálogos base e configurações mínimas do sistema.
- `inicial_seed_test` deve ser tratada como carga navegável de validação manual do portal.
- `inicial_seed_test` deve gerar cenários determinísticos simples, sem matriz N:N de tipos por pessoa.
- As seeds de teste devem cobrir apenas cadastros coerentes com um único `PersonType` por identidade, mantendo relacionamentos de responsável e dependente quando aplicáveis.

### 3.2 Fonte de verdade por agregado dentro de `system/`

- `identity_access`: identidade, autenticação, papéis e permissões.
- `student_registry`: pessoa, dependentes, dados cadastrais, contato de emergência e dados sensíveis.
- `instructor_ops`: perfil docente, agenda e alocação operacional.
- `class_catalog`: oferta de aula, sessão, capacidade, agenda e lotação planejada.
- `attendance_qr`: reserva válida, elegibilidade de check-in e presença confirmada.
- `finance_contracts`: estado local da matrícula, plano, bolsa, desconto, inadimplência, pausa e contrato operacional.
- `payments_stripe`: checkout, espelho financeiro externo, webhook, portal do cliente e reconciliação.
- `graduation_engine`: tempo ativo, histórico técnico, elegibilidade e promoção.
- `communications`: publicação, entrega e histórico de comunicação.
- `documents_lgpd`: consentimento, retenção, anonimização e exclusão definitiva.
- `reports_audit`: leitura agregada, auditoria, exportação e BI com fail-fast.

Regra central:

- o estado de negócio da academia é sempre local;
- integrações externas confirmam eventos, mas não substituem a fonte de verdade do domínio.

### 3.3 Fronteira entre portal e Django Admin

- O portal da academia e o Django Admin são superfícies distintas.
- O **portal** usa identidade local do domínio, modelada em `system`, com conta de acesso, sessão própria e permissões baseadas em `Person` + `PersonType`.
- O **Django Admin** existe apenas para administração técnica, suporte operacional restrito e manutenção de dados por equipe autorizada.
- É proibido usar `django.contrib.auth.User` como identidade primária do aluno, responsável, professor ou auxiliar administrativo do produto.
- É proibido depender de `request.user`, `LoginRequiredMixin`, `AuthenticationForm` ou `PasswordResetView` do Django como base do portal do produto.
- O fato de alguém existir no Django Admin não concede acesso ao portal.
- O fato de alguém possuir acesso ao portal não exige criação de `User` do Django.

---

## 4. Identidade, autenticação e modelo de acesso

### 4.1 Regra central de identidade

- Cada pessoa física deve ter **uma única identidade** no sistema.
- Cada identidade do portal deve possuir **um único `PersonType` ativo** na fase atual.
- **CPF é o identificador único de autenticação**.
- O banco pode usar um identificador técnico interno como PK física; o CPF deve ser tratado como chave natural única de login e negócio.
- É proibido duplicar cadastro para a mesma pessoa só porque ela exerce mais de um papel.

### 4.1.1 Regra de autenticação do portal

- A autenticação do portal é local ao domínio e deve ser modelada dentro de `system.identity_access`.
- A conta autenticável do portal deve referenciar exatamente uma `Person`.
- Hash de senha, tentativas de login, reset de senha, sessão e flags operacionais do acesso devem ficar em modelos do próprio domínio.
- O CPF é o identificador único de login do portal.
- Reset de senha do portal deve operar sobre token local do domínio e não sobre o fluxo padrão de `django.contrib.auth`.
- Sessão do portal deve ser independente da sessão usada pelo Django Admin.

### 4.2 Papéis de negócio

Os tipos de pessoa disponíveis são:

- `ADMIN_MASTER`
- `ADMIN_UNIDADE` / `RECEPCAO`
- `PROFESSOR`
- `ALUNO_TITULAR`
- `ALUNO_DEPENDENTE_COM_CREDENCIAL`
- `RESPONSAVEL_FINANCEIRO`

Regra da fase atual:

- uma pessoa possui apenas um tipo de pessoa por cadastro;
- multi-papel e matriz N:N de tipos por identidade não devem ser implementados enquanto essa fase de modelagem estiver ativa.

### 4.3 Dependentes

- Dependentes podem existir vinculados ao responsável financeiro.
- Acima de uma idade configurável e cumpridos os requisitos de cadastro, um dependente pode possuir credencial própria.
- O dependente com credencial acessa apenas o necessário para sua jornada esportiva.
- Quando `dependent` for o único papel autenticável da conta local do portal, o roteamento pós-login deve continuar levando ao escopo de aluno, sem exigir a presença simultânea de `student` ou `guardian` para navegação básica.
- Dados financeiros do titular não podem ser exibidos para o dependente.

### 4.4 Professor e aluno na fase atual

- A fase atual não suporta multi-papel no mesmo cadastro.
- Se houver necessidade de reintroduzir professor que também é aluno, isso deve ser tratado como nova decisão estrutural de modelagem antes de qualquer implementação.

### 4.5 Superfície administrativa técnica

- `django.contrib.admin` deve permanecer disponível apenas em `/django-admin/`.
- O superusuário técnico existe para administração do projeto, inspeção e suporte de manutenção.
- CRUDs do produto, permissões do portal e jornadas operacionais não devem exigir login no Django Admin.
- O sistema pode ter pessoas com papel administrativo no portal sem qualquer vínculo com `User` do Django.

---

## 5. Regras canônicas de negócio

### 5.1 Onboarding e cadastro

- O cadastro do titular e de seus dependentes deve ser transacional.
- Não pode existir onboarding parcialmente concluído com identidade quebrada.
- O onboarding coleta dados pessoais, contatos, documentos e, quando aplicável, dados de emergência e saúde.
- Para aluno titular e dependente com jornada esportiva, o onboarding deve coletar também o **sexo biológico** quando isso for necessário para validar elegibilidade de turma.
- Sempre que o cadastro criar alguém com direito de acesso ao portal, a conta local do domínio deve nascer junto com a pessoa, com senha definida no próprio onboarding.
- O onboarding não deve criar `User` do Django para titular, dependente, responsável ou professor do produto.
- Na etapa esportiva do onboarding, aluno titular e dependente selecionam **turmas liberadas**, não um único horário fixo.
- Horários ativos de treino são derivados automaticamente das turmas liberadas ao aluno; o onboarding não deve exigir seleção manual de dia da semana ou horário único para matrícula esportiva recorrente.

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

### 5.3.1 Turma, categoria e horário

- `ClassGroup` não deve possuir eixo separado de `público` ou flag de publicação.
- A classificação operacional da turma deve vir exclusivamente de `ClassCategory`.
- `ClassSchedule` representa o horário da turma e não deve ser colapsado no nome da turma.
- A superfície administrativa e a tela de informações não devem exibir `Público` como coluna ou atributo redundante da turma.
- A liberação esportiva do aluno deve acontecer por `ClassGroup`; `ClassSchedule` é agenda operacional da turma, não vínculo principal de matrícula do aluno.
- Ao liberar uma turma para um aluno elegível, todos os `ClassSchedule` ativos daquela turma ficam disponíveis automaticamente, sem distinção manual por dia da semana no onboarding.
- A elegibilidade da turma deve ser revalidada no backend com base na faixa etária calculada da pessoa.
- Turma feminina exige pessoa com **sexo biológico feminino** e faixa etária compatível com a categoria adulta.

### 5.4 Inadimplência

- Inadimplência bloqueia check-in e acesso esportivo conforme política da academia.
- O bloqueio precisa aparecer na UI antes de qualquer tentativa de câmera.
- O dashboard do aluno deve oferecer rota clara para regularização.
- Comprovante manual enviado para pagamento não regulariza acesso automaticamente: enquanto a fatura estiver `UNDER_REVIEW`, o contrato local permanece `PENDING_FINANCIAL` até revisão administrativa explícita.

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
- Todo turno encerrado precisa ficar imutável para novos lançamentos.
- Divergência acima do limiar configurável de caixa deve marcar o turno para revisão gerencial.

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
- O arquivo de controle de exportação crítica deve conter a diretiva explícita `EXPORT_ALLOWED=1`.
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
- redirecionamentos de `success_url`, `cancel_url` ou retorno de portal não podem ser usados como prova de quitação ou liberação de acesso.

#### 6.1.1 Fonte de verdade: Stripe x domínio local

- Stripe confirma eventos financeiros, cobrança recorrente, checkout e portal;
- `system.finance_contracts` e os agregados locais definem acesso, bloqueio, pausa, retomada e efeitos esportivos;
- uma assinatura ativa na Stripe não autoriza, sozinha, check-in, graduação ou acesso irrestrito;
- qualquer sincronização com a Stripe deve ser auditável, idempotente e reconciliável.
- criação bem-sucedida de Checkout Session ou retorno do usuário do checkout não muda, por si só, o estado operacional; a liberação depende de reconciliação local confiável, com webhook ou confirmação financeira equivalente.
- cada `FinancialPlan` precisa apontar para um unico `Price` Stripe vigente por vez, com aposentadoria explicita dos mapeamentos anteriores.
- o espelho `dj-stripe` deve ser tratado como camada auxiliar de observabilidade e reconciliacao, nunca como substituto do contrato local.

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
- manter auditoria transversal dos fluxos críticos de autenticação, financeiro, pagamentos, graduação, PDV, exportação e emergência.
- separar claramente autenticação técnica do Django Admin da autenticação funcional do portal.

### 7.3 Exclusão definitiva

Quando juridicamente cabível e respeitadas obrigações de retenção:

- apagar ou anonimizar dados pessoais identificáveis;
- remover selfie/biometria e dados médicos que não precisem ser preservados;
- manter apenas o mínimo técnico/financeiro necessário para integridade histórica e contábil.
- solicitações destrutivas de LGPD não podem ser concluídas enquanto houver contrato financeiro local em estado operacional ativo, pausado, bloqueado ou pendente, porque ainda existe obrigação de retenção operacional/contábil e vínculo transacional em aberto.

### 7.4 Lacunas que precisam permanecer explícitas

Enquanto não houver definição mais forte de produto e operação, estas lacunas precisam continuar visíveis no planejamento:

- política formal de retenção para selfie, biometria e prontuário;
- trilha de auditoria detalhada para acesso emergencial e dados médicos;
- política de chargeback, contestação e exceções financeiras;
- regras finas de comunicação transacional por canal;
- governança mais explícita de multi-unidade, caso a operação cresça.

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
11. separação correta entre login do portal e login do Django Admin;
12. reset de senha do portal sem tocar em `User` do Django.

---

## 10. Armadilhas conhecidas

- usar CPF como duplicador de papel em vez de identidade única;
- acoplar acesso do portal a `django.contrib.auth.User`;
- liberar rota do portal porque o usuário está autenticado no Django Admin;
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

### 11.1 Fronteiras atuais e lacunas abertas para planejamento

Estas lacunas devem ser tratadas como backlog arquitetural, e não como detalhe casual:

- formalização completa da política LGPD para exclusão, anonimização e retenção;
- evolução do motor de graduação para regras configuráveis mais finas por academia;
- governança explícita para multi-unidade e papéis administrativos mais granulares;
- observabilidade operacional de webhooks, retries e reconciliação financeira;
- estratégia de comunicação operacional desacoplada por e-mail, push e WhatsApp;
- catálogo oficial de planos, bolsas, descontos e versionamento de preços.
- política formal de retenção e rotação para artefatos de exportação gerados em disco.

Essas lacunas não invalidam a spec atual, mas precisam orientar o planejamento das próximas fases.

---

## 12. Changelog da spec

- **[2026-03-17]** Consolidação da identidade única por CPF como base do domínio.
- **[2026-03-17]** Formalização de dependente com credencial própria e escopo restrito.
- **[2026-03-17]** Reserva prévia como mecanismo oficial de consumo de lotação.
- **[2026-03-17]** Hard stop antes da câmera para inadimplência, pausa e ausência de reserva.
- **[2026-03-17]** Inclusão do estado local `PAUSADO` com integração financeira e congelamento de graduação.
- **[2026-03-17]** LGPD reforçada com fluxo de solicitação de exclusão definitiva e anonimização.
- **[2026-03-17]** Inclusão dos módulos operacionais de PDV, caixa diário, comunicações e prontuário de emergência.
- **[2026-03-17]** Exportações críticas reforçadas com fail-fast obrigatório do arquivo de controle.
- **[2026-03-30]** Reforçada a política de planejamento orientado a agregado, com fonte de verdade explícita por domínio.
- **[2026-03-30]** Formalizada a separação entre eventos financeiros da Stripe e o estado local de negócio da matrícula.
- **[2026-03-30]** Registradas lacunas arquiteturais abertas para orientar planejamento futuro sem diluir a spec atual.
- **[2026-04-01]** Formalizado que comprovante manual em análise não regulariza acesso até revisão administrativa explícita.
- **[2026-04-01]** Formalizado que retorno visual do checkout Stripe nunca libera acesso sem reconciliação local idempotente.
- **[2026-04-02]** Formalizado que solicitação LGPD destrutiva fica bloqueada enquanto houver contrato financeiro local ainda ativo ou pendente de retenção operacional/contábil.
- **[2026-04-02]** Formalizado que exportação crítica exige arquivo de controle com `EXPORT_ALLOWED=1` e que divergência relevante de caixa exige revisão gerencial.
- **[2026-04-02]** Formalizada a auditoria transversal obrigatória para autenticação, financeiro, pagamentos, graduação, PDV, exportação e emergência.
- **[2026-04-02]** Formalizado que o catalogo Stripe exige mapeamento deterministico por plano, com um unico `Price` vigente e aposentadoria explicita de legados.
- **[2026-04-02]** Formalizado que o espelho `dj-stripe` e camada auxiliar de reconciliacao e nao substitui a fonte de verdade do dominio local.
- **[2026-04-03]** Formalizado que a autenticação do portal é local ao domínio, independente do Django Admin, com sessão própria e reset de senha próprio.
- **[2026-04-04]** Formalizado que `dependent` isolado continua navegável no escopo de aluno do portal, sem reintroduzir multi-papel por identidade.
- **[2026-04-04]** Formalizado que a fase atual usa um único `PersonType` por pessoa e que `inicial_seed_test` deve gerar apenas cenários simples e determinísticos.
- **[2026-04-04]** Formalizado que, em refatorações estruturais da modelagem durante o desenvolvimento, o banco local deve ser descartado e recriado com `clear_migrations.py`.
- **[2026-04-05]** Formalizado que `ClassGroup` não possui eixo separado de `público`; a classificação da turma vem exclusivamente de `ClassCategory`, e a UI não deve exibir coluna redundante de `Público` em turmas.
- **[2026-04-07]** Reorganização do `AGENTS.md`/`CLAUDE.md` com protocolo SDD/TDD, PRDs em `docs/prd/`, fases de validação e política VMP explícita, preservando a spec de domínio do LV JIU JITSU.
