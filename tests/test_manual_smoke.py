#!/usr/bin/env python3
"""Tests del runner de smoke manual humano."""

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(ROOT, "scripts", "manual_smoke.py")


def _load_manual_smoke_module():
    spec = importlib.util.spec_from_file_location("manual_smoke", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def _mock_claude_cli_available(manual_smoke):
    original_which = manual_smoke.shutil.which

    def fake_which(name):
        if name == "claude":
            return "/usr/local/bin/claude"
        return original_which(name)

    try:
        manual_smoke.shutil.which = fake_which
        yield
    finally:
        manual_smoke.shutil.which = original_which


class TestManualSmokeRunner(unittest.TestCase):
    def test_manual_matrix_cases_are_unique_and_cover_release_doc_prompts(self):
        manual_smoke = _load_manual_smoke_module()

        case_ids = [case.case_id for case in manual_smoke.CASES]
        prompts = "\n".join(case.prompt for case in manual_smoke.CASES)

        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertGreaterEqual(len(case_ids), 36)
        self.assertIn("/alfred-dev:alfred", prompts)
        self.assertIn("/alfred-dev:ajustes", prompts)
        self.assertIn("/alfred-dev:feature sistema de login con email y password", prompts)
        self.assertIn("/alfred-dev:quick cambia el texto del CTA", prompts)
        self.assertIn("/alfred-dev:fix el login falla con password correcta", prompts)
        self.assertIn("/alfred-dev:spike compara SQLite y Postgres", prompts)
        self.assertIn("/alfred-dev:audit", prompts)
        self.assertIn("/alfred-dev:uat aprobado por usuario", prompts)
        self.assertIn("/alfred-dev:uat rechazado falta revisar copy", prompts)
        self.assertIn("/alfred-dev:uat pendiente esperando validacion de negocio", prompts)
        self.assertIn("/alfred-dev:lucius src/ --scope security", prompts)
        self.assertIn("/alfred-dev:lucius --scope architecture", prompts)
        self.assertIn("/alfred-dev:lucius --scope performance", prompts)
        self.assertIn("/alfred-dev:lucius --scope bananas", prompts)
        self.assertIn("/alfred-dev:uat", prompts)

    def test_manual_matrix_covers_every_public_command(self):
        manual_smoke = _load_manual_smoke_module()

        coverage = manual_smoke._case_command_coverage()
        aliases = getattr(manual_smoke, "_PUBLIC_COMMAND_ALIASES", {})
        missing = [name for name, case_ids in coverage.items() if not case_ids]
        unknown = sorted({
            command_name
            for case in manual_smoke.CASES
            for command_name in case.commands
            if aliases.get(command_name, command_name) not in coverage
            and command_name not in coverage
        })

        self.assertEqual(len(coverage), 18)
        self.assertEqual(missing, [])
        self.assertEqual(unknown, [])

    def test_manual_matrix_covers_public_option_contracts(self):
        manual_smoke = _load_manual_smoke_module()

        coverage = manual_smoke._case_option_coverage()
        missing = [name for name, case_ids in coverage.items() if not case_ids]
        unknown = sorted({
            option_key
            for case in manual_smoke.CASES
            for option_key in case.option_keys
            if option_key not in coverage
        })

        self.assertEqual(len(coverage), len(manual_smoke.OPTION_CONTRACTS))
        self.assertEqual(missing, [])
        self.assertEqual(unknown, [])
        self.assertIn("audit:sonarqube-docker-install-menu", coverage)
        self.assertIn("audit:sonarqube-docker-start-menu", coverage)
        self.assertIn("ship:deploy-confirmation-menu", coverage)
        self.assertIn("feature:user-gate-menu", coverage)
        self.assertIn("fix:user-gate-menu", coverage)
        self.assertIn("spike:conclusion-review-menu", coverage)
        self.assertIn("discuss:route-menu", coverage)
        self.assertIn("alfred:route-menu", coverage)
        self.assertIn("update:confirm-update-menu", coverage)
        self.assertIn("lucius:scope-security", coverage)
        self.assertIn("lucius:invalid-scope", coverage)
        self.assertIn("verify:no-argument", coverage)
        self.assertIn("feature:description", coverage)
        self.assertIn("verify:rejected", coverage)
        self.assertIn("alfred:optional-prompt", coverage)
        self.assertIn("config:exit-without-changes", coverage)
        self.assertIn("config:autonomia", coverage)
        self.assertIn("config:personalidad", coverage)
        self.assertEqual(coverage["config:memoria"], ["config"])

    def test_manual_matrix_covers_update_runtime_scope_contracts(self):
        manual_smoke = _load_manual_smoke_module()

        coverage = manual_smoke._case_runtime_coverage()
        missing = [name for name, case_ids in coverage.items() if not case_ids]
        unknown = sorted({
            runtime_key
            for case in manual_smoke.CASES
            for runtime_key in case.runtime_keys
            if runtime_key not in coverage
        })

        self.assertEqual(len(coverage), 4)
        self.assertEqual(missing, [])
        self.assertEqual(unknown, [])
        self.assertEqual(coverage["update:scope-local-to-user"], ["update"])
        self.assertEqual(coverage["update:scope-project-to-user"], ["update"])
        self.assertEqual(coverage["update:scope-managed"], ["update"])

    def test_default_timeout_allows_slow_claude_cli_cases(self):
        manual_smoke = _load_manual_smoke_module()

        self.assertEqual(manual_smoke.DEFAULT_TIMEOUT_SECONDS, 240)

    def test_dry_run_is_local_and_lists_cases(self):
        manual_smoke = _load_manual_smoke_module()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = manual_smoke.main(["--dry-run", "--case", "help"])

        self.assertEqual(result, 0)
        self.assertIn(f"plugin_dir={manual_smoke.ROOT}", output.getvalue())
        self.assertIn("plugin_source=worktree", output.getvalue())
        self.assertIn("runtime_contracts=4", output.getvalue())
        self.assertIn("missing_runtime_contracts=none", output.getvalue())

    def test_plugin_dir_selection_is_explicit_about_source(self):
        manual_smoke = _load_manual_smoke_module()

        path, source = manual_smoke._select_plugin_dir(None)
        self.assertEqual(path, manual_smoke.ROOT)
        self.assertEqual(source, "worktree")

        path, source = manual_smoke._select_plugin_dir(None, use_installed=True)
        self.assertEqual(path, manual_smoke.DEFAULT_PLUGIN_DIR)
        self.assertEqual(source, "installed-cache")

        path, source = manual_smoke._select_plugin_dir("~/alfred-test", use_installed=True)
        self.assertTrue(str(path).endswith("alfred-test"))
        self.assertEqual(source, "explicit")

    def test_plugin_surface_hash_ignores_pycache_and_tracks_real_files(self):
        manual_smoke = _load_manual_smoke_module()

        self.assertIn("package.json", manual_smoke.PLUGIN_SURFACE_ROOTS)
        self.assertIn("README.md", manual_smoke.PLUGIN_SURFACE_ROOTS)
        self.assertIn("scripts", manual_smoke.PLUGIN_SURFACE_ROOTS)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = Path(tmpdir)
            (plugin / "commands").mkdir()
            (plugin / "hooks" / "__pycache__").mkdir(parents=True)
            (plugin / "templates").mkdir()
            (plugin / ".mcp.json").write_text('{"mcpServers":{}}\n', encoding="utf-8")
            (plugin / "commands" / "help.md").write_text("help v1\n", encoding="utf-8")
            (plugin / "templates" / "prd.md").write_text("prd v1\n", encoding="utf-8")
            (plugin / "hooks" / "__pycache__" / "ignored.pyc").write_bytes(b"one")

            initial = manual_smoke._plugin_surface_snapshot(plugin)
            (plugin / "hooks" / "__pycache__" / "ignored.pyc").write_bytes(b"two")
            after_pyc = manual_smoke._plugin_surface_snapshot(plugin)
            (plugin / "commands" / "help.md").write_text("help v2\n", encoding="utf-8")
            after_real_change = manual_smoke._plugin_surface_snapshot(plugin)
            (plugin / "commands" / "help.md").write_text("help v1\n", encoding="utf-8")
            (plugin / "templates" / "prd.md").write_text("prd v2\n", encoding="utf-8")
            after_template_change = manual_smoke._plugin_surface_snapshot(plugin)

        self.assertEqual(initial["file_count"], 3)
        self.assertIn("templates", initial["roots"])
        self.assertEqual(initial["sha256"], after_pyc["sha256"])
        self.assertNotEqual(initial["sha256"], after_real_change["sha256"])
        self.assertNotEqual(initial["sha256"], after_template_change["sha256"])

    def test_active_quick_fixture_uses_valid_current_phase_index(self):
        manual_smoke = _load_manual_smoke_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            manual_smoke._seed_active_quick(project)
            state = json.loads(
                (project / ".claude" / "alfred-dev-state.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(state["comando"], "quick")
        self.assertEqual(state["fase_actual"], "ejecucion_acotada")
        self.assertEqual(state["fase_numero"], 0)

    def test_result_status_detects_auth_block(self):
        manual_smoke = _load_manual_smoke_module()
        payload = {
            "is_error": True,
            "api_error_status": 401,
            "result": "Failed to authenticate. API Error: 401 Invalid authentication credentials",
        }

        status, reason = manual_smoke._result_status(payload, json.dumps(payload), "", 1)

        self.assertEqual(status, "blocked_auth")
        self.assertIn("401", reason)

    def test_result_status_reports_budget_exhaustion(self):
        manual_smoke = _load_manual_smoke_module()
        payload = {
            "subtype": "error_max_budget_usd",
            "is_error": True,
            "errors": ["Reached maximum budget ($0.5)"],
        }

        status, reason = manual_smoke._result_status(payload, json.dumps(payload), "", 1)

        self.assertEqual(status, "failed")
        self.assertIn("presupuesto", reason)

    def test_run_case_uses_noninteractive_permissions_for_plugin_commands(self):
        manual_smoke = _load_manual_smoke_module()
        original_run = manual_smoke.subprocess.run
        captured = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            payload = {
                "is_error": False,
                "api_error_status": None,
                "result": "OK",
                "total_cost_usd": 0.2,
            }
            return manual_smoke.subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=json.dumps(payload),
                stderr="",
            )

        try:
            manual_smoke.subprocess.run = fake_run
            result = manual_smoke._run_case(
                manual_smoke.ManualCase("unit", "/alfred-dev:help", "ok"),
                manual_smoke.ROOT,
                "1.50",
                30,
            )
        finally:
            manual_smoke.subprocess.run = original_run

        self.assertEqual(result["status"], "needs_human_review")
        self.assertIn("--permission-mode", captured["command"])
        self.assertEqual(
            captured["command"][captured["command"].index("--permission-mode") + 1],
            "bypassPermissions",
        )
        self.assertEqual(
            captured["command"][captured["command"].index("--max-budget-usd") + 1],
            "1.50",
        )

    def test_run_case_records_timeout_without_aborting_matrix(self):
        manual_smoke = _load_manual_smoke_module()
        original_run = manual_smoke.subprocess.run

        def fake_run(command, **kwargs):
            raise manual_smoke.subprocess.TimeoutExpired(
                cmd=command,
                timeout=kwargs["timeout"],
                output="partial stdout",
                stderr="partial stderr",
            )

        try:
            manual_smoke.subprocess.run = fake_run
            result = manual_smoke._run_case(
                manual_smoke.ManualCase("unit-timeout", "/alfred", "ok"),
                manual_smoke.ROOT,
                "1.50",
                3,
            )
        finally:
            manual_smoke.subprocess.run = original_run

        self.assertEqual(result["status"], "failed")
        self.assertIn("timeout", result["reason"])
        self.assertEqual(result["returncode"], None)
        self.assertIn("partial stdout", result["response_preview"])
        self.assertIn("partial stderr", result["stderr_preview"])

    def test_auth_preflight_detects_real_401_before_cases(self):
        manual_smoke = _load_manual_smoke_module()
        result_payload = {
            "is_error": True,
            "api_error_status": 401,
            "result": "Failed to authenticate. API Error: 401 Invalid authentication credentials",
        }
        original_run = manual_smoke.subprocess.run
        original_env_snapshot = manual_smoke._credential_env_snapshot

        def fake_run(*args, **kwargs):
            command = args[0]
            if command == ["claude", "--version"]:
                return manual_smoke.subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="2.1.173 (Claude Code)\n",
                    stderr="",
                )
            if command == ["claude", "auth", "status", "--json"]:
                return manual_smoke.subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=json.dumps({
                        "loggedIn": True,
                        "authMethod": "claude.ai",
                        "apiProvider": "firstParty",
                        "email": "user@example.com",
                        "orgName": "Secret Org",
                        "subscriptionType": "max",
                    }),
                    stderr="",
                )
            return manual_smoke.subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout=json.dumps(result_payload),
                stderr="",
            )

        try:
            manual_smoke.subprocess.run = fake_run
            manual_smoke._credential_env_snapshot = lambda: {
                key: False for key in manual_smoke.CREDENTIAL_ENV_KEYS
            }
            result = manual_smoke._auth_preflight()
        finally:
            manual_smoke.subprocess.run = original_run
            manual_smoke._credential_env_snapshot = original_env_snapshot

        self.assertEqual(result["status"], "blocked_auth")
        self.assertEqual(result["api_error_status"], 401)
        self.assertEqual(result["auth_status"]["loggedIn"], True)
        self.assertEqual(result["auth_status"]["subscriptionType"], "max")
        self.assertEqual(result["auth_status"]["credential_env"]["ANTHROPIC_API_KEY"], False)
        self.assertEqual(result["diagnosis"]["code"], "first_party_oauth_token_rejected")
        self.assertIn("claude update", " ".join(result["diagnosis"]["next_steps"]))
        self.assertIn("claude auth logout", " ".join(result["diagnosis"]["next_steps"]))
        self.assertIn("safe-mode", result["preflight_mode"])
        self.assertNotIn("email", result["auth_status"])
        self.assertNotIn("orgName", result["auth_status"])

    def test_auth_preflight_budget_allows_cold_prompt_cache(self):
        """El preflight no debe fallar en frio por un presupuesto demasiado bajo."""
        manual_smoke = _load_manual_smoke_module()
        original_run = manual_smoke.subprocess.run

        captured_commands = []

        def fake_run(*args, **kwargs):
            command = args[0]
            captured_commands.append(command)
            if command == ["claude", "--version"]:
                return manual_smoke.subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="2.1.183 (Claude Code)\n",
                    stderr="",
                )
            if command == ["claude", "auth", "status", "--json"]:
                return manual_smoke.subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=json.dumps({"loggedIn": True, "authMethod": "claude.ai"}),
                    stderr="",
                )
            payload = {
                "is_error": False,
                "api_error_status": None,
                "result": "OK",
                "total_cost_usd": 0.028,
            }
            return manual_smoke.subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=json.dumps(payload),
                stderr="",
            )

        try:
            manual_smoke.subprocess.run = fake_run
            result = manual_smoke._auth_preflight()
        finally:
            manual_smoke.subprocess.run = original_run

        preflight_command = next(command for command in captured_commands if command[:2] == ["claude", "-p"])
        budget = preflight_command[preflight_command.index("--max-budget-usd") + 1]
        self.assertGreaterEqual(float(budget), 0.05)
        self.assertEqual(result["status"], "ok")

    def test_main_default_manual_budget_matches_real_plugin_cost(self):
        manual_smoke = _load_manual_smoke_module()
        original_run_case = manual_smoke._run_case
        captured = {}

        def fake_run_case(case, plugin_dir, budget, timeout):
            captured["budget"] = budget
            return {"case_id": case.case_id, "status": "needs_human_review"}

        output = io.StringIO()
        try:
            manual_smoke._run_case = fake_run_case
            with _mock_claude_cli_available(manual_smoke), contextlib.redirect_stdout(output):
                result = manual_smoke.main(["--case", "help"])
        finally:
            manual_smoke._run_case = original_run_case

        self.assertEqual(result, 0)
        self.assertGreaterEqual(float(captured["budget"]), 1.50)

    def test_successful_run_writes_complete_evidence_payload(self):
        manual_smoke = _load_manual_smoke_module()
        original_run_case = manual_smoke._run_case

        def fake_run_case(case, plugin_dir, budget, timeout):
            return {
                "case_id": case.case_id,
                "status": "needs_human_review",
                "reason": "ok",
            }

        output = io.StringIO()
        stderr = io.StringIO()
        try:
            manual_smoke._run_case = fake_run_case
            with tempfile.TemporaryDirectory() as tmpdir:
                evidence = Path(tmpdir) / "manual-smoke.json"
                with (
                    _mock_claude_cli_available(manual_smoke),
                    contextlib.redirect_stdout(output),
                    contextlib.redirect_stderr(stderr),
                ):
                    result = manual_smoke.main(["--case", "help", "--output", str(evidence)])
                payload = json.loads(evidence.read_text(encoding="utf-8"))
        finally:
            manual_smoke._run_case = original_run_case

        self.assertEqual(result, 0)
        self.assertEqual(payload["run_status"], "complete")
        self.assertEqual(payload["counts"]["total"], 1)
        self.assertEqual(payload["counts"]["needs_human_review"], 1)
        self.assertIn("[1/1] help", stderr.getvalue())

    def test_auth_diagnosis_distinguishes_missing_login_from_rejected_oauth(self):
        manual_smoke = _load_manual_smoke_module()

        missing_login = manual_smoke._auth_failure_diagnosis(
            "blocked_auth",
            401,
            {"loggedIn": False},
        )
        rejected_oauth = manual_smoke._auth_failure_diagnosis(
            "blocked_auth",
            401,
            {
                "loggedIn": True,
                "authMethod": "claude.ai",
                "apiProvider": "firstParty",
                "claude_version": "2.1.183 (Claude Code)",
            },
        )

        self.assertEqual(missing_login["code"], "not_logged_in")
        self.assertEqual(rejected_oauth["code"], "first_party_oauth_token_rejected")
        self.assertIn("claude auth login", " ".join(missing_login["next_steps"]))
        self.assertIn("claude doctor", " ".join(rejected_oauth["next_steps"]))
        self.assertIn("Keychain", " ".join(rejected_oauth["next_steps"]))
        self.assertIn("claude setup-token", " ".join(rejected_oauth["next_steps"]))
        self.assertNotIn("claude update", " ".join(rejected_oauth["next_steps"]))

    def test_auth_diagnosis_reports_environment_credential_precedence(self):
        manual_smoke = _load_manual_smoke_module()

        diagnosis = manual_smoke._auth_failure_diagnosis(
            "blocked_auth",
            401,
            {
                "loggedIn": True,
                "authMethod": "claude.ai",
                "apiProvider": "firstParty",
                "claude_version": "2.1.183 (Claude Code)",
                "credential_env": {
                    key: key == "ANTHROPIC_API_KEY"
                    for key in manual_smoke.CREDENTIAL_ENV_KEYS
                },
            },
        )

        self.assertEqual(diagnosis["code"], "environment_credential_rejected")
        self.assertIn("ANTHROPIC_API_KEY", " ".join(diagnosis["next_steps"]))
        self.assertIn("entorno limpio", " ".join(diagnosis["next_steps"]))

    def test_auth_diagnosis_recommends_update_for_old_claude_cli(self):
        manual_smoke = _load_manual_smoke_module()

        diagnosis = manual_smoke._auth_failure_diagnosis(
            "blocked_auth",
            401,
            {
                "loggedIn": True,
                "authMethod": "claude.ai",
                "apiProvider": "firstParty",
                "claude_version": "2.1.173 (Claude Code)",
            },
        )

        self.assertEqual(diagnosis["code"], "first_party_oauth_token_rejected")
        self.assertIn("claude update", diagnosis["next_steps"][0])

    def test_auth_preflight_can_abort_without_running_cases(self):
        manual_smoke = _load_manual_smoke_module()
        original_preflight = manual_smoke._auth_preflight
        original_run_case = manual_smoke._run_case

        def fake_preflight(timeout=45):
            return {
                "status": "blocked_auth",
                "reason": "Claude CLI devolvio 401 Invalid authentication credentials.",
                "duration_ms": 1,
                "returncode": 1,
                "api_error_status": 401,
                "total_cost_usd": 0,
                "response_preview": "Failed to authenticate",
                "stderr_preview": "",
            }

        def fake_run_case(*args, **kwargs):
            raise AssertionError("_run_case no debe ejecutarse si el preflight bloquea")

        output = io.StringIO()
        try:
            manual_smoke._auth_preflight = fake_preflight
            manual_smoke._run_case = fake_run_case
            with _mock_claude_cli_available(manual_smoke), contextlib.redirect_stdout(output):
                result = manual_smoke.main(["--auth-preflight", "--allow-auth-failure", "--case", "help"])
        finally:
            manual_smoke._auth_preflight = original_preflight
            manual_smoke._run_case = original_run_case

        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["auth_preflight"]["status"], "blocked_auth")
        self.assertEqual(payload["cases"], [])

    def test_auth_preflight_only_does_not_run_cases_when_auth_is_ok(self):
        manual_smoke = _load_manual_smoke_module()
        original_preflight = manual_smoke._auth_preflight
        original_run_case = manual_smoke._run_case

        def fake_preflight(timeout=45):
            return {
                "status": "ok",
                "reason": "Claude CLI pudo completar una llamada minima.",
                "duration_ms": 1,
                "returncode": 0,
                "api_error_status": None,
                "total_cost_usd": 0.01,
                "response_preview": "OK",
                "stderr_preview": "",
            }

        def fake_run_case(*args, **kwargs):
            raise AssertionError("_run_case no debe ejecutarse en --preflight-only")

        output = io.StringIO()
        try:
            manual_smoke._auth_preflight = fake_preflight
            manual_smoke._run_case = fake_run_case
            with _mock_claude_cli_available(manual_smoke), contextlib.redirect_stdout(output):
                result = manual_smoke.main(["--auth-preflight", "--preflight-only", "--case", "help"])
        finally:
            manual_smoke._auth_preflight = original_preflight
            manual_smoke._run_case = original_run_case

        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["auth_preflight"]["status"], "ok")
        self.assertEqual(payload["cases"], [])
        self.assertEqual(payload["counts"]["total"], 0)

    def test_auth_preflight_writes_blocked_output_without_running_cases(self):
        manual_smoke = _load_manual_smoke_module()
        original_preflight = manual_smoke._auth_preflight
        original_run_case = manual_smoke._run_case

        def fake_preflight(timeout=45):
            return {
                "status": "blocked_auth",
                "reason": "Claude CLI devolvio 401 Invalid authentication credentials.",
                "duration_ms": 1,
                "returncode": 1,
                "api_error_status": 401,
                "total_cost_usd": 0,
                "response_preview": "Failed to authenticate",
                "stderr_preview": "",
            }

        def fake_run_case(*args, **kwargs):
            raise AssertionError("_run_case no debe ejecutarse si el preflight bloquea")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manual-smoke.json"
            output = io.StringIO()
            try:
                manual_smoke._auth_preflight = fake_preflight
                manual_smoke._run_case = fake_run_case
                with _mock_claude_cli_available(manual_smoke), contextlib.redirect_stdout(output):
                    result = manual_smoke.main([
                        "--auth-preflight",
                        "--allow-auth-failure",
                        "--output",
                        str(output_path),
                    ])
            finally:
                manual_smoke._auth_preflight = original_preflight
                manual_smoke._run_case = original_run_case

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertIn("evidence=", output.getvalue())
        self.assertEqual(payload["auth_preflight"]["status"], "blocked_auth")
        self.assertEqual(payload["cases"], [])
        self.assertEqual(payload["counts"]["total"], 0)
        self.assertEqual(payload["plugin_source"], "worktree")

    def test_write_json_uses_private_file_permissions(self):
        manual_smoke = _load_manual_smoke_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "evidence.json"
            manual_smoke._write_json(output_path, {"status": "ok"})
            mode = stat.S_IMODE(output_path.stat().st_mode)

        self.assertEqual(mode, 0o600)

    def test_result_status_rejects_legacy_command_prefix(self):
        manual_smoke = _load_manual_smoke_module()
        payload = {
            "is_error": False,
            "result": "Puedes ejecutar `/alfred feature` para seguir.",
        }

        status, reason = manual_smoke._result_status(payload, json.dumps(payload), "", 0)

        self.assertEqual(status, "failed")
        self.assertIn("legacy", reason)

    def test_artifact_previews_capture_seeded_operational_files(self):
        manual_smoke = _load_manual_smoke_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            project = manual_smoke.Path(tmpdir)
            manual_smoke._seed_completed_quick(project)
            previews = manual_smoke._collect_artifact_previews(project)

        self.assertIn(".claude/alfred-dev-state.json", previews)
        self.assertIn("docs/project/uat.md", previews)
        self.assertIn("completado", previews[".claude/alfred-dev-state.json"])

    def test_safe_preview_sanitizes_secret_patterns(self):
        manual_smoke = _load_manual_smoke_module()
        anthropic_key = "sk-ant-" + ("a" * 24)
        openai_key = "sk-" + ("b" * 24)

        preview = manual_smoke._safe_preview(
            f"tokens: {anthropic_key} {openai_key} api_key='supersecret'",
            2000,
        )

        self.assertIn("[REDACTED:ANTHROPIC_KEY]", preview)
        self.assertIn("[REDACTED:SK_KEY]", preview)
        self.assertIn("[REDACTED:HARDCODED_CREDENTIAL]", preview)
        self.assertNotIn(anthropic_key, preview)
        self.assertNotIn(openai_key, preview)
        self.assertNotIn("supersecret", preview)

    def test_artifact_previews_sanitize_secrets(self):
        manual_smoke = _load_manual_smoke_module()
        anthropic_key = "sk-ant-" + ("c" * 24)

        with tempfile.TemporaryDirectory() as tmpdir:
            project = manual_smoke.Path(tmpdir)
            (project / ".claude").mkdir()
            (project / ".claude" / "alfred-dev-state.json").write_text(
                f'{{"token":"{anthropic_key}"}}\n',
                encoding="utf-8",
            )
            previews = manual_smoke._collect_artifact_previews(project)

        self.assertIn("[REDACTED:ANTHROPIC_KEY]", previews[".claude/alfred-dev-state.json"])
        self.assertNotIn(anthropic_key, previews[".claude/alfred-dev-state.json"])

    def test_seeded_runtime_artifacts_use_current_contracts(self):
        manual_smoke = _load_manual_smoke_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            project = manual_smoke.Path(tmpdir)
            manual_smoke._seed_active_quick(project)
            state = json.loads((project / ".claude" / "alfred-dev-state.json").read_text(encoding="utf-8"))

        self.assertEqual(state["comando"], "quick")
        self.assertEqual(state["fase_actual"], "ejecucion_acotada")

        with tempfile.TemporaryDirectory() as tmpdir:
            project = manual_smoke.Path(tmpdir)
            manual_smoke._seed_handoff(project)
            handoff = json.loads((project / ".claude" / "alfred-handoff.json").read_text(encoding="utf-8"))

        self.assertEqual(handoff["command"], "quick")
        self.assertEqual(handoff["phase"], "ejecucion_acotada")


if __name__ == "__main__":
    unittest.main()
