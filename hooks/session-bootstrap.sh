#!/usr/bin/env bash
# Hook sincrono de SessionStart: prepara artefactos locales del proyecto.
# No toca settings.json ni settings.local.json de Claude Code.

set -euo pipefail

PROJECT_DIR="${PWD}"
PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOCAL_CONFIG="${PROJECT_DIR}/.claude/alfred-dev.local.md"
MEMORY_DB="${PROJECT_DIR}/.claude/alfred-memory.db"
CONTINUITY_WRAPPER="${PROJECT_DIR}/.claude/alfred-continuity.py"

mkdir -p "${PROJECT_DIR}/.claude"

PYTHONPATH="${PLUGIN_ROOT}" python3 - "$LOCAL_CONFIG" <<'PY' 2>/dev/null || true
import sys
from core.config_loader import ensure_bootstrap_local_config

ensure_bootstrap_local_config(sys.argv[1])
PY

MEMORY_ENABLED=$(PYTHONPATH="${PLUGIN_ROOT}" python3 - "$PROJECT_DIR" <<'PY' 2>/dev/null || true
from core.memory_config import is_memory_enabled
import sys

print("yes" if is_memory_enabled(sys.argv[1]) else "no")
PY
)

if [[ "${MEMORY_ENABLED:-no}" == "yes" && ! -f "$MEMORY_DB" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.memory import MemoryDB
db = MemoryDB(sys.argv[1])
db.close()
" "$MEMORY_DB" "$PLUGIN_ROOT" 2>/dev/null || echo "[Alfred Dev] Aviso: no se pudo crear la BD de memoria" >&2
fi

python3 - "$CONTINUITY_WRAPPER" "$PLUGIN_ROOT" <<'PY' 2>/dev/null || \
  echo "[Alfred Dev] Aviso: no se pudo preparar el wrapper local de continuidad" >&2
import os
import sys

wrapper_path = sys.argv[1]
plugin_root = sys.argv[2]

content = f"""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

EMBEDDED_PLUGIN_ROOT = {plugin_root!r}
PLUGIN_NAME = "alfred-dev"


def _valid_root(path):
    if not path:
        return None
    root = Path(path).expanduser()
    try:
        root = root.resolve()
    except OSError:
        root = root.absolute()
    if (root / "core" / "continuity.py").is_file():
        return str(root)
    return None


def _cache_candidates():
    cache_dir = Path.home() / ".claude" / "plugins" / "cache" / PLUGIN_NAME
    if not cache_dir.is_dir():
        return []
    candidates = []
    for marker in cache_dir.rglob("core/continuity.py"):
        root = marker.parents[1]
        plugin_json = root / ".claude-plugin" / "plugin.json"
        try:
            mtime = plugin_json.stat().st_mtime
        except OSError:
            try:
                mtime = root.stat().st_mtime
            except OSError:
                mtime = 0
        candidates.append((mtime, str(root)))
    return [root for _mtime, root in sorted(candidates, reverse=True)]


def _resolve_plugin_root():
    candidates = [
        os.environ.get("CLAUDE_PLUGIN_ROOT"),
        os.environ.get("ALFRED_DEV_PLUGIN_ROOT"),
        EMBEDDED_PLUGIN_ROOT,
    ]
    candidates.extend(_cache_candidates())
    for candidate in candidates:
        resolved = _valid_root(candidate)
        if resolved:
            return resolved
    sys.stderr.write("[Alfred Dev] No se pudo resolver la instalacion activa del plugin. Ejecuta /reload-plugins o reinstala alfred-dev.\\n")
    raise SystemExit(2)


PLUGIN_ROOT = _resolve_plugin_root()
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

if [[ "${MEMORY_ENABLED:-no}" == "yes" && -f "$MEMORY_DB" ]]; then
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
