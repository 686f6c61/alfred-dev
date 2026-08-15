#!/usr/bin/env python3
"""UserPromptSubmit fail-open: inyecta la ruta Alfred si el texto no trae slash."""

from __future__ import annotations

import json
import os
import sys


def _plugin_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0

    prompt = (
        data.get("prompt")
        or data.get("user_prompt")
        or data.get("content")
        or ""
    )
    if not isinstance(prompt, str) or not prompt.strip():
        return 0

    try:
        root = _plugin_root()
        if root not in sys.path:
            sys.path.insert(0, root)
        from core.prompt_route import classify_prompt, render_route_hint

        match = classify_prompt(prompt)
        if not match:
            return 0
        hint = render_route_hint(match)
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": hint,
                    }
                },
                ensure_ascii=False,
            )
        )
    except Exception as exc:
        print(f"[prompt-route] aviso: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
