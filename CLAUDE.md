# CLAUDE.md

> Contexto persistente, específico e deliberadamente reforçado do projeto **LV Jiu Jitsu**.
> Este arquivo define **o que o projeto é**, **como o agente deve se orientar dentro dele** e **quais controles locais são obrigatórios**.
> O protocolo universal está em `AGENTS.md`.
> As regras sempre ativas do Cursor ficam em `.cursor/rules/`.
>
> **Este projeto prefere controle, auditoria, previsibilidade e coerência a qualquer ganho de economia de tokens, custo ou velocidade.**

---

## 1. Política local do projeto

Este projeto adota um regime de operação **control-first**.

### Isso significa:
- o agente deve priorizar comportamento previsível;
- o agente deve operar sob auditoria explícita;
- o agente deve minimizar alucinação por validação e evidência;
- o agente deve ler arquivos completos do fluxo antes de decidir;
- o agente deve usar MCPs relevantes como parte do processo padrão;
- o agente não deve tentar "otimizar" removendo contexto importante;
- o agente não deve trocar especificidade por generalização elegante.

### Regra local principal
Se uma instrução torna o comportamento mais rígido, mais auditável e menos sujeito a inferência vaga, essa instrução deve prevalecer no desenho operacional do projeto.

---

## 2. Identidade do projeto

- **Nome:** LV Jiu Jitsu — sistema de gestão para academia de jiu-jitsu
- **Stack:** Python 3.12 + Django 4.1.13
- **Persistência / banco:** SQLite local (`db.sqlite3`) — banco local descartável em desenvolvimento
- **Política de schema/migração:** banco local descartável — reset destrutivo permitido sob demanda
- **Paradigmas:** SDD, TDD, MTV, Design Patterns
- **Padrão de interação web:** server-driven HTML com CSS/JS customizado (sem framework CSS externo)
- **Ambiente operacional:** Windows + PowerShell; `.venv` obrigatória — nada no global
- **Gateways de pagamento:** Stripe (cartão) + Asaas (PIX)
- **Prioridade organizacional:** controle e governança do agente sobre economia de contexto

---

## 3. Diretriz arquitetural central

Este projeto é um **monólito Django com app única (`system`)** que segue o padrão MTV com camada de services.

### Estrutura modular interna
A app `system` organiza-se internamente em pacotes:
- `models/` — persistência e invariantes
- `forms/` — validação de entrada server-side
- `services/` — lógica de negócio e orquestração transacional
- `views/` — camada fina de HTTP
- `tests/` — cobertura por camada

### Regra de ownership
- lógica de negócio fica em `services/`, **nunca** em views;
- views são finas e delegam para services;
- services recebem dados já validados pelo Form;
- `@transaction.atomic` em múltiplas escritas;
- exceção explícita em erro (nunca `None` silencioso).

---

## 4. Preparação do ambiente

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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Get-Command python   # deve apontar para .venv\Scripts\
```

### `.env`

Credenciais e config sensível ficam em `.env` (fora do versionamento). Usar `python-decouple`:

```python
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

---

## 5. Arquitetura Django MTV

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Domínio | `models/` | Persistência e regras de domínio simples |
| Negócio | `services/` | Lógica de negócio (**NUNCA** só na view) |
| HTTP | `views/` | Orquestração — views finas |
| Validação | `forms/` | Entrada server-side |
| Rotas | `urls.py` | Namespace por app |
| Apresentação | `templates/<app>/` | Herdam `base.html` |
| Estilos/Scripts | `static/<app>/css/`, `static/<app>/js/` | Namespaced por app |
| Testes | `tests/test_*.py` | Separados por camada (models, services, views, forms) |
| Automação | `management/commands/` | Comandos administrativos |

**Ordem de implementação:** Models → Forms → Services → Views → URLs → Templates → Static → Tests

**TDD (Red-Green-Refactor):** escrever teste que falha → código mínimo para passar → refatorar.

---

