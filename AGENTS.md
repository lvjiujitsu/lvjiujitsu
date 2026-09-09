# AGENTS.md

Contrato operacional do LV Jiu Jitsu para Claude Code, Codex e agentes compatíveis.

Este arquivo diz o que vale. `CLAUDE.md` diz o que o projeto é.
`obsidian/projetos/lvjiujitsu/ciclo-execucao-lvjiujitsu.md` diz como executar. Um
dono por assunto, e nenhum arquivo repete a regra de outro.

## Universo

- A documentação de contrato e operação vive no vault descrito abaixo.
- `CLAUDE.md` contém os fatos do produto, da stack e dos ambientes.
- A solicitação atual do operador tem precedência dentro dos limites de
  segurança, integridade operacional e rastreabilidade.
- Divergência material entre contratos bloqueia a conclusão até ser resolvida. A
  precedência define qual contrato corrigir; não autoriza ignorar a contradição,
  nem seguir a fonte mais alta fingindo que a mais baixa não existe.
- Contrato define o comportamento exigido; código e testes mostram o observado.
  Divergências exigem reconciliação explícita com a solicitação do operador e
  a referência funcional. Código existente não revoga regra de negócio.
- Antes de editar: classificar o pedido, ler os arquivos diretos e adjacentes
  integralmente e confirmar o entendimento. Pergunta, leitura e diagnóstico sem
  escrita não exigem aprovação adicional. Ordem explícita e inequívoca autoriza
  o escopo descrito; pedido exploratório, ambíguo ou que implique expansão
  material de escopo exige decisão do operador.
- Mudança visual acrescenta um passo: hierarquia, wireframe e estados são
  apresentados antes do código.
- Busca textual localiza, mas não substitui leitura integral: um `grep` que acha
  a linha não mostra a guarda três funções acima. Ler models, forms, services,
  selectors, views, URLs, templates, static e testes envolvidos.
- Context7 vem primeiro para biblioteca, framework, SDK, API ou CLI; depois, a
  documentação oficial da versão em uso. Toda PRD registra ao menos uma fonte
  relevante, a conclusão e as limitações. Limitação de ferramenta é registrada,
  nunca preenchida por suposição.

### Onde os contratos vivem

