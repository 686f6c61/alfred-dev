# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code (Windows)
#
# Uso:
#   irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
#
# Que hace:
#   1. Verifica que Claude Code esta instalado
#   2. Registra el marketplace del plugin con claude plugin marketplace add
#   3. Instala el plugin con claude plugin install
#   4. Listo para usar: /alfred help
#
# El script delega toda la gestion en la CLI nativa de Claude Code
# (claude plugin marketplace / claude plugin install) para garantizar
# compatibilidad con cualquier version futura de la herramienta.
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

$Repo = "686f6c61/alfred-dev"
$PluginName = "alfred-dev"
$Version = "0.3.3"

# -- Funciones auxiliares ---------------------------------------------------

function Write-Info  { param([string]$Msg) Write-Host ">" $Msg -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "+" $Msg -ForegroundColor Green }
function Write-Err   { param([string]$Msg) Write-Host "x" $Msg -ForegroundColor Red }

# -- Verificaciones ---------------------------------------------------------

if (-not $env:USERPROFILE -or -not (Test-Path $env:USERPROFILE -PathType Container)) {
    Write-Err "USERPROFILE no esta definido o no apunta a un directorio valido"
    exit 1
}

$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $ClaudeDir)) {
    Write-Err "No se encontro el directorio $ClaudeDir"
    Write-Err "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Err "El comando 'claude' no esta disponible en el PATH"
    Write-Err "Asegurate de tener Claude Code instalado y accesible desde la terminal"
    exit 1
}

# -- Instalacion ------------------------------------------------------------

Write-Host ""
Write-Host "Alfred Dev" -ForegroundColor White -NoNewline
Write-Host " v$Version" -ForegroundColor DarkGray
Write-Host "Plugin de ingenieria de software automatizada" -ForegroundColor DarkGray
Write-Host ""

# -- 1. Registrar marketplace -----------------------------------------------

Write-Info "Registrando marketplace..."

$marketplaceList = & claude plugin marketplace list 2>&1
if ($marketplaceList -match $PluginName) {
    & claude plugin marketplace remove $PluginName 2>&1 | Out-Null
}

$marketplaceResult = & claude plugin marketplace add $Repo 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Marketplace registrado"
}
else {
    Write-Err "No se pudo registrar el marketplace"
    Write-Err "Verifica tu conexion a internet y que el repositorio sea accesible:"
    Write-Err "  https://github.com/$Repo"
    exit 1
}

# -- 2. Instalar plugin -----------------------------------------------------

Write-Info "Instalando plugin..."

$pluginKey = "$PluginName@$PluginName"
$pluginList = & claude plugin list 2>&1
if ($pluginList -match $pluginKey) {
    & claude plugin uninstall $pluginKey 2>&1 | Out-Null
}

$installResult = & claude plugin install $pluginKey 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Plugin instalado y habilitado"
}
else {
    Write-Err "No se pudo instalar el plugin"
    Write-Err "Puedes intentar instalarlo manualmente:"
    Write-Err "  claude plugin marketplace add $Repo"
    Write-Err "  claude plugin install $pluginKey"
    exit 1
}

# -- Resultado --------------------------------------------------------------

Write-Host ""
Write-Host "Instalacion completada" -ForegroundColor Green
Write-Host ""
Write-Host "  Reinicia Claude Code y ejecuta:"
Write-Host "  /alfred help" -ForegroundColor White
Write-Host ""
Write-Host "  Repositorio: https://github.com/$Repo" -ForegroundColor DarkGray
Write-Host "  Documentacion: https://alfred-dev.com" -ForegroundColor DarkGray
Write-Host ""
