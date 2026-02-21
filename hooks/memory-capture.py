#!/usr/bin/env python3
"""
Hook PostToolUse para Write/Edit: captura automatica de eventos en la memoria.

Intercepta las operaciones de escritura sobre el fichero de estado de sesion
(alfred-dev-state.json) y registra automaticamente eventos en la base de datos
de memoria persistente del proyecto. Esto permite mantener un historial
completo de iteraciones y fases sin que el usuario ni los agentes tengan que
hacerlo manualmente.

El hook actua como un observador pasivo: nunca bloquea la operacion ni
interfiere con el flujo de trabajo. Si algo falla (DB inexistente, JSON
corrupto, configuracion ausente, etc.), sale silenciosamente con exit 0.

Eventos capturados:
    - iteration_started: cuando se inicia una sesion sin iteracion activa.
    - phase_completed: cuando se completan fases nuevas respecto al estado
      almacenado en la base de datos.
    - iteration_completed: cuando la fase actual pasa a "completado".
"""

import json
import os
import re
import sys


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin proporcionado por el hook PostToolUse, determina si
    la escritura afecta al fichero de estado de Alfred Dev y, en caso
    afirmativo, compara el estado nuevo con lo almacenado en la memoria
    para registrar los eventos correspondientes.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(
            f"[memory-capture] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La captura de memoria está desactivada para esta operación.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})

    # Extraer la ruta del fichero segun la herramienta usada (Write o Edit)
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    # Solo actuar si el fichero es el estado de sesion de Alfred Dev
    if not file_path.endswith("alfred-dev-state.json"):
        sys.exit(0)

    # Comprobar si la memoria esta habilitada en la configuracion local
    if not _is_memory_enabled():
        sys.exit(0)

    # Leer el estado nuevo que se acaba de escribir
    new_state = _load_state_file(file_path)
    if new_state is None:
        sys.exit(0)

    # Importar MemoryDB desde core.memory (necesita el plugin root en el path)
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, plugin_root)

    try:
        from core.memory import MemoryDB
    except ImportError as e:
        print(
            f"[memory-capture] Aviso: no se pudo importar core.memory: {e}",
            file=sys.stderr,
        )
        sys.exit(0)

    # Resolver la ruta de la base de datos de memoria del proyecto
    project_dir = os.getcwd()
    db_path = os.path.join(project_dir, ".claude", "alfred-memory.db")

    # Si la DB no existe, solo tiene sentido crearla si se inicia una iteracion
    # Para el resto de eventos, sin DB previa no hay nada que comparar
    db_exists = os.path.isfile(db_path)

    try:
        db = MemoryDB(db_path)
    except Exception as e:
        print(
            f"[memory-capture] Aviso: no se pudo abrir la DB de memoria: {e}",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        _process_state(db, new_state, db_exists)
    except Exception as e:
        print(
            f"[memory-capture] Aviso: error al procesar estado: {e}",
            file=sys.stderr,
        )
    finally:
        db.close()

    sys.exit(0)


def _is_memory_enabled() -> bool:
    """Comprueba si la memoria persistente esta habilitada en la configuracion.

    Busca el fichero ``alfred-dev.local.md`` en el directorio ``.claude``
    del proyecto actual y verifica que contenga la seccion ``memoria:`` con
    ``enabled: true``. La comprobacion se hace con una expresion regular
    para no depender de un parser YAML completo.

    Returns:
        True si la memoria esta habilitada, False en caso contrario o si
        no se puede leer la configuracion.
    """
    project_dir = os.getcwd()
    config_path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, FileNotFoundError):
        return False

    # Buscar el patron "memoria:" seguido de "enabled: true" en las lineas
    # siguientes. Se usa re.DOTALL para cubrir saltos de linea intermedios.
    # El patron permite espacios y comentarios entre las dos claves, pero
    # exige que ambas esten presentes y en el orden correcto.
    pattern = r"memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true"
    return bool(re.search(pattern, content))


