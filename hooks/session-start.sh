#!/usr/bin/env bash
# SessionStart sincrono y corto. No llama a GitHub. No reescribe permisos.
# Rutas: /alfred-dev:alfred /alfred-dev:feature /alfred-dev:audit /alfred-dev:progress /alfred-dev:retomar
# Lucius bajo demanda. Agent Teams solo si ya está activo.

set -euo pipefail

PROJECT_DIR="${PWD}"
PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)

emit_hook_json() {
  python3 -c "
import json, sys
context = sys.stdin.read()
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context,
    }
}, ensure_ascii=False))
"
}

FALLBACK="## Cómo hablarle a Alfred

Si el usuario describe trabajo, un bug, retomar, entregar o preguntar qué toca sin un slash command, actúa como /alfred-dev:alfred: elige la ruta y ejecútala. No ofrezcas el catálogo.

Ruta principal: /alfred-dev:alfred. Flujos: /alfred-dev:feature, /alfred-dev:quick, /alfred-dev:fix, /alfred-dev:spike, /alfred-dev:audit, /alfred-dev:ship. Estado: /alfred-dev:progress. Continuar: /alfred-dev:retomar.

Si Agent Teams está activo en esta sesión, úsalo para fases en paralelo; si no, usa la herramienta Agent. No reescribas .claude/settings.json.

## Briefing

No hay sesión abierta. Pregunta qué quiere hacer o mapea el repo si es brownfield.
"

CONTEXT=$(
  PYTHONPATH="${PLUGIN_ROOT}" python3 - "${PROJECT_DIR}" <<'PY' 2>/dev/null || true
import sys
from core.session_brief import render_session_start_context

print(render_session_start_context(sys.argv[1]), end="")
PY
)

if [[ -z "${CONTEXT//[[:space:]]/}" ]]; then
  CONTEXT="$FALLBACK"
fi

printf '%s' "$CONTEXT" | emit_hook_json
