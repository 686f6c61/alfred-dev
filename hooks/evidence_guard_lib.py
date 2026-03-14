#!/usr/bin/env python3
"""
Libreria de verificacion de evidencia para Alfred Dev.

Contiene las funciones de deteccion y almacenamiento de evidencia de
tests separadas del punto de entrada del hook. Esto permite que otros
modulos (tests, stop-hook, orchestrator) importen las funciones sin
ejecutar el hook.

El hook ``evidence-guard.py`` importa desde aqui y solo añade el
punto de entrada ``main()`` con lectura de stdin.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# --- Constantes ---

# Fichero donde se registra la evidencia de tests.
_EVIDENCE_FILENAME = "alfred-evidence.json"

# Tiempo maximo (en segundos) para considerar una evidencia como reciente.
EVIDENCE_MAX_AGE_SECONDS = 600  # 10 minutos

# Patrones de runners de tests.
_CMD_POS = r"(?:^|[;&|])\s*"

TEST_RUNNERS = [
    rf"{_CMD_POS}pytest\b",
    r"\bpython3?\s+-m\s+pytest\b",
    rf"{_CMD_POS}vitest\b",
    rf"{_CMD_POS}jest\b",
    rf"{_CMD_POS}mocha\b",
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
    rf"{_CMD_POS}phpunit\b",
    rf"{_CMD_POS}rspec\b",
    r"\bmix\s+test\b",
    r"\bdotnet\s+test\b",
    r"\bmaven\s+test\b",
    r"\bmvn\s+test\b",
    r"\bgradle\s+test\b",
]

# Patrones de fallo en salida de tests.
# Se buscan en contexto de salida de runners, así que usamos patrones
# específicos para evitar falsos positivos con palabras como «fail-safe»
# o «OK» en texto genérico.
FAILURE_PATTERNS = [
    r"(?<!\d )\bFAIL[ED]*\b(?![-_])",  # FAIL, FAILED pero no fail-safe, fail_over ni "0 failed"
    r"[1-9]\d*\s+failures?\b",       # "1 failure", "3 failures" (excluye "0 failures")
    r"\bfailing\b",
    r"[Tt]ests?\s+failed",
    r"ERRORS?\s*[:=]",              # "ERRORS:" o "ERROR=" pero no "ERROR" suelto
    r"Assertion(?:Error|Failed)",    # AssertionError → typo corregido a ambas formas
    r"test\s+result:\s+FAILED",
    r"Build\s+FAILED",
    r"[1-9]\d*\s+failed",            # "1 failed", "3 failed" (excluye "0 failed")
    r"not\s+ok\s+\d+",              # TAP format: "not ok 1 - test name"
]

# Patrones de exito en salida de tests.
SUCCESS_PATTERNS = [
    r"\d+\s+passed",
    r"[Tt]ests?\s+passed",
    r"test\s+result:\s+ok\b",
    r"All\s+tests\s+passed",
    r"\d+\s+passing\b",
    r"\bPASS(?:ED)?\b",             # PASS o PASSED
    r"\d+\s+tests?\s+complete",
    r"[Tt]ests?\s+run:\s+\d+",      # "Tests run: N" — formato JUnit/Maven/TestNG
]


# --- Funciones de deteccion ---

def is_test_command(command: str) -> bool:
    """Determina si un comando corresponde a la ejecucion de tests.

    Args:
        command: comando Bash ejecutado (cadena completa).

    Returns:
        True si el comando coincide con un runner de tests.
    """
    return any(re.search(pattern, command) for pattern in TEST_RUNNERS)


def detect_test_result(output: str) -> str:
    """Analiza la salida de un comando de tests para determinar el resultado.

    Los patrones de fallo tienen prioridad sobre los de exito para
    cubrir el caso de tests parciales (3 passed, 1 failed).

    Args:
        output: salida completa del comando (stdout + stderr).

    Returns:
        ``"pass"``, ``"fail"`` o ``"unknown"``.
    """
    has_fail = any(
        re.search(pattern, output, re.IGNORECASE)
        for pattern in FAILURE_PATTERNS
    )
    has_pass = any(
        re.search(pattern, output, re.IGNORECASE)
        for pattern in SUCCESS_PATTERNS
    )

    if has_fail:
        return "fail"
    if has_pass:
        return "pass"
    return "unknown"


# --- Gestion del fichero de evidencia ---

def _evidence_path(project_dir: Optional[str] = None) -> str:
    """Calcula la ruta del fichero de evidencia."""
    base = project_dir or os.getcwd()
    return os.path.join(base, ".claude", _EVIDENCE_FILENAME)


def _load_evidence(project_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Carga el registro de evidencia existente."""
    path = _evidence_path(project_dir)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        print(
            f"[evidence-guard] Aviso: el fichero de evidencia no contiene "
            f"una lista. Se descarta el contenido.",
            file=sys.stderr,
        )
        return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(
            f"[evidence-guard] Aviso: fichero de evidencia corrupto "
            f"({path}): {e}. Se perdera la evidencia anterior.",
            file=sys.stderr,
        )
        return []
    except OSError as e:
        print(
            f"[evidence-guard] Aviso: no se pudo leer la evidencia "
            f"({path}): {e}.",
            file=sys.stderr,
        )
        return []


