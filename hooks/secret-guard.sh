#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook PreToolUse para Write/Edit: guardia de secretos.
#
# Intercepta las operaciones de escritura de ficheros y analiza el contenido
# en busca de patrones que indiquen secretos expuestos (claves API, tokens,
# credenciales hardcodeadas). Si detecta un patron sospechoso, bloquea la
# operacion (exit 2) con un aviso en la voz de "El Paranoico".
#
# Los ficheros .env se excluyen del analisis porque son su sitio legitimo.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Extraer la entrada del hook ---

# Claude pasa el JSON de la herramienta por stdin.
# Se extrae tool_input completo para analizar el contenido que se va a escribir.
# Politica de seguridad: fail-closed. Si no se puede parsear la entrada,
# se bloquea la operacion por precaucion.
HOOK_INPUT=$(python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})

    # Determinar la ruta del fichero segun la herramienta
    file_path = tool_input.get('file_path', '') or tool_input.get('path', '')

    # Determinar el contenido a analizar
    # Write usa 'content', Edit usa 'new_string'
    content = tool_input.get('content', '') or tool_input.get('new_string', '')

    # Emitir ambos valores separados por un delimitador unico
    print(file_path)
    print('---HOOK_SEPARATOR_8f3a---')
    print(content)
except Exception as e:
    print(f'Error al parsear entrada del hook: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

PARSE_EXIT=$?
if [[ $PARSE_EXIT -ne 0 ]]; then
  echo "[El Paranoico] No he podido analizar el contenido. Operacion bloqueada por precaucion." >&2
  exit 2
fi

# Separar ruta y contenido usando el delimitador robusto
FILE_PATH=$(echo "$HOOK_INPUT" | sed -n '1p')

# Verificar que el separador esta presente en la salida
if ! echo "$HOOK_INPUT" | grep -q '^---HOOK_SEPARATOR_8f3a---$'; then
  echo "[El Paranoico] Salida del parser malformada. Operacion bloqueada por precaucion." >&2
  exit 2
fi

CONTENT=$(echo "$HOOK_INPUT" | sed '1,/^---HOOK_SEPARATOR_8f3a---$/d')

# --- Excluir ficheros .env ---

# Los ficheros .env son el lugar correcto para guardar secretos.
# No tiene sentido bloquear escrituras ahi.
if [[ "$FILE_PATH" == *.env ]] || [[ "$FILE_PATH" == *.env.* ]] || [[ "$(basename "$FILE_PATH")" == .env* ]]; then
  exit 0
fi

# --- Deteccion de patrones de secretos ---

# Se analizan los patrones mas comunes de credenciales expuestas.
# Cada entrada del array contiene: "regex|descripcion" separados por pipe.
# El bucle comprueba cada patron y se detiene en la primera coincidencia.

SECRET_PATTERNS=(
  'AKIA[0-9A-Z]{16}|AWS Access Key (patron AKIA...)'
  'sk-[a-zA-Z0-9]{20,}|Clave API con prefijo sk- (OpenAI, Stripe u otro)'
  '(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})|GitHub Personal Access Token'
  'xox[bpsa]-[a-zA-Z0-9\-]{10,}|Slack Token'
  'AIza[0-9A-Za-z\-_]{35}|Google API Key (patron AIza...)'
  'SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}|SendGrid API Key'
)

FOUND_SECRET=""

for entry in "${SECRET_PATTERNS[@]}"; do
  pattern="${entry%%|*}"
  description="${entry#*|}"
  if echo "$CONTENT" | grep -qE "$pattern"; then
    FOUND_SECRET="$description"
    break
  fi
done

# Asignaciones directas de secretos en codigo:
# password = "...", api_key = "...", secret = "...", token = "..."
# Se busca tanto en sintaxis Python/Ruby (=) como JS/TS (= o :)
# Este patron se comprueba aparte porque usa grep -i (case insensitive)
if [[ -z "$FOUND_SECRET" ]] && echo "$CONTENT" | grep -qiE '(password|passwd|api_key|apikey|api_secret|secret_key|auth_token|access_token|private_key)\s*[:=]\s*["\x27][^"\x27]{8,}["\x27]'; then
  FOUND_SECRET="Credencial hardcodeada en asignacion"
fi

# --- Decision: bloquear o permitir ---

if [[ -n "$FOUND_SECRET" ]]; then
  # Bloquear con voz de El Paranoico
  cat >&2 <<EOF

[El Paranoico] ALERTA DE SEGURIDAD - Operacion bloqueada

He detectado lo que parece un secreto en el fichero: ${FILE_PATH}
Patron encontrado: ${FOUND_SECRET}

Los secretos no se hardcodean en el codigo. Nunca. Ni "solo para probar".
Usa variables de entorno, ficheros .env (que estan en .gitignore) o un
gestor de secretos. Pero en el codigo fuente, jamas.

Confianza cero. Ni en ti, ni en mi, ni en nadie.

EOF
  exit 2
fi

# Todo limpio, permitir la operacion
exit 0
