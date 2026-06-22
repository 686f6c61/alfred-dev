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
#   4. Instala el alias personal global /alfred y elimina shims obsoletos
#   5. Listo para usar: /alfred
#
# El script delega toda la gestion en la CLI nativa de Claude Code
# (claude plugin marketplace / claude plugin install) para registrar una
# fuente GitHub personalizada, no oficial, y mantener compatibilidad futura.
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

$Repo = "686f6c61/alfred-dev"
$PluginName = "alfred-dev"
$Version = "0.6.1"

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

function Normalize-ToUserScopeInstallation {
    param(
        [string]$PluginName,
        [string]$PluginKey
    )

    # Alfred Dev solo soporta instalacion global de usuario. Si alguien lo
    # instalo antes en local/project, limpiamos ese rastro en el contexto actual
    # antes de reinstalar con --scope user.
    & claude plugin uninstall $PluginKey --scope local 2>&1 | Out-Null
    & claude plugin uninstall $PluginKey --scope project 2>&1 | Out-Null
    & claude plugin marketplace remove $PluginName --scope local 2>&1 | Out-Null
    & claude plugin marketplace remove $PluginName --scope project 2>&1 | Out-Null
    Write-Ok "Scopes local/project normalizados; Alfred se instalara como usuario global"
}

function Remove-StaleUserMarketplaceCheckout {
    param(
        [string]$ClaudeDir,
        [string]$PluginName
    )

    $marketplaceDir = Join-Path $ClaudeDir "plugins/marketplaces/$PluginName"
    if (Test-Path $marketplaceDir -PathType Container) {
        Remove-Item -Path $marketplaceDir -Recurse -Force
        Write-Ok "Checkout local del marketplace limpiado para evitar cache obsoleta"
    }
}

function Update-UserMarketplace {
    param([string]$PluginName)

    $updateResult = & claude plugin marketplace update $PluginName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Marketplace local actualizado"
    }
    else {
        Write-Info "No se pudo ejecutar 'claude plugin marketplace update'; continuo con el checkout recien registrado"
    }
}

function Install-GlobalAlfredAlias {
    param(
        [string]$ClaudeDir,
        [string]$PluginRoot
    )

    if (-not $PluginRoot) {
        Write-Err "No se pudo resolver la raiz del plugin instalado para crear /alfred"
        exit 1
    }

    $sourceAlias = Join-Path $PluginRoot "skills/alfred/alfred/SKILL.md"
    if (-not (Test-Path $sourceAlias -PathType Leaf)) {
        Write-Err "No se encontro el skill de alias global en la instalacion:"
        Write-Err "  $sourceAlias"
        exit 1
    }

    $aliasDir = Join-Path $ClaudeDir "skills/alfred"
    $aliasFile = Join-Path $aliasDir "SKILL.md"
    $commandAliasDir = Join-Path $ClaudeDir "commands"
    $commandAliasFile = Join-Path $commandAliasDir "alfred.md"
    New-Item -ItemType Directory -Path $aliasDir -Force | Out-Null

    function Write-AlfredAlias {
        param(
            [string]$Source,
            [string]$Target,
            [bool]$Invocable
        )

        $content = Get-Content $Source -Raw -Encoding UTF8
        $value = if ($Invocable) { "true" } else { "false" }
        if ($content -match '(?m)^user-invocable:\s*(true|false)\s*$') {
            $content = [regex]::Replace(
                $content,
                '(?m)^user-invocable:\s*(true|false)\s*$',
                "user-invocable: $value",
                1
            )
        }
        elseif ($content.StartsWith("---`n")) {
            $content = "---`nuser-invocable: $value`n" + $content.Substring(4)
        }

        Write-TextFileAtomic -Path $Target -Content $content
    }

    if (Test-Path $aliasFile -PathType Leaf) {
        $existing = Get-Content $aliasFile -Raw -Encoding UTF8
        if ($existing -notmatch "Alfred Dev global alias") {
            $backup = "$aliasFile.before-alfred-dev.$(Get-Date -Format 'yyyyMMddHHmmss')"
            Copy-Item $aliasFile $backup -Force
            Write-Info "Skill /alfred existente respaldado en $backup"
        }
    }

    Write-AlfredAlias -Source $sourceAlias -Target $aliasFile -Invocable $true
    Write-Ok "Alias global /alfred instalado en $aliasFile"

    if (Test-Path $commandAliasFile -PathType Leaf) {
        $existing = Get-Content $commandAliasFile -Raw -Encoding UTF8
        if ($existing -match "Alfred Dev global alias") {
            Remove-Item $commandAliasFile -Force
            Write-Ok "Shim de comando global /alfred obsoleto eliminado en $commandAliasFile"
        }
        else {
            $backup = "$commandAliasFile.before-alfred-dev.$(Get-Date -Format 'yyyyMMddHHmmss')"
            Move-Item $commandAliasFile $backup -Force
            Write-Info "Comando /alfred existente movido a $backup para evitar duplicados"
        }
    }
}

