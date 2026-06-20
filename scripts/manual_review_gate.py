#!/usr/bin/env python3
"""Gate de revisión humana para la matriz manual de Alfred Dev 0.6.0."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.secrets import find_secret_label

VERSION = "0.6.0"
CASE_CONTRACT_FIELDS = (
    "prompt",
    "expected",
    "setup",
    "commands",
    "suite",
    "option_keys",
    "runtime_keys",
)
CASE_SEQUENCE_FIELDS = {"commands", "option_keys", "runtime_keys"}
SENSITIVE_REVIEW_KEY_RE = re.compile(
    r"(?i)(password|passwd|api_key|apikey|api_secret|secret_key"
    r"|auth_token|access_token|private_key)"
)
GENERIC_REVIEW_NOTES = {
    "ok",
    "okay",
    "vale",
    "aprobado",
    "aprobada",
    "revisado",
    "revisada",
    "todo ok",
    "correcto",
    "correcta",
    "lgtm",
    "pass",
    "passed",
    "done",
    "hecho",
    "hecha",
    "si",
    "sí",
    "yes",
}
MIN_REVIEW_NOTE_CHARS = 24
MIN_REVIEW_NOTE_WORDS = 4


class ReviewGateError(AssertionError):
    """La evidencia manual no puede aprobar publicación."""


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewGateError(f"No existe {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewGateError(f"{path} no contiene JSON valido: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReviewGateError(f"{path} debe contener un objeto JSON")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same_evidence_reference(recorded: str, evidence_path: Path) -> bool:
    recorded_path = Path(recorded).expanduser()
    if not recorded_path.is_absolute():
        recorded_path = (Path.cwd() / recorded_path).resolve()
    else:
        recorded_path = recorded_path.resolve()
    return recorded_path == evidence_path.resolve()


def _manual_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "manual_smoke_review_gate",
        ROOT / "scripts" / "manual_smoke.py",
    )
    if spec is None or spec.loader is None:
        raise ReviewGateError("No se pudo cargar scripts/manual_smoke.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _missing_coverage(coverage: dict) -> list[str]:
    return [
        key
        for key, case_ids in sorted(coverage.items())
        if not isinstance(case_ids, list) or not case_ids
    ]


def _expected_coverages(manual_smoke) -> dict[str, dict[str, list[str]]]:
    return {
        "command_coverage": manual_smoke._case_command_coverage(),
        "option_coverage": manual_smoke._case_option_coverage(),
        "runtime_coverage": manual_smoke._case_runtime_coverage(),
    }


def _coverage_problems(
    coverage_key: str,
    actual_coverage,
    expected_coverage: dict[str, list[str]],
) -> list[str]:
    if not isinstance(actual_coverage, dict):
        return [f"{coverage_key} debe ser un objeto"]

    problems: list[str] = []
    actual_keys = set(actual_coverage)
    expected_keys = set(expected_coverage)
    missing_keys = sorted(expected_keys - actual_keys)
    extra_keys = sorted(actual_keys - expected_keys)
    empty_or_invalid = _missing_coverage(actual_coverage)
    mismatched_values = [
        key
        for key in sorted(actual_keys & expected_keys)
        if actual_coverage.get(key) != expected_coverage[key]
    ]

    if missing_keys:
        problems.append(f"{coverage_key} no incluye claves actuales: {missing_keys}")
    if extra_keys:
        problems.append(f"{coverage_key} contiene claves obsoletas/desconocidas: {extra_keys}")
    if empty_or_invalid:
        problems.append(f"{coverage_key} incompleto: {empty_or_invalid}")
    if mismatched_values:
        problems.append(
            f"{coverage_key} no coincide con matriz actual en: {mismatched_values}"
        )
    return problems


def _case_contract(case) -> dict:
    contract = {}
    for field in CASE_CONTRACT_FIELDS:
        value = getattr(case, field)
        if field in CASE_SEQUENCE_FIELDS:
            value = list(value)
        contract[field] = value
    return contract


def _evidence_case_contract(case: dict) -> dict:
    contract = {}
    for field in CASE_CONTRACT_FIELDS:
        value = case.get(field)
        if field in CASE_SEQUENCE_FIELDS and isinstance(value, tuple):
            value = list(value)
        contract[field] = value
    return contract


def _iter_secret_findings(value, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (
                SENSITIVE_REVIEW_KEY_RE.search(str(key))
                and isinstance(child, str)
                and len(child.strip()) >= 8
                and "[REDACTED:" not in child
            ):
                findings.append(f"{child_path}: HARDCODED_CREDENTIAL")
            findings.extend(_iter_secret_findings(child, child_path))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_iter_secret_findings(child, f"{path}.{index}"))
        return findings
    if isinstance(value, str):
        label = find_secret_label(value)
        if label:
            findings.append(f"{path}: {label}")
    return findings


def _normalize_review_note(note: object) -> str:
    return " ".join(str(note or "").strip().lower().split())


def _is_low_quality_review_note(note: object) -> bool:
    normalized = _normalize_review_note(note)
    if not normalized:
        return True
    if normalized in GENERIC_REVIEW_NOTES:
        return True
    if len(normalized) < MIN_REVIEW_NOTE_CHARS:
        return True
    if len(normalized.split()) < MIN_REVIEW_NOTE_WORDS:
        return True
    return False


def build_review_template(evidence_path: Path) -> dict:
    evidence = _load_json(evidence_path)
    evidence_secret_findings = _iter_secret_findings(evidence, "evidence")
    if evidence_secret_findings:
        raise ReviewGateError(
            "No se crea plantilla de revisión con evidencia que contiene "
            "posibles secretos reales: "
            + ", ".join(evidence_secret_findings[:8])
        )
    manual_smoke = _manual_smoke_module()
    cases_by_id = {
        case.get("case_id"): case
        for case in evidence.get("cases", [])
        if isinstance(case, dict) and case.get("case_id")
    }
    return {
        "version": VERSION,
        "evidence_file": str(evidence_path),
        "evidence_sha256": _sha256(evidence_path),
        "approved": False,
        "reviewer": "",
        "reviewed_at": "",
        "cases": {
            case.case_id: {
                "approved": False,
                "prompt": case.prompt,
                "expected": case.expected,
                "setup": case.setup,
                "commands": list(case.commands),
                "suite": case.suite,
                "option_keys": list(case.option_keys),
                "runtime_keys": list(case.runtime_keys),
                "status": cases_by_id.get(case.case_id, {}).get("status"),
                "response_preview": cases_by_id.get(case.case_id, {}).get("response_preview", ""),
                "notes": "",
            }
            for case in manual_smoke.CASES
        },
    }


def write_review_template(evidence_path: Path, review_path: Path) -> list[str]:
    if review_path.exists():
        raise ReviewGateError(f"{review_path} ya existe; no se sobrescribe")
    payload = build_review_template(evidence_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    review_path.chmod(0o600)
    return [
        f"plantilla creada en {review_path}",
        "rellena reviewer, reviewed_at, approved=true y cada cases.*.approved=true tras revisar la evidencia",
    ]


def validate_review(
    evidence_path: Path,
    review_path: Path,
    expected_plugin_source: str | None = None,
    require_current_auth_preflight: bool = False,
) -> list[str]:
    evidence = _load_json(evidence_path)
    review = _load_json(review_path)
    manual_smoke = _manual_smoke_module()
    required_cases = {case.case_id: case for case in manual_smoke.CASES}
    required_case_ids = set(required_cases)
    evidence_sha256 = _sha256(evidence_path)
    evidence_plugin_dir = Path(str(evidence.get("plugin_dir") or ""))
    evidence_surface = evidence.get("plugin_surface") or {}

    problems: list[str] = []
    if evidence.get("version") != VERSION:
        problems.append(f"evidence.version debe ser {VERSION}")
    if review.get("version") != VERSION:
        problems.append(f"review.version debe ser {VERSION}")
    evidence_secret_findings = _iter_secret_findings(evidence, "evidence")
    review_secret_findings = _iter_secret_findings(review, "review")
    if evidence_secret_findings:
        problems.append(
            "evidence contiene posibles secretos reales: "
            + ", ".join(evidence_secret_findings[:8])
        )
    if review_secret_findings:
        problems.append(
            "review contiene posibles secretos reales: "
            + ", ".join(review_secret_findings[:8])
        )
    if expected_plugin_source and evidence.get("plugin_source") != expected_plugin_source:
        problems.append(
            "evidence.plugin_source no coincide con el origen esperado: "
            f"{evidence.get('plugin_source')!r} != {expected_plugin_source!r}"
        )
    review_evidence_file = str(review.get("evidence_file", "")).strip()
    if not review_evidence_file:
        problems.append("review.evidence_file es obligatorio")
    elif not _same_evidence_reference(review_evidence_file, evidence_path):
        problems.append("review.evidence_file no coincide con el evidence pasado al gate")
    if review.get("evidence_sha256") != evidence_sha256:
        problems.append("review.evidence_sha256 no coincide con la evidencia actual")
    if not evidence_plugin_dir.is_dir():
        problems.append("evidence.plugin_dir no existe o no es un directorio")
    else:
        current_surface = manual_smoke._plugin_surface_snapshot(evidence_plugin_dir)
        if evidence_surface.get("roots") != current_surface.get("roots"):
            problems.append("evidence.plugin_surface.roots no coincide con el plugin actual")
        if evidence_surface.get("sha256") != current_surface.get("sha256"):
            problems.append("evidence.plugin_surface.sha256 no coincide con el plugin actual")
        if evidence_surface.get("file_count") != current_surface.get("file_count"):
            problems.append("evidence.plugin_surface.file_count no coincide con el plugin actual")
    if review.get("approved") is not True:
        problems.append("review.approved debe ser true")
    if not str(review.get("reviewer", "")).strip():
        problems.append("review.reviewer es obligatorio")
    if not str(review.get("reviewed_at", "")).strip():
        problems.append("review.reviewed_at es obligatorio")
    if require_current_auth_preflight:
        current_preflight = manual_smoke._auth_preflight()
        if current_preflight.get("status") != "ok":
            diagnosis = current_preflight.get("diagnosis")
            diagnosis_code = ""
            if isinstance(diagnosis, dict) and diagnosis.get("code"):
                diagnosis_code = f" ({diagnosis.get('code')})"
            problems.append(
                "preflight actual de Claude CLI no esta ok: "
                f"{current_preflight.get('status')}{diagnosis_code}; "
                f"{current_preflight.get('reason')}"
            )

    counts = evidence.get("counts") or {}
    if counts.get("failed", 0) != 0 or counts.get("blocked_auth", 0) != 0:
        problems.append(f"evidence contiene fallos o bloqueos: {counts}")
    if counts.get("total") != len(required_case_ids):
        problems.append(
            "evidence no cubre todos los casos manuales: "
            f"{counts.get('total')} != {len(required_case_ids)}"
        )
    if counts.get("needs_human_review") != len(required_case_ids):
        problems.append(
            "evidence.needs_human_review debe cubrir todos los casos manuales: "
            f"{counts.get('needs_human_review')} != {len(required_case_ids)}"
        )

    for coverage_key, expected_coverage in _expected_coverages(manual_smoke).items():
        problems.extend(
            _coverage_problems(
                coverage_key,
                evidence.get(coverage_key),
                expected_coverage,
            )
        )

    evidence_cases = evidence.get("cases")
    if not isinstance(evidence_cases, list):
        problems.append("evidence.cases debe ser una lista")
        evidence_case_ids: set[str] = set()
    else:
        invalid_entries = [
            str(index)
            for index, case in enumerate(evidence_cases)
            if not isinstance(case, dict) or not case.get("case_id")
        ]
        if invalid_entries:
            problems.append(f"evidence.cases contiene entradas invalidas: {invalid_entries}")
        case_id_list = [
            str(case.get("case_id"))
            for case in evidence_cases
            if isinstance(case, dict) and case.get("case_id")
        ]
        evidence_case_ids = {
            case_id
            for case_id in case_id_list
        }
        duplicate_case_ids = sorted({
            case_id for case_id in case_id_list
            if case_id_list.count(case_id) > 1
        })
        if duplicate_case_ids:
            problems.append(f"evidence.cases contiene case_id duplicados: {duplicate_case_ids}")
        if len(evidence_cases) != len(required_case_ids):
            problems.append(
                "evidence.cases debe tener exactamente un registro por caso manual: "
                f"{len(evidence_cases)} != {len(required_case_ids)}"
            )
        bad_status_cases = [
            str(case.get("case_id"))
            for case in evidence_cases
            if isinstance(case, dict)
            and case.get("case_id")
            and case.get("status") != "needs_human_review"
        ]
        if bad_status_cases:
            problems.append(
                "evidence.cases deben estar en needs_human_review: "
                f"{bad_status_cases}"
            )
        stale_cases = []
        for evidence_case in evidence_cases:
            if not isinstance(evidence_case, dict) or not evidence_case.get("case_id"):
                continue
            case_id = str(evidence_case.get("case_id"))
            if case_id not in required_cases:
                continue
            actual_contract = _evidence_case_contract(evidence_case)
            expected_contract = _case_contract(required_cases[case_id])
            mismatched_fields = [
                field
                for field in CASE_CONTRACT_FIELDS
                if actual_contract.get(field) != expected_contract[field]
            ]
            if mismatched_fields:
                stale_cases.append(f"{case_id}: {', '.join(mismatched_fields)}")
        if stale_cases:
            problems.append(
                "evidence.cases desalineados con matriz actual: "
                f"{stale_cases}"
            )
    missing_cases = sorted(required_case_ids - evidence_case_ids)
    extra_cases = sorted(evidence_case_ids - required_case_ids)
    if missing_cases:
        problems.append(f"evidence.cases no incluye: {missing_cases}")
    if extra_cases:
        problems.append(f"evidence.cases contiene casos desconocidos: {extra_cases}")

    reviewed_cases = review.get("cases")
    if not isinstance(reviewed_cases, dict):
        problems.append("review.cases debe ser un objeto por case_id")
        reviewed_case_ids: set[str] = set()
    else:
        reviewed_case_ids = set(reviewed_cases)
        not_approved = [
            case_id
            for case_id in sorted(required_case_ids)
            if not isinstance(reviewed_cases.get(case_id), dict)
            or reviewed_cases[case_id].get("approved") is not True
        ]
        if not_approved:
            problems.append(f"review.cases sin approved=true: {not_approved}")
        missing_notes = [
            case_id
            for case_id in sorted(required_case_ids)
            if isinstance(reviewed_cases.get(case_id), dict)
            and not str(reviewed_cases[case_id].get("notes", "")).strip()
        ]
        if missing_notes:
            problems.append(f"review.cases sin notes humanas: {missing_notes}")
        low_quality_notes = [
            case_id
            for case_id in sorted(required_case_ids)
            if isinstance(reviewed_cases.get(case_id), dict)
            and str(reviewed_cases[case_id].get("notes", "")).strip()
            and _is_low_quality_review_note(reviewed_cases[case_id].get("notes", ""))
        ]
        if low_quality_notes:
            problems.append(
                "review.cases con notes humanas demasiado genericas o cortas: "
                f"{low_quality_notes}"
            )
        note_to_case_ids: dict[str, list[str]] = {}
        for case_id in sorted(required_case_ids):
            reviewed_case = reviewed_cases.get(case_id)
            if not isinstance(reviewed_case, dict):
                continue
            normalized_note = _normalize_review_note(reviewed_case.get("notes", ""))
            if not normalized_note:
                continue
            note_to_case_ids.setdefault(normalized_note, []).append(case_id)
        repeated_notes = [
            case_ids
            for case_ids in note_to_case_ids.values()
            if len(case_ids) > 1
        ]
        if repeated_notes:
            problems.append(
                "review.cases contiene notes humanas repetidas sin revision caso por caso: "
                f"{repeated_notes}"
            )
        stale_review_cases = []
        for case_id in sorted(required_case_ids):
            reviewed_case = reviewed_cases.get(case_id)
            if not isinstance(reviewed_case, dict):
                continue
            actual_contract = _evidence_case_contract(reviewed_case)
            expected_contract = _case_contract(required_cases[case_id])
            mismatched_fields = [
                field
                for field in CASE_CONTRACT_FIELDS
                if actual_contract.get(field) != expected_contract[field]
            ]
            if mismatched_fields:
                stale_review_cases.append(f"{case_id}: {', '.join(mismatched_fields)}")
        if stale_review_cases:
            problems.append(
                "review.cases desalineados con matriz actual: "
                f"{stale_review_cases}"
            )
    missing_review = sorted(required_case_ids - reviewed_case_ids)
    extra_review = sorted(reviewed_case_ids - required_case_ids)
    if missing_review:
        problems.append(f"review.cases no incluye: {missing_review}")
    if extra_review:
        problems.append(f"review.cases contiene casos desconocidos: {extra_review}")

    if problems:
        raise ReviewGateError("; ".join(problems))

    return [
        f"evidencia manual {evidence_path} cubre {len(required_case_ids)} casos",
        f"plugin_source verificado: {evidence.get('plugin_source')}",
        f"revision humana {review_path} aprobada por {review['reviewer']}",
        f"review.evidence_sha256 coincide: {evidence_sha256}",
        f"review.evidence_file coincide: {review_evidence_file}",
        "coverage maps coinciden con la matriz manual actual",
        "review.cases coincide con la matriz manual actual",
        "evidence/review sin patrones de secretos reales",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--init-template",
        action="store_true",
        help="Crea una plantilla de revision humana a partir de la evidencia.",
    )
    parser.add_argument(
        "--expect-plugin-source",
        choices=("worktree", "installed-cache", "explicit"),
        help="Exige que evidence.plugin_source coincida con el origen revisado.",
    )
    parser.add_argument(
        "--require-current-auth-preflight",
        action="store_true",
        help=(
            "Antes de aprobar, ejecuta un preflight actual de claude -p para "
            "evitar validar evidencias antiguas con autenticacion rota."
        ),
    )
    parser.add_argument("evidence", help="JSON generado por scripts/manual_smoke.py")
    parser.add_argument("review", help="JSON de revision humana caso por caso")
    args = parser.parse_args(argv)

    try:
        if args.init_template:
            lines = write_review_template(Path(args.evidence), Path(args.review))
        else:
            lines = validate_review(
                Path(args.evidence),
                Path(args.review),
                expected_plugin_source=args.expect_plugin_source,
                require_current_auth_preflight=args.require_current_auth_preflight,
            )
        for line in lines:
            print(f"ok {line}")
    except ReviewGateError as exc:
        print(f"FAIL manual-review-gate: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
