#!/usr/bin/env python3
"""Tests para hooks/prefetch-finish-guard.py."""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone


def _load_module():
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "hooks",
        "prefetch-finish-guard.py",
    )
    spec = importlib.util.spec_from_file_location("prefetch_finish_guard", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_guard = _load_module()


class TestPrefetchFinishGuard(unittest.TestCase):
    def _run_hook(self, payload: dict, cwd: str):
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_cwd = os.getcwd()
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()

        try:
            os.chdir(cwd)
            sys.stdin = io.StringIO(json.dumps(payload))
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr
            _guard.main()
        except SystemExit as exc:
            return exc.code, captured_stdout.getvalue(), captured_stderr.getvalue()
        finally:
            os.chdir(old_cwd)
            sys.stdin = old_stdin
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def test_without_marker_allows_tool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
                tmpdir,
            )
            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")

    def test_active_marker_blocks_followup_tool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            marker_path = os.path.join(tmpdir, ".claude", "alfred-prefetch-consumed.json")
            with open(marker_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "map-codebase",
                        "prefetched_command": "map-codebase",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "docs/project/codebase-map.md"}},
                tmpdir,
            )

            self.assertEqual(code, 2)
            self.assertIn('"decision": "block"', stdout)
            self.assertIn("helper-first", stderr)

    def test_pending_prefetch_blocks_wrapper_until_it_is_consumed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            prefetch_path = os.path.join(tmpdir, ".claude", "alfred-prefetch.json")
            with open(prefetch_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "alfred",
                        "prefetched_command": "map-codebase",
                        "response_text": "prefetch listo",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "src/index.js"}},
                tmpdir,
            )

            self.assertEqual(code, 2)
            self.assertIn("consume-prefetch", stdout)
            self.assertIn("prefetch pendiente", stderr)

    def test_pending_prefetch_for_quick_does_not_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            prefetch_path = os.path.join(tmpdir, ".claude", "alfred-prefetch.json")
            with open(prefetch_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "quick",
                        "prefetched_command": "quick",
                        "response_text": "prefetch quick",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "package.json"}},
                tmpdir,
            )

            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")

    def test_pending_prefetch_for_memory_ui_blocks_until_consumed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            prefetch_path = os.path.join(tmpdir, ".claude", "alfred-prefetch.json")
            with open(prefetch_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "memory-ui",
                        "prefetched_command": "memory-ui",
                        "response_text": "ui lista",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
                tmpdir,
            )

            self.assertEqual(code, 2)
            self.assertIn("consume-prefetch", stdout)
            self.assertIn("memory-ui", stderr)

    def test_resolves_project_dir_from_absolute_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as other_cwd:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            src_path = os.path.join(tmpdir, "src", "index.js")
            os.makedirs(os.path.dirname(src_path), exist_ok=True)
            with open(src_path, "w", encoding="utf-8") as fh:
                fh.write("console.log('hola')\n")

            marker_path = os.path.join(tmpdir, ".claude", "alfred-prefetch-consumed.json")
            with open(marker_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "map-codebase",
                        "prefetched_command": "map-codebase",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": src_path}},
                other_cwd,
            )

            self.assertEqual(code, 2)
            self.assertIn('"decision": "block"', stdout)
            self.assertIn("helper-first", stderr)

    def test_expired_marker_is_ignored_and_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            marker_path = os.path.join(tmpdir, ".claude", "alfred-prefetch-consumed.json")
            with open(marker_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_command": "map-codebase",
                        "prefetched_command": "map-codebase",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(),
                    },
                    fh,
                )

            code, stdout, stderr = self._run_hook(
                {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
                tmpdir,
            )

            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            self.assertFalse(os.path.exists(marker_path))


if __name__ == "__main__":
    unittest.main()
