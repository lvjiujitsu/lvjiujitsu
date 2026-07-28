---
description: "Compara as sete skills do LV JIU JITSU nas três plataformas (Claude, Codex, Cursor) e reporta divergências sem sobrescrever."
disable-model-invocation: true
---

# /sync-skills

Compara sem sobrescrever. `.claude/skills/` é a **fonte de edição**;
`.agents/skills/` e `.cursor/skills/` são espelhos e devem ser byte a byte
idênticos a ela. A mesma regra está em `docs/PLATFORM-ADAPTERS.md`; se os
dois divergirem, o adaptador vence e este comando é corrigido.

As sete skills existem nas três plataformas. Ausência em qualquer uma é
divergência a corrigir, não exceção. `lv-prompt-builder` e `lv-parity-audit` mantêm
`disable-model-invocation: true`, que rege como o Claude as aciona e não
dispensa o espelho.

## Passos

```powershell
$skills = @(
  "lv-task-intake",
  "lv-prd",
  "lv-django-delivery",
  "lv-ui-delivery",
  "lv-cleanup-audit",
  "lv-prompt-builder",
  "lv-parity-audit"
)
foreach ($skill in $skills) {
  $claude = ".claude\skills\$skill\SKILL.md"
  $codex  = ".agents\skills\$skill\SKILL.md"
  $cursor = ".cursor\skills\$skill\SKILL.md"
  if (!(Test-Path -LiteralPath $claude)) { Write-Output "$skill | claude AUSENTE"; continue }
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $claude).Hash
  $codexState  = if (!(Test-Path -LiteralPath $codex))  { "AUSENTE" } elseif ((Get-FileHash -Algorithm SHA256 -LiteralPath $codex).Hash  -eq $hash) { "idêntico" } else { "DIVERGENTE" }
  $cursorState = if (!(Test-Path -LiteralPath $cursor)) { "AUSENTE" } elseif ((Get-FileHash -Algorithm SHA256 -LiteralPath $cursor).Hash -eq $hash) { "idêntico" } else { "DIVERGENTE" }
  Write-Output "$skill | claude ok | codex $codexState | cursor $cursorState"
}
```

Conferir também o metadado Codex de cada skill, que existe só em `.agents/`:

```powershell
foreach ($skill in $skills) {
  $yaml = ".agents\skills\$skill\agents\openai.yaml"
  if (!(Test-Path -LiteralPath $yaml)) { Write-Output "$skill | openai.yaml AUSENTE"; continue }
  $raw = [System.IO.File]::ReadAllText($yaml)
  $state = if ($raw.Contains([char]0xFFFD)) { "CORROMPIDO" } else { "ok" }
  Write-Output "$skill | openai.yaml $state"
}
```

Os sete `openai.yaml` já estiveram corrompidos por replacement character. A
checagem acima existe para que isso não volte silenciosamente.
`.gitattributes` fixa `*.yaml` em LF.

## Alternativa por script

O mesmo resultado, com a comparação de cobertura embutida:

```powershell
.\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
```

## Saída

```text
Skill | Claude | Codex | Cursor | openai.yaml
<uma linha por skill>
Divergências reais: <nenhuma | lista>
Direção de cópia sugerida: <pergunta ao operador; não aplicar sozinho>
```

## Parar quando

- Houver ausência ou divergência: reportar e parar sem sobrescrever; pedir ao
  operador qual cópia é a fonte antes de sincronizar.
- As sete skills forem idênticas nas três plataformas e os sete
  `openai.yaml` estiverem íntegros: reportar sincronizado e encerrar.
