# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code (Windows)
#
# Uso:
#   irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
#
# Que hace:
#   1. Registra el marketplace en known_marketplaces.json
#   2. Crea el directorio de marketplace con el catalogo del plugin
#   3. Clona el repositorio en la cache de plugins de Claude Code
#   4. Registra el plugin en installed_plugins.json
#   5. Habilita el plugin en settings.json
#   6. Listo para usar: /alfred help
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

# -- Validar entorno ----------------------------------------------------------

# Verificar que USERPROFILE apunta a un directorio real para evitar que
# las rutas derivadas (ClaudeDir, PluginsDir) apunten a ubicaciones inesperadas.
if (-not $env:USERPROFILE -or -not (Test-Path $env:USERPROFILE -PathType Container)) {
    Write-Host "x USERPROFILE no esta definido o no apunta a un directorio valido" -ForegroundColor Red
    exit 1
}

$Repo = "686f6c61/alfred-dev"
$PluginName = "alfred-dev"
$Version = "0.3.0"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$PluginsDir = Join-Path $ClaudeDir "plugins"
# La ruta de cache sigue la convencion de Claude Code: cache/<marketplace>/<plugin>/<version>.
# En nuestro caso marketplace y plugin comparten nombre, por lo que se repite.
$CacheDir = Join-Path $PluginsDir "cache" $PluginName $PluginName
$InstallDir = Join-Path $CacheDir $Version
$MarketplaceDir = Join-Path $PluginsDir "marketplaces" $PluginName
$InstalledFile = Join-Path $PluginsDir "installed_plugins.json"
$KnownMarketplaces = Join-Path $PluginsDir "known_marketplaces.json"
$SettingsFile = Join-Path $ClaudeDir "settings.json"

# -- Funciones auxiliares ---------------------------------------------------

function Write-Info  { param([string]$Msg) Write-Host ">" $Msg -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "+" $Msg -ForegroundColor Green }
function Write-Err   { param([string]$Msg) Write-Host "x" $Msg -ForegroundColor Red }

# Leer JSON de un fichero con manejo de errores
function Read-JsonFile {
    param([string]$Path, [string]$Default = '{}')
    if (-not (Test-Path $Path)) {
        return $Default | ConvertFrom-Json
    }
    try {
        $content = Get-Content $Path -Raw -Encoding UTF8
        return $content | ConvertFrom-Json
    }
    catch {
        Write-Err "El fichero '$Path' contiene JSON invalido: $_"
        throw
    }
}

# Escribir JSON de forma atomica (fichero temporal en mismo directorio + mover).
# Crear el temporal junto al destino garantiza que Move-Item sea un rename
# atomico del sistema de ficheros, sin copias entre discos.
function Write-JsonFileAtomic {
    param([string]$Path, [object]$Data)
    $targetDir = Split-Path $Path -Parent
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    $tmpFile = Join-Path $targetDir ".tmp-$([System.IO.Path]::GetRandomFileName())"
    try {
        $Data | ConvertTo-Json -Depth 10 | Set-Content $tmpFile -Encoding UTF8
        Move-Item -Path $tmpFile -Destination $Path -Force
    }
    catch {
        if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue }
        throw
    }
}

# -- Verificaciones ---------------------------------------------------------

if (-not (Test-Path $ClaudeDir)) {
    Write-Err "No se encontro el directorio $ClaudeDir"
    Write-Err "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Err "git no esta instalado"
    exit 1
}

# -- Directorio de plugins --------------------------------------------------

if (-not (Test-Path $PluginsDir)) {
    New-Item -ItemType Directory -Path $PluginsDir -Force | Out-Null
}

# -- Instalacion ------------------------------------------------------------

Write-Host ""
Write-Host "Alfred Dev" -ForegroundColor White -NoNewline
Write-Host " v$Version" -ForegroundColor DarkGray
Write-Host "Plugin de ingenieria de software automatizada" -ForegroundColor DarkGray
Write-Host ""

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.000Z")

# -- 1. Registrar marketplace en known_marketplaces.json --------------------

Write-Info "Registrando marketplace..."

$known = Read-JsonFile $KnownMarketplaces '{}'

# Construir la entrada del marketplace como hashtable y asignar
$marketplaceEntry = @{
    source = @{
        source = "github"
        repo   = $Repo
    }
    installLocation = $MarketplaceDir
    lastUpdated     = $Timestamp
}

# Anadir o sobreescribir la entrada
if ($known -is [PSCustomObject]) {
    if ($known.PSObject.Properties.Name -contains $PluginName) {
        $known.$PluginName = [PSCustomObject]$marketplaceEntry
    }
    else {
        $known | Add-Member -NotePropertyName $PluginName -NotePropertyValue ([PSCustomObject]$marketplaceEntry)
    }
}

Write-JsonFileAtomic $KnownMarketplaces $known
Write-Ok "Marketplace registrado en known_marketplaces.json"

# -- 2. Crear directorio de marketplace ------------------------------------

Write-Info "Configurando marketplace local..."

if (Test-Path $MarketplaceDir) {
    Remove-Item $MarketplaceDir -Recurse -Force
}

$marketplacePluginDir = Join-Path $MarketplaceDir ".claude-plugin"
New-Item -ItemType Directory -Path $marketplacePluginDir -Force | Out-Null

