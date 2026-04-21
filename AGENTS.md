# AGENTS.md

> Protocolo universal, obrigatório, auditável e reutilizável para agentes de desenvolvimento.
> Este arquivo define **como o agente deve trabalhar** — independente do projeto.
> O contexto específico do projeto fica em `CLAUDE.md`.
>
> **Prioridade absoluta:** controle, coerência, evidência e previsibilidade.
> Se houver conflito entre velocidade e controle, **vence controle**.
> Se houver conflito entre brevidade e completude, **vence completude**.
> Se houver conflito entre "parece pronto" e "é verificável", **vence o que é verificável**.

---

## 1. Precedência

1. solicitação atual do usuário
2. segurança, integridade, rastreabilidade e conformidade
3. este `AGENTS.md`
4. `CLAUDE.md`
5. regras locais do repositório (`.cursor/rules/`, `.github/`, etc.)

Se `AGENTS.md` e `CLAUDE.md` divergirem, a tarefa **não está concluída** até a divergência ser corrigida.

---

## 2. Princípios inegociáveis

- spec antes de código (SDD)
- teste antes de implementação (TDD)
- validação antes de declarar sucesso
- evidência antes de alegação
- leitura integral antes de conclusão
- código simples antes de "esperteza"
- correção limpa antes de remendo frágil
- comportamento dinâmico antes de hardcode
- erro explícito antes de mascaramento
- contexto oficial antes de achismo
- menor mudança correta antes de expansão de escopo

---

## 3. Política de idioma

- identificadores técnicos, arquivos, classes, funções, variáveis, comandos e nomes de artefatos: **inglês**
- texto visível ao usuário final: **português pt-BR**, salvo regra explícita diferente no projeto
- respostas ao desenvolvedor: **português pt-BR**

---

## 4. Política central anti-alucinação

O agente **nunca** deve:

- assumir que entendeu o fluxo por um snippet
- assumir que o README está correto sem conferir o código
- assumir que um comando existe sem verificar
- assumir que uma ferramenta está funcional sem testá-la na sessão
- assumir que implementação pronta significa validação concluída
- inventar comportamento, integração, rota, comando, migração, seed ou contrato
- declarar sucesso sem evidência observável

Toda conclusão relevante deve estar apoiada por pelo menos um destes pilares:

- leitura integral dos arquivos do fluxo
- documentação oficial
- execução observável de comando
- teste automatizado
- validação visual
- inspeção de console, terminal ou ORM
- evidência registrada no PRD ou relatório final

---

## 5. Leitura integral obrigatória

Antes de responder, diagnosticar, planejar, editar, implementar ou concluir:

1. identificar os arquivos diretamente envolvidos no fluxo
2. ler **integralmente** cada arquivo relevante
3. ler contratos adjacentes do fluxo
4. só então produzir diagnóstico, plano, código ou conclusão

Arquivos adjacentes típicos, quando existirem:

- `models/`, `forms/`, `serializers/`, `services/`, `selectors/`
- `views/`, `urls.py`, `templates/`, `static/`, `tests/`
- `settings.py`, `middleware.py`, `signals.py`, `tasks.py`
- `management/commands/`, PRDs, documentação arquitetural

É **proibido**:

- decidir por grep quando o fluxo depende do arquivo completo
- alterar código crítico sem ler contratos e testes adjacentes
- alegar entendimento sem registrar o que foi lido
- pular arquivo porque "parece irrelevante"

---

## 6. Contexto externo obrigatório

Quando aplicável, o agente deve buscar contexto fora do repositório:

- **internet** para documentação oficial, troubleshooting, práticas atuais e comportamento de ferramenta
- **Context7 ou MCP documental equivalente** para bibliotecas, frameworks, setup, configuração e APIs
- **Playwright MCP ou browser automation** para validação funcional e visual

Ordem padrão:

- documentação de biblioteca ou framework: Context7 primeiro, docs oficiais em seguida
- comportamento atual de ferramenta ou ambiente: docs oficiais primeiro
- UI web: browser/Playwright antes de alegar que validou interface

---

## 7. Preflight obrigatório

Nada começa antes de validar:

1. alinhamento entre `AGENTS.md` e `CLAUDE.md`
2. shell e ambiente corretos
3. interpretador correto (`.venv` ou equivalente)
4. acesso à internet quando exigido
5. ferramentas obrigatórias da demanda
6. comandos reais do projeto
7. viabilidade da validação exigida

Se algo crítico falhar:

- corrigir primeiro
- registrar o impacto real
- seguir em modo degradado apenas se ainda houver segurança e coerência
- marcar como **não concluída** quando a limitação invalidar a tarefa

---

## 8. Classificação obrigatória da demanda

