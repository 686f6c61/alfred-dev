#!/usr/bin/env python3
"""SessionEnd fail-open: cierra Memory UI y deja el bloque de cierre."""

from __future__ import annotations

import os
import sys

def _plugin_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    project_dir = os.getcwd()
    try:
        root = _plugin_root()
        if root not in sys.path:
            sys.path.insert(0, root)
        from core.continuity import stop_memory_ui

        stop_memory_ui(project_dir)
    except Exception as exc:
        print(f"[session-end] aviso: no se pudo detener Memory UI: {exc}", file=sys.stderr)
    try:
        from core.hygiene import write_session_cierre

        write_session_cierre(project_dir)
    except Exception as exc:
        print(f"[session-end] aviso: no se pudo escribir el cierre: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
