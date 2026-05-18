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
- **nunca escrever migrações** — nem manualmente, nem via `makemigrations` autônomo; mudanças de schema requerem o ciclo destrutivo executado pelo usuário

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

### Setup mínimo (apenas o necessário para subir)

O sistema sobe sem nenhum dado de seed. Seeds são opcionais e serão recriadas uma a uma com validação manual.

```powershell
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Seeds disponíveis

> **Estado atual:** seeds estão sendo recriadas incrementalmente. Cada seed é validada com o usuário antes de ser considerada estável. A tabela abaixo reflete apenas os comandos que existem no repositório.

| Comando | Função | Depende de | Status |
|---|---|---|---|
| `create_admin_superuser` | cria superusuário administrativo | — | ativo |
| `seed_system_initial_person_type` | cria os 5 tipos de pessoa base | — | ativo |
| `seed_system_initial_teacher` | cria professores iniciais + contas de portal | `seed_system_initial_person_type` | ativo |
| `seed_system_initial_belt_ranks` | cria as 13 faixas com progressão e cores | — | ativo |
| `seed_system_initial_administrative` | cria usuários administrativos + histórico de graduação | `seed_system_initial_person_type`, `seed_system_initial_belt_ranks` | ativo |
| `seed_system_initial_class_categories` | cria as 4 categorias de turma (Adulto, Juvenil, Kids, Feminino) | — | ativo |
| `seed_system_initial_class_categories_teacher` | vincula cada professor à sua categoria principal | `seed_system_initial_teacher`, `seed_system_initial_class_categories` | ativo |
| `seed_system_initial_class_categories_administrative` | vincula cada administrativo à sua categoria | `seed_system_initial_administrative`, `seed_system_initial_class_categories` | ativo |
| `seed_system_initial_class_catalog` | cria turmas (`ClassGroup`) e horários (`ClassSchedule`) | `seed_system_initial_teacher`, `seed_system_initial_class_categories` | ativo |
| `seed_system_initial_class_catalog_administrative` | vincula administrativos à turma principal (`Person.class_group`) | `seed_system_initial_administrative`, `seed_system_initial_class_catalog` | ativo |
| `seed_system_initial_teacher_payroll_configs` | cria configurações iniciais de repasse dos professores | `seed_system_initial_teacher`, `seed_system_initial_class_catalog` | ativo |
| `seed_system_initial_holidays` | cria feriados iniciais de 2026 | — | ativo |
| `seed_system_initial_ibjjf_age_categories` | cria as 22 categorias de idade IBJJF (Pré-Mirim a Master 7) | — | ativo |
| `seed_system_initial_graduation_rules` | cria as 52 regras de graduação (adulto e infantil) | `seed_system_initial_belt_ranks` | ativo |
| `seed_system_initial_product_categories` | cria as 4 categorias de produto (Faixas, Kimonos, Rash Guard, Patches) | — | ativo |
| `seed_system_initial_product_catalog` | cria 5 produtos e 62 variantes com estoque inicial | `seed_system_initial_product_categories` | ativo |
| `seed_system_initial_subscription_plans` | cria 72 planos de assinatura (3 categorias × 2 frequências × 3 gateways × 4 ciclos) com precificação dinâmica | — | ativo |
| `seed_system_initial_subscription_plans_values` | cria/atualiza 72 valores reais de cobrança dos planos por categoria, frequência, gateway e periodicidade | `seed_system_initial_subscription_plans` | ativo |

### Arquitetura de seeds

- o sistema funciona como casca sem nenhuma codependência com seeds
- seeds são convenientes (poupam cadastro manual), não são requisito de boot
- cada seed deve falhar explicitamente quando uma dependência não foi executada
- não existe orquestrador: execução é manual e sequencial
- dados JSON das seeds vivem em `static/initial_data/`
- quando um JSON pertence a uma única seed, o nome do arquivo deve acompanhar o comando consumidor (`seed_system_initial_<dominio>.json`)
- JSONs compartilhados por duas ou mais seeds devem ser desmembrados por responsabilidade antes de receberem nomes específicos de seed
- seeds **nunca** aceitam argumentos `--` na linha de comando; toda configuração vem de variáveis de ambiente definidas no `.env`

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
- o sistema sobe sem nenhum dado — seeds são opcionais e poupam cadastro manual
- não existe o package `system/management/seeders/` — seeds são comandos individuais em `system/management/commands/`
- cada seed deve falhar explicitamente quando uma dependência não foi executada
- seeds são recriadas incrementalmente com validação manual; a lista de comandos no CLAUDE.md reflete apenas os existentes

### Schema
- existe apenas `system/migrations/0001_initial.py` (gerada pelo ciclo destrutivo)
- **é proibido escrever migrações manualmente** — nem `0001`, nem `0002`, nunca
- quando o modelo mudar, o agente deve: (1) corrigir o código, (2) solicitar ao usuário que rode o ciclo destrutivo
- o agente **nunca** executa o ciclo destrutivo por conta própria — apenas instrui o usuário a rodar

### Ciclo destrutivo (solicitado ao usuário, nunca executado pelo agente)

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
```

Após migrar, re-rodar as seeds necessárias.

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

## 11. Contrato local de UI e redesign

O redesign visual e responsivo do sistema é governado por:

- `docs/UI-SCREEN-CONTRACT.md`
- PRDs específicas em `docs/prd/`

### Regras locais para rework de tela

