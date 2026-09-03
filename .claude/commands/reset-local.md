---
description: "Reconstrói o ambiente local do LV JIU JITSU com guardas, testes e seeds explícitas do projeto."
disable-model-invocation: true
---

# /reset-local

## Quando acionar

Por invocação manual para reconstruir o banco local descartável. A invocação
autoriza o reset e as seeds locais. Ler a sequência de domínio em
`obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md` antes de executar.

## Passos

1. Confirmar a raiz do projeto e o interpretador `.venv/Scripts/python.exe`.
2. Executar `python clear_migrations.py --check` com esse interpretador. O comando
   valida ambiente, credenciais de seed, contenção e plano de remoção sem apagar
   arquivos nem encerrar processos. Usa o mesmo carregamento do reset efetivo.
3. Executar `python manage.py check`. Resolver cada seed e seus argumentos no
   código e na nota de banco. Confirmar os arquivos de entrada antes da remoção.
   Variáveis de dados fictícios só são exigidas quando essas seeds forem pedidas.
4. Executar individualmente e parar no primeiro código de saída diferente de zero:
   `clear_migrations.py`, `manage.py makemigrations`, `manage.py test --verbosity 2`,
   `manage.py migrate` e `manage.py create_admin_superuser`.
5. Executar as seeds de domínio na ordem da nota de banco, uma por vez. A lista
   pertence ao vault; este comando não mantém uma segunda cópia. Dados fictícios
   só entram quando o objetivo pedir telas povoadas.
6. Executar `manage.py check`, `manage.py makemigrations --check --dry-run` e
   `manage.py showmigrations`. Registrar resultados e quantidades reais das seeds.
7. Para subir o servidor, confirmar que a porta 8000 está livre. Porta ocupada
   não comprova que o processo pertence a este repositório: informar o PID e
   parar se o caminho do executável ou do script não comprovar a origem.
8. Iniciar `manage.py runserver localhost:8000 --noreload` com o interpretador do
   projeto, `Start-Process -WindowStyle Hidden -PassThru`. Consultar `/health/`
   por até 15 segundos e registrar o PID e o status HTTP observado.

## Saída

Informar guardas, passo que falhou, migrations, seeds executadas, testes,
HTTP de `/health/` e PID. Nunca imprimir valores de ambiente.

## Parar quando

- Uma guarda ou comando falhar; antes do reset, nada deve ser apagado.
- A nota de banco ou um insumo obrigatório não estiver disponível.
- A porta pertencer a outro processo ou o HTTP não responder no prazo.
- A validação terminar: entregar a evidência real e o PID do servidor.
