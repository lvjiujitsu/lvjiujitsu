# CLAUDE.md

@AGENTS.md

> Contexto persistente, específico e reutilizável do projeto atual.
> Este arquivo define **o que o projeto é**, **como ele deve ser tratado** e **quais restrições locais prevalecem**.
> O protocolo universal está em `AGENTS.md`.
> Este arquivo deve conter apenas contexto **real** do projeto — nunca regras genéricas duplicadas do `AGENTS.md`.

---

## 1. Identidade do projeto

- **Nome:** `<PROJECT_NAME>`
- **Objetivo:** `<SYSTEM_GOAL>`
- **Tipo de produto:** `<PRODUCT_TYPE>`
- **Stack:** Python + Django `<VERSION>`
- **Frontend:** server-rendered com templates Django + CSS/JS por tela
- **Banco local:** SQLite (descartável em dev)
- **Banco produção:** `<DB_PROD>`
- **Integrações externas:** `<INTEGRATIONS>`
- **Ambiente operacional:** Windows + PowerShell (`.venv` obrigatória)
- **Idioma técnico:** inglês
- **Idioma da interface:** português pt-BR
- **Criticidade:** `<LOW | MEDIUM | HIGH>`

---

## 2. Política local do projeto

Este projeto adota um regime de operação **`<MODE>`**.

> Exemplos de modo: `control-first`, `MVP destrutivo local`, `alta rastreabilidade`, `validação visual obrigatória`

### Isso significa:
- `<DESCREVER O QUE O MODO IMPLICA>`
- `<DESCREVER RESTRIÇÕES ESPECÍFICAS>`

### Regra local principal:
- `<REGRA MAIS IMPORTANTE DO PROJETO>`

---

## 3. Estrutura real do repositório

> Descrever a estrutura **real**, não a idealizada.

```
<project_root>/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .env                    # credenciais (fora do git)
├── manage.py
├── clear_migrations.py     # reset destrutivo local
├── db.sqlite3              # dev (fora do git)
├── <config_package>/       # settings.py, urls.py, wsgi.py
├── <app>/                  # app principal de domínio
│   ├── models/
│   ├── views/
│   ├── forms/
│   ├── services/
│   ├── selectors/
│   ├── tests/
│   ├── management/commands/
│   ├── migrations/
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── includes/
│   └── <fluxos>/
├── static/
│   ├── css/base.css
│   ├── js/base.js
│   └── <app>/css/, <app>/js/
├── staticfiles/            # collectstatic (fora do git)
├── media/                  # uploads (fora do git)
└── docs/prd/
```

### Fatos estruturais importantes
- `<FATO_1>` (ex: "todo o domínio vive em `system/`")
- `<FATO_2>` (ex: "seeds JSON ficam em `static/<namespace>_ini/`")

---

## 4. Arquitetura local

### Diretriz arquitetural central

`<DESCREVER>` (ex: "Monólito Django com app única seguindo padrão MVT com camada de services")

### Ownership

| Responsabilidade | Onde fica |
|---|---|
| Persistência e invariantes | `models/` |
| Validação de entrada | `forms/` |
| Lógica de negócio | `services/` (**nunca** só na view) |
| Leitura complexa | `selectors/` |
| Orquestração HTTP | `views/` (finas) |
| Apresentação | `templates/` |
| Estilos e scripts | `static/<app>/css/`, `static/<app>/js/` |
| Testes | `tests/` por camada |

### Proibições locais
- lógica de negócio em template ou JavaScript de interface
- lógica de negócio concentrada só na view
- `<PROIBIÇÃO_ESPECÍFICA_DO_PROJETO>`

---

## 5. Convenções locais de código

### Obrigatório
- identificadores técnicos em inglês
- interface em pt-BR
- configurações variáveis vindas de `.env`, `settings` ou banco
- tratamento de erro específico
- CSS e JS separados por tela e namespace

### Proibido
- hardcode de segredo, token, credencial ou valor configurável
- `except: pass` ou `except Exception` genérico
- condicionais longas e quebradiças
- comentários redundantes explicando o óbvio
- docstrings desnecessárias
- CSS/JS inline sem justificativa
- `<PROIBIÇÃO_ESPECÍFICA>`

---

## 6. Comandos reais do projeto

> Listar **apenas** comandos que existem de fato no projeto.
> Nunca confiar só no README se o código divergir.

### Ambiente

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe manage.py runserver <HOST:PORT>
```

### Testes e checks

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py shell -c "<CHECK>"
```

