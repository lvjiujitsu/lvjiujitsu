# Git e worktree

Usar exclusivamente `scripts/git_flow.py` nas mutações Git do ciclo.

## Invariantes

- `stage` pertence ao operador.
- `developer` recebe exclusivamente a integração validada do agente.
- A feature é local e temporária, nomeada `feature/prd-<número>-<slug>` com o menor número de PRD do lote e um slug curto em minúsculas, seguindo a convenção já usada no histórico do projeto. `git_flow.py` recusa qualquer outro formato.
- O worktree vive em `.agents-runtime/worktrees/`, diretório neutro compartilhado pelos dois agentes.
- O checkout do operador nunca é limpo, stashado, resetado ou trocado pelo agente.
- Nenhum comando usa force push.
- No máximo um Pull Request `developer` para `stage` permanece aberto.

## Sincronização

`git_flow.py sync` leva `developer` à paridade com `stage` por avanço rápido, sem criar feature nem worktree, e é o primeiro passo de toda rodada. Ele recusa o avanço quando `developer` tem commit ausente de `stage`; nesse caso a reconciliação passa pelo worktree da feature, que incorpora `origin/stage` sobre `origin/developer` e publica por comparação do SHA remoto. Se houver divergência, deixar o worktree preservado para resolução; nunca descartar um lado.

## Quando a feature nasce

A auditoria é leitura e não precisa de worktree. A única feature do ciclo só é criada depois que o lote de PRDs estiver congelado, isto é, quando existir defeito objetivo a corrigir. Rodada que percorre o inventário inteiro sem achado termina na auditoria, sem feature, sem worktree e sem Pull Request. Criar o par antes de haver correção deixa branch e diretório ocupados sem conteúdo e obriga a limpá-los ao final por nada.

`git_flow.py prepare` só cria: ele recusa branch e worktree já existentes. O checkpoint da auditoria vive no diretório Git comum e sobrevive à remoção do worktree, mas o worktree pode guardar trabalho que ainda não virou commit.

Por isso o teste para apagar não é "tem commit?", e sim "tem trabalho a preservar?". Há trabalho a preservar quando a feature tem commit ausente de `origin/developer`, **ou** o worktree está sujo, **ou** o checkpoint tem PRD fora de `resolved`. Em qualquer desses casos o par é herdado, nunca apagado: `git_flow.py commit` primeiro, para tirar do limbo o que estiver solto, e `git_flow.py refresh` em seguida.

Só se limpa quando as três condições falham ao mesmo tempo. `git_flow.py cleanup` recusa worktree sujo, o que é a última linha de defesa e não substitui a decisão correta. Nunca use `git checkout -- .` nem `git clean` para tornar um worktree "limpo" o bastante para apagar: isso destrói trabalho que ninguém mais tem.

O worktree não contém arquivos ignorados. Derivar a raiz principal pelo diretório Git comum e usar a `.venv` e o `.env` locais da raiz sem copiá-los para a feature.

## Publicação

Buscar novamente o remoto antes de publicar. Se o SHA de `origin/developer` diferir do esperado, reconciliar, repetir auditoria e gates e tentar novamente sem sobrescrever.

Executar `git_flow.py refresh` antes dos gates finais. `git_flow.py publish` recusa qualquer SHA que não contenha os `origin/stage` e `origin/developer` atuais.

## Limpeza

Remover worktree e feature somente quando o worktree estiver limpo, o HEAD for o SHA informado e esse SHA for ancestral de `origin/developer`. A limpeza não depende do merge em `stage`.

O agente cria ou atualiza o Pull Request e encerra. Somente o operador faz o merge em `stage`.

Se `origin/developer` não tiver commit exclusivo sobre `origin/stage`, `git_flow.py pull-request` retorna `no_changes`, não consulta o GitHub e o ciclo termina normalmente após `complete-cycle` e release. Nunca criar PR vazio.

Com diferença, o Pull Request nasce ou permanece draft. `git_flow.py pull-request --ready --head <SHA>` aguarda `quality-gates=SUCCESS` no mesmo SHA; check ausente, falho, obsoleto ou em timeout impede Ready.
