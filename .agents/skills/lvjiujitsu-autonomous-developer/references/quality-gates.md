# Quality gates

Usar apenas `requirements.txt` e a `.venv`. Não criar dependências paralelas.

## Cada correção

- demonstrar Red quando houver comportamento testável;
- implementar a causa raiz;
- executar teste focado e observar Green;
- revisar consumidores e regressões adjacentes;
- registrar comando, saída e arquivos na PRD.

## Lote

Derivar o interpretador e o ambiente local sem copiar arquivos ignorados:

```powershell
$gitCommon = [System.IO.Path]::GetFullPath((git rev-parse --git-common-dir))
$repoRoot = Split-Path $gitCommon -Parent
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$env:DJANGO_ENV_FILE = & $python -c "from clear_migrations import validate_local_environment; print(validate_local_environment())"
if ($LASTEXITCODE -ne 0) { throw 'Ambiente local indisponível.' }
& $python -m compileall -q lvjiujitsu system
& $python manage.py check
& $python manage.py showmigrations --plan
& $python manage.py makemigrations --check --dry-run
& $python manage.py collectstatic --noinput --dry-run
& $python manage.py test --verbosity 2
& $python -m pip check
& $python .agents\skills\lvjiujitsu-autonomous-developer\scripts\quality_scan.py --base origin/developer
git diff --check origin/developer...HEAD
```

Executar `quality_scan.py --all` antes de declarar a primeira auditoria global concluída.

Para UI, cumprir `ui-browser.md`. Para persistência, validar ORM, transações, migrations e seeds aplicáveis. Para segurança, cumprir `seguranca.md`.

Não publicar com gate falho, migration inesperada, segredo, comentário, docstring, arquivo fora das PRDs, teste removido sem equivalência, `staticfiles/` alterado ou evidência presumida.

## Suíte verde é pré-condição, sem exceção

`git_flow.py verify --path <worktree>` executa `manage.py check`, `makemigrations --check --dry-run` e a suíte completa dentro do worktree e grava um recibo amarrado ao SHA exato. `git_flow.py publish` recusa sem recibo verde para aquele SHA. Não existe caminho para publicar com a suíte vermelha.

Teste que já falhava antes da sua mudança **não é exceção**: é achado. Abra PRD, corrija na mesma feature e só então publique. "Não é regressão minha" descreve a origem do defeito, não autoriza entregá-lo. Um Pull Request que nasce vermelho gasta o CI, engana quem revisa e transfere ao operador um trabalho que era do ciclo.

Quando a correção depender de decisão de produto que você não pode tomar, encerre como bloqueado, com a PRD registrada e sem publicar. Parar é resultado aceitável; publicar vermelho não é.

Depois da publicação em `developer`, `.github/workflows/ci.yml` repete os
gates no Pull Request, com o job `quality-gates`. O PR permanece draft até
esse check concluir com sucesso no SHA exato. Revisor automático e preview
de banco não substituem esse check; indisponibilidade ou quota deles é
segunda opinião omitida, não pendência técnica do lote.
