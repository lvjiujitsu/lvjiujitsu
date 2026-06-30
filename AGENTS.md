# AGENTS.md

Protocolo comum do LV JIU JITSU para Claude, Codex, Cursor e agentes compatíveis.

## 1. Precedência

1. Solicitação atual do usuário.
2. Segurança, integridade operacional e rastreabilidade.
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

## 4. Gate de entendimento e execução

Antes de alterar arquivos:

1. classificar a demanda;
2. executar preflight proporcional;
3. ler integralmente arquivos diretos e contratos adjacentes;
4. pesquisar documentação atual;
5. resumir o entendimento;
6. seguir para execução quando a solicitação atual já autorizar o escopo.

Perguntas, leitura e diagnóstico sem escrita não exigem aprovação adicional.

Mudança visual deve registrar antes do código:

- objetivo e preservação funcional;
- hierarquia, wireframe e estados;
- permissões e desktop/mobile;
- aprovação explícita quando a solicitação atual não autorizar implementação.

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

## 7. TDD e execução de testes

Para comportamento implementável:

1. escrever ou ajustar o teste antes do código;
2. implementar o mínimo;
3. refatorar mantendo o contrato.

Política:

- testes locais estão autorizados para entregas operacionais solicitadas;
- executar teste focado e/ou suíte proporcional ao risco antes do fechamento;
- não declarar Red, Green ou regressão validada sem execução;
- registrar comando e resultado real.

Testes Django usam banco isolado. Reset local, migrations locais e seeds locais podem ser executados quando forem necessários para o objetivo solicitado.

## 8. Validação

| Mudança | Validação padrão |
|---|---|
| UI, template, CSS, JS ou fluxo visual | navegador interno, desktop/mobile, caminho feliz, edge case, console e screenshot |
| Lógica Django | `manage.py check`, teste focado/suíte proporcional e ORM quando aplicável |
| Persistência | ORM local proporcional ao objetivo; escrita remota exige confirmação de ambiente |
| Configuração/dependência | comando oficial proporcional ao risco |
| Documentação/governança | links, estrutura, busca textual e diff |

Em UI, validar no navegador imediatamente após implementar. Testes locais fazem parte da validação.

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

- O agente pode criar, editar e aplicar migrations locais quando isso for necessário para o objetivo solicitado.
- O agente pode executar reset destrutivo local, `makemigrations`, `migrate`, seeds e testes quando a tarefa pedir reconstrução ou primeira carga local.
- Mudança de schema em HG ou produção exige confirmação explícita de ambiente.
- Ciclos e seeds pertencem a `docs/OPERACAO-BANCO-SEEDS.md`.
- Seeds são executadas de forma explícita e registrada; não mascarar falhas nem importar dados amplos sem necessidade do fluxo.

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
