# Segurança

Verificar por fluxo:

- autenticação e expiração de sessão;
- autorização por objeto e por ação;
- CSRF em toda escrita;
- validação server-side e mass assignment;
- redirecionamento, enumeração e exposição de dados;
- XSS, uso de `safe`, `innerHTML` e interpolação de usuário;
- upload, nome, extensão, tipo, tamanho e armazenamento;
- SQL bruto, ORM inseguro e concorrência;
- mensagens de erro, logs e segredos;
- cookies, hosts, HTTPS e configurações de deploy;
- dependências conhecidamente vulneráveis em fontes primárias disponíveis.

Ler arquivos de ambiente somente quando o escopo exigir. Comparar nomes de chaves sem imprimir valores. Nunca copiar segredo para PRD, checkpoint, commit, log ou Pull Request.

Classificar como bloqueante falha explorável, perda de dados, quebra de autenticação ou permissão, indisponibilidade e migration destrutiva fora do ambiente autorizado.

Credencial deste projeto é descartável e não protege dado real (`CLAUDE.md` §1). Não versionar e não imprimir continuam obrigatórios; exigir rotação, abrir alerta de incidente ou condicionar a entrega a uma troca de chave, não. Credencial que o operador fornece na conversa é usada por variável de ambiente da sessão, sem alarme.
