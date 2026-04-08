# AGENTS.md

> Instruções universais e **obrigatórias** para agentes de desenvolvimento (Claude Code, Codex, Cursor, Jules, Copilot).
> Contexto específico do projeto fica em `CLAUDE.md`.
> **Nenhuma etapa é opcional.** Pular qualquer fase invalida a entrega.

---

## Princípios

- **SDD**: nenhuma implementação sem spec (PRD ou equivalente acordado). O código segue a especificação.
- **TDD (Red-Green-Refactor)**: ciclo obrigatório para fluxos centrais de domínio:
  1. **Red**: escrever teste que falha (o comportamento esperado ainda não existe).
  2. **Green**: escrever o código mínimo para o teste passar.
  3. **Refactor**: limpar o código mantendo todos os testes verdes.
  - Double-loop: testes funcionais (Playwright — comportamento do usuário) como loop externo; testes unitários (models, services, views) como loop interno.
- **MTV (Django)**: lógica de negócio em `services.py` / domínio, nunca só na view ou template.
- **Design Patterns Django**: Service Objects com `@transaction.atomic`, custom Manager/QuerySet, Form `clean_*` para validação, Mixins de view para reuso. KISS, DRY, YAGNI. Composição sobre herança.
- **Destruição > remendo**: em fase MVP, código ruim não é ajustado — é reescrito.

---

## Prioridade em caso de conflito

1. Solicitação atual do usuário
2. Regras de segurança e ambiente
3. Este `AGENTS.md`
4. `CLAUDE.md`
5. Convenções do repositório

---

## Preparação do ambiente (regra inviolável)

### PowerShell — configuração obrigatória (Windows)

```powershell
# 1. Liberar execução de scripts
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 2. Forçar encoding UTF-8 (evita corromper templates pt-BR com acentos)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

**Armadilhas do PowerShell que o agente DEVE evitar:**
- **`&&` não existe no PowerShell.** Usar `;` para encadear comandos, ou executar um por vez.
- **`source` não existe no PowerShell.** Ativar venv com `.\.venv\Scripts\Activate.ps1`.
- **Caminhos usam `\`**, não `/`. Usar `.\.venv\Scripts\python.exe`, não `./.venv/bin/python`.

### `.venv` — ambiente virtual (obrigatório)

**Se não existir:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Se existir:** `.\.venv\Scripts\Activate.ps1`

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Confirmar: `Get-Command python` (ou `which python`) deve apontar para a `.venv`.

---

## Gestão de dependências (regra inviolável)

- Instalar: `.\.venv\Scripts\pip.exe install <pacote>` → verificar com `pip show <pacote>` → **atualizar `requirements.txt` imediatamente**.
- `ModuleNotFoundError` em runtime: instalar → atualizar requirements → re-executar. **Não prosseguir até resolver.**
- Sincronizar ao iniciar: `pip install -r requirements.txt`.
- **Nunca** instalar no global, **nunca** `pip install --user`, **nunca** adicionar lib sem atualizar requirements.
- Se o projeto usar `pyproject.toml`, `Pipfile` ou outro gerenciador, seguir a convenção.

### Variáveis de ambiente e `.env`

- Credenciais e configurações sensíveis ficam em arquivo `.env` na raiz (fora do versionamento).
- Usar `python-decouple` ou `django-environ` para ler. Exemplo em `settings.py`:
  ```python
  from decouple import config
  SECRET_KEY = config('SECRET_KEY')
  DEBUG = config('DEBUG', default=False, cast=bool)
  ```
- Se o projeto não tiver `.env` e precisar de um, criar com valores de exemplo e informar o usuário.

---

## Execução real no terminal (regra inviolável)

- Shell padrão: **PowerShell** (Windows) com encoding UTF-8 configurado.
- **Executar comandos diretamente** — proibido criar `.ps1`, `.bat`, `.cmd`, `.sh` ou scripts auxiliares.
- Cada etapa reporta: comando exato, diretório, código de saída, trecho de stdout/stderr.
- Comandos sempre com caminho da `.venv`: `.\.venv\Scripts\python.exe manage.py <comando>`

---

## Política de idioma (regra inviolável)

- **Código e nomes técnicos**: inglês (models, fields, variáveis, funções, classes, rotas, arquivos).
- **Texto visível ao usuário final**: pt-BR (labels, mensagens, títulos, botões).
- **Respostas ao desenvolvedor**: pt-BR.
- **Código limpo**: evitar comentários; usar apenas quando decisão não é inferível pela estrutura.

---

## Segurança (regra inviolável)

- **Nunca** hardcodar `SECRET_KEY`, senhas, tokens, chaves de API. Usar `.env` + `python-decouple`/`django-environ`.
- **CSRF**: `{% csrf_token %}` em todo formulário POST. Nunca desabilitar sem justificativa.
- **Validação server-side obrigatória**: frontend bloqueia para UX, backend bloqueia por segurança.
- **SQL injection**: nunca concatenar strings em queries. Usar ORM ou queries parametrizadas.
- **XSS**: nunca `|safe` ou `mark_safe()` em dados do usuário sem sanitização.
- **Auth**: views protegidas com `@login_required`/`@permission_required`. Nunca confiar em esconder botões.
- **Upload**: validar MIME, extensão e tamanho no backend.
- **DEBUG**: nunca `True` em produção. Ler de `.env`.
- **Frontend**: nunca credenciais em JS/HTML. Nunca `innerHTML` com dados do usuário.

---

## Estrutura de arquivos frontend (obrigatória)

### Templates (`templates/`)

```
templates/
├── base.html                          # Layout raiz com blocos: content, extra_css, extra_js
├── includes/                          # Fragmentos reutilizáveis (prefixo _)
│   ├── _navbar.html
│   ├── _footer.html
│   └── _messages.html
├── <app_name>/
│   ├── <entity>_list.html
│   ├── <entity>_detail.html
│   ├── <entity>_form.html
│   └── <entity>_confirm_delete.html
└── registration/
    └── login.html
