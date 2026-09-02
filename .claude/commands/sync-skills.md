---
description: "Compara as seis skills do LV JIU JITSU nas duas plataformas (Claude e Codex) e reporta divergências sem sobrescrever."
disable-model-invocation: true
---

# /sync-skills

Compara sem sobrescrever. `.claude/skills/` é a **fonte de edição**;
`.agents/skills/` é o espelho e deve ser byte a byte idêntico a ela. A mesma regra está em `obsidian/projetos/lvjiujitsu/plataformas-agente-lvjiujitsu.md`; se os
dois divergirem, o adaptador vence e este comando é corrigido.

As seis skills existem nas duas plataformas. Ausência em qualquer uma é
divergência a corrigir, não exceção. `lv-prompt-builder` mantém
`disable-model-invocation: true`, que rege como o Claude a aciona e não
dispensa o espelho.

## Passos

```powershell
$skills = @(
  "lv-task-intake",
  "lv-prd",
  "lv-django-delivery",
  "lv-ui-delivery",
  "lv-cleanup-audit",
  "lv-prompt-builder"
)
foreach ($skill in $skills) {
  $claude = ".claude\skills\$skill\SKILL.md"
  $codex  = ".agents\skills\$skill\SKILL.md"
  if (!(Test-Path -LiteralPath $claude)) { Write-Output "$skill | claude AUSENTE"; continue }
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $claude).Hash
  $codexState  = if (!(Test-Path -LiteralPath $codex))  { "AUSENTE" } elseif ((Get-FileHash -Algorithm SHA256 -LiteralPath $codex).Hash  -eq $hash) { "idêntico" } else { "DIVERGENTE" }
  Write-Output "$skill | claude ok | codex $codexState"
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
Skill | Claude | Codex | openai.yaml
<uma linha por skill>
Divergências reais: <nenhuma | lista>
Direção de cópia sugerida: <pergunta ao operador; não aplicar sozinho>
```

## Parar quando

- Houver ausência ou divergência: reportar e parar sem sobrescrever; pedir ao
  operador qual cópia é a fonte antes de sincronizar.
- As seis skills forem idênticas nas duas plataformas e os seis
  `openai.yaml` estiverem íntegros: reportar sincronizado e encerrar.
