# AGENTS.md

> Protocolo universal, obrigatório, rígido e auditável para agentes de desenvolvimento.
> Este arquivo define **como o agente deve trabalhar**.
> O contexto persistente e específico do projeto fica em `CLAUDE.md`.
> As regras operacionais sempre ativas ficam em `.cursor/rules/`.
> Hooks, quando disponíveis, são parte do enforcement obrigatório.
>
> **Objetivo principal:** controle, coerência, auditabilidade, redução de alucinação e comportamento previsível.
> **Objetivo secundário:** produtividade.
> **Economia de tokens, custo e tempo NÃO são critérios de decisão.**
>
> Se houver conflito entre velocidade e controle, vence controle.
> Se houver conflito entre brevidade e completude, vence completude.
> Se houver conflito entre “parece suficiente” e “é verificável”, vence o que é verificável.

---

## 1. Papel de cada artefato

### `AGENTS.md`
Fonte de verdade para:
- protocolo de execução;
- ordem de precedência;
- fases obrigatórias;
- política de contexto máximo;
- política obrigatória de MCPs;
- PRD;
- implementação;
- validação;
- auditoria;
- critérios de falha;
- regeneração documental.

### `CLAUDE.md`
Fonte de verdade para:
- identidade real do projeto;
- topologia de domínios/apps;
- convenções locais;
- comandos reais;
- integrações e MCPs obrigatórios;
- restrições arquiteturais locais;
- decisões persistentes de negócio e infraestrutura.

### `.cursor/rules/`
Fonte de verdade para:
- reforço operacional por tema;
- redundância deliberada dos controles críticos;
- instruções sempre ativas no runtime do Cursor;
- validações e bloqueios textuais adicionais.

### Hooks / validações operacionais
Fonte de verdade para:
- enforcement determinístico quando o ambiente suportar;
- bloqueio de ações proibidas;
- auditoria automática;
- validações repetitivas;
- verificação de MCPs, evidências e ledger.

---

## 2. Precedência

Em caso de conflito:
1. solicitação atual do usuário;
2. segurança, integridade, auditoria e conformidade;
3. este `AGENTS.md`;
4. `CLAUDE.md`;
5. `.cursor/rules/`;
6. hooks / validações automáticas do ambiente;
7. convenções locais do repositório.

Se `AGENTS.md`, `CLAUDE.md` e `.cursor/rules/` divergirem, a tarefa **não está concluída** até a divergência ser corrigida.

---

## 3. Princípios inegociáveis

- **Controle > performance**.
- **Auditoria > conveniência**.
- **Contexto completo > resposta rápida**.
- **Evidência > alegação**.
- **MCP obrigatório quando existir e for relevante**.
- **PRD antes de mudança relevante**.
- **Validação antes de declarar sucesso**.
- **Sem decisões por snippet quando o fluxo exigir arquivo completo**.
- **Sem resposta genérica quando o projeto exige especificidade**.
- **Sem “achar” quando for possível verificar**.
- **Sem ocultar limitações do ambiente**.

---

## 4. Política central anti-alucinação

O agente DEVE operar sob o seguinte regime:

1. Não assumir que entendeu o fluxo com base em trecho parcial.
2. Não assumir que um arquivo irrelevante pode ser ignorado sem avaliação explícita.
3. Não assumir que um MCP está funcional sem teste na sessão atual.
4. Não assumir que documentação antiga continua válida sem checagem.
5. Não assumir que uma regra local está alinhada com `AGENTS.md`/`CLAUDE.md`/`.cursor/rules/` sem validação.
6. Não assumir que “implementado” significa “validado”.
7. Não assumir que um comando existe sem conferir.
8. Não assumir que uma integração externa pode ser usada sem segurança, autenticação e rastreabilidade.

### Regra obrigatória
Toda conclusão relevante deve estar apoiada por pelo menos um destes pilares:
- leitura integral dos arquivos do fluxo;
- execução observável de comando;
- resposta observável de MCP;
- teste automatizado;
- documentação oficial;
- evidência explícita registrada em ledger/PRD/relatório.

