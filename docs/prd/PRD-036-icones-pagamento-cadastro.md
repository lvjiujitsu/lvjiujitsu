# PRD-036: Icones de Pagamento no Cadastro

## Resumo do que será implementado
Adicionar identificacao visual para PIX e Cartao na etapa de escolha de plano do cadastro.

## Tipo de demanda
Correcao pontual de UI

## Problema atual
O filtro "Forma de pagamento" exibe apenas texto, deixando a etapa menos clara visualmente.

## Objetivo
Exibir logo do PIX e bandeiras Visa/Mastercard no filtro de forma de pagamento.

## Context Ledger
### Arquivos lidos integralmente
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `static/system/img/icons/pix.svg`
- `static/system/img/icons/credit-card.svg`

### Arquivos adjacentes consultados
- Evidencia visual enviada pelo usuario no browser em `http://localhost:8000/register/`.

### Internet / documentação oficial
- Nao aplicavel.

### MCPs / ferramentas verificadas
- Browser skill — carregado para validacao visual no navegador.
- PowerShell — leitura e edicao local.

### Limitações encontradas
- Nao havia assets locais de Visa/Mastercard; foram criados SVGs simples em `static/system/img/icons/`.

## Prompt de execução
### Persona
Agente de desenvolvimento Django/frontend seguindo SDD e validacao visual.

### Ação
Adicionar logos aos filtros PIX e Cartao.

### Contexto
Os filtros sao renderizados dinamicamente em `register.js` e estilizados em `register.css`.

### Restrições
- sem alterar regra de negocio
- sem inline CSS
- manter acessibilidade com texto visivel e `alt=""` em imagens decorativas
- atualizar cache-busting do template

### Critérios de aceite
- [x] O botao PIX exibe o logo PIX.
- [x] O botao Cartao exibe bandeiras Mastercard e Visa.
- [x] Layout nao quebra em desktop.
- [x] `python manage.py check` passa.

### Evidências esperadas
- Validacao visual no browser.
- Check passando.

### Formato de saída
Resumo + evidencias.

## Escopo
- Assets SVG.
- JS de renderizacao dos filtros.
- CSS dos icones.
- Versao dos assets no template.

## Fora do escopo
- Alterar checkout.
- Alterar precos ou filtros de plano.
- Criar novos testes de UI enquanto as telas estao sendo reimplementadas.

## Arquivos impactados
- `static/system/img/icons/mastercard.svg`
- `static/system/img/icons/visa.svg`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `templates/login/register.html`

## Riscos e edge cases
- Icones precisam manter tamanho fixo para nao deslocar os filtros.

## Regras e restrições
- sem migracoes
- validacao visual obrigatoria
- CSS separado

## Plano
- [x] 1. Localizar renderizacao dos filtros.
- [x] 2. Adicionar assets.
- [x] 3. Renderizar icones.
- [x] 4. Ajustar CSS e cache-busting.
- [x] 5. Validar check e browser.

## Validação visual
Validado no browser em `http://localhost:8000/register/`; a etapa de plano exibiu 3 imagens carregadas: PIX, Mastercard e Visa.

## Validação ORM
Nao aplicavel.

## Validação de qualidade
### Sem hardcode
Paths estaticos seguem `STATIC_URL` exposto pelo template.

### Sem estruturas condicionais quebradiças
Mapeamento restrito a `pix` e `credit_card`.

### Sem `except: pass`
Nao introduzido.

### Sem mascaramento de erro
Nao aplicavel.

### Sem comentários e docstrings desnecessários
Nao introduzido.

## Evidências
- `python manage.py check`: sem issues.
- `python manage.py collectstatic --noinput`: 169 arquivos copiados.
- `python manage.py test`: 158 testes, OK.
- Browser: `#plan-filters-area .payment-method-icon` retornou 3 imagens carregadas com `complete=true`.
- Browser mobile 457x1280: 4 botoes de periodicidade na mesma linha, com badges em segunda linha; 2 botoes de pagamento visiveis com altura ampliada.

## Implementado
- Adicionados assets `mastercard.svg` e `visa.svg`.
- Botões de forma de pagamento agora renderizam logo PIX e bandeiras de cartão.
- CSS de tamanho/espacamento dos ícones adicionado.
- Cache-busting de `register.css` e `register.js` atualizado.
- Responsividade mobile dos filtros de plano ajustada para botoes maiores e melhor aproveitamento horizontal.

## Desvios do plano
Nenhum.

## Pendências
Nenhuma.