Toda demanda deve ser classificada antes da execução:

- pergunta exploratória
- diagnóstico de erro
- correção pontual
- refatoração
- nova feature
- alteração arquitetural
- integração externa
- revisão de segurança
- revisão de performance
- revisão de governança do agente
- regeneração documental

A classificação define profundidade mínima de contexto, PRD, testes e validação.

---

## 9. SDD — Spec-Driven Development

A especificação (PRD) é a **fonte de verdade** do comportamento esperado.
O código, os testes e a validação devem ser **derivados** da spec.

### Por que SDD

- separa a fase de **design** da fase de **implementação**
- o PRD funciona como um "super-prompt" que comprime contexto para o agente
- especificações comportamentais eliminam ambiguidade e reduzem alucinação
- permite trabalhar em incrementos pequenos e validáveis
- cria trilha de auditoria: requisitos → design → código → testes → evidência

### Características de uma boa spec

- focada em **comportamento** (o que acontece), não em implementação (como faz)
- **testável**: cada requisito é verificável por comando, teste ou inspeção visual
- **não ambígua**: leitores diferentes chegam à mesma interpretação
- **completa o suficiente** sem sobre-especificar

### Fluxo SDD

1. requisitos em linguagem natural
2. análise e design (PRD)
3. revisão humana do PRD
4. implementação guiada pela spec
5. validação contra os critérios de aceite da spec

---

## 10. TDD — Test-Driven Development

Para implementação, seguir o ciclo **Red-Green-Refactor**:

1. **Red**: escrever teste que falha (o comportamento esperado ainda não existe)
2. **Green**: implementar o código mínimo para o teste passar
3. **Refactor**: limpar o código mantendo todos os testes verdes

### Double-loop TDD (para fluxos com interface)

- **loop externo**: teste funcional / E2E (comportamento do usuário, Playwright)
- **loop interno**: testes unitários (models, forms, services, selectors, views)

### Estrutura de testes por camada

```
<app>/tests/
├── __init__.py
├── test_models.py
├── test_forms.py
├── test_services.py
├── test_selectors.py
├── test_views.py
└── test_commands.py
```

### Regras de teste

- usar `setUp` / `setUpTestData` — nunca hardcodar dados repetidos em cada teste
- agrupar testes por classe refletindo o módulo testado
- nomear testes descrevendo o comportamento esperado
- cobrir fluxo feliz, fluxo de erro e edge cases

---

## 11. PRD obrigatório

Toda mudança relevante começa com um PRD em:

`docs/prd/PRD-<NNN>-<slug>.md`

### Estrutura mínima obrigatória

```md
# PRD-<NNN>: <Título>

## Resumo do que será implementado
## Tipo de demanda
## Problema atual
## Objetivo

## Context Ledger
### Arquivos lidos integralmente
- ...

### Arquivos adjacentes consultados
- ...

### Internet / documentação oficial
- ...

### MCPs / ferramentas verificadas
- ferramenta — status — teste executado

### Limitações encontradas
- ...

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em <STACK> seguindo SDD + TDD + <PARADIGMA>.

### Ação
Implementar <O QUE> seguindo a spec abaixo.

### Contexto
<POR QUE e ONDE se encaixa no sistema>

### Restrições
- sem hardcode
- sem mascaramento de erro
- sem migrações (salvo exceção explícita)
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] Ao fazer X, o sistema deve Y (verificável por: teste / comando / visual)
- [ ] Se Z inválido, o sistema deve retornar erro W (verificável por: teste)

### Evidências esperadas
- testes passando
- console do navegador limpo
- terminal sem stack trace
- shell check do ORM

### Formato de saída
Código implementado + testes + evidências de validação

## Escopo
## Fora do escopo
## Arquivos impactados

## Riscos e edge cases

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações (política do projeto)
- leitura integral obrigatória
- validação obrigatória

## Plano
- [ ] 1. Contexto e leitura integral
- [ ] 2. Contratos e modelagem
- [ ] 3. Testes (Red)
- [ ] 4. Implementação (Green)
- [ ] 5. Refatoração (Refactor)
- [ ] 6. Validação completa
- [ ] 7. Limpeza final
- [ ] 8. Atualização documental

## Validação visual
### Desktop
### Mobile
### Console do navegador
### Terminal

## Validação ORM
### Banco
### Shell checks
### Integridade do fluxo

## Validação de qualidade
### Sem hardcode
### Sem estruturas condicionais quebradiças
### Sem `except: pass`
### Sem mascaramento de erro
### Sem comentários e docstrings desnecessários

## Evidências
## Implementado
## Desvios do plano
## Pendências
```

Sem PRD em mudança relevante, a tarefa **não está concluída**.

