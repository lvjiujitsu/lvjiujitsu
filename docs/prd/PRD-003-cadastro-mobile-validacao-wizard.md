# PRD-003: Correções de responsividade e validação progressiva no cadastro
## Resumo
Corrigir problemas de renderização mobile no cadastro, reposicionar o controle visual do sistema na interface autenticada e impedir avanço de etapa quando campos obrigatórios estiverem inválidos.

## Problema atual
- Na tela de cadastro mobile, o agrupamento de ferramentas do topo quebra de forma inconsistente (botão "Voltar" e estado de rascunho).
- No wizard de cadastro, usuários avançam etapas com campos pendentes e só recebem erro no envio final.
- Em telas autenticadas (usuário/admin), o controle de tema do sistema não está visível no topo da tela.

## Objetivo
- Melhorar legibilidade e estabilidade do topo no mobile.
- Fazer validação por etapa antes de avançar.
- Exibir controle de tema também no cabeçalho das telas autenticadas.

## Contexto consultado
  - Context7: indisponível no ambiente atual de execução.
  - Web:
    - MDN `input[type="date"]`: comportamento de parsing/formato em dispositivos móveis e diferença entre valor exibido/local e valor serializado (`yyyy-mm-dd`).
      - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date
    - Django Forms Validation 4.1: reforço da responsabilidade de validação server-side (`clean`, `clean_<field>`, `ValidationError`) para manter segurança e consistência.
      - https://docs.djangoproject.com/en/4.1/ref/forms/validation/

## Dependências adicionadas
  - nenhuma

## Escopo / Fora do escopo
- **Escopo:** template de cadastro, script do wizard, CSS de autenticação e layout base.
- **Fora do escopo:** redesign completo do fluxo de turmas e implementação de novos componentes de cadastro.

## Arquivos impactados
  - `static/system/js/auth/registration-wizard-clean.js`
  - `static/system/css/auth/login.css`
  - `templates/login/register.html`
  - `templates/base.html`

## Riscos e edge cases
  - Regras de validação por etapa devem permanecer alinhadas às regras server-side do formulário.
  - Mensagens de validade nativa dependem do navegador (texto pode variar por locale).
  - Mudanças de layout mobile precisam preservar acessibilidade e toque em telas pequenas.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD: implementação restrita ao comportamento descrito neste PRD.
- MTV: mudanças de UX no template/CSS/JS sem mover regra de negócio para view.
- Validação de segurança permanece no backend; JS atua como pré-validação de UX.

## Critérios de aceite (escritos como assertions testáveis)
  - [x] Ao tocar em "Avançar" com campo obrigatório vazio na etapa atual, o wizard não deve avançar.
  - [x] Ao preencher senhas divergentes em uma etapa, o wizard deve impedir avanço e mostrar erro imediato.
  - [x] Em viewport pequena, botão "Voltar", indicador de rascunho e toggle de tema não devem quebrar layout de forma crítica.
  - [x] Em telas autenticadas, o toggle de tema deve ficar visível no topo.

## Plano (ordenado por dependência — fundações primeiro)
  - [x] 1. Ajustar regras de validação step-by-step no `registration-wizard-clean.js`
  - [x] 2. Corrigir nomes de campos médicos no template de cadastro para manter consistência de payload
  - [x] 3. Ajustar CSS mobile do topo do cadastro para eliminar quebras ruins
  - [x] 4. Expor toggle de tema no topo autenticado (`base.html`)
  - [x] 5. Validar fluxo com suíte de testes Django e `collectstatic`

## Comandos de validação
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 1`
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py findstatic system\css\auth\login.css`

## Implementado (preencher ao final)
- Validação por etapa foi reforçada no wizard com bloqueio de avanço, validação de confirmação de senha, validação de parentesco "Outro" e bloqueio global ao submeter caso etapas anteriores estejam inválidas.
- A etapa de turmas agora expõe seleção múltipla para titular/dependente/aluno do responsável com validação de pré-requisito no avanço.
- O fluxo foi reorganizado em etapas separadas por pessoa (titular/aluno, dependente e aluno do responsável), evitando mistura de turmas e prontuários.
- Campos ausentes foram completados no template (senhas/parentesco do dependente e do aluno do responsável, além de nascimento para perfil "Outro").
- Máscara de data `dd/mm/aaaa` foi reforçada com tratamento em `input`, `change` e `blur`, melhorando o comportamento em celular.
- Os campos médicos do titular no template foram alinhados aos nomes esperados pelo formulário backend (`holder_*`), evitando inconsistência no payload enviado.
- O layout do topo do cadastro foi ajustado para mobile com distribuição estável entre botão "Voltar", rascunho e toggle de tema.
- O toggle de tema passou a ficar visível no cabeçalho base também para telas autenticadas (usuário/admin).
- Validação técnica executada com `manage.py test`, `collectstatic --noinput` e `findstatic`.
- Reset destrutivo e re-seed executados com a sequência oficial do projeto (`clear_migrations.py`, `makemigrations`, `test`, `migrate`, `create_admin_superuser`, `inicial_seed`).
- Validação visual mobile executada com Playwright + Chromium, com capturas em `test_screenshots/`.

## Desvios do plano
- Nenhum até o momento.