---

## 5. FASE 0 — Preflight obrigatório e inviolável

Nada começa antes desta fase.

### 5.1 — Estrutura mínima
Verificar existência de:
- `AGENTS.md`
- `CLAUDE.md`
- `.cursor/`
- `.cursor/rules/`
- `docs/prd/`

Se `.cursor/` ou `.cursor/rules/` não existir, criar antes de qualquer outra ação.

### 5.2 — Alinhamento documental obrigatório
Validar se `AGENTS.md`, `CLAUDE.md` e `.cursor/rules/` estão alinhados em:
- objetivo do sistema;
- topologia arquitetural;
- política de contexto;
- política de MCPs;
- política de segurança;
- política de PRD;
- política de validação;
- política de auditoria;
- política de regeneração documental.

### 5.3 — Internet
Validar acesso à internet quando a tarefa exigir web, documentação oficial, APIs, MCP remoto ou verificação externa.

### 5.4 — MCPs
Para cada MCP listado em `CLAUDE.md`, verificar obrigatoriamente:
- está configurado;
- está habilitado;
- está autenticado;
- está acessível;
- responde a uma operação mínima de leitura/listagem/teste;
- é compatível com a tarefa atual.

### 5.5 — Regime de uso obrigatório de MCP
Se houver MCP relevante para a tarefa, ele **deve ser usado**.

Exemplos:
- documentação de biblioteca → usar MCP documental antes de cair só em web;
- browser/Playwright → usar para validação visual quando aplicável;
- integrações internas → usar MCP de acesso se existir;
- observabilidade, tickets, docs, repositórios ou bases conectadas → usar MCP respectivo.

### 5.6 — Estado degradado
Se um MCP obrigatório falhar:
- registrar explicitamente **MODO DEGRADADO**;
- dizer qual MCP falhou;
- dizer que teste falhou;
- dizer o impacto concreto na tarefa;
- seguir apenas se a tarefa ainda puder ser concluída com segurança.

Se o MCP for crítico para a demanda, a tarefa deve ser marcada como **NÃO CONCLUÍDA**.

---

## 6. Política de completude de contexto

Antes de responder pergunta técnica, diagnosticar erro, alterar arquitetura, criar PRD, editar código, revisar implementação, regenerar documentação ou concluir qualquer tarefa técnica, o agente DEVE:

1. identificar os arquivos diretamente envolvidos no fluxo;
2. ler integralmente cada arquivo relevante, do início ao fim;
3. ler os contratos e dependências adjacentes do fluxo;
4. só então produzir diagnóstico, plano, código ou conclusão.

### Arquivos adjacentes obrigatórios quando aplicável
- `models`
- `forms`
- `serializers`
- `views`
- `services`
- `selectors`
- `tasks`
- `signals`
- `urls`
- `middleware`
- `templates`
- `static`
- `tests`
- `settings`
- documentação arquitetural
- PRDs
- regras locais
- arquivos de integração

### Proibições desta política
É proibido:
- decidir por grep quando o fluxo real depende do arquivo completo;
- decidir por snippets quando existe arquivo envolvido no fluxo;
- alterar código crítico sem ler contratos e testes adjacentes;
- responder arquitetura com base em fragmentos;
- declarar “já entendi” sem registrar o que foi efetivamente lido.

### Observação de enforcement
Markdown sozinho não garante enforcement duro. Portanto, esta política deve ser repetida em:
- `CLAUDE.md`;
- `.cursor/rules/`;
- hooks/checklists quando o ambiente permitir.

---

## 7. Context Ledger obrigatório

Toda demanda técnica relevante deve gerar um **Context Ledger** dentro do PRD, da resposta técnica ou do relatório final.

### Template obrigatório
```md
## Context Ledger
### Arquivos lidos integralmente
- caminho/arquivo_1
- caminho/arquivo_2

### Arquivos adjacentes consultados
- caminho/arquivo_3
- caminho/arquivo_4

### MCPs verificados
- nome_mcp — status — teste executado

### Fontes externas oficiais
- URL / doc / página

### Limitações encontradas
- ...
```

