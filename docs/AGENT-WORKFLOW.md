# Fluxo operacional dos agentes

Este documento detalha o protocolo curto de `AGENTS.md`.

## 1. Ciclo

```text
Prompt
  -> classificação
  -> preflight
  -> leitura integral
  -> pesquisa oficial
  -> confirmação de entendimento
  -> autorização registrada pelo prompt
  -> PRD
  -> implementação
  -> validação proporcional
  -> auditoria de limpeza
  -> fechamento
```

Perguntas e diagnósticos sem escrita encerram após análise e evidência.

## 2. Classificação

Usar uma categoria principal:

- pergunta exploratória;
- diagnóstico;
- correção pontual;
- refatoração;
- nova feature;
- alteração arquitetural;
- integração externa;
- revisão de segurança;
- revisão de performance;
- revisão de governança;
- regeneração documental.

A classificação define arquivos adjacentes, PRD, validação e risco.

## 3. Preflight

Verificar conforme a demanda:

- alinhamento entre `AGENTS.md` e `CLAUDE.md`;
- worktree e mudanças preexistentes;
- PowerShell, `.venv` e interpretador;
- comandos reais;
- Context7, internet e browser;
- viabilidade de validação, ORM e gateway externo.

Mudanças existentes pertencem ao usuário e não podem ser revertidas.

## 4. Leitura

Antes de diagnosticar ou editar:

1. identificar arquivos diretos;
2. ler cada arquivo por inteiro;
3. ler contratos adjacentes;
4. registrar o ledger na PRD.

Busca textual localiza arquivos e pontos de entrada; não substitui leitura integral dos arquivos diretos.

Em Django, considerar models, forms, services, selectors, views, URLs, templates, CSS/JS, testes, settings, middleware, signals, tasks e management commands.

## 5. Pesquisa

Ordem:

1. Context7 para biblioteca, framework, SDK, API ou CLI;
2. documentação oficial atual;
3. fonte primária adicional quando necessária.

Toda PRD registra consulta, links, conclusão e limitações. Pesquisa irrelevante não preenche checklist.

## 6. Confirmação mínima

Antes de uma mudança ainda não autorizada pelo prompt:

```text
Entendi: <resultado>.
Escopo: <arquivos/fluxos>.
Validação: <browser, checks, testes e ORM local proporcionais>.
Posso implementar?
```

## 7. Autorizações

| Ação | Regra |
|---|---|
| Leitura, pesquisa e diagnóstico | implícita |
| Escrita solicitada com escopo claro | solicitação atual |
| Expansão material | nova aprovação |
| Implementação de UI | proposta aprovada |
| Teste local | autorizado para entrega operacional solicitada |
| ORM read-only | permitido quando necessário |
| ORM mutável local | autorizado quando necessário ao objetivo solicitado |
| Migration, migrate, reset local ou seed local | autorizado quando necessário ao objetivo solicitado |
| Pagamento externo real | autorização e ambiente operacional |
| Push ou deploy | autorização explícita |
| HG ou produção | confirmação explícita do ambiente antes de qualquer escrita |

## 8. SDD e TDD

- Criar PRD antes de mudança relevante.
- Escrever o teste do comportamento antes do código.
- Implementar o mínimo e refatorar.
- Executar testes locais proporcionais quando houver comportamento testável.
- Não declarar Red ou Green sem execução real.
- Registrar comando e resultado.

Testes Django usam banco de teste isolado. Reset + seeds é ciclo operacional local permitido quando necessário para primeira carga ou reconstrução.

## 9. Django

Ordem padrão:

1. contratos e invariantes;
2. forms;
3. services;
4. selectors;
5. views;
6. URLs;
7. templates;
8. static;
9. testes;
10. documentação.

Views permanecem finas. Múltiplas escritas usam transação. Queries relacionadas devem ser revisadas contra N+1.

## 10. UI

Antes do código:

- objetivo e comportamento preservado;
- hierarquia;
- wireframe;
- estados e erros;
- permissões;
- desktop e mobile.

Após implementar:

1. abrir a rota real na porta canônica;
2. validar caminho feliz e edge case;
3. inspecionar console e terminal;
4. validar desktop/mobile e temas;
5. registrar screenshot ou snapshot.

Para sessão autenticada, usar a superfície que mantenha a sessão. Headless não substitui browser interno quando ele está disponível.

## 11. Pagamentos

- Ler o fluxo completo e os documentos de Asaas/Stripe.
- Verificar settings e ambiente sem expor segredos.
- Separar redirect do browser, webhook server-to-server e confirmação no banco.
- Asaas local exige URL pública HTTPS válida.
- Stripe local pode exigir Stripe CLI e secret temporário.
- Não simular pagamento real por inferência nem declarar confirmação sem evidência do gateway e do ORM.

## 12. ORM

- Preferir read-only.
- Registrar comando e resultado.
- Criar dados locais somente quando fizer parte do objetivo ou da validação.
- Recuperação mutável deve ser explícita, idempotente e registrada.

## 13. Limpeza e fechamento

Revisar diff, fluxo e contratos adjacentes. Corrigir resíduos do escopo. Dívida material fora do escopo gera nova PRD e parada.

Fechamento:

```text
Implementado: ...
Evidências: ...
Não validado: ...
Pendências/desvios: ...
Status: concluída | concluída com limitações | não concluída
```
