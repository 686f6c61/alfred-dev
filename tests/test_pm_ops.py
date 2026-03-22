#!/usr/bin/env python3
"""Tests para la capa PM determinista y sync GitHub de Alfred 0.4.5."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (  # noqa: E402
    GITHUB_SYNC_JSON_RELATIVE_PATH,
    GITHUB_SYNC_MD_RELATIVE_PATH,
    build_lane_snapshot,
    build_standup_snapshot,
    load_kanban_board,
    render_lane_markdown,
    render_standup_markdown,
    render_validation_markdown,
    search_project_context,
    sync_project_to_github,
    validate_operational_artifacts,
)
from core.memory import MemoryDB  # noqa: E402


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


class TestPmHelpers(unittest.TestCase):
    def _seed_board(self, tmpdir: str) -> None:
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
            """# Backlog

### [T-001] Diseñar login

- **Historia:** HU-01
- **Criterios:** CA-01, CA-02
- **Agente:** architect
- **Dependencias:** ninguna
- **Notas:** Aterrizar el flujo base
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
            """# In Progress

### [T-002] Implementar endpoint POST /login

- **Historia:** HU-01
- **Criterios:** CA-01, CA-03
- **Agente:** senior-dev
- **Dependencias:** T-001
- **Notas:** Pendiente de cerrar tests de error
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "done.md"),
            """# Done

### [T-003] Preparar esquema de usuarios

- **Historia:** HU-01
- **Criterios:** CA-01
- **Agente:** data-engineer
- **Evidencia:** tests/test_users.py::test_schema_users
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"),
            """# Blocked

### [T-004] Integrar sesión persistente

- **Historia:** HU-01
- **Criterios:** CA-04
- **Agente:** senior-dev
- **Dependencias:** Decisión de cookies seguras
- **Notas:** Bloqueado por criterio legal pendiente
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "progress.md"),
            "# Progreso\n\n- Login base ya modelado\n- Queda cerrar la persistencia de sesión\n",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "traceability.md"),
            "# Traceability\n\n- CA-01 -> T-001, T-002, T-003\n- CA-02 -> T-001\n- CA-03 -> T-002\n- CA-04 -> T-004\n",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "current.md"),
            "# Current\n\n- Estado: implementación en curso\n- Comando recomendado: /alfred-dev:verify\n",
        )

    def test_load_kanban_board_parses_heading_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            board = load_kanban_board(tmpdir)

        self.assertEqual(board["backlog"][0]["id"], "T-001")
        self.assertEqual(board["in-progress"][0]["agent"], "senior-dev")
        self.assertEqual(board["done"][0]["evidence"], "tests/test_users.py::test_schema_users")
        self.assertEqual(board["blocked"][0]["dependencies"], "Decisión de cookies seguras")

    def test_standup_snapshot_and_render_include_focus_and_next(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            snapshot = build_standup_snapshot(tmpdir)
            content = render_standup_markdown(snapshot)

        self.assertIn("## Standup diario", content)
        self.assertIn("[T-002] Implementar endpoint POST /login", content)
        self.assertIn("[T-004] Integrar sesión persistente", content)
        self.assertIn("/alfred-dev:alfred", content)

    def test_lane_snapshot_renders_blocked_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            snapshot = build_lane_snapshot(tmpdir, "blocked")
            content = render_lane_markdown(snapshot)

        self.assertIn("Tareas en blocked", content)
        self.assertIn("Decisión de cookies seguras", content)

    def test_validate_detects_warnings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "done.md"),
                """# Done

### [T-003] Preparar esquema de usuarios

- **Historia:** HU-01
- **Criterios:** CA-01
- **Agente:** data-engineer
""",
            )
            report = validate_operational_artifacts(tmpdir)
            content = render_validation_markdown(report)

        self.assertEqual(report["status"], "warning")
        self.assertIn("done sin evidencia", content)

    def test_search_finds_docs_and_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            db_path = os.path.join(tmpdir, ".claude", "alfred-memory.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db = MemoryDB(db_path)
            try:
                iteration_id = db.start_iteration("feature", "Login")
                db.log_decision(
                    title="Cookies seguras en login",
                    chosen="Usar cookies HttpOnly",
                    context="Autenticación web",
                    rationale="Evita acceso desde JS",
                    iteration_id=iteration_id,
                )
            finally:
                db.close()

            result = search_project_context(tmpdir, "login")

        self.assertTrue(result["docs"])
        self.assertTrue(result["memory"])

    def test_cli_standup_and_search_modes_support_direct_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            continuity_script = os.path.join(
                os.path.dirname(__file__), "..", "core", "continuity.py"
            )
            standup = subprocess.run(
                [sys.executable, continuity_script, "standup", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            search = subprocess.run(
                [sys.executable, continuity_script, "search", tmpdir, "--raw", "login"],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(standup.returncode, 0, msg=standup.stderr)
        self.assertIn("## Standup diario", standup.stdout)
        self.assertEqual(search.returncode, 0, msg=search.stderr)
        self.assertIn("## Resultados para `login`", search.stdout)


class TestGitHubSyncHelpers(unittest.TestCase):
    def _seed_board(self, tmpdir: str) -> None:
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
            """# Backlog

