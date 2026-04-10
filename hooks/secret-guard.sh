#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook PreToolUse para Write/Edit: guardia de secretos.
#
# Intercepta las operaciones de escritura de ficheros y analiza el contenido
# en busca de patrones que indiquen secretos expuestos (claves API, tokens,
# credenciales hardcodeadas). Si detecta un patrón sospechoso, bloquea la
# operación (exit 2) con un aviso en la voz de "El Paranoico".
#
# Los ficheros .env se excluyen del análisis porque son su sitio legítimo.
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PLUGIN_ROOT=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)

# --- Extraer la entrada del hook ---

# Claude pasa el JSON de la herramienta por stdin.
# Se extrae tool_input completo para analizar el contenido que se va a escribir.
# Política de seguridad: fail-closed. Si no se puede parsear la entrada,
# se bloquea la operación por precaución.
# La cadena '|| PARSE_FAILED=1' evita que set -e intercepte el fallo,
# permitiendo que el handler explícito actúe con exit 2 (bloqueo).
PARSE_FAILED=0
HOOK_INPUT=$(python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})

    # Determinar la ruta del fichero según la herramienta
    file_path = tool_input.get('file_path', '') or tool_input.get('path', '')

    # Determinar el contenido a analizar
    # Write usa 'content', Edit usa 'new_string'
    content = tool_input.get('content', '') or tool_input.get('new_string', '')

    # Emitir ambos valores separados por un delimitador único
    print(file_path)
    print('---HOOK_SEPARATOR_8f3a---')
    print(content)
except Exception as e:
    print(f'Error al parsear entrada del hook: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null) || PARSE_FAILED=1

if [[ $PARSE_FAILED -ne 0 ]]; then
  echo "[El Paranoico] No he podido analizar el contenido. Operación bloqueada por precaución." >&2
  exit 2
fi

# Separar ruta y contenido usando el delimitador robusto
FILE_PATH=$(echo "$HOOK_INPUT" | sed -n '1p')

# Verificar que el separador está presente en la salida
if ! echo "$HOOK_INPUT" | grep -q '^---HOOK_SEPARATOR_8f3a---$'; then
  echo "[El Paranoico] Salida del parser malformada. Operación bloqueada por precaución." >&2
  exit 2
fi

CONTENT=$(echo "$HOOK_INPUT" | sed '1,/^---HOOK_SEPARATOR_8f3a---$/d')

# Validar que FILE_PATH se extrajo correctamente.
# Si hay contenido pero no hay ruta, se bloquea (fail-closed): contenido
# sin destino conocido es sospechoso. Si ambos estan vacios, no hay nada
# que analizar y se permite la operacion.
if [[ -z "$FILE_PATH" ]]; then
  if [[ -n "$CONTENT" ]]; then
    echo "[El Paranoico] Hay contenido pero no se pudo determinar la ruta del fichero. Operación bloqueada por precaución." >&2
    exit 2
  fi
  exit 0
fi

# --- Detección canónica de secretos ---

# El análisis delega en core/secrets.py para mantener exactamente la misma
# fuente de verdad que usa la sanitización de memoria. Si el helper falla,
# este hook bloquea (fail-closed) porque se trata de una guardia de escritura.
FOUND_SECRET=""
SCAN_FAILED=0
SCAN_RESULT=$(
  printf '%s' "$CONTENT" | \
    ALFRED_DEV_ROOT="$PLUGIN_ROOT" TARGET_FILE_PATH="$FILE_PATH" python3 -c '
import os
import sys

project_root = os.environ.get("ALFRED_DEV_ROOT", "")
if project_root:
    sys.path.insert(0, project_root)

from core.secrets import (  # noqa: E402
    describe_secret_label,
    find_secret_label,
    is_secret_storage_path,
)

file_path = os.environ.get("TARGET_FILE_PATH", "")
content = sys.stdin.read()

if is_secret_storage_path(file_path):
    print("ALLOW")
    raise SystemExit(0)

label = find_secret_label(content)
if label:
    print(f"BLOCK:{describe_secret_label(label)}")
' 2>/dev/null
) || SCAN_FAILED=1

if [[ $SCAN_FAILED -ne 0 ]]; then
  echo "[El Paranoico] No he podido analizar secretos con la fuente canónica. Operación bloqueada por precaución." >&2
  exit 2
fi

if [[ "$SCAN_RESULT" == "ALLOW" ]]; then
  exit 0
fi

if [[ "$SCAN_RESULT" == BLOCK:* ]]; then
  FOUND_SECRET="${SCAN_RESULT#BLOCK:}"
fi

# --- Decisión: bloquear o permitir ---

if [[ -n "$FOUND_SECRET" ]]; then
  # Bloquear con voz de El Paranoico y sugerir el fichero correcto
  cat >&2 <<EOF

[El Paranoico] ALERTA DE SEGURIDAD - Operación bloqueada

He detectado lo que parece un secreto en el fichero: ${FILE_PATH}
Patrón encontrado: ${FOUND_SECRET}

Los secretos no se hardcodean en el código. Nunca. Ni "solo para probar".

Donde ponerlo:
  - En un fichero .env, .env.local o local.env (asegúrate de que está en .gitignore)
  - En variables de entorno del sistema o del CI/CD
  - En un gestor de secretos (Vault, AWS Secrets Manager, etc.)

Pide al usuario que te pase el valor para que lo guardes en el sitio
correcto (.env, .env.local, local.env o el que use el proyecto). En el código fuente
solo debe aparecer la referencia: os.environ["MI_CLAVE"] o process.env.MI_CLAVE.

Confianza cero. Ni en ti, ni en mi, ni en nadie.

EOF
  exit 2
fi

# Todo limpio, permitir la operación
exit 0
