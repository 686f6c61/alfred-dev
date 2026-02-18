#!/usr/bin/env python3
"""
Hook de Stop para el plugin Alfred Dev (patron ralph-loop).

Se ejecuta cuando Claude intenta detener la ejecucion. Comprueba si hay
una sesion de trabajo activa con gates pendientes. Si la hay, emite una
decision de bloqueo con un prompt que le indica a Claude la fase actual,
los agentes asignados, el objetivo y la gate requerida para poder avanzar.

Si no hay sesion activa o la sesion esta completada, deja que Claude pare
normalmente (exit 0 sin salida).
"""

import json
import os
import sys

# --- Configuracion de rutas ---

# Se anade el directorio raiz del plugin al path para poder importar core
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_ROOT)

from core.orchestrator import FLOWS, load_state


def main():
    """Punto de entrada del hook de Stop.

    Lee el estado de sesion actual y decide si bloquear la parada de Claude
    o dejarle continuar. El bloqueo solo se produce cuando hay una sesion
    activa con una gate pendiente, lo que significa que el flujo de trabajo
    no ha terminado y Claude deberia seguir trabajando en la fase actual.
    """
    # El directorio de trabajo es el proyecto del usuario
    project_dir = os.getcwd()
    state_path = os.path.join(project_dir, ".claude", "alfred-dev-state.json")

    # Intentar cargar el estado de sesion
    session = load_state(state_path)

    # Si no hay sesion o no se pudo leer, dejar que Claude pare
    if session is None:
        sys.exit(0)

    # Si la sesion esta completada, no hay motivo para bloquear
    fase_actual = session.get("fase_actual", "completado")
    if fase_actual == "completado":
        sys.exit(0)

    comando = session.get("comando", "")

    # Verificar que el flujo existe en la definicion
    if comando not in FLOWS:
        print(
            f"[Alfred Dev] Aviso: la sesion referencia el flujo '{comando}' "
            f"que no esta definido. El fichero de estado puede estar corrupto.",
            file=sys.stderr,
        )
        sys.exit(0)

    flow = FLOWS[comando]
    fase_numero = session.get("fase_numero", 0)
    fases = flow.get("fases", [])

    # Si el numero de fase excede las fases disponibles, la sesion esta incoherente
    if fase_numero >= len(fases):
        print(
            f"[Alfred Dev] Aviso: la fase {fase_numero} excede las fases "
            f"del flujo '{comando}'. Estado incoherente.",
            file=sys.stderr,
        )
        sys.exit(0)

    # Extraer informacion de la fase actual para construir el prompt de bloqueo
    fase = fases[fase_numero]
    nombre_fase = fase["nombre"]
    agentes = fase.get("agentes", [])
    gate_tipo = fase.get("gate_tipo", "libre")
    descripcion_fase = fase.get("descripcion", "")
    descripcion_sesion = session.get("descripcion", "Sin descripcion")

    # Construir el mensaje de bloqueo que explica a Claude por que no debe parar.
    # El tono es directo: hay trabajo pendiente y una gate que superar.
    agentes_str = ", ".join(agentes) if agentes else "sin agentes asignados"

    reason_parts = [
        f"Disculpe, senor, pero aun no hemos terminado. Hay una sesion '{comando}' activa.",
        "",
        f"Fase actual: {nombre_fase}",
        f"Descripcion: {descripcion_fase}",
        f"Agentes asignados: {agentes_str}",
        f"Objetivo de la sesion: {descripcion_sesion}",
        "",
        f"Gate pendiente: {gate_tipo}",
        "",
    ]

    # Instrucciones especificas segun el tipo de gate
    if "automatico" in gate_tipo:
        reason_parts.append(
            "Necesitas que los tests pasen (gate automatica). "
            "Ejecuta los tests y verifica que estan en verde antes de avanzar."
        )
    if "seguridad" in gate_tipo:
        reason_parts.append(
            "Necesitas pasar la auditoria de seguridad. "
            "Revisa las vulnerabilidades pendientes."
        )
    if "usuario" in gate_tipo:
        reason_parts.append(
            "Necesitas la aprobacion del usuario para avanzar. "
            "Presenta los resultados y pide confirmacion."
        )
    if gate_tipo == "libre":
        reason_parts.append(
            "La gate es libre, pero aun queda trabajo por hacer en esta fase. "
            "Completa la tarea antes de parar."
        )

    reason = "\n".join(reason_parts)

    # Emitir la decision de bloqueo como JSON en stdout
    output = {
        "decision": "block",
        "reason": reason,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
