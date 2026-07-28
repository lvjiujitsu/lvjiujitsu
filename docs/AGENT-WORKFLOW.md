# Fluxo operacional dos agentes

Procedimento detalhado do ciclo de trabalho no LV JIU JITSU. `AGENTS.md` diz o
que vale; este arquivo diz como executar. Fatos de produto vivem em
`CLAUDE.md`.

## 1. Ciclo de uma demanda

```text
Prompt
  -> classificação
  -> preflight
  -> leitura integral
  -> pesquisa oficial
  -> confirmação de entendimento
  -> autorização registrada pelo prompt
  -> PRD
  -> teste primeiro
  -> implementação
  -> validação proporcional
  -> auditoria de limpeza
  -> fechamento
```

Cada etapa tem entrada, saída e critério de passagem. Etapa sem saída
verificável não foi executada.

| Etapa | Entrada | Saída | Passa quando |
|---|---|---|---|
| Classificação | pedido do operador | tipo declarado | o tipo determina o resto do ciclo |
| Preflight | tipo | ambiente confirmado | os comandos da seção 3 rodaram |
| Leitura | escopo | arquivos lidos por inteiro | nenhum arquivo do fluxo ficou só grepado |
| Pesquisa | dúvida de biblioteca | fontes no Context Ledger | Context7 e doc oficial consultados |
| Entendimento | tudo acima | resumo e autorização | o operador confirmou ou já ordenou |
| PRD | entendimento | `docs/prd/PRD-<NNN>-*.md` | critérios são verificáveis |
| Teste | PRD | teste escrito e Red observado | a falha foi vista, não presumida |
| Implementação | teste Red | menor mudança correta | Green observado |
| Validação | implementação | evidência real | saída de comando colada |
| Limpeza | diff | resíduos removidos | contratos adjacentes revisados |
| Fechamento | tudo | PRD atualizada | status real declarado |

Perguntas e diagnósticos sem escrita encerram após contexto, análise e
evidência.

## 2. Classificação

Usar uma categoria principal:

- pergunta exploratória;
- diagnóstico;
- correção pontual;
- refatoração;
- nova feature;
- alteração arquitetural;
- integração externa;
- revisão de segurança;
- revisão de performance;
- revisão de governança;
- regeneração documental.

A classificação define arquivos adjacentes, PRD, validação e risco.

## 3. Preflight

Verificar apenas o necessário para a demanda:

- `AGENTS.md` e `CLAUDE.md` alinhados;
- worktree e alterações preexistentes;
- shell, `.venv` e interpretador;
- comandos reais;
- ferramentas exigidas;
- acesso à internet;
- viabilidade de browser, ORM e validação.

Mudanças preexistentes pertencem ao operador. Não revertê-las.

## 4. Leitura integral

Antes de diagnosticar ou editar:

1. identificar os arquivos diretamente envolvidos;
2. ler cada arquivo por inteiro;
3. ler contratos adjacentes;
4. registrar o ledger na PRD.

Em Django, considerar:

- models;
- forms;
- services;
- selectors;
- views;
- URLs;
- templates;
- CSS/JS;
- testes;
- settings;
- signals;
- tasks;
- management commands.

Busca textual serve para localizar, não para substituir leitura.

## 5. Pesquisa

### Ordem

1. Context7 para biblioteca, framework, SDK, API ou CLI.
2. Documentação oficial atual.
3. Fonte primária adicional quando necessária.

### Registro

Toda PRD contém:

- consulta realizada;
- links;
- conclusão aplicável;
- limitação ou divergência.

Toda PRD registra ao menos uma fonte oficial externa relevante. Pesquisa
irrelevante não aumenta qualidade. Se a ferramenta estiver indisponível,
registrar a limitação sem inventar referência.

## 6. Confirmação mínima

Antes de uma mudança ainda não autorizada pelo prompt, responder:

```text
Entendi: <resultado desejado>.
Escopo: <arquivos/fluxos>.
Validação: <browser, ORM local, checks e testes proporcionais>.
Posso implementar?
```

Não repetir o prompt. Expor premissas que possam alterar o resultado.

## 7. Gates de autorização

| Ação | Autorização |
|---|---|
| Leitura, pesquisa e diagnóstico | implícita |
| Escrita solicitada com escopo claro | solicitação atual |
| Expansão material de escopo | nova aprovação |
| Proposta de UI | leitura e elaboração permitidas |
| Implementação de UI | aprovação da proposta |
| Execução de testes locais | autorizada para entrega operacional solicitada |
| ORM read-only | permitida quando necessária |
| ORM mutável em qualquer ambiente descartável | autorizada quando necessária ao objetivo solicitado |
| Migration, migrate, reset ou seeds em local, HG ou prod | autorizados quando necessários ao objetivo solicitado; os três ambientes são descartáveis (ver `CLAUDE.md` §1) |
| Ação irreversível fora do repositório: `git push`, deploy externo, escrita em serviço de terceiro, envio de e-mail real | autorização explícita |

## 8. PRD e SDD

Criar PRD antes do código em mudança relevante.

A PRD é um documento vivo:

- começa com contexto e plano;
- recebe evidência durante a execução;
- marca critérios somente quando comprovados;
- registra testes escritos e status de execução;
- registra limitações sem mascará-las.

