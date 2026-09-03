---
name: lvjiujitsu-autonomous-developer
description: Executa o ciclo rigoroso do único agente autônomo do LV Jiu Jitsu. Usar para sincronizar stage em developer, retomar uma auditoria global comprovável arquivo por arquivo e linha por linha, auditar diffs somente após concluir a cobertura global, criar uma PRD por defeito, corrigir todas as PRDs do lote em uma única feature e worktree, validar Django, segurança e UI, publicar exclusivamente em developer e abrir ou atualizar o Pull Request para stage sem fazer merge.
---

# Resultado

Entregar `developer` sincronizada, corrigida e validada, com um único Pull Request para `stage`. Nunca alterar `stage`, `main` ou produção.

# Arquivos obrigatórios

Ler antes de agir:

1. `CLAUDE.md` integralmente;
2. [auditoria-global.md](references/auditoria-global.md);
3. [django-mvt.md](references/django-mvt.md);
4. [seguranca.md](references/seguranca.md);
5. [ui-browser.md](references/ui-browser.md);
6. [git-worktree.md](references/git-worktree.md);
7. [quality-gates.md](references/quality-gates.md);
8. [checklist-auditoria.md](references/checklist-auditoria.md).

# Ferramentas fechadas

Usar:

- `scripts/state.py` para lease, inventário, checkpoint, cobertura e retomada;
- `scripts/git_flow.py` para sincronização, worktree, publicação, PR e limpeza;
- `scripts/quality_scan.py` para comentários, docstrings, resíduos e integridade do diff.

Não substituir operações desses scripts por comandos Git improvisados.

# Ciclo

1. Adquirir lease exclusivo com `state.py acquire`.
2. Ler `state.py summary` e decidir entre herdar e começar. Existe trabalho a preservar quando o worktree registrado existe no disco e ao menos uma destas é verdadeira: a feature tem commit ausente de `origin/developer`, o worktree está sujo, ou o checkpoint tem PRD fora de `resolved`. Havendo trabalho a preservar, **herdar**: sem `prepare`, primeiro `git_flow.py commit` para tirar do limbo o que estiver solto no worktree, depois `git_flow.py refresh` para incorporar `stage`. Só limpar com `cleanup` quando o worktree estiver limpo, sem commit exclusivo e sem PRD aberta; nesse caso seguir sem worktree.
3. Levar `developer` à paridade com `stage` por `git_flow.py sync`, que faz o avanço rápido sem criar feature nem worktree. Se `developer` tiver commit ausente de `stage`, o comando recusa e a reconciliação exige o worktree da feature.
4. Inicializar ou atualizar o inventário no SHA sincronizado.
5. Usar `state.py inspect` repetidamente até emitir todos os chunks de cada texto e a inspeção estrutural de cada binário; somente depois aplicar o checklist da responsabilidade e registrar `state.py audit`. Continuar até todos os arquivos do inventário estarem comprovadamente concluídos. Não criar prioridade separada para o diff.
6. Cada rodada audita o inventário inteiro. `state.py init` recomeça a cobertura do zero quando a rodada anterior tiver encerrado de verdade, isto é, `global_complete` com feature e worktree nulos e nenhuma PRD fora de `resolved`. Enquanto houver lote pendente de publicação, a cobertura é preservada para que o lote possa fechar antes de a rodada nova começar. Nenhum arquivo entra na rodada nova já auditado, e arquivo sem achado numa rodada não fica dispensado na seguinte.
7. Criar uma PRD própria para cada defeito objetivo. Não criar PRD para este agente, para ausência de achado ou para preferência estética.
8. Congelar o conjunto de PRDs do ciclo. Somente aqui, e somente havendo defeito a corrigir, executar `git_flow.py prepare` para criar a única feature e worktree do ciclo e resolver todas as PRDs nela. Rodada sem achado nunca cria feature nem worktree: ela termina na auditoria.
9. Executar teste focado depois de cada correção e atualizar sua PRD com comando e saída reais. Mudança ou baseline visual exige `state.py ui-require` e a matriz completa de `state.py ui-evidence` produzida pelo navegador interno.
10. Executar todos os gates do lote e auditar integralmente o diff da feature.
11. Buscar o remoto novamente com `git_flow.py refresh`. Incorporar eventual avanço de `stage`, invalidar a evidência anterior e repetir a auditoria e os gates afetados.
12. Executar `state.py assert-ready` e publicar o SHA validado exclusivamente em `developer` por CAS.
13. Confirmar que o SHA está em `origin/developer`; somente então limpar feature e worktree.
14. Executar `git_flow.py pull-request` com o SHA validado. Sem commits exclusivos em `developer`, aceitar somente `state=no_changes` e não criar PR. Com diferença, criar ou atualizar draft, aguardar o check remoto `quality-gates` no SHA exato e somente então marcar Ready. Rodada que não abriu feature pula os passos 8 a 13 e chega aqui direto, com `no_changes`.
15. Executar `state.py complete-cycle` depois da limpeza e da promoção ou `no_changes`; conferir `idle`, feature e worktree nulos e SHA de stage registrado.
16. Liberar o lease.

