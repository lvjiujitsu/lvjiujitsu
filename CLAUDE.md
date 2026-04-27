# CLAUDE.md

@AGENTS.md

> Contexto factual, específico e verificável do projeto `lvjiujitsu`.
> Este arquivo descreve o sistema real, sem repetir o protocolo universal do `AGENTS.md`.

---

## 1. Identidade do projeto

- **Nome:** LV JIU JITSU
- **Objetivo:** operar o portal público e as rotinas internas da academia, cobrindo cadastro, turmas, calendário, materiais e cobrança
- **Tipo de produto:** monólito web com área pública + áreas autenticadas operacionais
- **Stack:** Python + Django 4.1.13
- **Frontend:** templates Django server-rendered com CSS/JS por fluxo em `static/system/`
- **Banco local:** SQLite em `db.sqlite3`
- **Banco produção:** não documentado no repositório
- **Integrações externas reais no código:** Stripe, Asaas
- **Ambiente operacional padrão:** Windows + PowerShell com `.venv`
- **Idioma técnico:** inglês
- **Idioma da interface:** português pt-BR
- **Criticidade operacional:** média

---

## 2. Política local do projeto

Este repositório opera em modo **control-first com validação visual obrigatória para UI**.

### Isso implica
- mudanças com impacto relevante devem nascer de PRD em `docs/prd/`
- telas públicas e autenticadas devem ser validadas em navegador quando houver alteração visual ou de fluxo
- o projeto usa cache-busting manual em alguns assets de template; ao alterar JS/CSS referenciado com `?v=...`, atualizar a versão faz parte da entrega

### Regra local principal
- todo o domínio principal vive no app único `system/`, e o fluxo HTTP deve continuar fino, empurrando regra de negócio para `services/`

---

## 3. Estrutura real do repositório

```text
lvjiujitsu/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .env
├── manage.py
├── clear_migrations.py
├── db.sqlite3
├── docs/
│   └── prd/
├── lvjiujitsu/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── system/
│   ├── forms/
│   ├── management/commands/
│   ├── migrations/
│   ├── models/
│   ├── selectors/
│   ├── services/
│   ├── tests/
│   ├── utils/
│   └── views/
├── templates/
├── static/
└── staticfiles/
```

### Fatos estruturais importantes
- todo o domínio aplicacional está concentrado em `system/`
- `templates/login/` concentra home pública, login, cadastro e telas relacionadas ao portal
- `static/system/js/auth/registration-wizard-clean.js` é a implementação ativa do wizard de cadastro
- `staticfiles/` é saída gerada por `collectstatic`; fonte editável fica em `static/`

---

## 4. Arquitetura local

### Diretriz arquitetural central

Monólito Django com app única (`system`) seguindo MVT com camada explícita de `services/` para negócio e `selectors/` para leitura reutilizável.

### Ownership

| Responsabilidade | Onde fica |
|---|---|
| Persistência e invariantes | `system/models/` |
| Validação de entrada | `system/forms/` |
| Lógica de negócio | `system/services/` |
| Leituras e catálogos | `system/selectors/` e alguns serviços de overview |
| Orquestração HTTP | `system/views/` |
| Rotas | `system/urls.py`, `lvjiujitsu/urls.py` |
| Templates | `templates/` |
| Estilos e scripts | `static/system/css/`, `static/system/js/` |
| Testes | `system/tests/` |

### Proibições locais
- não colocar regra de negócio central em template ou JS de interface
- não editar arquivos-fonte em `staticfiles/`
- não introduzir migrações por padrão sem autorização explícita

---

## 5. Convenções locais de código

### Obrigatório
- identificadores técnicos em inglês
- UI em pt-BR
- configurações variáveis vindas de `.env` via `python-decouple`
- CSS/JS separados por fluxo em `static/system/`
- quando o template usa query string de versão em asset estático, atualizar o `?v=` ao alterar o arquivo correspondente

### Proibido
- hardcode de segredo ou chave externa
- `except: pass`
- colocar artefatos permanentes em `staticfiles/`
- tratar `README.md` como fonte de verdade do projeto; o código prevalece

---

## 6. Comandos reais do projeto

### Ambiente

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Testes e checks

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py shell -c "<CHECK>"
```

### Seeds e setup

```powershell
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py inicial_seed_test
.\.venv\Scripts\python.exe manage.py seed_person_type
.\.venv\Scripts\python.exe manage.py seed_class_catalog
.\.venv\Scripts\python.exe manage.py seed_plans
.\.venv\Scripts\python.exe manage.py seed_products
.\.venv\Scripts\python.exe manage.py seed_holidays --year <ANO>
```

### Comandos individuais de seed presentes no repositório

| Comando | Função |
|---|---|
| `seed_person_guardian` | cria responsável de teste |
| `seed_person_guardian_with_dependent` | cria responsável com dependente |
| `seed_person_student` | cria aluno individual |
| `seed_person_student_with_dependent` | cria titular com dependente |
| `seed_person_administrative` | cria perfil administrativo |
| `schedule_monthly_payouts` | agenda pagamentos mensais de professores |

### Comandos legados

- não há lista formal de comandos legados documentada no repositório

---

## 7. Ambiente local e ferramentas obrigatórias

### Shell padrão
- Windows + PowerShell

### Ferramentas obrigatórias quando aplicável

| Ferramenta | Obrigatória? | Uso principal |
|---|---|---|
| Playwright / browser MCP | sim, para UI | validação visual e console |
| Context7 / docs oficiais | sim, quando houver dúvida de biblioteca | referência atualizada |
| `.venv` local | sim | execução isolada do projeto |

### Configuração de estáticos

```python
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

## 8. Política local de banco, seeds e schema

### Banco local
- SQLite descartável em `db.sqlite3`

### Seeds
- o projeto possui seeds granulares e também agregadores (`inicial_seed`, `inicial_seed_test`)
- `seed_class_catalog`, `seed_plans` e `seed_products` são centrais para fluxos públicos e de checkout

### Schema
- existe apenas `system/migrations/0001_initial.py`
- migrações novas continuam proibidas por padrão
- reset destrutivo local é permitido **somente sob pedido explícito**

### Reset destrutivo local

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
```

---

## 9. Política local de validação

Uma entrega com impacto relevante deve, quando aplicável:

1. atualizar ou criar PRD
2. passar em `manage.py test --verbosity 2`
3. passar em `manage.py check`
4. executar `collectstatic --noinput` quando houver alteração de estático
5. manter `showmigrations` coerente com a política sem novas migrações
6. validar em navegador quando houver UI
7. inspecionar console do navegador
8. deixar o workspace sem artefatos temporários da validação

---

## 10. Critérios locais de falha

Marcar como não concluída quando houver:

- alteração visual sem validação em navegador
- mudança em asset versionado sem atualizar o `?v=` correspondente
- nova migração sem autorização
- artefato temporário deixado no repositório
- evidência insuficiente de teste/check

---

## 11. Regra final de manutenção

Atualizar este arquivo quando houver:

- novo comando real de setup/seed/check
- nova integração externa
- mudança na estrutura principal do app `system/`
- mudança no padrão de assets estáticos versionados manualmente

### Changelog da spec

```md
- **[2026-04-21]** CLAUDE.md reescrito com contexto factual do projeto LV JIU JITSU.
```
