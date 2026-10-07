# ─────────────────────────────────────────────────────────────────────────────
# gen-image.ps1 — motor de generacion/edicion de imagenes GRATIS via OpenAI Codex
# Usa el codex.exe que trae la app "OpenAI Codex" de la Microsoft Store + el login
# de ChatGPT (auth.json, modo ChatGPT, sin API key). ~30-60s por imagen.
#
# Salida (stdout, ultima linea):  RESULT_OK <ruta> <bytes>   |   RESULT_FAIL <motivo>
#
# GOTCHAS resueltos:
#   1) El prompt se pasa por STDIN ($prompt | & ...): da el EOF que codex necesita
#      (si no se cuelga) Y evita que el flag variadic -i (imagen) se coma el prompt.
#   2) En este Windows `sandbox="elevated"` -> nada de --approve-for-me (pide UAC y
#      cuelga); usamos --dangerously-bypass-approvals-and-sandbox (maquina propia).
# ─────────────────────────────────────────────────────────────────────────────
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Prompt,
  [Parameter(Mandatory=$true)][string]$Out,
  [string[]]$Ref = @(),        # imagenes de referencia/base para EDITAR
  [string]$Size = "",          # pista de lienzo: 1024x1024 / 1536x1024 / 1024x1536
  [string]$Model = "gpt-5.6-luna",           # modelo Codex a usar
  [ValidateSet("low","medium","high")]
  [string]$Reasoning = "low"                 # esfuerzo de razonamiento (bajo = rapido/barato)
)
$ErrorActionPreference = 'Stop'

function Find-Codex {
  $base = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
  if(-not (Test-Path $base)){ return $null }
  Get-ChildItem $base -Recurse -Filter 'codex.exe' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}

$cli = Find-Codex
if(-not $cli){
  Write-Output "RESULT_FAIL codex.exe no encontrado (instala/abre la app 'OpenAI Codex' de la Microsoft Store)"
  exit 3
}

# Normaliza rutas
if([System.IO.Path]::IsPathRooted($Out) -eq $false){ $Out = Join-Path (Get-Location).Path $Out }
$outDir = Split-Path -Parent $Out
if([string]::IsNullOrWhiteSpace($outDir)){ $outDir = (Get-Location).Path }
if(-not (Test-Path $outDir)){ New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
if(Test-Path $Out){ Remove-Item $Out -Force }

$lastmsg = Join-Path $env:TEMP ("codex-img-" + [guid]::NewGuid().ToString('N') + ".txt")

$sizeHint = if($Size){ " El lienzo debe medir aproximadamente $Size pixeles." } else { "" }
$refHint  = if($Ref.Count -gt 0){ " Usa la(s) imagen(es) adjunta(s) como base/referencia y aplica el cambio pedido." } else { "" }

$fullPrompt = @"
Usa tu herramienta interna de generacion de imagenes (image_gen) para producir esta imagen:
$Prompt
$refHint$sizeHint
Guarda el PNG resultante EXACTAMENTE en esta ruta absoluta (sobrescribe si ya existe): $Out
Cuando el archivo exista en disco, responde unicamente con la palabra DONE.
"@

$codexArgs = @('exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check',
  '-m', $Model,
  '-c', "model_reasoning_effort=`"$Reasoning`"",
  '-C', $outDir, '-o', $lastmsg)
foreach($r in $Ref){ if(Test-Path $r){ $codexArgs += @('-i', (Resolve-Path -LiteralPath $r).Path) } }
# OJO: el prompt NO va como argumento posicional. El flag -i es variadic y se lo
# comeria. Va por STDIN (abajo), que ademas aporta el EOF que codex exec necesita.

$start = Get-Date
# EAP=Continue: codex escribe avisos por stderr y con 'Stop' PowerShell abortaria.
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$fullPrompt | & $cli @codexArgs 2>&1 | Out-Null
$ErrorActionPreference = $prevEAP

# Fallback: si Codex genero pero no copio al destino, cogemos el PNG mas reciente
if(-not (Test-Path $Out)){
  $gen = Join-Path $env:USERPROFILE '.codex\generated_images'
  if(Test-Path $gen){
    $cand = Get-ChildItem $gen -Recurse -Filter *.png -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $start.AddSeconds(-5) } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if($cand){ Copy-Item -LiteralPath $cand.FullName -Destination $Out -Force }
  }
}

if(Test-Path $Out){
  $f = Get-Item $Out
  Write-Output ("RESULT_OK " + $f.FullName + " " + $f.Length)
  exit 0
} else {
  $tail = if(Test-Path $lastmsg){ (Get-Content $lastmsg -Raw) } else { "sin salida del modelo" }
  Write-Output ("RESULT_FAIL no se genero el PNG. Detalle: " + $tail)
  exit 1
}
