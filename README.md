# Kit de Governança para Agentes de Desenvolvimento

> Sistema de controle, auditoria e previsibilidade para agentes AI (Claude Code, Cursor, Codex, Copilot).
> Independente de projeto. Genérico. Reutilizável.

---

## Estrutura do kit

```
projeto/
├── AGENTS.md                   # Como o agente trabalha (universal)
├── CLAUDE.md                   # O que o projeto é (específico)
├── .cursor/
│   └── rules/
│       ├── protocol.mdc        # Governança central (alwaysApply)
│       ├── anti-hallucination.mdc  # Anti-alucinação (alwaysApply)
│       ├── language.mdc        # Política de idioma (alwaysApply)
│       ├── django-architecture.mdc # MVT + services (globs: **/*.py)
│       ├── clean-code.mdc      # Código limpo (globs: **/*.py)
│       ├── security.mdc        # Segurança (globs: **/*.py)
│       ├── testing.mdc         # TDD (globs: **/tests/**/*.py)
│       ├── templates-static.mdc # Templates (globs: **/templates/**/*.html)
│       ├── validation.mdc      # Checklist de validação (agent-requested)
│       ├── prd.mdc             # Estrutura de PRD (agent-requested)
│       └── environment.mdc     # Ambiente Windows/PS (agent-requested)
└── docs/
    └── prd/                    # PRDs do projeto
```

---

## Como usar

### 1. Novo projeto

1. Copie `AGENTS.md` para a raiz do novo projeto (não altere — é universal)
2. Copie `CLAUDE.md` para a raiz e preencha os placeholders `<...>`
3. Copie a pasta `.cursor/rules/` inteira para a raiz
4. Crie a pasta `docs/prd/`
5. Pronto — qualquer agente que leia esses arquivos vai operar sob o protocolo

### 2. Projeto existente

1. Copie os 3 artefatos para a raiz
2. Preencha `CLAUDE.md` com os dados reais do projeto
3. Verifique se há conflito entre os comandos documentados e os que existem de fato
4. Rode o projeto e valide que os comandos do `CLAUDE.md` funcionam

### 3. Compatibilidade entre ferramentas

| Ferramenta | Lê `AGENTS.md` | Lê `CLAUDE.md` | Lê `.cursor/rules/` |
|---|---|---|---|
| Claude Code | sim | sim (nativo) | não |
| Cursor | sim | sim (via @) | sim (nativo) |
| Codex (OpenAI) | sim (nativo) | não | não |
| Copilot | via .github/ | não | não |
| Gemini CLI | sim | não | não |

Para ferramentas que não leem `CLAUDE.md`, o `AGENTS.md` contém o protocolo completo. O `CLAUDE.md` adiciona contexto específico do projeto.

Para ferramentas que não leem `.cursor/rules/`, as regras já estão consolidadas no `AGENTS.md`.

---

## Filosofia

### O que o agente deve fazer

- Ler integralmente os arquivos do fluxo antes de decidir
- Buscar contexto externo (docs oficiais, Context7, Playwright)
- Criar PRD antes de mudança relevante
- Seguir SDD (spec antes de código) e TDD (Red-Green-Refactor)
- Validar com evidência observável antes de declarar sucesso
- Limpar tudo ao final — sistema pronto para o desenvolvedor

### O que o agente nunca deve fazer

- Inventar comportamento, comando ou integração
- Decidir por snippet quando existe o arquivo completo
- Criar migrações sem autorização explícita
- Hardcodar valores configuráveis
- Mascarar erro para forçar funcionamento
- Declarar sucesso sem evidência

---

## Economia de tokens

O kit foi desenhado para minimizar impacto no context window:

- `AGENTS.md` é universal — não muda entre projetos
- `CLAUDE.md` é enxuto — apenas contexto específico, sem duplicação
- `.cursor/rules/` são modulares — cada arquivo under 1400 bytes
- Apenas 3 rules usam `alwaysApply: true` (protocol, anti-hallucination, language)
- As demais ativam por `globs` (auto) ou por descrição (agent-requested)
- Nenhuma rule contradiz outra — foram desenhadas como conjunto coerente

---

## Fluxo completo de uma demanda

```
1. Preflight
   └── Validar AGENTS.md + CLAUDE.md + ambiente + ferramentas

2. Classificação
   └── Que tipo de demanda é? (feature, bug, refatoração, etc.)

3. Leitura integral
   └── Ler todos os arquivos do fluxo impactado

4. PRD (se mudança relevante)
   └── Criar docs/prd/PRD-<NNN>-<slug>.md com prompt de execução

5. Implementação (SDD + TDD)
   └── Models → Forms → Services → Views → URLs → Templates → Static → Tests

6. Validação completa
   └── Testes + check + collectstatic + showmigrations + shell checks
   └── Playwright + console do navegador + terminal
   └── Sem hardcode + sem mascaramento + sem prints

7. Limpeza final
   └── Remover temporários, logs, comentários provisórios

8. Fechamento
   └── Resumo + evidências + pendências + desvios + status real
```

---

## Manutenção

- Atualize `CLAUDE.md` quando mudar stack, arquitetura, comandos ou integrações
- `AGENTS.md` raramente precisa mudar — é o protocolo universal
- `.cursor/rules/` podem receber novas rules quando um erro se repetir
- Regra de ouro: **adicione uma rule na segunda vez que ver o mesmo erro**
