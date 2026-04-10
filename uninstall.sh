#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de desinstalación
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash
#   bash ./uninstall.sh
#
# Estrategia:
#   1. Si Claude CLI está disponible, desinstalar el plugin y eliminar el
#      marketplace usando la vía nativa.
#   2. Limpiar cualquier resto físico en cache/ y marketplaces/.
#   3. Como red de seguridad, limpiar known_marketplaces.json,
#      installed_plugins.json y settings.json si todavía contienen rastros.
# ---------------------------------------------------------------------------

set -euo pipefail

PLUGIN_NAME="alfred-dev"
PLUGIN_KEY="${PLUGIN_NAME}@${PLUGIN_NAME}"
CLAUDE_DIR="${HOME}/.claude"
PLUGINS_DIR="${CLAUDE_DIR}/plugins"
MARKETPLACE_DIR="${PLUGINS_DIR}/marketplaces/${PLUGIN_NAME}"
INSTALLED_FILE="${PLUGINS_DIR}/installed_plugins.json"
KNOWN_MARKETPLACES="${PLUGINS_DIR}/known_marketplaces.json"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

info()  { printf "${BLUE}>${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}+${NC} %s\n" "$1"; }
error() { printf "${RED}x${NC} %s\n" "$1" >&2; }

find_compatible_python() {
    local candidate ver major minor

    for candidate in python3 python3.13 python3.12 python3.11 python3.10; do
        if ! command -v "$candidate" &>/dev/null; then
            continue
        fi
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 10 ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    for brew_path in /opt/homebrew/bin /usr/local/bin; do
        for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
            local full="${brew_path}/${candidate}"
            if [[ ! -x "$full" ]]; then
                continue
            fi
            ver=$("$full" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 10 ]]; then
                printf '%s\n' "$full"
                return 0
            fi
        done
    done

    return 1
}

# Validar que HOME apunta a un directorio real
if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no está definida o no apunta a un directorio válido"
    exit 1
fi

if [[ ! -d "${CLAUDE_DIR}" ]]; then
    info "No se encontró ${CLAUDE_DIR}; no hay instalación local que limpiar"
    exit 0
fi

printf "\n${BOLD}Desinstalando Alfred Dev${NC}\n\n"

# Intentar primero la vía canónica de Claude Code.
if command -v claude &>/dev/null; then
    info "Desinstalando plugin con Claude CLI..."
    claude plugin uninstall "${PLUGIN_KEY}" >/dev/null 2>&1 || true
    claude plugin marketplace remove "${PLUGIN_NAME}" >/dev/null 2>&1 || true
    ok "Claude CLI ha intentado desregistrar el plugin y el marketplace"
else
    info "El comando 'claude' no está disponible; se aplicará limpieza manual de seguridad"
fi

# Eliminar cache del plugin.
# Se borra el directorio completo del marketplace en caché (cache/alfred-dev/)
# para limpiar tanto instalaciones nuevas (cache/alfred-dev/alfred-dev/<version>)
# como antiguas (cache/alfred-dev/<version>) de forma uniforme.
CACHE_MARKETPLACE_DIR="${PLUGINS_DIR}/cache/${PLUGIN_NAME}"
if [ -d "${CACHE_MARKETPLACE_DIR}" ]; then
    rm -rf "${CACHE_MARKETPLACE_DIR}"
    ok "Cache del plugin eliminada"
else
    info "No se encontró cache del plugin"
fi

# Eliminar directorio de marketplace
if [ -d "${MARKETPLACE_DIR}" ]; then
    rm -rf "${MARKETPLACE_DIR}"
    ok "Directorio de marketplace eliminado"
else
    info "No se encontró directorio de marketplace"
fi

# Si no hay Python compatible, no podemos aplicar la limpieza residual de JSON.
PYTHON_CMD="$(find_compatible_python || true)"
if [[ -z "${PYTHON_CMD}" ]]; then
    info "No se encontro Python 3.10+; se omite la limpieza residual de ficheros JSON"
    printf "\n${GREEN}${BOLD}Alfred Dev desinstalado${NC}\n"
    printf "  ${DIM}Reinicia Claude Code para aplicar los cambios.${NC}\n\n"
    exit 0
fi

# Eliminar marketplace de known_marketplaces.json si aún quedara rastro.
if [ -f "${KNOWN_MARKETPLACES}" ]; then
    "${PYTHON_CMD}" - "${KNOWN_MARKETPLACES}" "${PLUGIN_NAME}" <<'PYEOF'
import json, os, sys, tempfile

known_file, marketplace_name = sys.argv[1:3]

try:
    with open(known_file, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: '{known_file}' contiene JSON inválido: {e}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"Error: no se pudo leer '{known_file}': {e}", file=sys.stderr)
    sys.exit(1)

if marketplace_name in data:
    del data[marketplace_name]

# Escritura atómica
try:
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(known_file))
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, known_file)
except OSError as e:
    print(f"Error: no se pudo escribir '{known_file}': {e}", file=sys.stderr)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    sys.exit(1)
PYEOF
    ok "Marketplace limpiado de known_marketplaces.json"
fi

# Eliminar registro de installed_plugins.json si aún quedara rastro.
if [ -f "${INSTALLED_FILE}" ]; then
    "${PYTHON_CMD}" - "${INSTALLED_FILE}" "${PLUGIN_KEY}" <<'PYEOF'
import json, os, sys, tempfile

installed_file, plugin_key = sys.argv[1:3]

try:
    with open(installed_file, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: '{installed_file}' contiene JSON inválido: {e}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"Error: no se pudo leer '{installed_file}': {e}", file=sys.stderr)
    sys.exit(1)

if plugin_key in data.get('plugins', {}):
    del data['plugins'][plugin_key]

# Escritura atómica
try:
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(installed_file))
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, installed_file)
except OSError as e:
    print(f"Error: no se pudo escribir '{installed_file}': {e}", file=sys.stderr)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    sys.exit(1)
PYEOF
    ok "Registro limpiado de installed_plugins.json"
fi

# Deshabilitar en settings.json si aún quedara rastro.
if [ -f "${SETTINGS_FILE}" ]; then
    "${PYTHON_CMD}" - "${SETTINGS_FILE}" "${PLUGIN_KEY}" <<'PYEOF'
import json, os, sys, tempfile

settings_file, plugin_key = sys.argv[1:3]

try:
    with open(settings_file, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: '{settings_file}' contiene JSON inválido: {e}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"Error: no se pudo leer '{settings_file}': {e}", file=sys.stderr)
    sys.exit(1)

if plugin_key in data.get('enabledPlugins', {}):
    del data['enabledPlugins'][plugin_key]

# Escritura atómica
try:
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(settings_file))
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, settings_file)
except OSError as e:
    print(f"Error: no se pudo escribir '{settings_file}': {e}", file=sys.stderr)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    sys.exit(1)
PYEOF
    ok "Plugin limpiado de settings.json"
else
    info "No se encontró settings.json (nada que deshabilitar)"
fi

printf "\n${GREEN}${BOLD}Alfred Dev desinstalado${NC}\n"
printf "  ${DIM}Reinicia Claude Code para aplicar los cambios.${NC}\n\n"
