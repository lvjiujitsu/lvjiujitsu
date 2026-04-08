# CLAUDE.md

> Contexto persistente **do repositório atual**. Leia `AGENTS.md` para o protocolo de execução.

---

## Perfil do projeto

- **Stack:** Python 3.12 + Django 4.1.13
- **Persistência / banco:** SQLite local (`db.sqlite3`) - banco local descartável em desenvolvimento
- **Política de schema/migração:** banco local descartável - reset destrutivo permitido sob demanda
- **Paradigmas:** SDD, TDD, MTV, Design Patterns
- **Ambiente de execução:** `.venv` obrigatória — nada no global

---

## Preparação do ambiente

### PowerShell (Windows)

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

**Atenção:** `&&` não funciona no PowerShell (usar `;`). `source` não existe (usar `.\.venv\Scripts\Activate.ps1`). Caminhos com `\`.

### `.venv`

```powershell
# Criar (se não existir):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Verificar:
Get-Command python   # deve apontar para .venv\Scripts\
```

### `.env`

Credenciais e config sensível ficam em `.env` (fora do versionamento). Usar `python-decouple` ou `django-environ`:

```python
# settings.py
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

---

## Arquitetura Django MTV

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Domínio | `models.py` | Persistência e regras de domínio simples |
| Negócio | `services.py` | Lógica de negócio (**NUNCA** só na view) |
| Leitura | `selectors.py` | Consultas (`select_related`/`prefetch_related`) |
| HTTP | `views.py` | Orquestração — views finas |
| Validação | `forms.py` | Entrada server-side |
| Rotas | `urls.py` | Namespace por app |
| Apresentação | `templates/<app>/` | Herdam `base.html` |
| Estilos/Scripts | `static/<app>/css/`, `static/<app>/js/` | Namespaced por app |
| Testes | `tests/test_*.py` | Separados por camada (models, services, views, forms) |
| Automação | `management/commands/` | Comandos administrativos |

**Ordem de implementação:** Models → Forms → Services → Views → URLs → Templates → Static → Tests

**TDD (Red-Green-Refactor):** escrever teste que falha → código mínimo para passar → refatorar. Double-loop: Playwright (comportamento do usuário) como externo, unitários por camada como interno.

**Estrutura de testes:**

```
<app_name>/tests/
├── test_models.py
├── test_services.py
├── test_selectors.py
├── test_views.py
├── test_forms.py
└── test_commands.py
```

**Patterns nos serviços:** `@transaction.atomic` em múltiplas escritas, exceção explícita em erro (nunca `None` silencioso), serviço recebe dados já validados pelo Form.

---

## Configuração de estáticos e media no `settings.py`

```python
# Estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']        # onde os fontes ficam
STATIC_ROOT = BASE_DIR / 'staticfiles'           # gerado pelo collectstatic (NÃO editar)

# Media (uploads de usuário)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

```python
# urls.py (desenvolvimento)
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Regras:**
- **Nunca** colocar arquivos fonte em `STATIC_ROOT` (`staticfiles/`) — é gerado automaticamente.
- Arquivos fonte ficam em `static/` (raiz) ou `<app>/static/<app>/` (namespaced).
- Após alterar estáticos: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`.
- `media/` e `staticfiles/` ficam no `.gitignore`.

---

## Estrutura de templates e estáticos

### Templates

```
templates/
├── base.html                         # {% block content %}, {% block extra_css %}, {% block extra_js %}
├── includes/_navbar.html, _footer.html, _messages.html
├── <app_name>/<entity>_list.html, _detail.html, _form.html, _confirm_delete.html
└── registration/login.html
```

### Estáticos (com namespacing)

```
static/
├── css/base.css                      # Globais
├── js/base.js
├── images/logo.svg
└── <app_name>/                       # Namespace (evita colisão entre apps)
    ├── css/<entity>_list.css
    ├── js/<entity>_form.js
    └── images/
```

Template usa: `{% load static %}` → `{% static '<app_name>/css/file.css' %}`

---

## Ferramentas de validação

| Ferramenta | Instalação (dentro da `.venv`) |
|---|---|
| Playwright | `pip install playwright` → `playwright install chromium` → atualizar `requirements.txt` |
| Context7 (MCP) | Verificar disponibilidade; se indisponível, buscar via web |

---

## PRD — estrutura obrigatória

Criar em `docs/prd/PRD-<NNN>-<slug>.md` (ver detalhes completos em `AGENTS.md` Fase 3):

```md
# PRD-<NNN>: <Título>
## Resumo
## Problema atual
## Objetivo
## Contexto consultado (Context7 + Web)
## Dependências adicionadas
## Escopo / Fora do escopo
## Arquivos impactados
## Riscos e edge cases
## Regras e restrições (SDD, TDD, MTV, Design Patterns)
## Critérios de aceite (assertions testáveis)
## Plano (ordenado por dependência)
## Comandos de validação
## Implementado (ao final)
## Desvios do plano
```

---

## Reset destrutivo local (somente sob pedido explícito)

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

---

## Validação — checklist (Fase 6 do AGENTS.md)

1. **Ambiente**: `.venv`, ExecutionPolicy, UTF-8, dependências
2. **Visual**: Playwright/headless
3. **Estáticos**: `collectstatic --noinput` OK, sem 404, `findstatic` confirma
4. **Console browser**: sem erros JS
5. **Testes**: 0 falhas, 0 erros
6. **Terminal**: sem stack traces
7. **ORM/Banco**: `showmigrations`, shell check
8. **Segurança**: CSRF, server-side, sem hardcode, `.env`
9. **Verificação cruzada**: sem regressões

---

## Estrutura esperada

```
projeto/
├── .env                    # Credenciais (fora do git)
├── .gitignore              # inclui: .env, media/, staticfiles/, db.sqlite3, __pycache__/
├── requirements.txt
├── manage.py
├── <project_config>/       # settings.py, urls.py, wsgi.py
├── <apps>/
│   ├── models.py, views.py, forms.py, services.py, selectors.py
│   ├── urls.py, tests.py
│   └── management/commands/
├── templates/
│   ├── base.html
│   ├── includes/
│   └── <app_name>/
├── static/
│   ├── css/base.css, js/base.js, images/
│   └── <app_name>/css/, js/, images/
├── media/                  # Uploads (fora do git)
├── staticfiles/            # Gerado por collectstatic (fora do git)
├── docs/prd/
├── CLAUDE.md
└── AGENTS.md
```

---

## Critérios de falha

**NÃO CONCLUÍDA** quando: sem PRD, sem validação visual, sem console/logs, sem evidência, reset sem pedido, execução inventada, sem pesquisa de contexto, ferramentas não garantidas, lib sem requirements, pacote fora da `.venv`, credenciais hardcodadas, CSRF desabilitado, God Class, CSS/JS inline, `&&` usado no PowerShell, arquivos colocados em `STATIC_ROOT`.

---

### Changelog da spec

```md
- **[YYYY-MM-DD]** Descrição da decisão ou mudança.
```
