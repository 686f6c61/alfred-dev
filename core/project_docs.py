#!/usr/bin/env python3
"""Documentación viva del proyecto: esqueleto, índice y comprobación por gate.

El helper no rellena prosa. Crea ficheros estructurales, actualiza el índice
y dice qué falta para cerrar una fase. El contenido lo escriben los agentes.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


SCAFFOLD_MARKER = "<!-- alfred-doc:scaffold -->"
FILLED_MARKER = "<!-- alfred-doc:filled -->"
INDEX_MARKER = "<!-- alfred-doc:index -->"

PROJECT_DOCS_DIR = os.path.join("docs", "project")
ADR_DIR = os.path.join("docs", "adr")

DOC_FILES = {
    "index": os.path.join(PROJECT_DOCS_DIR, "README.md"),
    "architecture": os.path.join(PROJECT_DOCS_DIR, "architecture.md"),
    "compliance": os.path.join(PROJECT_DOCS_DIR, "compliance.md"),
    "threat_model": os.path.join(PROJECT_DOCS_DIR, "threat-model.md"),
    "dependencies": os.path.join(PROJECT_DOCS_DIR, "dependencies.md"),
}

DOC_TITLES = {
    "index": "Índice de documentación viva",
    "architecture": "Arquitectura del proyecto",
    "compliance": "Registro de compliance",
    "threat_model": "Modelo de amenazas",
    "dependencies": "Dependencias evaluadas",
}

# (documento, "exists" | "filled")
_Req = Tuple[str, str]

REQUIREMENTS: Dict[Tuple[str, str], Tuple[_Req, ...]] = {
    ("feature", "producto"): (("index", "exists"),),
    ("feature", "estilo_visual"): (("index", "exists"),),
    ("feature", "arquitectura"): (
        ("index", "exists"),
        ("architecture", "filled"),
        ("threat_model", "filled"),
    ),
    ("feature", "desarrollo"): (("index", "exists"),),
    ("feature", "calidad"): (
        ("index", "exists"),
        ("compliance", "filled"),
    ),
    ("feature", "documentacion"): (
        ("index", "exists"),
        ("architecture", "filled"),
    ),
    ("feature", "entrega"): (("index", "exists"),),
    ("fix", "diagnostico"): (("index", "exists"),),
    ("fix", "correccion"): (("index", "exists"),),
    ("fix", "validacion"): (("index", "exists"),),
    ("quick", "ejecucion_acotada"): (("index", "exists"),),
    ("quick", "validacion_rapida"): (("index", "exists"),),
    ("spike", "exploracion"): (("index", "exists"),),
    ("spike", "conclusiones"): (("index", "exists"),),
    ("audit", "*"): (
        ("index", "exists"),
        ("compliance", "filled"),
        ("threat_model", "exists"),
    ),
    ("ship", "auditoria_final"): (
        ("index", "exists"),
        ("compliance", "exists"),
    ),
    ("ship", "documentacion"): (("index", "exists"),),
    ("ship", "empaquetado"): (("index", "exists"),),
    ("ship", "despliegue"): (("index", "exists"),),
    ("map-codebase", "*"): (
        ("index", "exists"),
        ("architecture", "exists"),
    ),
    ("discuss", "*"): (("index", "exists"),),
}

_SCAFFOLDS: Dict[str, str] = {
    "architecture": f"""# Arquitectura del proyecto

{SCAFFOLD_MARKER}

## Contexto

_(pendiente)_

## Diagrama

```mermaid
flowchart LR
    pendiente[Pendiente de dibujar]
```

## Componentes

| Componente | Responsabilidad | Límites |
|------------|-----------------|--------|
| _(pendiente)_ |  |  |

## Flujos de datos

_(pendiente)_

## Decisiones abiertas

_(pendiente)_
""",
    "compliance": f"""# Registro de compliance

{SCAFFOLD_MARKER}

No es un dictamen jurídico. Es un registro técnico con evidencia.

## Alcance

| Marco | Aplica | Motivo |
|-------|--------|--------|
| RGPD | pendiente |  |
| NIS2 | pendiente |  |
| CRA | pendiente |  |

## Controles

| Control | Marco | Estado | Evidencia |
|---------|-------|--------|-----------|
| _(pendiente)_ |  | pendiente |  |

Estados: `cumple` (con evidencia), `parcial`, `pendiente`, `no aplica`, `riesgo aceptado`.

## Riesgos aceptados

| Hueco | Quién | Cuándo | Motivo |
|-------|-------|--------|--------|
| _(ninguno)_ |  |  |  |
""",
    "threat_model": f"""# Modelo de amenazas

