# ---------------------------------------------------------------------------
# Alfred Dev -- script de desinstalacion (Windows)
#
# Uso:
#   irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

$PluginName = "alfred-dev"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$PluginsDir = Join-Path $ClaudeDir "plugins"
# La ruta de cache sigue la convencion de Claude Code: cache/<marketplace>/<plugin>/<version>.
# Se borra el directorio completo del marketplace para cubrir instalaciones viejas y nuevas.
$CacheDir = Join-Path $PluginsDir "cache" $PluginName
$MarketplaceDir = Join-Path $PluginsDir "marketplaces" $PluginName
$InstalledFile = Join-Path $PluginsDir "installed_plugins.json"
$KnownMarketplaces = Join-Path $PluginsDir "known_marketplaces.json"
$SettingsFile = Join-Path $ClaudeDir "settings.json"
$PluginKey = "$PluginName@$PluginName"

# -- Funciones auxiliares ---------------------------------------------------

function Write-Info  { param([string]$Msg) Write-Host ">" $Msg -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "+" $Msg -ForegroundColor Green }
function Write-Err   { param([string]$Msg) Write-Host "x" $Msg -ForegroundColor Red }

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        return (Get-Content $Path -Raw -Encoding UTF8) | ConvertFrom-Json
    }
    catch {
        Write-Err "El fichero '$Path' contiene JSON invalido: $_"
        throw
    }
}

function Write-JsonFileAtomic {
    param([string]$Path, [object]$Data)
    $tmpFile = [System.IO.Path]::GetTempFileName()
    try {
        $Data | ConvertTo-Json -Depth 10 | Set-Content $tmpFile -Encoding UTF8
        Move-Item -Path $tmpFile -Destination $Path -Force
    }
    catch {
        if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue }
        throw
    }
}

# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "Desinstalando Alfred Dev" -ForegroundColor White
Write-Host ""

# Eliminar cache del plugin
if (Test-Path $CacheDir) {
    Remove-Item $CacheDir -Recurse -Force
    Write-Ok "Cache del plugin eliminada"
}
else {
    Write-Info "No se encontro cache del plugin"
}

# Eliminar directorio de marketplace
if (Test-Path $MarketplaceDir) {
    Remove-Item $MarketplaceDir -Recurse -Force
    Write-Ok "Directorio de marketplace eliminado"
}
else {
    Write-Info "No se encontro directorio de marketplace"
}

# Eliminar marketplace de known_marketplaces.json
if (Test-Path $KnownMarketplaces) {
    $known = Read-JsonFile $KnownMarketplaces
    if ($null -ne $known -and $known.PSObject.Properties.Name -contains $PluginName) {
        $known.PSObject.Properties.Remove($PluginName)
        Write-JsonFileAtomic $KnownMarketplaces $known
        Write-Ok "Marketplace eliminado de known_marketplaces.json"
    }
}

# Eliminar registro de installed_plugins.json
if (Test-Path $InstalledFile) {
    $installed = Read-JsonFile $InstalledFile
    if ($null -ne $installed -and
        $installed.PSObject.Properties.Name -contains 'plugins' -and
        $installed.plugins.PSObject.Properties.Name -contains $PluginKey) {
        $installed.plugins.PSObject.Properties.Remove($PluginKey)
        Write-JsonFileAtomic $InstalledFile $installed
        Write-Ok "Registro eliminado de installed_plugins.json"
    }
}

# Deshabilitar en settings.json
if (Test-Path $SettingsFile) {
    $settings = Read-JsonFile $SettingsFile
    if ($null -ne $settings -and
        $settings.PSObject.Properties.Name -contains 'enabledPlugins' -and
        $settings.enabledPlugins.PSObject.Properties.Name -contains $PluginKey) {
        $settings.enabledPlugins.PSObject.Properties.Remove($PluginKey)
        Write-JsonFileAtomic $SettingsFile $settings
        Write-Ok "Plugin deshabilitado en settings.json"
    }
}

Write-Host ""
Write-Host "Alfred Dev desinstalado" -ForegroundColor Green
Write-Host "  Reinicia Claude Code para aplicar los cambios." -ForegroundColor DarkGray
Write-Host ""
