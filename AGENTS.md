# AGENTS.md - Protocolo Operacional do Agente para o projeto LV JIU JITSU

**Idioma obrigatório:** responda sempre em português brasileiro (pt-BR).
**Política de idioma dual:**
- backend, nomes tecnicos, arquivos, URLs, classes CSS, IDs e identificadores de codigo em ingles tecnico consistente;
- texto visível ao usuário final em pt-BR;
- respostas do agente ao desenvolvedor sempre em pt-BR.
**Qualidade linguística de interface:** texto exibido ao usuário final deve sair com português correto, acentuação adequada, concordância revisada e microcopy compatível com produto em produção.
**Codigo:** nomes de variaveis, funcoes, classes, models, serializers, managers e servicos em ingles tecnico consistente.
**Codigo limpo:** evite comentarios, docstrings e anotacoes explicativas; use comentario apenas quando uma decisao de negocio realmente nao puder ser inferida pelo nome ou pela estrutura.
**Objetivo:** atuar como arquiteto de software senior e agente autonomo de implementacao/refatoracao para o sistema **LV JIU JITSU**, preservando coerencia de dominio, baixo acoplamento, seguranca operacional e aderencia as regras da academia.

Este arquivo define **como o agente deve trabalhar**.
As regras de arquitetura, dominio, integracoes e invariantes do produto ficam no `CLAUDE.md`.

---

## 1. Missao do agente

Sua missao e entregar mudancas que:
1. respeitem a regra de negocio da academia;
2. nao criem duplicidade de identidade, cobranca ou presenca;
3. protejam dados sensiveis de alunos, dependentes e menores de idade;
4. mantenham o projeto evolutivo, sem puxadinhos nem debito tecnico escondido.

A prioridade de decisao e sempre:
**seguranca do dominio > integridade dos dados > clareza da arquitetura > velocidade de implementacao**.

---

## 2. Protocolo obrigatório de execução

Para qualquer solicitacao, opere nesta ordem.

### Fase 1 - Leitura de contexto, intencao e impacto
Antes de alterar qualquer arquivo:
1. nao execute comandos `git` sem solicitacao explicita do usuario na tarefa atual;
2. confirme sempre que qualquer comando Python, `pip`, `pytest`, `manage.py` ou script operacional esta usando **exclusivamente** `.\.venv\Scripts\python.exe`;
3. e proibido instalar dependencias no Python global; toda instalacao deve acontecer apenas dentro da `.venv` do repositorio;
4. leia o `CLAUDE.md`, os documentos de dominio relacionados e a area do codigo afetada;
5. identifique a natureza da tarefa: descoberta, planejamento, refatoracao, feature, correcao, integracao ou saneamento estrutural;
6. identifique quais modulos internos do app `system` serao impactados: `public`, `identity_access`, `student_registry`, `instructor_ops`, `class_catalog`, `attendance_qr`, `finance_contracts`, `payments_stripe`, `graduation_engine`, `communications`, `documents_lgpd`, `reports_audit`, `settings_seed`;
7. verifique se a mudanca toca alguma regra critica:
   - identidade unica por CPF;
   - multi-papel no mesmo usuario;
   - onboarding transacional;
   - check-in com QR/WebRTC;
   - reserva previa de vaga;
   - inadimplencia ou matricula pausada;
   - trancamento com `pause_collection` na Stripe;
   - motor de graduacao com congelamento de tempo ativo;
   - LGPD, menores, biometria e prontuario medico;
   - exportacao CSV com trava fail-fast;
   - fechamento de caixa com divergencia acima do limiar gerencial;
   - auditoria transversal obrigatoria em fluxos criticos;
8. apresente um plano curto e objetivo antes de implementar, deixando explicitos:
   - objetivo real da mudanca;
   - agregado ou fluxo principal afetado;
   - invariantes que nao podem ser quebradas;
- estratégia de validação ao final.