def _save_evidence(
    records: List[Dict[str, Any]],
    project_dir: Optional[str] = None,
) -> None:
    """Guarda el registro de evidencia. Trunca a 50 registros."""
    path = _evidence_path(project_dir)
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)

    trimmed = records[-50:]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(
            f"[evidence-guard] Error: no se pudo guardar la evidencia "
            f"en '{path}': {e}. Los resultados de tests de esta "
            f"ejecucion no quedaran registrados.",
            file=sys.stderr,
        )


def record_evidence(
    command: str,
    result: str,
    project_dir: Optional[str] = None,
) -> None:
    """Registra una ejecucion de tests como evidencia.

    Args:
        command: comando de tests ejecutado.
        result: resultado detectado (``"pass"``, ``"fail"``, ``"unknown"``).
        project_dir: directorio del proyecto.
    """
    records = _load_evidence(project_dir)
    records.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command[:200],
        "result": result,
    })
    _save_evidence(records, project_dir)


def get_evidence(
    max_age_seconds: int = EVIDENCE_MAX_AGE_SECONDS,
    project_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Consulta el estado actual de la evidencia de tests.

    Args:
        max_age_seconds: ventana temporal en segundos.
        project_dir: directorio del proyecto.

    Returns:
        Diccionario con ``has_evidence``, ``all_passing``, ``last_result``,
        ``count`` y ``records``.
    """
    records = _load_evidence(project_dir)
    now = datetime.now(timezone.utc)

    recent = []
    skipped = 0
    for record in records:
        try:
            ts_str = record.get("timestamp", "")
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age = (now - ts).total_seconds()
            if age <= max_age_seconds:
                recent.append(record)
        except (ValueError, TypeError):
            skipped += 1
            continue

    if skipped > 0:
        print(
            f"[evidence-guard] Aviso: se descartaron {skipped} registros "
            f"de evidencia con timestamp invalido.",
            file=sys.stderr,
        )

    if not recent:
        return {
            "has_evidence": False,
            "all_passing": False,
            "last_result": None,
            "count": 0,
            "records": [],
        }

    last = recent[-1]
    all_passing = all(r.get("result") == "pass" for r in recent)

    return {
        "has_evidence": True,
        "all_passing": all_passing,
        "last_result": last.get("result"),
        "count": len(recent),
        "records": recent,
    }


def clear_evidence(project_dir: Optional[str] = None) -> None:
    """Limpia el fichero de evidencia."""
    path = _evidence_path(project_dir)
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError as e:
        print(
            f"[evidence-guard] Aviso: no se pudo eliminar la evidencia "
            f"({path}): {e}.",
            file=sys.stderr,
        )