function Assert-UserScopeInstallation {
    param([string]$PluginKey)

    $pluginListJson = & claude plugin list --json 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "No se pudo confirmar el scope global con 'claude plugin list --json'"
        Write-Err "Alfred Dev debe quedar instalado como scope user."
        exit 1
    }

    try {
        $entries = @(($pluginListJson | Out-String) | ConvertFrom-Json)
    }
    catch {
        Write-Err "JSON invalido en claude plugin list --json: $_"
        exit 1
    }

    $matches = @($entries | Where-Object { $_.id -eq $PluginKey })
    if ($matches.Count -eq 0) {
        Write-Err "No aparece $PluginKey en claude plugin list --json"
        exit 1
    }

    $activeNonUser = @($matches | Where-Object { $_.enabled -eq $true -and $_.scope -ne "user" })
    if ($activeNonUser.Count -gt 0) {
        $details = @($activeNonUser | ForEach-Object {
            "scope=$($_.scope) projectPath=$($_.projectPath)"
        }) -join ", "
        Write-Err "Hay instalaciones activas no globales de ${PluginKey}: $details"
        exit 1
    }

    $enabledUser = @($matches | Where-Object { $_.enabled -eq $true -and $_.scope -eq "user" })
    if ($enabledUser.Count -eq 0) {
        $scopes = @($matches | ForEach-Object { "$($_.scope)" }) -join ", "
        Write-Err "$PluginKey existe, pero no hay entrada enabled con scope user. Scopes vistos: $scopes"
        exit 1
    }

    $staleNonUser = @($matches | Where-Object { $_.enabled -ne $true -and $_.scope -ne "user" })
    if ($staleNonUser.Count -gt 0) {
        $details = @($staleNonUser | ForEach-Object {
            "scope=$($_.scope) projectPath=$($_.projectPath)"
        }) -join ", "
        Write-Info "AVISO: quedan entradas antiguas no activas de ${PluginKey}: $details"
    }

    Write-Ok "Instalacion global de usuario confirmada (--scope user)"
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
    Write-Err "Asegurate de tener Claude Code instalado: https://code.claude.com/docs/en/setup"
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
Normalize-ToUserScopeInstallation -PluginName $PluginName -PluginKey $pluginKey

$pluginList = & claude plugin list 2>&1
if ($pluginList -match [regex]::Escape($pluginKey)) {
    & claude plugin uninstall $pluginKey --scope user 2>&1 | Out-Null
}

$marketplaceList = & claude plugin marketplace list 2>&1
if ($marketplaceList -match $PluginName) {
    & claude plugin marketplace remove $PluginName --scope user 2>&1 | Out-Null
}
Remove-StaleUserMarketplaceCheckout -ClaudeDir $ClaudeDir -PluginName $PluginName

