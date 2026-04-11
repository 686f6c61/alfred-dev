# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code (Windows)
#
# Uso:
#   irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
#
# Que hace:
#   1. Verifica que Claude Code esta instalado
#   2. Registra globalmente en Claude Code la fuente GitHub del plugin
#   3. Instala el plugin con claude plugin install
#   4. Listo para usar: /alfred-dev:help
#
# El script delega toda la gestion en la CLI nativa de Claude Code
# (claude plugin marketplace / claude plugin install) para registrar una
# fuente GitHub personalizada, no oficial, y mantener compatibilidad futura.
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

$Repo = "686f6c61/alfred-dev"
$PluginName = "alfred-dev"
$Version = "0.5.2"

# -- Funciones auxiliares ---------------------------------------------------

function Write-Info  { param([string]$Msg) Write-Host ">" $Msg -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "+" $Msg -ForegroundColor Green }
function Write-Err   { param([string]$Msg) Write-Host "x" $Msg -ForegroundColor Red }

function Get-CompatiblePython {
    $candidates = @(
        @{ Display = "py -3.13"; Command = "py"; LauncherArg = "-3.13" },
        @{ Display = "py -3.12"; Command = "py"; LauncherArg = "-3.12" },
        @{ Display = "py -3.11"; Command = "py"; LauncherArg = "-3.11" },
        @{ Display = "py -3.10"; Command = "py"; LauncherArg = "-3.10" },
        @{ Display = "python3"; Command = "python3" },
        @{ Display = "python"; Command = "python" }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }

        try {
            $args = @()
            if ($candidate.ContainsKey("LauncherArg")) {
                $args += $candidate.LauncherArg
            }
            $args += @(
                "-c",
                'import sys; print(sys.executable); print("{}.{}".format(sys.version_info.major, sys.version_info.minor))'
            )

            $output = & $candidate.Command @args 2>$null
            if ($LASTEXITCODE -ne 0 -or $null -eq $output -or $output.Count -lt 2) {
                continue
            }

            $pythonPath = "$($output[0])".Trim()
            $version = "$($output[1])".Trim()
            $parts = $version -split '\.'
            if ($parts.Count -lt 2) {
                continue
            }

            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                return @{
                    DisplayCommand = $candidate.Display
                    ExecutablePath = $pythonPath
                    Version = $version
                }
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Write-TextFileAtomic {
    param([string]$Path, [string]$Content)
    $targetDir = Split-Path $Path -Parent
    $tmpFile = Join-Path $targetDir ".tmp-$([System.IO.Path]::GetRandomFileName())"
    try {
        [System.IO.File]::WriteAllText($tmpFile, $Content, [System.Text.Encoding]::UTF8)
        Move-Item -Path $tmpFile -Destination $Path -Force
    }
    catch {
        if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue }
        throw
    }
}

function Get-InstalledPluginRoot {
    param(
        [string]$ClaudeDir,
        [string]$PluginName,
        [string]$Version
    )

    $cacheDir = Join-Path $ClaudeDir "plugins/cache/$PluginName"
    $exact = Join-Path $cacheDir "$PluginName/$Version"
    $legacy = Join-Path $cacheDir $Version

    if (Test-Path $exact -PathType Container) { return $exact }
    if (Test-Path $legacy -PathType Container) { return $legacy }
    if (-not (Test-Path $cacheDir -PathType Container)) { return $null }

    $candidates = Get-ChildItem -Path $cacheDir -Filter plugin.json -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*\.claude-plugin\*" } |
        Sort-Object LastWriteTimeUtc -Descending

    foreach ($candidate in $candidates) {
        try {
            $data = (Get-Content $candidate.FullName -Raw -Encoding UTF8) | ConvertFrom-Json
        }
        catch {
            continue
        }

        if ($data.version -ne $Version) {
            continue
        }

        return Split-Path (Split-Path $candidate.FullName -Parent) -Parent
    }

    return $null
}

function Test-GlobalSourceRegistration {
    param(
        [string]$ClaudeDir,
        [string]$PluginName,
        [string]$Repo
    )

    $knownMarketplaces = Join-Path $ClaudeDir "plugins/known_marketplaces.json"
    if (-not (Test-Path $knownMarketplaces -PathType Leaf)) {
        return $false
    }

    try {
        $data = (Get-Content $knownMarketplaces -Raw -Encoding UTF8) | ConvertFrom-Json
    }
    catch {
        return $false
    }

    if (-not $data.PSObject.Properties.Name.Contains($PluginName)) {
        return $false
    }

    $entry = $data.$PluginName
    return $entry.source.source -eq "github" -and $entry.source.repo -eq $Repo
}

# -- Verificaciones ---------------------------------------------------------

$Python = Get-CompatiblePython
if ($null -eq $Python) {
    Write-Err "No se encontro Python 3.10 o superior"
    Write-Err "Se buscaron: py -3.13, py -3.12, py -3.11, py -3.10, python3, python"
    Write-Err "Alfred Dev necesita Python para hooks, core y MCP tambien en Windows"
    exit 1
}

Write-Ok "Python $($Python.Version) detectado ($($Python.DisplayCommand))"

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

# -- 1. Registrar fuente global en Claude Code ------------------------------

Write-Info "Registrando fuente GitHub global en Claude Code..."

$pluginKey = "$PluginName@$PluginName"
$pluginList = & claude plugin list 2>&1
if ($pluginList -match [regex]::Escape($pluginKey)) {
    & claude plugin uninstall $pluginKey 2>&1 | Out-Null
}

$marketplaceList = & claude plugin marketplace list 2>&1
if ($marketplaceList -match $PluginName) {
    & claude plugin marketplace remove $PluginName 2>&1 | Out-Null
}

$marketplaceResult = & claude plugin marketplace add $Repo 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Fuente GitHub declarada"
}
else {
    Write-Err "No se pudo registrar la fuente GitHub"
    Write-Err "Verifica tu conexion a internet y que el repositorio sea accesible:"
    Write-Err "  https://github.com/$Repo"
    exit 1
}

