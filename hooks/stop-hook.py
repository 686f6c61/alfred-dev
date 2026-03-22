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
import sqlite3
import sys
from datetime import datetime, timezone

# --- Configuracion de rutas ---

# Se anade el directorio raiz del plugin al path para poder importar core
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLUGIN_ROOT)
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from core.continuity import (
    HANDOFF_JSON_RELATIVE_PATH,
    clear_stop_hook_bypass,
    is_session_paused,
    load_stop_hook_bypass,
)
from core.orchestrator import FLOWS, load_state
from core.session_report import generate_report


READ_ONLY_OPERATIONAL_COMMANDS = frozenset({
    "/alfred-dev:progress",
    "/alfred-dev:status",
    "/alfred-dev:help",
})


def should_block(session, flow):
    """Decide si la sesion justifica bloquear la parada de Claude.

    Comprueba que la sesion no esta completada, que el numero de fase
    es coherente y que existe una fase pendiente en el flujo.

    Args:
        session: diccionario con el estado de la sesion.
        flow: definicion del flujo (de FLOWS) correspondiente al comando.

    Returns:
        True si se debe bloquear la parada, False en caso contrario.
    """
    fase_actual = session.get("fase_actual", "completado")
    if fase_actual == "completado":
        return False
    fase_numero = session.get("fase_numero", 0)
    fases = flow.get("fases", [])
    if not isinstance(fase_numero, int):
        return False
    if fase_numero >= len(fases):
        return False
    if is_session_paused(session):
        return False
    return True


def should_allow_transient_stop(project_dir):
    """Permite una parada puntual para comandos de continuidad one-shot."""
    bypass = load_stop_hook_bypass(project_dir)
    if not bypass:
        return False

    try:
        expires_at = datetime.fromisoformat(bypass["expires_at"])
    except (KeyError, TypeError, ValueError):
        clear_stop_hook_bypass(project_dir)
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        clear_stop_hook_bypass(project_dir)
        return False

    clear_stop_hook_bypass(project_dir)
    return True


