#!/usr/bin/env python3
"""PreToolUse: bloquea secretos en Write, Edit, Bash y tools MCP de escritura."""

from __future__ import annotations

import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.secrets import describe_secret_label, find_secret_label, is_secret_storage_path


_MCP_WRITE_MARKERS = (
    "write",
    "create",
    "update",
    "put",
    "patch",
    "append",
    "upload",
    "set_",
    "log_",
)


def _load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as exc:
        print(
            f"[El Paranoico] No he podido analizar la entrada del hook: {exc}. "
            "Operación bloqueada por precaución.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _collect_scan_targets(data: dict) -> list[tuple[str, str]]:
    tool_name = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    targets: list[tuple[str, str]] = []

    looks_like_write = tool_name in {"Write", "Edit"} or (
        not tool_name
        and (
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("content")
            or tool_input.get("new_string")
        )
    )
    if looks_like_write:
        path = str(tool_input.get("file_path") or tool_input.get("path") or "")
        content = str(tool_input.get("content") or tool_input.get("new_string") or "")
        if content:
            targets.append((path, content))
        return targets

    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if command:
            targets.append(("", command))
        return targets

    lowered = tool_name.lower()
    if lowered.startswith("mcp__") and any(marker in lowered for marker in _MCP_WRITE_MARKERS):
        serialized = json.dumps(tool_input, ensure_ascii=False, default=str)
        targets.append(("", serialized))

    return targets


def main() -> None:
    data = _load_payload()
    for path, content in _collect_scan_targets(data):
        if path and is_secret_storage_path(path):
            continue
        label = find_secret_label(content)
        if not label:
            continue
        print(
            "\n[El Paranoico] ALERTA DE SEGURIDAD - Operación bloqueada\n\n"
            f"He detectado un secreto ({describe_secret_label(label)}).\n"
            "No lo hardcodees. Usa .env, variables de entorno o un gestor de secretos.\n",
            file=sys.stderr,
        )
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