---

## 12. Estratégia padrão de implementação

Salvo restrição explícita do projeto:

1. contratos e modelagem
2. validação de entrada
3. regra de negócio (services)
4. leitura e consulta (selectors)
5. interface HTTP (views)
6. rotas (urls)
7. templates
8. arquivos estáticos
9. testes (Red → Green → Refactor)
10. validação completa
11. limpeza final
12. atualização documental

---

## 13. Diretrizes padrão para Django

Quando o projeto for Django, seguir por padrão:

### Arquitetura MVT

| Camada | Responsabilidade | Regra |
|---|---|---|
| `models/` | persistência e invariantes de domínio | regras simples de domínio |
| `forms/` | validação de entrada server-side | `clean_<field>()` e `clean()` |
| `services/` | lógica de negócio e orquestração | `@transaction.atomic` em múltiplas escritas |
| `selectors/` | leitura complexa e consultas reutilizáveis | `select_related()` e `prefetch_related()` |
| `views/` | camada fina de HTTP | delega para services, nunca concentra lógica |
| `templates/` | apresentação | herdam `base.html`, sem lógica de negócio |
| `static/` | CSS e JS | separados por tela e por namespace |
| `tests/` | cobertura por camada | Red-Green-Refactor |

### Patterns obrigatórios

- views finas — lógica de negócio **nunca** só na view
- services recebem dados já validados pelo Form
- `@transaction.atomic` em fluxos com múltiplas escritas
- exceção explícita em erro (nunca `None` silencioso, nunca `except: pass`)
- `select_related()` / `prefetch_related()` para evitar N+1
- `CheckConstraint`, managers e querysets quando fizer sentido
- CSRF ativo (`{% csrf_token %}` em todo POST)
- segredos em `.env` ou fonte equivalente
- rotas, labels e mensagens para o usuário em pt-BR
- nenhuma regra de negócio central em template ou JavaScript de interface
- CSS e JS separados por tela e por namespace — nunca inline sem justificativa

---

## 14. Clean Code — qualidade de código

### Obrigatório

- código limpo e legível
- funções pequenas e focadas
- guard clauses em vez de cascatas longas de `if/else`
- máximo 2 níveis de aninhamento condicional
- comportamento configurável vindo de `settings`, `.env`, banco ou fonte explícita
- exceções específicas
- nomes claros e descritivos (auto-explicativos — dispensam comentário)
- composição antes de herança quando fizer sentido
- estrutura simples, dinâmica e expansível
- DRY: lógica repetida deve ser extraída para funções, decorators ou mixins

### Proibido

- hardcode de segredo, token, credencial, regra variável ou valor configurável
- `except: pass`
- `except Exception` genérico sem critério técnico explícito
- condicionais longas e quebradiças (máx. 2 níveis de aninhamento)
- mascarar erro para produzir "funcionamento aparente"
- God Class (uma classe fazendo tudo)
- CSS/JS inline sem justificativa formal
- arquivo monolítico que mistura responsabilidades por conveniência
- `innerHTML` com dados do usuário
- `.all()` sem paginação ou justificativa
- queries em loop (N+1)

### Comentários e docstrings

Por padrão, **evitar** comentários e docstrings.
Código bem escrito deve ser auto-explicativo.

Só são aceitáveis quando **estritamente necessários** para:

- contrato público não trivial
- integração externa
- decisão arquitetural não inferível pela estrutura
- risco real de ambiguidade

---

## 15. Política de migração

**Nunca criar migrações por padrão.**

Correções e implementações devem priorizar:

- serviço, formulário, consulta, template, view, configuração, fluxo, contrato existente e organização do código

Se a única solução aparente exigir alteração de schema, isso deve ser tratado como **bloqueio ou exceção explícita** do projeto.
Sem autorização expressa, não criar migrações.

---

## 16. Validação funcional obrigatória

Nenhuma mudança relevante pode ser dada como pronta sem validação.

### Quando aplicável, validar:

- rota (responde corretamente)
- renderização (template carrega sem erro)
- botões e ações críticas (funcionam no fluxo real)
- mensagens de sucesso e erro (exibidas corretamente)
- estados vazios e edge cases
- autenticação e permissões
- console do navegador (sem erros JS críticos)
- terminal do servidor (sem stack trace)
- persistência via ORM ou shell check
- impacto em desktop e mobile
- regressões do fluxo relacionado

---

## 17. Playwright e validação visual

Quando houver UI web, a validação mínima deve incluir:

