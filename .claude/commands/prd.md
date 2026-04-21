Crie um novo PRD para a seguinte demanda: $ARGUMENTS

Siga rigorosamente a estrutura definida em @AGENTS.md seção 11 (PRD obrigatório).

Antes de criar o PRD:
1. Classifique o tipo de demanda
2. Leia integralmente os arquivos do fluxo impactado
3. Registre o Context Ledger (arquivos lidos, adjacentes, internet, MCPs)
4. Busque contexto externo se envolver lib ou framework (Context7 primeiro)

O PRD deve incluir:
- Prompt de execução com Persona, Ação, Contexto, Restrições, Critérios de aceite, Evidências esperadas, Formato
- Critérios de aceite como assertions testáveis
- Plano TDD (Red → Green → Refactor)
- Seções de validação: visual, ORM, qualidade
- Sem migrações (política do projeto)

Salve em docs/prd/PRD-<NNN>-<slug>.md com o próximo número sequencial disponível.
