#!/usr/bin/env python3
"""Tests para el orquestador de flujos."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (
    CURRENT_RELATIVE_PATH,
    PROGRESS_MD_RELATIVE_PATH,
    TRACEABILITY_MD_RELATIVE_PATH,
    UAT_JSON_RELATIVE_PATH,
    UAT_MD_RELATIVE_PATH,
    load_kanban_board,
    write_uat_files,
)
from core.config_loader import load_config, save_project_config
from core.orchestrator import (
    FLOWS, create_session, advance_phase, check_gate,
    load_state, save_state, get_effective_agents,
    run_flow, _validate_equipo_sesion, _KNOWN_OPTIONAL_AGENTS,
    OPTIONAL_INTEGRATIONS,
    should_retry_phase, reset_phase_iterations,
    is_autopilot_gate_passable, run_flow_autopilot,
    MAX_PHASE_ITERATIONS,
)


def _save_project_config_with_optionals(
    project_dir: str,
    enabled_optionals,
    *,
    notes: str = "Configuración temporal para test.",
) -> str:
    """Guarda una config local mínima activando los opcionales indicados."""
    config = load_config("/ruta/que/no/existe")
    for agent_name in enabled_optionals:
        config["agentes_opcionales"][agent_name] = True
    return save_project_config(
        project_dir,
        config,
        notes=notes,
        include_defaults=False,
    )


class TestFlows(unittest.TestCase):
    def test_feature_flow_has_7_phases(self):
        self.assertEqual(len(FLOWS["feature"]["fases"]), 7)

    def test_fix_flow_has_3_phases(self):
        self.assertEqual(len(FLOWS["fix"]["fases"]), 3)

    def test_quick_flow_has_2_phases(self):
        self.assertEqual(len(FLOWS["quick"]["fases"]), 2)

    def test_all_flows_defined(self):
        expected = {"feature", "fix", "quick", "spike", "ship", "audit"}
        self.assertEqual(set(FLOWS.keys()), expected)

    def test_architecture_gate_is_usuario_seguridad(self):
        """La fase de arquitectura debe tener gate usuario+seguridad."""
        fase_arq = FLOWS["feature"]["fases"][2]
        self.assertEqual(fase_arq["nombre"], "arquitectura")
        self.assertEqual(fase_arq["gate_tipo"], "usuario+seguridad")

    def test_optional_integrations_cover_known_optional_agents(self):
        self.assertEqual(set(OPTIONAL_INTEGRATIONS.keys()), _KNOWN_OPTIONAL_AGENTS)


class TestSession(unittest.TestCase):
    def test_create_session(self):
        session = create_session("feature", "Sistema de autenticación")
        self.assertEqual(session["comando"], "feature")
        self.assertEqual(session["fase_actual"], "producto")
        self.assertEqual(session["fase_numero"], 0)
        self.assertEqual(len(session["fases_completadas"]), 0)

    def test_save_and_load_state(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            session = create_session("fix", "Bug en login")
            save_state(session, state_path)
            loaded = load_state(state_path)
            self.assertEqual(loaded["comando"], "fix")
            self.assertEqual(loaded["descripcion"], "Bug en login")
        finally:
            os.unlink(state_path)

    def test_create_quick_session(self):
        session = create_session("quick", "Ajuste pequeño en login")
        self.assertEqual(session["comando"], "quick")
        self.assertEqual(session["fase_actual"], "ejecucion_acotada")
        self.assertEqual(session["fase_numero"], 0)

    def test_create_session_accepts_optional_stack(self):
        session = create_session(
            "feature",
            "Sistema de autenticación",
            stack={"runtime": "python", "framework": "fastapi"},
        )
        self.assertEqual(session["stack"]["framework"], "fastapi")

    def test_save_state_syncs_active_session_to_kanban(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Sistema de autenticación")

            save_state(session, state_path)

            loaded = load_state(state_path)
            board = load_kanban_board(tmpdir)

        self.assertTrue(loaded["kanban_task_id"].startswith("T-"))
        self.assertTrue(loaded["kanban_verify_task_id"].startswith("T-"))
        self.assertTrue(any(task["id"] == loaded["kanban_task_id"] for task in board["in-progress"]))
        self.assertTrue(any(task["id"] == loaded["kanban_verify_task_id"] for task in board["backlog"]))

    def test_save_state_assigns_task_types_to_runtime_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Sistema de autenticación")

            save_state(session, state_path)

            loaded = load_state(state_path)
            board = load_kanban_board(tmpdir)

        main_task = next(task for task in board["in-progress"] if task["id"] == loaded["kanban_task_id"])
        verify_task = next(task for task in board["backlog"] if task["id"] == loaded["kanban_verify_task_id"])
        producto_task = next(task for task in board["in-progress"] if task["title"].startswith("feature:producto"))
        self.assertEqual(main_task["task_type"], "main")
        self.assertEqual(verify_task["task_type"], "verify")
        self.assertEqual(producto_task["task_type"], "phase")

    def test_save_state_syncs_completed_session_to_done_and_keeps_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("fix", "Bug en login")
            save_state(session, state_path)
            while session["fase_actual"] != "completado":
                session = advance_phase(session, resultado="aprobado", artefactos=[])

            save_state(session, state_path)

            loaded = load_state(state_path)
            board = load_kanban_board(tmpdir)

        self.assertTrue(any(task["id"] == loaded["kanban_task_id"] for task in board["done"]))
        self.assertFalse(any(task["id"] == loaded["kanban_task_id"] for task in board["in-progress"]))
        self.assertTrue(any(task["id"] == loaded["kanban_verify_task_id"] for task in board["backlog"]))

    def test_save_state_respects_rejected_uat_and_blocks_main_task(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Checkout")
            save_state(session, state_path)
            while session["fase_actual"] != "completado":
                session = advance_phase(session, resultado="aprobado", artefactos=[])
            save_state(session, state_path)

            loaded = load_state(state_path)
            write_uat_files(tmpdir, raw_request="rechazado smoke roto")
            save_state(loaded, state_path)

            reloaded = load_state(state_path)
            board = load_kanban_board(tmpdir)

        self.assertTrue(any(task["id"] == reloaded["kanban_task_id"] for task in board["blocked"]))
        self.assertFalse(any(task["id"] == reloaded.get("kanban_verify_task_id", "") for task in board["backlog"]))

    def test_save_state_creates_phase_tasks_for_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("fix", "Bug en login")

            save_state(session, state_path)

            loaded = load_state(state_path)
            board = load_kanban_board(tmpdir)

        self.assertEqual(set(loaded["kanban_phase_task_ids"].keys()), {"diagnostico", "correccion", "validacion"})
        self.assertTrue(any(task["title"].startswith("fix:diagnostico") for task in board["in-progress"]))
        self.assertTrue(any(task["title"].startswith("fix:correccion") for task in board["backlog"]))
        self.assertTrue(any(task["title"].startswith("fix:validacion") for task in board["backlog"]))

    def test_save_state_updates_phase_tasks_when_advancing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("fix", "Bug en login")
            save_state(session, state_path)
            session = load_state(state_path)
            session = advance_phase(session, resultado="aprobado", artefactos=["docs/diag.md"])

            save_state(session, state_path)

            board = load_kanban_board(tmpdir)

        diagnostico = next(task for task in board["done"] if task["title"].startswith("fix:diagnostico"))
        self.assertIn("resultado 'aprobado'", diagnostico["notes"])
        self.assertIn("Artefactos:", diagnostico["body"])
        self.assertIn("docs/diag.md", diagnostico["body"])
        self.assertTrue(any(task["title"].startswith("fix:correccion") for task in board["in-progress"]))

    def test_save_state_generates_operational_docs_automatically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Sistema de autenticación")

            save_state(session, state_path)

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()
            loaded = load_state(state_path)

        self.assertIn("Flujo: `feature`.", current)
        self.assertIn("Siguiente comando recomendado: /alfred-dev:resume", current)
        self.assertIn("Gate pendiente: `usuario`.", current)
        self.assertIn("Fases completadas: 0/7.", progress)
        self.assertIn("Kanban visible:", progress)
        self.assertIn("## Fases del flujo", progress)
        self.assertIn("`producto` -> `en curso` · gate `usuario`", progress)
        self.assertIn("Gate pendiente:", traceability)
        self.assertIn("Riesgo principal:", traceability)
        self.assertIn("## Criterios y evidencia por fase", traceability)
        self.assertIn("### `producto`", traceability)
        self.assertIn(
            "Criterios visibles: Análisis de requisitos y definición del alcance funcional de la nueva característica; Cerrar la gate `usuario` sin bloqueos abiertos.",
            traceability,
        )
        self.assertIn("## Verificación manual", traceability)
        self.assertIn(CURRENT_RELATIVE_PATH, loaded["artefactos"])
        self.assertIn(PROGRESS_MD_RELATIVE_PATH, loaded["artefactos"])
        self.assertIn(TRACEABILITY_MD_RELATIVE_PATH, loaded["artefactos"])

    def test_save_state_updates_operational_docs_after_completion_and_uat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("quick", "Ajuste pequeño en login")
            save_state(session, state_path)
            while session["fase_actual"] != "completado":
                session = advance_phase(session, resultado="aprobado", artefactos=["docs/cambio.md"])
            save_state(session, state_path)
            write_uat_files(tmpdir, raw_request="aprobado smoke manual correcto")

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()
            loaded = load_state(state_path)

        self.assertIn("Estado: completado y verificado.", current)
        self.assertIn("Siguiente comando recomendado: /alfred", current)
        self.assertIn("Verificación/UAT: aprobada.", progress)
        self.assertIn("Artefactos acumulados: 6.", progress)
        self.assertIn("## Fases del flujo", progress)
        self.assertIn("`ejecucion_acotada` -> `aprobado`", progress)
        self.assertIn("UAT actual: aprobada.", traceability)
        self.assertIn("## Verificación manual", traceability)
        self.assertIn("Estado de verify: `done`.", traceability)
        self.assertIn("docs/cambio.md", traceability)
        self.assertIn(UAT_MD_RELATIVE_PATH, traceability)
        self.assertIn(UAT_MD_RELATIVE_PATH, loaded["artefactos"])
        self.assertIn(UAT_JSON_RELATIVE_PATH, loaded["artefactos"])

    def test_save_state_operational_docs_show_active_optional_agents_for_phase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Checkout nuevo")
            session["fase_actual"] = "calidad"
            session["fase_numero"] = 4
            session["equipo_sesion"] = {
                "opcionales_activos": {
                    "lucius": True,
                },
                "infra": {
                    "memoria": False,
                    "gui": False,
                },
                "fuente": "composicion_dinamica",
            }

            save_state(session, state_path)

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertIn(
            "Especialistas opcionales activos: secuencial: `lucius`.",
            current,
        )
        self.assertIn(
            "`calidad` -> `en curso` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_save_state_operational_docs_show_release_optionals_for_ship(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("ship", "Release 1.2.0")
            session["equipo_sesion"] = {
                "opcionales_activos": {
                    "lucius": True,
                },
                "infra": {
                    "memoria": False,
                    "gui": False,
                },
                "fuente": "composicion_dinamica",
            }

            expectations = [
                ("auditoria_final", 0, "secuencial: `lucius`"),
            ]

            for phase_name, phase_number, expected_summary in expectations:
                session["fase_actual"] = phase_name
                session["fase_numero"] = phase_number
                save_state(session, state_path)

                with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                    current = fh.read()
                with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                    progress = fh.read()
                with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                    traceability = fh.read()

                self.assertIn(expected_summary, current)
                self.assertIn(expected_summary, progress)
                if "paralelo" in expected_summary:
                    self.assertIn(
                        f"- Opcionales en paralelo: `{expected_summary.split('`')[1]}`.",
                        traceability,
                    )
                else:
                    self.assertIn(
                        f"- Opcionales secuenciales: `{expected_summary.split('`')[1]}`.",
                        traceability,
                    )

    def test_feature_flow_uses_persisted_optional_agents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "name": "demo",
                        "dependencies": {
                            "react": "^19.0.0",
                            "express": "^5.0.0",
                        },
                    },
                    fh,
                )
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("feature", "Checkout nuevo", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn(
            "`calidad` -> `pendiente` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_fix_flow_uses_persisted_optional_agents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("fix", "Regresión en checkout", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn(
            "`validacion` -> `pendiente` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_ship_flow_uses_persisted_optional_agents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("ship", "Release 2.0.0", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn("Especialistas opcionales activos: secuencial: `lucius`.", current)
        self.assertIn(
            "`auditoria_final` -> `en curso` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_quick_flow_uses_persisted_optional_agents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("quick", "Ajuste fino", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn(
            "`validacion_rapida` -> `pendiente` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_audit_flow_uses_persisted_optional_agents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("audit", "Auditoría anual", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn("Especialistas opcionales activos: secuencial: `lucius`.", current)
        self.assertIn(
            "`auditoria_paralela` -> `en curso` · gate `automatico+seguridad` · opcionales secuencial: `lucius`",
            progress,
        )
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_spike_flow_marks_persisted_optionals_as_on_demand_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _save_project_config_with_optionals(
                tmpdir,
                ["lucius"],
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            session = run_flow("spike", "Evaluar Bun para jobs", project_dir=tmpdir)
            save_state(session, state_path)

            persisted = load_state(state_path)
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertEqual(persisted["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(persisted["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(persisted["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("- Origen del equipo runtime: configuración persistida.", current)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", progress)
        self.assertIn("- Origen del equipo runtime: configuración persistida.", traceability)
        self.assertIn(
            "- Opcionales activos solo bajo demanda en este flujo: `lucius`.",
            current,
        )
        self.assertIn(
            "- Opcionales activos solo bajo demanda en este flujo: `lucius`.",
            progress,
        )
        self.assertIn(
            "- Opcionales activos solo bajo demanda en este flujo: `lucius`.",
            traceability,
        )
        self.assertIn("`exploracion` -> `en curso` · gate `libre`", progress)
        self.assertIn("`conclusiones` -> `pendiente` · gate `usuario`", progress)

    def test_save_state_operational_docs_show_lucius_for_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("audit", "Auditoría anual")
            session["fase_actual"] = "auditoria_paralela"
            session["fase_numero"] = 0
            session["equipo_sesion"] = {
                "opcionales_activos": {
                    "lucius": True,
                },
                "infra": {
                    "memoria": False,
                    "gui": False,
                },
                "fuente": "composicion_dinamica",
            }

            save_state(session, state_path)

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertIn("Especialistas opcionales activos: secuencial: `lucius`.", current)
        self.assertIn("secuencial: `lucius`", progress)
        self.assertIn("- Opcionales secuenciales: `lucius`.", traceability)

    def test_save_state_marks_skipped_phase_task_as_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session(
                "feature",
                "Sistema de autenticación",
                stack={"runtime": "python", "framework": "fastapi"},
            )
            save_state(session, state_path)
            session = load_state(state_path)
            session = advance_phase(session, resultado="aprobado", artefactos=[])

            save_state(session, state_path)

            board = load_kanban_board(tmpdir)

        producto = next(task for task in board["done"] if task["title"].startswith("feature:producto"))
        estilo = next(task for task in board["done"] if task["title"].startswith("feature:estilo_visual"))
        self.assertIn("resultado 'aprobado'", producto["notes"])
        self.assertIn("saltada", estilo["notes"])
        self.assertIn("Gate: usuario", producto["body"])
        self.assertIn("Estado de fase: saltada", estilo["body"])
        self.assertTrue(any(task["title"].startswith("feature:arquitectura") for task in board["in-progress"]))

    def test_ship_empaquetado_has_no_optional_agents(self):
        effective = get_effective_agents(
            "empaquetado",
            {"lucius": True},
        )
        self.assertEqual(effective["paralelo"], [])
        self.assertEqual(effective["secuencial"], [])

    def test_ship_empaquetado_gate_is_automatico_seguridad(self):
        empaquetado = FLOWS["ship"]["fases"][2]
        self.assertEqual(empaquetado["nombre"], "empaquetado")
        self.assertEqual(empaquetado["gate_tipo"], "automatico+seguridad")

    def test_save_state_phase_task_body_includes_gate_and_iterations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")
            session = create_session("feature", "Sistema de autenticación")
            session["iteraciones_fase"] = 2
            session = advance_phase(session, resultado="aprobado", artefactos=["docs/producto.md"])

            save_state(session, state_path)

            board = load_kanban_board(tmpdir)

        producto = next(task for task in board["done"] if task["title"].startswith("feature:producto"))
        self.assertIn("Gate: usuario", producto["body"])
        self.assertIn("Iteraciones internas: 2", producto["body"])
        self.assertIn("docs/producto.md", producto["body"])

    def test_save_state_enriches_estilo_visual_with_artifact_and_choice_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "docs"), exist_ok=True)
            os.makedirs(
                os.path.join(tmpdir, ".alfred-dev", "visual", "session-1", "state"),
                exist_ok=True,
            )
            state_path = os.path.join(tmpdir, ".claude", "alfred-dev-state.json")

            with open(os.path.join(tmpdir, "docs", "style-direction.md"), "w", encoding="utf-8") as fh:
                fh.write("# Direccion de estilo\n")
            with open(
                os.path.join(tmpdir, ".alfred-dev", "visual", "session-1", "state", "events"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    '{"type":"click","choice":"B","label":"Editorial cálido","ts":"2026-04-07T10:00:02Z"}\n'
                )

            session = create_session("feature", "Sistema de autenticación")
            session = advance_phase(session, resultado="aprobado", artefactos=["docs/producto.md"])
            session = advance_phase(session, resultado="aprobado", artefactos=[])

            save_state(session, state_path)

            persisted = load_state(state_path)
            board = load_kanban_board(tmpdir)

        estilo_phase = next(
            phase for phase in persisted["fases_completadas"] if phase["nombre"] == "estilo_visual"
        )
        self.assertIn("docs/style-direction.md", estilo_phase["artefactos"])
        self.assertIn("docs/style-direction.md", persisted["artefactos"])

        estilo_task = next(task for task in board["done"] if task["title"].startswith("feature:estilo_visual"))
        self.assertIn("docs/style-direction.md", estilo_task["body"])
        self.assertIn("Editorial cálido", estilo_task["notes"])
        self.assertIn("Elección visual", estilo_task["evidence"])


class TestGates(unittest.TestCase):
    def test_gate_passes_with_correct_result(self):
        session = create_session("feature", "Test feature")
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"])

    def test_gate_fails_with_incorrect_result(self):
        session = create_session("feature", "Test feature")
        result = check_gate(session, resultado="rechazado")
        self.assertFalse(result["passed"])

    def test_automatic_gate_fails_when_tests_fail(self):
        """Las gates automáticas bloquean si los tests no pasan."""
        session = create_session("feature", "Test")
        # Avanzar a fase de desarrollo (gate automática)
        session = advance_phase(session)  # producto -> estilo_visual
        session = advance_phase(session)  # estilo_visual -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        result = check_gate(session, resultado="aprobado", tests_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("tests", result["reason"].lower())

    def test_automatic_gate_passes_when_tests_ok(self):
        """Las gates automáticas dejan pasar si tests y resultado OK."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto -> estilo_visual
        session = advance_phase(session)  # estilo_visual -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        result = check_gate(session, resultado="aprobado", tests_ok=True)
        self.assertTrue(result["passed"])

    def test_security_gate_fails_when_security_fails(self):
        """Las gates con seguridad bloquean si security_ok es False."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto -> estilo_visual
        session = advance_phase(session)  # estilo_visual -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        session = advance_phase(session)  # desarrollo -> calidad
        # Fase de calidad: gate automático+seguridad
        result = check_gate(session, resultado="aprobado", security_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("seguridad", result["reason"].lower())

    def test_advance_phase_propagates_tests_ok(self):
        """advance_phase propaga tests_ok a check_gate."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto -> estilo_visual
        session = advance_phase(session)  # estilo_visual -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        # Intentar avanzar desarrollo con tests rojos
        with self.assertRaises(RuntimeError):
            advance_phase(session, resultado="aprobado", tests_ok=False)