$marketplaceResult = & claude plugin marketplace add $Repo --scope user 2>&1
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
    & claude plugin marketplace remove $PluginName --scope user 2>&1 | Out-Null
    $marketplaceResult = & claude plugin marketplace add $Repo --scope user 2>&1
    if ($LASTEXITCODE -eq 0 -and (Test-GlobalSourceRegistration -ClaudeDir $ClaudeDir -PluginName $PluginName -Repo $Repo)) {
        Write-Ok "Fuente GitHub registrada globalmente tras reintento"
    }
    else {
        Write-Err "Claude Code no dejo registrada la fuente global del plugin"
        Write-Err "Fichero esperado: $(Join-Path $ClaudeDir 'plugins/known_marketplaces.json')"
        Write-Err "Prueba a ejecutar manualmente:"
        Write-Err "  claude plugin marketplace remove $PluginName --scope user"
        Write-Err "  claude plugin marketplace add $Repo --scope user"
        exit 1
    }
}

Update-UserMarketplace -PluginName $PluginName

# -- 2. Instalar plugin -----------------------------------------------------

Write-Info "Instalando plugin..."

$installResult = & claude plugin install $pluginKey --scope user 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Plugin instalado y habilitado"
}
else {
    Write-Err "No se pudo instalar el plugin"
    Write-Err "Puedes intentar instalarlo manualmente:"
    Write-Err "  claude plugin marketplace add $Repo --scope user"
    Write-Err "  claude plugin install $pluginKey --scope user"
    exit 1
}

# -- 3. Parchear hooks y MCP con el Python detectado -----------------------

$PluginRoot = Get-InstalledPluginRoot -ClaudeDir $ClaudeDir -PluginName $PluginName -Version $Version
$hooksJson = $null
$mcpJson = $null

Install-GlobalAlfredAlias -ClaudeDir $ClaudeDir -PluginRoot $PluginRoot
Assert-UserScopeInstallation -PluginKey $pluginKey

if ($PluginRoot) {
    $hooksPath = Join-Path $PluginRoot "hooks/hooks.json"
    $mcpPath = Join-Path $PluginRoot ".mcp.json"
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
                if ($hook.command -eq 'python3') {
                    $hook.command = $Python.ExecutablePath
                    $patchedHooks = $true
                    continue
                }
                if ($hook.command -match 'python3 \$\{CLAUDE_PLUGIN_ROOT\}') {
                    $hook.command = $hook.command -replace 'python3 \$\{CLAUDE_PLUGIN_ROOT\}', $quotedPython
                    $patchedHooks = $true
                }
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
    $mcpServers = $mcpData
    if ($mcpData.PSObject.Properties.Name.Contains("mcpServers")) {
        $mcpServers = $mcpData.mcpServers
    }
    if ($mcpServers.'alfred-memory'.command -ne $Python.ExecutablePath) {
        $mcpServers.'alfred-memory'.command = $Python.ExecutablePath
        Write-TextFileAtomic $mcpJson.FullName ($mcpData | ConvertTo-Json -Depth 20)
        Write-Ok ".mcp.json parcheado para usar $($Python.ExecutablePath)"
    }
}
else {
    Write-Info "Aviso: no se encontro .mcp.json en la instalacion activa para parchear Python"
}

# -- Resultado --------------------------------------------------------------

Write-Host ""
Write-Host "Instalacion completada" -ForegroundColor Green
Write-Host ""
Write-Host "  En Claude Code, ejecuta /reload-plugins y despues:"
Write-Host "  /alfred" -ForegroundColor White
Write-Host "  Ayuda completa: /alfred-dev:help" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Si /reload-plugins avisa por MCP/coste de cache o no aparece el plugin, reinicia Claude Code." -ForegroundColor DarkGray
Write-Host "  Repositorio: https://github.com/$Repo" -ForegroundColor DarkGray
Write-Host "  Documentacion: https://alfred-dev.com" -ForegroundColor DarkGray
Write-Host ""
