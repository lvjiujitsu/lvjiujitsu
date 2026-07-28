# PRD-075: Fundação UI, rotas em inglês e CRUD modal

## Summary
Reconstruir a fundação autenticada do LV para que os módulos CRUD usem rotas canônicas em inglês, interface pt-BR e ações curtas em modal/dialog na mesma tela, conforme o padrão descrito no contrato atual, sem copiar domínio externo.

## Demand type
Reimplementação UI/UX multi-módulo + governança de rotas.

## Current problem
- `system/urls.py` usa paths em português para módulos administrativos (`pessoas`, `planos`, `administracao`, `turmas`, `financeiro`, `graduacao`, `materiais`), enquanto a solicitação atual exige rotas em inglês.
- Inventário local encontrou 49 `template_name` em views e 36 templates ausentes.
- `templates/lv/base.html`, `templates/lv/modal_base.html`, `templates/lv/modal_done.html`, `static/system/css/lv/base.css`, `static/system/js/lv/crud_modal.js` e `crud_frame.js` não existem.
- `PersonCreateView`, `PersonUpdateView` e `PersonDetailView` apontam para templates modais inexistentes.
- Templates existentes de Pessoas/Home/Planos são HTML standalone, com tema e scripts inline, em desacordo com a fundação compartilhada exigida.
- PRD-066 declara parte da fundação como entregue, mas o código atual não contém os arquivos.

## Goal
- Criar shell autenticado único e fundação modal reutilizável.
- Definir rotas canônicas em inglês com nomes de URL já em inglês.
- Manter labels e mensagens do front em pt-BR.
- Implementar CRUD curto em modal/dialog para Pessoas como referência.
- Preparar replicação para Planos, Turmas, Materiais, Financeiro e Graduação.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-066-padrao-visual-modal-crud.md`
- `docs/prd/PRD-068-rework-limpo-pessoas-fundacao-lv.md`
- `docs/prd/PRD-065-hubs-administrativos-modulos-lv.md`
- `system/urls.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `static/system/css/people/people.css`
- `templates/home/dashboard.html`

