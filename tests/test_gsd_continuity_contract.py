#!/usr/bin/env python3
"""Tests de contrato para el primer bloque GSD en Alfred."""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestHelpListsContinuityCommands(unittest.TestCase):
    def test_help_includes_new_commands(self):
        help_md = _read("commands/help.md")
        self.assertIn("/alfred-dev:discuss", help_md)
        self.assertIn("/alfred-dev:map-codebase", help_md)
        self.assertIn("/alfred-dev:next", help_md)
        self.assertIn("/alfred-dev:pause", help_md)
        self.assertIn("/alfred-dev:progress", help_md)
        self.assertIn("/alfred-dev:quick", help_md)
        self.assertIn("/alfred-dev:resume", help_md)
        self.assertIn("/alfred-dev:verify", help_md)


class TestMapCodebaseContract(unittest.TestCase):
    def test_map_codebase_creates_operational_artifacts(self):
        command = _read("commands/map-codebase.md")
        self.assertIn("docs/project/codebase-map.md", command)
        self.assertIn("docs/project/current.md", command)
        self.assertIn('python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected map-codebase', command)
        self.assertIn('python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn("NO modifiques código de aplicación", command)


class TestNextContract(unittest.TestCase):
    def test_next_prioritizes_state_handoff_then_brownfield(self):
        command = _read("commands/next.md")
        self.assertIn(".claude/alfred-dev-state.json", command)
        self.assertIn(".claude/alfred-handoff.json", command)
        self.assertIn(".claude/alfred-uat.json", command)
        self.assertIn("docs/project/discovery.md", command)
        self.assertIn("actúa como `/alfred-dev:resume`", command)
        self.assertIn("actúa como `/alfred-dev:verify`", command)
        self.assertIn("allow-stop-once", command)
        self.assertIn("actúa como `/alfred-dev:map-codebase`", command)
        self.assertIn("fuente es `discovery`", command)


class TestPauseResumeContract(unittest.TestCase):
    def test_pause_writes_handoff_files(self):
        command = _read("commands/pause.md")
        self.assertIn(".claude/alfred-handoff.json", command)
        self.assertIn("docs/project/handoff.md", command)
        self.assertIn("paused_at", command)
        self.assertIn('paused_via: "/alfred-dev:pause"', command)
        self.assertIn('python3 .claude/alfred-continuity.py pause "$PWD"', command)
        self.assertIn("NO marques la sesión como completada", command)

    def test_resume_uses_state_then_handoff(self):
        command = _read("commands/resume.md")
        self.assertIn(".claude/alfred-dev-state.json", command)
        self.assertIn(".claude/alfred-handoff.json", command)
        self.assertIn("Prioridad de reanudación", command)
        self.assertIn("resumed_at", command)
        self.assertIn('python3 .claude/alfred-continuity.py resume "$PWD"', command)
        self.assertIn("NO uses `AskUserQuestion` dentro de `/alfred-dev:resume`", command)
        self.assertIn("/alfred-dev:next", command)


class TestVerifyContract(unittest.TestCase):
    def test_verify_uses_continuity_helper_and_uat_artifacts(self):
        command = _read("commands/verify.md")
        self.assertIn(".claude/alfred-uat.json", command)
        self.assertIn("docs/project/uat.md", command)
        self.assertIn('python3 .claude/alfred-continuity.py verify "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn("NO uses `AskUserQuestion` como paso obligatorio", command)


class TestQuickContract(unittest.TestCase):
    def test_quick_uses_light_flow_and_helper(self):
        command = _read("commands/quick.md")
        self.assertIn("flujo `quick`", command)
        self.assertIn("ejecucion_acotada", command)
        self.assertIn("validacion_rapida", command)
        self.assertIn('python3 .claude/alfred-continuity.py quick "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn("bypass transitorio del stop hook", command)
        self.assertIn("Al terminar, deja visible que el siguiente paso esperado es `/alfred-dev:verify`", command)


class TestDiscussContract(unittest.TestCase):
    def test_discuss_creates_refinement_artifacts(self):
        command = _read("commands/discuss.md")
        self.assertIn("docs/project/discovery.md", command)
        self.assertIn("docs/project/current.md", command)
        self.assertIn('python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected discuss', command)
        self.assertIn("product-owner", command)
        self.assertIn("siguiente comando recomendado", command)
        self.assertIn('python3 .claude/alfred-continuity.py discuss "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn("/alfred-dev:feature", command)
        self.assertIn("/alfred-dev:quick", command)
        self.assertIn("/alfred-dev:fix", command)
        self.assertIn("/alfred-dev:spike", command)


if __name__ == "__main__":
    unittest.main()