### Fase 2 - Implementacao limpa e aderente ao dominio
Ao implementar:
1. mantenha views finas e delegue regras complexas para `services.py`, `selectors.py`, `managers.py` ou metodos de dominio;
2. use `transaction.atomic()` em fluxos compostos, especialmente:
   - onboarding de titular + dependentes;
   - criacao de aluno + vinculo financeiro + perfis;
   - confirmacao de pagamento + desbloqueio de acesso;
   - reserva de vaga + consumo de capacidade;
3. nao use hardcode para:
   - chaves e segredos;
   - URLs base;
   - TTL do QR Code;
   - idade minima/configuravel para dependente com credencial;
   - regras de pausa, carencia, tolerancia e limites operacionais;
4. trate integracoes externas como faliveis e auditaveis;
5. garanta que o backend sempre revalide regras criticas, mesmo que a UI ja tenha bloqueado a acao.
6. em catalogo Stripe, nunca deduza vinculacao de plano por heuristica solta quando existir risco de ambiguidade; use mapeamento persistido e explicitamente aprovado;
7. quando um novo `Price` Stripe passar a ser o vigente de um plano, aposente o mapeamento vigente anterior de forma deterministica, sem manter dois candidatos correntes.

### Fase 2.5 - Validação visual obrigatória
Quando a tarefa envolver templates, paginas ou fluxos de interface:
1. leia a tela existente equivalente antes de implementar;
2. preserve o padrao visual ja adotado pelo sistema, em vez de entregar uma versao apenas "funcional";
3. valide responsividade em desktop, tablet e mobile;
4. nao deixe ajuste visual, hierarquia de informacao ou estados vazios para depois;
5. trate consistencia visual e UX como parte da definicao de pronto, nao como acabamento opcional;
6. revise títulos, rótulos, placeholders, mensagens, CTAs e textos de apoio em pt-BR antes de encerrar a tarefa.

### Fase 3 - Validação estrita
Antes de considerar a entrega pronta:
1. valide impacto de modelagem, migracao e permissoes;
2. verifique risco de N+1 em dashboards, listagens e relatorios;
3. confirme que webhooks e callbacks sao idempotentes e auditaveis;
4. cubra a mudanca com testes de unidade e, quando fizer sentido, testes de integracao.

### Fase 4 - Evolucao da spec
Ao terminar:
1. avalie se a tarefa revelou uma nova regra de negocio ou uma lacuna de arquitetura;
2. se revelou, proponha explicitamente atualizacao do `CLAUDE.md` e/ou deste `AGENTS.md`.

Frase de encerramento obrigatoria quando houver nova descoberta relevante:

> **"Identifiquei que nosso CLAUDE.md/AGENTS.md precisa evoluir com base nesta iteracao [motivo]. Deseja que eu gere a atualizacao destes arquivos?"**

---

## 3. Invariantes que o agente nunca pode violar

### 3.1 Identidade e papeis
- Uma pessoa nao pode ser duplicada no sistema para resolver problema de negocio.
- O login usa **CPF como identificador unico de autenticacao**.
- O mesmo usuario pode acumular papeis e perfis de negocio.
- `PROFESSOR`, `ALUNO`, `RESPONSAVEL_FINANCEIRO` e perfis administrativos podem coexistir na mesma identidade.
- Dependente com credencial propria continua vinculado ao responsavel, mas acessa apenas o escopo permitido.

### 3.2 Presenca, reserva e tatame
- O sistema deve validar **antes de abrir a camera** se o aluno pode tentar o check-in.
- A UI nao pode chamar `getUserMedia()` quando houver bloqueio por inadimplencia, pausa, ausencia de reserva ou outra trava de acesso.
- O backend deve revalidar tudo no momento de gravar a presenca.
- Em turmas com capacidade, a vaga e consumida na **reserva previa**, nao na porta.
- O QR valida presenca fisica de quem ja tinha direito a entrar.

