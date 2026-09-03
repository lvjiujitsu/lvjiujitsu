---
name: lvjiujitsu-visual-auditor
description: Executa o ciclo do agente visual do LV JIU JITSU. Usar para auditar toda a superfície de interface — CSS, HTML e JavaScript — rota por rota em desktop e mobile, tema claro e escuro, exercitando cada elemento interativo, medindo responsividade, rolagem, contraste e alvo de toque pelo navegador interno, abrindo uma PRD por defeito visual, corrigindo o lote em uma única feature e entregando o Pull Request de developer para stage sem fazer merge.
---

# Resultado

Entregar `developer` com os defeitos visuais corrigidos e um Pull Request para
`stage`. Nunca alterar `stage`, `main` ou produção.

# Arquivos obrigatórios

Ler antes de agir:

1. `CLAUDE.md` integralmente;
2. [checklist-visual.md](references/checklist-visual.md);
3. [sonda.md](references/sonda.md);
4. `C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\contrato-ui-lvjiujitsu.md`;
5. de `.agents/skills/lvjiujitsu-autonomous-developer/references/`:
   [git-worktree.md](../lvjiujitsu-autonomous-developer/references/git-worktree.md)
   e [quality-gates.md](../lvjiujitsu-autonomous-developer/references/quality-gates.md).

# Ferramentas fechadas

- `scripts/visual_state.py` para lease próprio, inventário de rotas, sondagem,
  achados e retomada;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py` **somente**
  para `prd-reserve --owner visual`, que entrega números de PRD sem colisão;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/git_flow.py` para
  sincronização, worktree, publicação, PR e limpeza;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py` para
  resíduos e integridade do diff.

O lease desta trilha é privado e vive no próprio checkpoint: o que ocorre nas
trilhas de código e de limpeza não bloqueia esta. Ele vale por prova de vida, e
uma execução que trava perde a chave depois de quarenta e cinco minutos sem
carimbar `heartbeat`, de modo que a execução seguinte retoma o lote registrado.

# Ciclo

1. Adquirir o lease da trilha com `visual_state.py acquire --owner visual`.
2. Ler `visual_state.py summary` e decidir entre herdar e começar. Há trabalho a
   preservar quando o worktree registrado existe e ao menos uma destas vale:
   commit ausente de `origin/developer`, worktree sujo, ou achado fora de
   `resolved`. Nesse caso herdar, sem `prepare`: `git_flow.py commit` primeiro,
   para tirar do limbo o que estiver solto, e `git_flow.py refresh` depois.
   Terminar o lote herdado antes de abrir rodada nova; ele é do ciclo, não de
   quem o começou. Só limpar com `cleanup` quando as três condições falharem.
3. Levar `developer` à paridade com `stage` por `git_flow.py sync --execute`,
   que não cria feature nem worktree.
4. Derivar o inventário de rotas de `system/urls.py`, resolvendo cada nome com
   `reverse` e os argumentos de um registro real semeado, e gravá-lo com
   `visual_state.py init`. Rota que exige sessão recebe `access: staff`.
5. Subir o servidor local a partir do worktree quando ele existir, ou da raiz
   quando ainda não houver feature, com ambiente descartável e porta livre.
6. Para cada rota pendente, nas quatro combinações de viewport e tema: aplicar o
   checklist, exercitar todo elemento interativo, rodar a sonda, completar o
   relatório e registrar com `visual_state.py probe`.
7. Criar uma PRD própria para cada defeito objetivo. Medição problemática sem
   PRD é recusada pelo script.
8. Congelar o lote. Somente aqui, e somente havendo defeito, abrir a única
   feature e worktree com `git_flow.py prepare`.
9. Corrigir, e ressondar nas quatro combinações toda rota afetada e toda rota
   que consuma o arquivo alterado.
10. Executar `visual_state.py complete-visual`, os gates de `quality-gates.md` e
    a auditoria do próprio diff.
11. `git_flow.py refresh`, `visual_state.py assert-ready`, publicar em
    `developer` por CAS, comprovar integração e limpar feature e worktree.
12. `git_flow.py pull-request` com o SHA validado; sem commits exclusivos,
    aceitar `no_changes` e não criar PR.
13. `visual_state.py complete-cycle` e liberar o lease.

# Cobertura

Cada rodada sonda o inventário inteiro. `visual_state.py init` devolve todas as
rotas a pendente quando a rodada anterior tiver encerrado de verdade ou quando a
baseline mudar. Rota sem achado numa rodada não fica dispensada na seguinte.

Rota só conta como coberta com as quatro combinações registradas. O script
recusa sondagem com viewport incompatível, tema divergente, interativos não
exercitados por completo ou defeito medido sem achado.

# Interface do produto, nunca do navegador

Lista de valores, sugestão, confirmação e aviso são HTML, CSS e JavaScript deste
projeto, com os tokens do tema. `<datalist>`, `alert`, `confirm`, `prompt` e
qualquer widget desenhado pelo agente de usuário são defeito visual e viram PRD:
ignoram tema, idioma, layout e largura de tela. A única exceção é o que só o
dispositivo entrega — teclado virtual por `inputmode`, seletor de arquivo e
comportamento nativo de campo no celular. Quando já existir componente
equivalente no produto, ele é reaproveitado em vez de reinventado.

# PRDs

Seguir `padrao-prd-lvjiujitsu.md` do vault e a numeração já existente em
`docs/prd/`, sem
reaproveitar número. Cada PRD registra a rota, o viewport, o tema, a medição que
comprova o defeito, o comportamento esperado e a evidência depois da correção.

# Falhas

- Lease ocupado encerra sem escrita e sem alterar o checkpoint.
- Servidor local indisponível interrompe a execução; preservar checkpoint e
  retomar na recorrência seguinte.
- Screenshot indisponível não impede o ciclo: a auditoria é por medição. Quando
  o painel estiver visível, capturar imagem é reforço, nunca substituto.
- Gate falho impede publicação e Ready.

# Saída

Informar lease, baseline, rotas cobertas e pendentes, combinações sondadas,
defeitos medidos por categoria, PRDs criadas e resolvidas, gates, SHA publicado,
URL do Pull Request, limpeza e pendências.
