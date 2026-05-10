# PRD-016: Identidade no menu lateral

## Resumo do que será implementado
Exibir no topo do menu lateral o nome da pessoa logada e sua classificação de acesso.

## Tipo de demanda
Correção pontual de interface autenticada com teste de renderização.

## Problema atual
O menu lateral mostra apenas o rótulo "Menu", navegação, tema e saída. Não há confirmação clara de qual conta está autenticada.

## Objetivo
O topo do menu lateral deve mostrar:
- nome da pessoa logada no portal e tipo de vínculo, quando houver `PortalAccount`;
- usuário técnico e classificação de administrador técnico, quando o acesso for técnico.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `templates/base.html`
- `system/context_processors.py`
- `system/middleware.py`
- `system/views/portal_mixins.py`

### Arquivos adjacentes consultados
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`

### Internet / documentação oficial
- Não aplicável. Mudança usa contratos locais de template, middleware e testes Django.

### MCPs / ferramentas verificadas
- PowerShell — OK — leitura dos arquivos.
- Django test client — a validar por teste automatizado.
- Browser/Playwright — a validar visualmente após implementação.

### Limitações encontradas
- `rg` segue indisponível por acesso negado no ambiente; buscas feitas com PowerShell.
- O worktree já possui alterações não relacionadas anteriores.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD + TDD.

### Ação
Adicionar indicador de identidade no menu lateral autenticado.

### Contexto
`PortalSessionMiddleware` injeta `request.portal_person`, `request.portal_account`, `request.technical_admin_user` e flags de papel no request. `templates/base.html` renderiza o drawer compartilhado.

### Restrições
- sem regra de negócio no JavaScript
- sem migração
- texto visível em pt-BR
- não duplicar por tela
- preservar menu responsivo

### Critérios de aceite
- [x] Conta de portal deve ver o próprio nome no topo do menu lateral.
- [x] Conta de portal deve ver sua classificação/tipo de vínculo no topo do menu lateral.
- [x] Acesso técnico deve ver usuário técnico e classificação técnica.
- [x] O bloco não deve aparecer em páginas públicas sem autenticação.
- [x] O texto deve caber em desktop e mobile.

### Evidências esperadas
- Testes de renderização passando.
- `manage.py check` passando.
- Validação visual do drawer.

### Formato de saída
Código implementado + testes + evidências.

## Escopo
Template base, CSS do portal, testes de views autenticadas e PRD.

## Fora do escopo
Alterar autenticação, permissões, rotas, cadastro, login ou regras de papel.

## Arquivos impactados
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `docs/prd/PRD-016-identidade-menu-lateral.md`

## Riscos e edge cases
- Usuário técnico sem nome completo.
- Pessoa sem tipo de vínculo.
- Nome longo quebrando layout do drawer.
- Conta técnica e conta de portal presentes simultaneamente.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem migrações
- validação obrigatória
- sem hardcode de pessoa específica

## Plano
- [x] 1. Contexto e leitura
- [x] 2. Testes (Red)
- [x] 3. Implementação
- [x] 4. Validação técnica
- [x] 5. Validação visual
- [x] 6. Atualização documental

## Validação visual
### Desktop
Playwright em `1280x800`: drawer aberto em `/home/instructor/`, bloco exibiu `Layon Quirino` e `Professor`, com `accountFitsDrawer=true`.

### Mobile
Playwright em `390x844`: drawer aberto em `/home/instructor/`, bloco exibiu `Layon Quirino` e `Professor`, com `accountFitsDrawer=true`.

### Console do navegador
Sem erros de console nas validações desktop e mobile.

### Terminal
Servidor local respondeu `200` em `http://127.0.0.1:8000/login/`.

## Validação ORM
### Banco
Não há mudança de schema.

### Shell checks
Validado via testes de renderização do Django.

### Integridade do fluxo
Renderização de home autenticada validada por Django test client e Playwright.

## Validação de qualidade
### Sem hardcode
Sem hardcode de pessoa específica no código. Os nomes usados aparecem apenas em teste/validação.

### Sem estruturas condicionais quebradiças
Condição limitada a `request.portal_person` e `request.portal_is_technical_admin`, contratos existentes do middleware.

### Sem `except: pass`
Não introduzido.

### Sem mascaramento de erro
Não introduzido.

### Sem comentários e docstrings desnecessários
Não introduzidos.

## Evidências
- Red: `manage.py test system.tests.test_views.PortalViewTestCase.test_drawer_shows_logged_portal_person_identity system.tests.test_views.PortalViewTestCase.test_drawer_shows_technical_admin_identity system.tests.test_views.PortalViewTestCase.test_public_route_does_not_render_logged_user_identity --verbosity 2` falhou antes da implementação por ausência de `aria-label="Usuário logado"`.
- Green: o mesmo comando passou com 3 testes OK.
- `manage.py check` passou: `System check identified no issues (0 silenced).`
- `manage.py collectstatic --noinput` passou: 1 arquivo estático copiado e 164 inalterados.
- `manage.py test --verbosity 2` executou 317 testes, mas não ficou verde por falhas já existentes fora desta mudança:
  - `system.tests.test_services` não importa `append_order_refund_record`;
  - `system.tests.test_asaas.AsaasWebhookTests.test_withdrawal_service_is_removed` ainda encontra `asaas_payroll.request_withdrawal`;
  - `system.tests.test_views.PortalViewTestCase.test_staff_financial_screen_rejects_withdrawal_post` recebe 200 em vez de 405.
- Browser in-app: drawer exibiu `LOGADO COMO / Layon Quirino / Professor` e não retornou erros de console.
- Playwright: desktop `1280x800` e mobile `390x844` passaram com `accountFitsDrawer=true`.

## Implementado
- Adicionado bloco `.drawer-account` no topo do menu lateral autenticado.
- Conta de portal exibe `request.portal_person.full_name` e `request.portal_person.person_type.display_name`.
- Acesso técnico exibe nome/username técnico e classificação `Administrador técnico`.
- CSS garante truncamento de nome longo e contenção do selo de classificação.
- Cache-buster do CSS atualizado para `20260507f`.

## Desvios do plano
- A suíte completa foi executada, mas falhou por problemas existentes em fluxo financeiro/Asaas fora do escopo deste PRD.

## Pendências
- Corrigir separadamente as falhas existentes da suíte completa relacionadas a Asaas/financeiro.