```

Herança obrigatória de `base.html`. Nomes em inglês, snake_case.

### Arquivos estáticos (`static/`) — com namespacing por app

**Django exige namespacing** para evitar colisão entre apps com arquivos de mesmo nome.

```
static/
├── css/
│   └── base.css                       # Estilos globais
├── js/
│   └── base.js                        # Scripts globais
├── images/
│   └── logo.svg
└── <app_name>/                        # Namespace por app (OBRIGATÓRIO)
    ├── css/
    │   └── <entity>_list.css
    ├── js/
    │   └── <entity>_form.js
    └── images/
```

**Regras críticas:**
- Carregar via `{% load static %}` e `{% static '<app_name>/css/file.css' %}`.
- `base.html` carrega `css/base.css` e `js/base.js`. Filhos usam `{% block extra_css %}` / `{% block extra_js %}`.
- **Nunca** colocar arquivos diretamente em `STATIC_ROOT` — esse diretório é gerado pelo `collectstatic`.
- **Nunca** CSS/JS inline no template. **Nunca** arquivo monolítico com tudo junto.
- Cada tela com comportamento específico tem seu próprio arquivo CSS/JS.

### `collectstatic` — comando obrigatório

Após criar ou alterar arquivos estáticos, executar:

```powershell
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

Na validação (Fase 6), verificar que `collectstatic` roda sem erros e que `STATIC_ROOT` não é o mesmo diretório onde os arquivos fonte estão.

### Media files (uploads de usuário)

Se o projeto tiver upload de arquivos, garantir no `settings.py`:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

E no `urls.py` (desenvolvimento):

