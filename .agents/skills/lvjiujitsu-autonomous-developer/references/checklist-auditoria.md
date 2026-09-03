# Checklist de auditoria

Ler o arquivo inteiro não é auditá-lo. `state.py audit` só pode ser registrado
depois de executar, sobre aquele arquivo, todas as verificações da sua
responsabilidade mais as universais. Verificação não executada é arquivo não
auditado.

Cada item exige uma constatação concreta: um caminho de consumidor rastreado,
uma contagem, uma busca com resultado, um trecho identificado. Impressão geral,
"parece correto" e "segue o padrão do projeto" não satisfazem nenhum item.

## Universais, para todo arquivo

1. Consumidores: buscar quem importa, chama, herda, referencia por string, por
   URL, por template, por signal ou por comando. Registrar os caminhos em
   `--consumers`. Zero consumidores é candidato a código morto e exige a busca
   nas seis formas antes de concluir.
2. Valor cravado: número mágico, caminho absoluto, URL, host, porta, e-mail,
   telefone, CPF/CNPJ, ano, prazo, limite, credencial ou nome de ambiente
   escrito no corpo do arquivo em vez de vir de `settings`, de constante
   nomeada ou do banco.
3. Duplicação: a mesma regra implementada em outro arquivo com redação
   diferente. Comparar com o consumidor mais próximo antes de aceitar.
4. Divergência com o contrato: o comportamento observado contradiz `CLAUDE.md`,
   a PRD que o originou ou a documentação operacional.
5. Tratamento de erro: exceção engolida, `except` amplo, falha silenciosa,
   retorno `None` não verificado pelo chamador.

## `form`

1. Contar consultas dentro de `clean`, `clean_<campo>`, `save` e validadores.
   Toda chamada a `.filter`, `.exists`, `.count`, `.get` ou `.first` dentro de
   laço, `for` de compreensão ou `any`/`all` é N+1: substituir por uma consulta
   com `__in` e comparar em memória.
2. Provar o custo quando o campo aceitar múltiplos valores: medir com
   `CaptureQueriesContext` variando a quantidade de itens submetidos e
   confirmar que o número de consultas não cresce com a entrada.
3. Validar server-side tudo que o template restringe apenas no widget:
   `queryset` do campo, escolhas aceitas, faixa numérica, tamanho e formato.
4. Verificar mass assignment: `fields` explícito, nunca `__all__`; campos de
   estado, dono, preço ou situação nunca vindos do POST.
5. Confirmar que o formulário público não expõe objeto inativo, de outro ano,
   de outro cliente ou já ocupado.

## `view`

1. Autorização por ação e por objeto: decorador presente, e o objeto carregado
   pertence ao escopo de quem pede. Rota administrativa sem
   `staff_member_required` é bloqueante.
2. Método HTTP restrito; toda escrita em POST e com CSRF.
3. Queryset otimizado: `select_related` para ForeignKey lida no template,
   `prefetch_related`/`Prefetch` para reverso, e nenhuma consulta dentro de
   laço de montagem de contexto.
4. Escrita relacionada dentro de `transaction.atomic`, exceto quando sucesso
   parcial for o comportamento desejado e estiver reportado ao operador.
5. Redirecionamento com destino vindo de parâmetro, de banco ou de header sem
   validação de origem.
6. Enumeração: resposta que diferencia "não existe" de "existe mas é proibido"
   para quem não tem permissão.

## `model`

1. Constraint e validação de invariante no banco, não só no formulário:
   `unique_together`, `CheckConstraint`, `null`/`blank` coerentes.
2. `index` nos campos usados em filtro e ordenação frequentes.
3. Propriedade que executa consulta e é usada dentro de laço em template.
4. `save` sobrescrito com efeito colateral não transacional.
5. Construção de URL, telefone ou identificador a partir de campo livre:
   confirmar que o prefixo fixo impede escapar para outro host ou esquema.

## `selector`

1. Toda função devolve queryset ou lista já otimizada, sem consulta pendente
   que o consumidor executará em laço.
2. Filtro por ano, layout, cliente e situação aplicado no banco, não em Python.
3. Ausência de `len()` sobre queryset onde `count()` basta, e vice-versa quando
   o resultado já será materializado.

