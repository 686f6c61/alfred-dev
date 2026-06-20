#!/usr/bin/env python3
"""Genera un reporte Markdown de apoyo para revisar evidencias manuales.

Este script no aprueba la release ni modifica la plantilla de review. Solo
resume la evidencia y marca riesgos para que una persona revise con menos
friccion antes de usar scripts/manual_review_gate.py.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.secrets import find_secret_label, sanitize_text


RISK_TERMS = (
    "traceback",
    "reached maximum budget",
    "maximum budget",
    "incoherencia",
    "no se pudo",
    "failed",
    "error",
    "exception",
    "invalid authentication",
)


class ManualReviewReportError(AssertionError):
    """No se pudo construir el reporte de revision asistida."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManualReviewReportError(f"No existe {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManualReviewReportError(f"{path} no contiene JSON valido: {exc}") from exc
    if not isinstance(payload, dict):
        raise ManualReviewReportError(f"{path} debe contener un objeto JSON")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clip(value: object, limit: int = 420) -> str:
    text = sanitize_text(str(value or "").strip())
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _risk_flags(case: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    status = str(case.get("status") or "")
    if status != "needs_human_review":
        flags.append(f"status={status or 'missing'}")
    if case.get("returncode") not in (0, None):
        flags.append(f"returncode={case.get('returncode')}")
    if case.get("api_error_status"):
        flags.append(f"api_error_status={case.get('api_error_status')}")
    if not str(case.get("response_preview") or "").strip():
        flags.append("empty_response_preview")
    if str(case.get("stderr_preview") or "").strip():
        flags.append("stderr_preview_present")

    combined = "\n".join(
        str(case.get(key) or "")
        for key in ("reason", "response_preview", "stderr_preview")
    )
    lowered = combined.lower()
    for term in RISK_TERMS:
        if term in lowered:
            flags.append(f"term:{term}")
    secret_label = find_secret_label(combined)
    if secret_label:
        flags.append(f"secret:{secret_label}")
    return sorted(set(flags))


def _review_state(review_path: Path | None) -> dict[str, Any] | None:
    if review_path is None:
        return None
    return _load_json(review_path)


def _manual_review_gate_module():
    spec = importlib.util.spec_from_file_location(
        "manual_review_gate_report",
        ROOT / "scripts" / "manual_review_gate.py",
    )
    if spec is None or spec.loader is None:
        raise ManualReviewReportError("No se pudo cargar scripts/manual_review_gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case_list(case_ids: list[str]) -> str:
    return ", ".join(f"`{case_id}`" for case_id in sorted(case_ids))


def _review_quality_flags(review: dict[str, Any]) -> list[str]:
    gate = _manual_review_gate_module()
    flags: list[str] = []
    secret_findings = gate._iter_secret_findings(review, "review")
    if secret_findings:
        flags.append(
            "review_secret_findings: "
            + ", ".join(_clip(finding, 120) for finding in secret_findings[:8])
        )

    reviewed_cases = review.get("cases")
    if not isinstance(reviewed_cases, dict):
        flags.append("review.cases debe ser un objeto por case_id")
        return flags

    missing_notes: list[str] = []
    low_quality_notes: list[str] = []
    invalid_cases: list[str] = []
    note_to_case_ids: dict[str, list[str]] = {}
    for case_id, reviewed_case in sorted(reviewed_cases.items()):
        case_id_text = str(case_id)
        if not isinstance(reviewed_case, dict):
            invalid_cases.append(case_id_text)
            continue
        note = reviewed_case.get("notes", "")
        normalized_note = gate._normalize_review_note(note)
        if not normalized_note:
            missing_notes.append(case_id_text)
            continue
        if gate._is_low_quality_review_note(note):
            low_quality_notes.append(case_id_text)
        note_to_case_ids.setdefault(normalized_note, []).append(case_id_text)

    repeated_notes = [
        case_ids
        for case_ids in note_to_case_ids.values()
        if len(case_ids) > 1
    ]
    if invalid_cases:
        flags.append(f"cases_invalidos: {_case_list(invalid_cases)}")
    if missing_notes:
        flags.append(f"notes_missing: {_case_list(missing_notes)}")
    if low_quality_notes:
        flags.append(f"notes_low_quality: {_case_list(low_quality_notes)}")
    if repeated_notes:
        groups = "; ".join(_case_list(group) for group in repeated_notes)
        flags.append(f"notes_repeated: {groups}")
    return flags


def _plugin_surface_flags(evidence: dict[str, Any]) -> list[str]:
    surface = evidence.get("plugin_surface")
    if not isinstance(surface, dict):
        return ["evidence.plugin_surface debe ser un objeto"]

    plugin_dir_text = str(evidence.get("plugin_dir") or "").strip()
    if not plugin_dir_text:
        return ["evidence.plugin_dir es obligatorio para comparar la superficie actual"]

    plugin_dir = Path(plugin_dir_text).expanduser()
    if not plugin_dir.is_dir():
        return [f"evidence.plugin_dir no existe o no es directorio: {_clip(plugin_dir, 180)}"]

    gate = _manual_review_gate_module()
    manual_smoke = gate._manual_smoke_module()
    current_surface = manual_smoke._plugin_surface_snapshot(plugin_dir)
    checks = (
        ("roots", "evidence.plugin_surface.roots no coincide con el plugin actual"),
        ("file_count", "evidence.plugin_surface.file_count no coincide con el plugin actual"),
        ("sha256", "evidence.plugin_surface.sha256 no coincide con el plugin actual"),
    )
    flags: list[str] = []
    for key, message in checks:
        if surface.get(key) != current_surface.get(key):
            flags.append(
                f"{message} "
                f"(evidencia={_clip(surface.get(key), 160)}, actual={_clip(current_surface.get(key), 160)})"
            )
    return flags


def build_report(
    evidence_path: Path,
    review_path: Path | None = None,
) -> str:
    evidence = _load_json(evidence_path)
    review = _review_state(review_path)
    cases = [
        case for case in evidence.get("cases", [])
        if isinstance(case, dict)
    ]
    counts = evidence.get("counts") if isinstance(evidence.get("counts"), dict) else {}
    surface = evidence.get("plugin_surface") if isinstance(evidence.get("plugin_surface"), dict) else {}

    lines: list[str] = [
        "# Reporte asistido de revision manual",
        "",
        "> Este reporte no aprueba la release. Es una ayuda de lectura; la aprobacion real sigue en `scripts/manual_review_gate.py` y requiere revision humana explicita.",
        "",
        "## Resumen",
        "",
        f"- Evidencia: `{evidence_path}`",
        f"- Evidence SHA256: `{_sha256(evidence_path)}`",
        f"- Version: `{evidence.get('version', '-')}`",
        f"- Plugin source: `{evidence.get('plugin_source', '-')}`",
        f"- Plugin dir: `{evidence.get('plugin_dir', '-')}`",
        f"- Plugin surface SHA256: `{surface.get('sha256', '-')}`",
        f"- Casos: total={counts.get('total', len(cases))}, needs_human_review={counts.get('needs_human_review', '-')}, failed={counts.get('failed', '-')}, blocked_auth={counts.get('blocked_auth', '-')}",
    ]
    auth = evidence.get("auth_preflight")
    if isinstance(auth, dict):
        lines.extend(
            [
                f"- Auth preflight: `{auth.get('status', '-')}` ({_clip(auth.get('reason'), 140)})",
                f"- Claude CLI: `{((auth.get('auth_status') or {}).get('claude_version') or '-')}`",
            ]
        )
    if review is None:
        lines.append("- Review template: no suministrada")
    else:
        lines.extend(
            [
                f"- Review template: `{review_path}`",
                f"- Review approved: `{review.get('approved', False)}`",
                f"- Reviewer: `{review.get('reviewer') or '-'}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Superficie Del Plugin",
            "",
        ]
    )
    surface_flags = _plugin_surface_flags(evidence)
    if not surface_flags:
        lines.append("- Sin flags de superficie: la evidencia coincide con el plugin actual.")
    else:
        for flag in surface_flags:
            lines.append(f"- {flag}")

    lines.extend(
        [
            "",
            "## Calidad De Review Humana",
            "",
        ]
    )
    if review is None:
        lines.append("- Sin plantilla de review suministrada.")
    else:
        review_flags = _review_quality_flags(review)
        if not review_flags:
            lines.append(
                "- Sin flags automaticos de notas humanas. Sigue siendo necesaria revision caso por caso."
            )
        else:
            for flag in review_flags:
                lines.append(f"- {flag}")

    all_flags = {case.get("case_id", "-"): _risk_flags(case) for case in cases}
    flagged = {case_id: flags for case_id, flags in all_flags.items() if flags}
    lines.extend(
        [
            "",
            "## Flags De Riesgo",
            "",
        ]
    )
    if not flagged:
        lines.append("- Sin flags automaticos. Sigue siendo necesaria revision humana caso por caso.")
    else:
        for case_id, flags in sorted(flagged.items()):
            lines.append(f"- `{case_id}`: {', '.join(flags)}")

    lines.extend(
        [
            "",
            "## Casos",
            "",
            "| Caso | Estado | Duracion | Coste | Flags | Preview |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for case in cases:
        case_id = str(case.get("case_id") or "-")
        flags = ", ".join(all_flags.get(case_id, [])) or "-"
        duration_ms = case.get("duration_ms")
        duration = f"{duration_ms} ms" if isinstance(duration_ms, int) else "-"
        cost = case.get("total_cost_usd")
        cost_text = f"${cost:.3f}" if isinstance(cost, (int, float)) else "-"
        preview = _clip(case.get("response_preview"), 260).replace("|", "\\|")
        lines.append(
            f"| `{case_id}` | `{case.get('status', '-')}` | {duration} | {cost_text} | {flags} | {preview or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Siguiente Paso",
            "",
            "- Revisar manualmente cada preview y los artefactos completos de los casos relevantes.",
            "- Completar la plantilla de review con `reviewer`, `reviewed_at`, `approved=true` y `cases.*.approved=true` solo tras revision humana real.",
            "- Ejecutar `npm run release:audit:manual:review` y `npm run release:audit:manual:review:installed` para el gate final.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_report(evidence_path: Path, review_path: Path | None, output_path: Path) -> list[str]:
    report = build_report(evidence_path, review_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    output_path.chmod(0o600)
    return [f"reporte creado en {output_path}", "este reporte no aprueba la release"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", help="JSON generado por scripts/manual_smoke.py")
    parser.add_argument(
        "review",
        nargs="?",
        help="Plantilla/review JSON opcional generado por manual_review_gate.py",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Ruta Markdown de salida para el reporte asistido",
    )
    args = parser.parse_args(argv)

    try:
        for line in write_report(
            Path(args.evidence),
            Path(args.review) if args.review else None,
            Path(args.output),
        ):
            print(line)
        return 0
    except ManualReviewReportError as exc:
        print(f"FAIL manual-review-report: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
