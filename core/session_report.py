#!/usr/bin/env python3
"""
Generador de informes de sesion para Alfred Dev.

Al finalizar una sesion de trabajo (evento Stop), este modulo genera un
informe en formato markdown con el resumen de la actividad: estado del
flujo, fases completadas, artefactos generados, evidencia de tests y
proximo paso operativo.

El informe se guarda en ``docs/alfred-reports/`` y queda disponible
como registro historico para consultas futuras. Si la memoria
persistente esta activa, se registra tambien como evento en la DB.

Arquitectura:
    El informe se compone de secciones modulares. Cada seccion es una
    funcion que recibe los datos y devuelve un bloque de markdown. La
    funcion principal ``generate_report()`` las ensambla en orden.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.optional_agents import get_optional_integrations, order_optional_agent_names
from core.orchestrator import FLOWS


# --- Formato del informe ---

_REPORT_DIR = "docs/alfred-reports"

_REPORT_TEMPLATE = """# Informe de sesion: {comando}

**Fecha:** {fecha}
**Duracion estimada:** {duracion}
**Descripcion:** {descripcion}

---

{secciones}

---

*Generado automaticamente por Alfred Dev v{version}*
"""

_REPORT_TEMPLATE_INTERRUPTED = """# Sesion interrumpida: {comando}

**Fecha:** {fecha}
**Duracion estimada:** {duracion}
**Descripcion:** {descripcion}

---

{secciones}

---

*Generado automaticamente por Alfred Dev v{version}*
"""

_OPTIONAL_INTEGRATIONS = get_optional_integrations()


# --- Secciones del informe ---


def _single_line_text(value: Any, default: str = "") -> str:
    """Normaliza texto libre a una sola linea legible."""
    if value is None:
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or default


def _markdown_table_cell(value: Any, default: str = "-") -> str:
    """Escapa una celda de tabla Markdown para texto libre."""
    text = _single_line_text(value, default=default)
    return text.replace("|", r"\|")


def _markdown_inline_code(value: Any, default: str = "-") -> str:
    """Renderiza texto seguro para usarlo como codigo inline."""
    text = _single_line_text(value, default=default)
    text = text.replace("`", "'")
    return f"`{text}`"


def _truncate_text(value: Any, limit: int = 120, default: str = "") -> str:
    """Recorta texto libre manteniendo una sola linea."""
    text = _single_line_text(value, default=default)
    if len(text) <= limit:
        return text
    return text[: max(limit - 3, 0)].rstrip() + "..."


def _session_team_source_label(session: Dict[str, Any]) -> str:
    """Devuelve una etiqueta humana para la fuente del equipo runtime."""
    equipo = session.get("equipo_sesion")
    if not isinstance(equipo, dict):
        return ""

    source = _single_line_text(equipo.get("fuente", ""))
    if source == "config_persistida":
        return "configuración persistida"
    if source == "composicion_dinamica":
        return "composición dinámica"
    return ""


def _session_on_demand_optionals_for_flow(session: Dict[str, Any]) -> List[str]:
    """Devuelve opcionales activos que no participan en ninguna fase del flujo."""
    command = _single_line_text(session.get("comando", ""))
    flow = FLOWS.get(command, {})
    flow_phases = {
        _single_line_text(phase.get("nombre", ""))
        for phase in (flow.get("fases") or [])
        if _single_line_text(phase.get("nombre", ""))
    }

    equipo = session.get("equipo_sesion")
    if not isinstance(equipo, dict):
        return []
    opcionales = equipo.get("opcionales_activos", {})
    if not isinstance(opcionales, dict):
        return []

    activos = order_optional_agent_names(
        name for name, enabled in opcionales.items() if enabled
    )
    on_demand: List[str] = []
    for agent_name in activos:
        integrated_phases = {
            _single_line_text(phase_name)
            for phase_name in _OPTIONAL_INTEGRATIONS.get(agent_name, {}).get("fases", [])
            if _single_line_text(phase_name)
        }
        if not flow_phases.intersection(integrated_phases):
            on_demand.append(agent_name)
    return on_demand


def _last_completed_at(session: Dict[str, Any]) -> str:
    """Obtiene la referencia temporal del ultimo cierre de fase/sesion."""
    completed = session.get("fases_completadas") or []
    if completed and isinstance(completed[-1], dict):
        completed_at = _single_line_text(completed[-1].get("completada_en", ""))
        if completed_at:
            return completed_at

    for key in ("actualizado_en", "creado_en"):
        value = _single_line_text(session.get(key, ""))
        if value:
            return value

    return ""


def _load_matching_session_uat(
    project_dir: Optional[str], session: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Carga la UAT asociada exactamente a esta sesion completada."""
    if not project_dir or session.get("fase_actual") != "completado":
        return None

    try:
        from core.continuity import load_uat  # noqa: PLC0415
    except Exception:
        return None

    uat = load_uat(project_dir)
    if not isinstance(uat, dict):
        return None

    command = _single_line_text(session.get("comando", "desconocido"), default="desconocido")
    target_id = f"session:{command}:{_last_completed_at(session)}"
    if uat.get("target_id") == target_id:
        return uat
    return None


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    """Parsea fechas ISO de forma tolerante."""
    text = _single_line_text(value)
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _normalized_match_key(value: Any) -> str:
    """Normaliza texto para comparaciones blandas."""
    return _single_line_text(value).casefold()


