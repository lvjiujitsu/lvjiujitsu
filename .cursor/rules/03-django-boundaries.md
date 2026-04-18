# Django Boundaries Rule

- Cada app Django é um bounded context.
- Não importar `views` ou `forms` de outro app.
- Compartilhar apenas por `services`, `selectors`, `tasks`, eventos ou APIs internas explícitas.
- Views finas; lógica de negócio em services; leitura complexa em selectors.