- nenhuma tela pode ser reimplementada sem PRD ou item explícito em PRD
- nenhuma funcionalidade existente pode ser removida, escondida ou substituída por aparência
- tema claro e escuro são obrigatórios em toda tela alterada
- telas devem ser validadas em desktop e mobile antes de conclusão
- telas administrativas devem priorizar densidade, escaneabilidade e operação real
- telas públicas podem usar assets visuais LV, mas sem quebrar cadastro, login ou pagamento
- é proibido criar novas pastas; novos arquivos só podem ser criados dentro de pastas já existentes
- `staticfiles/` continua sendo saída gerada e não deve ser editado
- quando CSS/JS versionado por `?v=` for alterado, o template correspondente deve atualizar a versão
- JavaScript e CSS inline existentes devem ser tratados quando a tela correspondente entrar no escopo, sem criar regra de negócio no frontend

### Fonte de verdade de UI

O contrato de UI documenta os papéis reais do sistema (`student`, `guardian`, `dependent`, `instructor`, `administrative-assistant` e admin técnico), os módulos de tela, responsividade, componentes mínimos, validação visual e critérios de parada.

Se houver divergência entre `docs/UI-SCREEN-CONTRACT.md`, PRD da tela, `CLAUDE.md`, `AGENTS.md` e o código real, a tarefa deve parar até a divergência ser resolvida.

---

## 12. Regra final de manutenção

Atualizar este arquivo quando houver:

- novo comando real de setup/seed/check
- nova integração externa
- mudança na estrutura principal do app `system/`
- mudança no padrão de assets estáticos versionados manualmente
- mudança no contrato local de UI e redesign

### Changelog da spec

```md
- **[2026-04-21]** CLAUDE.md reescrito com contexto factual do projeto LV JIU JITSU.
- **[2026-05-07]** Removido `inicial_seed` da documentação operacional; setup base passou a usar sequência explícita de seeds granulares.
- **[2026-05-07]** Separadas seeds de categorias, faixas, regras de graduação, professores oficiais, repasses, categorias de produto e produtos; logs de auditoria passaram a listar registros cadastrados.
- **[2026-05-11]** Seeds opcionais por `.env` (`SEED_ENABLE_*`, `SEED_STRICT`, `SEED_DATA_ROOT`); dados volumosos em `config/initial_data/*.json` carregados via `system/services/initial_load/`.
- **[2026-05-12]** Seeds atomicas e manuais; removidos `initial_load`/`seeding` como arquitetura oficial e agregadores de seed.
- **[2026-05-16]** Sistema reestruturado para subir como casca sem codependência com seeds; package `system/management/seeders/` removido; seeds serão recriadas incrementalmente; testes seed-dependentes eliminados da suite.
- **[2026-05-16]** Seeds passam a não aceitar argumentos `--`; toda configuração via `.env`. Implementadas `seed_system_initial_person_type` e `seed_system_initial_teacher`. Dados JSON em `static/initial_data/`.
- **[2026-05-16]** Criado contrato local de UI e redesign responsivo em `docs/UI-SCREEN-CONTRACT.md`; reworks de tela passam a exigir PRD por etapa, preservação de funcionalidades e validação visual desktop/mobile.
- **[2026-05-16]** Implementadas `seed_system_initial_belt_ranks`, `seed_system_initial_administrative`, `seed_system_initial_class_categories`, `seed_system_initial_class_categories_teacher`, `seed_system_initial_class_categories_administrative`, `seed_system_initial_class_catalog`, `seed_system_initial_class_catalog_administrative`. Dados JSON em `static/initial_data/`.
- **[2026-05-16]** Removido `ClassGroup.code` (SlugField hardcoded); identificação de turmas passa a ser feita por relacionamentos (`class_category` + `main_teacher`). Payroll rules migrado de `class_group_code` para `class_group_id`.
- **[2026-05-16]** Regra definitiva: **nunca escrever migrations**. Mudanças de schema exigem ciclo destrutivo (`clear_migrations.py` → `makemigrations` → `migrate`) executado **pelo usuário**, nunca pelo agente.
- **[2026-05-17]** Implementadas `seed_system_initial_ibjjf_age_categories`, `seed_system_initial_graduation_rules`, `seed_system_initial_product_categories`, `seed_system_initial_product_catalog`. Preço unitário dos produtos inicializado como R$ 0,00 — configurar via admin.
- **[2026-05-17]** Implementada `seed_system_initial_subscription_plans` com 72 planos (Individual, Fidelidade, Família × 2x/5x × Asaas PIX, Asaas Cartão, Stripe Cartão × 4 ciclos). Modelo `SubscriptionPlan` expandido com campos de precificação dinâmica (`base_monthly_net_price`, `gateway_fixed_fee`, `gateway_percentage_fee`, `cycle_discount_percentage`, `is_loyalty_plan`); `price` calculado automaticamente em `save()`. Requer ciclo destrutivo.
- **[2026-05-18]** JSONs de seeds com consumidor único renomeados para acompanhar o comando consumidor; JSONs compartilhados permanecem pendentes de desmembramento por responsabilidade.
- **[2026-05-18]** Implementada `seed_system_initial_teacher_payroll_configs`; repasses de professores passam a usar JSON próprio e resolver turmas por `class_category` + CPF do professor principal, sem `ClassGroup.code`.
- **[2026-05-18]** Implementada `seed_system_initial_holidays` para feriados iniciais de 2026 via JSON próprio, substituindo o legado `seed_holidays --year 2026` sem argumentos de linha de comando.
- **[2026-05-18]** Implementada `seed_system_initial_subscription_plans_values` para aplicar os valores reais dos planos enviados em planilha, preservando preço cobrado, taxas, descontos e valor líquido desejado em campos editáveis.
```
