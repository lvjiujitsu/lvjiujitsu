# Guia rápido: como preencher o CLAUDE.md para um novo projeto

> Este guia mostra como adaptar o template `CLAUDE.md` para qualquer projeto Django em menos de 15 minutos.

---

## Passo 1 — Identidade (2 min)

Preencha os dados básicos. Exemplo real:

```md
- **Nome:** Visary
- **Objetivo:** Sistema web de gestão de consultoria de vistos
- **Stack:** Python + Django 4.1.13
- **Frontend:** server-rendered com templates Django + CSS/JS por tela
- **Banco local:** SQLite (descartável em dev)
- **Banco produção:** PostgreSQL
- **Integrações:** PaddleOCR (passaporte), ViaCEP (endereço)
- **Ambiente operacional:** Windows + PowerShell
- **Idioma técnico:** inglês
- **Idioma da interface:** português pt-BR
- **Criticidade:** média
```

---

## Passo 2 — Política local (1 min)

Escolha o modo e descreva o que ele implica:

- **control-first**: prioriza previsibilidade e auditoria
- **MVP destrutivo**: banco descartável, rebuild limpo a cada ciclo
- **alta rastreabilidade**: toda decisão documentada em PRD

Exemplo:

```md
Este projeto adota um regime de operação **MVP destrutivo local**.

Isso significa:
- a base local pode ser destruída e recriada integralmente
- validação ocorre sobre ambiente limpo
- toda implementação deve provar que não quebrou o restante
```

---

## Passo 3 — Estrutura real (3 min)

Abra o terminal, rode `tree -L 2` (ou `Get-ChildItem -Recurse -Depth 2`) e documente o que existe **de verdade**:

```md
visary/
├── manage.py
├── visary/             # settings.py, urls.py
├── system/             # app única de domínio
│   ├── models/
│   ├── views/
│   ├── forms/
│   ├── services/
│   └── tests/
├── templates/
├── static/
└── docs/prd/
```

Registre fatos importantes: "todo o domínio vive em `system/`", "seeds JSON ficam em `static/*_ini/`".

---

## Passo 4 — Comandos reais (3 min)

**Nunca confie no README.** Abra o código e liste apenas comandos que existem de fato:

```md
### Comandos reais
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py initial_seeds
```

Se houver comandos legados que o README ainda cita mas que foram renomeados, registre:

```md
### Comandos legados (NÃO usar)
| Legado | Atual |
|---|---|
| `criar_superuser_admin` | `create_admin_superuser` |
| `seed_modulos` | `seed_modules` |
```

---

## Passo 5 — Banco e seeds (2 min)

```md
### Banco local
- SQLite descartável — reset destrutivo permitido sob demanda

### Seeds
- comando agregador: `manage.py initial_seeds`
- executa na ordem: superuser → módulos → perfis → países → tipos de visto → ...

### Schema
- migrações: proibidas por padrão
- reset destrutivo: permitido sob pedido explícito
```

---

## Passo 6 — Critérios de falha (2 min)

Liste o que faz uma tarefa ser marcada como **NÃO CONCLUÍDA** neste projeto específico:

```md
- usar comando legado em vez do atual
- rodar clear_migrations.py sem pedido explícito
- editar requirements.txt sem preservar encoding UTF-16 (quando aplicável)
- criar código de domínio fora de `system/`
- assumir que README é fonte de verdade sobre comandos
```

---

## Passo 7 — Changelog (30 seg)

```md
### Changelog da spec
- **[2026-04-21]** CLAUDE.md criado: setup inicial do projeto Visary.
```

---

## Checklist final

- [ ] Identidade preenchida com dados reais
- [ ] Política local definida
- [ ] Estrutura do repositório é a real (não idealizada)
- [ ] Comandos são os que existem de fato (não os do README)
- [ ] Banco e seeds documentados
- [ ] Critérios de falha específicos do projeto registrados
- [ ] Nenhuma regra genérica duplicada do `AGENTS.md`

---

## Dica importante

O `CLAUDE.md` não é um segundo `AGENTS.md`. Ele deve conter **apenas o que é específico deste projeto**. As regras universais (SDD, TDD, Clean Code, validação, etc.) já estão no `AGENTS.md` e nas `.cursor/rules/`.

Quanto mais enxuto e factual, melhor o agente performa — menos tokens gastos com contexto irrelevante significa mais contexto disponível para a tarefa real.
