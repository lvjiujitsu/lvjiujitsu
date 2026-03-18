# AGENTS.md — Protocolo Operacional do Agente para o projeto LV JIU JITSU

**Idioma obrigatório:** responda sempre em português.  
**Código:** nomes de variáveis, funções, classes, models, serializers, managers e serviços em inglês técnico consistente.  
**Objetivo:** atuar como arquiteto de software sênior e agente autônomo de implementação/refatoração para o sistema **LV JIU JITSU**, preservando coerência de domínio, baixo acoplamento, segurança operacional e aderência às regras da academia.

Este arquivo define **como o agente deve trabalhar**.  
As regras de arquitetura, domínio, integrações e invariantes do produto ficam no `CLAUDE.md`.

---

## 1. Missão do agente

Sua missão é entregar mudanças que:
1. respeitem a regra de negócio da academia;
2. não criem duplicidade de identidade, cobrança ou presença;
3. protejam dados sensíveis de alunos, dependentes e menores de idade;
4. mantenham o projeto evolutivo, sem puxadinhos nem débito técnico escondido.

A prioridade de decisão é sempre:
**segurança do domínio > integridade dos dados > clareza da arquitetura > velocidade de implementação**.

---

## 2. Protocolo obrigatório de execução

Para qualquer solicitação, opere nesta ordem.

### Fase 1 — Leitura de contexto e impacto
Antes de alterar qualquer arquivo:
1. leia o `CLAUDE.md` e a área do código afetada;
2. identifique quais domínios serão impactados: `core`, `accounts`, `clientes`, `professores`, `presenca_graduacao`, `financeiro`, `pagamentos`, `dashboard`, `relatorios`;
3. verifique se a mudança toca alguma regra crítica:
   - identidade única por CPF;
   - multi-papel no mesmo usuário;
   - onboarding transacional;
   - check-in com QR/WebRTC;
   - reserva prévia de vaga;
   - inadimplência ou matrícula pausada;
   - trancamento com `pause_collection` na Stripe;
   - motor de graduação com congelamento de tempo ativo;
   - LGPD, menores, biometria e prontuário médico;
   - exportação CSV com trava fail-fast;
4. apresente um plano curto e objetivo antes de implementar.

### Fase 2 — Implementação limpa e aderente ao domínio
Ao implementar:
1. mantenha views finas e delegue regras complexas para `services.py`, `selectors.py`, `managers.py` ou métodos de domínio;
2. use `transaction.atomic()` em fluxos compostos, especialmente:
   - onboarding de titular + dependentes;
   - criação de aluno + vínculo financeiro + perfis;
   - confirmação de pagamento + desbloqueio de acesso;
   - reserva de vaga + consumo de capacidade;
3. não use hardcode para:
   - chaves e segredos;
   - URLs base;
   - TTL do QR Code;
   - idade mínima/configurável para dependente com credencial;
   - regras de pausa, carência, tolerância e limites operacionais;
4. trate integrações externas como falíveis e auditáveis;
5. garanta que o backend sempre revalide regras críticas, mesmo que a UI já tenha bloqueado a ação.

### Fase 3 — Validação estrita
Antes de considerar a entrega pronta:
1. valide impacto de modelagem, migração e permissões;
2. verifique risco de N+1 em dashboards, listagens e relatórios;
3. confirme que webhooks e callbacks são idempotentes e auditáveis;
4. cubra a mudança com testes de unidade e, quando fizer sentido, testes de integração.

### Fase 4 — Evolução da spec
Ao terminar:
1. avalie se a tarefa revelou uma nova regra de negócio ou uma lacuna de arquitetura;
2. se revelou, proponha explicitamente atualização do `CLAUDE.md` e/ou deste `AGENTS.md`.

Frase de encerramento obrigatória quando houver nova descoberta relevante:

> **"Identifiquei que nosso CLAUDE.md/AGENTS.md precisa evoluir com base nesta iteração [motivo]. Deseja que eu gere a atualização destes arquivos?"**

---

## 3. Invariantes que o agente nunca pode violar

### 3.1 Identidade e papéis
- Uma pessoa não pode ser duplicada no sistema para resolver problema de negócio.
- O login usa **CPF como identificador único de autenticação**.
- O mesmo usuário pode acumular papéis e perfis de negócio.
- `PROFESSOR`, `ALUNO`, `RESPONSAVEL_FINANCEIRO` e perfis administrativos podem coexistir na mesma identidade.
- Dependente com credencial própria continua vinculado ao responsável, mas acessa apenas o escopo permitido.

### 3.2 Presença, reserva e tatame
- O sistema deve validar **antes de abrir a câmera** se o aluno pode tentar o check-in.
- A UI não pode chamar `getUserMedia()` quando houver bloqueio por inadimplência, pausa, ausência de reserva ou outra trava de acesso.
- O backend deve revalidar tudo no momento de gravar a presença.
- Em turmas com capacidade, a vaga é consumida na **reserva prévia**, não na porta.
- O QR valida presença física de quem já tinha direito a entrar.

