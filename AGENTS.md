# AGENTS.md

Protocolo comum do LV JIU JITSU para Claude, Codex, Cursor e agentes compatíveis.

## 1. Precedência

1. Solicitação atual do usuário.
2. Segurança, integridade, autorização e rastreabilidade.
3. Este arquivo.
4. `CLAUDE.md`.
5. PRD ativa e contratos locais.
6. Adaptadores da ferramenta.

Divergência entre fontes bloqueia a conclusão até ser resolvida.

## 2. Fontes de verdade

| Responsabilidade | Fonte |
|---|---|
| Protocolo comum | `AGENTS.md` |
| Fatos do LV | `CLAUDE.md` |
| Fluxo detalhado | `docs/AGENT-WORKFLOW.md` |
| Padrão de PRD | `docs/PRD-STANDARD.md` |
| Diferenças por ferramenta | `docs/PLATFORM-ADAPTERS.md` |
| UI/UX | `docs/UI-SCREEN-CONTRACT.md` |
| Banco e seeds | `docs/OPERACAO-BANCO-SEEDS.md` |
| Pagamentos | `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` e PRD-058 |
| Comportamento da mudança | PRD correspondente |
| Comportamento real | código, testes e execução observável |

## 3. Idioma e comunicação

- Código, nomes técnicos, arquivos, classes e funções: inglês.
- Interface e mensagens ao usuário: português pt-BR.
- Respostas ao desenvolvedor: português pt-BR.
- Responder de forma mínima: entendimento, escopo, validação e próxima decisão.
- Não expor raciocínio interno. Informar conclusões, premissas e evidências.

## 4. Gate de entendimento e aprovação

Antes de alterar arquivos:

1. classificar a demanda;
2. executar preflight proporcional;
3. ler integralmente arquivos diretos e contratos adjacentes;
4. pesquisar documentação atual;
5. resumir o entendimento;
6. pedir aprovação quando a mudança ainda não estiver explicitamente autorizada.

Perguntas, leitura e diagnóstico sem escrita não exigem aprovação adicional.

Mudança visual exige antes do código:

- objetivo e preservação funcional;
- hierarquia, wireframe e estados;
- permissões e desktop/mobile;
- aprovação explícita da proposta.

Usar Plan mode, Figma, mockup ou recurso visual disponível. Não inventar uma ferramenta chamada “Claude Design”.

## 5. Contexto e pesquisa

- Busca textual localiza; não substitui leitura integral.
- Ler models, forms, services, selectors, views, URLs, templates, static e testes envolvidos.
- Usar Context7 primeiro para biblioteca, framework, SDK, CLI ou API.
- Consultar documentação oficial atual em seguida.
- Toda PRD registra ao menos uma fonte oficial relevante, conclusão e limitações.
- Se a ferramenta estiver indisponível, registrar a limitação sem inventar referência.

## 6. SDD e PRD

Mudança relevante exige PRD em `docs/prd/PRD-<NNN>-<slug>.md`.

A PRD deve:

- seguir `docs/PRD-STANDARD.md`;
- declarar skills;
- definir escopo, riscos e critérios verificáveis;
- separar evidência planejada de executada;
- manter checkboxes desmarcados até existir evidência;
- ser atualizada durante a execução.

## 7. TDD e autorização de testes

Para comportamento implementável:

1. escrever ou ajustar o teste antes do código;
2. implementar o mínimo;
3. refatorar mantendo o contrato.

Política:

- não executar testes sem autorização explícita;
- perguntar após implementar lógica ou corrigir erro;
- não declarar Red, Green ou regressão validada sem execução;
- registrar “teste escrito, não executado por política” quando aplicável.

Testes Django usam banco isolado. Reset destrutivo e seeds são operações separadas.

## 8. Validação

| Mudança | Validação padrão |
|---|---|
| UI, template, CSS, JS ou fluxo visual | navegador interno, desktop/mobile, caminho feliz, edge case, console e screenshot |
| Lógica Django | `manage.py check`, ORM seguro quando aplicável e oferta de teste focado |
| Persistência | ORM read-only por padrão; mutação exige autorização |
| Configuração/dependência | comando oficial proporcional ao risco |
| Documentação/governança | links, estrutura, busca textual e diff |

Em UI, validar no navegador imediatamente após implementar. Testes continuam sujeitos à autorização.

Pagamento real segue o documento operacional e exige ambiente, túnel, gateway e browser adequados.

## 9. Django MVT

| Camada | Responsabilidade |
|---|---|
| `models/` | Persistência e invariantes simples |
| `forms/` | Validação de entrada |
| `services/` | Regras de negócio e escrita transacional |
| `selectors/` | Leituras reutilizáveis e queries otimizadas |
| `views/` | HTTP fino |
| `templates/` | Apresentação |
| `static/` | CSS/JS por fluxo |
| `tests/` | Contratos por camada |

Usar `transaction.atomic` em múltiplas escritas e carregar relações para evitar N+1.

## 10. Clean code e segurança

- Menor mudança correta e causa raiz.
- Funções pequenas, nomes claros, guard clauses e no máximo dois níveis de condição.
- Configuração em `.env`, settings, banco ou fonte explícita.
- Sem segredo, credencial ou regra variável hardcoded.
- Sem `except: pass`, erro mascarado, query em loop ou `innerHTML` com dado do usuário.
- Sem regra de negócio central em template ou JavaScript.
- CSRF, validação server-side e permissão no backend.
- Não adicionar comentário ou docstring por padrão.
- Não editar `staticfiles/`.

## 11. Banco, migrations e seeds

- Não criar, editar ou aplicar migrations sem autorização explícita.
- O agente não executa reset destrutivo local, HG ou produção.
- Mudança de schema exige parada e decisão do usuário.
- Ciclos e seeds pertencem a `docs/OPERACAO-BANCO-SEEDS.md`.
- Seeds são explícitas; não inferir execução.

## 12. Limpeza e follow-up

Ao final:

1. revisar o diff e o fluxo tocado;
2. remover resíduos introduzidos;
3. procurar legado, duplicação, hardcode, órfãos e risco no escopo;
4. registrar dívida material fora do escopo em novo PRD;
5. pedir aprovação antes de implementar o follow-up.

Não expandir a tarefa indefinidamente.

## 13. Fechamento

Toda entrega informa:

- implementado;
- evidências reais;
- não validado e motivo;
- pendências e desvios;
- status: **concluída**, **concluída com limitações** ou **não concluída**.

## 14. Skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

Invocação e localização estão em `docs/PLATFORM-ADAPTERS.md`.
