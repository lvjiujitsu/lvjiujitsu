# PRD-068: Login unico progressivo

## Summary
Estado inicial progressivo do LV JIU JITSU: manter somente a tela de login e os arquivos diretamente vinculados a ela pela referencia de contrato. Qualquer template, CSS, JS ou imagem nao mapeado aqui deve permanecer ausente ate uma PRD futura recriar o modulo correspondente.

## Demand type
Limpeza destrutiva local de UI e reimplementacao minima de login.

## Current problem
Ainda existiam templates e assets de home, pessoas, shell, modal e icones nao autorizados para a etapa inicial. Isso contradiz a estrategia progressiva solicitada.

## Goal
Deixar o projeto com apenas a superficie visual de login renderizavel e seus assets diretos.

## Scope
Arquivos permitidos nesta etapa:
- `templates/auth/base_auth.html`
- `templates/login/login_form.html`
- `static/system/css/auth/login.css`
- `static/system/js/auth/login.js`
- `static/system/js/lv/theme_boot.js`
- `static/system/img/favicon-lv.svg`
- `static/system/img/logo-lv-dark.png`
- `static/system/img/logo-lv-white.png`

## Out of scope
- Home.
- Pessoas.
- Shell autenticado.
- Modal CRUD.
- Cadastro completo.
- Financeiro, materiais, turmas, graduacao e calendario.
- Seeds, migrations, banco e testes automatizados.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Acceptance criteria
- Nenhum template fora de `templates/auth/base_auth.html` e `templates/login/login_form.html`.
- Nenhum CSS fora de `static/system/css/auth/login.css`.
- Nenhum JS fora de `static/system/js/auth/login.js` e `static/system/js/lv/theme_boot.js`.
- Nenhuma imagem fora de favicon e logos do login.
- `/login/` renderiza com os arquivos mapeados.

## Validation
- Inventario `templates`: somente `templates/auth/base_auth.html` e `templates/login/login_form.html`.
- Inventario `static/system`: somente `static/system/css/auth/login.css`, `static/system/js/auth/login.js`, `static/system/js/lv/theme_boot.js`, `favicon-lv.svg`, `logo-lv-dark.png`, `logo-lv-white.png`.
- Django Client em `/login/`: `status 200`.
- HTML contem `system/css/auth/login.css`, `system/js/auth/login.js`, `system/js/lv/theme_boot.js`, `logo-lv-dark.png` e `logo-lv-white.png`.
- `node --check static/system/js/auth/login.js`: sucesso.

## Final status
Concluida.
