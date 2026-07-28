# AGENTS.md

Protocolo comum do LV JIU JITSU para Claude, Codex, Cursor e agentes compatíveis.

Este arquivo diz o que vale. `CLAUDE.md` diz o que o projeto é.
`docs/AGENT-WORKFLOW.md` diz como executar. Um dono por assunto.

## 1. Precedência

1. Solicitação atual do usuário.
2. Segurança, integridade operacional e rastreabilidade.
3. Este arquivo.
4. `CLAUDE.md`.
5. PRD ativa e contratos locais.
6. Adaptadores da ferramenta.

Divergência material entre fontes bloqueia a conclusão até ser resolvida. A
precedência define qual contrato deve ser corrigido; não autoriza ignorar a
contradição, nem seguir a fonte mais alta fingindo que a mais baixa não
existe.

## 2. Fontes de verdade

Cada assunto tem um dono único. Os outros arquivos referenciam o dono; não
repetem a regra. Alterar uma regra exige editar apenas o dono.

| Responsabilidade | Dono único | Quem referencia |
|---|---|---|
| Protocolo comum | `AGENTS.md` | skills, `.cursor/rules/` |
| Fatos do produto, stack, ambientes e portas | `CLAUDE.md` | todos |
| Ciclo detalhado de execução | `docs/AGENT-WORKFLOW.md` | `AGENTS.md`, skills |
| Formato e numeração de PRD | `docs/PRD-STANDARD.md` | `lv-prd` |
| Contrato visual, estados e evidência | `docs/UI-SCREEN-CONTRACT.md` | `lv-ui-delivery` |
| Banco, migrations e seeds | `docs/OPERACAO-BANCO-SEEDS.md` | `CLAUDE.md`, `AGENTS.md` |
| Deploy Render e Supabase | `docs/DEPLOY-RENDER-SUPABASE.md` | `CLAUDE.md`, `AGENTS.md` |
| Roteiro de preenchimento para teste manual | `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` | `lv-ui-delivery` |
| Diferenças por ferramenta | `docs/PLATFORM-ADAPTERS.md` | `AGENTS.md` |
| Índice e próximo número de PRD | `docs/prd/README.md` | `lv-prd` |
| Comportamento da mudança | PRD correspondente | — |
| Comportamento real | código, testes e execução observável | — |

Contrato descreve o que existe. Ao divergir do código, o código vence e o
contrato é corrigido na mesma mudança.

## 3. Idioma e comunicação

- Código, nomes técnicos, arquivos, classes e funções: inglês.
- Interface, mensagens, PRDs, commits e respostas: português pt-BR, com
  acentuação correta.
- Informar entendimento, escopo, validação, limitações e próxima decisão.
- Não repetir ao operador o que ele acabou de dizer, nem pedir confirmação do
  que já foi ordenado.
- Não expor raciocínio interno. Informar conclusões, premissas e evidências
  verificáveis.

## 4. Gate de entendimento e execução

Antes de editar: classificar o pedido, executar preflight, ler os arquivos
diretos e adjacentes integralmente, pesquisar fontes atuais e confirmar o
entendimento.

Perguntas, leitura e diagnóstico sem escrita não exigem aprovação adicional.

Ordem explícita e inequívoca autoriza o escopo descrito — não é preciso
perguntar de novo. Pedido exploratório, ambíguo ou que implique expansão
material de escopo exige decisão do operador.

Mudança visual acrescenta um passo: hierarquia, wireframe e estados são
apresentados antes do código, conforme `docs/UI-SCREEN-CONTRACT.md`.

A ferramenta visual a usar por plataforma está em `docs/PLATFORM-ADAPTERS.md`.

## 5. Contexto e pesquisa

Context7 vem primeiro para biblioteca, framework, SDK, API ou CLI; depois,
documentação oficial da versão em uso.

Busca textual localiza, mas não substitui leitura integral: um `grep` que
acha a linha não mostra a guarda três funções acima. Ler models, forms,
services, selectors, views, URLs, templates, static e testes envolvidos.

Toda PRD registra ao menos uma fonte oficial relevante, a conclusão e as
limitações. Pesquisa sem relação com a demanda não preenche checklist.
Limitações de ferramenta são registradas no Context Ledger, nunca preenchidas
por suposição.

## 6. SDD e PRD

Mudança relevante exige PRD numerada em `docs/prd/PRD-<NNN>-<slug>.md`,
aprovada e atualizada **durante** a execução, não depois.

O número vem de `docs/prd/README.md`, não de `ls` — a listagem não revela gaps
reservados nem duplicatas. Ao criar ou fechar uma PRD, o índice é regenerado no
mesmo passo por `python scripts/build_prd_index.py`, que recusa colisão de
número.

A PRD declara skills, critérios verificáveis, testes, evidências, desvios,
limpeza, pendências e status. Critério só é marcado com evidência real;
inferência não fecha critério. Checkbox permanece desmarcado até existir
evidência.

## 7. TDD e execução de testes

Escrever ou ajustar primeiro o teste quando houver comportamento testável.
Observar o Red, implementar o mínimo, observar o Green, refatorar com a suíte
verde.

Executar teste focado e suíte proporcional ao risco da mudança. Não declarar
Red, Green ou ausência de regressão sem saída real de comando; registrar
comando e resultado. Testes Django usam banco isolado e não tocam o SQLite
local.

