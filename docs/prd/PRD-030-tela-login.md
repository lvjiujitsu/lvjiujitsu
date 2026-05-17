# PRD-030: Tela de Login — Implementação do Zero

## Resumo do que será implementado

Implementação completa do zero da tela de login do portal LV JIU JITSU: template HTML standalone, CSS com tokens de tema claro/escuro e JS mínimo (alternância de tema + visibilidade de senha). Inclui limpeza de `system/urls.py` para manter apenas rotas de autenticação e homes, e reescrita completa de `docs/UI-SCREEN-CONTRACT.md`.

---

## Tipo de demanda

Redesign + implementação do zero (nova feature de UI)

---

## Problema atual

Todos os templates, CSS e JS foram deletados pelo usuário para reiniciar o projeto visual do zero. O sistema não renderiza nenhuma tela. A tela de login é o ponto de entrada do sistema e deve ser a primeira entrega.

---

## Objetivo

Entregar uma tela de login funcional, visualmente coerente com a identidade LV, responsiva em celular e desktop, com tema claro e escuro, a partir de nenhum template ou asset existente.

---

## Context Ledger

### Arquivos lidos integralmente

- `system/views/auth_views.py` — PortalLoginView, PortalLogoutView, PortalPasswordResetView e variantes
- `system/forms/auth_forms.py` — PortalAuthenticationForm (campos: identifier, password)
- `system/urls.py` — inventário completo de rotas antes da limpeza
- `system/views/home_views.py` — DashboardRedirectView e homes (destino pós-login)
- `system/views/__init__.py` — estrutura de re-exports
- `docs/UI-SCREEN-CONTRACT.md` — contrato visual (reescrito nesta entrega)
- `lvjiujitsu/settings.py` — configurações gerais

### Arquivos adjacentes consultados

- `system/views/portal_mixins.py`
- `static/system/img/` — assets de logo disponíveis

### Internet / documentação oficial

- Django 4.1 FormView, CSRF, sistema de mensagens
- WCAG 2.2 — target size mínimo (2.5.8), contraste (1.4.3)

### MCPs / ferramentas verificadas

- Playwright v1.52.0 — disponível no .venv
- Python 3.12.10 via `.venv/Scripts/python.exe` — funcional
- `manage.py check` — 0 issues pré-entrega

### Limitações encontradas

- `templates/login/` não existia — criado nesta entrega
- `static/system/css/auth/` não existia — criado nesta entrega
- `static/system/js/auth/` não existia — criado nesta entrega
- Após login bem-sucedido, `DashboardRedirectView` redireciona para homes sem template ainda — `TemplateDoesNotExist` esperado nesta fase, não é bug desta entrega

---

## Mapeamento de rotas

| Rota | View | Método | Propósito | Template desta entrega |
|---|---|---|---|---|
| `GET /` | PortalLoginView | GET | Redireciona root para login | `login/login_form.html` |
| `GET /login/` | PortalLoginView | GET | Exibe formulário de login | `login/login_form.html` |
| `POST /login/` | PortalLoginView | POST | Processa credenciais | `login/login_form.html` (em erro) |
| `GET /logout/` | PortalLogoutView | GET | Encerra sessão → root | — |
| `POST /logout/` | PortalLogoutView | POST | Encerra sessão → root | — |
| `GET /dashboard/` | DashboardRedirectView | GET | Redireciona para home do perfil | — |
| `GET /home/admin/` | AdminHomeView | GET | Home admin técnico | fora do escopo |
| `GET /home/administrative/` | AdministrativeHomeView | GET | Home administrativo | fora do escopo |
| `GET /home/instructor/` | InstructorHomeView | GET | Home professor | fora do escopo |
| `GET /home/student/` | StudentHomeView | GET | Home aluno | fora do escopo |
| `GET/POST /password-reset/` | PortalPasswordResetView | GET/POST | Solicitar redefinição | fora do escopo |
| `GET /password-reset/done/` | PortalPasswordResetDoneView | GET | Confirmação de envio | fora do escopo |
| `GET/POST /reset/<token>/` | PortalPasswordResetConfirmView | GET/POST | Redefinir senha | fora do escopo |
| `GET /reset/done/` | PortalPasswordResetCompleteView | GET | Senha redefinida | fora do escopo |

---

## Requisitos funcionais (RF)

### RF-01 — Exibição para usuário não autenticado
O sistema deve exibir o formulário de login quando o usuário acessa `GET /login/` ou `GET /` sem sessão ativa.

**Verificável por:** navegador sem sessão → rota `/login/` → formulário visível.

### RF-02 — Redirecionamento de usuário já autenticado
Se o usuário já tiver sessão ativa (`portal_account` ou `portal_is_technical_admin`), o sistema deve redirecionar automaticamente para `/dashboard/` sem exibir o formulário.