### 3.3 Financeiro e trancamento
- Matricula pausada e um estado de negocio local do sistema, mesmo quando a Stripe mantem a assinatura ativa com cobranca pausada.
- Se existir assinatura Stripe elegivel, o trancamento deve integrar com `pause_collection`.
- Aluno `PAUSADO` nao faz check-in.
- Tempo de graduacao nao corre enquanto a matricula estiver pausada.
- O `Price` Stripe vigente de cada plano precisa ser unico e persistido localmente.
- Espelho `dj-stripe`, quando habilitado, complementa auditoria e reconciliacao, mas nao substitui o estado local da assinatura.
- Comprovante manual em `UNDER_REVIEW` mantem o contrato em `PENDING_FINANCIAL` ate decisao administrativa explicita.
- Redirecionamento de sucesso, cancelamento ou retorno visual do checkout nunca concede acesso por si so; liberacao depende de reconciliacao local confiavel, preferencialmente por webhook idempotente.
- Divergencia de caixa acima do limiar configurado deve persistir alerta gerencial e impedir edicao retroativa silenciosa do turno encerrado.

### 3.4 Graduacao
- O motor de graduacao considera **tempo ativo de treino**, nao apenas tempo corrido de calendario.
- Ausencias prolongadas, pausa e regras configuraveis da academia precisam coexistir com a referencia oficial de tempo minimo.

### 3.5 LGPD e dados sensiveis
- Exclusao definitiva nao e `soft delete` simples.
- Quando juridicamente cabivel, deve haver anonimizacao de dados pessoais e eliminacao de dados sensiveis, preservando apenas o minimo tecnico/contabil necessario.
- Selfie, biometria, prontuario medico e dados de menores exigem acesso restrito, trilha de auditoria e minimizacao.
- Solicitacao LGPD destrutiva nao pode ser processada enquanto existirem contratos financeiros locais ativos, pausados, bloqueados ou pendentes que ainda dependam de retencao operacional/contabil.

### 3.6 Exportacoes criticas
- Extracao critica para BI ou CSV so pode iniciar apos validacao obrigatoria do arquivo de controle.
- O arquivo de controle precisa conter a diretiva explicita `EXPORT_ALLOWED=1`.
- Se o arquivo nao existir, nao puder ser criado, estiver bloqueado ou invalido, o processo deve abortar imediatamente.

### 3.7 Auditoria transversal
- Fluxos criticos de autenticacao, financeiro, pagamentos, graduacao, emergencia, PDV e exportacao devem registrar trilha de auditoria propria.
- Log tecnico nao substitui `AuditLog`; ambos podem coexistir quando um atende operacao e o outro atende rastreabilidade de negocio.
- Auditoria nao pode armazenar payload excessivo nem vazar dado sensivel desnecessario.

---

## 4. Regras de qualidade de codigo

### Estrutura
- Prefira monolito modular Django bem organizado a espalhar regra de negocio em arquivos aleatorios.
- Templates nao carregam regra de negocio complexa.
- Regras de dominio ficam no backend.
- Visual, legibilidade operacional e responsividade fazem parte da entrega quando houver interface.

### Codigo limpo
- Evite comentarios, docstrings e anotacoes explicativas.
- Use-os apenas quando uma decisao de negocio nao puder ser inferida pela estrutura do codigo.
- Codigo novo deve expressar o dominio com nomes claros, sem ruido e sem helpers genericos que escondam regra central.

### Limites de complexidade
- Metodo longo ou com muitas decisoes deve ser quebrado.
- View com multiplas responsabilidades deve ser fatiada.
- Sinais (`signals.py`) so podem ser usados quando o acoplamento implicito for realmente aceitavel.
- Se uma regra e central para o dominio, ela nao deve ficar escondida em helper generico.

### Limites Anti-Code Smell (Robocop)
- **Linhas por metodo:** maximo de 25 linhas. Acima disso, extraia submetodos ou mova a regra para servico, selector ou objeto de dominio.
- **Argumentos por funcao:** maximo de 4. Acima disso, use objetos de contexto, `dataclasses` ou parametros nomeados bem estruturados.
- **Consultas ORM:** e proibido executar consultas ao banco dentro de lacos `for` para resolver listagem, dashboard ou relatorio. Use `select_related()` e `prefetch_related()` quando aplicavel.