class TestAdvancePhase(unittest.TestCase):
    def test_advance_moves_to_next_phase(self):
        session = create_session("feature", "Test")
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        self.assertEqual(session["fase_actual"], "estilo_visual")
        self.assertEqual(session["fase_numero"], 1)
        self.assertEqual(len(session["fases_completadas"]), 1)

    def test_cannot_advance_past_last_phase(self):
        session = create_session("spike", "Investigación")
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        self.assertEqual(session["fase_actual"], "completado")


# --- Fixture compartida para equipo_sesion ---
# Representa un equipo de sesión válido con composición dinámica.
# Se usa como referencia en los tests de validación y run_flow.
VALID_EQUIPO_SESION = {
    "opcionales_activos": {
        "lucius": True,
    },
    "infra": {
        "memoria": True,
        "gui": False,
    },
    "fuente": "composicion_dinamica",
}


class TestValidateEquipoSesion(unittest.TestCase):
    """Validación de la estructura del equipo de sesión."""

    def test_tc20_dict_valido_completo(self):
        """TC-20: un dict válido completo devuelve True."""
        self.assertTrue(_validate_equipo_sesion(VALID_EQUIPO_SESION))

    def test_tc21_dict_vacio(self):
        """TC-21: un dict vacío devuelve False."""
        self.assertFalse(_validate_equipo_sesion({}))

    def test_tc22_agente_extra_en_opcionales_acepta_con_aviso(self):
        """TC-22: un agente extra se acepta (True) pero emite aviso a stderr."""
        import copy
        import io
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        malo["opcionales_activos"]["agente-inventado"] = True
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            result = _validate_equipo_sesion(malo)
        finally:
            sys.stderr = old_stderr
        self.assertTrue(result)
        self.assertIn("agente-inventado", captured.getvalue())

    def test_tc22b_agente_faltante_en_opcionales_falla(self):
        """TC-22b: si falta un agente conocido, devuelve False."""
        import copy
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        del malo["opcionales_activos"]["lucius"]
        self.assertFalse(_validate_equipo_sesion(malo))

    def test_tc23_valor_no_bool_en_opcionales(self):
        """TC-23: un valor no booleano en opcionales devuelve False."""
        import copy
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        malo["opcionales_activos"]["lucius"] = "si"
        self.assertFalse(_validate_equipo_sesion(malo))

    def test_tc23b_fuente_persistida_tambien_es_valida(self):
        """TC-23b: la config persistida usa el mismo contrato runtime."""
        import copy
        persisted = copy.deepcopy(VALID_EQUIPO_SESION)
        persisted["fuente"] = "config_persistida"
        self.assertTrue(_validate_equipo_sesion(persisted))