Os contratos de ciclo, PRD, UI, fluxos, banco, deploy, performance, teste manual
e plataforma **não estão no repositório**: são notas do vault Obsidian em
`C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\`, cujo índice é
`lvjiujitsu.md`.

| Responsabilidade | Dono único |
|---|---|
| Protocolo comum | `AGENTS.md` |
| Fatos do produto, stack, ambientes e portas | `CLAUDE.md` |
| Índice da documentação | `obsidian/projetos/lvjiujitsu/lvjiujitsu.md` |
| Ciclo detalhado de execução | `obsidian/projetos/lvjiujitsu/ciclo-execucao-lvjiujitsu.md` |
| Formato e numeração de PRD | `obsidian/projetos/lvjiujitsu/padrao-prd-lvjiujitsu.md` |
| Contrato visual, estados e evidência | `obsidian/projetos/lvjiujitsu/contrato-ui-lvjiujitsu.md` |
| Fluxos de tela | `obsidian/projetos/lvjiujitsu/fluxos-tela-lvjiujitsu.md` |
| Banco, migrations e seeds | `obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md` |
| Deploy Render e Supabase | `obsidian/projetos/lvjiujitsu/deploy-render-supabase-lvjiujitsu.md` |
| Teto da plataforma e orçamento de carga | `obsidian/projetos/lvjiujitsu/performance-plataforma-lvjiujitsu.md` |
| Roteiro de preenchimento para teste manual | `obsidian/projetos/lvjiujitsu/guia-teste-cliente-lvjiujitsu.md` |
| Diferenças por ferramenta | `obsidian/projetos/lvjiujitsu/plataformas-agente-lvjiujitsu.md` |
| Conhecimento do produto | `obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md` |
| Runbook operacional dos três ambientes | `obsidian/projetos/lvjiujitsu/comandos-powershell-lvjiujitsu.md` |
| Regra de negócio do produto | `obsidian/projetos/lvjiujitsu/regras-negocio-lvjiujitsu.md` |
| Índice e próximo número de PRD | `docs/prd/README.md` |
| Comportamento da mudança | PRD correspondente |
| Comportamento real | código, testes e execução observável |

O vault é lido durante a implementação. Escrever nele só quando a mudança tornar
uma nota factualmente incorreta, e a nota corrigida não entra no Pull Request.

## Idioma

- Código, nomes técnicos, arquivos, classes e funções: inglês.
- Interface, mensagens, commits e respostas: português pt-BR, com acentuação
  correta. PRDs seguem o idioma inglês definido pelo padrão do vault.
- Informar entendimento, escopo, validação, limitações e próxima decisão.
- Não repetir ao operador o que ele acabou de dizer, nem pedir confirmação do
  que já foi ordenado.
- Não expor raciocínio interno. Informar conclusões, premissas e evidências
  verificáveis.

## Quatro agentes autônomos, um escritor por vez

| Agente | Definição | Owner | Assunto |
|---|---|---|---|
| Codex | `.codex/agents/lvjiujitsu-agent-developer.toml` | `codex` | código inteiro |
| Claude Code | `.claude/agents/lvjiujitsu-agent-developer.md` | `claude` | código inteiro |
| Visual | `.claude/agents/lvjiujitsu-agent-visual.md` | `visual` | interface |
| Clean Code | `.claude/agents/lvjiujitsu-agent-clean-code.md` | `clean` | higiene do código |

- Os dois agentes de código executam a mesma skill de ciclo autônomo. O visual
  executa a skill de auditoria visual e o Clean Code a de higiene. Os quatro
  escrevem no mesmo branch `developer`.
- **Cada trilha tem lease próprio, no seu próprio checkpoint.** Se o lease da
  trilha estiver ocupado, encerrar imediatamente sem escrita e retomar na
  próxima execução — isso é esperado, não é falha.
- **O lease vale por prova de vida, não por relógio.** Todo comando de estado
  carimba um `heartbeat`; a trilha que para de carimbar libera o lease.
- **Número de PRD é reservado, não escolhido.** Com as trilhas em paralelo, o
  número vem de reserva explícita, e o índice canônico continua sendo
  `docs/prd/README.md`.
- Nenhum agente delega, cria subagentes ou executa duas correções em paralelo
  dentro do próprio ciclo.
- O fluxo detalhado, os scripts fechados e as referências pertencem à skill;
  este arquivo não os duplica.
- O estado de execução e os worktrees vivem fora do controle de versão.

## Skills

| Demanda | Skill | Onde |
|---|---|---|
| Ciclo autônomo de auditoria e correção | `lvjiujitsu-autonomous-developer` | `.agents/skills/` |
| Auditoria visual rota por rota | `lvjiujitsu-visual-auditor` | `.agents/skills/` |
| Varredura de comentário, hardcode e idioma | `lvjiujitsu-clean-code` | `.agents/skills/` |
| Recriar HG ou produção | `lvjiujitsu-remote-refresh` | `.claude/skills/` |

As três skills de ciclo são **canônicas em `.agents/skills/`**, com as
referências, os scripts fechados e os testes de contrato que o CI executa.
`.claude/skills/` guarda um adaptador fino de cada uma, que aponta para o
arquivo canônico e declara só o que é específico do Claude Code.

`lvjiujitsu-remote-refresh` é de invocação manual (`disable-model-invocation`) e
vive somente em `.claude/skills/`: toca ambiente remoto e nunca é acionada como
parte automática de outra entrega.

Skills manuais usam `Quando acionar` / `Passos` / `Saída` / `Parar quando`.
Skills de ciclo mantêm resultado, leituras, ferramentas, ciclo, cobertura,
PRDs, falhas e saída; adaptadores apontam para esse contrato canônico.

Este contrato vale para toda mudança e não é reempacotado em skill. Skill que
apenas reescreve o que já está aqui duplica contrato.

## Branches

- O operador trabalha em `stage`. `push` nela dispara o Auto-Deploy do Render.
- O agente trabalha em uma única `feature/prd-<número>-<slug>` isolada, criada
  apenas quando há defeito a corrigir, e publica somente em `developer`.
- O agente abre ou atualiza o Pull Request `developer -> stage`; somente o
  operador faz o merge.
- Nenhum agente faz merge ou push em `stage` ou `main`, force push, reescrita de
  histórico remoto ou operação de produção. `main` recebe apenas promoção
  manual.
- Commit e `git push` não são feitos por agente sem ordem explícita do operador.

## Banco, migrations e seeds

O contrato completo é
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md`. As guardas ficam
aqui de propósito, para sobreviverem a quem não alcança o vault.

- Reset, migrations, testes e ORM **locais** necessários ao escopo são
  autorizados sem perguntar. Testes Django usam banco isolado e não tocam o
  SQLite local.
