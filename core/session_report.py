#!/usr/bin/env python3
"""
Generador de informes de sesion para Alfred Dev.

Al finalizar una sesion de trabajo (evento Stop), este modulo genera un
informe en formato markdown con el resumen de la actividad: fases
completadas, artefactos generados, evidencia de tests, decisiones
tomadas y metricas basicas.

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
from typing import Any, Dict, List, Optional


# --- Formato del informe ---

_REPORT_DIR = "docs/alfred-reports"

_REPORT_TEMPLATE = """# Informe de sesion: {comando}

**Fecha:** {fecha}
**Duracion estimada:** {duracion}
**Descripcion:** {descripcion}

---

{secciones}

---

*Generado automaticamente por Alfred Dev v0.4.1*
"""


# --- Secciones del informe ---

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
        nombre = fase.get("nombre", "desconocida")
        resultado = fase.get("resultado", "sin resultado")
        artefactos = fase.get("artefactos", [])
        artefactos_str = ", ".join(artefactos) if artefactos else "-"
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

        cmd = record.get("command", "")
        cmd_short = cmd[:60] + "..." if len(cmd) > 60 else cmd
        result = record.get("result", "unknown")
        result_display = {
            "pass": "OK",
            "fail": "FALLO",
            "unknown": "indeterminado",
        }.get(result, result)

        lines.append(f"| {hora} | `{cmd_short}` | {result_display} |")

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
    lines.append("Agentes opcionales activos:\n")
    for agent in sorted(activos):
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
        lines.append(f"- `{artefacto}`")

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
) -> str:
    """Genera un informe de sesion completo en formato markdown.

    Ensambla las secciones del informe en orden: fases, evidencia de
    tests, equipo y artefactos. El informe se guarda en el directorio
    ``docs/alfred-reports/`` del proyecto.

    Args:
        session: estado de la sesion (dict del orquestador).
        evidence: datos de evidencia de tests (opcional).
        project_dir: directorio del proyecto. Si es None, usa cwd.

    Returns:
        Ruta del fichero generado.
    """
    base = project_dir or os.getcwd()

    # Ensamblar secciones
    secciones = []
    secciones.append(_section_phases(session))
    secciones.append(_section_evidence(evidence))
    secciones.append(_section_team(session))
    secciones.append(_section_artifacts(session))

    # Filtrar secciones vacias
    secciones_text = "\n".join(s for s in secciones if s.strip())

    # Datos del encabezado
    comando = session.get("comando", "desconocido")
    descripcion = session.get("descripcion", "sin descripcion")
    duracion = _estimate_duration(session)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report_content = _REPORT_TEMPLATE.format(
        comando=comando,
        fecha=fecha,
        duracion=duracion,
        descripcion=descripcion,
        secciones=secciones_text,
    )

    # Guardar el informe
    report_dir = os.path.join(base, _REPORT_DIR)
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
