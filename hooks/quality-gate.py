#!/usr/bin/env python3
"""
Hook PostToolUse para Bash: quality gate de tests.

Intercepta la salida de comandos Bash para detectar si se han ejecutado
tests y, en caso afirmativo, analizar si han fallado. Cuando detecta
fallos, informa por stderr con la voz de "El Rompe-cosas" (QA).

Delega la deteccion de comandos y resultados a ``evidence_guard_lib``
para mantener una unica fuente de verdad en los patrones.

Solo actua sobre comandos que coincidan con runners de tests conocidos.
El resto de comandos Bash pasan sin inspeccion.
"""

import json
import os
import sys

# Anadir el directorio de hooks al path para importar la libreria
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from evidence_guard_lib import is_test_command, detect_test_result


def _get_tool_result(data: dict) -> dict:
    """Normaliza payloads historicos y actuales del runtime de hooks."""
    tool_result = data.get("tool_result")
    if isinstance(tool_result, dict):
        return tool_result

    tool_output = data.get("tool_output")
    if isinstance(tool_output, dict):
        return tool_output

    return {}


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae el comando ejecutado y su salida,
    y determina si hay tests fallidos. Si los hay, emite un aviso
    por stderr con la voz de El Rompe-cosas.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(
            f"[quality-gate] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La monitorizacion de tests esta desactivada para este comando.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    tool_result = _get_tool_result(data)

    command = tool_input.get("command", "")

    if not command or not is_test_command(command):
        sys.exit(0)

    stdout = tool_result.get("stdout", "") or tool_result.get("output", "")
    stderr_out = tool_result.get("stderr", "")
    exit_code = tool_result.get("exit_code")
    output = f"{stdout}\n{stderr_out}"

    if detect_test_result(output, exit_code=exit_code) == "fail":
        print(
            "\n"
            "[El Rompe-cosas] He pillado tests rotos\n"
            "\n"
            "Los tests no pasan. Sorpresa: ninguna.\n"
            "No se avanza con tests en rojo. Asi funciona esto.\n"
            "\n"
            "Repasa la salida, corrige los fallos y vuelve a ejecutar.\n"
            "Ese edge case que no contemplaste? Lo encontre.\n",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
