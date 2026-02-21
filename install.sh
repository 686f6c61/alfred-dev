#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalación para Claude Code
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
#
# Qué hace:
#   1. Registra el marketplace en known_marketplaces.json
#   2. Crea el directorio de marketplace con el catálogo del plugin
#   3. Clona el repositorio en la cache de plugins de Claude Code
#   4. Registra el plugin en installed_plugins.json
#   5. Habilita el plugin en settings.json
#   6. Listo para usar: /alfred help
# ---------------------------------------------------------------------------

set -euo pipefail

REPO="686f6c61/alfred-dev"
PLUGIN_NAME="alfred-dev"
VERSION="0.2.1"
CLAUDE_DIR="${HOME}/.claude"
PLUGINS_DIR="${CLAUDE_DIR}/plugins"
# La ruta de caché sigue la convención de Claude Code: cache/<marketplace>/<plugin>/<version>.
# En nuestro caso marketplace y plugin comparten nombre, por lo que se repite.
CACHE_DIR="${PLUGINS_DIR}/cache/${PLUGIN_NAME}/${PLUGIN_NAME}"
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

# Validar que HOME apunta a un directorio real para evitar que las rutas
# derivadas (CLAUDE_DIR, PLUGINS_DIR) apunten a ubicaciones inesperadas.
if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no está definida o no apunta a un directorio válido"
    exit 1
fi

if [ ! -d "${CLAUDE_DIR}" ]; then
    error "No se encontró el directorio ${CLAUDE_DIR}"
    error "Asegúrate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

if ! command -v git &>/dev/null; then
    error "git no está instalado"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    error "python3 no está instalado"
    exit 1
fi

# Asegurar que el directorio de plugins existe.
# En instalaciones limpias (sin ningun plugin previo) podria no existir.
mkdir -p "${PLUGINS_DIR}"

# -- Limpieza automática en caso de interrupción ---------------------------

# TEMP_DIR se asigna más adelante; el trap limpia si el script aborta
# por error, SIGINT o cualquier otro motivo antes de terminar.
TEMP_DIR=""
cleanup() {
    if [[ -n "${TEMP_DIR}" ]] && [[ -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi
}
trap cleanup EXIT

# -- Instalación ------------------------------------------------------------

printf "\n${BOLD}Alfred Dev${NC} ${DIM}v${VERSION}${NC}\n"
printf "${DIM}Plugin de ingeniería de software automatizada${NC}\n\n"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# -- 1. Registrar marketplace en known_marketplaces.json --------------------

info "Registrando marketplace..."

if [ ! -f "${KNOWN_MARKETPLACES}" ]; then
    echo '{}' > "${KNOWN_MARKETPLACES}"
fi

python3 - "${KNOWN_MARKETPLACES}" "${PLUGIN_NAME}" "${MARKETPLACE_DIR}" "${REPO}" "${TIMESTAMP}" <<'PYEOF'
import json, os, sys, tempfile

known_file, marketplace_name, marketplace_dir, repo, timestamp = sys.argv[1:6]

try:
    with open(known_file, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: '{known_file}' contiene JSON inválido: {e}", file=sys.stderr)
    print(f"Puedes restaurarlo con: echo '{{}}' > {known_file}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"Error: no se pudo leer '{known_file}': {e}", file=sys.stderr)
    sys.exit(1)

data[marketplace_name] = {
    'source': {
        'source': 'github',
        'repo': repo
    },
    'installLocation': marketplace_dir,
    'lastUpdated': timestamp
}

# Escritura atómica: fichero temporal + rename
try:
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(known_file))
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, known_file)
except OSError as e:
    print(f"Error: no se pudo escribir '{known_file}': {e}", file=sys.stderr)
    # Limpiar temporal huérfano
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    sys.exit(1)
PYEOF

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
GIT_SHA=$(git -C "${TEMP_DIR}" rev-parse HEAD)

# Copiar la estructura completa del plugin al marketplace
cp -r "${TEMP_DIR}/.claude-plugin/marketplace.json" "${MARKETPLACE_DIR}/.claude-plugin/"
cp -r "${TEMP_DIR}/.claude-plugin/plugin.json" "${MARKETPLACE_DIR}/.claude-plugin/"
for dir in agents commands skills hooks core templates; do
    if [ -d "${TEMP_DIR}/${dir}" ]; then
        cp -r "${TEMP_DIR}/${dir}" "${MARKETPLACE_DIR}/"
    fi
done
for file in README.md package.json .gitignore uninstall.sh uninstall.ps1; do
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

# Limpiar artefactos innecesarios para runtime.
# Se comprueba existencia antes de borrar para detectar rutas inesperadas.
for artifact in .git site install.sh tests .pytest_cache; do
    target="${INSTALL_DIR}/${artifact}"
    if [ -e "${target}" ]; then
        rm -rf "${target}" || echo "[Alfred Dev] Aviso: no se pudo eliminar ${target}" >&2
    fi
done

# El trap cleanup EXIT se encarga de TEMP_DIR si el script falla antes,
# pero en el camino feliz lo limpiamos aquí para no esperar al exit.
rm -rf "${TEMP_DIR}"
TEMP_DIR=""

ok "Plugin instalado en ${INSTALL_DIR}"

# -- 4. Registrar en installed_plugins.json --------------------------------

info "Registrando plugin..."

if [ ! -f "${INSTALLED_FILE}" ]; then
    echo '{"version":2,"plugins":{}}' > "${INSTALLED_FILE}"
fi

python3 - "${INSTALLED_FILE}" "${PLUGIN_NAME}@${PLUGIN_NAME}" "${INSTALL_DIR}" "${VERSION}" "${TIMESTAMP}" "${GIT_SHA}" <<'PYEOF'
import json, os, sys, tempfile

installed_file, plugin_key, install_path, version, timestamp, git_sha = sys.argv[1:7]

try:
    with open(installed_file, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: '{installed_file}' contiene JSON inválido: {e}", file=sys.stderr)
    print(f"Puedes restaurarlo con: echo '{{\"version\":2,\"plugins\":{{}}}}' > {installed_file}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"Error: no se pudo leer '{installed_file}': {e}", file=sys.stderr)
    sys.exit(1)

if 'plugins' not in data:
    data['plugins'] = {}

data['plugins'][plugin_key] = [{
    'scope': 'user',
    'installPath': install_path,
    'version': version,
    'installedAt': timestamp,
    'lastUpdated': timestamp,
    'gitCommitSha': git_sha
}]

# Escritura atómica: fichero temporal + rename
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

ok "Plugin registrado en installed_plugins.json"

# -- 5. Habilitar en settings.json -----------------------------------------

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

if 'enabledPlugins' not in data:
    data['enabledPlugins'] = {}

data['enabledPlugins'][plugin_key] = True

# Escritura atómica: fichero temporal + rename
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
    ok "Plugin habilitado en settings.json"
else
    info "No se encontró settings.json (se habilitará al iniciar Claude Code)"
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalación completada${NC}\n\n"
printf "  Reinicia Claude Code y ejecuta:\n"
printf "  ${BOLD}/alfred help${NC}\n\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Documentación: https://686f6c61.github.io/alfred-dev/${NC}\n\n"
