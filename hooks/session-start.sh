#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook de SessionStart para el plugin Alfred Dev.
#
# Se ejecuta al inicio de cada sesión (startup, resume, clear, compact)
# para inyectar contexto en Claude: presentación del plugin, comandos
# disponibles, configuración del proyecto y estado de sesión activa.
#
# Emite JSON en stdout con hookSpecificOutput que Claude interpreta
# como contexto adicional para la conversación.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Utilidades ---

# Genera el JSON final del hook a partir del contexto recibido por stdin.
# Usar stdin en vez de sys.argv evita el limite de ARG_MAX del kernel y
# problemas de truncado con caracteres especiales en cadenas largas.
emit_hook_json() {
  python3 -c "
import json, sys
context = sys.stdin.read()
output = {
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context,
    }
}
# json.dumps garantiza un JSON valido independientemente del contenido
print(json.dumps(output, ensure_ascii=False))
"
}

# --- Rutas de referencia ---

# El directorio de trabajo actual es el proyecto del usuario
PROJECT_DIR="${PWD}"
CONFIG_FILE="${PROJECT_DIR}/.claude/alfred-dev.local.md"
STATE_FILE="${PROJECT_DIR}/.claude/alfred-dev-state.json"

# --- Construcción del contexto ---

# Bloque de presentación que siempre se incluye.
# Describe quién es Alfred Dev y qué puede hacer.
CONTEXT="## Alfred Dev - tu empresa de ingeniería en un plugin

Tienes a tu disposición un equipo completo de agentes especializados:
Alfred (orquestador), El Buscador de Problemas (producto), El Dibujante de Cajas (arquitectura),
El Artesano (senior dev), El Paranoico (seguridad), El Rompe-cosas (QA),
El Fontanero (DevOps), El Escriba (documentación) y SonIA (project management).

### Comandos disponibles

- /alfred-dev:feature <descripción> - Nuevo desarrollo con flujo completo (producto -> arquitectura -> desarrollo -> calidad -> docs -> entrega)
- /alfred-dev:discuss <idea> - Refinar una idea o feature antes de abrir implementación
- /alfred-dev:quick <descripción> - Cambio pequeño y acotado con menos ceremonia, pero con tests y seguridad
- /alfred-dev:fix <descripción> - Corregir un bug (diagnóstico -> corrección -> validación)
- /alfred-dev:spike <descripción> - Investigación exploratoria (exploración -> conclusiones)
- /alfred-dev:ship - Preparar release (auditoría -> docs -> empaquetado -> despliegue)
- /alfred-dev:audit - Auditoría completa del código (calidad + seguridad + simplificación)
- /alfred-dev:map-codebase [área] - Crear un mapa persistente de un repo existente antes de tocar código
- /alfred-dev:next - Decidir qué toca hacer ahora y retomar si hay trabajo pendiente
- /alfred-dev:pause - Guardar handoff explícito para seguir más tarde
- /alfred-dev:progress - Ver progreso, kanban, bloqueos y trazabilidad del proyecto
- /alfred-dev:standup - Standup breve y accionable desde SonIA
- /alfred-dev:blocked - Ver solo las tareas bloqueadas
- /alfred-dev:in-progress - Ver solo el trabajo en curso
- /alfred-dev:resume - Retomar una sesión activa o un handoff pendiente
- /alfred-dev:verify [estado] - Preparar o registrar la verificación manual/UAT del entregable actual
- /alfred-dev:validate - Validar la salud operativa de kanban, trazabilidad y UAT
- /alfred-dev:search <texto> - Buscar en artefactos de SonIA y memoria SQLite
- /alfred-dev:sync-github [owner/repo] - Ejecutar SonIA Sync sobre GitHub Issues
- /alfred-dev:config - Ver o modificar la configuración del plugin
- /alfred-dev:status - Estado de la sesión de trabajo activa
- /alfred-dev:update - Comprobar y aplicar actualizaciones del plugin
- /alfred-dev:help - Ayuda detallada de todos los comandos

### Reglas de operación

- Las quality gates son infranqueables: si los tests no pasan, no se avanza.
- La seguridad se audita en cada fase que lo requiera.
- Se sigue TDD estricto en las fases de desarrollo.
- En comandos helper-first (map-codebase, discuss, quick y el caso brownfield de alfred), si existe .claude/alfred-prefetch.json, consúmelo con python3 .claude/alfred-continuity.py consume-prefetch <project_dir> --expected <comando> antes de explorar el repo.
- El agente El Paranoico vigila secretos en cada escritura de fichero."