### Adjacent files consulted
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`

### Internet / official documentation
- Django 5.2 templates: https://docs.djangoproject.com/en/5.2/topics/templates/
- Django 5.2 class-based auth/access docs: https://docs.djangoproject.com/en/5.2/topics/auth/default/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: templates e access mixins.
- Browser interno ainda não usado porque não houve alteração visual nesta etapa.

### Limitations found
- Várias views apontam para templates ausentes; validar visualmente todos os módulos exige implementação por fases.
- Rotas antigas em português podem precisar de redirects temporários para não quebrar links existentes.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual: rotas em inglês, front em português, fluxo sem redirecionar para nova tela e com popup/modal.

## Visual hierarchy
- Shell: topbar compacta com logo, navegação por permissões, alternância de tema e logout.
- Conteúdo: header operacional, filtros, lista densa e ações icônicas.
- Modal CRUD: header com contexto, corpo server-rendered e ações claras.
- Mobile: uma coluna, ações 44x44, modal quase full-screen sem overflow horizontal.

## Wireframe
### Região: Shell
- Logo LV à esquerda.
- Navegação por módulos permitidos.
- Tema e usuário à direita.

### Região: Hub/listagem
- Eyebrow do módulo.
- Título em pt-BR.
- Ação primária icônica/textual quando permitida.
- Filtros antes da lista.
- Lista/card operacional com ações: visualizar, editar, excluir.

### Região: Modal
- Título e botão fechar.
- Formulário ou detalhe.
- Cancelar/salvar ou confirmação destrutiva.

### Estados da tela
- `empty`, `populated`, `filtered`, `modal-open`, `submitting`, `success`, `error`, `forbidden`.

## State machine
- CRUD modal: `closed -> open -> submitting -> success|error`.
- Delete confirmation: `closed -> confirmable -> submitting -> success|blocked`.
- Route compatibility: `old-portuguese-path -> redirect/query modal` apenas se necessário durante transição.

## Scope
- Criar fundação `templates/lv/*`, `static/system/css/lv/base.css`, `static/system/js/lv/*`.
- Migrar Pessoas para base + modal CRUD como referência.
- Criar redirects ou aliases para rotas antigas quando necessário.
- Escrever testes de renderização real para templates existentes.
- Atualizar `?v=` dos assets alterados.

## Out of scope
- Implementar todos os CRUDs de módulos nesta mesma PRD; isso pertence à PRD-077.
- Alterar regra de papel/capacidade; pertence à PRD-074.

## Impacted files
- `system/urls.py`
- `system/views/person_views.py`
- `templates/lv/*`
- `templates/people/*`
- `static/system/css/lv/base.css`
- `static/system/js/lv/theme.js`
- `static/system/js/lv/crud_modal.js`
- `static/system/js/lv/crud_frame.js`
- testes de renderização/rotas

## Risks and edge cases
- Rotas em inglês podem quebrar links históricos se não houver transição controlada.
- Modal em iframe precisa de `X-Frame-Options` seguro e mesma origem.
- POST inválido deve reabrir modal com erros por campo.
- Permissões devem ser validadas no backend, não só ocultadas.

## Rules and constraints
- UI pt-BR.
- Código, nomes técnicos e rotas canônicas em inglês.
- Sem JS inline de comportamento.
- Sem `innerHTML` com dados do usuário.
- Não editar `staticfiles/`.

## Plan
- [x] Escrever teste de inventário/renderização real para as rotas de Pessoas.
- [x] Criar fundação compartilhada (`templates/lv/*`, `static/system/css/lv/base.css`, `static/system/js/lv/*`).
- [x] Migrar Pessoas para modal CRUD (create/edit em iframe modal; detalhe mantém página dedicada, exceção documentada por concentrar financeiro/graduação).
- [x] Adicionar rotas canônicas em inglês (`/people/...`) com redirect de compatibilidade das rotas antigas em português (`/pessoas/...`).
- [x] Validar desktop/mobile/claro/escuro no navegador interno.
- [ ] Replicar o padrão para os demais módulos (Planos, Turmas, Materiais, Financeiro, Graduação) — escopo da PRD-077.

## Test plan
### Tests to author
- Cada rota canônica de Pessoas renderiza 200 para perfil permitido.
- Rotas antigas redirecionam para as canônicas.
- Modal `?modal=1` renderiza template modal; POST válido renderiza `lv/modal_done.html` e persiste no banco.

### Execution authorization
Autorizada localmente.

### Execution evidence
- Novo arquivo `system/tests/test_lv_foundation_people.py` com 8 testes: rota inglesa renderiza, 3 redirects de rotas antigas, modal de criar/editar/visualizar renderiza o template modal correto, POST válido no modal cria a pessoa e renderiza `lv/modal_done.html`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_people --verbosity 2` — 8 testes OK (Red real antes: CPF/sexo biológico inválidos no dado de teste; Green real depois de corrigir o dado).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 275 testes OK (suíte completa, sem regressão).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Executada no navegador interno em `http://localhost:8000/people/` logado como admin técnico:
- Desktop, tema escuro: lista renderiza com botões Detalhe/Editar/Excluir; modal de criação abre em `<dialog>` com iframe, mesmo tema; POST cria pessoa sem navegar de tela (7→8 pessoas) e fecha sozinho via `postMessage`.
- Edição em modal pré-preenche os campos corretamente.
- Exclusão via `<dialog>` de confirmação com nome dinâmico da pessoa; POST real exclui e mostra mensagem de sucesso, sem navegar para página de confirmação separada.
- Tema claro: modal e shell consistentes.
- Mobile (375×812): sem overflow horizontal (`scrollWidth === innerWidth`); modal ocupa quase a tela cheia ancorado à base.
- Bug real encontrado e corrigido durante a validação: `.crud-modal__frame { height: min(85vh, 100%) }` no breakpoint mobile colapsava para 150px (altura padrão de iframe sem tamanho resolvido, porque o `<dialog>` não tem altura própria para o `100%` referenciar). Corrigido para `height: 80vh` (unidade de viewport, não depende do pai).
- Também corrigido durante a validação: um processo Python remanescente de uma sessão anterior estava preso na porta 8000 servindo templates desatualizados; documentado aqui para o próximo agente não perder tempo com o mesmo sintoma — sempre matar processos na porta antes de validar visualmente.

## ORM validation
Dados reais do banco de desenvolvimento local (seeds já aplicadas); pessoa de teste criada via modal (`529.982.247-25` / `390.533.447-05`) e removida ao final da validação.

## Quality validation
- `manage.py check`
- `manage.py test system.tests.test_lv_foundation_people` e `manage.py test system` completos
- Navegador interno (desktop, mobile, claro, escuro)

## Evidence
- Inventário `template_name -> exists` retornou 36 templates ausentes (permanece válido para os módulos ainda não migrados; ver PRD-078).
- `templates/lv/*` e `static/system/js/lv/*` não existiam antes desta execução.
- `templates/people/person_list.html` e `person_form.html` continham tema e JS inline (corrigido para Pessoas nesta PRD; outros módulos ficam para PRD-084).
- `system/urls.py` continha paths em português para Pessoas (corrigido nesta PRD; demais módulos ficam para PRD-077/078).

## Implemented
- `static/system/css/lv/base.css`: tokens compartilhados + shell do modal CRUD (`dialog.crud-modal`, `.confirm-delete-dialog`, `.modal-frame`).
- `static/system/js/lv/theme_boot.js`, `theme_toggle.js`, `crud_modal.js`, `modal_child.js`, `confirm_delete.js`: sem JS inline, comunicação pai/iframe via `postMessage` restrita à mesma origem.
- `templates/lv/modal_frame.html` e `templates/lv/modal_done.html`: shell reutilizável do iframe modal e página de conclusão.
- `templates/people/person_form_modal.html` e `templates/people/person_detail_modal.html`: variantes modais de Pessoas.
- `templates/people/person_list.html`: botões Criar/Editar abrem modal via `data-crud-modal-open`; Excluir abre `<dialog>` de confirmação; scripts inline removidos.
- `system/urls.py`: rotas de Pessoas migradas para `/people/...` (inglês); rotas antigas `/pessoas/...` viram `RedirectView` para as novas.
- `system/tests/test_lv_foundation_people.py`: 8 testes cobrindo rotas, redirects e o fluxo modal completo (GET e POST).

## Cleanup findings
- Nenhum resíduo temporário deixado no repositório (o processo Python remanescente na porta 8000 era de sessão anterior, não gerado por este trabalho, e foi encerrado).
- Nenhum comentário/docstring desnecessário adicionado.
- Dívida fora do escopo permanece em PRD-077 (demais módulos), PRD-078 (templates administrativos ainda ausentes) e PRD-084 (tokens/estilo inline nos módulos restantes).

## Follow-up PRDs
- PRD-077 para replicar o padrão modal/rotas em inglês nos demais módulos.
- PRD-078 para os templates administrativos ainda ausentes.
- PRD-084 para tokens/estilo inline nos módulos ainda não migrados.

## Deviations from plan
- Detalhe de pessoa (`PersonDetailView`) manteve página dedicada como ação principal (só criou o template modal compacto já referenciado no código, sem trigger no card), por ser uma tela rica (financeiro, graduação, histórico) — exceção explicitamente documentada para páginas de detalhe que concentram múltiplas áreas.

## Pending
- Repetir esta fundação para Planos, Turmas, Materiais, Financeiro e Graduação (PRD-077).

## Final status
Concluída com limitações — fundação criada e módulo de referência (Pessoas) com CRUD curto em modal, rotas em inglês e compatibilidade retroativa, testado (8 testes novos + suíte completa de 275) e validado visualmente (desktop/mobile, claro/escuro). Réplica para os demais módulos fica para a PRD-077.
