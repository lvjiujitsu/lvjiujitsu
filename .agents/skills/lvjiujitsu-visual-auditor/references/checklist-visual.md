# Checklist visual

Rota só recebe sondagem registrada depois de todas as verificações abaixo terem
sido executadas naquele viewport e naquele tema. Olhar a tela não é auditar;
cada item exige um número, um seletor ou um comportamento observado.

A matriz obrigatória por rota é desktop 1440×900 e mobile 390×844, em tema claro
e escuro. Quatro combinações, sem exceção.

## 1. Antes de medir

1. Redimensionar o viewport e recarregar, para que regra de mídia e gate de
   dispositivo sejam reavaliados na carga.
2. Aplicar o tema pelo mesmo mecanismo do produto, não por preferência do
   sistema, e confirmar que o atributo de tema mudou no documento.
3. Limpar o console e só então interagir.

## 2. Interação — todo elemento, sem amostragem

1. Enumerar todo `a[href]`, `button`, `input`, `select`, `textarea`,
   `[role="button"]` e `[tabindex]` visível.
2. Acionar cada um e observar o resultado: navegação, envio, abertura de modal,
   alternância de estado ou ausência deliberada de efeito.
3. Botão que não faz nada, link com `href="#"` sem handler, controle que erra no
   console e formulário que não valida são achados.
4. `interactive_exercised` precisa igualar `interactive_total`. O script recusa
   sondagem parcial.
5. Modal e menu: abrir, fechar por botão, por `Esc` e por clique fora; conferir
   foco preso dentro do modal e devolvido ao gatilho ao fechar.

## 3. Responsividade

1. Overflow horizontal: `scrollWidth > clientWidth` no documento é achado, sem
   exceção. É o defeito mais comum em mobile.
2. Conteúdo cortado: texto com reticências não intencionais, imagem estourando o
   contêiner, tabela sem rolagem própria.
3. Quebra de layout entre 390px e 1440px: verificar também 768px quando a rota
   tiver grade de duas colunas.
4. Elemento fixo ou grudento cobrindo conteúdo ou o próprio rodapé em telas
   baixas.
5. Alvo de toque menor que 44×44 em mobile é achado, salvo quando fizer parte de
   um grupo com espaçamento suficiente, o que precisa ser justificado.

## 4. Rolagem

1. Conferir se a página rola quando deveria e não rola quando não deveria.
2. Contêiner com `overflow` que gera rolagem aninhada indesejada.
3. Rolagem travada com modal aberto e devolvida ao fechar.
4. Posição de rolagem preservada ou reiniciada de forma coerente após ação.

## 5. Contraste e legibilidade

1. Texto normal abaixo de 4.5:1 e texto grande abaixo de 3:1 são achados, medidos
   nos dois temas.
2. Estado de foco visível em todo elemento navegável por teclado.
3. Placeholder não substitui rótulo; campo sem rótulo associado é achado.
4. Mensagem de erro perceptível sem depender só de cor.

## 6. CSS

1. Cor cravada fora dos tokens de tema.
2. `!important` usado para vencer especificidade acidental.
3. Seletor sem correspondência no DOM das rotas auditadas, candidato a remoção
   depois de conferir todos os templates.
4. Regra duplicada ou sobrescrita imediatamente por outra.
5. Unidade fixa onde o layout precisa acompanhar o viewport.
6. Valor que existe no token e foi reescrito à mão.

## 7. JavaScript

1. Erro no console em qualquer momento da interação.
2. Listener adicionado sem remoção em componente recriado, comprovado por
   contagem antes e depois de repetir o ciclo de abrir e fechar.
3. Escrita em `innerHTML` com origem não rastreada.
4. Comportamento que só existe no cliente e não tem equivalente no servidor.

## 8. Correção

Defeito objetivo vira PRD própria, corrigido na mesma feature do ciclo, e a rota
afetada é sondada de novo depois da correção, nas quatro combinações. Correção
de CSS preserva os dois temas e não regride outra rota que use o mesmo seletor:
antes de fechar, ressondar toda rota que consuma o arquivo alterado.

Não abrir PRD para preferência estética, para escolha de layout que funciona ou
para diferença que só existe entre navegadores. Achado precisa ser mensurável e
reproduzível.
