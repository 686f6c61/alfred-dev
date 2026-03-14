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
VERSION="0.4.2"

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

# Python 3.10+ es necesario para los hooks y el core del plugin.
# En macOS, /usr/bin/python3 suele ser 3.9 (Apple). Los usuarios pueden
# tener 3.10+ via Homebrew, pyenv o instalador oficial como python3.13,
# python3.12, etc. Buscamos la mejor version disponible.

PYTHON_CMD=""
PYTHON_VERSION=""

# Buscar entre los candidatos mas comunes en orden descendente
for candidate in python3 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 10 ]]; then
            PYTHON_CMD="$candidate"
            PYTHON_VERSION="$ver"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    # Ultimo intento: Homebrew en las rutas habituales de macOS
    for brew_path in /opt/homebrew/bin /usr/local/bin; do
        for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
            full="${brew_path}/${candidate}"
            if [[ -x "$full" ]]; then
                ver=$("$full" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
                major=$(echo "$ver" | cut -d. -f1)
                minor=$(echo "$ver" | cut -d. -f2)
                if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 10 ]]; then
                    PYTHON_CMD="$full"
                    PYTHON_VERSION="$ver"
                    break 2
                fi
            fi
        done
    done
fi

if [[ -z "$PYTHON_CMD" ]]; then
    error "No se encontro Python 3.10 o superior"
    error "Se buscaron: python3, python3.13, python3.12, python3.11, python3.10"
    error "Tambien en /opt/homebrew/bin y /usr/local/bin"
    error ""
    error "Instala Python desde https://www.python.org/downloads/"
    error "o con Homebrew: brew install python@3.12"
    exit 1
fi

ok "Python $PYTHON_VERSION detectado ($PYTHON_CMD)"

# Si python3 del PATH no es el que encontramos, avisar al usuario
DEFAULT_PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
if [[ "$PYTHON_CMD" != "python3" ]] && [[ "$DEFAULT_PY_VER" != "$PYTHON_VERSION" ]]; then
    info "Nota: 'python3' en tu PATH es $DEFAULT_PY_VER (demasiado antiguo)"
    info "Los hooks del plugin usaran '$PYTHON_CMD' en su lugar"
fi

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

# -- 3. Parchear hooks si python3 no es 3.10+ ------------------------------
# Si el python3 por defecto del sistema es demasiado antiguo pero encontramos
# una version compatible (python3.12, python3.11, etc.), actualizamos
# hooks.json para que los hooks usen esa version concreta.

if [[ "$PYTHON_CMD" != "python3" ]]; then
    # Buscar hooks.json en la cache del plugin recien instalado
    HOOKS_JSON=$(find "${HOME}/.claude/plugins/cache/${PLUGIN_NAME}" -name "hooks.json" -path "*/hooks/*" 2>/dev/null | head -1)

    if [[ -n "$HOOKS_JSON" ]]; then
        # Obtener la ruta absoluta del Python compatible
        PYTHON_ABS=$(command -v "$PYTHON_CMD" 2>/dev/null || echo "$PYTHON_CMD")

        # Reemplazar 'python3 ' por la ruta absoluta en los comandos de hooks
        if sed -i.bak "s|python3 \${CLAUDE_PLUGIN_ROOT}|${PYTHON_ABS} \${CLAUDE_PLUGIN_ROOT}|g" "$HOOKS_JSON" 2>/dev/null; then
            rm -f "${HOOKS_JSON}.bak"
            ok "hooks.json parcheado para usar $PYTHON_ABS"
        else
            # macOS sed tiene sintaxis diferente para -i
            sed -i '' "s|python3 \${CLAUDE_PLUGIN_ROOT}|${PYTHON_ABS} \${CLAUDE_PLUGIN_ROOT}|g" "$HOOKS_JSON" 2>/dev/null && \
                ok "hooks.json parcheado para usar $PYTHON_ABS" || \
                info "Aviso: no se pudo parchear hooks.json, los hooks usaran 'python3'"
        fi
    fi
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalacion completada${NC}\n\n"
printf "  Reinicia Claude Code y ejecuta:\n"
printf "  ${BOLD}/alfred help${NC}\n\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Documentacion: https://alfred-dev.com${NC}\n\n"