- Enquanto os ambientes forem descartáveis, cada app admite no máximo uma
  migration vigente, `<app>/migrations/0001_initial.py`, e o checkout atual não
  versiona nenhuma. Mudança de schema termina com o ciclo destrutivo local e uma
  `0001_initial` consistente por app — nunca com uma `0002`.
- `clear_migrations.py` recusa qualquer ambiente que não seja inequivocamente
  local: arquivo de ambiente fora da raiz ou do compartilhado autorizado, `.env.hg`, `.env.prod`,
  `DJANGO_ENVIRONMENT` remoto, `DATABASE_URL` preenchida ou variável de seed
  ausente. Em toda recusa, nada é apagado.
- Dado de negócio nunca entra por migration. Produção usa seed explícita;
  homologação pode ser reconstruída pelo Build Command aprovado.
- Ação destrutiva no Supabase exige ambiente correto, `DEBUG=False`, host
  oficial, conexão PostgreSQL, `SUPABASE_PROJECT_REF` conferido,
  `SUPABASE_RESET_CONFIRM` e `--execute` em HG e produção. Sem a flag,
  o comando simula. Produção exige também `--confirm-ref`.
- **Limpeza remota exige perguntar ao operador antes**, em HG e em produção,
  mesmo com a tarefa já autorizada de forma geral, salvo autorização explícita
  já registrada na mesma conversa.
- **Antes de qualquer checagem contra `hg` ou `prod`, rodar
  `manage.py check_environment_parity`.** Falha dele é bloqueio: auditar
  ambiente remoto com env incompleta produz diagnóstico falso.
- `.env` pode ser usado em execução local descartável; `.env.hg` somente em
  auditoria read-only. Valores nunca são impressos, e arquivo de ambiente nunca
  é copiado para worktree, log, PRD ou Pull Request.

## Critério de conclusão

- Toda mudança relevante tem PRD numerada em `docs/prd/PRD-<NNN>-<slug>.md`,
  aprovada e atualizada **durante** a execução, não depois. O número vem de
  `docs/prd/README.md`, não de `ls` — a listagem não revela gaps reservados nem
  duplicatas. Ao criar ou fechar uma PRD, o índice é atualizado no mesmo passo,
  sem reaproveitar número.
- A PRD declara skills, critérios verificáveis, testes, evidências, desvios,
  limpeza, pendências e status. Critério só é marcado com evidência real;
  inferência não fecha critério, e checkbox permanece desmarcado até existir
  evidência.
- **TDD.** Escrever ou ajustar primeiro o teste quando houver comportamento
  testável: observar o Red, implementar o mínimo, observar o Green, refatorar
  com a suíte verde. Não declarar Red, Green ou ausência de regressão sem saída
  real de comando. Quando não houver comportamento testável, dizer isso na PRD
  em vez de inventar um teste que não prova nada.
- **Validação por tipo de mudança.** UI, template, CSS ou JS: browser real,
  desktop e mobile, os dois temas, fluxo, edge case, console e screenshot, no
  ato da implementação. Django: `check`, teste focado e suíte proporcional.
  Persistência: `makemigrations --check --dry-run` e `showmigrations`.
  Configuração: parser ou comando oficial, nunca leitura a olho. PRD e índice:
  número e status conferidos em `docs/prd/README.md`. Documentação: links
  verificados em disco.
- **Django MVT.** `models/` persistência e invariantes; `forms/` validação de
  entrada; `services/` regra de negócio e escrita transacional; `selectors/`
  leitura reutilizável e query otimizada; `views/` HTTP fino; `templates/`
  apresentação; `static/` CSS e JS por fluxo; `tests/` contrato por camada.
  Evitar N+1 e query dentro de laço; carregar relações com `select_related` e
  `prefetch_related` onde forem usadas. Operação que altera mais de um registro
  relacionado roda em `transaction.atomic`.
- **O orçamento de carga é critério, não conselho.** O projeto roda em 512 MB e
  0.1 CPU, sem shell, sem cron e sem worker. Rota de lista e de relatório fecha
  com contagem de query constante em relação ao volume de dado. Query dentro de
  laço sobre linhas, agregação em Python no lugar de `GROUP BY`, busca linear em
  coluna de texto, coleção inteira materializada em memória e chamada de rede
  sem orçamento dentro do request são proibidos. Lentidão é aceitável; trabalho
  ilimitado dentro de um request não.
- **Clean code.** Menor mudança correta, causa raiz, guard clauses, funções
  pequenas, nomes claros, no máximo dois níveis de condição e configuração
  explícita. Proibido: segredo hardcoded, erro mascarado, exceção engolida sem
  tratamento, query em loop, `innerHTML` com dado do usuário, regra central de
  negócio em template ou JavaScript, edição de `staticfiles/`.