Quando não houver comportamento testável, dizer isso na PRD em vez de
inventar um teste que não prova nada.

## 8. Validação

| Mudança | Validação |
|---|---|
| UI, template, CSS ou JS | browser real, desktop e mobile, os dois temas, fluxo, edge case, console e screenshot |
| Django | `check`, teste focado, suíte proporcional e ORM quando couber |
| Persistência | `makemigrations --check --dry-run`, `showmigrations` e runbook de banco |
| Configuração | parser ou comando oficial, nunca leitura a olho |
| Skills e plataformas | `scripts/validate_skill_frontmatter.py` |
| PRD e índice | `scripts/build_prd_index.py --check` |
| Documentação | links verificados em disco, estrutura, busca e diff |

Em UI, validar no browser imediatamente após implementar. Não declarar
validação visual por leitura de template nem por teste automatizado.

"Implementado" não significa "validado". Sem execução observável, o item vai
para `Pending`, não para `Evidence`.

## 9. Django MVT

| Camada | Responsabilidade |
|---|---|
| `models/` | Persistência e invariantes |
| `forms/` | Validação de entrada |
| `services/` | Regras de negócio e escrita transacional |
| `selectors/` | Leituras reutilizáveis e queries otimizadas |
| `views/` | HTTP fino |
| `templates/` | Apresentação |
| `static/` | CSS/JS por fluxo |
| `tests/` | Contratos por camada |

Evitar N+1 e query dentro de laço; carregar relações com `select_related` e
`prefetch_related` onde forem usadas. Operação que altera mais de um registro
relacionado roda em `transaction.atomic`.

## 10. Clean code e segurança

Menor mudança correta, causa raiz, guard clauses, funções pequenas, nomes
claros, no máximo dois níveis de condição e configuração explícita.

Proibido: segredo hardcoded, erro mascarado, `except: pass`, query em loop,
`innerHTML` com dado do usuário, regra central de negócio em template ou
JavaScript, edição de `staticfiles/`.

**Código não tem comentário nem docstring.** A regra é absoluta e vale para
`.py`, `.html`, `.css` e `.js`: nome, assinatura e teste dizem o que o código
faz; o porquê vive na PRD e a operação vive em `docs/`. Explicação que só cabe
em comentário é sinal de código que precisa de nome melhor ou de PRD.

A única exceção é arquivo gerado por ferramenta — `migrations/` — que não é
editado à mão.

CSRF, validação server-side e permissão são resolvidos no backend.

Segredo operacional nunca é impresso em saída, log ou PRD, mesmo sendo
descartável. Ao ler arquivo de ambiente, reportar nomes de chave, não valores.

## 11. Banco, migrations e seeds

Reset, migrations, testes e ORM locais necessários ao escopo são autorizados
sem perguntar.

`clear_migrations.py` recusa qualquer ambiente que não seja inequivocamente
local: arquivo de ambiente fora da raiz, `.env.hg`, `.env.prod`,
`DJANGO_ENVIRONMENT` remoto, `DATABASE_URL` preenchida ou variável de seed
ausente. Em toda recusa, nada é apagado.

Seeds são sempre explícitas e nunca entram no Build Command. Dado de negócio
não é carregado implicitamente por migration.

Ação destrutiva no Supabase exige ambiente correto, `DEBUG=False`, host
oficial, `SUPABASE_PROJECT_REF` conferido, `SUPABASE_RESET_CONFIRM` e
`--execute`. Sem a flag, o comando simula. Detalhes em
`docs/OPERACAO-BANCO-SEEDS.md`.

## 12. Limpeza e follow-up

Revisar o diff inteiro e os contratos adjacentes; remover resíduos
introduzidos; procurar legado, duplicação, hardcode, órfão e risco no escopo;
corrigir documentação que a mudança tornou obsoleta.

Dívida material fora do escopo vira PRD de follow-up com número reservado, e
**não é implementada silenciosamente**. Ampliar escopo sem registro é tão
ruim quanto deixar a dívida.

## 13. Fechamento

Informar implementado, evidências com saída real, o que não foi validado,
pendências, desvios e status real: **concluída**, **concluída com
limitações** ou **não concluída**.

Concluída com limitações exige dizer qual limitação e por quê. Parte
bloqueada não transforma o resto em incompleto: entregar tudo que foi
possível e declarar explicitamente o que ficou de fora.

## 14. Skills obrigatórias

| Demanda | Skill |
|---|---|
| Toda mudança não trivial | `lv-task-intake` |
| PRD | `lv-prd` |
| Django | `lv-django-delivery` |
| UI | `lv-ui-delivery` |
| Fechamento | `lv-cleanup-audit` |
| Gerar prompt de execução | `lv-prompt-builder` |
| Auditar coerência do repositório | `lv-parity-audit` |

`lv-prompt-builder` é de invocação manual
(`disable-model-invocation`): entrega o prompt de execução e para, sem
implementar.

Cada `SKILL.md` segue a estrutura `Quando acionar` / `Passos` / `Saída` /
`Parar quando`.

As sete vivem em `.claude/skills/`, fonte de edição, e são espelhadas byte a
byte em `.agents/skills/` e `.cursor/skills/`. Ausência em qualquer
plataforma é divergência a corrigir, verificada por
`scripts/validate_skill_frontmatter.py` no CI. Invocação e localização por
ferramenta estão em `docs/PLATFORM-ADAPTERS.md`.
