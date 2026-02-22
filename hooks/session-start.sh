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

# Escapa una cadena para que sea segura dentro de un valor JSON.
# Gestiona: barra invertida, comillas dobles, saltos de línea, tabuladores
# y retornos de carro.
escape_for_json() {
  local text="$1"
  python3 -c "
import json, sys
# Se lee el texto tal cual y se emite escapado para JSON
print(json.dumps(sys.argv[1])[1:-1])
" "$text"
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
El Fontanero (DevOps) y El Traductor (documentación).

### Comandos disponibles

- /alfred feature <descripción> - Nuevo desarrollo con flujo completo (producto -> arquitectura -> desarrollo -> calidad -> docs -> entrega)
- /alfred fix <descripción> - Corregir un bug (diagnóstico -> corrección -> validación)
- /alfred spike <descripción> - Investigación exploratoria (exploración -> conclusiones)
- /alfred ship - Preparar release (auditoría -> docs -> empaquetado -> despliegue)
- /alfred audit - Auditoría completa del código (calidad + seguridad + simplificación)
- /alfred config - Ver o modificar la configuración del plugin
- /alfred status - Estado de la sesión de trabajo activa
- /alfred update - Comprobar y aplicar actualizaciones del plugin
- /alfred help - Ayuda detallada de todos los comandos

### Reglas de operación

- Las quality gates son infranqueables: si los tests no pasan, no se avanza.
- La seguridad se audita en cada fase que lo requiera.
- Se sigue TDD estricto en las fases de desarrollo.
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

Puedes continuar la sesión con /alfred status o avanzar a la siguiente fase."
  fi
fi

# --- Memoria persistente del proyecto ---

# Si el proyecto tiene memoria activa (.claude/alfred-memory.db), se extrae
# un resumen de las últimas decisiones para dar contexto histórico a Claude.
# El bloque Python importa core.memory desde el directorio raíz del plugin
# y consulta la base de datos. Si algo falla, se omite silenciosamente.
MEMORY_DB="${PROJECT_DIR}/.claude/alfred-memory.db"
PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)

if [[ -f "$MEMORY_DB" ]]; then
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
        # Inyectar decisiones de la iteracion activa
        decisions = db.get_decisions(iteration_id=active['id'], limit=10)
        lines.append('### Memoria del proyecto')
        lines.append('')
        cmd_activo = active.get('command', '?')
        desc_activa = active.get('description', '')
        lines.append(f'Iteracion activa: {cmd_activo} #{active[\"id\"]}')
        if desc_activa:
            lines.append(f'Descripcion: {desc_activa}')
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

  # Solo aceptar versiones con formato semántico válido para evitar
  # inyección de contenido arbitrario desde la respuesta de la API.
  if [[ -n "$LATEST_RELEASE" && "$LATEST_RELEASE" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ && "$LATEST_RELEASE" != "$CURRENT_VERSION" ]]; then
    CONTEXT="${CONTEXT}

### Actualización disponible

Hay una nueva versión de Alfred Dev: v${LATEST_RELEASE} (actual: v${CURRENT_VERSION}). Ejecuta /alfred update para actualizar."
  fi
fi

# --- Servidor GUI ---

# Levantar el servidor del dashboard si hay memoria activa.
# El servidor corre en background y se para con stop-hook.py.
# Si falla, la sesion continua sin GUI (fail-open).
GUI_SERVER="${PLUGIN_ROOT}/gui/server.py"
GUI_PID_FILE="${PROJECT_DIR}/.claude/alfred-gui.pid"

if [[ -f "$MEMORY_DB" && -f "$GUI_SERVER" ]]; then
  # Matar proceso anterior si existe (sesion previa no limpiada)
  if [[ -f "$GUI_PID_FILE" ]]; then
    OLD_PID=$(cat "$GUI_PID_FILE" 2>/dev/null)
    if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
      kill "$OLD_PID" 2>/dev/null || true
      sleep 0.5
    fi
    rm -f "$GUI_PID_FILE"
  fi

  # Levantar nuevo servidor
  PYTHONPATH="${PLUGIN_ROOT}" python3 "$GUI_SERVER" --db "$MEMORY_DB" &
  GUI_PID=$!

  # Verificar que el proceso arranco (esperar brevemente)
  sleep 1
  if kill -0 "$GUI_PID" 2>/dev/null; then
    echo "$GUI_PID" > "$GUI_PID_FILE"
    CONTEXT="${CONTEXT}

### Dashboard GUI

El servidor del dashboard esta activo. El usuario puede abrir la GUI con /alfred gui."
  else
    echo "[Alfred Dev] Aviso: el servidor GUI no pudo arrancar." >&2
  fi
fi

# --- Emisión del JSON de salida ---

ESCAPED_CONTEXT=$(escape_for_json "$CONTEXT")

cat <<HOOK_JSON
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${ESCAPED_CONTEXT}"
  }
}
HOOK_JSON