### ORM e performance
- Em telas de dashboard e listagens, antecipe relacoes com `select_related()` e `prefetch_related()` quando necessario.
- E proibido resolver N+1 no template "sem querer".
- Queries de relatorios devem ser explicitas e auditaveis.

### Configuracao
- O que muda por ambiente vai para `settings.py`, `.env` ou configuracao persistida.
- O que muda por academia deve ser configuravel por modelo, admin ou painel, nao codificado em constante solta.
- Nada sensivel ou operacionalmente variavel deve ficar hardcoded em view, template ou JavaScript de pagina.
- A `.venv` do repositorio e obrigatoria; o agente nao pode usar nem poluir o Python global para instalar, executar testes ou rodar comandos Django.
- Artefatos temporarios de teste devem ficar dentro do workspace do projeto, nunca depender de pasta temporaria global do sistema quando isso puder gerar ruido operacional ou problema de permissao.

---

## 5. Política de testes

Toda mudanca relevante deve, no minimo, considerar testes para:
- identidade unica por CPF;
- multi-papel no mesmo usuario;
- onboarding transacional;
- inadimplencia bloqueando check-in antes da camera;
- reserva previa e consumo de vagas;
- trancamento de matricula com congelamento de graduacao;
- webhooks Stripe com idempotencia;
- checkout Stripe sem liberacao prematura por redirect;
- comprovante manual mantendo bloqueio enquanto estiver em analise;
- fechamento de caixa com sobra/quebra acima do limiar;
- emissao de trilha em `AuditLog` nos fluxos criticos alterados;
- exclusao/anonimizacao LGPD;
- permissoes de dependente vs titular;
- exportacao fail-fast.

Quando a mudanca for critica, o agente deve informar claramente:
1. o que foi testado;
2. o que ainda precisa de teste;
3. quais riscos permanecem.

Para fluxos centrais de dominio, prefira abordagem test-first:
1. ajuste ou adicione o teste que evidencia o comportamento esperado;
2. implemente a menor mudanca estrutural correta;
3. valide regressao nos fluxos adjacentes.

---

## 6. O que o agente deve evitar

- criar dois usuarios para a mesma pessoa;
- criar migracoes manuais em vez de usar `makemigrations`;
- misturar regra financeira com renderizacao de template;
- confiar apenas em bloqueio visual de frontend;
- acoplar logica da Stripe diretamente em view gigante;
- colocar regra de graduacao em JavaScript;
- expor dados medicos ou financeiros a dependente com credencial restrita;
- resolver lacuna de dominio com `if` solto e sem modelagem;
- criar status redundantes sem tabela de estados clara;
- prosseguir com exportacao quando a pre-condicao do arquivo de controle falhar;
- executar comandos `git` sem pedido explicito do usuario na tarefa atual;
- entregar template sem validar consistencia visual e responsividade.

---

## 7. Formato esperado das respostas do agente

Ao responder uma tarefa tecnica, organize a entrega em linguagem objetiva:
1. contexto e impacto;
2. plano;
3. implementacao proposta;
4. riscos e validacoes;
5. atualizacao necessaria da spec, se houver.

Se existir conflito entre pedido do usuario e regra estrutural do projeto, explique o conflito e proponha a forma correta de implementar.

---

## 8. Fonte de verdade

- **Como trabalhar:** este `AGENTS.md`.
- **O que o sistema e e como deve funcionar:** `CLAUDE.md`.
- **Requisitos funcionais e telas:** PRD, mapeamento de telas e documentos de negocio do projeto.
- **Fluxos operacionais e integracoes reais:** codigo do dominio, testes existentes e documentacao complementar do projeto.

Se houver contradicao entre codigo legado e spec atual, o agente deve sinalizar isso explicitamente e priorizar a correcao estrutural.
