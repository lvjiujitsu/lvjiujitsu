Execute a validação completa do protocolo AGENTS.md para: $ARGUMENTS

Checklist obrigatório:

1. Testes: `manage.py test --verbosity 2` → 0 falhas, 0 erros
2. Check: `manage.py check` → sem erros
3. Estáticos: `manage.py collectstatic --noinput` (se aplicável)
4. Migrações: `manage.py showmigrations` → coerente com política
5. Shell checks via ORM (se tocar em persistência)
6. Visual via Playwright (se houver impacto em UI):
   - Abrir tela real na porta canônica
   - Validar fluxo crítico
   - Console do navegador sem erros JS
   - Desktop e mobile
7. Terminal sem stack traces
8. Qualidade: sem hardcode, sem except:pass, sem mascaramento

Reporte cada item com status ✅ ou ❌ e evidência.
