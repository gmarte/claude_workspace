<#
.SYNOPSIS
  Despacha un brief de generación de imagen o video a un worker Gemini (Antigravity CLI `agy`) en modo headless.
.DESCRIPTION
  Misma técnica que C:\TEMP\pricing\plan\scripts\agentes\despachar.ps1 y C:\TEMP\intranet\scripts\agentes\despachar.ps1:
  el líder (Claude Code) escribe un brief Markdown, este script lo entrega a `agy -p --new-project` y valida que el
  worker imprimió la centinela y que el archivo de salida existe. No hay git ni worktrees: cada brief es independiente
  y escribe un único archivo bajo <OutDir>.

  `--new-project` es obligatorio: sin él agy ignora el cwd y escribe en el proyecto registrado.
  `--dangerously-skip-permissions` es obligatorio en headless: sin él agy auto-deniega las herramientas y no produce nada
  (mensaje "a tool required the command permission that headless mode cannot prompt for").

  Brief:   <BriefDir>\<ID>.md            (por defecto media\briefs\<ID>.md)
  Salida:  <OutDir>\<ID>\<archivo>       (el brief indica el nombre; el script comprueba que exista al menos un archivo)
  Log:     <OutDir>\logs\<ID>.log
  Centinela esperada en el log:  === MEDIA <ID> TERMINADA ===
.EXAMPLE
  .\despachar_media.ps1 -Prueba                     # humo: agy responde "ok"
  .\despachar_media.ps1 -Capacidades                # pregunta a agy qué herramientas de imagen/video tiene
  .\despachar_media.ps1 img-camion-almacen          # despacha media\briefs\img-camion-almacen.md
  .\despachar_media.ps1 img-camion-almacen -SoloPreparar
#>
param(
  [Parameter(Position = 0)][string]$Id,
  [switch]$Prueba,
  [switch]$Capacidades,
  [switch]$SoloPreparar,
  [string]$Root     = $(if ($env:MEDIA_ROOT)  { $env:MEDIA_ROOT }  else { (Get-Location).Path }),
  [string]$BriefDir = $(if ($env:MEDIA_BRIEFS) { $env:MEDIA_BRIEFS } else { 'media\briefs' }),
  [string]$OutDir   = $(if ($env:MEDIA_OUT)   { $env:MEDIA_OUT }   else { 'media\out' }),
  [string]$Modelo   = $(if ($env:AGY_MODEL)   { $env:AGY_MODEL }   else { 'gemini-3.8-flash-high' }),
  [string]$Timeout  = $(if ($env:AGY_TIMEOUT) { $env:AGY_TIMEOUT } else { '15m' })
)
$ErrorActionPreference = 'Stop'

if (-not (Get-Command agy -ErrorAction SilentlyContinue)) { throw 'No se encontró agy.exe en el PATH (Antigravity CLI).' }

if ($Prueba) {
  $salida = (& agy -p 'Responde unicamente con la palabra ok, sin puntuacion.' --model $Modelo --print-timeout 2m 2>&1 | Out-String).Trim()
  if ($salida -match '(?im)^ok$') { Write-Host "ok  (modelo $Modelo)"; exit 0 }
  Write-Host "FALLO: agy no respondio 'ok'. Salida:`n$salida"; exit 1
}

if ($Capacidades) {
  $q = 'Lista, una por linea y sin explicaciones, las herramientas de las que dispones para GENERAR o EDITAR imagenes o videos (por ejemplo generacion nativa de imagenes, Veo, Imagen, MCP). Si no tienes ninguna responde exactamente SIN_HERRAMIENTA_DE_MEDIA.'
  & agy -p $q --model $Modelo --dangerously-skip-permissions --new-project --print-timeout 3m 2>&1 | Out-String -Stream | ForEach-Object { Write-Host $_ }
  exit 0
}

if (-not $Id) { throw 'Falta el ID del brief (p. ej. img-camion-almacen) o usa -Prueba / -Capacidades' }

$slug   = $Id.ToLower()
$brief  = Join-Path (Join-Path $Root $BriefDir) "$slug.md"
if (-not (Test-Path $brief)) { throw "No existe el brief $brief" }
$outAbs = Join-Path (Join-Path $Root $OutDir) $slug
$logs   = Join-Path (Join-Path $Root $OutDir) 'logs'
New-Item -ItemType Directory -Force -Path $outAbs, $logs | Out-Null
$log = Join-Path $logs "$slug.log"

$sentinela = "=== MEDIA $Id TERMINADA ==="
$prompt = (Get-Content $brief -Raw) -replace '\{\{OUT_DIR\}\}', $outAbs -replace '\{\{ID\}\}', $Id
# agy.exe (Go) recibe argv re-tokenizado por Windows; las comillas dobles internas rompen el parseo si no se escapan.
$promptArg = $prompt -replace '"', '\"'

Write-Host "Brief    : $brief"
Write-Host "Salida   : $outAbs"
Write-Host "Modelo   : $Modelo   Timeout: $Timeout"
Write-Host "Log      : $log"
if ($SoloPreparar) {
  Write-Host 'Solo preparado. Para lanzar a mano:'
  Write-Host "  cd '$outAbs'; agy -p (Get-Content '$brief' -Raw) --model $Modelo --dangerously-skip-permissions --new-project --print-timeout $Timeout"
  exit 0
}

Write-Host "Lanzando agy... ($(Get-Date -Format 'HH:mm:ss'))"
Push-Location $outAbs
try {
  if (Test-Path $log) { Remove-Item $log -Force }
  & agy -p $promptArg --model $Modelo --dangerously-skip-permissions --new-project --print-timeout $Timeout 2>&1 |
    Out-String -Stream | ForEach-Object { Write-Host $_; Add-Content -Path $log -Value $_ -Encoding UTF8 }
  $codigo = $LASTEXITCODE
} finally { Pop-Location }

$terminado = (Select-String -Path $log -Pattern ([regex]::Escape($sentinela)) -Quiet)
$sinTool   = (Select-String -Path $log -Pattern 'SIN_HERRAMIENTA_DE_MEDIA' -Quiet)
$archivos  = @(Get-ChildItem -Path $outAbs -File -Include *.png,*.jpg,*.jpeg,*.webp,*.mp4,*.webm,*.gif -Recurse -ErrorAction SilentlyContinue)
Write-Host ''
Write-Host "agy termino con codigo $codigo a las $(Get-Date -Format 'HH:mm:ss'). Centinela: $(if ($terminado) { 'si' } else { 'NO' }). Archivos de media: $($archivos.Count)"
if ($sinTool) { Write-Host 'El worker reporto SIN_HERRAMIENTA_DE_MEDIA: usar el fallback (Higgsfield MCP) descrito en SKILL.md'; exit 3 }
if ($terminado -and $archivos.Count -gt 0) { $archivos | ForEach-Object { Write-Host "  -> $($_.FullName)" }; exit 0 } else { exit 2 }
