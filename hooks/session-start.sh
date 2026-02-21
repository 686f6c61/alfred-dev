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

    # Últimas 5 decisiones (las más recientes primero)
    decisions = db.get_decisions(limit=5)

    # Iteración activa (si la hay)
    active = db.get_active_iteration()

    # Construir el bloque de texto
    lines = []
    lines.append('### Memoria del proyecto')
    lines.append('')
    lines.append(f'El proyecto tiene memoria persistente activa con {total} decisiones registradas.')
    lines.append('Ultimas decisiones:')
    lines.append('')

    for d in decisions:
        fecha = d.get('decided_at', '')[:10]
        titulo = d.get('title', 'sin titulo')
        iter_id = d.get('iteration_id')

        # Obtener datos de la iteración asociada si existe
        if iter_id is not None:
            it = db.get_iteration(iter_id)
            if it is not None:
                cmd = it.get('command', '?')
                lines.append(f'- [{fecha}] {titulo} (iteracion: {cmd} #{iter_id})')
            else:
                lines.append(f'- [{fecha}] {titulo}')
        else:
            lines.append(f'- [{fecha}] {titulo}')

    if active is not None:
        lines.append('')
        cmd_activo = active.get('command', '?')
        desc_activa = active.get('description', '')
        lines.append(f'Iteracion activa: {cmd_activo} #{active[\"id\"]}')
        if desc_activa:
            lines.append(f'Descripcion: {desc_activa}')

    lines.append('')
    lines.append('Para consultas historicas detalladas, delega en El Bibliotecario (agente opcional).')

    db.close()
    print('\n'.join(lines))
except Exception:
    # Cualquier error se ignora: la memoria es contexto opcional
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
CURRENT_VERSION="0.2.0"
if command -v curl &>/dev/null; then
  LATEST_RELEASE=$(curl -s --max-time 3 --proto '=https' \
    "https://api.github.com/repos/686f6c61/alfred-dev/releases/latest" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('tag_name','').lstrip('v'))" 2>/dev/null || echo "")

  # Solo aceptar versiones con formato semántico válido para evitar
  # inyección de contenido arbitrario desde la respuesta de la API.
  if [[ -n "$LATEST_RELEASE" && "$LATEST_RELEASE" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ && "$LATEST_RELEASE" != "$CURRENT_VERSION" ]]; then
    CONTEXT="${CONTEXT}

### Actualización disponible

Hay una nueva versión de Alfred Dev: v${LATEST_RELEASE} (actual: v${CURRENT_VERSION}). Ejecuta /alfred update para actualizar."
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
