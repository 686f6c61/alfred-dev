#!/usr/bin/env python3
"""
Hook PostToolUse para Bash: verificacion de evidencia.

Implementa el patron «evidencia antes que afirmaciones» inspirado en el
plugin Ralph Loop. Registra en un fichero temporal las ejecuciones de
tests detectadas durante la sesion, de modo que otros componentes del
plugin (stop-hook, check_gate) puedan verificar que cuando un agente
afirma que los tests pasan, efectivamente se ejecutaron.

La logica de deteccion y almacenamiento esta en ``evidence_guard_lib.py``
para que otros modulos puedan importarla sin ejecutar el hook.

Politica fail-open: nunca bloquea el flujo de trabajo.
"""

import json
import os
import sys

# Anadir el directorio de hooks al path para importar la libreria
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from evidence_guard_lib import (
    is_test_command,
    detect_test_result,
    record_evidence,
)

_LOG_PREFIX = "[evidence-guard]"


def main():
    """Punto de entrada del hook PostToolUse para Bash.

    Lee el JSON de stdin, detecta si el comando ejecutado es un runner
    de tests, analiza su resultado y lo registra como evidencia.

    Politica fail-open: cualquier error inesperado se reporta en stderr
    pero el hook siempre termina con exit 0 para no bloquear el flujo.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(
            f"{_LOG_PREFIX} Aviso: no se pudo leer la entrada: {e}",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        tool_input = data.get("tool_input", {})
        tool_output = data.get("tool_output", {})

        command = tool_input.get("command", "")
        if not command or not is_test_command(command):
            sys.exit(0)

        # Extraer la salida del comando
        stdout = tool_output.get("stdout", "")
        stderr = tool_output.get("stderr", "")
        output = f"{stdout}\n{stderr}"

        # Detectar resultado y registrar evidencia
        result = detect_test_result(output)
        record_evidence(command, result)

        if result == "unknown":
            print(
                f"{_LOG_PREFIX} Tests ejecutados pero no se pudo determinar "
                f"el resultado. El comando se ha registrado igualmente.",
                file=sys.stderr,
            )
    except Exception as e:
        print(
            f"{_LOG_PREFIX} Error inesperado (fail-open, no bloquea): {e}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