```python
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

`media/` fica fora do versionamento (adicionar ao `.gitignore`).

---

## Anti-code-smell (regras concretas)

- **Máx. 25 linhas/método, 4 argumentos/função, 300 linhas/arquivo.**
- **Proibido God Class.** Uma classe faz uma coisa. View orquestra, serviço processa, model persiste.
- **Proibido condicionais aninhadas (máx. 2 níveis).** Usar early return, guard clauses, dicionários de dispatch.
- **Proibido `except: pass`** ou `except Exception` genérico sem justificativa. Capturar exceções específicas.
- **Proibido hardcode de valores configuráveis.** Extrair para `settings.py`, `.env`, constante ou enum.
- **Proibido N+1**: `select_related`/`prefetch_related`. Proibido queries em loop. Proibido `.all()` sem paginação.
- **Signals**: só quando acoplamento implícito for aceitável. Regra central explícita no serviço.
- **Frontend**: proibido CSS/JS inline, arquivo monolítico, seletor CSS por ID para estilo, `innerHTML` com dados do usuário.

---

## Protocolo obrigatório — TODAS as fases

### FASE 0 — Ambiente (uma vez por sessão)

1. PowerShell: `Set-ExecutionPolicy` + encoding UTF-8 + `chcp 65001`.
2. `.venv` ativa + `pip install -r requirements.txt`.
3. Confirmar `python`/`pip` apontam para `.venv`.

### FASE 1 — Contexto

Ler `CLAUDE.md`, PRDs, arquivos impactados. Classificar a mudança. Não executar `git` sem pedido.

### FASE 2 — Pesquisa e contexto externo

1. **MCP Context7**: documentação das libs envolvidas (instalar se ausente).
2. **Busca na internet**: soluções, padrões, issues conhecidas.
3. Novas libs necessárias: instalar na `.venv`, atualizar `requirements.txt`, registrar no PRD.

### FASE 3 — PRD

Criar `docs/prd/PRD-<NNN>-<slug>.md`:

```md
# PRD-<NNN>: <Título>
## Resumo
## Problema atual
## Objetivo
## Contexto consultado
  - Context7: (o que foi encontrado)
  - Web: (links e resumos relevantes)
## Dependências adicionadas
  - (pacote==versão — motivo) ou "nenhuma"
## Escopo / Fora do escopo
## Arquivos impactados
  - (lista de arquivos que serão criados, alterados ou removidos)
## Riscos e edge cases
  - (o que pode dar errado, casos limite, dependências externas frágeis)
## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
## Critérios de aceite (escritos como assertions testáveis)
  - [ ] Ao fazer X, o sistema deve Y (verificável por: comando/teste/visual)
  - [ ] Se Z inválido, o sistema deve retornar erro W
## Plano (ordenado por dependência — fundações primeiro)
  - [ ] 1. Models e migrações
  - [ ] 2. Forms e validação
  - [ ] 3. Services (lógica de negócio)
  - [ ] 4. Views e URLs
  - [ ] 5. Templates e estáticos
  - [ ] 6. Testes (Red-Green-Refactor)
  - [ ] 7. Validação completa (Fase 6)
## Comandos de validação
  - (quais comandos rodar para verificar os critérios — ex.: test, shell, collectstatic, playwright)