**Verificável por:** login → voltar a `/login/` → deve redirecionar, não mostrar formulário.

### RF-03 — Campos do formulário
O formulário deve exibir dois campos com labels visíveis:
- "CPF ou acesso técnico" (campo `identifier`)
- "Senha" (campo `password`)

Os atributos `autofocus`, `autocomplete` e `placeholder` do `PortalAuthenticationForm` devem ser preservados.

**Verificável por:** inspeção visual e de HTML renderizado.

### RF-04 — Submissão e autenticação
- O formulário deve ser enviado via `POST` com CSRF token obrigatório.
- Em caso de sucesso, redirecionar para o valor de `next` da query string, ou para `/dashboard/`.
- Em caso de falha, re-exibir o formulário com erros não-campo visíveis.

**Verificável por:** POST com credencial inválida → formulário re-exibido com erro.

### RF-05 — Erros de campo e não-campo
- Erros de campo individuais devem aparecer abaixo do campo correspondente.
- Erros não-campo (credenciais inválidas, pagamento pendente) devem aparecer acima dos campos com destaque visual e `role="alert"`.

**Verificável por:** POST inválido → erro visível no lugar correto.

### RF-06 — Mensagens do Django
Mensagens da sessão (ex.: redirecionamento por pagamento pendente) devem ser exibidas antes do formulário.

**Verificável por:** sessão com mensagem pendente → mensagem visível ao renderizar o login.

### RF-07 — Link para recuperação de senha
O formulário deve exibir um link com texto "Esqueceu sua senha?" apontando para `/password-reset/`.

**Verificável por:** inspeção visual e do HTML renderizado.

### RF-08 — Alternância de tema
- A tela deve disponibilizar botão de alternância claro/escuro.
- O tema inicial respeita `localStorage["lv-theme"]` ou, na ausência, `prefers-color-scheme`.
- A preferência deve persistir após reload via `localStorage`.

**Verificável por:** clicar no botão → tema muda; reload → tema persiste.

### RF-09 — Visibilidade de senha
O campo de senha deve ter um botão de alternância que exibe/oculta o conteúdo (toggle `type="text"` / `type="password"`).

**Verificável por:** clicar no botão de olho → campo alterna entre texto e pontos.

### RF-10 — Parâmetro `next`
Se presente na query string, o valor de `next` deve ser propagado na `action` do formulário para ser enviado no POST.

**Verificável por:** `GET /login/?next=/home/student/` → action do form contém `?next=/home/student/`.

---

## Requisitos não funcionais (RNF)

### RNF-01 — Responsividade
- **Mobile (até 639px):** layout em coluna única; logo no topo centralizado; formulário abaixo com largura controlada.
- **Desktop (768px+):** layout em duas colunas — painel de marca à esquerda, formulário à direita.

### RNF-02 — Tema claro e escuro
- Todos os tokens CSS do contrato `UI-SCREEN-CONTRACT.md` devem ser usados.
- Nenhuma cor hardcoded fora dos tokens.
- Contraste de texto mínimo: WCAG AA (4.5:1 para texto normal).

### RNF-03 — Acessibilidade
- Labels visíveis associadas por `for`/`id`.
- Foco visível em todos os controles (`:focus-visible` com `--focus-ring`).
- Botões com `aria-label` descritivo.
- Erros com `role="alert"`.
- Alvo mínimo de toque: 44×44px (WCAG 2.5.8).

### RNF-04 — Performance
- CSS carregado de arquivo externo em `static/system/css/auth/login.css`.
- JS carregado com `defer` de arquivo externo em `static/system/js/auth/login.js`.
- Nenhum CSS ou JS inline.

### RNF-05 — Segurança
- `{% csrf_token %}` obrigatório no formulário POST.
- Sem credenciais ou segredos em HTML/JS.
- Sem `innerHTML` com dados do usuário.
- Input de senha com `autocomplete="current-password"`.

### RNF-06 — Identidade visual LV
- Logo LV visível com destaque.
- Paleta: preto/grafite base, vermelho LV como acento.
- Nenhum gradiente genérico.

### RNF-07 — Autonomia do template
- A tela de login não herda `base.html` (ainda não existe).
- É um documento HTML completo e autossuficiente.

---

## Escopo desta entrega

- [x] `system/urls.py` — limpeza para manter apenas rotas de autenticação e homes
- [x] `docs/UI-SCREEN-CONTRACT.md` — reescrita completa do contrato visual
- [x] `docs/prd/PRD-030-tela-login.md` — este documento
- [x] `templates/login/login_form.html` — template standalone de login
- [x] `static/system/css/auth/login.css` — CSS com tokens claro/escuro
- [x] `static/system/js/auth/login.js` — tema + visibilidade de senha

---

## Fora do escopo

- Templates de recuperação de senha (`password_reset_*.html`)
- Template de registro (`register.html`)
- `base.html` e shell global
- Home dashboards (admin, administrativo, professor, aluno)
- Qualquer outro módulo do sistema

