# UI e navegador

Para cada rota ou estado visual afetado:

1. iniciar o servidor com ambiente local descartável;
2. usar o navegador interno;
3. testar desktop `1440x900` e mobile `390x844`;
4. testar temas claro e escuro;
5. percorrer todos os botões, links, formulários e estados da superfície;
6. validar caminho feliz, vazio, inválido, erro, carregamento e permissão;
7. inspecionar console e terminal;
8. capturar screenshot somente depois de interagir;
9. comparar screenshot com DOM, estado e resultado esperado.

Antes de testar, registrar `state.py ui-require --prd <escopo>`. Quando a auditoria global encontrar UI sem PRD de defeito, usar o escopo `global`. Depois de cada combinação, registrar `state.py ui-evidence` com rota, viewport, tema, estados exercitados, screenshot PNG dentro do diretório de evidências retornado pelo estado e contagens zero de erros de console e terminal.

A matriz mínima obrigatória contém desktop/claro, desktop/escuro, mobile/claro e mobile/escuro. Em conjunto, as evidências precisam cobrir `happy`, `invalid`, `error` e `permission`. `assert-ready`, resolução da PRD e `complete-cycle` recusam matriz incompleta.

## Quando o screenshot é impossível

A captura depende de o painel do navegador estar visível na janela do aplicativo. Execução agendada não tem quem o exiba e falha com "the Browser pane is not displayed, so the page is not compositing frames". Nesse caso, e somente nele, `state.py ui-evidence` aceita `--dom-report` no lugar de `--screenshot`.

O relatório é um JSON dentro do diretório de evidências contendo a falha exata do screenshot em `screenshot_error`, a `url` inspecionada, o `theme` aplicado, o `viewport_width` real e ao menos três entradas em `assertions`, cada uma com `selector`, `property`, `observed` e `expected`. O script recusa relatório sem a falha registrada, com tema divergente, com largura incompatível com o viewport declarado ou com menos de três constatações. Navegar e ler o DOM continua obrigatório: o relatório substitui o pixel, não a interação.

Toda PRD validada assim fica marcada com `visual_confirmation_pending`, o Pull Request precisa declarar isso no corpo, e a conferência visual final cabe ao operador no momento do merge.

Usar `.env` e banco local descartável para validar a feature. Criar autenticação e dados locais temporários quando necessário e removê-los ao terminar. Usar `.env.hg` em modo read-only quando a auditoria depender do ambiente implantado. Falta de sessão pronta, screenshot, console ou credencial local não autoriza substituir navegador por leitura de HTML.

Verificar foco, teclado, rótulos, contraste, mensagens, feedback, overflow, toque, hierarquia, consistência e responsividade. Screenshot isolada não comprova funcionamento.

Quando a mudança e a baseline auditada não tocarem UI, registrar que o gate visual não se aplica e justificar.

## Interface do produto

A interface é do produto, nunca do navegador: lista de valores, sugestão,
confirmação e aviso são HTML, CSS e JavaScript deste projeto, com os tokens do
tema. `<datalist>`, `alert`, `confirm`, `prompt` e qualquer widget desenhado
pelo agente de usuário estão proibidos; a exceção é o que só o dispositivo
entrega, como teclado virtual, seletor de arquivo e comportamento nativo de
campo no celular. Componente equivalente já existente no produto é
reaproveitado em vez de reinventado.
