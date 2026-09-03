# Checklist de limpeza

Arquivo só recebe `review` depois que os quatro eixos abaixo forem examinados
nele. `clean_state.py scan` varre o arquivo por conta própria e o `review`
recusa o registro quando encontra candidato que o agente não transformou em PRD
nem justificou explicitamente. O scanner é o piso, não o teto: ele acha o
mecânico, e o julgamento continua sendo do agente.

## 1. Comentário e docstring

O projeto não usa comentário nem docstring em código. O nome e a estrutura
carregam a intenção; quando não carregam, o defeito é o nome ou a estrutura.

1. Remover todo comentário e docstring de `.py`, `.js`, `.html`, `.css`.
2. Cobrir também `.svg`, `.toml`, `.yml` e `.yaml`, que o gate de CI não olha.
3. Comentário que documenta uma decisão real não vira comentário melhor: vira
   PRD, entrada de documentação operacional ou nome mais claro.
4. Exceção legítima: diretiva exigida por ferramenta, como `# noqa` reconhecido
   por um linter em uso, ou cabeçalho obrigatório de formato. Justificar.

`quality_scan.py --all` já barra os quatro primeiros formatos no CI. Este eixo
é a segunda barreira e o único que cobre os demais formatos.

## 2. Hardcode

Valor que deveria vir de configuração, constante nomeada, token de tema ou do
banco, e está escrito no corpo do arquivo.

1. URL e host externos, inclusive CDN de fonte e de biblioteca. Repetição do
   mesmo endereço em vários templates é achado mesmo quando cada ocorrência
   parece inofensiva.
2. Caminho absoluto de sistema de arquivos.
3. E-mail, telefone e documento fora de teste.
4. Credencial, chave ou token literais, em qualquer arquivo. Achado bloqueante:
   registrar sem transcrever o valor.
5. Número mágico em regra de negócio, prazo, limite ou dimensão.
6. Cor, espaçamento e tipografia cravados fora dos tokens de tema.
7. Valores de domínio que já existem em `settings`, em `TextChoices` ou no banco.

Arquivo de teste é fixture: e-mail, senha e URL falsos ali são corretos e o
scanner não os reporta. Isso não autoriza credencial real em teste.

## 3. Idioma

A regra do projeto é código em inglês e tudo que o usuário lê em português.

1. Em inglês: nome de arquivo, módulo, pacote, classe, função, método,
   variável, argumento, campo de modelo, chave de contexto, nome de rota,
   nome de template e identificador em JavaScript e CSS.
2. Em português: texto de template, rótulo, placeholder, mensagem de erro e de
   sucesso, `verbose_name`, `help_text`, `label`, título de página e conteúdo de
   documentação de operação. PRDs seguem o padrão em inglês do vault.
3. Identificador com acento é sempre achado.
4. Identificador em português é achado; palavra inglesa que contém uma
   portuguesa como pedaço, tipo `reservation` ou `error`, não é.
5. Texto de interface em inglês vazando para o usuário é achado. Termo
   consagrado em português técnico, como `login`, `e-mail` e `layout`, não é.
6. Mistura no mesmo identificador é achado, mesmo quando cada metade se
   defende.

## 4. Governança de nome

1. Nome de arquivo em minúsculas, com `_` em Python e `-` em ativo estático,
   sem acento e sem espaço.
2. Nome que descreve o conteúdo; `utils`, `helpers`, `misc`, `novo`, `final`,
   `v2` e `temp` são achados.
3. Arquivo na camada certa conforme a tabela de responsabilidades de
   `CLAUDE.md`.
4. PRD seguindo `padrao-prd-lvjiujitsu.md` do vault, com número não reutilizado.
5. Nome de branch, worktree e comando conforme os contratos vigentes.
6. Arquivo sem consumidor, depois de buscar importação, chamada dinâmica, URL,
   template, signal, comando e referência por string.

Credencial literal em arquivo do repositório continua bloqueante, e o valor
nunca é transcrito. Mas as chaves deste projeto são descartáveis
(`CLAUDE.md` §1): o achado é sobre estar no arquivo, não sobre a chave ter
sido vista. Não propor rotação nem tratar como incidente.

## Registro

Achado objetivo vira PRD própria e é corrigido na mesma feature do ciclo.
Candidato do scanner que o agente considerar legítimo é declarado com
`--justified`, e o número precisa cobrir todos os candidatos daquele arquivo;
silêncio não é aceito. Justificativa recorrente e sempre igual é sinal de que o
scanner precisa mudar, e isso também vira PRD.

Remoção de comentário nunca altera comportamento. Quando a remoção exigir
renomear ou reestruturar para preservar a intenção, isso é mudança de código:
teste focado, gates e evidência, como qualquer correção.