### [T-010] Preparar labels de issues

- **Agente:** github-manager
- **Criterios:** CA-10
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
            """# In Progress

### [T-011] Sincronizar tablero

- **Agente:** project-manager
- **Criterios:** CA-11
""",
        )
        _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
        _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
        _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n\n- CA-10 -> T-010\n- CA-11 -> T-011\n")

    def test_sync_project_to_github_writes_mapping_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)

            created = {}

            def fake_create_or_update_issue(repo, task, sync_state):
                number = 100 + len(created) + 1
                payload = {
                    "number": number,
                    "url": f"https://github.com/{repo}/issues/{number}",
                    "title": f"[{task['id']}] {task['title']}",
                    "status": task["status"],
                    "updated_at": "2026-03-22T00:00:00+00:00",
                }
                created[task["id"]] = payload
                return payload

            with mock.patch("core.continuity._ensure_gh_ready"), \
                mock.patch("core.continuity._ensure_github_labels"), \
                mock.patch("core.continuity._detect_github_repo", return_value="686f6c61/alfred-e2e"), \
                mock.patch("core.continuity._create_or_update_issue", side_effect=fake_create_or_update_issue), \
                mock.patch(
                    "core.continuity._ensure_board_issue",
                    return_value={
                        "number": 99,
                        "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                        "title": "SonIA Sync: alfred-e2e",
                    },
                ):
                result = sync_project_to_github(tmpdir)

            self.assertEqual(result["repo"], "686f6c61/alfred-e2e")
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            with open(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                markdown = fh.read()

        self.assertEqual(payload["repo"], "686f6c61/alfred-e2e")
        self.assertIn("T-010", payload["tasks"])
        self.assertIn("SonIA Sync", markdown)
        self.assertIn("#101", markdown)
        self.assertNotIn("[T-010] [T-010]", markdown)

    def test_cli_sync_github_supports_end_to_end_with_fake_gh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            _write(
                os.path.join(tmpdir, "package.json"),
                json.dumps({"name": "alfred-e2e-pm"}, ensure_ascii=False),
            )
            subprocess.run(["git", "-C", tmpdir, "init", "-q"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    tmpdir,
                    "remote",
                    "add",
                    "origin",
                    "git@github.com:686f6c61/alfred-e2e-pm.git",
                ],
                check=True,
            )

            fake_bin = os.path.join(tmpdir, "fake-bin")
            os.makedirs(fake_bin, exist_ok=True)
            gh_state = os.path.join(tmpdir, "gh-state.json")
            gh_script = os.path.join(fake_bin, "gh")
            _write(
                gh_script,
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import os
                    import re
                    import sys

                    state_path = os.environ["GH_STUB_STATE"]
                    if os.path.exists(state_path):
                        with open(state_path, "r", encoding="utf-8") as fh:
                            state = json.load(fh)
                    else:
                        state = {"issues": [], "labels": [], "next_issue": 1}

                    def save():
                        with open(state_path, "w", encoding="utf-8") as fh:
                            json.dump(state, fh, ensure_ascii=False, indent=2)

                    def issue_payload(issue):
                        return {
                            "number": issue["number"],
                            "title": issue["title"],
                            "state": issue["state"],
                            "url": issue["url"],
                            "labels": [{"name": label} for label in issue.get("labels", [])],
                        }

                    args = sys.argv[1:]
                    if args == ["--version"]:
                        print("gh version 0.0.0-fake")
                        raise SystemExit(0)
                    if args[:3] == ["auth", "status", "-h"]:
                        print("github.com\\n  ✓ Logged in")
                        raise SystemExit(0)
                    if args[:2] == ["label", "create"]:
                        name = args[2]
                        if name not in state["labels"]:
                            state["labels"].append(name)
                            save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "view"]:
                        number = int(args[2])
                        for issue in state["issues"]:
                            if issue["number"] == number:
                                print(json.dumps(issue_payload(issue), ensure_ascii=False))
                                raise SystemExit(0)
                        raise SystemExit(1)
                    if args[:2] == ["issue", "list"]:
                        label = None
                        title = None
                        for idx, token in enumerate(args):
                            if token == "--label":
                                label = args[idx + 1]
                            elif token == "--search":
                                raw = args[idx + 1]
                                match = re.match(r'"(?P<title>.*)" in:title', raw)
                                title = match.group("title") if match else raw
                        matches = []
                        for issue in state["issues"]:
                            if label and label not in issue.get("labels", []):
                                continue
                            if title and issue["title"] != title:
                                continue
                            matches.append(issue_payload(issue))
                        print(json.dumps(matches, ensure_ascii=False))
                        raise SystemExit(0)
                    if args[:2] == ["issue", "create"]:
                        repo = ""
                        title = ""
                        body = ""
                        labels = []
                        idx = 2
                        while idx < len(args):
                            token = args[idx]
                            if token == "--repo":
                                repo = args[idx + 1]
                                idx += 2
                            elif token == "--title":
                                title = args[idx + 1]
                                idx += 2
                            elif token == "--body":
                                body = args[idx + 1]
                                idx += 2
                            elif token == "--label":
                                labels.append(args[idx + 1])
                                idx += 2
                            else:
                                idx += 1
                        number = state["next_issue"]
                        state["next_issue"] += 1
                        issue = {
                            "number": number,
                            "title": title,
                            "body": body,
                            "state": "OPEN",
                            "url": f"https://github.com/{repo}/issues/{number}",
                            "labels": labels,
                        }
                        state["issues"].append(issue)
                        save()
                        print(issue["url"])
                        raise SystemExit(0)
                    if args[:2] == ["issue", "edit"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        idx = 3
                        while idx < len(args):
                            token = args[idx]
                            if token == "--title":
                                issue["title"] = args[idx + 1]
                                idx += 2
                            elif token == "--body":
                                issue["body"] = args[idx + 1]
                                idx += 2
                            elif token == "--add-label":
                                label = args[idx + 1]
                                if label not in issue["labels"]:
                                    issue["labels"].append(label)
                                idx += 2
                            elif token == "--remove-label":
                                label = args[idx + 1]
                                issue["labels"] = [item for item in issue["labels"] if item != label]
                                idx += 2
                            else:
                                idx += 1
                        save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "close"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        issue["state"] = "CLOSED"
                        save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "reopen"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        issue["state"] = "OPEN"
                        save()
                        raise SystemExit(0)

                    print(f"Unsupported gh invocation: {args}", file=sys.stderr)
                    raise SystemExit(1)
                    """
                ),
            )
            os.chmod(gh_script, 0o755)

            continuity_script = os.path.join(
                os.path.dirname(__file__), "..", "core", "continuity.py"
            )
            env = os.environ.copy()
            env["PATH"] = fake_bin + os.pathsep + env.get("PATH", "")
            env["GH_STUB_STATE"] = gh_state
            proc = subprocess.run(
                [sys.executable, continuity_script, "sync-github", tmpdir],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("## SonIA Sync", proc.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH)))

            with open(gh_state, "r", encoding="utf-8") as fh:
                gh_payload = json.load(fh)

        self.assertGreaterEqual(len(gh_payload["issues"]), 3)
        self.assertTrue(any(issue["title"].startswith("[T-010]") for issue in gh_payload["issues"]))
        self.assertTrue(any(issue["title"].startswith("SonIA Sync:") for issue in gh_payload["issues"]))

    def test_rendered_sync_markdown_does_not_duplicate_task_prefix(self):
        result = {
            "repo": "686f6c61/alfred-e2e",
            "board_issue": {"url": "https://github.com/686f6c61/alfred-e2e/issues/9"},
            "tasks": [
                {
                    "id": "T-010",
                    "title": "[T-010] Preparar labels de issues",
                    "status": "backlog",
                    "number": 101,
                }
            ],
            "skipped": [],
        }

        from core.continuity import render_github_sync_markdown  # noqa: E402

        markdown = render_github_sync_markdown(result)

        self.assertIn("## SonIA Sync", markdown)
        self.assertIn("[T-010] Preparar labels de issues", markdown)
        self.assertNotIn("[T-010] [T-010]", markdown)


if __name__ == "__main__":
    unittest.main()
