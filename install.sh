#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Alfred Dev -- script de instalacion para Claude Code
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
#   bash ./install.sh
#
# Que hace:
#   1. Verifica que Claude Code esta instalado
#   2. Registra globalmente en Claude Code la fuente GitHub del plugin
#   3. Instala el plugin con claude plugin install
#   4. No pisa ~/.claude/skills ni instala alias global /alfred
#   5. Listo para usar: /alfred-dev:alfred
#
# El script delega toda la gestion en la CLI nativa de Claude Code
# (claude plugin marketplace / claude plugin install) para registrar una
# fuente GitHub personalizada, no oficial, y mantener compatibilidad futura.
# ---------------------------------------------------------------------------

set -euo pipefail

REPO="686f6c61/alfred-dev"
PLUGIN_NAME="alfred-dev"
VERSION="0.7.0"

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

resolve_installed_plugin_root() {
    local cache_dir="${HOME}/.claude/plugins/cache/${PLUGIN_NAME}"
    local exact="${cache_dir}/${PLUGIN_NAME}/${VERSION}"
    local legacy="${cache_dir}/${VERSION}"

    if [[ -d "${exact}" ]]; then
        printf '%s\n' "${exact}"
        return 0
    fi

    if [[ -d "${legacy}" ]]; then
        printf '%s\n' "${legacy}"
        return 0
    fi

    "${PYTHON_CMD}" - "${cache_dir}" "${VERSION}" <<'PYEOF'
import json
import os
import sys

cache_dir, target_version = sys.argv[1:3]
candidates = []

for root, _dirs, files in os.walk(cache_dir):
    if "plugin.json" not in files or ".claude-plugin" not in root:
        continue
    plugin_json = os.path.join(root, "plugin.json")
    try:
        with open(plugin_json, "r", encoding="utf-8") as fh:
            version = json.load(fh).get("version")
    except (OSError, json.JSONDecodeError):
        continue
    if version != target_version:
        continue
    plugin_root = os.path.dirname(root)
    try:
        mtime = os.path.getmtime(plugin_json)
    except OSError:
        mtime = 0
    candidates.append((mtime, plugin_root))

if not candidates:
    sys.exit(1)

candidates.sort(key=lambda item: item[0], reverse=True)
print(candidates[0][1])
PYEOF
}

is_global_source_registered() {
    local known_marketplaces_file="${HOME}/.claude/plugins/known_marketplaces.json"

    [[ -f "${known_marketplaces_file}" ]] || return 1

    "${PYTHON_CMD}" - "${known_marketplaces_file}" "${PLUGIN_NAME}" "${REPO}" <<'PYEOF'
import json
import sys

path, plugin_name, repo = sys.argv[1:4]

try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except (OSError, json.JSONDecodeError):
    sys.exit(1)

entry = data.get(plugin_name)
source = entry.get("source", {}) if isinstance(entry, dict) else {}

if source.get("source") == "github" and source.get("repo") == repo:
    sys.exit(0)

sys.exit(1)
PYEOF
}

normalize_to_user_scope_installation() {
    # Alfred Dev solo soporta instalacion global de usuario. Si alguien lo
    # instalo antes en local/project, limpiamos ese rastro en el contexto actual
    # antes de reinstalar con --scope user.
    claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope local >/dev/null 2>&1 || true
    claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope project >/dev/null 2>&1 || true
    claude plugin marketplace remove "${PLUGIN_NAME}" --scope local >/dev/null 2>&1 || true
    claude plugin marketplace remove "${PLUGIN_NAME}" --scope project >/dev/null 2>&1 || true
    ok "Scopes local/project normalizados; Alfred se instalara como usuario global"
}

remove_stale_user_marketplace_checkout() {
    local marketplace_dir="${HOME}/.claude/plugins/marketplaces/${PLUGIN_NAME}"

    if [[ -d "${marketplace_dir}" ]]; then
        rm -rf "${marketplace_dir}"
        ok "Checkout local del marketplace limpiado para evitar cache obsoleta"
    fi
}

refresh_user_marketplace() {
    # Claude Code puede conservar un clon local obsoleto del marketplace aunque
    # 'plugin install' termine correctamente. Forzamos refresh antes de instalar
    # para que cache/alfred-dev materialice la version publicada actual.
    if claude plugin marketplace update "${PLUGIN_NAME}" 2>&1; then
        ok "Marketplace local actualizado"
    else
        info "No se pudo ejecutar 'claude plugin marketplace update'; continuo con el checkout recien registrado"
    fi
}