Usar `docs/PRD-STANDARD.md`. O número vem de `docs/prd/README.md`, e o índice é
regenerado por `python scripts/build_prd_index.py` no mesmo passo — o comando
recusa colisão de número.

## 9. TDD com execução local

### Ordem de autoria

1. escrever o teste do comportamento esperado;
2. implementar o mínimo;
3. refatorar.

### Execução

Executar testes locais proporcionais ao risco do escopo.

Sem execução real:

- não afirmar que o teste falha;
- não afirmar que passa;
- não afirmar ausência de regressão.

### Banco de testes

`django.test.TestCase` usa banco de teste isolado. Não limpar `db.sqlite3` para
executar testes.

O ciclo destrutivo mais seeds é usado apenas para:

- reconstrução deliberada do baseline de schema;
- validação operacional de primeira carga;
- auditoria de seeds em ambiente descartável.

## 10. Implementação Django

Ordem padrão:

1. contratos e invariantes;
2. forms;
3. services;
4. selectors;
5. views;
6. URLs;
7. templates;
8. static;
9. testes;
10. documentação.

Adaptar a ordem quando o menor patch correto exigir.

Views permanecem finas. Múltiplas escritas relacionadas usam transação.
Queries relacionadas devem ser verificadas contra N+1.

## 11. UI

### Antes do código

Produzir proposta curta:

- objetivo da tela;
- hierarquia;
- wireframe;
- estados;
- ações e permissões;
- desktop e mobile;
- preservação funcional.

Pedir aprovação.

### Após o código

Usar o navegador interno da ferramenta:

1. abrir a rota real na porta canônica;
2. validar caminho feliz;
3. validar ao menos um edge case;
4. inspecionar console e terminal;
5. validar desktop e mobile;
6. validar tema claro e escuro;
7. **auditar a renderização** (checklist abaixo);
8. registrar screenshot ou snapshot na PRD.

### Auditar a renderização — gate, não formalidade

Screenshot não é carimbo de aprovação: é material a ser auditado. "A tela
abriu" não é validação. Antes de declarar qualquer etapa concluída, verificar
explicitamente e relatar o resultado:

- **Layout**: elemento cortado no topo ou na base, dialog maior que a
  viewport, overflow horizontal, conteúdo inalcançável por rolagem.
- **Colisão**: rodapé fixo, botão de ação ou barra sobrepondo conteúdo de
  forma que impeça leitura ou clique.
- **Dados renderizados**: campo obrigatório vazio quando o dado já é conhecido
  pelo sistema; rótulo sem valor; select em `---------` onde havia contexto
  para pré-preencher.
- **Estado**: item selecionado que não parece selecionado, contador divergente
  da lista, badge sem correspondência.

Quando um defeito aparecer no próprio screenshot capturado pelo agente, ele é
**achado do agente** — não pode ser deixado para o operador encontrar.
Confirmar cada suspeita por medição (geometria via JS, computed style, valor do
campo) antes de afirmar que é ou não defeito; não declarar bug por impressão
visual nem descartar por conveniência.

Para rotas autenticadas, usar a superfície com sessão disponível. Não declarar
sucesso com base em navegador sem autenticação.

## 12. ORM

- Preferir checagem read-only.
- Registrar comando e resultado.
- Criar dados locais somente quando fizer parte do objetivo ou da validação.
- Não corrigir dados locais como efeito colateral silencioso.
- Qualquer escrita de recuperação deve ser idempotente, explícita e
  registrada.

## 13. Limpeza

Revisar somente o escopo e contratos adjacentes:

- código morto;
- imports e branches obsoletos;
- duplicação;
- hardcode;
- erro mascarado;
- template, rota ou asset órfão;
- comentário e docstring, que o §10 do `AGENTS.md` proíbe;
- documentação desatualizada;
- teste sem contrato real.

Corrigir o que pertence ao escopo. Para achado material fora do escopo:

1. criar PRD de follow-up;
2. descrever risco e evidência;
3. parar;
4. aguardar aprovação.

## 14. Fechamento

Formato mínimo:

```text
Implementado: ...
Evidências: ...
Não validado: ...
Pendências/desvios: ...
Status: concluída | concluída com limitações | não concluída
```

## 15. Slash commands

Três comandos em `.claude/commands/`, para o ciclo que se repete. Eles não
substituem as skills: executam uma sequência já decidida, e não introduzem
regra de governança nova.

| Comando | O que faz |
|---|---|
| `/reset-local` | ciclo destrutivo local até o servidor no ar; verifica as pré-condições antes de apagar o banco e recusa `.env.hg` e `.env.prod` |
| `/validar-tela <rota>` | valida uma rota em desktop e mobile, nos dois temas, com screenshot obrigatório |
| `/sync-skills` | compara as sete skills nas três plataformas e reporta divergência sem sobrescrever |

`/reset-local` destrói o ambiente local; sua invocação manual é a autorização
explícita para as seeds do ciclo.

Claude expõe os três como slash command. Codex e Cursor seguem o procedimento
equivalente deste workflow e do runbook — o conteúdo é o mesmo, muda apenas a
forma de acionar. `scripts/validate_skill_frontmatter.py` e
`scripts/build_prd_index.py --check` rodam em qualquer plataforma e são o que o
CI executa.
