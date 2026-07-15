# PRD-145: Auditoria operacional de cadastros, pagamentos e documentação

## Summary

Auditar o estado real das PRDs 138–144 contra código, testes e execução observável; corrigir lacunas diretamente relacionadas; homologar pela interface todos os perfis solicitados; revisar a documentação operacional do projeto e remover credenciais expostas nos guias externos do Obsidian.

## Demand type

Auditoria operacional + correção Django/UI quando comprovada + integração sandbox Stripe/Asaas + regeneração documental + revisão de segurança.

## Current problem

- As PRDs 138–144 misturam auditoria read-only, execução posterior e estados finais desatualizados.
- A PRD-140 ainda registra implementação e evidência como pendentes apesar de existir código correspondente no worktree.
- Os guias Render e Supabase externos contêm segredos e credenciais em texto claro, embora alertem que o cofre pode estar em repositório público.
- O guia de teste do cliente mantém trechos específicos de Claude e afirmações contraditórias sobre a confirmação sandbox Asaas.
- Os sete cenários de cadastro solicitados ainda não possuem evidência conjunta de browser, gateway e ORM no estado atual.

## Goal

1. Reconciliar PRDs 138–144 com o código e resultados reais.
2. Corrigir bugs encontrados nos fluxos diretamente exercitados.
3. Criar, pela interface, sete contas/cenários distintos:
   - aluno com Stripe;
   - aluno com Asaas;
   - responsável com aluno e Stripe;
   - responsável com aluno e Asaas;
   - aluno + administrativo;
   - pessoa apenas administrativa;
   - professor.
4. Validar desktop e mobile, console, terminal, gateway sandbox e ORM local.
5. Atualizar os cinco guias externos e os contratos internos afetados.
6. Entregar usuários e senhas de teste sem expor segredos de infraestrutura.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `docs/prd/README.md`
- `docs/prd/PRD-138-auditoria-arquitetural-fluxo-unico-consistencia.md`
- `docs/prd/PRD-139-auditoria-cobertura-total-inventario-completo.md`
- `docs/prd/PRD-140-dependente-wizard-correcoes.md`
- `docs/prd/PRD-141-critica-frontend-problemas.md`
- `docs/prd/PRD-142-critica-backend-performance.md`
- `docs/prd/PRD-143-critica-views-models-forms-mvt.md`
- `docs/prd/PRD-144-pendencias-implementacao-varredura-jul-2026.md`
- Os cinco arquivos `comandos-*.md` indicados pelo usuário no cofre Obsidian.

### Adjacent files consulted

- Fluxos atuais em `system/models/`, `forms/`, `services/`, `selectors/`, `views/`, `urls.py`, `templates/login/register.html`, `static/system/js/auth/register.js` e testes de cadastro/pagamento.
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` e PRD-058.

### Internet / official documentation

- Django 5.2: https://docs.djangoproject.com/en/5.2/topics/db/optimization/
- Stripe CLI: https://docs.stripe.com/stripe-cli/triggers e https://docs.stripe.com/cli/listen
- Asaas sandbox confirm payment: https://docs.asaas.com/reference/confirm-payment
- Asaas sandbox FAQ: https://docs.asaas.com/docs/sandbox-1
- ngrok agent/CLI: https://ngrok.com/docs/agent/cli e https://ngrok.com/docs/agent/api
- Render Django: https://render.com/docs/deploy-django
- Supabase Data API/RLS: https://supabase.com/docs/guides/api/securing-your-api e https://supabase.com/docs/guides/database/postgres/row-level-security

### Context7 / MCPs / tools verified

- Context7 consultado para Django 5.2, Stripe CLI e Supabase.
- Browser interno conectado à rota real `http://localhost:8000/register/`.
- Servidor Django local, ngrok e Stripe CLI detectados ativos.

### Limitations found

