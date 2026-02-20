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

# --- Excluir ficheros .env ---

# Los ficheros .env son el lugar correcto para guardar secretos.
# No tiene sentido bloquear escrituras ahí.
if [[ "$FILE_PATH" == *.env ]] || [[ "$FILE_PATH" == *.env.* ]] || [[ "$(basename "$FILE_PATH")" == .env* ]]; then
  exit 0
fi

# --- Detección de patrones de secretos ---

# Se analizan los patrones más comunes de credenciales expuestas.
# Cada entrada del array contiene: "regex|descripción" separados por pipe.
# El bucle comprueba cada patrón y se detiene en la primera coincidencia.

SECRET_PATTERNS=(
  'AKIA[0-9A-Z]{16}|AWS Access Key (patrón AKIA...)'
  'sk-[a-zA-Z0-9]{20,}|Clave API con prefijo sk- (OpenAI, Stripe u otro)'
  'sk-ant-[a-zA-Z0-9\-]{20,}|Anthropic API Key'
  '(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})|GitHub Personal Access Token'
  'xox[bpsa]-[a-zA-Z0-9\-]{10,}|Slack Token'
  'AIza[0-9A-Za-z\-_]{35}|Google API Key (patrón AIza...)'
  'SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}|SendGrid API Key'
  '-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----|Clave privada PEM/SSH'
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|JWT token hardcodeado'
  '(mysql|postgresql|postgres|mongodb(\+srv)?|redis|amqp)://[^[:space:]"'"'"']{10,}@|Connection string con credenciales'
  'https://hooks\.slack\.com/services/[A-Za-z0-9/]+|Slack Webhook URL'
  'https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+|Discord Webhook URL'
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

# Asignaciones directas de secretos en código:
# password = "...", api_key = "...", secret = "...", token = "..."
# Se busca tanto en sintaxis Python/Ruby (=) como JS/TS (= o :)
# Este patrón se comprueba aparte porque usa grep -i (case insensitive)
if [[ -z "$FOUND_SECRET" ]] && echo "$CONTENT" | grep -qiE '(password|passwd|api_key|apikey|api_secret|secret_key|auth_token|access_token|private_key)\s*[:=]\s*["\x27][^"\x27]{8,}["\x27]'; then
  FOUND_SECRET="Credencial hardcodeada en asignación"
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
  - En un fichero .env o local.env (asegúrate de que está en .gitignore)
  - En variables de entorno del sistema o del CI/CD
  - En un gestor de secretos (Vault, AWS Secrets Manager, etc.)

Pide al usuario que te pase el valor para que lo guardes en el sitio
correcto (.env, local.env o el que use el proyecto). En el código fuente
solo debe aparecer la referencia: os.environ["MI_CLAVE"] o process.env.MI_CLAVE.

Confianza cero. Ni en ti, ni en mi, ni en nadie.

EOF
  exit 2
fi

# Todo limpio, permitir la operación
exit 0