- **Código não tem comentário nem docstring**, em `.py`, `.html`, `.css` e
  `.js`. Nome, assinatura e teste dizem o que o código faz; o porquê vive na
  PRD. As exceções são `migrations/`, gerado por ferramenta, e o comentário
  de seção em `settings.py` e `urls.py`, que marca onde a base técnica
  termina e começa a regra de negócio do produto. Docstring continua
  proibida também nesses dois arquivos.
- CSRF, validação server-side e permissão são resolvidos no backend. Segredo
  nunca é impresso, mesmo descartável: reportar nome de chave, não valor.
- **A interface é do produto, nunca do navegador.** Lista de valores, sugestão,
  confirmação e aviso são HTML, CSS e JavaScript deste projeto, com os tokens do
  tema. `<datalist>`, `alert`, `confirm`, `prompt` e qualquer widget desenhado
  pelo agente de usuário estão proibidos; a exceção é o que só o dispositivo
  entrega, como teclado virtual e seletor de arquivo. Componente equivalente já
  existente é reaproveitado.
- **Limpeza.** Revisar o diff inteiro e os contratos adjacentes; remover
  resíduos introduzidos; procurar legado, duplicação, hardcode, órfão e risco no
  escopo; corrigir documentação que a mudança tornou obsoleta.
- Dívida fora do escopo vira PRD de follow-up com número reservado, nunca
  implementação silenciosa. Ampliar escopo sem registro é tão ruim quanto deixar
  a dívida.
- `Pending` material, PRD bloqueada, gate incompleto ou CI ausente impedem
  conclusão e Pull Request Ready. Interrupção externa preserva o checkpoint.
- "Implementado" não significa "validado". Sem execução observável, o item vai
  para `Pending`, não para `Evidence`.
- O fechamento informa implementado, evidências com saída real, o que não foi
  validado, pendências, desvios e status: **concluída**, **concluída com
  limitações** ou **não concluída**. Concluída com limitações exige dizer qual
  limitação e por quê. Parte bloqueada não torna o resto incompleto.

## Execução agendada

Os quatro agentes rodam uma vez por dia, em sequência, com três horas entre um e
outro para que uma execução longa não faça o seguinte encontrar o lease ocupado
e perder o dia inteiro:

| Horário | Agente | Owner | Acionamento |
|---|---|---|---|
| 01h | Codex | `codex` | tarefa do Codex Desktop |
| 04h | Claude Code, código | `claude` | tarefa do Claude Code Desktop |
| 07h | Claude Code, visual | `visual` | tarefa do Claude Code Desktop |
| 10h | Claude Code, limpeza | `clean` | tarefa do Claude Code Desktop |

A ordem é deliberada: o Codex publica primeiro, o agente de código do Claude o
encontra publicado e pode revisá-lo no mesmo dia, o visual roda em seguida sobre
o resultado dos dois, e o de limpeza roda por último, sobre o resultado dos três
anteriores.

Todas as definições de agendamento vivem fora do Git, cada uma no aplicativo que
a executa.

## Base técnica e regra de negócio

A base técnica deste repositório — arquivos de plataforma, ferramentas de ciclo e
suas ordens — é estável: nome relativo, sequência e comportamento não mudam por
conveniência de uma entrega.

A fronteira entre base técnica e produto tem duas formas. Para módulo Python,
template e asset, a fronteira é **diretório**: `system/core/`,
`templates/core/` e `static/system/` são base; `system/business_rule/`,
`templates/business_rule/` e `static/business_rule/` são produto. `system/core/`
nunca importa `system/business_rule/`; o caminho contrário é o único permitido, e
o produto se liga ao núcleo por registro explícito em `BusinessRuleConfig.ready()`.

Para o artefato achatado, que não comporta diretório — `settings.py`,
`urls.py` do pacote, `wsgi.py`, `asgi.py`, `manage.py`, `system/urls.py`,
`clear_migrations.py`, `requirements.txt`, `.env.example` e
`.github/workflows/ci.yml` — o que é próprio do produto vem ao final do
arquivo, marcado como `BN - business rule`, com consumidor e justificativa em
`obsidian/projetos/lvjiujitsu/conhecimento-lvjiujitsu.md`.

`/reset-local` e o hook `Stop` são desta base; o hook só verifica e nunca aplica
correções. `.claude/settings.local.json` é configuração pessoal, ignorada pelo Git, e não
integra o contrato deste repositório.