## `service`

1. Toda escrita múltipla em `transaction.atomic`.
2. Idempotência e concorrência: duas execuções simultâneas não duplicam nem
   corrompem; usar `select_for_update` ou constraint quando aplicável.
3. Regra de negócio vive aqui e não no template, na view ou no formulário.
4. Integração externa com timeout, tratamento de falha e sem vazar credencial
   em log ou exceção.

## `template`

1. `csrf_token` em todo `form` com método POST.
2. Nenhum `|safe`, `mark_safe` ou `autoescape off` sobre valor de origem
   humana; dado para JavaScript passa por `json_script`.
3. Sem consulta ou regra de negócio no template; sem acesso a atributo que
   dispara consulta dentro de `for`.
4. Acessibilidade: rótulo associado a campo, texto alternativo em imagem,
   ordem de foco, papel e estado em componente interativo, contraste.
5. Responsividade: a estrutura não assume largura fixa nem quebra em 390px.

## `javascript`

1. `innerHTML`, `outerHTML`, `insertAdjacentHTML` e `eval` com origem
   rastreada; se vier de resposta do servidor, confirmar que o servidor escapa.
2. Escrita enviando CSRF e respeitando o mesmo controle de permissão do
   servidor; a validação do cliente nunca substitui a do servidor.
3. Listener adicionado sem remoção em componente recriado, e laço sobre o DOM
   dentro de evento de alta frequência.
4. Estado inicial coerente com o servidor quando o JavaScript estiver
   desabilitado ou falhar.

## `css`

1. Suporte aos dois temas, sem cor cravada fora das variáveis do tema.
2. Contraste suficiente em ambos os temas.
3. Sem `!important` para vencer especificidade acidental, sem seletor morto e
   sem regra duplicada.
4. Comportamento em 390px e 1440px, sem overflow horizontal.

## `command`

1. Guarda de ambiente para operação destrutiva: o comando recusa produção ou
   exige confirmação explícita documentada.
2. Idempotência declarada e verdadeira.
3. Saída não imprime valor de variável de ambiente nem credencial.
4. Consistência com
   `C:\Users\whsf\Documents\GitHub\obsidian\projetos\operacao-banco-seeds-lvjiujitsu.md`.

## `migration`

1. Corresponde exatamente ao estado dos models: confirmar com
   `makemigrations --check --dry-run`.
2. Nenhum dado de negócio criado por migration.
3. Operação destrutiva ou irreversível identificada e justificada.

## `seed`

1. Compatível com o schema atual e com a ordem canônica documentada.
2. Não sobrescreve dado que não criou; reexecução não duplica.

## `configuration`

1. Segredo vem do ambiente, com falha explícita quando ausente em `hg` e
   `prod`; comparar nomes de chave, nunca imprimir valor.
2. `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, cookies seguros, HSTS e
   `X_FRAME_OPTIONS` coerentes com o ambiente.
3. Dependência declarada em `requirements.txt`, sem versão frouxa e sem pacote
   não usado.

## `test`

1. O teste falha se o comportamento quebrar: verificar que a asserção é sobre o
   resultado observável e não sobre a implementação nem sobre si mesma.
2. Cobre caminho feliz, inválido, proibido e limite; autorização testada por
   ação.
3. Sem dependência de ordem de execução, de relógio, de rede ou de dado
   residual.
4. Teste marcado como pulado sem justificativa é achado.

## `documentation`

1. Cada afirmação verificável contra o código atual; divergência é achado.
2. Comando citado existe e funciona como descrito.
3. Link interno resolve.

## `asset`

1. Consumidores rastreados; asset sem consumidor é candidato a remoção.
2. Duplicação com outro asset do repositório.
3. Peso desproporcional ao uso.
4. Binário recebe finalidade, tamanho, localização e consumidores, sem
   interpretar bytes.

## Registro

`--risks` deve refletir as categorias efetivamente examinadas naquele arquivo.
`none` só é aceitável quando nenhuma categoria da responsabilidade se aplicar,
o que é raro fora de `asset`. Defeito objetivo encontrado vira PRD própria na
mesma rodada, mesmo que pequeno, e mesmo que o arquivo já tenha sido auditado
sem achado em rodadas anteriores.
