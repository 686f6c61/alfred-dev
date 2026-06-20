#!/usr/bin/env bash
# start-server.sh — Arranca el servidor visual de Alfred.
#
# Uso:
#   start-server.sh [--project-dir <ruta>] [--host <host>] [--url-host <host>]
#                   [--foreground | --background]
#
# En modo foreground el proceso de Node se ejecuta directamente (bloqueante).
# En modo background se lanza con nohup + disown y se espera hasta 5 s a que
# aparezca la linea "server-started" en el log.
#
# Salida JSON en stdout:
#   Exito:  {"type":"server-started","port":...,"url":"...","session_dir":"..."}
#   Error:  {"type":"error","message":"..."}

set -euo pipefail
umask 077

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

json_error() {
  local message="$1"
  printf '{"type":"error","message":"%s"}\n' "$(json_escape "$message")"
}

require_value() {
  local flag="$1"
  if [[ $# -lt 2 || -z "${2:-}" || "${2:-}" == --* ]]; then
    json_error "Falta valor para ${flag}"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Valores por defecto
# ---------------------------------------------------------------------------

PROJECT_DIR=""
HOST="127.0.0.1"
URL_HOST=""
MODE=""          # foreground | background (se resuelve abajo)

# ---------------------------------------------------------------------------
# Parseo de argumentos
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir)
      require_value "$1" "${2:-}"
      PROJECT_DIR="$2"
      shift 2
      ;;
    --host)
      require_value "$1" "${2:-}"
      HOST="$2"
      shift 2
      ;;
    --url-host)
      require_value "$1" "${2:-}"
      URL_HOST="$2"
      shift 2
      ;;
    --foreground)
      MODE="foreground"
      shift
      ;;
    --background)
      MODE="background"
      shift
      ;;
    *)
      json_error "Argumento desconocido: $1"
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Autodeteccion de entorno que exige foreground
# Codex CI y entornos Windows (MSYS/Cygwin) no soportan nohup + disown bien.
# ---------------------------------------------------------------------------

if [[ -z "$MODE" ]]; then
  if [[ -n "${CODEX_CI:-}" ]]; then
    MODE="foreground"
  elif [[ "${MSYSTEM:-}" == MINGW* ]] || [[ "${MSYSTEM:-}" == MSYS* ]] || \
       [[ "${OSTYPE:-}" == cygwin* ]]; then
    MODE="foreground"
  else
    MODE="background"
  fi
fi

# ---------------------------------------------------------------------------
# Directorio del script — necesario para localizar server.cjs
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_CJS="$SCRIPT_DIR/server.cjs"

if ! command -v node >/dev/null 2>&1; then
  json_error "Node.js no esta en PATH"
  exit 1
fi

if [[ ! -f "$SERVER_CJS" ]]; then
  json_error "No se encontro server.cjs en $SCRIPT_DIR"
  exit 1
fi

# ---------------------------------------------------------------------------
# Resolucion del PID propietario (abuelo del proceso actual).
# Claude Code invoca este script como hijo; el "dueno" real es el proceso
# que lanzo Claude Code, es decir el abuelo (PPID del PPID).
# ---------------------------------------------------------------------------

OWNER_PID=""
_ppid="$$"
_parent=""
_grandparent=""

# Intentar obtener el PPID del proceso actual
_parent="$(ps -o ppid= -p "$_ppid" 2>/dev/null | tr -d ' ')" || true

if [[ -n "$_parent" && "$_parent" != "0" ]]; then
  _grandparent="$(ps -o ppid= -p "$_parent" 2>/dev/null | tr -d ' ')" || true
  if [[ -n "$_grandparent" && "$_grandparent" != "0" ]]; then
    OWNER_PID="$_grandparent"
  fi
fi

# ---------------------------------------------------------------------------
# Construccion del directorio de sesion
# ---------------------------------------------------------------------------

TIMESTAMP="$(date +%s)"

if [[ -n "$PROJECT_DIR" ]]; then
  # Directorio persistente dentro del proyecto
  SESSION_DIR="${PROJECT_DIR}/.alfred-dev/visual/${$}-${TIMESTAMP}"
else
  # Directorio temporal si no hay proyecto
  SESSION_DIR="/tmp/alfred-visual-${$}-${TIMESTAMP}"
fi

# Crear subdirectorios requeridos por server.cjs
mkdir -p "${SESSION_DIR}/content" "${SESSION_DIR}/state"

PID_FILE="${SESSION_DIR}/state/server.pid"
LOG_FILE="${SESSION_DIR}/state/server.log"

