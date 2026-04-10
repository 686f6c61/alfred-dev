#!/usr/bin/env bash
# stop-server.sh — Detiene el servidor visual de Alfred.
#
# Uso:
#   stop-server.sh <session_dir>
#
# Lee el PID desde <session_dir>/state/server.pid, envia SIGTERM y espera
# hasta 2 s. Si el proceso no termina, envia SIGKILL. Limpia los ficheros
# de estado y elimina el directorio de sesion si esta bajo /tmp.
#
# Salida JSON en stdout:
#   {"status":"stopped"}          — El servidor se detuvo correctamente.
#   {"status":"not_running"}      — No habia servidor activo en ese directorio.
#   {"status":"failed","error":"..."} — No se pudo detener el proceso.

set -euo pipefail

# ---------------------------------------------------------------------------
# Validacion de argumentos
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  printf '{"status":"failed","error":"Uso: stop-server.sh <session_dir>"}\n'
  exit 1
fi

SESSION_DIR="$1"

if [[ ! -d "$SESSION_DIR" ]]; then
  printf '{"status":"not_running"}\n'
  exit 0
fi

PID_FILE="${SESSION_DIR}/state/server.pid"
LOG_FILE="${SESSION_DIR}/state/server.log"
SERVER_INFO_FILE="${SESSION_DIR}/state/server-info"

# ---------------------------------------------------------------------------
# Comprobar si hay un PID registrado
# ---------------------------------------------------------------------------

if [[ ! -f "$PID_FILE" ]]; then
  printf '{"status":"not_running"}\n'
  exit 0
fi

SERVER_PID="$(cat "$PID_FILE" 2>/dev/null | tr -d '[:space:]')"

if [[ -z "$SERVER_PID" ]]; then
  rm -f "$PID_FILE"
  printf '{"status":"not_running"}\n'
  exit 0
fi

REAL_SESSION_DIR="$(cd "$SESSION_DIR" 2>/dev/null && pwd -P || echo "$SESSION_DIR")"

get_process_command() {
  local pid="$1"
  ps eww -p "$pid" -o command= 2>/dev/null || ps -p "$pid" -o command= 2>/dev/null || true
}

is_expected_visual_process() {
  local pid="$1"
  local command_line
  local server_info_pid=""
  local server_info_session=""
  command_line="$(get_process_command "$pid")"
  [[ -n "$command_line" ]] || return 1
  [[ "$command_line" == *"server.cjs"* ]] || return 1

  if [[ "$command_line" == *"ALFRED_VISUAL_DIR=$REAL_SESSION_DIR"* ]]; then
    return 0
  fi

  if [[ -f "$SERVER_INFO_FILE" ]]; then
    server_info_pid="$(python3 - <<'PY' "$SERVER_INFO_FILE"
import json, sys
try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    print("")
else:
    print(data.get("server_pid", ""))
PY
)"
    server_info_session="$(python3 - <<'PY' "$SERVER_INFO_FILE"
import json, os, sys
try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    print("")
else:
    value = data.get("session_dir", "")
    if value:
        print(os.path.realpath(value))
    else:
        print("")
PY
)"
  fi

  [[ "$server_info_pid" == "$pid" ]] || return 1
  [[ "$server_info_session" == "$REAL_SESSION_DIR" ]] || return 1
  return 0
}

# ---------------------------------------------------------------------------
# Verificar si el proceso esta vivo
# ---------------------------------------------------------------------------

if ! kill -0 "$SERVER_PID" 2>/dev/null || ! is_expected_visual_process "$SERVER_PID"; then
  # El proceso ya no existe; limpiar residuos
  rm -f "$PID_FILE" "$LOG_FILE" "$SERVER_INFO_FILE"
  printf '{"status":"not_running"}\n'
  exit 0
fi

# ---------------------------------------------------------------------------
# Enviar SIGTERM y esperar hasta 2 s (poll cada 0.1 s)
# ---------------------------------------------------------------------------

kill -TERM "$SERVER_PID" 2>/dev/null || true

_waited=0
while kill -0 "$SERVER_PID" 2>/dev/null && [[ $_waited -lt 20 ]]; do
  sleep 0.1
  (( _waited++ )) || true
done

# ---------------------------------------------------------------------------
# Fallback a SIGKILL si el proceso sigue vivo
# ---------------------------------------------------------------------------

if kill -0 "$SERVER_PID" 2>/dev/null; then
  kill -KILL "$SERVER_PID" 2>/dev/null || true

  # Esperar un segundo mas para confirmar la muerte
  _kill_waited=0
  while kill -0 "$SERVER_PID" 2>/dev/null && [[ $_kill_waited -lt 10 ]]; do
    sleep 0.1
    (( _kill_waited++ )) || true
  done

  # Si sigue vivo tras SIGKILL, informar del fallo
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    printf '{"status":"failed","error":"No se pudo detener el proceso %s"}\n' "$SERVER_PID"
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# Limpiar ficheros de estado
# ---------------------------------------------------------------------------

rm -f "$PID_FILE" "$LOG_FILE"

# ---------------------------------------------------------------------------
# Eliminar el directorio de sesion solo si esta bajo /tmp.
# Los directorios persistentes (dentro de un proyecto) se conservan para
# que el usuario pueda inspeccionar el contenido generado.
# ---------------------------------------------------------------------------

# Normalizar la ruta real para comparar con /tmp de forma segura
REAL_TMP="$(cd /tmp 2>/dev/null && pwd -P || echo "/tmp")"

if [[ "$REAL_SESSION_DIR" == "${REAL_TMP}/"* ]]; then
  rm -rf "$SESSION_DIR"
fi

printf '{"status":"stopped"}\n'