## 6. Configuração de estáticos e media

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']        # fontes ficam aqui
STATIC_ROOT = BASE_DIR / 'staticfiles'           # gerado pelo collectstatic (NÃO editar)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**Regras:**
- **Nunca** colocar arquivos fonte em `STATIC_ROOT` (`staticfiles/`).
- Arquivos fonte ficam em `static/` (raiz) ou `<app>/static/<app>/` (namespaced).
- Após alterar estáticos: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`.
- `media/` e `staticfiles/` ficam no `.gitignore`.

---

## 7. Estrutura de templates e estáticos

### Templates

```
templates/
├── base.html
├── includes/_navbar.html, _footer.html, _messages.html
├── home/student/dashboard.html, home/instructor/dashboard.html
├── billing/payment_method_choice.html, pix_checkout.html, plan_change_*.html
├── login/register.html, login/login.html
├── plans/, products/, people/
```

### Estáticos (com namespacing)

```
static/
├── css/base.css, js/base.js, images/
└── system/
    ├── css/auth/, css/billing/, css/portal/
    └── js/auth/, js/shared/
```

---

## 8. Política local de completude de contexto

Neste projeto, **o agente deve ler o arquivo completo sempre que ele estiver envolvido no fluxo**.

### Processo obrigatório
Antes de responder, diagnosticar, planejar ou editar:
1. identificar os arquivos do fluxo;
2. ler integralmente cada arquivo do fluxo;
3. ler contratos adjacentes;
4. só então decidir.

### Proibido localmente
- decidir por snippet quando existe arquivo envolvido;
- alterar código crítico com leitura parcial;
- alegar entendimento total sem registro explícito.

---

## 9. Política local de MCPs

### Princípio
Neste projeto, MCPs **não são acessórios**. Eles são parte central do processo de operação do agente.

### Inventário mínimo

| MCP / Ferramenta | Obrigatório? | Uso principal |
|---|---|---|
| Context7 ou MCP documental | sim, quando envolver libs/frameworks | documentação atualizada |
| Playwright / browser MCP | sim, quando houver UI, CSS, JS | validação visual |

---

## 10. PRD — estrutura obrigatória

Criar em `docs/prd/PRD-<NNN>-<slug>.md`:

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

## 11. Reset destrutivo local (somente sob pedido explícito)

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

## 12. Validação — checklist

1. **Ambiente**: `.venv`, ExecutionPolicy, UTF-8, dependências
2. **Visual**: Playwright/headless
3. **Estáticos**: `collectstatic --noinput` OK, sem 404
4. **Console browser**: sem erros JS
5. **Testes**: 0 falhas, 0 erros
6. **Terminal**: sem stack traces
7. **ORM/Banco**: `showmigrations`, shell check
8. **Segurança**: CSRF, server-side, sem hardcode, `.env`
9. **Verificação cruzada**: sem regressões

---

## 13. Estrutura esperada

```
lvjiujitsu/
├── .env                    # Credenciais (fora do git)
├── .gitignore
├── requirements.txt
├── manage.py
├── lvjiujitsu/             # settings.py, urls.py, wsgi.py
├── system/                 # App única de domínio
│   ├── models/             # person, plan, membership, registration_order, product, asaas, trial_access
│   ├── views/              # auth, home, payment, billing_admin, asaas, plan_change, product, person
│   ├── forms/              # registration, plan, product, auth, person, payroll
│   ├── services/           # membership, stripe_*, asaas_*, registration_*, plan_change, trial_access
│   ├── tests/
│   └── management/commands/
├── templates/
│   ├── base.html
│   ├── includes/
│   ├── home/, billing/, login/, plans/, products/, people/
├── static/
│   └── system/css/, system/js/
├── docs/prd/
├── CLAUDE.md
└── AGENTS.md
```

---

## 14. Critérios de falha

**NÃO CONCLUÍDA** quando: sem PRD, sem validação visual, sem console/logs, sem evidência, reset sem pedido, execução inventada, sem pesquisa de contexto, ferramentas não garantidas, lib sem requirements, pacote fora da `.venv`, credenciais hardcodadas, CSRF desabilitado, God Class, CSS/JS inline, `&&` usado no PowerShell, arquivos colocados em `STATIC_ROOT`.

---

### Changelog da spec

```md
- **[2026-04-18]** CLAUDE.md adaptado: filosofia control-first integrada com stack real do lvjiujitsu.
```