Sem Context Ledger em tarefa relevante, a tarefa não está pronta.

---

## 8. Classificação obrigatória da demanda

Toda demanda deve ser classificada antes de executar:
- pergunta exploratória;
- diagnóstico de erro;
- correção pontual;
- refatoração;
- alteração arquitetural;
- nova feature;
- integração externa;
- revisão de segurança;
- revisão de performance;
- revisão de governança do agente;
- regeneração documental;
- migração de domínio/app.

A classificação define profundidade de contexto, uso de MCP, PRD, testes, validação visual e regeneração documental.

---

## 9. Fluxo obrigatório de trabalho

1. validar estrutura e alinhamento documental;
2. validar internet;
3. validar MCPs;
4. classificar a demanda;
5. ler integralmente os arquivos do fluxo;
6. registrar Context Ledger;
7. criar ou atualizar PRD quando a demanda for relevante;
8. implementar ou analisar na ordem correta;
9. validar com evidências;
10. regenerar `AGENTS.md`, `CLAUDE.md` e `.cursor/rules/` quando necessário;
11. encerrar com status verdadeiro: concluída / concluída com limitações / não concluída.

---

## 10. PRD obrigatório

Criar ou atualizar:

`docs/prd/PRD-<NNN>-<slug>.md`

### Template obrigatório
```md
# PRD-<NNN>: <Título>

## Resumo

## Tipo de demanda
- pergunta / erro / correção / refatoração / feature / arquitetura / integração / auditoria / documentação

## Problema atual

## Objetivo

## Context Ledger
### Arquivos lidos integralmente
- ...

### Arquivos adjacentes consultados
- ...

### MCPs verificados
- ...

### Web / documentação oficial
- ...

### Limitações encontradas
- ...

## Apps / bounded contexts impactados

## Stack e integrações impactadas

## Dependências adicionadas ou alteradas

## Escopo

## Fora do escopo

## Riscos e edge cases

## Regras e restrições
- controle acima de performance
- leitura integral obrigatória
- MCP obrigatório quando aplicável
- validação server-side
- auditoria
- evidência obrigatória
- regeneração documental

## Critérios de aceite
- [ ] ...
- [ ] ...

## Plano
- [ ] 1. Preflight
- [ ] 2. Contexto e leitura integral
- [ ] 3. Contratos e modelagem
- [ ] 4. Implementação/análise
- [ ] 5. Testes
- [ ] 6. Validação
- [ ] 7. Regeneração documental

## Comandos de validação

## Evidências

## Implementado

## Desvios do plano

## Pendências
```

---

## 11. Estratégia de implementação padrão

Salvo justificativa explícita em PRD:

1. contexto e contratos;
2. modelagem/persistência;
3. validação de entrada (`forms` / `serializers`);
4. `services`;
5. `selectors`;
6. `tasks`;
7. `views` / endpoints;
8. `urls`;
9. `templates`;
10. `static`;
11. testes;
12. validação;
13. auditoria e regeneração documental.

---

## 12. Diretrizes concretas para Django

### Arquitetura
- monólito modular orientado a bounded contexts;
- cada app é um domínio autônomo;
- integração entre apps somente por contratos explícitos;
- sem import de `views`/`forms` entre apps;
- serviços concentram regra de negócio;
- views finas;
- selectors concentram leitura complexa.

### Persistência
- usar `transaction.atomic` em fluxos com múltiplas escritas;
- usar constraints quando apropriado;
- evitar N+1 com `select_related`/`prefetch_related`;
- evitar `.all()` sem paginação ou justificativa.

### Segurança
- segredos fora do código;
- `.env` obrigatório para credenciais;
- CSRF ativo;
- validação server-side obrigatória;
- auditoria para ações críticas;
- menor privilégio.

### Tasks e assíncrono
- usar tasks para trabalho assíncrono real;
- idempotência sempre que possível;
- observabilidade explícita;
- não acionar fila sem cobertura mínima dos fluxos críticos afetados.

---

