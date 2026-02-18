#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
#
# Que hace:
#   1. Registra el marketplace en known_marketplaces.json
#   2. Crea el directorio de marketplace con el catalogo del plugin
#   3. Clona el repositorio en la cache de plugins de Claude Code
#   4. Registra el plugin en installed_plugins.json
#   5. Habilita el plugin en settings.json
#   6. Listo para usar: /alfred help
# ---------------------------------------------------------------------------

set -euo pipefail

REPO="686f6c61/Claude-JARVIS-dev"
PLUGIN_NAME="alfred-dev"
VERSION="0.1.0"
CLAUDE_DIR="${HOME}/.claude"
PLUGINS_DIR="${CLAUDE_DIR}/plugins"
CACHE_DIR="${PLUGINS_DIR}/cache/${PLUGIN_NAME}"
INSTALL_DIR="${CACHE_DIR}/${VERSION}"
MARKETPLACE_DIR="${PLUGINS_DIR}/marketplaces/${PLUGIN_NAME}"
INSTALLED_FILE="${PLUGINS_DIR}/installed_plugins.json"
KNOWN_MARKETPLACES="${PLUGINS_DIR}/known_marketplaces.json"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"

# -- Colores ----------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

info()  { printf "${BLUE}>${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}+${NC} %s\n" "$1"; }
error() { printf "${RED}x${NC} %s\n" "$1" >&2; }

# -- Verificaciones ---------------------------------------------------------

if [ ! -d "${CLAUDE_DIR}" ]; then
    error "No se encontro el directorio ${CLAUDE_DIR}"
    error "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

if ! command -v git &>/dev/null; then
    error "git no esta instalado"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    error "python3 no esta instalado"
    exit 1
fi

# -- Instalacion ------------------------------------------------------------

printf "\n${BOLD}Alfred Dev${NC} ${DIM}v${VERSION}${NC}\n"
printf "${DIM}Plugin de ingenieria de software automatizada${NC}\n\n"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# -- 1. Registrar marketplace en known_marketplaces.json --------------------

info "Registrando marketplace..."

if [ ! -f "${KNOWN_MARKETPLACES}" ]; then
    echo '{}' > "${KNOWN_MARKETPLACES}"
fi

python3 -c "
import json

known_file = '${KNOWN_MARKETPLACES}'
marketplace_name = '${PLUGIN_NAME}'
marketplace_dir = '${MARKETPLACE_DIR}'
repo = '${REPO}'
timestamp = '${TIMESTAMP}'

with open(known_file, 'r') as f:
    data = json.load(f)

data[marketplace_name] = {
    'source': {
        'source': 'github',
        'repo': repo
    },
    'installLocation': marketplace_dir,
    'lastUpdated': timestamp
}

with open(known_file, 'w') as f:
    json.dump(data, f, indent=2)
"

ok "Marketplace registrado en known_marketplaces.json"

# -- 2. Crear directorio de marketplace ------------------------------------

info "Configurando marketplace local..."

if [ -d "${MARKETPLACE_DIR}" ]; then
    rm -rf "${MARKETPLACE_DIR}"
fi

mkdir -p "${MARKETPLACE_DIR}/.claude-plugin"

# Clonar en un directorio temporal para extraer los ficheros del marketplace
TEMP_DIR=$(mktemp -d)
git clone --quiet --depth 1 "https://github.com/${REPO}.git" "${TEMP_DIR}"

# Copiar la estructura completa del plugin al marketplace
cp -r "${TEMP_DIR}/.claude-plugin/marketplace.json" "${MARKETPLACE_DIR}/.claude-plugin/"
cp -r "${TEMP_DIR}/.claude-plugin/plugin.json" "${MARKETPLACE_DIR}/.claude-plugin/"
for dir in agents commands skills hooks core templates; do
    if [ -d "${TEMP_DIR}/${dir}" ]; then
        cp -r "${TEMP_DIR}/${dir}" "${MARKETPLACE_DIR}/"
    fi
done
for file in README.md package.json .gitignore uninstall.sh; do
    if [ -f "${TEMP_DIR}/${file}" ]; then
        cp "${TEMP_DIR}/${file}" "${MARKETPLACE_DIR}/"
    fi
done

ok "Marketplace configurado en ${MARKETPLACE_DIR}"

# -- 3. Instalar plugin en cache -------------------------------------------

info "Instalando plugin en cache..."

if [ -d "${INSTALL_DIR}" ]; then
    rm -rf "${INSTALL_DIR}"
fi

mkdir -p "${CACHE_DIR}"
cp -r "${TEMP_DIR}" "${INSTALL_DIR}"

# Limpiar artefactos innecesarios para runtime
rm -rf "${INSTALL_DIR}/.git" \
       "${INSTALL_DIR}/site" \
       "${INSTALL_DIR}/install.sh" \
       "${INSTALL_DIR}/tests" \
       "${INSTALL_DIR}/.pytest_cache" 2>/dev/null || true

# Limpiar directorio temporal
rm -rf "${TEMP_DIR}"

ok "Plugin instalado en ${INSTALL_DIR}"

# -- 4. Registrar en installed_plugins.json --------------------------------

info "Registrando plugin..."

if [ ! -f "${INSTALLED_FILE}" ]; then
    echo '{"version":2,"plugins":{}}' > "${INSTALLED_FILE}"
fi

python3 -c "
import json

installed_file = '${INSTALLED_FILE}'
plugin_key = '${PLUGIN_NAME}@${PLUGIN_NAME}'
install_path = '${INSTALL_DIR}'
version = '${VERSION}'
timestamp = '${TIMESTAMP}'

with open(installed_file, 'r') as f:
    data = json.load(f)

if 'plugins' not in data:
    data['plugins'] = {}

data['plugins'][plugin_key] = [{
    'scope': 'user',
    'installPath': install_path,
    'version': version,
    'installedAt': timestamp,
    'lastUpdated': timestamp
}]

with open(installed_file, 'w') as f:
    json.dump(data, f, indent=2)
"

ok "Plugin registrado en installed_plugins.json"

# -- 5. Habilitar en settings.json -----------------------------------------

if [ -f "${SETTINGS_FILE}" ]; then
    python3 -c "
import json

settings_file = '${SETTINGS_FILE}'
plugin_key = '${PLUGIN_NAME}@${PLUGIN_NAME}'

with open(settings_file, 'r') as f:
    data = json.load(f)

if 'enabledPlugins' not in data:
    data['enabledPlugins'] = {}

data['enabledPlugins'][plugin_key] = True

with open(settings_file, 'w') as f:
    json.dump(data, f, indent=2)
"
    ok "Plugin habilitado en settings.json"
else
    info "No se encontro settings.json (se habilitara al iniciar Claude Code)"
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalacion completada${NC}\n\n"
printf "  Reinicia Claude Code y ejecuta:\n"
printf "  ${BOLD}/alfred help${NC}\n\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Documentacion: https://686f6c61.github.io/Claude-JARVIS-dev/${NC}\n\n"