{SCAFFOLD_MARKER}

**Metodología:** STRIDE

## Superficie

_(pendiente: componentes reales, no una lista genérica)_

## Límites de confianza

_(pendiente)_

## STRIDE

| Amenaza | Componente | Probabilidad | Impacto | Mitigación o riesgo aceptado |
|---------|------------|--------------|---------|------------------------------|
| _(pendiente)_ |  |  |  |  |
""",
    "dependencies": f"""# Dependencias evaluadas

{SCAFFOLD_MARKER}

| Paquete | Versión | Veredicto | Licencia | Notas |
|---------|---------|-----------|----------|-------|
| _(ninguna evaluada)_ |  |  |  |  |
""",
}


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _abs(project_dir: str, relative: str) -> str:
    return os.path.join(os.path.abspath(project_dir), relative)


def _read(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def doc_status(text: str) -> str:
    """Clasifica un documento: empty, scaffold o filled."""
    if not text.strip():
        return "empty"
    if FILLED_MARKER in text:
        return "filled"
    if SCAFFOLD_MARKER in text:
        return "scaffold"
    return "filled"


def required_docs(command: str, phase: str = "") -> Tuple[_Req, ...]:
    """Devuelve los requisitos de documentación para un comando y fase."""
    comando = (command or "").strip().lower()
    fase = (phase or "").strip().lower() or "*"
    exact = REQUIREMENTS.get((comando, fase))
    if exact is not None:
        return exact
    return REQUIREMENTS.get((comando, "*"), ())


def ensure_project_docs(project_dir: str) -> Dict[str, Any]:
    """Crea el esqueleto que falte y refresca el índice. No rellena prosa."""
    created: List[str] = []
    for key, relative in DOC_FILES.items():
        if key == "index":
            continue
        path = _abs(project_dir, relative)
        if not os.path.isfile(path):
            _write(path, _SCAFFOLDS[key])
            created.append(relative)
    os.makedirs(_abs(project_dir, ADR_DIR), exist_ok=True)
    index_relative = refresh_index(project_dir)
    return {
        "created": created,
        "index": index_relative,
        "docs": inspect_docs(project_dir),
    }


def inspect_docs(project_dir: str) -> List[Dict[str, str]]:
    """Estado de cada documento vivo."""
    rows: List[Dict[str, str]] = []
    for key, relative in DOC_FILES.items():
        if key == "index":
            continue
        path = _abs(project_dir, relative)
        text = _read(path)
        status = doc_status(text) if text or os.path.isfile(path) else "missing"
        updated = ""
        if os.path.isfile(path):
            updated = datetime.fromtimestamp(
                os.path.getmtime(path), tz=timezone.utc
            ).date().isoformat()
        rows.append(
            {
                "key": key,
                "path": relative,
                "title": DOC_TITLES[key],
                "status": status,
                "updated": updated,
            }
        )
    return rows


def refresh_index(project_dir: str) -> str:
    """Reescribe la tabla del índice. Conserva notas bajo el marcador de corte."""
    relative = DOC_FILES["index"]
    path = _abs(project_dir, relative)
    existing = _read(path)
    notes = ""
    cut = "## Notas del equipo"
    if cut in existing:
        notes = existing.split(cut, 1)[1].strip()

    rows = inspect_docs(project_dir)
    lines = [
        "# Documentación viva del proyecto",
        "",
        INDEX_MARKER,
        "",
        "Solo se actualiza lo que la fase ha cambiado. El Escriba sincroniza este índice.",
        "",
        "| Documento | Estado | Actualizado |",
        "|-----------|--------|-------------|",
    ]
    for row in rows:
        lines.append(f"| `{row['path']}` | {row['status']} | {row['updated'] or '—'} |")

    adr_count = len(list_adr_files(project_dir))
    next_number = next_adr_number(project_dir)
    lines.extend(
        [
            "",
            f"ADRs en `{ADR_DIR}/`: {adr_count}. Siguiente número: {next_number:03d}.",
            "",
            "## Notas del equipo",
            "",
        ]
    )
    lines.append(notes if notes else "_(sin notas)_")
    lines.append("")
    _write(path, "\n".join(lines))
    return relative


def list_adr_files(project_dir: str) -> List[str]:
    directory = _abs(project_dir, ADR_DIR)
    if not os.path.isdir(directory):
        return []
    names = [
        name
        for name in os.listdir(directory)
        if name.endswith(".md") and name.startswith("ADR-")
    ]
    return sorted(names)


def next_adr_number(project_dir: str) -> int:
    highest = 0
    for name in list_adr_files(project_dir):
        match = re.match(r"ADR-(\d+)", name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _slugify(title: str) -> str:
    normalized = title.strip().lower()
    normalized = re.sub(r"[^a-z0-9áéíóúüñ]+", "-", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "decision"


def scaffold_adr(project_dir: str, title: str) -> Dict[str, Any]:
    """Crea el esqueleto del siguiente ADR. No escribe la decisión."""
    number = next_adr_number(project_dir)
    slug = _slugify(title)
    relative = os.path.join(ADR_DIR, f"ADR-{number:03d}-{slug}.md")
    path = _abs(project_dir, relative)
    if os.path.isfile(path):
        return {"path": relative, "number": number, "created": False}
    content = (
        f"# ADR-{number:03d}: {title.strip() or 'Decisión'}\n\n"
        f"{SCAFFOLD_MARKER}\n\n"
        f"**Fecha:** {_now_date()}\n"
        "**Estado:** propuesto\n"
        "**Autor:** architect\n\n"
        "## Contexto\n\n_(pendiente)_\n\n"
        "## Opciones evaluadas\n\n### Opción 1\n\n_(pendiente)_\n\n"
        "### Opción 2\n\n_(pendiente)_\n\n"
        "## Decisión\n\n_(pendiente)_\n\n"
        "## Consecuencias\n\n_(pendiente)_\n"
    )
    _write(path, content)
    refresh_index(project_dir)
    return {"path": relative, "number": number, "created": True}


def check_project_docs(
    project_dir: str,
    command: str,
    phase: str = "",
) -> Dict[str, Any]:
    """Comprueba los documentos exigidos por la gate. No escribe nada."""
    requirements = required_docs(command, phase)
    missing: List[str] = []
    empty: List[str] = []
    ok: List[str] = []
    inspected = {row["key"]: row for row in inspect_docs(project_dir)}
    index_path = _abs(project_dir, DOC_FILES["index"])
    inspected["index"] = {
        "key": "index",
        "path": DOC_FILES["index"],
        "status": "filled" if os.path.isfile(index_path) else "missing",
    }

    for key, rule in requirements:
        row = inspected.get(key) or {"path": DOC_FILES.get(key, key), "status": "missing"}
        status = row["status"]
        path = row["path"]
        if status == "missing":
            missing.append(path)
            continue
        if rule == "filled" and status != "filled":
            empty.append(path)
            continue
        ok.append(path)

    passed = not missing and not empty
    return {
        "passed": passed,
        "command": command,
        "phase": phase or "*",
        "required": [
            {"doc": key, "rule": rule, "path": DOC_FILES[key]}
            for key, rule in requirements
        ],
        "ok": ok,
        "missing": missing,
        "empty": empty,
    }


def render_sync_markdown(result: Dict[str, Any]) -> str:
    lines = ["## Docs de proyecto", ""]
    created = result.get("created") or []
    if created:
        lines.append("Creados:")
        lines.extend(f"- `{path}`" for path in created)
        lines.append("")
    else:
        lines.append("No faltaba esqueleto.")
        lines.append("")
    lines.append("Estado:")
    for row in result.get("docs") or []:
        lines.append(f"- `{row['path']}`: {row['status']}")
    lines.append("")
    lines.append(f"Índice: `{result.get('index', DOC_FILES['index'])}`")
    return "\n".join(lines)


def render_check_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "## Comprobación de docs de proyecto",
        "",
        f"Comando: `{result['command']}` / fase: `{result['phase']}`",
        "",
    ]
    if result["passed"]:
        lines.append("Resultado: listo para la gate.")
    else:
        lines.append("Resultado: no se puede cerrar la gate.")
    if result["missing"]:
        lines.append("")
        lines.append("Faltan:")
        lines.extend(f"- `{path}`" for path in result["missing"])
    if result["empty"]:
        lines.append("")
        lines.append("Siguen en esqueleto (hace falta contenido real y `<!-- alfred-doc:filled -->`):")
        lines.extend(f"- `{path}`" for path in result["empty"])
    if result["ok"]:
        lines.append("")
        lines.append("Cubiertos:")
        lines.extend(f"- `{path}`" for path in result["ok"])
    return "\n".join(lines)


def render_adr_markdown(result: Dict[str, Any]) -> str:
    verb = "Creado" if result.get("created") else "Ya existía"
    return (
        f"## ADR\n\n{verb}: `{result['path']}`\n\n"
        "Rellena contexto, opciones, decisión y consecuencias. "
        f"Sustituye `{SCAFFOLD_MARKER}` por `{FILLED_MARKER}` al terminar."
    )