verify_user_scope_installation() {
    local plugin_key="${PLUGIN_NAME}@${PLUGIN_NAME}"
    local list_json
    local verify_output

    if ! list_json=$(claude plugin list --json 2>/dev/null); then
        error "No se pudo confirmar el scope global con 'claude plugin list --json'"
        error "Alfred Dev debe quedar instalado como scope user."
        return 1
    fi

    if verify_output=$(
        CLAUDE_PLUGIN_LIST_JSON="${list_json}" "${PYTHON_CMD}" - "${plugin_key}" <<'PYEOF'
import json
import os
import sys

plugin_key = sys.argv[1]

try:
    entries = json.loads(os.environ.get("CLAUDE_PLUGIN_LIST_JSON", ""))
except json.JSONDecodeError as exc:
    print(f"JSON invalido en claude plugin list --json: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(entries, list):
    print("claude plugin list --json no devolvio una lista", file=sys.stderr)
    sys.exit(1)

matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == plugin_key]
if not matches:
    print(f"No aparece {plugin_key} en claude plugin list --json", file=sys.stderr)
    sys.exit(1)

active_non_user = [
    entry for entry in matches
    if entry.get("enabled") is True and entry.get("scope") != "user"
]
if active_non_user:
    details = ", ".join(
        f"scope={entry.get('scope', 'desconocido')} projectPath={entry.get('projectPath', '')}"
        for entry in active_non_user
    )
    print(f"Hay instalaciones activas no globales de {plugin_key}: {details}", file=sys.stderr)
    sys.exit(1)

enabled_user = [
    entry for entry in matches
    if entry.get("enabled") is True and entry.get("scope") == "user"
]
if not enabled_user:
    scopes = ", ".join(str(entry.get("scope", "desconocido")) for entry in matches)
    print(f"{plugin_key} existe, pero no hay entrada enabled con scope user. Scopes vistos: {scopes}", file=sys.stderr)
    sys.exit(1)

stale_non_user = [
    entry for entry in matches
    if entry.get("enabled") is not True and entry.get("scope") != "user"
]
if stale_non_user:
    details = ", ".join(
        f"scope={entry.get('scope', 'desconocido')} projectPath={entry.get('projectPath', '')}"
        for entry in stale_non_user
    )
    print(f"AVISO: quedan entradas antiguas no activas de {plugin_key}: {details}")
PYEOF
    ); then
        if [[ -n "${verify_output}" ]]; then
            info "${verify_output}"
        fi
        ok "Instalacion global de usuario confirmada (--scope user)"
        return 0
    fi

    error "${verify_output}"
    return 1
}

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

if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no esta definida o no apunta a un directorio valido"
    exit 1
fi

if [ ! -d "${HOME}/.claude" ]; then
    error "No se encontro el directorio ~/.claude"
    error "Asegurate de tener Claude Code instalado: https://code.claude.com/docs/en/setup"
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

# -- 1. Registrar fuente global en Claude Code ------------------------------
# Si ya existe, la actualizamos eliminandola primero para forzar un refresh
# del registro global y del cache con los ficheros mas recientes del repo.

info "Registrando fuente GitHub global en Claude Code..."
normalize_to_user_scope_installation

# Si existe una instalacion previa, la quitamos antes de refrescar el
# marketplace. Esto evita estados intermedios donde el plugin sigue apuntando
# a un marketplace ya corrupto o incompleto en disco.
if claude plugin list 2>/dev/null | grep -q "${PLUGIN_NAME}@${PLUGIN_NAME}"; then
    claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope user >/dev/null 2>&1 || true
fi

if claude plugin marketplace list 2>/dev/null | grep -q "${PLUGIN_NAME}"; then
    claude plugin marketplace remove "${PLUGIN_NAME}" --scope user >/dev/null 2>&1 || true
fi
remove_stale_user_marketplace_checkout

if claude plugin marketplace add "${REPO}" --scope user 2>&1; then
    ok "Fuente GitHub declarada"
else
    error "No se pudo registrar la fuente GitHub"
    error "Verifica tu conexion a internet y que el repositorio sea accesible:"
    error "  https://github.com/${REPO}"
    exit 1
fi

# Lo que vuelve global la instalacion no es una carpeta concreta, sino que
# Claude Code deje registrada la fuente en known_marketplaces.json.
if is_global_source_registered; then
    ok "Fuente GitHub registrada globalmente"
else
    info "La CLI respondio OK, pero la fuente no quedo registrada; reintentando..."
    claude plugin marketplace remove "${PLUGIN_NAME}" --scope user >/dev/null 2>&1 || true
    if claude plugin marketplace add "${REPO}" --scope user 2>&1 && is_global_source_registered; then
        ok "Fuente GitHub registrada globalmente tras reintento"
    else
        error "Claude Code no dejo registrada la fuente global del plugin"
        error "Fichero esperado: ${HOME}/.claude/plugins/known_marketplaces.json"
        error "Prueba a ejecutar manualmente:"
        error "  claude plugin marketplace remove ${PLUGIN_NAME} --scope user"
        error "  claude plugin marketplace add ${REPO} --scope user"
        exit 1
    fi
fi

refresh_user_marketplace

# -- 2. Instalar plugin -----------------------------------------------------

info "Instalando plugin..."

if claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope user 2>&1; then
    ok "Plugin instalado y habilitado"
else
    error "No se pudo instalar el plugin"
    error "Puedes intentar instalarlo manualmente:"
    error "  claude plugin marketplace add ${REPO} --scope user"
    error "  claude plugin install ${PLUGIN_NAME}@${PLUGIN_NAME} --scope user"
    exit 1
fi

