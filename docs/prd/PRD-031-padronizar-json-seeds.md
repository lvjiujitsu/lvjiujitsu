# PRD-031: Padronizar JSONs das seeds

## Resumo do que será implementado
Renomear arquivos JSON de `static/initial_data/` para refletirem o comando de seed que os consome quando houver relação direta de um arquivo para uma seed. Arquivos consumidos por duas ou mais seeds não serão renomeados nesta etapa sem desmembramento, para evitar manter acoplamento oculto.

## Tipo de demanda
Regeneração documental e correção pontual de governança de seeds.

## Problema atual
Os arquivos JSON usam nomes de domínio (`belt_ranks.json`, `class_categories.json`, etc.), enquanto a operação real do projeto é por seeds atomizadas (`seed_system_initial_*`). Alguns JSONs são compartilhados por várias seeds, principalmente professores e administrativos, o que dificulta rastrear ownership.

## Objetivo
Deixar os JSONs de uso único com o mesmo nome da seed consumidora e registrar plano claro para separar os JSONs compartilhados por responsabilidade.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `system/management/commands/seed_system_initial_belt_ranks.py`
- `system/management/commands/seed_system_initial_class_categories.py`
- `system/management/commands/seed_system_initial_class_catalog.py`
- `system/management/commands/seed_system_initial_ibjjf_age_categories.py`
- `system/management/commands/seed_system_initial_graduation_rules.py`
- `system/management/commands/seed_system_initial_product_categories.py`
- `system/management/commands/seed_system_initial_product_catalog.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_class_categories_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `system/management/commands/seed_system_initial_class_categories_administrative.py`
- `system/management/commands/seed_system_initial_class_catalog_administrative.py`

### Arquivos adjacentes consultados
- `static/initial_data/`
- `docs/prd/`

### Internet / documentação oficial
- Não aplicável. Mudança interna de nomes de arquivos e contratos locais.

### MCPs / ferramentas verificadas
- PowerShell — OK — `Get-ChildItem`, `Get-Content`, `Move-Item`
- ripgrep — OK — `rg`
- Django — OK com limitação — `manage.py check` passou; suíte completa mantém falhas preexistentes de templates/rotas

### Limitações encontradas
- `system/migrations/0001_initial.py` já estava modificado antes desta tarefa e não será tocado.
- `legacy_product_skus.json` não tem consumidor ativo nos comandos atuais.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + governança de seeds.

### Ação
Renomear JSONs de uso único para o nome da seed consumidora e documentar plano de desmembramento dos JSONs compartilhados.

### Contexto
As seeds atuais são comandos individuais em `system/management/commands/` e os dados ficam em `static/initial_data/`.

### Restrições
- sem migrações
- sem alterar schema
- sem executar ciclo destrutivo
- sem criar orquestrador
- sem hardcode fora do contrato explícito do arquivo de seed
- preservar execução manual e sequencial das seeds

### Critérios de aceite
- [ ] JSONs consumidos por uma única seed têm nome derivado do comando consumidor.
- [ ] Comandos consumidores apontam para os novos nomes.
- [ ] JSONs compartilhados são listados com plano de separação por chave e dependência.
- [ ] `manage.py check` passa.
- [ ] Não há referências aos nomes antigos dos JSONs renomeados.

### Evidências esperadas
- `manage.py check`
- shell check carregando os JSONs renomeados sem erro
- `rg` sem referências obsoletas para arquivos renomeados

### Formato de saída
Código ajustado + PRD + evidências de validação.

## Escopo
Renomear:
- `belt_ranks.json`
- `class_categories.json`
- `class_catalog.json`
- `ibjjf_age_categories.json`
- `graduation_rules.json`
- `product_categories.json`
- `product_catalog.json`
- `product_inventory.json`
- `subscription_plans.json`

## Fora do escopo
Desmembrar agora os JSONs compartilhados por professores e administrativos.
Criar seeds novas para arquivos órfãos.
Alterar banco, modelos ou migrations.

## Arquivos impactados
- `static/initial_data/*.json`
- `system/management/commands/seed_system_initial_*.py`
- `docs/prd/PRD-031-padronizar-json-seeds.md`

## Riscos e edge cases
- Comandos podem falhar se mensagens ou nomes antigos ficarem hardcoded.
- Dois arquivos podem pertencer à mesma seed, como catálogo e inventário de produto; nesses casos o arquivo principal recebe o nome da seed e o complementar recebe sufixo funcional.
- JSON compartilhado por múltiplas seeds não deve receber nome de apenas uma seed sem separar o conteúdo.

## Regras e restrições
- SDD antes de código
- validação obrigatória
- sem migrações
- leitura integral obrigatória
- menor mudança correta antes de expansão de escopo

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes/checks antes da mudança
- [x] 4. Renomeação direta dos JSONs de uso único
- [x] 5. Ajuste dos comandos consumidores
- [x] 6. Plano de desmembramento dos JSONs compartilhados
- [x] 7. Validação completa
- [x] 8. Limpeza final
- [x] 9. Atualização documental

## Validação visual
### Desktop
Não aplicável.
### Mobile
Não aplicável.
### Console do navegador
Não aplicável.
### Terminal
Executar checks Django e inspeção de referências.

## Validação ORM
### Banco
Não haverá alteração de banco.
### Shell checks
Carregar os JSONs renomeados via `_load_json()` dos comandos.
### Integridade do fluxo
Confirmar que comandos continuam encontrando arquivos.

## Validação de qualidade
### Sem hardcode
Nomes de arquivo permanecem explícitos dentro de cada seed, que é o contrato atual do projeto.
### Sem estruturas condicionais quebradiças
Não aplicável.
### Sem `except: pass`
Não aplicável.
### Sem mascaramento de erro
`CommandError` permanece explícito quando arquivo não existe.
### Sem comentários e docstrings desnecessários
Não adicionar comentários novos desnecessários.

## Plano de desmembramento para JSONs compartilhados
### `initial_teachers.json`
Consumidores atuais:
- `seed_system_initial_teacher`
- `seed_system_initial_class_categories_teacher`

Separação proposta:
- `seed_system_initial_teacher.json`: dados da pessoa, conta de portal e histórico de graduação.
- `seed_system_initial_class_categories_teacher.json`: vínculos `{ "cpf": "...", "class_category": "..." }`.

Chaves de ligação:
- `cpf` identifica `Person`.
- `class_category` referencia `ClassCategory.code`.

Ordem:
1. `seed_system_initial_person_type`
2. `seed_system_initial_belt_ranks`
3. `seed_system_initial_teacher`
4. `seed_system_initial_class_categories`
5. `seed_system_initial_class_categories_teacher`

### `initial_administrative.json`
Consumidores atuais:
- `seed_system_initial_administrative`
- `seed_system_initial_class_categories_administrative`
- `seed_system_initial_class_catalog_administrative`

Separação proposta:
- `seed_system_initial_administrative.json`: dados da pessoa, conta de portal e histórico de graduação.
- `seed_system_initial_class_categories_administrative.json`: vínculos `{ "cpf": "...", "class_category": "..." }`.
- `seed_system_initial_class_catalog_administrative.json`: vínculos `{ "cpf": "...", "class_group_category": "...", "class_group_teacher_cpf": "..." }`.

Chaves de ligação:
- `cpf` identifica `Person` administrativo.
- `class_category` referencia `ClassCategory.code`.
- `class_group_category` referencia `ClassCategory.code`.
- `class_group_teacher_cpf` referencia `Person.cpf` do professor principal da turma.
- O `ClassGroup` é resolvido por `(class_category__code, main_teacher__cpf)`, conforme contrato atual pós-remoção de `ClassGroup.code`.

Ordem:
1. `seed_system_initial_person_type`
2. `seed_system_initial_belt_ranks`
3. `seed_system_initial_administrative`
4. `seed_system_initial_class_categories`
5. `seed_system_initial_class_categories_administrative`
6. `seed_system_initial_teacher`
7. `seed_system_initial_class_catalog`
8. `seed_system_initial_class_catalog_administrative`

### `product_catalog.json` e `product_inventory.json`
Ambos pertencem a uma única seed: `seed_system_initial_product_catalog`.

Separação aplicada nesta etapa:
- `seed_system_initial_product_catalog.json`: catálogo de produtos.
- `seed_system_initial_product_catalog_inventory.json`: variantes e estoque por SKU.

Chaves de ligação:
- `sku` identifica `Product`.
- `category` referencia `ProductCategory.code`.
- `inventory[].sku` referencia `Product.sku`.

### Arquivos sem consumidor ativo
Arquivos atuais:
- `legacy_product_skus.json`

Tratamento proposto:
- manter sem renomear nesta etapa, porque não há seed ativa que declare ownership.
- antes de renomear, escolher um destino explícito:
  - remover o arquivo se for legado morto; ou
  - recriar uma seed dedicada quando houver consumidor ativo.

## Evidências
- `.\.venv\Scripts\python.exe manage.py check` — passou: `System check identified no issues (0 silenced).`
- Shell check Django carregando `_load_json()` dos comandos — passou:
  - `seed_system_initial_belt_ranks`: 13 registros
  - `seed_system_initial_class_categories`: 4 registros
  - `seed_system_initial_class_catalog`: 6 registros
  - `seed_system_initial_ibjjf_age_categories`: 22 registros
  - `seed_system_initial_graduation_rules`: 52 registros
  - `seed_system_initial_product_categories`: 4 registros
  - `seed_system_initial_subscription_plans`: 3 registros
  - `seed_system_initial_product_catalog`: 5 produtos
  - `seed_system_initial_product_catalog_inventory`: 5 entradas de inventário
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands --verbosity 2` — passou: 4 testes OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — falhou com 5 failures e 109 errors, mantendo padrão observado antes desta mudança: exemplos incluem `TemplateDoesNotExist: home/student/dashboard.html`, `TemplateDoesNotExist: home/admin/dashboard.html` e `NoReverseMatch: person-list`.

## Implementado
- Renomeados JSONs de uso único para o padrão `seed_system_initial_<dominio>.json`.
- Mantidos `initial_teachers.json` e `initial_administrative.json` sem renomear até o desmembramento.
- Mantido `legacy_product_skus.json` sem renomear por não haver consumidor ativo.
- Ajustados comandos consumidores para carregar os novos nomes.

## Desvios do plano
- Nenhum desvio na mudança de seeds.
- A validação completa não ficou verde por falhas preexistentes na suíte geral.

## Pendências
- Desmembrar `initial_teachers.json` e `initial_administrative.json` em PRD/etapa própria.
- Decidir destino de `legacy_product_skus.json`, que não tem consumidor ativo.
