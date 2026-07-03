# PRD-121: Home do cliente com dependentes, mensalidades e CRUD modal

## Summary
Corrigir a home autenticada do aluno/responsável para voltar a exibir mensalidade do titular, separar mensalidade de dependentes, mostrar graduação/histórico de cada dependente e disponibilizar CRUD curto em popup/modal. O cabeçalho grande com saudação/data sai da área principal; os dados do cliente passam para um ícone na topbar, ao lado da troca de tema.

## Demand type
Correção funcional + UI + Django MVT.

## Current problem
- A home atual pode ocultar mensalidade quando a pessoa treina mas `portal_is_student` não está verdadeiro.
- Dependentes aparecem como lista simples, sem mensalidade separada, graduação detalhada, histórico e ações de edição/remoção.
- O link textual "Adicionar dependente" quebra o padrão de ações icônicas.
- O cabeçalho "Olá, Aluno" ocupa a tela e deve virar popup de dados do cliente.
- Ações curtas de dependente não devem trocar de tela.

## Goal
Entregar uma home operacional de cliente em que titular e dependentes tenham informações financeiras e de graduação visíveis, com ações de adicionar/editar/remover em popup/modal e permissões validadas no backend.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`

### Adjacent files consulted
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/models/plan.py`
- `system/services/membership.py`
- `system/services/graduation.py`
- `system/urls.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

### Internet / official documentation
- Django 5.2 generic editing views: `https://docs.djangoproject.com/en/5.2/topics/class-based-views/generic-editing`
- Django 5.2 class-based editing reference: `https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing`
- Django 5.2 messages framework: `https://docs.djangoproject.com/en/5.2/ref/contrib/messages`

### Context7 / MCPs / tools verified
- Context7: `/websites/djangoproject_en_5_2`, consulta sobre `FormView`/`UpdateView`/`DeleteView`, redirects POST, messages e remoção protegida.
- Browser interno será usado na validação da UI.

### Limitations found
- O banco local do usuário foi alterado em ciclos anteriores; a validação visual deve considerar o estado atual e também testes isolados.
- A remoção de dependente será remoção do vínculo responsável -> dependente, não deleção física de `Person`, para preservar histórico financeiro, graduação e auditoria.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
O usuário pediu explicitamente: "gere um PRD de correção com as informações e implemente." A implementação local, testes e validação no navegador interno estão autorizados pelo pedido atual e pelo protocolo do repositório.

## Execution prompt
### Persona
Agente Django/UI sênior no LV JIU JITSU.

### Action
Corrigir a home do cliente e o CRUD curto de dependentes, mantendo regra de negócio no backend e ações visuais em modal.

### Context
O portal usa Django 5.2 server-rendered, `system/` como app de domínio, assets em `static/system/` e templates em `templates/`. A home unificada já tem modal de dependente por iframe.

### Constraints
- Não editar `staticfiles/`.
- Não apagar pessoa dependente fisicamente.
- Não criar regra de negócio em template/JS.
- Não mostrar ação destrutiva sem POST e confirmação.
- Não mostrar CRUD de dependente de outra pessoa.
- Atualizar `?v=` quando asset editado.

### Acceptance criteria
- [ ] A home não renderiza mais o bloco grande `.page-header` com data/saudação/role.
- [ ] A topbar exibe ícone de dados do cliente ao lado da troca de tema e abre popup com dados do cliente, perfis e ações de dependente.
- [ ] A seção de mensalidade aparece para o titular quando ele treina ou possui dependentes, mesmo se a flag `portal_is_student` não estiver verdadeira.
- [ ] A mensalidade do titular e a mensalidade de cada dependente ficam separadas e identificadas.
- [ ] Cada dependente exibe graduação atual, resumo de progresso, histórico e aulas do dia.
- [ ] Cada dependente tem ações icônicas para editar e remover.
- [ ] Editar dependente abre popup/modal, valida campos no servidor e só permite dependente vinculado ao cliente logado.
- [ ] Remover dependente usa POST, confirma no front, valida vínculo no servidor e remove apenas `PersonRelationship`.
- [ ] Usuário sem vínculo não edita nem remove dependente de terceiro.
- [ ] UI funciona em tema claro/escuro, desktop/mobile e sem erro crítico de console.

### Expected evidence
- Testes Django focados executados com resultado real.
- `manage.py check` executado.
- Validação no navegador interno em `/home/` com estado de dependente.
- PRD atualizado com evidências executadas.

### Output format
Resumo curto em pt-BR: implementado, evidências, limitações e status.

## Scope
- Home do cliente autenticado.
- Cards de dependentes.
- Popup de dados do cliente.
- Modal iframe reaproveitado para adicionar/editar dependente.
- Remoção de vínculo de dependente.
- Testes focados.