---

## Arquivos impactados

| Arquivo | Operação |
|---|---|
| `system/urls.py` | modificado |
| `docs/UI-SCREEN-CONTRACT.md` | reescrito |
| `docs/prd/PRD-030-tela-login.md` | criado |
| `templates/login/login_form.html` | criado |
| `static/system/css/auth/login.css` | criado |
| `static/system/js/auth/login.js` | criado |

---

## Riscos e edge cases

- **TemplateDoesNotExist pós-login:** `DashboardRedirectView` redireciona para homes sem template. Esperado nesta fase.
- **Open redirect em `next`:** `PortalLoginView` usa o parâmetro `next` sem validar `is_safe_url`. Risco documentado como pendência de segurança para PRD futuro.
- **Logo ausente:** se `logo-lv-bjj.png` não estiver disponível, a tela ainda deve renderizar corretamente com o `alt` visível.

---

## Regras e restrições

- SDD antes de código
- TDD para implementação (testes de view existentes devem passar)
- Sem hardcode de cores fora dos tokens
- Sem `innerHTML` com dados do usuário
- Sem migrações (nenhuma alteração de modelo)
- Leitura integral obrigatória antes de editar
- Validação visual obrigatória (Playwright)

---

## Plano

- [x] 1. Contexto e leitura integral (views, forms, urls, settings, contract)
- [x] 2. Limpar `system/urls.py`
- [x] 3. Reescrever `UI-SCREEN-CONTRACT.md`
- [x] 4. Criar este PRD
- [x] 5. Criar `login_form.html`
- [x] 6. Criar `login.css`
- [x] 7. Criar `login.js`
- [ ] 8. `manage.py check` — 0 issues
- [ ] 9. `manage.py collectstatic --noinput`
- [ ] 10. Validação visual desktop e mobile
- [ ] 11. Verificação de console e terminal

---

## Critérios de aceite

- [ ] `GET /login/` renderiza sem erro 500
- [ ] `POST /login/` com credencial inválida re-exibe formulário com erro visível
- [ ] `POST /login/` com credencial válida redireciona para `/dashboard/`
- [ ] Tema claro: tokens de fundo, texto e borda corretos
- [ ] Tema escuro: todos os tokens substituídos corretamente
- [ ] Preferência de tema persiste após reload (localStorage)
- [ ] Botão de visibilidade de senha alterna o campo corretamente
- [ ] Link "Esqueceu sua senha?" presente e aponta para `/password-reset/`
- [ ] Layout desktop: duas colunas (brand + form)
- [ ] Layout mobile (< 640px): uma coluna, logo + formulário empilhados
- [ ] `manage.py check` — 0 issues
- [ ] Console do navegador — sem erros JS

---

## Validação visual

### Desktop
- [ ] Painel de marca visível à esquerda com logo LV
- [ ] Painel de formulário à direita, centralizado verticalmente
- [ ] Campos com label, placeholder e foco visíveis
- [ ] Botão "Entrar" com acento vermelho LV
- [ ] Link "Esqueceu sua senha?" abaixo do botão
- [ ] Botão de tema no canto superior direito

### Mobile
- [ ] Logo no topo centralizado
- [ ] Formulário abaixo, largura adequada
- [ ] Campos com toque mínimo confortável
- [ ] Nenhum elemento cortado ou oculto

### Console do navegador
- [ ] Sem erros JavaScript
- [ ] Sem 404 de assets estáticos

### Terminal
- [ ] Sem stack trace no runserver

---

## Validação ORM

Não aplicável para esta tela. A autenticação ocorre via `authenticate_portal_identity` em `system/services/`, sem acesso direto ao banco na view.

---

## Validação de qualidade

- [ ] Nenhuma cor hardcoded fora dos tokens CSS
- [ ] Nenhum `innerHTML` com dados do usuário
- [ ] Nenhum CSS ou JS inline no template
- [ ] Nenhum comentário desnecessário no código

---

## Evidências

(a preencher após validação)

---

## Implementado

- `system/urls.py` — limpo para 13 rotas (auth + homes)
- `docs/UI-SCREEN-CONTRACT.md` — reescrito do zero com tokens, inventário e regras
- `templates/login/login_form.html` — template standalone criado
- `static/system/css/auth/login.css` — CSS com tokens claro/escuro criado
- `static/system/js/auth/login.js` — JS de tema e senha criado

---

## Desvios do plano

(a preencher)

---

## Pendências

- Validação do parâmetro `next` contra URLs seguras (open redirect potencial)
- Templates de recuperação de senha (PRD futuro)
- Template de registro/cadastro (PRD futuro)
- Shell global `base.html` e topbar (PRD futuro)
- Home dashboards de todos os perfis (PRDs futuros)