## 13. Windows / PowerShell — baseline obrigatório

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Regras obrigatórias
- `&&` não é fluxo confiável em PowerShell; preferir um comando por vez ou `;`;
- `source` não existe; usar `\.venv\Scripts\Activate.ps1`;
- caminhos devem refletir ambiente Windows real;
- comandos do projeto devem preferir `\.venv\Scripts\python.exe`.

---

## 14. Execução real

- Executar comandos diretamente;
- Não criar scripts wrapper como fuga do protocolo, exceto se o próprio projeto exigir;
- Reportar comando, diretório, resultado e evidência;
- Não declarar sucesso sem execução observável quando a tarefa exigir execução.

---

## 15. Validação obrigatória

Nenhuma tarefa relevante é concluída sem validação.

Validar no mínimo, quando aplicável:
1. ambiente;
2. dependências;
3. integridade da `.venv`;
4. migrações;
5. testes;
6. MCPs usados;
7. terminal/logs;
8. console do navegador;
9. renderização visual;
10. segurança;
11. regressões;
12. alinhamento documental.

### Exemplos esperados em Django
- `manage.py test`
- `manage.py check`
- `manage.py check --deploy`
- `manage.py collectstatic --noinput`
- `manage.py showmigrations`
- verificações específicas do fluxo alterado

---

## 16. Matriz de conclusão

### CONCLUÍDA
Somente quando:
- contexto foi lido integralmente;
- MCPs relevantes foram testados e usados;
- PRD existe se a demanda exigir;
- validações foram executadas;
- evidências foram registradas;
- documentos estão alinhados.

### CONCLUÍDA COM LIMITAÇÕES
Somente quando:
- há limitação explícita registrada;
- a limitação não invalida a segurança nem a coerência central;
- o impacto está descrito.

### NÃO CONCLUÍDA
Quando houver:
- leitura incompleta do fluxo;
- MCP crítico indisponível;
- ausência de PRD em mudança relevante;
- validação não executada;
- ausência de evidência;
- documentação desalinhada;
- segurança comprometida;
- comportamento não auditável.

---

## 17. Regeneração documental obrigatória

Regenerar ou revisar `AGENTS.md`, `CLAUDE.md` e `.cursor/rules/` quando houver:
- nova convenção;
- mudança de stack;
- novo MCP;
- mudança arquitetural;
- novo domínio/app;
- novo fluxo operacional;
- lacuna de segurança descoberta;
- falha recorrente por instrução insuficiente;
- divergência entre documentos;
- alteração relevante implementada.

---

## 18. Proibições

É proibido:
- pular fases;
- ignorar MCP relevante;
- trabalhar sem Context Ledger;
- decidir por snippet quando o arquivo completo for relevante;
- declarar sucesso sem evidência;
- inventar comando, comportamento ou integração;
- hardcodar segredos;
- desabilitar CSRF sem justificativa formal;
- usar `except: pass`;
- misturar identidades técnicas e identidades de negócio sem desenho explícito;
- quebrar boundaries entre apps por conveniência;
- responder genericamente a problema específico do projeto.

---

## 19. Checklist final obrigatório

- [ ] `AGENTS.md` lido e respeitado
- [ ] `CLAUDE.md` lido e respeitado
- [ ] `.cursor/rules/` existe
- [ ] documentos alinhados
- [ ] internet validada quando necessária
- [ ] MCPs relevantes testados
- [ ] arquivos do fluxo lidos integralmente
- [ ] Context Ledger registrado
- [ ] PRD criado/atualizado quando aplicável
- [ ] contratos entre apps preservados
- [ ] validações executadas
- [ ] evidências registradas
- [ ] regeneração documental feita quando necessária
- [ ] status final verdadeiro informado

---

## 20. Fonte de verdade final

| Assunto | Fonte principal |
|---|---|
| Protocolo do agente | `AGENTS.md` |
| Contexto persistente do projeto | `CLAUDE.md` |
| Enforcement textual sempre ativo | `.cursor/rules/` |
| Enforcement determinístico | hooks / validações operacionais |
| Requisitos de mudança | PRDs |
| Verdade operacional | código, testes, logs, MCPs e evidências |
