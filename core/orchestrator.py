#!/usr/bin/env python3
"""
Orquestador de flujos del plugin Alfred Dev.

Este modulo gestiona el ciclo de vida completo de los flujos de trabajo
(feature, fix, spike, ship, audit). Cada flujo se compone de fases
secuenciales con gates de control que determinan si se puede avanzar
a la siguiente fase.

El orquestador se encarga de:
- Definir los flujos disponibles y sus fases.
- Crear y gestionar sesiones de trabajo.
- Evaluar las gates de cada fase para decidir si se aprueba el avance.
- Persistir y recuperar el estado de las sesiones en disco.

Arquitectura de gates:
    Las gates actuan como puntos de control entre fases. Hay dos tipos
    principales: las HARD_GATES (obligatorias e infranqueables) y las
    gates normales que dependen del resultado reportado. Las gates de
    tipo «usuario» requieren aprobacion explicita; las «automatico» se
    evaluan contra metricas objetivas como tests verdes o pipeline OK.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# --- Definicion de flujos ---------------------------------------------------
# Cada flujo describe una secuencia de fases que el orquestador recorre.
# Los agentes listados en cada fase son los responsables de ejecutarla.

FLOWS: Dict[str, Dict[str, Any]] = {
    "feature": {
        "nombre": "feature",
        "fases": [
            {
                "nombre": "producto",
                "agentes": ["product-owner"],
                "paralelo": False,
                "gate": "gate_producto",
                "gate_tipo": "usuario",
                "descripcion": (
                    "Analisis de requisitos y definicion del alcance "
                    "funcional de la nueva caracteristica."
                ),
            },
            {
                "nombre": "arquitectura",
                "agentes": ["architect", "security-officer"],
                "paralelo": True,
                "gate": "gate_arquitectura",
                "gate_tipo": "usuario",
                "descripcion": (
                    "Diseno tecnico, eleccion de patrones y validacion "
                    "de la propuesta arquitectonica con threat model."
                ),
            },
            {
                "nombre": "desarrollo",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_desarrollo",
                "gate_tipo": "automatico",
                "descripcion": (
                    "Implementacion del codigo siguiendo TDD estricto "
                    "con ciclos rojo-verde-refactor."
                ),
            },
            {
                "nombre": "calidad",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_calidad",
                "gate_tipo": "automatico+seguridad",
                "descripcion": (
                    "Revision de calidad, ejecucion de tests y "
                    "auditoria de seguridad en paralelo."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion",
                "gate_tipo": "libre",
                "descripcion": (
                    "Generacion de documentacion tecnica y de usuario "
                    "para la comunidad."
                ),
            },
            {
                "nombre": "entrega",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_entrega",
                "gate_tipo": "usuario+seguridad",
                "descripcion": (
                    "Preparacion del entregable, changelog y "
                    "validacion final antes del merge."
                ),
            },
        ],
    },
    "fix": {
        "nombre": "fix",
        "fases": [
            {
                "nombre": "diagnostico",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_diagnostico",
                "gate_tipo": "usuario",
                "descripcion": (
                    "Identificacion de la causa raiz del bug "
                    "mediante analisis de logs, trazas y reproduccion."
                ),
            },
            {
                "nombre": "correccion",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_correccion",
                "gate_tipo": "automatico",
                "descripcion": (
                    "Aplicacion del fix con test de regresion "
                    "que demuestre que el bug queda resuelto."
                ),
            },
            {
                "nombre": "validacion",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion",
                "gate_tipo": "automatico+seguridad",
                "descripcion": (
                    "Validacion completa: tests de regresion, "
                    "suite existente y revision de seguridad."
                ),
            },
        ],
    },
    "spike": {
        "nombre": "spike",
        "fases": [
            {
                "nombre": "exploracion",
                "agentes": ["architect", "senior-dev"],
                "paralelo": True,
                "gate": "gate_exploracion",
                "gate_tipo": "libre",
                "descripcion": (
                    "Investigacion exploratoria: pruebas de concepto, "
                    "benchmarks y evaluacion de alternativas."
                ),
            },
            {
                "nombre": "conclusiones",
                "agentes": ["architect"],
                "paralelo": False,
                "gate": "gate_conclusiones",
                "gate_tipo": "usuario",
                "descripcion": (
                    "Consolidacion de hallazgos en un informe "
                    "con recomendaciones accionables."
                ),
            },
        ],
    },
    "ship": {
        "nombre": "ship",
        "fases": [
            {
                "nombre": "auditoria_final",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_auditoria_final",
                "gate_tipo": "automatico+seguridad",
                "descripcion": (
                    "Auditoria completa de calidad y seguridad "
                    "antes de la release."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion_ship",
                "gate_tipo": "libre",
                "descripcion": (
                    "Actualizacion de la documentacion de release, "
                    "changelog y guias de migracion."
                ),
            },
            {
                "nombre": "empaquetado",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_empaquetado",
                "gate_tipo": "automatico",
                "descripcion": (
                    "Generacion del artefacto de release, "
                    "versionado semantico y etiquetado."
                ),
            },
            {
                "nombre": "despliegue",
                "agentes": ["devops-engineer"],
                "paralelo": False,
                "gate": "gate_despliegue",
                "gate_tipo": "usuario+seguridad",
                "descripcion": (
                    "Despliegue a produccion con validacion "
                    "post-deploy y rollback preparado."
                ),
            },
        ],
    },
    "audit": {
        "nombre": "audit",
        "fases": [
            {
                "nombre": "auditoria_paralela",
                "agentes": [
                    "qa-engineer",
                    "security-officer",
                    "architect",
                    "tech-writer",
                ],
                "paralelo": True,
                "gate": "gate_auditoria",
                "gate_tipo": "automatico+seguridad",
                "descripcion": (
                    "Auditoria completa del codigo en paralelo: "
                    "calidad, seguridad, arquitectura "
                    "y documentacion."
                ),
            },
        ],
    },
}

# Gates infranqueables: si alguna de estas condiciones no se cumple,
# el avance se bloquea independientemente de cualquier otro criterio.
HARD_GATES = {"tests_verdes", "qa_seguridad_aprobado", "pipeline_verde"}


def create_session(command: str, description: str) -> Dict[str, Any]:
    """
    Crea una nueva sesion de trabajo para el flujo indicado.

    La sesion contiene todo el estado necesario para que el orquestador
    sepa en que punto del flujo se encuentra el usuario y que fases
    se han completado.

    Args:
        command: Identificador del flujo (feature, fix, spike, ship, audit).
        description: Descripcion en lenguaje natural de la tarea.

    Returns:
        Diccionario con el estado inicial de la sesion.

    Raises:
        ValueError: Si el comando no corresponde a ningun flujo definido.
    """
    if command not in FLOWS:
        raise ValueError(
            f"Flujo '{command}' no reconocido. "
            f"Flujos disponibles: {', '.join(FLOWS.keys())}"
        )

    flow = FLOWS[command]
    primera_fase = flow["fases"][0]["nombre"]

    return {
        "comando": command,
        "descripcion": description,
        "fase_actual": primera_fase,
        "fase_numero": 0,
        "fases_completadas": [],
        "artefactos": [],
        "creado_en": datetime.now(timezone.utc).isoformat(),
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }


def check_gate(
    session: Dict[str, Any],
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Evalua la gate de la fase actual para decidir si se puede avanzar.

    La logica de evaluacion depende del tipo de gate definido en la fase:
    - «usuario»: requiere resultado «aprobado».
    - «automatico»: requiere resultado «aprobado» y tests verdes.
    - «usuario+seguridad»: requiere aprobacion del usuario y seguridad OK.
    - «automatico+seguridad»: requiere tests, seguridad y resultado OK.
    - «libre»: se aprueba siempre que el resultado sea «aprobado».

    Args:
        session: Estado actual de la sesion.
        resultado: Resultado reportado (normalmente «aprobado» o «rechazado»).
        security_ok: Indica si la auditoria de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con las claves «passed» (bool) y «reason» (str).
    """
    flow = FLOWS[session["comando"]]
    fase_numero = session["fase_numero"]
    fase = flow["fases"][fase_numero]
    gate_tipo = fase["gate_tipo"]

    # Se acumulan las condiciones que debe cumplir la gate.
    # El orden de comprobacion determina que error se reporta primero.
    failures = []

    requires_tests = "automatico" in gate_tipo
    requires_security = "seguridad" in gate_tipo
    requires_approval = gate_tipo in ("usuario", "usuario+seguridad")
    is_known = gate_tipo in (
        "libre", "usuario", "automatico",
        "usuario+seguridad", "automatico+seguridad",
    )

    if not is_known:
        return {"passed": False, "reason": f"Tipo de gate desconocido: {gate_tipo}"}

    if requires_tests and not tests_ok:
        failures.append("Los tests no pasan.")
    if requires_security and not security_ok:
        failures.append("La auditoria de seguridad no es favorable.")
    if resultado != "aprobado":
        if requires_approval:
            failures.append("Aprobacion del usuario requerida.")
        else:
            failures.append("El resultado no es favorable.")

    passed = len(failures) == 0
    reason = failures[0] if failures else ""

    return {"passed": passed, "reason": reason}