class TestRunFlow(unittest.TestCase):
    """Tests para la función run_flow de creación de sesión con equipo."""

    def test_tc15_sin_equipo_sesion(self):
        """TC-15: run_flow sin equipo_sesion crea sesión con equipo_sesion=None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = run_flow("feature", "Nueva funcionalidad", project_dir=tmpdir)
        self.assertIn("equipo_sesion", session)
        self.assertIsNone(session["equipo_sesion"])
        self.assertIsNone(session["equipo_sesion_error"])

    def test_tc16_con_equipo_sesion_valido(self):
        """TC-16: run_flow con equipo_sesion válido lo inyecta en la sesión."""
        session = run_flow("feature", "Nueva funcionalidad", equipo_sesion=VALID_EQUIPO_SESION)
        self.assertEqual(session["equipo_sesion"], VALID_EQUIPO_SESION)
        self.assertIsNone(session["equipo_sesion_error"])

    def test_tc17_equipo_sesion_invalido_cae_a_none_con_error(self):
        """TC-17: run_flow con equipo_sesion inválido cae a None y registra motivo."""
        import io
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                session = run_flow(
                    "feature",
                    "Test",
                    equipo_sesion={"malo": True},
                    project_dir=tmpdir,
                )
        finally:
            sys.stderr = old_stderr
        self.assertIsNone(session["equipo_sesion"])
        self.assertIn("Alfred Dev", captured.getvalue())
        # Verifica que el motivo del descarte se registra en la sesión
        self.assertIsNotNone(session["equipo_sesion_error"])
        self.assertIn("no pasó la validación", session["equipo_sesion_error"])

    def test_tc18_comando_desconocido_lanza_valueerror(self):
        """TC-18: run_flow con comando desconocido lanza ValueError."""
        with self.assertRaises(ValueError):
            run_flow("inventado", "No existe")

    def test_tc19_integracion_extremo_a_extremo(self):
        """TC-19: run_flow -> extraer opcionales -> get_effective_agents."""
        session = run_flow("feature", "Nuevo módulo", equipo_sesion=VALID_EQUIPO_SESION)
        opcionales = session["equipo_sesion"]["opcionales_activos"]
        arquitectura = get_effective_agents("arquitectura", opcionales)
        calidad = get_effective_agents("calidad", opcionales)
        self.assertEqual(arquitectura["paralelo"], [])
        self.assertEqual(arquitectura["secuencial"], [])
        self.assertIn("lucius", calidad["secuencial"])

    def test_tc24_retrocompatibilidad_get_effective_agents_con_none(self):
        """TC-24: get_effective_agents(fase, None) sigue funcionando."""
        result = get_effective_agents("calidad", None)
        self.assertEqual(result, {"paralelo": [], "secuencial": []})

    def test_run_flow_detects_stack_and_injects_it_into_session(self):
        with patch(
            "core.config_loader.detect_stack",
            return_value={"runtime": "python", "framework": "fastapi", "lenguaje": "python"},
        ):
            session = run_flow("feature", "API backend")
        self.assertEqual(session["stack"]["framework"], "fastapi")

    def test_run_flow_skips_estilo_visual_when_detected_stack_has_no_frontend(self):
        with patch(
            "core.config_loader.detect_stack",
            return_value={"runtime": "python", "framework": "fastapi", "lenguaje": "python"},
        ):
            session = run_flow("feature", "API backend")

        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "arquitectura")
        skipped = [f for f in session["fases_completadas"] if f["nombre"] == "estilo_visual"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["resultado"], "saltada")

    def test_run_flow_uses_persisted_project_config_when_no_ephemeral_team_is_passed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "agentes_opcionales:\n"
                    "  lucius: true\n"
                    "memoria:\n"
                    "  enabled: true\n"
                    "---\n"
                )

            session = run_flow(
                "ship",
                "Release 2.0.0",
                project_dir=tmpdir,
            )

        self.assertIsNotNone(session["equipo_sesion"])
        self.assertEqual(session["equipo_sesion"]["fuente"], "config_persistida")
        self.assertEqual(set(session["equipo_sesion"]["opcionales_activos"]), {"lucius"})
        self.assertTrue(session["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertTrue(session["equipo_sesion"]["infra"]["memoria"])

    def test_run_flow_invalid_ephemeral_team_falls_back_to_persisted_project_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "agentes_opcionales:\n"
                    "  lucius: true\n"
                    "---\n"
                )

            session = run_flow(
                "ship",
                "Release 2.1.0",
                equipo_sesion={"malo": True},
                project_dir=tmpdir,
            )

        self.assertEqual(session["equipo_sesion"]["fuente"], "config_persistida")
        self.assertTrue(session["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIsNotNone(session["equipo_sesion_error"])
        self.assertIn("Se aplicó la configuración persistida", session["equipo_sesion_error"])

    def test_quick_flow_uses_optional_agents_on_light_phases(self):
        """quick integra Lucius solo en la validación rápida."""
        opcionales = {
            **VALID_EQUIPO_SESION["opcionales_activos"],
            "lucius": True,
        }
        ejecucion = get_effective_agents("ejecucion_acotada", opcionales)
        validacion = get_effective_agents("validacion_rapida", opcionales)
        self.assertEqual(ejecucion["paralelo"], [])
        self.assertEqual(ejecucion["secuencial"], [])
        self.assertIn("lucius", validacion["secuencial"])

    def test_fix_flow_uses_optional_agents_on_bug_phases(self):
        """fix integra Lucius solo en validacion."""
        opcionales = {
            **VALID_EQUIPO_SESION["opcionales_activos"],
            "lucius": True,
        }
        diagnostico = get_effective_agents("diagnostico", opcionales)
        correccion = get_effective_agents("correccion", opcionales)
        validacion = get_effective_agents("validacion", opcionales)

        self.assertEqual(diagnostico["paralelo"], [])
        self.assertEqual(diagnostico["secuencial"], [])
        self.assertEqual(correccion["paralelo"], [])
        self.assertEqual(correccion["secuencial"], [])
        self.assertIn("lucius", validacion["secuencial"])

    def test_unknown_optional_flags_are_ignored_by_effective_agents(self):
        """Los opcionales recortados no reaparecen aunque vengan en el estado."""
        opcionales = {
            "lucius": True,
            "copywriter": True,
            "github-manager": True,
        }
        calidad = get_effective_agents("calidad", opcionales)
        documentacion = get_effective_agents("documentacion", opcionales)
        empaquetado = get_effective_agents("empaquetado", opcionales)
        self.assertEqual(calidad["secuencial"], ["lucius"])
        self.assertEqual(documentacion["paralelo"], [])
        self.assertEqual(empaquetado["secuencial"], [])

    def test_lucius_runs_as_external_audit_in_quality_closures(self):
        """Lucius se integra al cierre como auditoría secuencial externa."""
        opcionales = {
            **VALID_EQUIPO_SESION["opcionales_activos"],
            "lucius": True,
        }
        calidad = get_effective_agents("calidad", opcionales)
        auditoria = get_effective_agents("auditoria_final", opcionales)
        self.assertIn("lucius", calidad["secuencial"])
        self.assertIn("lucius", auditoria["secuencial"])

    def test_ship_and_audit_use_release_optional_agents(self):
        """ship y audit integran Lucius en las fases de auditoria."""
        opcionales = {
            **VALID_EQUIPO_SESION["opcionales_activos"],
            "lucius": True,
        }
        auditoria_final = get_effective_agents("auditoria_final", opcionales)
        documentacion = get_effective_agents("documentacion", opcionales)
        empaquetado = get_effective_agents("empaquetado", opcionales)
        despliegue = get_effective_agents("despliegue", opcionales)
        auditoria_paralela = get_effective_agents("auditoria_paralela", opcionales)

        self.assertIn("lucius", auditoria_final["secuencial"])
        self.assertEqual(documentacion["paralelo"], [])
        self.assertEqual(empaquetado["secuencial"], [])
        self.assertEqual(despliegue["secuencial"], [])
        self.assertIn("lucius", auditoria_paralela["secuencial"])


class TestLoopIterativo(unittest.TestCase):
    """Tests para el loop iterativo dentro de fases (v0.4.0)."""

    def test_should_retry_when_gate_fails(self):
        """Si la gate falla y hay iteraciones, recomienda retry."""
        session = create_session("feature", "Test loop")
        # Fase 0 = producto, gate_tipo = usuario
        result = should_retry_phase(session, resultado="rechazado")
        self.assertEqual(result["action"], "retry")
        self.assertEqual(result["iteration"], 1)

    def test_should_advance_when_gate_passes(self):
        """Si la gate se supera, recomienda avanzar."""
        session = create_session("feature", "Test loop")
        result = should_retry_phase(session, resultado="aprobado")
        self.assertEqual(result["action"], "advance")

    def test_should_escalate_after_max_iterations(self):
        """Al agotar iteraciones, recomienda escalar al usuario."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = MAX_PHASE_ITERATIONS
        result = should_retry_phase(session, resultado="rechazado")
        self.assertEqual(result["action"], "escalate")

    def test_iteration_counter_increments(self):
        """El contador de iteraciones se incrementa con cada retry."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 0
        should_retry_phase(session, resultado="rechazado")
        self.assertEqual(session["iteraciones_fase"], 1)
        should_retry_phase(session, resultado="rechazado")
        self.assertEqual(session["iteraciones_fase"], 2)

    def test_reset_phase_iterations(self):
        """El reset pone el contador a 0."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 3
        reset_phase_iterations(session)
        self.assertEqual(session["iteraciones_fase"], 0)

    def test_advance_phase_resets_iterations(self):
        """Avanzar de fase reinicia el contador automaticamente."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 3
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session.get("iteraciones_fase", 0), 0)

    def test_advance_phase_preserves_iterations(self):
        """advance_phase guarda el contador de iteraciones en la fase completada."""
        session = create_session("feature", "Test iteraciones")
        session["iteraciones_fase"] = 3
        session = advance_phase(session, resultado="aprobado")
        fase_completada = session["fases_completadas"][-1]
        self.assertEqual(fase_completada["iteraciones"], 3)

    def test_should_retry_invalid_session_state_escalates_instead_of_retrying(self):
        session = create_session("feature", "Test loop")
        session["fase_numero"] = -1
        result = should_retry_phase(session, resultado="rechazado")
        self.assertEqual(result["action"], "escalate")
        self.assertIn("inválido", result["reason"])


class TestAutopilot(unittest.TestCase):
    """Tests para el modo autopilot (v0.4.0)."""

    def test_run_flow_autopilot_creates_session(self):
        """El modo autopilot crea una sesion con el flag activo."""
        session = run_flow_autopilot("feature", "Login automatico")
        self.assertTrue(session["autopilot"])

    def test_run_flow_autopilot_uses_persisted_project_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "agentes_opcionales:\n"
                    "  lucius: true\n"
                    "---\n"
                )

            session = run_flow_autopilot("ship", "Release automática", project_dir=tmpdir)

        self.assertTrue(session["autopilot"])
        self.assertEqual(session["equipo_sesion"]["fuente"], "config_persistida")
        self.assertTrue(session["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertEqual(session["iteraciones_fase"], 0)
        self.assertEqual(session["max_iteraciones_fase"], MAX_PHASE_ITERATIONS)

    def test_autopilot_approves_user_gates(self):
        """En autopilot, las gates de usuario se aprueban automaticamente."""
        session = create_session("feature", "Test autopilot")
        # Fase 0 = producto, gate_tipo = usuario
        result = is_autopilot_gate_passable(session)
        self.assertTrue(result["passed"])
        self.assertIn("autopilot", result["reason"])

    def test_autopilot_evaluates_automatic_gates(self):
        """En autopilot, las gates automaticas se evaluan normalmente."""
        session = create_session("feature", "Test autopilot")
        # Avanzar a fase 3 = desarrollo, gate_tipo = automatico
        session = advance_phase(session, resultado="aprobado")  # producto -> estilo_visual
        session = advance_phase(session, resultado="aprobado")  # estilo_visual -> arquitectura
        session = advance_phase(session, resultado="aprobado")  # arquitectura -> desarrollo
        result = is_autopilot_gate_passable(session, tests_ok=False)
        self.assertFalse(result["passed"])

    def test_autopilot_evaluates_security_gates(self):
        """En autopilot, las gates de seguridad se evaluan normalmente."""
        session = create_session("feature", "Test autopilot")
        session = advance_phase(session, resultado="aprobado")  # producto -> estilo_visual
        session = advance_phase(session, resultado="aprobado")  # estilo_visual -> arquitectura
        session = advance_phase(session, resultado="aprobado")  # arquitectura -> desarrollo
        session = advance_phase(session, resultado="aprobado", tests_ok=True)  # desarrollo -> calidad
        # Fase 4 = calidad, gate_tipo = automatico+seguridad
        result = is_autopilot_gate_passable(session, security_ok=False)
        self.assertFalse(result["passed"])

    def test_autopilot_invalid_command(self):
        """Autopilot con comando invalido lanza ValueError."""
        with self.assertRaises(ValueError):
            run_flow_autopilot("inexistente", "Test")

    def test_autopilot_gate_completed_session(self):
        """is_autopilot_gate_passable no falla con sesion completada."""
        session = create_session("spike", "Test")
        session = advance_phase(session, resultado="aprobado")
        session = advance_phase(session, resultado="aprobado")
        # Ahora fase_actual == "completado"
        result = is_autopilot_gate_passable(session)
        self.assertTrue(result["passed"])

    def test_autopilot_usuario_seguridad_auto_approves_user_part(self):
        """En autopilot, GATE_USUARIO_SEGURIDAD aprueba la parte de usuario
        pero evalua la de seguridad. Test de documentacion del comportamiento."""
        session = create_session("feature", "Test autopilot")
        session = advance_phase(session, resultado="aprobado")  # producto -> estilo_visual
        session = advance_phase(session, resultado="aprobado")  # estilo_visual -> arquitectura
        # Ahora en fase arquitectura con gate GATE_USUARIO_SEGURIDAD
        # Con seguridad OK: debe pasar
        result = is_autopilot_gate_passable(session, security_ok=True)
        self.assertTrue(result["passed"])
        # Con seguridad KO: debe fallar
        result = is_autopilot_gate_passable(session, security_ok=False)
        self.assertFalse(result["passed"])

    def test_autopilot_ship_deploy_keeps_user_confirmation_mandatory(self):
        session = create_session("ship", "Release autopilot")
        session = advance_phase(session, resultado="aprobado", tests_ok=True, security_ok=True)
        session = advance_phase(session, resultado="aprobado")
        session = advance_phase(session, resultado="aprobado", tests_ok=True, security_ok=True)

        self.assertEqual(session["fase_actual"], "despliegue")
        result = is_autopilot_gate_passable(session, security_ok=True)
        self.assertFalse(result["passed"])
        self.assertIn("confirmación explícita del usuario", result["reason"])


class TestCompletedSessionGuards(unittest.TestCase):
    """Verifica que check_gate no lanza IndexError con sesiones completadas."""

    def test_check_gate_completed_session(self):
        """check_gate devuelve passed=True para sesiones completadas."""
        session = create_session("spike", "Investigacion")
        session = advance_phase(session, resultado="aprobado")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "completado")
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"])

    def test_check_gate_overflowed_fase_numero(self):
        """Un índice fuera de rango debe rechazarse como estado inválido."""
        session = create_session("spike", "Test")
        session["fase_numero"] = 999
        result = check_gate(session, resultado="aprobado")
        self.assertFalse(result["passed"])
        self.assertIn("fuera de rango", result["reason"])

    def test_check_gate_negative_fase_numero_is_invalid(self):
        session = create_session("feature", "Test")
        session["fase_numero"] = -1
        result = check_gate(session, resultado="aprobado")
        self.assertFalse(result["passed"])
        self.assertIn("negativo", result["reason"])

    def test_advance_phase_rejects_invalid_phase_index(self):
        session = create_session("feature", "Test")
        session["fase_numero"] = -1
        with self.assertRaises(RuntimeError):
            advance_phase(session, resultado="aprobado")


class TestLoadStateValidation(unittest.TestCase):
    def test_load_state_rejects_negative_phase_index(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "comando": "feature",
                        "fase_actual": "producto",
                        "fase_numero": -1,
                    },
                    fh,
                )
            self.assertIsNone(load_state(state_path))
        finally:
            os.unlink(state_path)

    def test_load_state_rejects_phase_name_mismatch(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "comando": "feature",
                        "fase_actual": "producto",
                        "fase_numero": 3,
                    },
                    fh,
                )
            self.assertIsNone(load_state(state_path))
        finally:
            os.unlink(state_path)

    def test_load_state_accepts_coherent_completed_session(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "comando": "spike",
                        "fase_actual": "completado",
                        "fase_numero": len(FLOWS["spike"]["fases"]),
                    },
                    fh,
                )
            loaded = load_state(state_path)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["fase_actual"], "completado")
        finally:
            os.unlink(state_path)


if __name__ == "__main__":
    unittest.main()