cleanup_failed_start() {
  rm -f "$PID_FILE"
}

# ---------------------------------------------------------------------------
# Matar servidor anterior si existe un PID file de una sesion anterior.
# Esto solo aplica cuando reutilizamos un directorio de sesion fijo; en este
# script cada sesion tiene un directorio unico, pero dejamos la logica por
# si en el futuro se pasa un SESSION_DIR ya existente.
# ---------------------------------------------------------------------------

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null || true
    # Esperar hasta 2 s a que muera
    _waited=0
    while kill -0 "$OLD_PID" 2>/dev/null && [[ $_waited -lt 20 ]]; do
      sleep 0.1
      (( _waited++ )) || true
    done
  fi
  rm -f "$PID_FILE"
fi

# ---------------------------------------------------------------------------
# Variables de entorno para el proceso Node
# ---------------------------------------------------------------------------

export ALFRED_VISUAL_DIR="$SESSION_DIR"
export ALFRED_VISUAL_HOST="$HOST"
if [[ -n "$URL_HOST" ]]; then
  export ALFRED_VISUAL_URL_HOST="$URL_HOST"
fi
if [[ -n "$OWNER_PID" ]]; then
  export ALFRED_VISUAL_OWNER_PID="$OWNER_PID"
fi

# ---------------------------------------------------------------------------
# Arranque en modo foreground (bloqueante)
# ---------------------------------------------------------------------------

if [[ "$MODE" == "foreground" ]]; then
  exec node "$SERVER_CJS"
fi

# ---------------------------------------------------------------------------
# Arranque en modo background
# ---------------------------------------------------------------------------

# Iniciar el servidor redirigiendo stdout/stderr al log
nohup node "$SERVER_CJS" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
disown "$SERVER_PID" 2>/dev/null || true

# Guardar PID para que stop-server.sh pueda detenerlo
echo "$SERVER_PID" > "$PID_FILE"

# Esperar hasta 5 s a que el servidor emita la linea "server-started"
MAX_WAIT=50   # 50 iteraciones x 0.1 s = 5 s
_iter=0
SERVER_STARTED_LINE=""

while [[ $_iter -lt $MAX_WAIT ]]; do
  sleep 0.1
  (( _iter++ )) || true

  # Comprobar que el proceso sigue vivo
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    ERROR_LOG="$(cat "$LOG_FILE" 2>/dev/null || echo "")"
    cleanup_failed_start
    printf '{"type":"error","message":"El proceso del servidor termino inesperadamente","session_dir":"%s","log":%s}\n' \
      "$SESSION_DIR" \
      "$(printf '%s' "$ERROR_LOG" | node -e 'let d="";process.stdin.on("data",c=>d+=c);process.stdin.on("end",()=>process.stdout.write(JSON.stringify(d)))' 2>/dev/null || printf '""')"
    exit 1
  fi

  # Buscar linea JSON con type=server-started en el log
  if [[ -f "$LOG_FILE" ]]; then
    SERVER_STARTED_LINE="$(grep -m1 '"server-started"' "$LOG_FILE" 2>/dev/null || true)"
    if [[ -n "$SERVER_STARTED_LINE" ]]; then
      break
    fi
  fi
done

# Verificar si finalmente obtuvimos la confirmacion
if [[ -z "$SERVER_STARTED_LINE" ]]; then
  # Matar el proceso huerfano si aun vive
  kill "$SERVER_PID" 2>/dev/null || true
  cleanup_failed_start
  printf '{"type":"error","message":"El servidor no arranco en 5 segundos","session_dir":"%s"}\n' "$SESSION_DIR"
  exit 1
fi

# Enriquecer la salida con session_dir y pid_file para que el llamador
# pueda invocar stop-server.sh correctamente.
# Pasar datos como variable de entorno en lugar de interpolar en codigo
# para evitar inyeccion de codigo a traves del contenido del log.
ALFRED_RAW_LINE="$SERVER_STARTED_LINE" \
ALFRED_SESSION_DIR="$SESSION_DIR" \
ALFRED_PID_FILE="$PID_FILE" \
ALFRED_SERVER_PID="$SERVER_PID" \
node -e '
  const line = JSON.parse(process.env.ALFRED_RAW_LINE);
  const out = Object.assign({}, line, {
    session_dir: process.env.ALFRED_SESSION_DIR,
    pid_file: process.env.ALFRED_PID_FILE,
    server_pid: Number(process.env.ALFRED_SERVER_PID)
  });
  process.stdout.write(JSON.stringify(out) + "\n");
'
