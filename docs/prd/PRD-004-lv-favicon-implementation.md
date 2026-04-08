# PRD-004: Implementar favicon da marca LV
## Resumo
Adicionar um favicon próprio da LV JIU JITSU, derivado da identidade visual já usada no projeto, com integração correta no `base.html` e cobertura para a requisição padrão a `/favicon.ico`.

## Problema atual
- O navegador ainda registra `404` para `/favicon.ico`.
- O projeto não declara favicon no layout base.
- A aplicação usa a marca LV no cabeçalho, mas não a replica na identidade do navegador.

## Objetivo
- Criar um favicon limpo da marca LV.
- Declarar os links corretos no `<head>` do layout base.
- Responder à rota `/favicon.ico` sem erro.

## Contexto consultado
- Context7:
  - Django docs sobre `static` template tag: usar `{% load static %}` e `{% static 'path/to/file' %}` em templates.
- Web:
  - MDN, metadata e favicon: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Webpage_metadata

## Dependências adicionadas
- nenhuma

## Escopo / Fora do escopo
### Escopo
- Criar asset de favicon em `static/system/img/`.
- Integrar favicon e fallback no `templates/base.html`.
- Adicionar atendimento para `/favicon.ico`.
- Validar headless que o `404` do favicon foi removido.

### Fora do escopo
- Redesenho completo da logo institucional.
- Alterações de branding além do favicon.

## Arquivos impactados
- `docs/prd/PRD-004-lv-favicon-implementation.md`
- `templates/base.html`
- `lvjiujitsu/urls.py`
- `static/system/img/favicon-lv.svg`
- `system/tests/test_views.py`

## Riscos e edge cases
- Um favicon muito detalhado perde legibilidade em tamanhos pequenos.
- Apenas adicionar `rel="icon"` pode não eliminar a requisição automática a `/favicon.ico`.
- O asset precisa permanecer coerente com a marca já existente no cabeçalho.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD guiado por este PRD.
- TDD para metadata no layout e resposta de `/favicon.ico`.
- Django deve servir o asset via estáticos namespaced.
- Nada de hardcode de caminho fora de `static` e `staticfiles_storage`.

## Critérios de aceite (escritos como assertions testáveis)
- [x] A página raiz deve incluir metadata de favicon no `<head>`.
- [x] A rota `/favicon.ico` deve responder sem `404`.
- [x] O console do navegador não deve mais registrar erro para `/favicon.ico`.
- [x] O favicon deve usar a identidade LV, sem depender de texto longo ilegível.

## Plano (ordenado por dependência — fundações primeiro)
- [x] 1. Adicionar testes para metadata e rota de favicon.
- [x] 2. Criar o asset do favicon.
- [x] 3. Integrar o favicon no `base.html`.
- [x] 4. Atender `/favicon.ico` no projeto.
- [x] 5. Validar testes, estáticos e Playwright headless.

## Comandos de validação
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_views --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
- `.\.venv\Scripts\python.exe manage.py findstatic system/img/favicon-lv.svg`
- `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8013 --noreload`
- Playwright headless em `/` para checar ausência de `404` em `/favicon.ico`

## Implementado (preencher ao final)
- Asset novo em `static/system/img/favicon-lv.svg`, com monograma LV simplificado e legível para uso em tamanho pequeno.
- Include reutilizável `templates/includes/_favicon.html` criado para centralizar `theme-color`, `rel="icon"` em SVG, fallback PNG e `apple-touch-icon`.
- `templates/base.html` atualizado para carregar o include do favicon.
- Templates standalone de autenticação atualizados para carregar o mesmo include:
  - `templates/login/login.html`
  - `templates/login/login_form.html`
  - `templates/login/register.html`
  - `templates/login/password_reset_form.html`
  - `templates/login/password_reset_done.html`
  - `templates/login/password_reset_confirm.html`
  - `templates/login/password_reset_complete.html`
- `lvjiujitsu/urls.py` atualizado com redirect limpo de `/favicon.ico` para o asset estático da marca, eliminando o `404` do navegador.
- Testes adicionados em `system/tests/test_views.py` para metadata e para a rota `/favicon.ico`.
- Validação executada:
  - `.\.venv\Scripts\python.exe manage.py test system.tests.test_views.PortalViewTestCase.test_root_route_includes_lv_favicon_metadata system.tests.test_views.PortalViewTestCase.test_favicon_route_redirects_to_lv_asset --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py findstatic system/img/favicon-lv.svg`
  - `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8013 --noreload`
  - Validação headless com Playwright em `/`, com console sem erros e confirmação no DOM dos links:
    - `/static/system/img/favicon-lv.svg`
    - `/static/system/img/logo-lv-bjj.png`
- Evidência visual gerada em `test_artifacts/root-favicon-8013.png`

## Desvios do plano
- Nenhum.
