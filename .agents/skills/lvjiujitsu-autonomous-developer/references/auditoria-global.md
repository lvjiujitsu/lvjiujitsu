# Auditoria global

## Ordem

Auditar o inventário rastreado pelo Git em ordem lexical, agrupando somente consumidores adjacentes necessários para compreender o arquivo atual.

1. raiz, configuração e dependências;
2. projeto Django e URLs;
3. models e migrations;
4. forms;
5. services;
6. selectors;
7. views;
8. commands e seeds;
9. templates;
10. CSS e JavaScript;
11. testes;
12. documentação operacional e estrutura.

## Evidência por arquivo

Antes de registrar, executar sobre o arquivo todas as verificações que
[checklist-auditoria.md](checklist-auditoria.md) exige para a sua
responsabilidade, mais as universais. Verificação não executada é arquivo não
auditado.

Registrar no checkpoint com os campos fechados de `state.py audit`:

- blob SHA auditado;
- `--responsibility` com a responsabilidade observada;
- `--consumers` somente com caminhos rastreados consultados;
- `--risks` somente com categorias aceitas pelo script;
- `--prds` somente com PRDs já registradas no ciclo;
- resultado `audited` somente após leitura integral.

Antes de `audit`, executar `state.py inspect` até `complete=true`. Cada chamada emite o próximo chunk do blob da baseline e registra offset, SHA-256, bytes, linhas e quantidade de chunks. O script recusa `audit` sem inspeção completa. Não registrar vários arquivos por inferência ou por uma busca que não emitiu seu conteúdo.

O checkpoint não aceita texto livre, valores de ambiente, URLs, credenciais ou trechos de código.

Para binários, registrar finalidade, duplicação, tamanho, localização e consumidores. Não interpretar bytes como código.

## Mudança durante a cobertura

Quando `stage` avançar antes de `global_complete`, incorporar a mudança em `developer`, atualizar a baseline e invalidar arquivos alterados, novos, removidos e consumidores afetados. Continuar a auditoria global; não criar prioridade separada para o diff.

Depois de `global_complete`, a rodada terminou. A rodada seguinte não audita apenas o diff: `state.py init` devolve todo o inventário a `pending` e a cobertura recomeça do zero, arquivo por arquivo, com o checklist inteiro. Não existe arquivo dispensado por ter sido auditado antes, e "sem achado na rodada anterior" nunca justifica leitura mais rasa — a rodada anterior pode ter deixado passar. Alteração de schema, dependência, URL, regra central ou estrutura continua exigindo atenção redobrada ao módulo relacionado dentro da rodada.

## Achado aceitável

Exigir evidência reproduzível ou demonstração estática completa. Não criar PRD por gosto pessoal, possibilidade abstrata ou refatoração sem benefício verificável.

Verificar comportamento incorreto, ausência de funcionalidade, segurança, autorização, persistência, desempenho medido, código morto comprovado, arquitetura, UX, acessibilidade, testes, configuração e documentação divergente.
