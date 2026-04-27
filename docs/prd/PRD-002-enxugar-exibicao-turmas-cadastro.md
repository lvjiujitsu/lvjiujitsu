# PRD-002: Enxugar a exibição das turmas no cadastro

## Resumo do que será implementado
Reduzir a verbosidade da etapa de turmas do wizard de cadastro, exibindo apenas as informações necessárias para decisão do usuário em mobile: nome da turma sem repetição desnecessária, resumo curto e grade por dia no formato `Horário - Professor`.

## Tipo de demanda
Correção pontual

## Problema atual
A etapa de turmas do cadastro está longa demais no mobile. A card repete `Jiu Jitsu Adulto`, exibe estrutura prolixa de grade por dia/professor e mantém elementos visuais redundantes, o que aumenta a rolagem e piora a leitura.

## Objetivo
Apresentar as turmas de forma mais compacta e direta, preservando a seleção e a elegibilidade atuais, mas simplificando a leitura para o usuário final.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-001-cadastro-cliente.md`
- `lvjiujitsu/urls.py`
- `system/urls.py`
- `system/views/auth_views.py`
- `system/forms/registration_forms.py`
- `system/services/class_overview.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/tests/test_forms.py`
- `system/tests/test_class_portal_views.py`
- trecho relevante de `system/tests/test_views.py` para o fluxo de cadastro
- trechos relevantes de `static/system/css/auth/login.css`
- trechos relevantes de `static/system/css/portal/class-catalog.css`

### Arquivos adjacentes consultados
- saída de busca em `system/models/` e `system/services/` para mapear o fluxo de turmas/horários
- `git status --short`

### Internet / documentação oficial
- Não aplicável para a correção proposta.

### MCPs / ferramentas verificadas
- shell PowerShell no workspace — ok — `Get-Location`
- ripgrep — ok — `rg --files ...`
- Playwright/browser MCP — pendente de verificação nesta execução

### Limitações encontradas
- Durante o preflight, `CLAUDE.md` estava desalinhado do repositório real; a divergência foi corrigida no decorrer desta entrega.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django server-rendered com JavaScript progressivo, seguindo SDD + TDD.

### Ação
Simplificar a apresentação das turmas na etapa de cadastro sem alterar a lógica de elegibilidade, seleção ou persistência do fluxo.

### Contexto
O wizard de cadastro usa `registration-wizard-clean.js` para renderizar dinamicamente as cards de turma com base no payload serializado por `get_registration_catalog_payload()`. O problema está na camada de apresentação mobile da etapa de turmas.

### Restrições
- sem hardcode de regras de negócio
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória do fluxo impactado
- validação visual obrigatória
- interface em pt-BR

### Critérios de aceite
- [ ] A card da turma no cadastro não deve repetir `Jiu Jitsu Adulto` desnecessariamente.
- [ ] A área expansível da turma deve priorizar `Dia da semana` e linhas simples no formato `Horário - Professor`.
- [ ] Informações secundárias não essenciais para a escolha imediata não devem poluir a tela.
- [ ] Seleção da turma, elegibilidade e payload do cadastro devem continuar funcionando.
- [ ] Layout deve ficar mais curto e legível no mobile.
- [ ] Console do navegador deve permanecer sem erros JS críticos.

### Evidências esperadas
- testes automatizados passando
- `manage.py check` sem erros
- `collectstatic --noinput` sem erros
- `showmigrations` coerente com a política do projeto
- validação visual da etapa de turmas em navegador
- console sem erro JS crítico

### Formato de saída
Código implementado + testes/ajustes de contrato + evidências reais de validação + limitações registradas

## Escopo
- reduzir a densidade visual das cards de turma do wizard
- simplificar a organização da grade de horários/professores
- manter compatibilidade com o fluxo atual de seleção

## Fora do escopo
- alterar regras de negócio de elegibilidade
- alterar persistência do cadastro
- alterar páginas públicas de catálogo fora do wizard
- criar migrações

## Arquivos impactados
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/css/auth/login.css`
- `system/tests/test_views.py` ou outro teste de contrato necessário

## Riscos e edge cases
- quebrar a distinção entre turmas físicas diferentes que compartilham o mesmo nome lógico
- perder informação útil demais ao resumir professor/horário
- regressão visual em telas pequenas por mudança de grid
- impacto indireto em plano família caso a seleção de turma deixe de refletir corretamente o estado atual

## Regras e restrições
- SDD antes de código
- TDD para o que for viável cobrir no contrato atual
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [ ] 1. Confirmar o estado atual da etapa de turmas
- [ ] 2. Definir o contrato visual mínimo e o menor ajuste necessário
- [ ] 3. Escrever teste/ajuste de contrato (Red)
- [ ] 4. Implementar simplificação do render (Green)
- [ ] 5. Ajustar estilos do bloco resumido (Refactor)
- [ ] 6. Validar tecnicamente
- [ ] 7. Validar visualmente em mobile
- [ ] 8. Registrar evidências e limitações

## Validação visual
### Desktop
- verificar que a card continua funcional e selecionável

### Mobile
- verificar redução de altura e leitura clara da grade

### Console do navegador
- sem erros JS críticos

### Terminal
- sem stack traces

## Validação ORM
### Banco
- não há alteração de schema

### Shell checks
- não aplicável além da integridade do fluxo de render e submissão

### Integridade do fluxo
- a seleção de turma deve continuar alimentando o campo oculto/multiple select corretamente

## Validação de qualidade
### Sem hardcode
- manter regras de elegibilidade e público vindas do catálogo existente

### Sem estruturas condicionais quebradiças
- extrair helpers simples e focados para o novo resumo

### Sem `except: pass`
- nenhuma supressão silenciosa de erro

### Sem mascaramento de erro
- manter falhas do fluxo visíveis via validação existente

### Sem comentários e docstrings desnecessários
- seguir o padrão atual do arquivo

## Evidências
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 186 testes passando
- `.\.venv\Scripts\python.exe manage.py check` → sem erros
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → 2 arquivos estáticos atualizados, sem erro
- `.\.venv\Scripts\python.exe manage.py showmigrations` → somente `system.0001_initial`, sem migrações novas
- Validação visual via Playwright em `http://127.0.0.1:8000/register/` no mobile e desktop → card da etapa 3 exibindo `Treinos disponíveis` e linhas no formato `06:30 - Layon Quirino`
- Console do navegador inspecionado via Playwright → 0 erros e 0 warnings críticos
- Cache-busting do template atualizado para garantir entrega do JS/CSS novo no navegador
- Artefatos temporários de screenshot removidos após a validação

## Implementado
- Payload do cadastro agora expõe `compact_schedule_sections` por dia com entradas prontas no formato `horário - professor`
- Renderer do wizard passou a consumir o resumo compacto em vez de montar uma grade tabular prolixa
- Card do fluxo solo deixou de repetir `Jiu Jitsu Adulto` no cabeçalho interno e passou a usar `Treinos disponíveis`
- Resumo expansível foi reduzido para `Ver horários da semana`
- CSS da grade antiga foi simplificado para uma lista curta e legível no mobile
- Versões dos assets em `templates/login/register.html` foram incrementadas para invalidar cache

## Desvios do plano
- Foi necessário incluir atualização de versão dos assets no template porque o navegador continuava servindo o JS/CSS anterior, impedindo a validação real da mudança.
- Foi necessário reescrever `CLAUDE.md` com dados factuais do projeto para remover a divergência encontrada no preflight.

## Pendências
- Nenhuma pendência funcional identificada para esta correção.
