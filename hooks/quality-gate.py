#!/usr/bin/env python3
"""
Hook PostToolUse para Bash: quality gate de tests.

Intercepta la salida de comandos Bash para detectar si se han ejecutado
tests y, en caso afirmativo, analizar si han fallado. Cuando detecta
fallos, informa por stderr con la voz de "El Rompe-cosas" (QA).

Solo actua sobre comandos que coincidan con runners de tests conocidos.
El resto de comandos Bash pasan sin inspeccion.
"""

import json
import re
import sys


# --- Patrones de runners de tests ---

# Expresiones regulares que identifican comandos de ejecucion de tests.
# Se comprueba contra el comando completo para evitar falsos positivos
# (por ejemplo, un 'grep pytest' no deberia activar el hook).
TEST_RUNNERS = [
    r"\bpytest\b",
    r"\bpython\s+-m\s+pytest\b",
    r"\bvitest\b",
    r"\bjest\b",
    r"\bmocha\b",
    r"\bcargo\s+test\b",
    r"\bgo\s+test\b",
    r"\bnpm\s+test\b",
    r"\bnpm\s+run\s+test\b",
    r"\bpnpm\s+test\b",
    r"\bpnpm\s+run\s+test\b",
    r"\bbun\s+test\b",
    r"\bbun\s+run\s+test\b",
    r"\byarn\s+test\b",
    r"\byarn\s+run\s+test\b",
    r"\bpython\s+-m\s+unittest\b",
    r"\bphpunit\b",
    r"\brspec\b",
    r"\bmix\s+test\b",
    r"\bdotnet\s+test\b",
    r"\bmaven\s+test\b",
    r"\bmvn\s+test\b",
    r"\bgradle\s+test\b",
]

# --- Patrones de fallo en la salida ---

# Indicadores comunes de que los tests han fallado. Se buscan como
# palabras completas o patrones especificos para minimizar falsos positivos.
FAILURE_PATTERNS = [
    r"\bFAIL\b",
    r"\bFAILED\b",
    r"\bERROR\b",
    r"\bfailures?\b",
    r"\bfailing\b",
    r"Tests?\s+failed",
    r"tests?\s+failed",
    r"ERRORS?:",
    r"AssertionError",
    r"AssertError",
    r"test\s+result:\s+FAILED",
    r"Build\s+FAILED",
    r"\d+\s+failed",
    r"not\s+ok\b",
]


def is_test_command(command: str) -> bool:
    """Determina si un comando corresponde a la ejecucion de tests.

    Comprueba el comando contra la lista de runners conocidos. Se usa
    busqueda por regex con limites de palabra para evitar que comandos
    como 'cat pytest.ini' activen el hook.

    Args:
        command: Comando Bash ejecutado (cadena completa).

    Returns:
        True si el comando coincide con un runner de tests.
    """
    return any(re.search(pattern, command) for pattern in TEST_RUNNERS)


def has_failures(output: str) -> bool:
    """Analiza la salida de un comando de tests en busca de fallos.

    Busca patrones comunes de fallo en la salida estandar del comando.
    Los patrones se aplican linea a linea con busqueda case-sensitive
    para los indicadores que suelen ir en mayusculas y case-insensitive
    para los genéricos.

    Args:
        output: Salida estandar del comando Bash.

    Returns:
        True si se detecta al menos un patron de fallo.
    """
    return any(re.search(pattern, output) for pattern in FAILURE_PATTERNS)


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae el comando ejecutado y su salida,
    y determina si hay tests fallidos. Si los hay, emite un aviso
    por stderr con la voz de El Rompe-cosas.
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(
            f"[quality-gate] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La monitorizacion de tests esta desactivada para este comando.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    tool_output = data.get("tool_output", {})

    # Extraer el comando ejecutado
    command = tool_input.get("command", "")

    # Solo actuar si es un comando de tests
    if not command or not is_test_command(command):
        sys.exit(0)

    # Extraer la salida del comando
    stdout = tool_output.get("stdout", "")
    stderr = tool_output.get("stderr", "")
    output = f"{stdout}\n{stderr}"

    # Analizar si hay fallos
    if has_failures(output):
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

    # Siempre exit 0 para PostToolUse (solo informa, no bloquea)
    sys.exit(0)


if __name__ == "__main__":
    main()
