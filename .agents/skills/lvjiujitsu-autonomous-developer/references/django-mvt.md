# Django MVT

## Responsabilidades

- `models/`: persistência, constraints e invariantes locais.
- `forms/`: normalização e validação de entrada.
- `services/`: escrita transacional e regra de negócio.
- `selectors/`: leitura reutilizável e queries otimizadas.
- `views/`: HTTP, autenticação, autorização e coordenação fina.
- `templates/`: apresentação sem regra central.
- `static/`: interação e estilo sem substituir validação server-side.
- `tests/`: contratos por camada, regressão e autorização.

## Revisão obrigatória

Rastrear URL até view, form, service, selector, model, template, static e testes. Verificar caminhos feliz, vazio, inválido, proibido, concorrente e destrutivo.

Procurar N+1, query em laço, carregamento excessivo, ausência de `select_related` ou `prefetch_related`, escrita relacionada sem `transaction.atomic`, validação duplicada, view espessa, regra em template, dependência circular e exceção mascarada.

Conferir migrations contra models, seeds contra schema, comandos contra ambientes e testes contra o comportamento real. Não editar `staticfiles/` nem migration gerada manualmente.

Remover função somente depois de buscar importações, chamadas dinâmicas, URLs, templates, signals, commands, testes e referências por string.