# Lote herdado

O lote pode ter sido começado por outro agente da mesma trilha que perdeu a
sessão no meio do caminho. Terminá-lo é parte do seu trabalho, não uma exceção:
as PRDs abertas são do ciclo, não de quem as escreveu. Enquanto existir PRD fora
de `resolved`, `state.py init` preserva a cobertura e `assert-ready` recusa a
publicação, de modo que a rodada nova só começa depois que a anterior fechar.

Herdar significa, nesta ordem: commitar o que estiver solto no worktree para que
nada dependa de disco; incorporar o avanço de `stage`; ler cada PRD aberta;
implementar, testar e resolver todas; e só então seguir para a sua própria
auditoria. Nunca descartar PRD alheia por não a ter escrito, e nunca apagar
worktree com arquivo não commitado.

# PRDs

Usar o formato de `C:\Users\whsf\Documents\GitHub\obsidian\projetos\lvjiujitsu\padrao-prd-lvjiujitsu.md`. Nota inalcançável é limitação registrada, não licença para inventar o formato nem para recriar o arquivo em `docs/`. Começar em `PRD-001` quando `docs/prd/` não contiver PRD. Nunca reutilizar um número já existente no filesystem, no lote ou no checkpoint.

Cada PRD deve conter causa reproduzível, arquivos afetados, comportamento esperado, riscos, testes, gates aplicáveis, evidência e status. Um problema material corresponde a uma PRD; todas as PRDs do ciclo pertencem à mesma feature.

# Critério de cobertura

Arquivo só recebe `audited` depois que `state.py inspect` comprovar emissão sequencial de todo o blob rastreado, com SHA-256, bytes, linhas e chunks, seguida da leitura integral e da execução de todas as verificações que [checklist-auditoria.md](references/checklist-auditoria.md) exige para a responsabilidade daquele arquivo, mais as universais. Binário recebe metadados estruturais sem imprimir bytes. Teste verde, busca textual, ausência de erro visível ou leitura atenta sem verificação executada não comprovam auditoria.

Auditoria anterior sem achado não é credencial: o inventário recomeça a cada rodada e cada arquivo é reexaminado com o checklist inteiro, porque a rodada passada pode ter sido rasa.

Cobertura global só termina quando `state.py complete-global` aceitar o inventário sem item pendente ou invalidado.

# Pendências e ambientes

Defeito objetivo encontrado no ciclo deve possuir PRD, implementação, teste, auditoria e status `Resolvida` antes de `assert-ready`. Não publicar lote com PRD `found`, `blocked`, gate incompleto, evidência presumida ou seção `Pending` material.

Usar `.env` para execução local descartável. `.env.hg` está disponível para auditoria read-only de homologação quando o comportamento depender do ambiente implantado. Criar usuário e dados temporários somente no banco local; remover ao terminar. Ausência de sessão autenticada não é limitação: criar acesso local descartável ou usar a credencial já configurada sem imprimir valores. Nunca copiar arquivo de ambiente para worktree, log, PRD ou Pull Request.

Quota, rede ou autenticação externas podem interromper a execução, mas nunca transformam o ciclo em concluído: preservar checkpoint, manter o item aberto e exigir retomada na recorrência seguinte. Problema técnico reproduzível não pode ser adiado como limitação.

# Falhas

- Em quota, rede ou autenticação indisponível, salvar fase e encerrar como não concluído; a próxima recorrência retoma antes de iniciar novo ciclo.
- Cobertura global que não cabe em uma execução encerra sem PRD, correção, commit ou Pull Request, o que é o resultado correto enquanto `global_status` não for `global_complete`. A cobertura vive no checkpoint, não no worktree: sem commit exclusivo na feature, limpar feature e worktree com `git_flow.py cleanup` antes de liberar o lease.
- Renovar o lease antes do vencimento durante uma execução longa.
- Em conflito objetivo, resolver e repetir evidências.
- Em ambiguidade de negócio, registrar a decisão humana necessária, resolver todas as PRDs independentes e nunca marcar o lote Ready enquanto o bloqueio afetar seu comportamento.
- Em mudança de segredo, Render, `main` ou produção, informar exatamente a ação humana necessária sem registrar valores.
- Em falha de gate, não publicar o novo SHA em `developer` e não marcar o PR como pronto.

# Saída

Informar lease, baseline, cobertura, PRDs criadas e resolvidas, testes, gates, SHA publicado, URL do Pull Request, limpeza e pendências. Nunca declarar concluído sem evidência observável.

- A interface é do produto, nunca do navegador: lista de valores, sugestão,
  confirmação e aviso são HTML, CSS e JavaScript deste projeto, com os tokens do
  tema. `<datalist>`, `alert`, `confirm`, `prompt` e qualquer widget desenhado
  pelo agente de usuário estão proibidos; a exceção é o que só o dispositivo
  entrega, como teclado virtual, seletor de arquivo e comportamento nativo de
  campo no celular. Componente equivalente já existente no produto é
  reaproveitado em vez de reinventado.
