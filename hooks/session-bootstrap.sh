#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook síncrono de bootstrap para SessionStart.
#
# Se ejecuta antes del contexto rico de session-start.sh para preparar, desde
# el primer arranque, los artefactos locales que necesitan los comandos
# helper-first en Claude Code CLI:
# - configuración local mínima (.claude/alfred-dev.local.md)
# - SQLite de memoria del proyecto
# - permisos locales de Claude Code (.claude/settings.local.json y .claude/settings.json)
# - wrapper local .claude/alfred-continuity.py
# - iteración "session" activa para el dashboard/memoria
#
# No emite contexto adicional. Su único trabajo es dejar el proyecto listo y
# salir rápido.
# ---------------------------------------------------------------------------

set -euo pipefail

PROJECT_DIR="${PWD}"
PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOCAL_CONFIG="${PROJECT_DIR}/.claude/alfred-dev.local.md"
MEMORY_DB="${PROJECT_DIR}/.claude/alfred-memory.db"
CLAUDE_PROJECT_SETTINGS_LOCAL="${PROJECT_DIR}/.claude/settings.local.json"
CLAUDE_PROJECT_SETTINGS_SHARED="${PROJECT_DIR}/.claude/settings.json"
CONTINUITY_WRAPPER="${PROJECT_DIR}/.claude/alfred-continuity.py"

mkdir -p "${PROJECT_DIR}/.claude"

if [[ ! -f "$LOCAL_CONFIG" ]]; then
  cat > "$LOCAL_CONFIG" <<'LOCALCFG'
---
autonomia:
  producto: autonomo
  arquitectura: autonomo
  desarrollo: autonomo
  calidad: autonomo
  documentacion: autonomo
  entrega: autonomo
memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
  capture_decisions: true
  capture_commits: true
  retention_days: 365
---

# Configuración local de Alfred Dev

Este fichero se genera automáticamente en la primera sesión.
Puedes personalizarlo con `/alfred-dev:config`.
LOCALCFG
else
  PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import re, sys

config_path = sys.argv[1]
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

memoria_block = '''memoria:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365'''

autonomia_block = '''autonomia:
  producto: autonomo
  arquitectura: autonomo
  desarrollo: autonomo
  calidad: autonomo
  documentacion: autonomo
  entrega: autonomo'''

if not re.search(r'memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true', content):
    if content.startswith('---'):
        idx = content.index('---') + 3
        content = content[:idx] + '\n' + memoria_block + content[idx:]
    else:
        content = '---\n' + memoria_block + '\n---\n\n' + content

if not re.search(r'(^|\n)autonomia:\s*\n', content):
    if content.startswith('---'):
        idx = content.index('---') + 3
        content = content[:idx] + '\n' + autonomia_block + content[idx:]
    else:
        content = '---\n' + autonomia_block + '\n---\n\n' + content

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)
" "$LOCAL_CONFIG" 2>/dev/null || true
fi

if [[ ! -f "$MEMORY_DB" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.memory import MemoryDB
db = MemoryDB(sys.argv[1])
db.close()
" "$MEMORY_DB" "$PLUGIN_ROOT" 2>/dev/null || echo "[Alfred Dev] Aviso: no se pudo crear la BD de memoria" >&2
fi

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

if [[ -f "$MEMORY_DB" ]]; then
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
        payload={'source': 'session-bootstrap.sh'},
        iteration_id=iteration_id,
    )
db.close()
" "$MEMORY_DB" "$PLUGIN_ROOT" 2>/dev/null || true
fi

exit 0