## Implementado (preencher ao final)
## Desvios do plano
```

### FASE 4 — Estratégia

Abordagem, arquivos impactados, testes planejados, riscos. Menor mudança correta.

### FASE 5 — Implementação

Ordem: **Models → Forms → Services → Views → URLs → Templates → Static (CSS/JS) → Tests**.

**Ciclo TDD para fluxos centrais (obrigatório):**
1. Escrever teste que falha (Red) para o comportamento esperado.
2. Implementar código mínimo para passar (Green).
3. Refatorar mantendo testes verdes (Refactor).
4. Para features com interface: teste funcional (Playwright) como loop externo primeiro.

**Estrutura de testes por camada:**

```
<app_name>/
├── tests/
│   ├── __init__.py
│   ├── test_models.py       # Validações, propriedades, constraints
│   ├── test_services.py     # Regras de negócio, fluxos felizes e de erro
│   ├── test_selectors.py    # Queries, filtros, paginação
│   ├── test_views.py        # Status codes, redirects, contexto, permissões
│   ├── test_forms.py        # Validação de entrada, clean_*
│   └── test_commands.py     # Management commands (se existirem)
```

Usar `setUp` / `setUpTestData` para dados de teste — nunca hardcodar dados repetidos em cada teste. Se o projeto tiver `factory_boy`, usar factories.

**Patterns obrigatórios nos serviços:**
- `@transaction.atomic` em fluxos que envolvem múltiplas escritas.
- Levantar exceção explícita (nunca retornar `None` silencioso) em caso de erro.
- Serviço recebe dados já validados (pelo Form) — não revalidar o que o Form já fez.

**Regras de implementação:**
- Views finas; regras de negócio em `services.py` ou domínio.
- Templates herdam de `base.html`, organizados por app.
- CSS e JS separados por app/tela em `static/<app_name>/`.
- Respeitar regras de segurança e anti-code-smell.
- Biblioteca nova: instalar na `.venv`, atualizar `requirements.txt`, registrar no PRD.

### FASE 6 — Validação completa (a mais importante)

#### 6.1 — Ferramentas

Garantir: ExecutionPolicy, `.venv`, dependências, Playwright + Chromium instalados (na `.venv`, atualizar requirements).

```powershell
.\.venv\Scripts\pip.exe install playwright
.\.venv\Scripts\playwright.exe install chromium
.\.venv\Scripts\python.exe -c "from playwright.sync_api import sync_playwright; print('OK')"
```

#### 6.2 — Visual (HTML + CSS + JS)

Playwright MCP ou headless. Screenshot. Renderização, responsividade, estados. Se impossível: declarar.

#### 6.3 — Arquivos estáticos

```powershell
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py findstatic css/base.css
```

Sem 404 para CSS/JS/imagens no browser.

#### 6.4 — Console browser

Sem erros JS críticos. Reportar warnings.

#### 6.5 — Testes

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

0 falhas, 0 erros. `ModuleNotFoundError` → instalar + requirements + re-executar.

#### 6.6 — Terminal

Sem stack traces. Servidor sobe sem erros (verificar porta livre).

#### 6.7 — ORM / Banco

```powershell
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py shell -c "<verificação>"
```

#### 6.8 — Verificação cruzada

Re-executar testes. Checar outros endpoints. Corrigir antes de seguir.

### FASE 7 — Atualização do PRD

Marcar `[x]`, preencher Implementado, Dependências, Desvios, evidências.

### FASE 8 — Fechamento

```md
## Resumo da demanda
## O que foi implementado
## Dependências adicionadas ao requirements.txt
## Validação
- [ ] Ambiente (.venv, ExecutionPolicy, UTF-8, dependências)
- [ ] Visual (Playwright/headless)
- [ ] Estáticos (collectstatic OK, sem 404)
- [ ] Console browser (sem erros JS)
- [ ] Testes (0 falhas, 0 erros)
- [ ] Terminal (sem stack traces)
- [ ] ORM/Banco (integridade)
- [ ] Segurança (CSRF, server-side, sem hardcode)
- [ ] Verificação cruzada (sem regressões)
## O que NÃO foi validado (e por quê)
## Pendências
## Próximo passo sugerido
```

---

## Debate multiagente interno

| Papel | Pergunta-chave |
|---|---|
| **Arquiteto** | Estrutura adequada? Impacto controlado? |
| **Testador** | Fluxos felizes e de erro cobertos? |
| **Revisor UI** | Responsivo? CSS/JS separados por tela? |
| **Revisor Dados** | Migrações coerentes? |
| **Revisor Segurança** | CSRF? Validação server-side? Sem credenciais expostas? |

---

## Reset destrutivo local (somente sob pedido explícito)

**Não é o fluxo padrão.** Somente quando o usuário pedir e `CLAUDE.md` declarar banco descartável. Executar na ordem (somente comandos existentes):

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Não editar migrations manualmente. Se comando não existir, reportar.

---

## Proibições

- Pular qualquer fase. Implementar sem PRD. Pular pesquisa de contexto.
- Fingir execução. Declarar sucesso sem evidência.
- Criar scripts wrapper. Substituir execução por documentação.
- Expandir escopo sem registrar. Inventar comandos.
- `git` sem pedido. Reset destrutivo sem pedido.
- Instalar no global. `pip install --user`. Lib sem atualizar requirements.
- Hardcodar credenciais. Desabilitar CSRF. `except: pass`. God Class.
- CSS/JS inline. Usar `&&` no PowerShell. Colocar arquivos em `STATIC_ROOT`.

---

## Sinais de bloqueio

Reportar **não concluído** quando: servidor não sobe, UI não validável, testes quebram, comandos não existem, ferramentas não instaláveis, PowerShell não permite execução, encoding corrompendo saída, `.venv` não criável, dependência não resolve.

---

## Fonte de verdade

| O quê | Onde |
|---|---|
| Como o agente trabalha | Este `AGENTS.md` |
| O que o projeto é | `CLAUDE.md` |
| Requisitos | PRDs em `docs/prd/` |
| Fluxos reais | Código e testes |
