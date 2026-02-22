#!/usr/bin/env python3
"""
Hook de Stop para el plugin Alfred Dev (patrón ralph-loop).

Se ejecuta cuando Claude intenta detener la ejecución. Comprueba si hay
una sesión de trabajo activa con gates pendientes. Si la hay, emite una
decisión de bloqueo con un prompt que le indica a Claude la fase actual,
los agentes asignados, el objetivo y la gate requerida para poder avanzar.

Si no hay sesión activa o la sesión está completada, deja que Claude pare
normalmente (exit 0 sin salida).
"""

import json
import os
import signal
import sys

# --- Configuración de rutas ---

# Se añade el directorio raíz del plugin al path para poder importar core
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_ROOT)

from core.orchestrator import FLOWS, load_state


def main():
    """Punto de entrada del hook de Stop.

    Lee el estado de sesión actual y decide si bloquear la parada de Claude
    o dejarle continuar. El bloqueo solo se produce cuando hay una sesión
    activa con una gate pendiente, lo que significa que el flujo de trabajo
    no ha terminado y Claude debería seguir trabajando en la fase actual.
    """
    # El directorio de trabajo es el proyecto del usuario
    project_dir = os.getcwd()

    # Limpiar servidor GUI si esta corriendo
    gui_pid_file = os.path.join(project_dir, ".claude", "alfred-gui.pid")
    if os.path.isfile(gui_pid_file):
        killed = False
        try:
            with open(gui_pid_file, "r") as f:
                gui_pid = int(f.read().strip())
            os.kill(gui_pid, signal.SIGTERM)
            killed = True
        except ProcessLookupError:
            # El proceso ya no existe, seguro borrar el PID
            killed = True
        except (OSError, ValueError) as exc:
            print(
                f"[Alfred Dev] No se pudo detener el servidor GUI: {exc}",
                file=sys.stderr,
            )
        finally:
            if killed:
                try:
                    os.remove(gui_pid_file)
                except OSError:
                    pass

    state_path = os.path.join(project_dir, ".claude", "alfred-dev-state.json")

    # Intentar cargar el estado de sesión
    session = load_state(state_path)

    # Si no hay sesión o no se pudo leer, dejar que Claude pare
    if session is None:
        sys.exit(0)

    # Si la sesión está completada, no hay motivo para bloquear
    fase_actual = session.get("fase_actual", "completado")
    if fase_actual == "completado":
        sys.exit(0)

    comando = session.get("comando", "")

    # Verificar que el flujo existe en la definición
    if comando not in FLOWS:
        print(
            f"[Alfred Dev] Aviso: la sesión referencia el flujo '{comando}' "
            f"que no está definido. El fichero de estado puede estar corrupto.",
            file=sys.stderr,
        )
        sys.exit(0)

    flow = FLOWS[comando]
    fase_numero = session.get("fase_numero", 0)
    fases = flow.get("fases", [])

    # Validación defensiva: fase_numero debe ser entero para las
    # comparaciones con len(fases). Si no lo es, el estado es incoherente.
    if not isinstance(fase_numero, int):
        print(
            "[Alfred Dev] Aviso: 'fase_numero' no es un entero "
            "en el estado de sesión. Estado incoherente.",
            file=sys.stderr,
        )
        sys.exit(0)

    # Si el número de fase excede las fases disponibles, la sesión está incoherente
    if fase_numero >= len(fases):
        print(
            f"[Alfred Dev] Aviso: la fase {fase_numero} excede las fases "
            f"del flujo '{comando}'. Estado incoherente.",
            file=sys.stderr,
        )
        sys.exit(0)

    # Extraer información de la fase actual para construir el prompt de bloqueo
    fase = fases[fase_numero]
    nombre_fase = fase.get("nombre", f"fase_{fase_numero}")
    agentes = fase.get("agentes", [])
    gate_tipo = fase.get("gate_tipo", "libre")
    descripcion_fase = fase.get("descripcion", "")
    descripcion_sesion = session.get("descripcion", "Sin descripción")

    # Construir el mensaje de bloqueo que explica a Claude por qué no debe parar.
    # El tono es directo: hay trabajo pendiente y una gate que superar.
    agentes_str = ", ".join(agentes) if agentes else "sin agentes asignados"

    reason_parts = [
        f"Eh eh eh, para el carro. Aún no hemos terminado. Hay una sesión '{comando}' activa.",
        "",
        f"Fase actual: {nombre_fase}",
        f"Descripción: {descripcion_fase}",
        f"Agentes asignados: {agentes_str}",
        f"Objetivo de la sesión: {descripcion_sesion}",
        "",
        f"Gate pendiente: {gate_tipo}",
        "",
    ]

    # Instrucciones específicas según el tipo de gate
    if "automatico" in gate_tipo:
        reason_parts.append(
            "Necesitas que los tests pasen (gate automática). "
            "Ejecuta los tests y verifica que están en verde antes de avanzar."
        )
    if "seguridad" in gate_tipo:
        reason_parts.append(
            "Necesitas pasar la auditoría de seguridad. "
            "Revisa las vulnerabilidades pendientes."
        )
    if "usuario" in gate_tipo:
        reason_parts.append(
            "Necesitas la aprobación del usuario para avanzar. "
            "Presenta los resultados y pide confirmación."
        )
    if gate_tipo == "libre":
        reason_parts.append(
            "La gate es libre, pero aún queda trabajo por hacer en esta fase. "
            "Completa la tarea antes de parar."
        )

    reason = "\n".join(reason_parts)

    # Emitir la decisión de bloqueo como JSON en stdout
    output = {
        "decision": "block",
        "reason": reason,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