def _open_memory_db(project_dir: Optional[str]):
    """Abre la DB de memoria si existe y es accesible."""
    if not project_dir:
        return None

    db_path = os.path.join(project_dir, ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        return None

    try:
        from core.memory import MemoryDB  # noqa: PLC0415
    except Exception:
        return None

    try:
        return MemoryDB(db_path)
    except Exception:
        return None


def _find_session_iteration(db: Any, session: Dict[str, Any], completed: bool) -> Optional[Dict[str, Any]]:
    """Encuentra la iteracion de memoria que mejor encaja con la sesion."""
    command_key = _normalized_match_key(session.get("comando", ""))
    description_key = _normalized_match_key(session.get("descripcion", ""))
    session_time = _parse_iso_datetime(
        _last_completed_at(session) if completed else session.get("actualizado_en") or session.get("creado_en")
    )
    desired_status = "completed" if completed and session.get("fase_actual") == "completado" else "active"

    best_match: Optional[Dict[str, Any]] = None
    best_score: Optional[Tuple[int, int, int, str, int]] = None

    for iteration in db.get_iterations(limit=100):
        if _normalized_match_key(iteration.get("command", "")) != command_key:
            continue

        iteration_description = _normalized_match_key(iteration.get("description", ""))
        if description_key:
            if iteration_description == description_key:
                description_score = 2
            elif description_key in iteration_description or iteration_description in description_key:
                description_score = 1
            else:
                continue
        else:
            description_score = 0

        status = _single_line_text(iteration.get("status", ""), default="desconocido")
        if status == desired_status:
            status_score = 3
        elif desired_status == "completed" and status == "abandoned":
            status_score = 2
        elif desired_status == "completed" and status == "active":
            status_score = 1
        else:
            status_score = 0

        iteration_time = _parse_iso_datetime(
            iteration.get("completed_at") or iteration.get("started_at")
        )
        if session_time and iteration_time:
            diff = abs(int((iteration_time - session_time).total_seconds()))
            if diff <= 300:
                time_score = 3
            elif diff <= 3600:
                time_score = 2
            else:
                time_score = 1
        elif iteration_time:
            time_score = 1
        else:
            time_score = 0

        candidate_score = (
            description_score,
            status_score,
            time_score,
            _single_line_text(iteration.get("completed_at") or iteration.get("started_at") or ""),
            int(iteration.get("id", 0) or 0),
        )
        if best_score is None or candidate_score > best_score:
            best_score = candidate_score
            best_match = iteration

    return best_match


def _session_decisions_snapshot(
    project_dir: Optional[str],
    session: Dict[str, Any],
    completed: bool,
    limit: int = 5,
) -> Dict[str, Any]:
    """Recupera decisiones vinculadas a la iteracion de esta sesion."""
    snapshot = {
        "available": False,
        "iteration_id": None,
        "total": 0,
        "items": [],
    }
    db = _open_memory_db(project_dir)
    if db is None:
        return snapshot

    try:
        iteration = _find_session_iteration(db, session, completed)
        if not iteration:
            return snapshot

        iteration_id = int(iteration["id"])
        total = sum(1 for _ in db.iter_decisions(iteration_id=iteration_id, batch_size=200))
        items = db.get_decisions(iteration_id=iteration_id, limit=limit, status="active")
        if not items and total:
            items = db.get_decisions(iteration_id=iteration_id, limit=limit)

        snapshot.update(
            {
                "available": True,
                "iteration_id": iteration_id,
                "total": total,
                "items": items,
            }
        )
        return snapshot
    finally:
        db.close()


def _test_summary(evidence: Optional[Dict[str, Any]]) -> str:
    """Resume la evidencia de tests en una linea legible."""
    if evidence is None:
        return "sin datos de evidencia"
    if not evidence.get("has_evidence", False):
        return "sin tests ejecutados"

    records = evidence.get("records", []) or []
    passed = sum(1 for record in records if record.get("result") == "pass")
    failed = sum(1 for record in records if record.get("result") == "fail")
    unknown = max(len(records) - passed - failed, 0)

    parts = [f"{len(records)} ronda(s)"]
    if passed:
        parts.append(f"{passed} OK")
    if failed:
        parts.append(f"{failed} con fallo")
    if unknown:
        parts.append(f"{unknown} indeterminada(s)")
    return ", ".join(parts)


def _verification_status(
    project_dir: Optional[str], session: Dict[str, Any], completed: bool
) -> Dict[str, str]:
    """Resume el estado de verify/UAT y el siguiente paso recomendado."""
    if not completed or session.get("fase_actual") != "completado":
        current_phase = _single_line_text(
            session.get("fase_actual", "desconocida"), default="desconocida"
        )
        return {
            "label": "no aplica todavía",
            "detail": f"El flujo sigue activo en la fase '{current_phase}'.",
            "next_command": "/alfred-dev:resume",
            "next_reason": "La sesión no está cerrada todavía; conviene retomarla donde se quedó.",
        }

    uat = _load_matching_session_uat(project_dir, session)
    if not uat:
        return {
            "label": "pendiente",
            "detail": "El flujo figura completado, pero todavía no hay verificación manual/UAT registrada.",
            "next_command": "/alfred-dev:verify",
            "next_reason": "Hace falta validar el resultado final antes de dar el flujo por cerrado de verdad.",
        }

    status = _single_line_text(uat.get("status", ""), default="desconocido")
    updated_at = _single_line_text(uat.get("updated_at", ""))
    notes = _single_line_text(uat.get("notes", ""))

    if status == "approved":
        detail = "UAT aprobada."
        if updated_at:
            detail = f"{detail} Registrada el {updated_at}."
        return {
            "label": "aprobada",
            "detail": detail,
            "next_command": "/alfred-dev:alfred",
            "next_reason": "La validación final ya está cerrada; toca continuar con el siguiente trabajo o preparar release.",
        }

    if status == "rejected":
        detail = "UAT rechazada."
        if notes:
            detail = f"{detail} {notes}"
        elif updated_at:
            detail = f"{detail} Registrada el {updated_at}."
        return {
            "label": "rechazada",
            "detail": detail,
            "next_command": "/alfred-dev:alfred",
            "next_reason": "Hay que corregir el cambio y volver a pasar la verificación manual.",
        }

    detail = "Verificación manual/UAT pendiente."
    if updated_at:
        detail = f"{detail} Última actualización: {updated_at}."
    return {
        "label": "pendiente",
        "detail": detail,
        "next_command": "/alfred-dev:verify",
        "next_reason": "La validación final sigue abierta y necesita cerrarse explícitamente.",
    }


def _report_next_step_payload(
    project_dir: Optional[str], session: Dict[str, Any], completed: bool
) -> Dict[str, str]:
    """Devuelve una guía estructurada del siguiente paso para el informe."""
    verification = _verification_status(project_dir, session, completed)
    next_command = _single_line_text(
        verification.get("next_command", "/alfred-dev:alfred"),
        default="/alfred-dev:alfred",
    )

    if next_command == "/alfred-dev:resume":
        return {
            "focus": "Retomar la sesión en curso",
            "source_label": "sesión activa",
            "source": "state",
            "command": next_command,
            "directive": "Reanuda la sesión donde se quedó y trabaja sobre la fase abierta antes de abrir otro flujo.",
            "reason": verification.get("next_reason", "La sesión no está cerrada todavía."),
        }

    if next_command == "/alfred-dev:verify":
        return {
            "focus": "Cerrar la verificación pendiente",
            "source_label": "verificación/UAT",
            "source": "verify",
            "command": next_command,
            "directive": "Registra o completa la verificación manual/UAT del entregable antes de seguir con otro trabajo.",
            "reason": verification.get("next_reason", "Hace falta validar el resultado final."),
        }

    return {
        "focus": "Continuar después del cierre del flujo",
        "source_label": "cierre de sesión",
        "source": "report",
        "command": next_command,
        "directive": "Usa Alfred para decidir el siguiente ciclo o cerrar la entrega apoyándote en el contexto ya sembrado.",
        "reason": verification.get(
            "next_reason",
            "El flujo ya quedó cerrado y toca decidir el siguiente movimiento.",
        ),
    }


def _section_summary(
    session: Dict[str, Any],
    evidence: Optional[Dict[str, Any]],
    decisions: Dict[str, Any],
    project_dir: Optional[str],
    completed: bool,
) -> str:
    """Genera un resumen ejecutivo corto y accionable."""
    phases = [
        phase for phase in (session.get("fases_completadas") or []) if isinstance(phase, dict)
    ]
    skipped = sum(1 for phase in phases if _single_line_text(phase.get("resultado", "")) == "saltada")
    retried = sum(1 for phase in phases if int(phase.get("iteraciones", 0) or 0) > 0)
    artifacts = [item for item in (session.get("artefactos") or []) if _single_line_text(item)]
    verification = _verification_status(project_dir, session, completed)

    if completed and session.get("fase_actual") == "completado":
        state_label = "flujo completado en estado"
    else:
        current_phase = _single_line_text(
            session.get("fase_actual", "desconocida"), default="desconocida"
        )
        state_label = f"sesión interrumpida en '{current_phase}'"

    lines = ["## Resumen ejecutivo\n"]
    lines.append(f"- Estado general: {state_label}.")
    lines.append(
        f"- Fases registradas: {len(phases)}"
        f" ({skipped} saltada(s), {retried} con reintentos)."
    )
    lines.append(f"- Artefactos globales: {len(artifacts)}.")
    lines.append(f"- Tests: {_test_summary(evidence)}.")
    if decisions.get("available"):
        lines.append(f"- Decisiones en memoria: {int(decisions.get('total', 0))} vinculada(s) a la sesión.")
    lines.append(f"- Verificación/UAT: {verification['label']}. {verification['detail']}")

    equipo = session.get("equipo_sesion") or {}
    opcionales = equipo.get("opcionales_activos", {}) if isinstance(equipo, dict) else {}
    activos = order_optional_agent_names(
        name for name, enabled in opcionales.items() if enabled
    )
    team_source = _session_team_source_label(session)
    on_demand = _session_on_demand_optionals_for_flow(session)
    if team_source:
        lines.append(f"- Origen del equipo runtime: {team_source}.")
    if activos:
        lines.append(f"- Equipo opcional activo: {', '.join(activos)}.")
    if on_demand:
        lines.append(f"- Opcionales solo bajo demanda en este flujo: {', '.join(on_demand)}.")

    return "\n".join(lines) + "\n"


def _section_decisions(decisions: Dict[str, Any]) -> str:
    """Renderiza las decisiones destacadas recuperadas de memoria."""
    if not decisions.get("available"):
        return ""

    items = decisions.get("items") or []
    lines = ["## Decisiones destacadas\n"]
    total = int(decisions.get("total", 0) or 0)

    if not items:
        lines.append("No se detectaron decisiones registradas en memoria para esta sesión.\n")
        return "\n".join(lines) + "\n"

    lines.append(
        f"Se recuperaron **{total} decisiones** vinculadas a la iteración de memoria.\n"
    )
    for item in items:
        title = _truncate_text(item.get("title", ""), limit=90, default="Decisión sin título")
        chosen = _truncate_text(item.get("chosen", ""), limit=120, default="sin elección registrada")
        phase = _single_line_text(item.get("phase", ""))
        status = _single_line_text(item.get("status", ""), default="active")
        rationale = _truncate_text(item.get("rationale", ""), limit=120)

        meta: List[str] = []
        if phase:
            meta.append(f"fase: {phase}")
        if status and status != "active":
            meta.append(f"estado: {status}")
        if rationale:
            meta.append(rationale)
        meta_suffix = f" ({'; '.join(meta)})" if meta else ""

        lines.append(f"- **{title}** -> {chosen}{meta_suffix}")

    return "\n".join(lines) + "\n"


def _section_next_step(
    session: Dict[str, Any], project_dir: Optional[str], completed: bool
) -> str:
    """Indica el siguiente paso operativo más razonable."""
    payload = _report_next_step_payload(project_dir, session, completed)
    return (
        "## Siguiente paso recomendado\n\n"
        f"- Foco: {payload['focus']}\n"
        f"- Fuente: {payload['source_label']} (`{payload['source']}`)\n"
        f"- Comando: `{payload['command']}`\n"
        f"- Qué hacer ahora: {payload['directive']}\n"
        f"- Motivo: {payload['reason']}\n"
    )

def _section_phases(session: Dict[str, Any]) -> str:
    """Genera la seccion de fases completadas.

    Recorre las fases registradas en la sesion y genera una tabla con
    el nombre de cada fase, su resultado y los artefactos generados.

    Args:
        session: estado de la sesion.

    Returns:
        Bloque markdown con la tabla de fases.
    """
    fases = session.get("fases_completadas", [])
    if not fases:
        return "## Fases\n\nNo se completaron fases en esta sesion.\n"

    lines = ["## Fases completadas\n"]
    lines.append("| Fase | Resultado | Artefactos |")
    lines.append("|------|-----------|------------|")

    for fase in fases:
        nombre = _markdown_table_cell(fase.get("nombre", "desconocida"))
        resultado = _markdown_table_cell(fase.get("resultado", "sin resultado"))
        artefactos = fase.get("artefactos", [])
        artefactos_str = (
            _markdown_table_cell(", ".join(_single_line_text(a) for a in artefactos))
            if artefactos
            else "-"
        )
        lines.append(f"| {nombre} | {resultado} | {artefactos_str} |")

    lines.append("")
    fase_actual = session.get("fase_actual", "desconocida")
    if fase_actual == "completado":
        lines.append("Estado final: **flujo completado**.")
    else:
        lines.append(f"Estado final: detenido en fase **{fase_actual}**.")

    return "\n".join(lines) + "\n"


def _section_evidence(evidence: Optional[Dict[str, Any]] = None) -> str:
    """Genera la seccion de evidencia de tests.

    Muestra si se ejecutaron tests durante la sesion, cuantos y cual
    fue el resultado de cada uno.

    Args:
        evidence: datos de evidencia de ``get_evidence()``. Si es None,
            se omite la seccion.

    Returns:
        Bloque markdown con la evidencia.
    """
    if evidence is None:
        return ""

    if not evidence.get("has_evidence", False):
        return (
            "## Evidencia de tests\n\n"
            "No se ejecutaron tests durante esta sesion.\n"
        )

    records = evidence.get("records", [])
    all_passing = evidence.get("all_passing", False)

    lines = ["## Evidencia de tests\n"]
    status = "todos verdes" if all_passing else "con fallos"
    lines.append(f"Se ejecutaron **{len(records)} rondas de tests** ({status}).\n")
    lines.append("| Hora | Comando | Resultado |")
    lines.append("|------|---------|-----------|")

    for record in records:
        ts = record.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            hora = dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            hora = ts[:19] if ts else "-"

        cmd = _single_line_text(record.get("command", ""))
        cmd_short = cmd[:60] + "..." if len(cmd) > 60 else cmd
        result = record.get("result", "unknown")
        result_display = {
            "pass": "OK",
            "fail": "FALLO",
            "unknown": "indeterminado",
        }.get(result, result)

        lines.append(
            f"| {_markdown_table_cell(hora)} | "
            f"{_markdown_table_cell(_markdown_inline_code(cmd_short))} | "
            f"{_markdown_table_cell(result_display)} |"
        )

    return "\n".join(lines) + "\n"


def _section_team(session: Dict[str, Any]) -> str:
    """Genera la seccion de equipo de sesion.

    Muestra los agentes opcionales activos durante la sesion, si los hay.

    Args:
        session: estado de la sesion.

    Returns:
        Bloque markdown con el equipo.
    """
    equipo = session.get("equipo_sesion")
    if not equipo:
        return ""

    opcionales = equipo.get("opcionales_activos", {})
    activos = [name for name, enabled in opcionales.items() if enabled]

    if not activos:
        return ""

    lines = ["## Equipo de sesion\n"]
    source = _session_team_source_label(session)
    if source:
        lines.append(f"Origen runtime: **{source}**.\n")
    lines.append("Agentes opcionales activos:\n")
    for agent in order_optional_agent_names(activos):
        lines.append(f"- {agent}")

    on_demand = _session_on_demand_optionals_for_flow(session)
    if on_demand:
        lines.append("")
        lines.append("Opcionales solo bajo demanda en este flujo:\n")
        for agent in on_demand:
            lines.append(f"- {agent}")

    return "\n".join(lines) + "\n"


def _section_artifacts(session: Dict[str, Any]) -> str:
    """Genera la seccion de artefactos generados.

    Lista todos los artefactos registrados durante el flujo.

    Args:
        session: estado de la sesion.

    Returns:
        Bloque markdown con los artefactos.
    """
    artefactos = session.get("artefactos", [])
    if not artefactos:
        return ""

    lines = ["## Artefactos generados\n"]
    for artefacto in artefactos:
        lines.append(f"- {_markdown_inline_code(artefacto)}")

    return "\n".join(lines) + "\n"


def _get_plugin_version() -> str:
    """Lee la version del plugin desde plugin.json. Fallback a hardcoded."""
    try:
        plugin_path = os.path.join(
            os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json"
        )
        with open(plugin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("version", "0.5.1")
    except (OSError, json.JSONDecodeError, KeyError):
        return "0.5.1"


def _section_mode(session: Dict[str, Any]) -> str:
    """Genera la seccion de modo de sesion (autopilot o interactivo).

    Args:
        session: estado de la sesion.

    Returns:
        Bloque markdown con el modo de sesion.
    """
    is_autopilot = session.get("autopilot", False)
    modo = "autopilot" if is_autopilot else "interactivo"
    return f"## Modo de sesion\n\nModo: **{modo}**\n"


def _section_iterations(session: Dict[str, Any]) -> str:
    """Genera la seccion de iteraciones por fase si alguna tuvo reintentos.

    Solo muestra fases que tuvieron al menos una iteracion, lo que
    indica que la gate correspondiente no se supero a la primera.

    Args:
        session: estado de la sesion.

    Returns:
        Bloque markdown con la tabla de iteraciones, o cadena vacia
        si ninguna fase tuvo reintentos.
    """
    fases = session.get("fases_completadas", [])
    fases_con_iteraciones = [
        f for f in fases if f.get("iteraciones", 0) > 0
    ]
    if not fases_con_iteraciones:
        return ""

    lines = ["## Iteraciones por fase\n"]
    lines.append("| Fase | Iteraciones |")
    lines.append("|------|------------|")
    for fase in fases_con_iteraciones:
        lines.append(
            f"| {_markdown_table_cell(fase['nombre'])} | "
            f"{_markdown_table_cell(fase['iteraciones'])} |"
        )

    return "\n".join(lines) + "\n"


def _estimate_duration(session: Dict[str, Any]) -> str:
    """Estima la duracion de la sesion a partir de las marcas temporales.

    Calcula la diferencia entre ``creado_en`` y ``actualizado_en``.

    Args:
        session: estado de la sesion.

    Returns:
        Cadena con la duracion estimada en formato legible.
    """
    creado = session.get("creado_en", "")
    actualizado = session.get("actualizado_en", "")

    if not creado or not actualizado:
        return "no disponible"

    try:
        dt_start = datetime.fromisoformat(creado)
        dt_end = datetime.fromisoformat(actualizado)
        delta = dt_end - dt_start
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return "no disponible"
        if total_seconds < 60:
            return f"{total_seconds} segundos"
        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes} minutos"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m"
    except (ValueError, TypeError):
        return "no disponible"


# --- Funcion principal ---

def generate_report(
    session: Dict[str, Any],
    evidence: Optional[Dict[str, Any]] = None,
    project_dir: Optional[str] = None,
    completed: bool = True,
) -> str:
    """Genera un informe de sesion completo en formato markdown.

    Ensambla las secciones del informe en orden: resumen ejecutivo,
    siguiente paso, modo, fases, iteraciones, evidencia de tests, equipo
    y artefactos. El informe se guarda en el
    directorio ``docs/alfred-reports/`` del proyecto.

    Si ``completed`` es False, se usa un template alternativo que marca
    la sesion como interrumpida, util para informes parciales generados
    cuando el hook de stop detecta una sesion en curso.

    Args:
        session: estado de la sesion (dict del orquestador).
        evidence: datos de evidencia de tests (opcional).
        project_dir: directorio del proyecto. Si es None, usa cwd.
        completed: True si la sesion esta completada, False si es parcial.

    Returns:
        Ruta del fichero generado.
    """
    base = project_dir or os.getcwd()

    # Ensamblar secciones
    decisions = _session_decisions_snapshot(base, session, completed)
    secciones = []
    secciones.append(_section_summary(session, evidence, decisions, base, completed))
    secciones.append(_section_next_step(session, base, completed))
    secciones.append(_section_decisions(decisions))
    secciones.append(_section_mode(session))
    secciones.append(_section_phases(session))
    secciones.append(_section_iterations(session))
    secciones.append(_section_evidence(evidence))
    secciones.append(_section_team(session))
    secciones.append(_section_artifacts(session))

    # Filtrar secciones vacias
    secciones_text = "\n".join(s for s in secciones if s.strip())

    # Datos del encabezado
    comando = _single_line_text(session.get("comando", "desconocido"), default="desconocido")
    descripcion = _single_line_text(
        session.get("descripcion", "sin descripcion"), default="sin descripcion"
    )
    duracion = _estimate_duration(session)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    version = _get_plugin_version()

    template = _REPORT_TEMPLATE if completed else _REPORT_TEMPLATE_INTERRUPTED
    report_content = template.format(
        comando=comando,
        fecha=fecha,
        duracion=duracion,
        descripcion=descripcion,
        secciones=secciones_text,
        version=version,
    )

    # Guardar el informe
    report_dir = os.path.join(base, _REPORT_DIR)
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    # Sanitizar el nombre del comando para evitar path traversal
    safe_comando = re.sub(r"[^a-zA-Z0-9_-]", "_", comando)
    filename = f"{timestamp}-{safe_comando}.md"
    report_path = os.path.join(report_dir, filename)

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
    except OSError as e:
        raise RuntimeError(
            f"No se pudo guardar el informe de sesion en '{report_path}': {e}. "
            f"Comprueba que el directorio '{report_dir}' existe y tiene "
            f"permisos de escritura."
        ) from e

    return report_path
