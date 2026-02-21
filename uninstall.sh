#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de desinstalación
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash
# ---------------------------------------------------------------------------

set -euo pipefail

PLUGIN_NAME="alfred-dev"
CLAUDE_DIR="${HOME}/.claude"
PLUGINS_DIR="${CLAUDE_DIR}/plugins"
CACHE_DIR="${PLUGINS_DIR}/cache/${PLUGIN_NAME}"
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

# Validar que HOME apunta a un directorio real
if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no está definida o no apunta a un directorio válido"
    exit 1
fi

printf "\n${BOLD}Desinstalando Alfred Dev${NC}\n\n"

# Eliminar cache del plugin
if [ -d "${CACHE_DIR}" ]; then
    rm -rf "${CACHE_DIR}"
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

# Eliminar marketplace de known_marketplaces.json
if [ -f "${KNOWN_MARKETPLACES}" ]; then
    python3 - "${KNOWN_MARKETPLACES}" "${PLUGIN_NAME}" <<'PYEOF'
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
    ok "Marketplace eliminado de known_marketplaces.json"
fi

# Eliminar registro de installed_plugins.json
if [ -f "${INSTALLED_FILE}" ]; then
    python3 - "${INSTALLED_FILE}" "${PLUGIN_NAME}@${PLUGIN_NAME}" <<'PYEOF'
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
    ok "Registro eliminado de installed_plugins.json"
fi

# Deshabilitar en settings.json
if [ -f "${SETTINGS_FILE}" ]; then
    python3 - "${SETTINGS_FILE}" "${PLUGIN_NAME}@${PLUGIN_NAME}" <<'PYEOF'
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
    ok "Plugin deshabilitado en settings.json"
fi

printf "\n${GREEN}${BOLD}Alfred Dev desinstalado${NC}\n"
printf "  ${DIM}Reinicia Claude Code para aplicar los cambios.${NC}\n\n"
