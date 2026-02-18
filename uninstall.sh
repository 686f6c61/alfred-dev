#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de desinstalacion
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/uninstall.sh | bash
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

printf "\n${BOLD}Desinstalando Alfred Dev${NC}\n\n"

# Eliminar cache del plugin
if [ -d "${CACHE_DIR}" ]; then
    rm -rf "${CACHE_DIR}"
    ok "Cache del plugin eliminada"
else
    info "No se encontro cache del plugin"
fi

# Eliminar directorio de marketplace
if [ -d "${MARKETPLACE_DIR}" ]; then
    rm -rf "${MARKETPLACE_DIR}"
    ok "Directorio de marketplace eliminado"
else
    info "No se encontro directorio de marketplace"
fi

# Eliminar marketplace de known_marketplaces.json
if [ -f "${KNOWN_MARKETPLACES}" ]; then
    python3 -c "
import json
known_file = '${KNOWN_MARKETPLACES}'
marketplace_name = '${PLUGIN_NAME}'
with open(known_file, 'r') as f:
    data = json.load(f)
if marketplace_name in data:
    del data[marketplace_name]
with open(known_file, 'w') as f:
    json.dump(data, f, indent=2)
"
    ok "Marketplace eliminado de known_marketplaces.json"
fi

# Eliminar registro de installed_plugins.json
if [ -f "${INSTALLED_FILE}" ]; then
    python3 -c "
import json
installed_file = '${INSTALLED_FILE}'
plugin_key = '${PLUGIN_NAME}@${PLUGIN_NAME}'
with open(installed_file, 'r') as f:
    data = json.load(f)
if plugin_key in data.get('plugins', {}):
    del data['plugins'][plugin_key]
with open(installed_file, 'w') as f:
    json.dump(data, f, indent=2)
"
    ok "Registro eliminado de installed_plugins.json"
fi

# Deshabilitar en settings.json
if [ -f "${SETTINGS_FILE}" ]; then
    python3 -c "
import json
settings_file = '${SETTINGS_FILE}'
plugin_key = '${PLUGIN_NAME}@${PLUGIN_NAME}'
with open(settings_file, 'r') as f:
    data = json.load(f)
if plugin_key in data.get('enabledPlugins', {}):
    del data['enabledPlugins'][plugin_key]
with open(settings_file, 'w') as f:
    json.dump(data, f, indent=2)
"
    ok "Plugin deshabilitado en settings.json"
fi

printf "\n${GREEN}${BOLD}Alfred Dev desinstalado${NC}\n"
printf "  ${DIM}Reinicia Claude Code para aplicar los cambios.${NC}\n\n"