if (Test-GlobalSourceRegistration -ClaudeDir $ClaudeDir -PluginName $PluginName -Repo $Repo) {
    Write-Ok "Fuente GitHub registrada globalmente"
}
else {
    Write-Info "La CLI respondio OK, pero la fuente no quedo registrada; reintentando..."
    & claude plugin marketplace remove $PluginName 2>&1 | Out-Null
    $marketplaceResult = & claude plugin marketplace add $Repo 2>&1
    if ($LASTEXITCODE -eq 0 -and (Test-GlobalSourceRegistration -ClaudeDir $ClaudeDir -PluginName $PluginName -Repo $Repo)) {
        Write-Ok "Fuente GitHub registrada globalmente tras reintento"
    }
    else {
        Write-Err "Claude Code no dejo registrada la fuente global del plugin"
        Write-Err "Fichero esperado: $(Join-Path $ClaudeDir 'plugins/known_marketplaces.json')"
        Write-Err "Prueba a ejecutar manualmente:"
        Write-Err "  claude plugin marketplace remove $PluginName"
        Write-Err "  claude plugin marketplace add $Repo"
        exit 1
    }
}

# -- 2. Instalar plugin -----------------------------------------------------

Write-Info "Instalando plugin..."

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

# -- 3. Parchear hooks y MCP con el Python detectado -----------------------

$PluginRoot = Get-InstalledPluginRoot -ClaudeDir $ClaudeDir -PluginName $PluginName -Version $Version
$hooksJson = $null
$mcpJson = $null

if ($PluginRoot) {
    $hooksPath = Join-Path $PluginRoot "hooks/hooks.json"
    $mcpPath = Join-Path $PluginRoot ".claude-plugin/mcp.json"
    if (Test-Path $hooksPath -PathType Leaf) {
        $hooksJson = Get-Item $hooksPath
    }
    if (Test-Path $mcpPath -PathType Leaf) {
        $mcpJson = Get-Item $mcpPath
    }
}

if ($hooksJson) {
    $hooksData = (Get-Content $hooksJson.FullName -Raw -Encoding UTF8) | ConvertFrom-Json
    $patchedHooks = $false
    $quotedPython = '"' + $Python.ExecutablePath + '" ${CLAUDE_PLUGIN_ROOT}'

    foreach ($eventGroup in $hooksData.hooks.PSObject.Properties) {
        foreach ($matcher in $eventGroup.Value) {
            if (-not $matcher.hooks) { continue }
            foreach ($hook in $matcher.hooks) {
                if ($hook.type -ne 'command' -or -not $hook.command) { continue }
                if ($hook.command -notmatch 'python3 \$\{CLAUDE_PLUGIN_ROOT\}') { continue }
                $hook.command = $hook.command -replace 'python3 \$\{CLAUDE_PLUGIN_ROOT\}', $quotedPython
                $patchedHooks = $true
            }
        }
    }

    if ($patchedHooks) {
        Write-TextFileAtomic $hooksJson.FullName ($hooksData | ConvertTo-Json -Depth 20)
        Write-Ok "hooks.json parcheado para usar $($Python.ExecutablePath)"
    }
}
else {
    Write-Info "Aviso: no se encontro hooks.json en la instalacion activa para parchear Python"
}

if ($mcpJson) {
    $mcpData = (Get-Content $mcpJson.FullName -Raw -Encoding UTF8) | ConvertFrom-Json
    if ($mcpData.mcpServers.'alfred-memory'.command -ne $Python.ExecutablePath) {
        $mcpData.mcpServers.'alfred-memory'.command = $Python.ExecutablePath
        Write-TextFileAtomic $mcpJson.FullName ($mcpData | ConvertTo-Json -Depth 20)
        Write-Ok "mcp.json parcheado para usar $($Python.ExecutablePath)"
    }
}
else {
    Write-Info "Aviso: no se encontro mcp.json en la instalacion activa para parchear Python"
}

# -- Resultado --------------------------------------------------------------

Write-Host ""
Write-Host "Instalacion completada" -ForegroundColor Green
Write-Host ""
Write-Host "  Reinicia Claude Code y ejecuta:"
Write-Host "  /alfred-dev:help" -ForegroundColor White
Write-Host ""
Write-Host "  Repositorio: https://github.com/$Repo" -ForegroundColor DarkGray
Write-Host "  Documentacion: https://alfred-dev.com" -ForegroundColor DarkGray
Write-Host ""