def advance_phase(
    session: Dict[str, Any],
    resultado: str = "aprobado",
    artefactos: Optional[List[str]] = None,
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Intenta avanzar la sesion a la siguiente fase del flujo.

    Primero evalua la gate de la fase actual. Si la gate se supera,
    registra la fase como completada y actualiza el puntero a la
    siguiente. Si ya no quedan fases, marca la sesion como «completado».

    Args:
        session: Estado actual de la sesion.
        resultado: Resultado a evaluar en la gate (por defecto «aprobado»).
        artefactos: Lista opcional de artefactos generados en la fase.
        security_ok: Indica si la auditoria de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con el estado actualizado de la sesion.

    Raises:
        RuntimeError: Si la gate de la fase actual no se supera.
    """
    if artefactos is None:
        artefactos = []

    flow = FLOWS[session["comando"]]
    fases = flow["fases"]

    # Si ya esta completado, devolver sin cambios
    if session["fase_actual"] == "completado":
        return session

    # Evaluar la gate de la fase actual propagando todos los parametros
    gate_result = check_gate(
        session, resultado=resultado, security_ok=security_ok, tests_ok=tests_ok
    )
    if not gate_result["passed"]:
        raise RuntimeError(
            f"No se puede avanzar: {gate_result['reason']}"
        )

    # Registrar la fase completada
    fase_completada = {
        "nombre": fases[session["fase_numero"]]["nombre"],
        "resultado": resultado,
        "artefactos": artefactos,
        "completada_en": datetime.now(timezone.utc).isoformat(),
    }
    session["fases_completadas"].append(fase_completada)

    # Incorporar artefactos al registro global de la sesion
    session["artefactos"].extend(artefactos)

    # Avanzar al siguiente indice
    siguiente = session["fase_numero"] + 1

    if siguiente < len(fases):
        session["fase_numero"] = siguiente
        session["fase_actual"] = fases[siguiente]["nombre"]
    else:
        # No quedan mas fases: el flujo esta completado
        session["fase_actual"] = "completado"
        session["fase_numero"] = siguiente

    session["actualizado_en"] = datetime.now(timezone.utc).isoformat()
    return session


def save_state(session: Dict[str, Any], state_path: str) -> None:
    """
    Persiste el estado de la sesion en un fichero JSON.

    Se utiliza escritura atomica (escritura + renombrado) para evitar
    corrupcion si el proceso se interrumpe a mitad de escritura. Si la
    operacion falla, se limpia el fichero temporal y se relanza el error
    como RuntimeError para que el llamante sepa que el estado no se guardo.

    Args:
        session: Estado de la sesion a guardar.
        state_path: Ruta absoluta del fichero de destino.

    Raises:
        RuntimeError: Si no se puede guardar el estado por cualquier razon.
    """
    tmp_path = state_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        # Renombrado atomico en sistemas POSIX
        os.replace(tmp_path, state_path)
    except (OSError, TypeError) as e:
        # Limpiar el fichero temporal si quedo huerfano
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise RuntimeError(
            f"No se pudo guardar el estado de sesion en '{state_path}': {e}"
        ) from e


# Claves minimas que debe tener un estado de sesion valido
_REQUIRED_STATE_KEYS = {"comando", "fase_actual", "fase_numero"}


def load_state(state_path: str) -> Optional[Dict[str, Any]]:
    """
    Carga el estado de una sesion desde un fichero JSON.

    Distingue entre tres situaciones:
    - Fichero ausente: devuelve None silenciosamente (caso normal).
    - Fichero corrupto o ilegible: devuelve None pero avisa en stderr.
    - Fichero con estructura invalida: devuelve None y avisa en stderr.

    Args:
        state_path: Ruta absoluta del fichero a leer.

    Returns:
        Diccionario con el estado de la sesion, o None si el fichero
        no existe, esta corrupto o tiene estructura invalida.
    """
    if not os.path.isfile(state_path):
        return None

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"[Alfred Dev] Error: el fichero de estado '{state_path}' esta corrupto: {e}",
            file=sys.stderr,
        )
        return None
    except OSError as e:
        print(
            f"[Alfred Dev] Error al leer el estado de sesion '{state_path}': {e}",
            file=sys.stderr,
        )
        return None

    # Validar estructura minima
    if not isinstance(data, dict) or not _REQUIRED_STATE_KEYS.issubset(data.keys()):
        print(
            f"[Alfred Dev] Aviso: el fichero de estado '{state_path}' tiene una "
            f"estructura inesperada (faltan claves obligatorias). Se ignorara.",
            file=sys.stderr,
        )
        return None

    return data