info "Usa /alfred-dev:alfred o /alfred-dev:feature. No se pisa ~/.claude/skills."
verify_user_scope_installation

# -- 3. Parchear hooks y MCP si python3 no es 3.10+ ------------------------
# Si el python3 por defecto del sistema es demasiado antiguo pero encontramos
# una version compatible (python3.12, python3.11, etc.), actualizamos la
# configuracion instalada para que hooks y el MCP usen esa version concreta.

if [[ "$PYTHON_CMD" != "python3" ]]; then
    _patch_in_place() {
        local file="$1"
        local expression="$2"

        if sed -i.bak "$expression" "$file" 2>/dev/null; then
            rm -f "${file}.bak"
            return 0
        fi

        # macOS sed tiene sintaxis diferente para -i
        sed -i '' "$expression" "$file" 2>/dev/null
    }

    # Obtener la ruta absoluta del Python compatible
    PYTHON_ABS=$(command -v "$PYTHON_CMD" 2>/dev/null || echo "$PYTHON_CMD")

    # Resolver de forma determinista la raiz del plugin recien instalado.
    # Si coexisten varias versiones en cache, preferimos la ruta exacta de
    # la version que acaba de instalarse y, en ultimo termino, la mas reciente
    # cuyo plugin.json declare esa version.
    PLUGIN_ROOT=$(resolve_installed_plugin_root 2>/dev/null || true)
    HOOKS_JSON=""
    MCP_JSON=""
    if [[ -n "${PLUGIN_ROOT}" ]]; then
        HOOKS_JSON="${PLUGIN_ROOT}/hooks/hooks.json"
        MCP_JSON="${PLUGIN_ROOT}/.mcp.json"
    fi

    if [[ -f "$HOOKS_JSON" ]]; then
        if "${PYTHON_CMD}" - "$HOOKS_JSON" "$PYTHON_ABS" <<'PYEOF'
import json
import os
import sys
import tempfile

path, python_abs = sys.argv[1:3]

with open(path, "r", encoding="utf-8") as fh:
    data = json.load(fh)

patched = False
for event_group in data.get("hooks", {}).values():
    if not isinstance(event_group, list):
        continue
    for matcher in event_group:
        if not isinstance(matcher, dict):
            continue
        for hook in matcher.get("hooks", []):
            if not isinstance(hook, dict) or hook.get("type") != "command":
                continue
            command = hook.get("command")
            if command == "python3":
                hook["command"] = python_abs
                patched = True
            elif isinstance(command, str) and "python3 ${CLAUDE_PLUGIN_ROOT}" in command:
                hook["command"] = command.replace(
                    "python3 ${CLAUDE_PLUGIN_ROOT}",
                    f"{python_abs} ${{CLAUDE_PLUGIN_ROOT}}",
                )
                patched = True

if not patched:
    raise SystemExit("hooks.json no contiene hooks Python parcheables")

directory = os.path.dirname(path)
fd, tmp_path = tempfile.mkstemp(prefix=".tmp-plugin-", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp_path, path)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
PYEOF
        then
            ok "hooks.json parcheado para usar $PYTHON_ABS"
        else
            info "Aviso: no se pudo parchear hooks.json, los hooks usaran 'python3'"
        fi
    else
        info "Aviso: no se encontro hooks.json en la instalacion activa para parchear Python"
    fi

    if [[ -f "$MCP_JSON" ]]; then
        if "${PYTHON_CMD}" - "$MCP_JSON" "$PYTHON_ABS" <<'PYEOF'
import json
import os
import sys
import tempfile

path, python_abs = sys.argv[1:3]

with open(path, "r", encoding="utf-8") as fh:
    data = json.load(fh)

mcp_servers = data.get("mcpServers") if isinstance(data.get("mcpServers"), dict) else data
if not isinstance(mcp_servers, dict):
    raise SystemExit(".mcp.json no declara servidores MCP")

alfred_memory = mcp_servers.get("alfred-memory")
if not isinstance(alfred_memory, dict):
    raise SystemExit(".mcp.json no declara alfred-memory")

alfred_memory["command"] = python_abs

directory = os.path.dirname(path)
fd, tmp_path = tempfile.mkstemp(prefix=".tmp-plugin-", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp_path, path)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
PYEOF
        then
            ok ".mcp.json parcheado para usar $PYTHON_ABS"
        else
            info "Aviso: no se pudo parchear .mcp.json, el MCP usara 'python3'"
        fi
    else
        info "Aviso: no se encontro .mcp.json en la instalacion activa para parchear Python"
    fi
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalacion completada${NC}\n\n"
printf "  En Claude Code, ejecuta ${BOLD}/reload-plugins${NC} y despues:\n"
printf "  ${BOLD}/alfred-dev:alfred${NC}\n"
printf "  ${DIM}Estado: /alfred-dev:progress · retomar: /alfred-dev:retomar${NC}\n\n"
printf "  ${DIM}Si /reload-plugins avisa por MCP/coste de cache o no aparece el plugin, reinicia Claude Code.${NC}\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Documentacion: https://alfred-dev.com${NC}\n\n"