### Seeds e setup

```powershell
.\.venv\Scripts\python.exe manage.py <comando_superuser>
.\.venv\Scripts\python.exe manage.py <comando_seed_agregador>
```

### Comandos individuais de seed

| Comando | Função |
|---|---|
| `<COMANDO_1>` | `<FUNÇÃO_1>` |
| `<COMANDO_2>` | `<FUNÇÃO_2>` |

### Comandos legados (NÃO usar)

| Comando legado | Substituído por |
|---|---|
| `<LEGADO_1>` | `<NOVO_1>` |

---

## 7. Ambiente local e ferramentas obrigatórias

### Shell padrão
- Windows + PowerShell

### Baseline

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Ferramentas obrigatórias quando aplicável

| Ferramenta | Obrigatória? | Uso principal |
|---|---|---|
| Playwright / browser MCP | sim, quando houver UI | validação visual e E2E |
| Context7 ou MCP documental | sim, quando envolver libs | documentação atualizada |
| `<FERRAMENTA>` | `<SIM/NÃO>` | `<USO>` |

### Configuração de estáticos

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']        # fontes ficam aqui
STATIC_ROOT = BASE_DIR / 'staticfiles'           # gerado pelo collectstatic (NÃO editar)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**Regras:**
- **nunca** colocar arquivos fonte em `STATIC_ROOT` (`staticfiles/`)
- arquivos fonte ficam em `static/` (raiz) ou `<app>/static/<app>/` (namespaced)
- após alterar estáticos: `collectstatic --noinput`
- `media/` e `staticfiles/` ficam no `.gitignore`

---

## 8. Política local de banco, seeds e schema

### Banco local
- `<DESCREVER>` (ex: "SQLite descartável — reset destrutivo permitido sob demanda")

### Seeds
- comando agregador: `manage.py <SEED_COMMAND>`
- comandos individuais: `<LISTA>`
- ordem de execução respeita dependências entre apps
- cada seed registra claramente o que fez

### Schema
- migrações: **proibidas por padrão**
- reset destrutivo: `<PERMITIDO_SOB_PEDIDO | PROIBIDO>`
- condições para exceção: `<DESCREVER>`

### Reset destrutivo local (somente sob pedido explícito)

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py <comando_superuser>
.\.venv\Scripts\python.exe manage.py <comando_seed>
.\.venv\Scripts\python.exe manage.py runserver <HOST:PORT>
```

---

## 9. Política local de validação

Uma tarefa só está pronta quando:

1. PRD foi criado ou atualizado (quando aplicável)
2. fluxo impactado foi lido integralmente
3. testes passaram (`manage.py test --verbosity 2` — 0 falhas, 0 erros)
4. `manage.py check` sem erros
5. `collectstatic --noinput` sem erros (quando houver estáticos)
6. `showmigrations` coerente com a política do projeto
7. shell checks do ORM validando persistência
8. validação visual executada (quando houver impacto em UI)
9. console do navegador sem erros JS críticos
10. terminal sem stack traces
11. sem hardcode, sem mascaramento de erro
12. limpeza final realizada
13. documentação alinhada ao novo estado

---

## 10. Critérios locais de falha

Marcar como **NÃO CONCLUÍDA** quando:

- sem PRD (quando necessário)
- sem validação visual (quando houver UI)
- sem console/logs inspecionados
- sem evidência de validação
- reset destrutivo sem pedido explícito
- execução inventada
- sem pesquisa de contexto quando necessária
- ferramentas obrigatórias não garantidas
- lib adicionada sem atualizar requirements
- pacote instalado fora da `.venv`
- credenciais hardcodadas
- CSRF desabilitado
- God Class introduzida
- CSS/JS inline sem justificativa
- `&&` usado no PowerShell
- arquivos colocados em `STATIC_ROOT`
- comando legado usado em vez do atual
- `<CRITÉRIO_ESPECÍFICO_DO_PROJETO>`

---

## 11. Regra final de manutenção

Sempre atualizar `CLAUDE.md` quando houver:

- mudança de stack
- mudança de arquitetura
- novo comando real
- nova integração
- nova ferramenta obrigatória
- novo risco recorrente
- divergência entre README e código
- mudança relevante no workflow operacional

Este arquivo deve ser: **factual, enxuto, específico, verificável** e livre de duplicação desnecessária do `AGENTS.md`.

---

### Changelog da spec

```md
- **[<DATA>]** CLAUDE.md criado: <DESCRIÇÃO>.
```