def _load_state_file(file_path: str) -> dict | None:
    """Lee y parsea el fichero de estado de sesion.

    Args:
        file_path: ruta absoluta al fichero alfred-dev-state.json.

    Returns:
        Diccionario con el estado, o None si no se puede leer o parsear.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        return None

    # Validacion minima de estructura
    if not isinstance(state, dict):
        return None
    if "comando" not in state or "fase_actual" not in state:
        return None

    return state


def _process_state(db, new_state: dict, db_existed: bool) -> None:
    """Compara el estado nuevo con la memoria y registra eventos.

    La logica de comparacion sigue tres ejes:

    1. Si no hay iteracion activa en la DB, se inicia una nueva (esto cubre
       tanto la primera vez como sesiones posteriores donde la anterior ya
       se completo).

    2. Si hay fases completadas en el estado nuevo que no estan registradas
       como eventos en la DB, se registra un evento ``phase_completed`` por
       cada una.

    3. Si la fase actual es "completado", se cierra la iteracion activa.

    Args:
        db: instancia de MemoryDB ya abierta.
        new_state: diccionario con el estado recien escrito.
        db_existed: indica si la DB ya existia antes de esta ejecucion.
    """
    comando = new_state.get("comando", "desconocido")
    descripcion = new_state.get("descripcion", "")
    fase_actual = new_state.get("fase_actual", "")
    fases_completadas = new_state.get("fases_completadas", [])

    # --- Comprobar si hay una iteracion activa ---
    active = db.get_active_iteration()

    if active is None:
        # No hay iteracion activa: iniciar una nueva
        iteration_id = db.start_iteration(
            command=comando,
            description=descripcion,
        )
        db.log_event(
            event_type="iteration_started",
            payload={"comando": comando, "descripcion": descripcion},
            iteration_id=iteration_id,
        )
        # Refrescar la iteracion activa para las comparaciones siguientes
        active = db.get_active_iteration()

    if active is None:
        # Si despues de intentar crear sigue sin haber iteracion, abortar
        return

    iteration_id = active["id"]

    # --- Detectar fases nuevas completadas ---
    # Las fases ya registradas se obtienen de los eventos de tipo
    # "phase_completed" para esta iteracion. Se comparan por nombre de fase.
    existing_events = db.get_timeline(iteration_id)
    existing_phases = set()
    for event in existing_events:
        if event.get("event_type") == "phase_completed":
            # El nombre de la fase se guarda en el payload del evento
            payload_raw = event.get("payload")
            if payload_raw:
                try:
                    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                    phase_name = payload.get("fase", "")
                    if phase_name:
                        existing_phases.add(phase_name)
                except (json.JSONDecodeError, AttributeError):
                    pass

    # Registrar cada fase completada que aun no tenga evento
    for fase in fases_completadas:
        nombre_fase = fase.get("nombre", "") if isinstance(fase, dict) else str(fase)
        if not nombre_fase:
            continue
        if nombre_fase in existing_phases:
            continue

        # Construir el payload del evento con los datos disponibles
        payload = {"fase": nombre_fase}
        if isinstance(fase, dict):
            if "resultado" in fase:
                payload["resultado"] = fase["resultado"]
            if "completada_en" in fase:
                payload["completada_en"] = fase["completada_en"]
            if "artefactos" in fase:
                payload["artefactos"] = fase["artefactos"]

        db.log_event(
            event_type="phase_completed",
            phase=nombre_fase,
            payload=payload,
            iteration_id=iteration_id,
        )

    # --- Detectar iteracion completada ---
    if fase_actual == "completado":
        db.complete_iteration(iteration_id)
        db.log_event(
            event_type="iteration_completed",
            payload={
                "comando": comando,
                "total_fases": len(fases_completadas),
            },
            iteration_id=iteration_id,
        )


if __name__ == "__main__":
    main()