## Out of scope
- Loja de materiais.
- Histórico completo de compras.
- Alteração de schema.
- Deleção física de `Person`.
- Redesign de todo dashboard administrativo/professor.
- Migração remota, deploy, HG ou produção.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-121-home-cliente-dependentes-mensalidades-crud.md`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `templates/dependents/dependent_edit.html`
- `templates/dependents/dependent_registration_done.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_home_dependents_section.py`
- `system/tests/test_dependent_registration.py`

## Risks and edge cases
- Dependente com mensalidade própria versus coberto pelo responsável.
- Responsável que também treina.
- Pessoa com matrícula/faixa mas sem `portal_is_student`.
- Dependente sem graduação registrada.
- Dependente com histórico financeiro que não pode ser apagado.
- Modal iframe sem suporte a `showModal`.
- Tema e foco em mobile.

## Rules and constraints
- `GET /dependents/add/` sem `modal=1` continua redirecionando para `/home/?dependent_modal=1`.
- `GET /dependents/<pk>/edit/` sem `modal=1` redireciona para home abrindo modal previsível.
- `POST /dependents/<pk>/remove/` remove vínculo apenas quando `source_person` é o cliente logado.
- Ações de dependente usam ícones com `aria-label` e `title`.

## Plan
1. Criar testes de contrato para home e dependente.
2. Implementar form/view/URL de edição.
3. Implementar view POST de remoção do vínculo.
4. Ajustar contexto da home para cobrança, perfil do cliente e dependentes enriquecidos.
5. Ajustar template, CSS e JS.
6. Executar testes, `manage.py check` e validação visual.
7. Atualizar PRD e auditoria de limpeza.

## Visual hierarchy
- Topbar: logo à esquerda; ações à direita: dados do cliente, tema, sair.
- Conteúdo: começa direto em "Minha área" ou na primeira seção operacional.
- Mensalidade: seção própria do titular; dependentes têm mensalidade resumida dentro do card.
- Dependentes: lista de cards com nome, badges, mensalidade, graduação, aulas e ações icônicas.

## Wireframe
### Região: Topbar
- Logo LV.
- Botão ícone "Dados do cliente".
- Botão ícone "Alternar tema".
- Botão ícone "Sair".

### Região: Popup Dados do Cliente
- Cabeçalho: nome completo e perfis ativos.
- Dados: CPF, e-mail, telefone.
- Plano do titular: status, nome do plano e vigência quando existir.
- Dependentes: contador e ação icônica para adicionar.

### Região: Conteúdo Principal
- Seção "Minha área" quando houver treino pessoal.
- Seção "Turmas de hoje".
- Seção "Graduação" do titular.
- Seção "Mensalidade" do titular.
- Seção "Meus dependentes": cards com financeiro, graduação, histórico e CRUD.

### Estados da tela
- Sem dependentes: estado vazio com ação icônica/texto curto para adicionar.
- Com dependentes: lista operacional.
- Sem mensalidade: badge "Sem plano ativo".
- Mensalidade ativa/em atraso/isenta: badge semântico.
- Remoção: confirmação antes do POST.

## State machine
### Popup de dados do cliente
- Estados: `closed` -> `open` -> `closed`.
- Fechamento: botão, backdrop ou `Esc`.

### Modal de dependente
- Estados: `closed` -> `open` -> `submitting` -> `success` ou `error`.
- Sucesso: iframe envia `dependent-modal-done`, modal fecha e home recarrega.

### Remover dependente
- Estados: `idle` -> `confirmable` -> `submitting` -> `success` ou `error`.
- Sucesso: redirect para home com mensagem.

## Test plan
### Tests to author
- Home renderiza sem `.page-header` e com botão/modal de cliente.
- Home exibe mensalidade para pessoa que treina mesmo sem depender apenas da flag `portal_is_student`.
- Card de dependente exibe mensalidade separada, graduação, histórico e ações icônicas.
- Editar dependente altera campos permitidos para vínculo próprio.
- Editar dependente de outro responsável é bloqueado.
- Remover dependente remove apenas vínculo próprio.

### Execution authorization
Autorizada pelo pedido atual e pelo `AGENTS.md`.

### Execution evidence
- Pendente.

## Visual validation
- Pendente.

## ORM validation
- Pendente.

## Quality validation
- Pendente.

## Evidence
- Pendente.

## Implemented
- Pendente.

## Cleanup findings
- Pendente.

## Follow-up PRDs
- Pendente.

## Deviations from plan
- Pendente.

## Pending
- Pendente.

## Final status
Não concluída.
