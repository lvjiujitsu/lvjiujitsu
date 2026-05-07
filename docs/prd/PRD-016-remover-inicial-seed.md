# PRD-016: Remover inicial_seed

## Resumo do que será implementado
Remover o comando agregador `inicial_seed` e substituir sua dependência em `inicial_seed_test` por uma sequência explícita de comandos granulares.

## Tipo de demanda
Refatoração de governança de seeds.

## Problema atual
`inicial_seed` concentra múltiplas responsabilidades e esconde a ordem real de carga inicial do sistema. Além disso, `inicial_seed_test` depende desse agregador, então remover apenas o arquivo deixaria o comando de teste quebrado.

## Objetivo
Eliminar o comando `inicial_seed` como ponto de entrada e registrar a sequência correta de execução das seeds iniciais sem quebrar o setup de teste manual.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/management/commands/seed_person_type.py`
- `system/management/commands/seed_class_catalog.py`
- `system/management/commands/seed_belts.py`
- `system/management/commands/seed_products.py`
- `system/management/commands/seed_plans.py`
- `system/management/commands/seed_holidays.py`
- `system/management/commands/seed_test_personas.py`
- `system/management/commands/seed_person_administrative.py`
- `system/tests/test_commands.py`
- `system/services/seeding.py`

### Arquivos adjacentes consultados
- `README.md`
- lista de comandos em `system/management/commands/`
- PRDs existentes em `docs/prd/`

### Internet / documentação oficial
- Não aplicável. A mudança usa comandos Django já existentes no projeto.

### MCPs / ferramentas verificadas
- PowerShell — OK — `Get-Location`, `Get-Content`, `Get-ChildItem`
- Python da `.venv` — OK — `.\.venv\Scripts\python.exe --version`
- Django management — OK — `manage.py help inicial_seed`
- Git — OK — `git status --short`, `git diff`

### Limitações encontradas
- `rg` falhou com acesso negado neste ambiente; foi substituído por PowerShell.
- A worktree já possuía muitas alterações não relacionadas; a mudança deve ser mínima e preservar o estado atual.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + MVT com services.

### Ação
Remover `inicial_seed` e ajustar os pontos vivos que dependem dele, sem alterar ainda a implementação interna das seeds granulares.

### Contexto
O projeto precisa migrar de uma seed inicial agregadora para uma sequência explícita de seeds independentes. Esta primeira etapa remove o guarda-chuva `inicial_seed` e documenta a ordem operacional.

### Restrições
- sem hardcode de segredo
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória
- não reverter alterações pré-existentes da worktree

### Critérios de aceite
- [ ] `manage.py help inicial_seed` não deve encontrar o comando.
- [ ] `inicial_seed_test` não deve chamar `inicial_seed`.
- [ ] `inicial_seed_test` deve chamar uma sequência explícita de seeds granulares.
- [ ] `CLAUDE.md` deve deixar de documentar `inicial_seed` como comando real.
- [ ] A sequência recomendada de seeds iniciais deve estar documentada.

### Evidências esperadas
- teste específico falhando antes da implementação
- teste específico passando depois da implementação
- `manage.py check` sem erros
- `manage.py help inicial_seed` retornando comando desconhecido

### Formato de saída
Código implementado + testes + evidências de validação + sequência correta de execução.

## Escopo
- Remover `system/management/commands/inicial_seed.py`.
- Atualizar `system/management/commands/inicial_seed_test.py`.
- Adicionar testes de governança para os comandos de seed.
- Atualizar `CLAUDE.md`.

## Fora do escopo
- Refatorar `system/services/seeding.py`.
- Tornar `seed_class_catalog` isolado internamente.
- Criar novas seeds granulares.
- Alterar schema ou criar migrações.

## Arquivos impactados
- `docs/prd/PRD-016-remover-inicial-seed.md`
- `system/management/commands/inicial_seed.py`
- `system/management/commands/inicial_seed_test.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Riscos e edge cases
- `inicial_seed_test` pode quebrar se continuar chamando o comando removido.
- Documentação pode ficar divergente se `CLAUDE.md` ainda listar `inicial_seed`.
- Seeds ainda não são totalmente independentes internamente; esse risco permanece para a próxima etapa.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementação (Green)
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Não aplicável.

### Mobile
Não aplicável.

### Console do navegador
Não aplicável.

### Terminal
Validar via comandos Django.

## Validação ORM
### Banco
Não há alteração de schema nem necessidade de escrita permanente para esta etapa.

### Shell checks
Não aplicável para remoção do comando.

### Integridade do fluxo
Validar que `inicial_seed_test` usa comandos granulares.

## Validação de qualidade
### Sem hardcode
Nenhum segredo ou configuração variável será introduzido.

### Sem estruturas condicionais quebradiças
Não aplicável.

### Sem `except: pass`
Não introduzir.

### Sem mascaramento de erro
Comando removido deve falhar explicitamente como comando desconhecido.

### Sem comentários e docstrings desnecessários
Não adicionar comentários de código.

## Evidências
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` falhou com 2 falhas esperadas antes da implementação.
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_commands.SeedCommandGovernanceTestCase --verbosity 2` passou com 2 testes.
- `.\.venv\Scripts\python.exe manage.py help inicial_seed` retornou `Unknown command: 'inicial_seed'. Did you mean inicial_seed_test?`.
- `.\.venv\Scripts\python.exe manage.py help inicial_seed_test` retornou help válido do comando.
- `.\.venv\Scripts\python.exe manage.py check` retornou `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\python.exe manage.py showmigrations` mostrou `system [X] 0001_initial`, sem migração nova.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` executou 314 testes com `OK`.
- Artefato temporário de teste `cleanup-artifacts-0jwsat8s` removido após validação.

## Implementado
- Removido `system/management/commands/inicial_seed.py`.
- Atualizado `inicial_seed_test` para chamar explicitamente seeds granulares.
- Adicionados testes de governança para impedir retorno de `inicial_seed`.
- Atualizado `CLAUDE.md` com sequência operacional explícita.

## Desvios do plano
- Nenhum.

## Pendências
- Refatorar posteriormente seeds internas para que cada comando tenha responsabilidade única.
