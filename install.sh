#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
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

set -euo pipefail

REPO="686f6c61/alfred-dev"
PLUGIN_NAME="alfred-dev"
VERSION="0.3.7"

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

# Python 3.10+ es necesario para los hooks y el core del plugin
if ! command -v python3 &>/dev/null; then
    error "Python 3 no esta instalado o no esta en el PATH"
    error "Alfred Dev requiere Python 3.10 o superior"
    error "Instala Python desde https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 10 ]]; }; then
    error "Python $PYTHON_VERSION detectado, pero se requiere 3.10 o superior"
    error "Actualiza Python desde https://www.python.org/downloads/"
    exit 1
fi

ok "Python $PYTHON_VERSION detectado"

# git es necesario para descargar el plugin
if ! command -v git &>/dev/null; then
    error "git no esta instalado o no esta en el PATH"
    error "Instala git desde https://git-scm.com/"
    exit 1
fi

if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no esta definida o no apunta a un directorio valido"
    exit 1
fi

if [ ! -d "${HOME}/.claude" ]; then
    error "No se encontro el directorio ~/.claude"
    error "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    error "El comando 'claude' no esta disponible en el PATH"
    error "Asegurate de tener Claude Code instalado y accesible desde la terminal"
    exit 1
fi

# -- Instalacion ------------------------------------------------------------

printf "\n${BOLD}Alfred Dev${NC} ${DIM}v${VERSION}${NC}\n"
printf "${DIM}Plugin de ingenieria de software automatizada${NC}\n\n"

# -- 1. Registrar marketplace -----------------------------------------------
# Si ya existe, lo actualizamos eliminandolo primero para forzar un refresh
# del cache con los ficheros mas recientes del repositorio.

info "Registrando marketplace..."

if claude plugin marketplace list 2>/dev/null | grep -q "${PLUGIN_NAME}"; then
    claude plugin marketplace remove "${PLUGIN_NAME}" >/dev/null 2>&1 || true
fi

if claude plugin marketplace add "${REPO}" 2>&1; then
    ok "Marketplace registrado"
else
    error "No se pudo registrar el marketplace"
    error "Verifica tu conexion a internet y que el repositorio sea accesible:"
    error "  https://github.com/${REPO}"
    exit 1
fi

# -- 2. Instalar plugin -----------------------------------------------------

info "Instalando plugin..."

# Si hay una version anterior instalada, la eliminamos primero
if claude plugin list 2>/dev/null | grep -q "${PLUGIN_NAME}@${PLUGIN_NAME}"; then
    claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" >/dev/null 2>&1 || true
fi

if claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}" 2>&1; then
    ok "Plugin instalado y habilitado"
else
    error "No se pudo instalar el plugin"
    error "Puedes intentar instalarlo manualmente:"
    error "  claude plugin marketplace add ${REPO}"
    error "  claude plugin install ${PLUGIN_NAME}@${PLUGIN_NAME}"
    exit 1
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalacion completada${NC}\n\n"
printf "  Reinicia Claude Code y ejecuta:\n"
printf "  ${BOLD}/alfred help${NC}\n\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Documentacion: https://alfred-dev.com${NC}\n\n"
