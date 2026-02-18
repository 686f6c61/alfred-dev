#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook de SessionStart para el plugin Alfred Dev.
#
# Se ejecuta al inicio de cada sesion (startup, resume, clear, compact)
# para inyectar contexto en Claude: presentacion del plugin, comandos
# disponibles, configuracion del proyecto y estado de sesion activa.
#
# Emite JSON en stdout con hookSpecificOutput que Claude interpreta
# como contexto adicional para la conversacion.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Utilidades ---

# Escapa una cadena para que sea segura dentro de un valor JSON.
# Gestiona: barra invertida, comillas dobles, saltos de linea, tabuladores
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

# --- Construccion del contexto ---

# Bloque de presentacion que siempre se incluye.
# Describe quien es Alfred Dev y que puede hacer.
CONTEXT="## Alfred Dev - tu empresa de ingenieria en un plugin

Tienes a tu disposicion un equipo completo de agentes especializados:
Alfred (orquestador), El Buscador de Problemas (producto), El Dibujante de Cajas (arquitectura),
El Artesano (senior dev), El Paranoico (seguridad), El Rompe-cosas (QA),
El Fontanero (DevOps) y El Traductor (documentacion).

### Comandos disponibles

- /alfred feature <descripcion> - Nuevo desarrollo con flujo completo (producto -> arquitectura -> desarrollo -> calidad -> docs -> entrega)
- /alfred fix <descripcion> - Corregir un bug (diagnostico -> correccion -> validacion)
- /alfred spike <descripcion> - Investigacion exploratoria (exploracion -> conclusiones)
- /alfred ship - Preparar release (auditoria -> docs -> empaquetado -> despliegue)
- /alfred audit - Auditoria completa del codigo (calidad + seguridad + simplificacion)
- /alfred config - Ver o modificar la configuracion del plugin
- /alfred status - Estado de la sesion de trabajo activa
- /alfred help - Ayuda detallada de todos los comandos

### Reglas de operacion

- Las quality gates son infranqueables: si los tests no pasan, no se avanza.
- La seguridad se audita en cada fase que lo requiera.
- Se sigue TDD estricto en las fases de desarrollo.
- El agente El Paranoico vigila secretos en cada escritura de fichero."

# --- Configuracion del proyecto ---

# Si el usuario tiene un fichero de configuracion local, se incluye
# como contexto para que Claude adapte su comportamiento.
if [[ -f "$CONFIG_FILE" ]]; then
  CONFIG_CONTENT=$(cat "$CONFIG_FILE" 2>&1) || {
    echo "[Alfred Dev] Aviso: no se pudo leer '$CONFIG_FILE': $CONFIG_CONTENT" >&2
    CONFIG_CONTENT=""
  }
  if [[ -n "$CONFIG_CONTENT" ]]; then
    CONTEXT="${CONTEXT}

### Configuracion del proyecto

El usuario ha definido preferencias en .claude/alfred-dev.local.md:

\`\`\`
${CONFIG_CONTENT}
\`\`\`"
  fi
fi

# --- Estado de sesion activa ---

# Si existe un fichero de estado, se extrae informacion relevante
# para que Claude sepa en que punto del flujo se encuentra el usuario.
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

    # Si la sesion esta completada, no aporta contexto util
    if fase == 'completado':
        sys.exit(0)

    partes = []
    partes.append(f'Flujo activo: {comando}')
    partes.append(f'Fase actual: {fase}')
    if descripcion:
        partes.append(f'Descripcion: {descripcion}')
    if num_completadas > 0:
        nombres = [c['nombre'] for c in completadas]
        partes.append(f'Fases completadas: {\", \".join(nombres)}')

    print('\n'.join(partes))
except FileNotFoundError:
    sys.exit(0)
except (json.JSONDecodeError, KeyError) as e:
    print(f'[Alfred Dev] Aviso: estado de sesion corrupto o incompleto: {e}', file=sys.stderr)
    sys.exit(0)
" "$STATE_FILE" 2>&2) || echo "")

  if [[ -n "$STATE_INFO" ]]; then
    CONTEXT="${CONTEXT}

### Sesion de trabajo activa

${STATE_INFO}

Puedes continuar la sesion con /alfred status o avanzar a la siguiente fase."
  fi
fi

# --- Emision del JSON de salida ---

ESCAPED_CONTEXT=$(escape_for_json "$CONTEXT")

cat <<HOOK_JSON
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${ESCAPED_CONTEXT}"
  }
}
HOOK_JSON