# --- Configuración del proyecto ---

# Si el usuario tiene un fichero de configuración local, se incluye
# como contexto para que Claude adapte su comportamiento.
if [[ -f "$CONFIG_FILE" ]]; then
  if ! CONFIG_CONTENT=$(cat "$CONFIG_FILE"); then
    echo "[Alfred Dev] Aviso: no se pudo leer '$CONFIG_FILE'" >&2
    CONFIG_CONTENT=""
  fi
  if [[ -n "$CONFIG_CONTENT" ]]; then
    CONTEXT="${CONTEXT}

### Configuración del proyecto

El usuario ha definido preferencias en .claude/alfred-dev.local.md:

\`\`\`
${CONFIG_CONTENT}
\`\`\`"
  fi
fi

# --- Rutas del plugin y memoria ---

PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)
MEMORY_DB="${PROJECT_DIR}/.claude/alfred-memory.db"
CLAUDE_PROJECT_SETTINGS_LOCAL="${PROJECT_DIR}/.claude/settings.local.json"
CLAUDE_PROJECT_SETTINGS_SHARED="${PROJECT_DIR}/.claude/settings.json"

CONFIG_SUMMARY=$(PYTHONPATH="${PLUGIN_ROOT}" python3 - "$PROJECT_DIR" "$STATE_FILE" <<'PY' 2>/dev/null || true
import sys

sys.path.insert(0, sys.path[0] or "")

from core.config_loader import (
    get_active_optional_agents,
    is_autopilot_configured,
    is_autopilot_enabled_for_project,
    load_project_config,
)
from core.personality import AGENTS, get_agent_voice

project_dir = sys.argv[1]
state_path = sys.argv[2]
config = load_project_config(project_dir)

autonomia = config.get("autonomia", {})
stack = config.get("proyecto", {})
memory = config.get("memoria", {})
personality = config.get("personalidad", {})

sarcasmo = personality.get("nivel_sarcasmo", 3)
allow_mocking = personality.get("insultar_malas_practicas", True)
effective_sarcasm = sarcasmo if allow_mocking else min(sarcasmo, 3)
voice = get_agent_voice("alfred", nivel_sarcasmo=effective_sarcasm)
base_voice_count = len(AGENTS["alfred"]["frases"])
if effective_sarcasm >= 4 and len(voice) > base_voice_count:
    sample_phrase = voice[-1]
else:
    sample_phrase = voice[(max(effective_sarcasm, 1) - 1) % base_voice_count]

phase_order = (
    "producto",
    "arquitectura",
    "desarrollo",
    "calidad",
    "documentacion",
    "entrega",
)
autonomia_summary = ", ".join(
    f"{phase}={autonomia.get(phase, 'desconocido')}"
    for phase in phase_order
)

stack_keys = ("runtime", "lenguaje", "framework", "orm", "test_runner", "bundler")
stack_summary = ", ".join(
    f"{key}={stack.get(key, 'desconocido')}"
    for key in stack_keys
)

active_optional_agents = get_active_optional_agents(config)
memory_status = "activa" if memory.get("enabled", False) else "inactiva"

lines = [
    "### Configuración efectiva",
    "",
    f"- Autopilot por configuración: {'sí' if is_autopilot_configured(config) else 'no'}",
    (
        "- Autopilot efectivo (config/estado): "
        f"{'sí' if is_autopilot_enabled_for_project(project_dir, state_path) else 'no'}"
    ),
    f"- Autonomía por fase: {autonomia_summary}",
    f"- Stack efectivo: {stack_summary}",
    f"- Memoria persistente: {memory_status}",
    (
        "- Personalidad: "
        f"sarcasmo={sarcasmo}, idioma={personality.get('idioma', 'es')}, "
        f"verbosidad={personality.get('verbosidad', 'normal')}, "
        f"celebrar_victorias={'sí' if personality.get('celebrar_victorias', True) else 'no'}, "
        "insultar_malas_practicas="
        f"{'sí' if personality.get('insultar_malas_practicas', True) else 'no'}"
    ),
    f"- Muestra de tono de Alfred: {sample_phrase}",
    (
        "- Agentes opcionales activos: "
        f"{', '.join(active_optional_agents) if active_optional_agents else 'ninguno'}"
    ),
]

print("\n".join(lines))
PY
)

if [[ -n "$CONFIG_SUMMARY" ]]; then
  CONTEXT="${CONTEXT}

${CONFIG_SUMMARY}"
fi

# --- Estado de sesión activa ---

# Si existe un fichero de estado, se extrae información relevante
# para que Claude sepa en qué punto del flujo se encuentra el usuario.
if [[ -f "$STATE_FILE" ]]; then
  STATE_INFO=$(python3 -c "
import json, sys

try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        state = json.load(f)

    comando = state.get('comando', 'desconocido')
    fase = state.get('fase_actual', 'desconocida')
    descripcion = state.get('descripcion', '')
    completadas = state.get('fases_completadas', [])
    num_completadas = len(completadas)

    # Si la sesión está completada, no aporta contexto útil
    if fase == 'completado':
        sys.exit(0)

    partes = []
    partes.append(f'Flujo activo: {comando}')
    partes.append(f'Fase actual: {fase}')
    if descripcion:
        partes.append(f'Descripción: {descripcion}')
    if num_completadas > 0:
        nombres = [c['nombre'] for c in completadas]
        partes.append(f'Fases completadas: {\", \".join(nombres)}')

    print('\n'.join(partes))
except FileNotFoundError:
    sys.exit(0)
except (json.JSONDecodeError, KeyError) as e:
    print(f'[Alfred Dev] Aviso: estado de sesión corrupto o incompleto: {e}', file=sys.stderr)
    sys.exit(0)
" "$STATE_FILE") || STATE_INFO=""

  if [[ -n "$STATE_INFO" ]]; then
    CONTEXT="${CONTEXT}

### Sesión de trabajo activa

${STATE_INFO}

Puedes continuar la sesión con /alfred-dev:status o avanzar a la siguiente fase."
  fi
fi

# --- Siguiente paso sugerido ---

NEXT_INFO=$(PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.continuity import suggest_next_action

suggestion = suggest_next_action(sys.argv[1])
print(suggestion['command'])
print(suggestion['reason'])
" "$PROJECT_DIR" "$PLUGIN_ROOT" 2>/dev/null || true)

if [[ -n "$NEXT_INFO" ]]; then
  NEXT_COMMAND=$(printf '%s\n' "$NEXT_INFO" | sed -n '1p')
  NEXT_REASON=$(printf '%s\n' "$NEXT_INFO" | tail -n +2)

  if [[ -n "$NEXT_COMMAND" && -n "$NEXT_REASON" ]]; then
    CONTEXT="${CONTEXT}

### Siguiente paso recomendado

- /alfred-dev:${NEXT_COMMAND}
- ${NEXT_REASON}"
  fi
fi

# --- Asegurar que la memoria está habilitada por defecto ---
#
# Si el fichero de configuración local no existe, se crea con la memoria
# activada para que los hooks de captura registren datos desde la primera
# sesión y el dashboard tenga contenido real desde el minuto 1.

LOCAL_CONFIG="${PROJECT_DIR}/.claude/alfred-dev.local.md"

PYTHONPATH="${PLUGIN_ROOT}" python3 - "$LOCAL_CONFIG" <<'PY' 2>/dev/null || true
import sys

from core.config_loader import ensure_bootstrap_local_config

ensure_bootstrap_local_config(sys.argv[1])
PY

MEMORY_RUNTIME_SETTINGS=$(PYTHONPATH="${PLUGIN_ROOT}" python3 - "$PROJECT_DIR" <<'PY' 2>/dev/null || true
from core.memory_config import load_memory_config
import sys

config = load_memory_config(sys.argv[1])
print("MEMORY_ENABLED=" + ("yes" if config.get("enabled", False) else "no"))
print("SYNC_TO_NATIVE=" + ("yes" if config.get("sync_to_native", True) else "no"))
PY
)

MEMORY_ENABLED="no"
SYNC_TO_NATIVE="yes"
while IFS='=' read -r key value; do
  case "$key" in
    MEMORY_ENABLED) MEMORY_ENABLED="$value" ;;
    SYNC_TO_NATIVE) SYNC_TO_NATIVE="$value" ;;
  esac
done <<< "${MEMORY_RUNTIME_SETTINGS}"

# --- Asegurar que la BD de memoria existe desde el primer arranque ---
#
# La BD solo se crea si la memoria persistente está activa. Si el usuario la
# ha desactivado explícitamente, se respeta y no se siembran side effects.

if [[ "$MEMORY_ENABLED" == "yes" && ! -f "$MEMORY_DB" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.memory import MemoryDB
db = MemoryDB(sys.argv[1])
db.close()
" "$MEMORY_DB" "$PLUGIN_ROOT" 2>/dev/null || echo "[Alfred Dev] Aviso: no se pudo crear la BD de memoria" >&2
fi

# --- Bootstrap de permisos locales para Claude Code CLI ---
#
# Alfred necesita una base estable de permisos en el proyecto para que los
# comandos operativos helper-first funcionen de forma natural en CLI, sobre todo
# en `claude -p`. Se añaden reglas mínimas y acotadas para:
# - leer el proyecto;
# - editar y escribir artefactos operativos en docs/project/ y .claude/alfred-*;
# - ejecutar los helpers deterministas vía un wrapper local en `.claude/`.
# - arrancar la sesión en `acceptEdits` cuando el proyecto todavía no tenga un
#   `defaultMode` explícito, para que los comandos operativos no se queden
#   bloqueados al persistir artefactos.
#
# Si el fichero ya existe, se fusionan solo las reglas que falten. Si está roto,
# se respeta y solo se avisa por stderr.

for SETTINGS_PATH in "$CLAUDE_PROJECT_SETTINGS_LOCAL" "$CLAUDE_PROJECT_SETTINGS_SHARED"; do
PYTHONPATH="${PLUGIN_ROOT}" python3 - "$SETTINGS_PATH" <<'PY' 2>/dev/null || \
  echo "[Alfred Dev] Aviso: no se pudieron bootstrapear los permisos locales de Claude Code en ${SETTINGS_PATH}" >&2
import json
import os
import sys

settings_path = sys.argv[1]
required_allow = [
    "Read(**)",
    "Edit(docs/project/**)",
    "Write(docs/project/**)",
    "Edit(.claude/alfred-*.json)",
    "Write(.claude/alfred-*.json)",
    "Edit(.claude/alfred-*.md)",
    "Write(.claude/alfred-*.md)",
    "Bash(python3 *)",
    "Bash(python3 .claude/alfred-continuity.py *)",
]

os.makedirs(os.path.dirname(settings_path), exist_ok=True)

if os.path.exists(settings_path):
    try:
        with open(settings_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        sys.exit(1)
else:
    data = {}

if not isinstance(data, dict):
    data = {}

default_mode = data.get("defaultMode")
if not isinstance(default_mode, str) or not default_mode.strip():
    data["defaultMode"] = "acceptEdits"

permissions = data.get("permissions")
if not isinstance(permissions, dict):
    permissions = {}

allow = permissions.get("allow")
if not isinstance(allow, list):
    allow = []

normalized_allow = [str(item) for item in allow]
for rule in required_allow:
    if rule not in normalized_allow:
        normalized_allow.append(rule)

permissions["allow"] = normalized_allow
data["permissions"] = permissions

with open(settings_path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
PY
done

# --- Wrapper local para helpers deterministas ---
#
# Claude Code CLI tiende a pedir aprobación si el comando Bash apunta a una ruta
# fuera del proyecto actual, aunque la acción sea inocua y esté permitida en
# términos generales. Para que los slash commands helper-first funcionen de
# forma natural en `claude -p`, se genera un wrapper local en `.claude/` que
# importa la lógica real desde el plugin instalado.

CONTINUITY_WRAPPER="${PROJECT_DIR}/.claude/alfred-continuity.py"

python3 - "$CONTINUITY_WRAPPER" "$PLUGIN_ROOT" <<'PY' 2>/dev/null || \
  echo "[Alfred Dev] Aviso: no se pudo preparar el wrapper local de continuidad" >&2
import os
import sys

wrapper_path = sys.argv[1]
plugin_root = sys.argv[2]

content = f"""#!/usr/bin/env python3
import sys

PLUGIN_ROOT = {plugin_root!r}
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.continuity import main

if __name__ == "__main__":
    raise SystemExit(main())
"""

os.makedirs(os.path.dirname(wrapper_path), exist_ok=True)
with open(wrapper_path, "w", encoding="utf-8") as fh:
    fh.write(content)
os.chmod(wrapper_path, 0o755)
PY

# --- Asegurar iteración activa para el dashboard ---
#
# Si la BD existe pero no hay iteración activa, se crea una de tipo "session"
# para que los commits y eventos capturados durante el trabajo normal se
# asocien a algo y el dashboard tenga contenido desde el primer uso.
# Si el usuario inicia un flujo (/alfred-dev:feature, etc.), la iteración
# "session" se completará y se creará una nueva del flujo correspondiente.

if [[ "$MEMORY_ENABLED" == "yes" && -f "$MEMORY_DB" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.memory import MemoryDB

db = MemoryDB(sys.argv[1])
active = db.get_active_iteration()
if active is None:
    iteration_id = db.start_iteration(
        command='session',
        description='Sesion de trabajo general',
    )
    db.log_event(
        event_type='session_started',
        payload={'source': 'session-start.sh'},
        iteration_id=iteration_id,
    )
db.close()
" "$MEMORY_DB" "$PLUGIN_ROOT" 2>/dev/null || true
fi

# --- Sincronizacion de memoria a ficheros nativos de Claude Code ---
#
# Proyecta las decisiones, iteraciones y commits de la DB a ficheros .md
# en el directorio de memoria nativa (~/.claude/projects/<hash>/memory/).
# Esto permite que Claude acceda a la memoria del proyecto sin necesidad
# de invocar herramientas MCP ni al Bibliotecario.

if [[ "$MEMORY_ENABLED" == "yes" && -f "$MEMORY_DB" && "$SYNC_TO_NATIVE" == "yes" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 "${PLUGIN_ROOT}/core/memory_sync.py" \
    --action sync_all \
    --project-dir "$PROJECT_DIR" 2>/dev/null || true
fi

# --- Memoria persistente del proyecto ---

# Si el proyecto tiene memoria (.claude/alfred-memory.db), se extrae
# un resumen de las últimas decisiones para dar contexto histórico a Claude.
# El bloque Python importa core.memory desde el directorio raíz del plugin
# y consulta la base de datos. Si algo falla, se omite silenciosamente.

if [[ "$MEMORY_ENABLED" == "yes" && -f "$MEMORY_DB" ]]; then
  MEMORY_INFO=$(PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sqlite3
import sys

try:
    from core.memory import MemoryDB

    db = MemoryDB(sys.argv[1])

    # Estadísticas generales para saber cuántas decisiones hay
    stats = db.get_stats()
    total = stats.get('total_decisions', 0)

    if total == 0:
        db.close()
        sys.exit(0)

    # Contexto por iteracion activa o global
    active = db.get_active_iteration()

    lines = []

    if active:
        # Inyectar decisiones de la iteracion activa y, si aun no hay ninguna,
        # degradar a las decisiones recientes del proyecto para no perder
        # continuidad historica en sesiones nuevas.
        decisions = db.get_decisions(iteration_id=active['id'], limit=10)
        using_project_fallback = False
        if not decisions:
            decisions = db.get_decisions(limit=5)
            using_project_fallback = bool(decisions)
        lines.append('### Memoria del proyecto')
        lines.append('')
        cmd_activo = active.get('command', '?')
        desc_activa = active.get('description', '')
        lines.append(f'Iteracion activa: {cmd_activo} #{active[\"id\"]}')
        if desc_activa:
            lines.append(f'Descripcion: {desc_activa}')
        if using_project_fallback:
            lines.append('La iteracion activa aun no tiene decisiones; se muestran las mas recientes del proyecto.')
        else:
            lines.append(f'Decisiones en esta iteracion: {len(decisions)}')
        lines.append(f'Total de decisiones del proyecto: {total}')
    else:
        # Sin iteracion activa: ultimas 5 globales
        decisions = db.get_decisions(limit=5)
        lines.append('### Memoria del proyecto')
        lines.append('')
        lines.append(f'El proyecto tiene memoria persistente activa con {total} decisiones registradas.')

    if decisions:
        lines.append('Ultimas decisiones:')
        lines.append('')

        for d in decisions:
            fecha = d.get('decided_at', '')[:10]
            titulo = d.get('title', 'sin titulo')
            tags = d.get('tags', '[]')
            try:
                import json as _json
                tag_list = _json.loads(tags) if isinstance(tags, str) else tags
                if tag_list:
                    _sep = ', '
                    tag_str = ' [' + _sep.join(tag_list) + ']'
                else:
                    tag_str = ''
            except Exception:
                tag_str = ''

            iter_id = d.get('iteration_id')
            if iter_id is not None:
                it = db.get_iteration(iter_id)
                if it is not None:
                    cmd = it.get('command', '?')
                    lines.append(f'- [{fecha}] {titulo}{tag_str} (iteracion: {cmd} #{iter_id})')
                else:
                    lines.append(f'- [{fecha}] {titulo}{tag_str}')
            else:
                lines.append(f'- [{fecha}] {titulo}{tag_str}')

    lines.append('')
    lines.append('Para consultas historicas detalladas, delega en El Bibliotecario (agente opcional).')

    db.close()
    print('\n'.join(lines))
except ImportError as e:
    # core.memory no disponible: la memoria no esta instalada o el path es incorrecto
    print(f'[Alfred Dev] Aviso: no se pudo cargar el modulo de memoria: {e}. '
          f'El resumen de decisiones no estara disponible.', file=sys.stderr)
    sys.exit(0)
except sqlite3.OperationalError as e:
    # DB bloqueada, disco lleno u otro error operativo de SQLite
    print(f'[Alfred Dev] Aviso: error al leer la memoria del proyecto: {e}', file=sys.stderr)
    sys.exit(0)
except sqlite3.DatabaseError as e:
    # DB corrupta: avisar al usuario para que pueda reconstruirla
    print(f'[Alfred Dev] Aviso: la base de datos de memoria puede estar corrupta: {e}', file=sys.stderr)
    sys.exit(0)
except Exception as e:
    # Otros errores inesperados: registrar para diagnostico
    print(f'[Alfred Dev] Aviso: error inesperado al cargar memoria: {e}', file=sys.stderr)
    sys.exit(0)
" "$MEMORY_DB") || MEMORY_INFO=""

  if [[ -n "$MEMORY_INFO" ]]; then
    CONTEXT="${CONTEXT}

${MEMORY_INFO}"
  fi
fi

# --- Comprobación de actualizaciones ---

# Consulta la última release publicada en GitHub. Si hay versión nueva,
# añade un aviso al contexto de sesión. Falla silenciosamente si no hay
# red, se excede el timeout (3s) o la API devuelve error.
# La version se lee de plugin.json para evitar tener que actualizarla
# manualmente con cada bump. Si la lectura falla, se usa un fallback.
CURRENT_VERSION=$(python3 -c "
import json, sys
try:
    with open(sys.argv[1], 'r') as f:
        print(json.load(f).get('version', '0.0.0'))
except Exception as e:
    print(f'[Alfred Dev] Aviso: no se pudo leer la version del plugin: {e}', file=sys.stderr)
    print('0.0.0')
" "${PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null) || CURRENT_VERSION="0.0.0"
if command -v curl &>/dev/null; then
  LATEST_RELEASE=$(curl -s --max-time 3 --proto '=https' \
    -H "User-Agent: alfred-dev-plugin" \
    "https://api.github.com/repos/686f6c61/alfred-dev/releases/latest" \
    | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'tag_name' in data:
        print(data['tag_name'].lstrip('v'))
    elif 'message' in data:
        print(f'[Alfred Dev] GitHub API: {data[\"message\"]}', file=sys.stderr)
except Exception as e:
    print(f'[Alfred Dev] Error comprobando actualizaciones: {e}', file=sys.stderr)
" 2>/dev/null || echo "")

  UPDATE_AVAILABLE=$(python3 -c "
import re, sys

def parse(version):
    match = re.match(r'^([0-9]+)\.([0-9]+)\.([0-9]+)(?:-[A-Za-z0-9.]+)?$', version)
    if not match:
        raise ValueError(version)
    return tuple(int(part) for part in match.groups())

current = parse(sys.argv[1])
latest = parse(sys.argv[2])
print('yes' if latest > current else 'no')
" "$CURRENT_VERSION" "$LATEST_RELEASE" 2>/dev/null || echo "")

  # Solo aceptar versiones con formato semántico válido para evitar
  # inyección de contenido arbitrario desde la respuesta de la API.
  if [[ -n "$LATEST_RELEASE" && "$LATEST_RELEASE" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ && "$UPDATE_AVAILABLE" == "yes" ]]; then
    CONTEXT="${CONTEXT}

### Actualización disponible

Hay una nueva versión de Alfred Dev: v${LATEST_RELEASE} (actual: v${CURRENT_VERSION}). Ejecuta /alfred-dev:update para actualizar."
  fi
fi

# --- Emisión del JSON de salida ---
#
# Se pasa el contexto por stdin a Python para evitar limites de ARG_MAX
# y garantizar un JSON valido independientemente del contenido.

printf '%s' "$CONTEXT" | emit_hook_json