- abrir a tela real (servidor na porta canônica do projeto)
- validar fluxo crítico (navegação, formulários, botões, rotas)
- inspecionar console do navegador
- inspecionar terminal/logs
- validar estados, mensagens e permissões
- usar seletores resilientes e semânticos (`getByRole`, `getByLabel`, `getByText`)
- usar assertions que aguardam o estado esperado (auto-retry do Playwright)
- não declarar validação visual com base apenas em leitura de template ou screenshot isolada

### Não é aceito

- declarar validação visual sem abrir navegador
- validar apenas por leitura de template
- usar porta alternativa para contornar erro de ambiente
- prosseguir com Playwright quebrado sem tentar corrigir

---

## 18. Validação técnica mínima

Quando aplicável, executar e registrar evidência de:

- ambiente e dependências
- `.venv` ou ambiente equivalente
- `manage.py test --verbosity 2` (0 falhas, 0 erros)
- `manage.py check`
- `manage.py check --deploy` quando fizer sentido
- `manage.py collectstatic --noinput` quando houver estáticos
- `manage.py showmigrations`
- shell checks via ORM
- logs de execução
- ausência de stack trace não tratado
- ausência de erro JS crítico
- ausência de 404 relevante de estáticos

---

## 19. Segurança

- **nunca** hardcodar `SECRET_KEY`, senhas, tokens ou chaves de API
- CSRF ativo: `{% csrf_token %}` em todo formulário POST
- validação server-side obrigatória (frontend bloqueia para UX, backend por segurança)
- nunca concatenar strings em queries — usar ORM ou queries parametrizadas
- nunca `|safe` ou `mark_safe()` em dados do usuário sem sanitização
- views protegidas com `@login_required` / `@permission_required`
- nunca confiar em esconder botões como mecanismo de permissão
- upload: validar MIME, extensão e tamanho no backend
- `DEBUG` nunca `True` em produção — ler de `.env`
- nunca credenciais em JS/HTML
- nunca `innerHTML` com dados do usuário

---

## 20. Limpeza final obrigatória

Antes de encerrar:

- remover arquivos temporários criados só para diagnóstico
- remover prints, logs e código provisório de depuração
- remover comentários temporários
- remover fixtures improvisadas não aprovadas
- remover scripts descartáveis criados só para contornar ambiente
- deixar apenas código, testes e documentação que pertençam ao estado final
- sistema **limpo e pronto** para validação do desenvolvedor

---

## 21. Fechamento obrigatório

Toda entrega termina com:

- resumo do que foi analisado ou implementado
- evidências reais de validação
- o que não foi validado e por quê
- pendências reais
- desvios do plano
- status final verdadeiro:
  - **concluída**
  - **concluída com limitações**
  - **não concluída**

---

## 22. Critérios de não conclusão

Marcar como **não concluída** quando houver:

- leitura parcial do fluxo
- ausência de PRD quando necessário
- validação não executada
- execução inventada
- evidência insuficiente
- ferramenta crítica indisponível sem mitigação segura
- hardcode introduzido
- erro mascarado
- migração criada em desacordo com a política
- documentação final desalinhada
- limpeza final não realizada

---

## 23. Ambiente operacional

### Windows + PowerShell (quando aplicável)

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

**Armadilhas que o agente deve evitar:**

- `&&` não funciona no PowerShell — usar `;` ou executar um por vez
- `source` não existe — usar `.\.venv\Scripts\Activate.ps1`
- caminhos usam `\`, não `/`
- preferir sempre `.\.venv\Scripts\python.exe` e `.\.venv\Scripts\pip.exe`
- nunca instalar no global
- nunca criar scripts wrapper como fuga do protocolo

### Linux/macOS (quando aplicável)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Gestão de dependências

- instalar: `pip install <pacote>` → `pip show <pacote>` → atualizar `requirements.txt` imediatamente
- `ModuleNotFoundError`: instalar → atualizar requirements → re-executar
- nunca `pip install --user`
- nunca adicionar lib sem atualizar requirements

---

## 24. Reset destrutivo local (somente sob pedido explícito)

**Não é o fluxo padrão.** Somente quando o usuário pedir e `CLAUDE.md` declarar banco descartável.

Executar na ordem definida em `CLAUDE.md`, usando **apenas comandos reais do projeto**.

Exemplo típico (adaptar conforme `CLAUDE.md`):

```powershell
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py <comando_superuser>
.\.venv\Scripts\python.exe manage.py <comando_seed>
.\.venv\Scripts\python.exe manage.py runserver <HOST:PORT>
```

Não editar migrations manualmente. Se comando não existir, reportar.

---

## 25. Fonte de verdade

| O quê | Onde |
|---|---|
| Como o agente trabalha | Este `AGENTS.md` |
| O que o projeto é | `CLAUDE.md` |
| Requisitos de mudança | PRDs em `docs/prd/` |
| Fluxos reais | Código e testes |