# Clonar en directorio temporal.
# El bloque try/finally garantiza la limpieza del temporal incluso si el
# script aborta por error o interrupcion (equivalente al trap EXIT de bash).
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "alfred-dev-install-$(Get-Random)"
try {
    git clone --quiet --depth 1 "https://github.com/$Repo.git" "$TempDir"

    # Verificar integridad del clone antes de continuar.
    # Si falta plugin.json el repositorio esta corrupto o incompleto.
    $pluginJsonCheck = Join-Path $TempDir ".claude-plugin" "plugin.json"
    if (-not (Test-Path $pluginJsonCheck)) {
        Write-Err "El repositorio clonado no contiene .claude-plugin/plugin.json"
        Write-Err "La clonacion puede estar corrupta. Reintenta la instalacion."
        exit 1
    }

    $GitSha = (git -C "$TempDir" rev-parse HEAD).Trim()

    # Copiar ficheros del plugin al marketplace
    Copy-Item (Join-Path $TempDir ".claude-plugin" "marketplace.json") $marketplacePluginDir -Force
    Copy-Item (Join-Path $TempDir ".claude-plugin" "plugin.json") $marketplacePluginDir -Force

    foreach ($dir in @("agents", "commands", "skills", "hooks", "core", "templates")) {
        $srcDir = Join-Path $TempDir $dir
        if (Test-Path $srcDir) {
            Copy-Item $srcDir (Join-Path $MarketplaceDir $dir) -Recurse -Force
        }
    }

    foreach ($file in @("README.md", "package.json", ".gitignore", "uninstall.sh", "uninstall.ps1")) {
        $srcFile = Join-Path $TempDir $file
        if (Test-Path $srcFile) {
            Copy-Item $srcFile $MarketplaceDir -Force
        }
    }

    Write-Ok "Marketplace configurado en $MarketplaceDir"

    # -- 3. Instalar plugin en cache -------------------------------------------

    Write-Info "Instalando plugin en cache..."

    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
    }

    if (-not (Test-Path $CacheDir)) {
        New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
    }

    Copy-Item "$TempDir" $InstallDir -Recurse -Force

    # Limpiar artefactos innecesarios para runtime
    foreach ($artifact in @(".git", "site", "install.sh", "install.ps1", "tests", ".pytest_cache")) {
        $target = Join-Path $InstallDir $artifact
        if (Test-Path $target) {
            Remove-Item $target -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
finally {
    # Limpiar directorio temporal pase lo que pase
    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-Item "$TempDir" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Eliminar versiones anteriores de la cache para que los usuarios siempre
# usen la version recien instalada.
Get-ChildItem -Path $CacheDir -Directory | Where-Object {
    $_.FullName -ne $InstallDir
} | ForEach-Object {
    Write-Info "Eliminando version anterior: $($_.Name)"
    Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Ok "Plugin instalado en $InstallDir"

# -- 4. Registrar en installed_plugins.json --------------------------------

Write-Info "Registrando plugin..."

$installed = Read-JsonFile $InstalledFile '{"version":2,"plugins":{}}'

# Asegurar estructura base
if (-not ($installed.PSObject.Properties.Name -contains 'version')) {
    $installed | Add-Member -NotePropertyName 'version' -NotePropertyValue 2
}
if (-not ($installed.PSObject.Properties.Name -contains 'plugins')) {
    $installed | Add-Member -NotePropertyName 'plugins' -NotePropertyValue ([PSCustomObject]@{})
}

$pluginKey = "$PluginName@$PluginName"
$pluginEntry = @(
    [PSCustomObject]@{
        scope        = "user"
        installPath  = $InstallDir
        version      = $Version
        installedAt  = $Timestamp
        lastUpdated  = $Timestamp
        gitCommitSha = $GitSha
    }
)

if ($installed.plugins.PSObject.Properties.Name -contains $pluginKey) {
    $installed.plugins.$pluginKey = $pluginEntry
}
else {
    $installed.plugins | Add-Member -NotePropertyName $pluginKey -NotePropertyValue $pluginEntry
}

Write-JsonFileAtomic $InstalledFile $installed
Write-Ok "Plugin registrado en installed_plugins.json"

# -- 5. Habilitar en settings.json -----------------------------------------

if (Test-Path $SettingsFile) {
    $settings = Read-JsonFile $SettingsFile '{}'

    if (-not ($settings.PSObject.Properties.Name -contains 'enabledPlugins')) {
        $settings | Add-Member -NotePropertyName 'enabledPlugins' -NotePropertyValue ([PSCustomObject]@{})
    }

    if ($settings.enabledPlugins.PSObject.Properties.Name -contains $pluginKey) {
        $settings.enabledPlugins.$pluginKey = $true
    }
    else {
        $settings.enabledPlugins | Add-Member -NotePropertyName $pluginKey -NotePropertyValue $true
    }

    Write-JsonFileAtomic $SettingsFile $settings
    Write-Ok "Plugin habilitado en settings.json"
}
else {
    Write-Info "No se encontro settings.json (se habilitara al iniciar Claude Code)"
}

# -- Resultado --------------------------------------------------------------

Write-Host ""
Write-Host "Instalacion completada" -ForegroundColor Green
Write-Host ""
Write-Host "  Reinicia Claude Code y ejecuta:"
Write-Host "  /alfred help" -ForegroundColor White
Write-Host ""
Write-Host "  Repositorio: https://github.com/$Repo" -ForegroundColor DarkGray
Write-Host "  Documentacion: https://686f6c61.github.io/alfred-dev/" -ForegroundColor DarkGray
Write-Host ""
