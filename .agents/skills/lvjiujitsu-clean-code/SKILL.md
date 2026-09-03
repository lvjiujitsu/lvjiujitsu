---
name: lvjiujitsu-clean-code
description: Executa o ciclo do agente de limpeza do LV Jiu Jitsu. Usar para varrer o repositório inteiro em busca de comentário e docstring, hardcode, mistura de idioma entre código em inglês e interface em português, e desvio de governança em nome de arquivo; abrir uma PRD por defeito, corrigir o lote em uma única feature e entregar o Pull Request de developer para stage sem fazer merge.
---

# Resultado

Entregar `developer` sem comentário, sem hardcode indevido, com código em inglês
e interface em português, e um Pull Request para `stage`. Nunca alterar `stage`,
`main` ou produção.

# Arquivos obrigatórios

Ler antes de agir:

1. `CLAUDE.md` integralmente;
2. [checklist-limpeza.md](references/checklist-limpeza.md);
3. `C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\padrao-prd-lvjiujitsu.md`;
4. de `.agents/skills/lvjiujitsu-autonomous-developer/references/`:
   [git-worktree.md](../lvjiujitsu-autonomous-developer/references/git-worktree.md)
   e [quality-gates.md](../lvjiujitsu-autonomous-developer/references/quality-gates.md).

# Ferramentas fechadas

- `scripts/clean_state.py` para lease próprio, inventário, varredura, revisão e
  retomada;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py` **somente**
  para `prd-reserve --owner clean`, que entrega números de PRD sem colisão;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/git_flow.py` para
  sincronização, worktree, publicação, PR e limpeza;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py` para
  conferir o diff antes de publicar.

O lease desta trilha é privado e vive no próprio checkpoint: o que ocorre nas
trilhas de código e visual não bloqueia esta. Ele vale por prova de vida, e uma
execução que trava perde a chave depois de quarenta e cinco minutos sem carimbar
`heartbeat`, de modo que a execução seguinte retoma o lote registrado.

# Ciclo

1. Adquirir o lease da trilha com `clean_state.py acquire --owner clean`.
2. Ler `clean_state.py summary` e decidir entre herdar e começar. Há trabalho a
   preservar quando o worktree registrado existe e ao menos uma destas vale:
   commit ausente de `origin/developer`, worktree sujo, ou achado fora de
   `resolved`. Nesse caso herdar, sem `prepare`: `git_flow.py commit` primeiro,
   para tirar do limbo o que estiver solto, e `git_flow.py refresh` depois.
   Terminar o lote herdado antes de abrir rodada nova; ele é do ciclo, não de
   quem o começou. Só limpar com `cleanup` quando as três condições falharem.
3. Levar `developer` à paridade com `stage` por `git_flow.py sync --execute`.
4. `clean_state.py init` no SHA sincronizado. O inventário cobre `.py`, `.js`,
   `.html`, `.css`, `.svg`, `.toml`, `.yml` e `.yaml` rastreados pelo Git, e
   guarda o blob de cada arquivo.
5. Para cada arquivo pendente, em ordem lexical: ler integralmente, rodar
   `clean_state.py scan --path <arquivo>`, aplicar os quatro eixos do checklist
   e registrar com `clean_state.py review`. Candidato do scanner exige PRD ou
   `--justified` cobrindo todos; o script recusa silêncio.
6. Criar uma PRD própria para cada defeito objetivo.
7. Congelar o lote. Somente aqui, e somente havendo defeito, abrir a única
   feature e worktree com `git_flow.py prepare`.
8. Corrigir. Remoção de comentário não muda comportamento; quando exigir
   renomear ou reestruturar, tratar como mudança de código, com teste focado.
9. `clean_state.py complete-clean`, gates de `quality-gates.md` e auditoria do
   próprio diff.
10. `git_flow.py refresh`, `clean_state.py assert-ready`, publicar em
    `developer` por CAS, comprovar integração e limpar feature e worktree.
11. `git_flow.py pull-request` com o SHA validado; sem commits exclusivos,
    aceitar `no_changes` e não criar PR.
12. `clean_state.py complete-cycle` e liberar o lease.

# Cobertura

Cada rodada revisa o inventário inteiro. `clean_state.py init` devolve todos os
arquivos a pendente quando a rodada anterior tiver encerrado de verdade. Dentro
de uma rodada inacabada, arquivo cujo blob não mudou permanece revisado e
arquivo alterado volta à fila, de modo que um avanço de `stage` no meio do ciclo
não obriga a recomeçar.

Arquivo sem achado numa rodada não fica dispensado na seguinte.

# PRDs

Seguir `padrao-prd-lvjiujitsu.md` do vault e a numeração existente em
`docs/prd/`, sem
reaproveitar número. Registrar arquivo, linha, eixo, o que estava e o que passou
a estar. Credencial literal é achado bloqueante e a PRD descreve a ocorrência
sem transcrever o valor.

# Falhas

- Lease ocupado encerra sem escrita e sem alterar o checkpoint.
- Gate falho impede publicação e Ready.
- Justificativa repetida para o mesmo padrão em muitos arquivos indica scanner
  desalinhado com a realidade do projeto: registrar PRD para corrigir o scanner
  em vez de justificar indefinidamente.

# Saída

Informar lease, baseline, arquivos revisados e pendentes, candidatos por eixo,
quantos viraram PRD e quantos foram justificados, PRDs criadas e resolvidas,
gates, SHA publicado, URL do Pull Request, limpeza e pendências.

- A interface é do produto, nunca do navegador: lista de valores, sugestão,
  confirmação e aviso são HTML, CSS e JavaScript deste projeto, com os tokens do
  tema. `<datalist>`, `alert`, `confirm`, `prompt` e qualquer widget desenhado
  pelo agente de usuário estão proibidos; a exceção é o que só o dispositivo
  entrega, como teclado virtual, seletor de arquivo e comportamento nativo de
  campo no celular. Componente equivalente já existente no produto é
  reaproveitado em vez de reinventado.