- Banco em escopo: SQLite local. HG/produção não serão alterados.
- Asaas e Stripe estão em sandbox/test mode; nenhuma cobrança real é autorizada.
- A documentação oficial Asaas está temporariamente contraditória: a referência específica, atualizada mais recentemente, publica o endpoint de confirmação sandbox; o FAQ ainda diz que não existe. O fluxo deve manter fallback pela interface sandbox.
- Credenciais já expostas em repositório externo exigem rotação nos provedores; esta PRD remove valores dos arquivos, mas não autoriza rotação externa.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery` quando houver alteração visual
- `lv-cleanup-audit`
- `browser:control-in-app-browser`
- `supabase` para o guia HG

## Understanding approved

O pedido atual autoriza auditoria, correções locais, testes, uso da interface, criação dos dados locais/sandbox e atualização dos cinco documentos indicados. Não autoriza deploy, push, escrita em HG/produção nem rotação de credenciais externas.

## Execution prompt

### Persona

Revisor e operador sênior Django, com foco em rastreabilidade, pagamentos sandbox, segurança documental e validação visual.

### Action

Comparar PRDs com o estado real, escrever teste antes de corrigir comportamento, cadastrar os cenários pela UI, verificar gateway/ORM e atualizar contratos e guias.

### Context

Worktree possui mudanças preexistentes extensas do usuário; preservar todo conteúdo fora do escopo e editar apenas arquivos diretamente necessários.

### Constraints

- Não expor chaves, tokens, connection strings ou senhas de infraestrutura.
- Não escrever em HG/produção.
- Não declarar pagamento confirmado sem evidência do sandbox e do ORM.
- Não criar `Person` antes da finalização do pré-cadastro.
- Não editar `staticfiles/`.

### Acceptance criteria

- [x] PRDs 138–144 reconciliadas com evidência atual.
- [x] Segredos removidos dos guias externos; placeholders e instrução de rotação presentes.
- [x] Sete cenários cadastrados pela interface com credenciais entregáveis.
- [x] Aluno/responsável Stripe confirmados por checkout hospedado sandbox e ORM.
- [x] Aluno/responsável Asaas confirmados por sandbox e ORM.
- [x] Perfis administrativos/professor persistidos com papéis e estado corretos.
- [x] Desktop e mobile renderizados sem overflow bloqueante ou erro crítico de console.
- [x] `manage.py check`, testes focados e suíte proporcional executados.
- [x] Documentação interna e externa alinhada ao comportamento observado.

### Expected evidence

- Comandos e saídas de testes/checks.
- Snapshots/screenshots desktop e mobile.
- Eventos/gateway sandbox sem revelar IDs sensíveis desnecessários.
- Consulta ORM consolidada dos sete cenários.
- Diff documental sem segredos.

### Output format

Fechamento em pt-BR com implementado, evidências, não validado, pendências, credenciais de teste e status final.

## Scope

- PRDs 138–145 e índice.
- Cadastro público, finalização, pagamentos Stripe/Asaas e perfis operacionais.
- Contratos internos de cadastro/pagamento/seeds/UI afetados.
- Cinco guias externos indicados pelo usuário.

## Out of scope

- Deploy/push.
- Escrita, reset, migrate, seed ou backfill em HG/produção.
- Rotação efetiva de chaves nos painéis externos.
- Implementar toda a dívida estrutural P2/P3 da PRD-144 sem relação com falha observada nestes fluxos.

## Impacted files

- Definidos após auditoria e falhas reproduzidas; sempre registrados em `Implemented`.

## Risks and edge cases

- CPFs/emails já existentes impedem avanço; gerar dados fictícios inéditos e válidos.
- Webhooks Stripe criam eventos auxiliares e IDs de fixture distintos do checkout original.
- Confirmação Asaas pode exigir fallback pela interface por contradição documental/API.
- Responsável + aluno exige distinguir conta do responsável, dependente, membership e cobrança.
- Perfil administrativo/professor pode produzir solicitação pendente em vez de acesso imediato; validar contrato real antes de afirmar credencial ativa.
- Sessão do browser deve ser limpa entre cadastros para evitar reidratação de wizard anterior.

## Rules and constraints

- TDD para todo bug corrigido.
- Browser interno primeiro; desktop e mobile com viewport explícito e reset ao final.
- Gateway e ORM são evidências distintas.
- Credenciais de contas fictícias podem ser entregues; segredos de infraestrutura não.

## Plan

1. Auditar código e executar suíte baseline.
2. Reproduzir e corrigir lacunas com testes.
3. Homologar os sete cadastros pela interface.
4. Validar desktop/mobile, console, terminal e ORM.
5. Atualizar PRDs e documentação interna/externa.
6. Executar limpeza final, busca de segredos e regressão.

## Test plan

### Tests to author

- Definidos por falhas reproduzidas; não criar testes especulativos.

### Execution authorization

Testes, ORM e dados locais/sandbox autorizados pelo pedido atual.

### Execution evidence

- `manage.py test system` antes da mudança: **675/675 OK**.
- Falhas Red reproduzidas antes das correções:
  - wizard administrativo/professor não criava solicitação;
  - intenção `student` criava pessoa sem tipo;
  - repasse do professor descartava condição/valor;
  - dependente finalizado permanecia inativo;
  - snapshot terminal mantinha senhas.
- Suíte focada final: **72/72 OK** em 19,805 s.
- `manage.py check`: 0 issues.
- `manage.py makemigrations --check --dry-run`: `No changes detected`.
- `python -m compileall -q system`: sem erro.
- Suíte final: **679/679 OK** em 157,706 s.

## Visual validation

- Cadastro público: 1440×900 e 390×844, tema escuro, quatro perfis e CTA íntegros.
- Home do aluno Stripe: 390×844, tema claro, mensalidade ativa e gateway visível.
- Modal “Adicionar dependente”: 1440×900 e 390×844, título, fechamento, progresso
  1/7, formulário rolável e CTA fixo sem sobreposição.
- Detalhe da solicitação do professor: condição “Valor fixo · R$ 300,00” e dois
  horários visíveis antes da aprovação.
- Nove logins executados pela interface; nenhum permaneceu no formulário de login.
- Console final: 0 erros e 0 avisos.
- Evidências:
  - `docs/prd/evidence/prd-145-register-desktop.png`
  - `docs/prd/evidence/prd-145-register-mobile.png`
  - `docs/prd/evidence/prd-145-home-mobile-light.png`
  - `docs/prd/evidence/prd-145-dependent-modal-desktop.png`
  - `docs/prd/evidence/prd-145-dependent-modal-mobile.png`

## ORM validation

- Nove `Person` e nove `PortalAccount` ativos, com senhas verificadas pelo hasher.
- Tipos: 3 alunos, 2 responsáveis, 2 dependentes, 1 administrativo e 1 professor.
- Quatro memberships ativas: 2 `stripe_card` e 2 `asaas_pix`.
- Quatro ordens pagas: provider Stripe/Asaas coerente com o cenário.
- Duas relações `responsible_for`.
- Aluno administrativo: tipo `student` + papel `people-support`; sem plano porque o
  fluxo de acesso operacional não executa matrícula comercial.
- Administrativo pleno: tipo `administrative-assistant` + papel `academy-manager`.
- Professor: solicitação aprovada, conta bancária PIX ativa, turma “Jiu Jitsu
  Auditoria” e horários terça/quinta às 20:30.
- Pré-cadastros 1–4 e 6–8 finalizados; tentativa inválida 5 marcada abandonada.
- Zero campo de senha populado nos oito snapshots terminais auditados.

## Quality validation

- TDD observado em cinco falhas comportamentais.
- `git diff --check` limpo nos dois repositórios.
- Busca por chave Stripe/Asaas, webhook secret, connection string Postgres, secret
  Django e senha SMTP: zero valores nos seis guias revisados.
- `SITE_BASE_URL` local restaurado para o domínio ngrok ativo.
- `lv-cleanup-audit` executada; dívida de professor/turma existente separada na
  PRD-146.

## Evidence

- Stripe: dois checkouts hospedados concluídos com cartão de teste; retorno ao LV,
  membership `stripe_card` ativa e IDs de assinatura/cliente presentes.
- Asaas: duas cobranças PIX confirmadas pelo endpoint oficial do sandbox; retorno ao
  LV, ordem paga e membership `asaas_pix` ativa.
- Interface: nove logins e cinco screenshots persistidos.
- ORM consolidado e suíte de 679 testes registrados acima.

## Implemented

- [x] PRD-145 criada antes das correções.
- [x] `submit_operational_pre_registration()` cria solicitações pendentes reais para
  administrativo e professor com proposta de horário.
- [x] Aprovação de intenção aluno preserva `PersonTypeCode.STUDENT` e concede papel.
- [x] Condição financeira do professor preservada e exibida no detalhe.
- [x] Finalização ativa todos os dependentes e suas contas.
- [x] Finalização/abandono removem recursivamente senhas dos snapshots.
- [x] PRDs 138–144 reconciliadas sem apagar o histórico.
- [x] Cinco guias externos e dois contratos internos atualizados.
- [x] Sete cenários homologados pela interface e aprovados quando aplicável.

## Cleanup findings

- Credenciais de infraestrutura em texto claro nos guias externos foram removidas;
  rotação externa continua obrigatória.
- O modo público de professor “turmas existentes” é visível e validado no form, mas
  não possui workflow backend compatível com consentimento do professor atual.
- Nenhum resíduo, temporário, migration inesperada ou edição em `staticfiles/` foi
  introduzido.

## Follow-up PRDs

- [PRD-146](PRD-146-professor-publico-vinculo-turmas-existentes.md): definir vínculo
  principal/assistente/substituição, aprovadores e decisão parcial antes de implementar.

## Deviations from plan

- A conta sandbox Asaas tinha o domínio HG cadastrado e rejeitava callback para o
  ngrok. Os dois pagamentos foram confirmados no sandbox com `SITE_BASE_URL`
  temporariamente alinhado ao domínio cadastrado; a configuração local foi restaurada.
- A auditoria encontrou duas falhas adicionais diretamente relacionadas ao fluxo:
  dependentes inativos e senhas em snapshots. Ambas foram corrigidas e cobertas.

## Pending

- Rotacionar nos provedores as credenciais anteriormente expostas; não autorizado nesta
  execução.
- Decisão de produto da PRD-146.
- HG/produção não foram alterados nem homologados.

## Final status

**Concluída com limitações** — todos os cenários solicitados foram cadastrados e
validados localmente/sandbox; ficam pendentes apenas rotação externa, decisão da
PRD-146 e qualquer validação em HG/produção.
