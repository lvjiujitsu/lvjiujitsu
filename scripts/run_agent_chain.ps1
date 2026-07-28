[CmdletBinding()]
param(
    [string]$Prefix = "lv",
    [switch]$IncludeRelease,
    [string]$Only
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root ".claude\logs"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$GhDir = "C:\Program Files\GitHub CLI"
if (Test-Path $GhDir -PathType Container) { $env:PATH = "$GhDir;$env:PATH" }

$Chain = @(
    @{ slug = "comments";       task = "Remova todo comentario e docstring deste repositorio e escreva a PRD." },
    @{ slug = "python";         task = "Revise e corrija o codigo Python deste repositorio e escreva a PRD." },
    @{ slug = "css";            task = "Audite e corrija o CSS deste repositorio, valide no browser e escreva a PRD." },
    @{ slug = "html";           task = "Revise os templates deste repositorio, valide no browser e escreva a PRD." },
    @{ slug = "django";         task = "Revise models, migrations, settings e seguranca deste repositorio e escreva a PRD." },
    @{ slug = "business";       task = "Verifique se o comportamento entregue bate com as PRDs e escreva os testes que faltam." },
    @{ slug = "cleancode";      task = "Ache codigo morto e duplicacao neste repositorio. So apague com prova de orfandade." },
    @{ slug = "e2e";            task = "Exercite o CRUD deste sistema no navegador de ponta a ponta e escreva a PRD." },
    @{ slug = "responsive";     task = "Confira todas as telas em celular, tablet e desktop, nos dois temas, e escreva a PRD." },
    @{ slug = "prd-review";     task = "Audite as PRDs concluidas e corrija o status do que foi marcado sem evidencia." },
    @{ slug = "second-opinion"; task = "Peca uma segunda opiniao ao Codex sobre o diff desta branch e confronte os pareceres." }
)

if ($IncludeRelease) {
    $Chain += @{ slug = "release"; task = "Crie a branch, commite, suba e abra o Pull Request com a descricao vinda das PRDs." }
}
if ($Only) {
    $Chain = $Chain | Where-Object { $_.slug -eq $Only }
    if (-not $Chain) { throw "Agente desconhecido: $Only" }
}

$Results = @()
foreach ($step in $Chain) {
    $agent = "$Prefix-agent-$($step.slug)"
    $log = Join-Path $LogDir "$Stamp-$($step.slug).log"
    Write-Host "==> $agent"

    $prompt = "Use o subagente $agent. Tarefa: $($step.task) Trabalhe apenas neste repositorio."
    $started = Get-Date

    & claude -p $prompt --permission-mode acceptEdits --output-format json 2>&1 |
        Tee-Object -FilePath $log | Out-Null
    $code = $LASTEXITCODE

    $Results += [pscustomobject]@{
        Agente   = $agent
        Saida    = $code
        Duracao  = [int]((Get-Date) - $started).TotalSeconds
        Log      = $log
    }
    Write-Host ("    exit={0}  {1}s  {2}" -f $code, [int]((Get-Date) - $started).TotalSeconds, $log)
}

Write-Host ""
$Results | Format-Table -AutoSize
$falhou = @($Results | Where-Object { $_.Saida -ne 0 })
$resumo = Join-Path $LogDir "$Stamp-resumo.json"
$Results | ConvertTo-Json -Depth 4 | Set-Content $resumo -Encoding UTF8

if ($falhou.Count) {
    Write-Host "$($falhou.Count) agente(s) falharam. Resumo em $resumo" -ForegroundColor Yellow
    exit 1
}
Write-Host "Cadeia completa sem falha. Resumo em $resumo" -ForegroundColor Green
exit 0