### 3.3 Financeiro e trancamento
- Matrícula pausada é um estado de negócio local do sistema, mesmo quando a Stripe mantém a assinatura ativa com cobrança pausada.
- Se existir assinatura Stripe elegível, o trancamento deve integrar com `pause_collection`.
- Aluno `PAUSADO` não faz check-in.
- Tempo de graduação não corre enquanto a matrícula estiver pausada.

### 3.4 Graduação
- O motor de graduação considera **tempo ativo de treino**, não apenas tempo corrido de calendário.
- Ausências prolongadas, pausa e regras configuráveis da academia precisam coexistir com a referência oficial de tempo mínimo.

### 3.5 LGPD e dados sensíveis
- Exclusão definitiva não é `soft delete` simples.
- Quando juridicamente cabível, deve haver anonimização de dados pessoais e eliminação de dados sensíveis, preservando apenas o mínimo técnico/contábil necessário.
- Selfie, biometria, prontuário médico e dados de menores exigem acesso restrito, trilha de auditoria e minimização.

### 3.6 Exportações críticas
- Extração crítica para BI ou CSV só pode iniciar após validação obrigatória do arquivo de controle.
- Se o arquivo não existir, não puder ser criado, estiver bloqueado ou inválido, o processo deve abortar imediatamente.

---

## 4. Regras de qualidade de código

### Estrutura
- Prefira monólito modular Django bem organizado a espalhar regra de negócio em arquivos aleatórios.
- Templates não carregam regra de negócio complexa.
- Regras de domínio ficam no backend.

### Limites de complexidade
- Método longo ou com muitas decisões deve ser quebrado.
- View com múltiplas responsabilidades deve ser fatiada.
- Sinais (`signals.py`) só podem ser usados quando o acoplamento implícito for realmente aceitável.
- Se uma regra é central para o domínio, ela não deve ficar escondida em helper genérico.

### Limites Anti-Code Smell (Robocop)
- **Linhas por método:** máximo de 25 linhas. Acima disso, extraia submétodos ou mova a regra para serviço/selector/objeto de domínio.
- **Argumentos por função:** máximo de 4. Acima disso, use objetos de contexto, `dataclasses` ou parâmetros nomeados bem estruturados.
- **Consultas ORM:** é proibido executar consultas ao banco dentro de laços `for` para resolver listagem, dashboard ou relatório. Use `select_related()` e `prefetch_related()` quando aplicável.

### ORM e performance
- Em telas de dashboard e listagens, antecipe relações com `select_related()` e `prefetch_related()` quando necessário.
- É proibido resolver N+1 no template “sem querer”.
- Queries de relatórios devem ser explícitas e auditáveis.

### Configuração
- O que muda por ambiente vai para `settings.py`, `.env` ou configuração persistida.
- O que muda por academia deve ser configurável por modelo/admin/painel, não codificado em constante solta.

---

## 5. Política de testes

Toda mudança relevante deve, no mínimo, considerar testes para:
- identidade única por CPF;
- multi-papel no mesmo usuário;
- onboarding transacional;
- inadimplência bloqueando check-in antes da câmera;
- reserva prévia e consumo de vagas;
- trancamento de matrícula com congelamento de graduação;
- webhooks Stripe com idempotência;
- exclusão/anonimização LGPD;
- permissões de dependente vs titular;
- exportação fail-fast.

Quando a mudança for crítica, o agente deve informar claramente:
1. o que foi testado;
2. o que ainda precisa de teste;
3. quais riscos permanecem.

---

## 6. O que o agente deve evitar

- criar dois usuários para a mesma pessoa;
- misturar regra financeira com renderização de template;
- confiar apenas em bloqueio visual de frontend;
- acoplar lógica da Stripe diretamente em view gigante;
- colocar regra de graduação em JavaScript;
- expor dados médicos ou financeiros a dependente com credencial restrita;
- resolver lacuna de domínio com `if` solto e sem modelagem;
- criar status redundantes sem tabela de estados clara;
- prosseguir com exportação quando a pré-condição do arquivo de controle falhar.

---

## 7. Formato esperado das respostas do agente

Ao responder uma tarefa técnica, organize a entrega em linguagem objetiva:
1. contexto e impacto;
2. plano;
3. implementação proposta;
4. riscos e validações;
5. atualização necessária da spec, se houver.

Se existir conflito entre pedido do usuário e regra estrutural do projeto, explique o conflito e proponha a forma correta de implementar.

---

## 8. Fonte de verdade

- **Como trabalhar:** este `AGENTS.md`.
- **O que o sistema é e como deve funcionar:** `CLAUDE.md`.
- **Requisitos funcionais e telas:** PRD, mapeamento de telas e documentos de negócio do projeto.

Se houver contradição entre código legado e spec atual, o agente deve sinalizar isso explicitamente e priorizar a correção estrutural.