def should_allow_read_only_operational_prompt(
    project_dir,
    max_age_seconds=180,
):
    """Permite salir si el último prompt reciente fue una vista operativa.

    Se apoya en la memoria persistente del proyecto. Si el último evento
    `user_prompt` empieza por un comando de solo lectura como
    `/alfred-dev:progress`, no tiene sentido que el stop-hook bloquee la
    salida solo por existir una sesión activa.
    """
    db_path = os.path.join(project_dir, ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        return False

    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT content, summary, created_at FROM events "
            "WHERE event_type = 'user_prompt' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
    except sqlite3.Error:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        return False

    try:
        created_at = datetime.fromisoformat(row[2])
    except (TypeError, ValueError):
        return False

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age_seconds < 0 or age_seconds > max_age_seconds:
        return False

    text = (row[0] or row[1] or "").strip()
    if not text:
        return False

    first_line = ""
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            first_line = candidate
            break

    if not first_line:
        return False

    return any(first_line.startswith(command) for command in READ_ONLY_OPERATIONAL_COMMANDS)


def build_block_message(session, fase, gate_tipo):
    """Construye el mensaje de bloqueo con instrucciones segun el tipo de gate.

    El mensaje incluye informacion sobre la fase actual, los agentes
    asignados, el objetivo de la sesion y las instrucciones especificas
    para superar la gate pendiente.

    Args:
        session: diccionario con el estado de la sesion.
        fase: diccionario con la definicion de la fase actual.
        gate_tipo: tipo de gate pendiente (automatico, seguridad, usuario, libre).

    Returns:
        Cadena con el mensaje de bloqueo formateado.
    """
    comando = session.get("comando", "")
    descripcion_fase = fase.get("descripcion", "")
    descripcion_sesion = session.get("descripcion", "Sin descripcion")
    agentes = fase.get("agentes", [])
    agentes_str = ", ".join(agentes) if agentes else "sin agentes asignados"
    nombre_fase = fase.get("nombre", "desconocida")
    is_autopilot = session.get("autopilot", False)

    reason_parts = [
        f"Eh eh eh, para el carro. Aun no hemos terminado. Hay una sesion '{comando}' activa.",
        "",
        f"Fase actual: {nombre_fase}",
        f"Descripcion: {descripcion_fase}",
        f"Agentes asignados: {agentes_str}",
        f"Objetivo de la sesion: {descripcion_sesion}",
        "",
        f"Gate pendiente: {gate_tipo}",
        "",
    ]

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
        if is_autopilot:
            reason_parts.append(
                "El flujo esta en autopilot. Investiga por que se ha detenido "
                "y resuelve el problema para continuar."
            )
        else:
            reason_parts.append(
                "Necesitas la aprobacion del usuario para avanzar. "
                "Presenta los resultados y pide confirmacion."
            )
    if gate_tipo == "libre":
        reason_parts.append(
            "La gate es libre, pero aun queda trabajo por hacer en esta fase. "
            "Completa la tarea antes de parar."
        )

    return "\n".join(reason_parts)


def handle_session_report(session, project_dir, completed=True):
    """Genera informe de sesion (completa o parcial).

    Intenta cargar la evidencia de tests y generar el informe. Si la
    sesion esta completada, limpia la evidencia despues de generar el
    informe. Los errores se imprimen en stderr sin bloquear el cierre.

    Args:
        session: diccionario con el estado de la sesion.
        project_dir: ruta al directorio del proyecto del usuario.
        completed: True si la sesion esta completada, False si es parcial.
    """
    try:
        evidence = None
        evidence_lib_available = False
        try:
            from evidence_guard_lib import get_evidence, clear_evidence
            evidence_lib_available = True
            evidence = get_evidence(
                max_age_seconds=None,
                project_dir=project_dir,
            )
        except ImportError:
            print(
                "[Alfred Dev] Aviso: no se pudo cargar evidence_guard_lib. "
                "El informe se generara sin evidencia de tests.",
                file=sys.stderr,
            )

        report_path = generate_report(
            session,
            evidence=evidence,
            project_dir=project_dir,
            completed=completed,
        )
        print(
            f"[Alfred Dev] Informe de sesion guardado en: {report_path}",
            file=sys.stderr,
        )

        if completed and evidence_lib_available:
            try:
                clear_evidence(project_dir=project_dir)
            except OSError as e:
                print(
                    f"[Alfred Dev] Aviso: no se pudo limpiar la evidencia: {e}",
                    file=sys.stderr,
                )
    except (OSError, ValueError, RuntimeError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo generar el informe de sesion: {e}",
            file=sys.stderr,
        )


def main():
    """Punto de entrada del hook de Stop.

    Lee el estado de sesion actual y decide si bloquear la parada de Claude
    o dejarle continuar. El bloqueo solo se produce cuando hay una sesion
    activa con una gate pendiente, lo que significa que el flujo de trabajo
    no ha terminado y Claude deberia seguir trabajando en la fase actual.
    """
    project_dir = os.getcwd()
    state_path = os.path.join(project_dir, ".claude", "alfred-dev-state.json")
    handoff_path = os.path.join(project_dir, HANDOFF_JSON_RELATIVE_PATH)

    session = load_state(state_path)
    if session is None:
        sys.exit(0)

    fase_actual = session.get("fase_actual", "completado")

    if fase_actual == "completado":
        handle_session_report(session, project_dir, completed=True)
        sys.exit(0)

    comando = session.get("comando", "")
    if comando not in FLOWS:
        print(
            f"[Alfred Dev] Aviso: la sesion referencia el flujo '{comando}' "
            f"que no esta definido.",
            file=sys.stderr,
        )
        sys.exit(0)

    flow = FLOWS[comando]

    # Generar informe parcial
    handle_session_report(session, project_dir, completed=False)

    if is_session_paused(session):
        if os.path.isfile(handoff_path):
            sys.exit(0)
        print(
            "[Alfred Dev] Aviso: la sesión está marcada como pausada, pero falta "
            "el handoff. Se mantiene el bloqueo para no perder contexto.",
            file=sys.stderr,
        )

    if should_allow_transient_stop(project_dir):
        sys.exit(0)

    if should_allow_read_only_operational_prompt(project_dir):
        sys.exit(0)

    if not should_block(session, flow):
        sys.exit(0)

    fase_numero = session.get("fase_numero", 0)
    fase = flow["fases"][fase_numero]
    gate_tipo = fase.get("gate_tipo", "libre")

    reason = build_block_message(session, fase, gate_tipo)

    output = {
        "decision": "block",
        "reason": reason,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
