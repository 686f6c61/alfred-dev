#!/usr/bin/env python3
"""Smoke tests del desinstalador bash sin tocar la instalacion real."""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_VERSION = json.loads(
    (PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
)["version"]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class TestUninstallSh(unittest.TestCase):
    def test_uninstall_sh_prefers_claude_cli_and_cleans_residual_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            plugins_dir = claude_dir / "plugins"
            cache_dir = plugins_dir / "cache" / "alfred-dev" / "alfred-dev" / PLUGIN_VERSION
            marketplace_dir = plugins_dir / "marketplaces" / "alfred-dev"
            fake_bin = home / "bin"
            calls_file = claude_dir / "fake-claude-calls.log"

            fake_bin.mkdir(parents=True)
            cache_dir.mkdir(parents=True, exist_ok=True)
            marketplace_dir.mkdir(parents=True, exist_ok=True)

            (plugins_dir / "known_marketplaces.json").write_text(
                json.dumps(
                    {
                        "alfred-dev": {
                            "source": {"source": "github", "repo": "686f6c61/alfred-dev"}
                        }
                    }
                ),
                encoding="utf-8",
            )
            (plugins_dir / "installed_plugins.json").write_text(
                json.dumps(
                    {
                        "version": 2,
                        "plugins": {
                            "alfred-dev@alfred-dev": [
                                {"scope": "user", "installPath": str(cache_dir)}
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            (claude_dir / "settings.json").write_text(
                json.dumps({"enabledPlugins": {"alfred-dev@alfred-dev": True}}),
                encoding="utf-8",
            )

            _write_executable(
                fake_bin / "python3",
                "#!/bin/sh\nexit 1\n",
            )
            _write_executable(
                fake_bin / "python3.12",
                f"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then\n  echo 3.12\n  exit 0\nfi\nexec {sys.executable} \"$@\"\n",
            )
            _write_executable(
                fake_bin / "claude",
                f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {calls_file}\nexit 0\n",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["/bin/bash", str(PROJECT_ROOT / "uninstall.sh")],
                cwd=home,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            calls = calls_file.read_text(encoding="utf-8")
            self.assertIn("plugin uninstall alfred-dev@alfred-dev", calls)
            self.assertIn("plugin marketplace remove alfred-dev", calls)
            self.assertFalse((plugins_dir / "cache" / "alfred-dev").exists())
            self.assertFalse(marketplace_dir.exists())

            known = json.loads((plugins_dir / "known_marketplaces.json").read_text(encoding="utf-8"))
            installed = json.loads((plugins_dir / "installed_plugins.json").read_text(encoding="utf-8"))
            settings = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))

            self.assertNotIn("alfred-dev", known)
            self.assertNotIn("alfred-dev@alfred-dev", installed.get("plugins", {}))
            self.assertNotIn("alfred-dev@alfred-dev", settings.get("enabledPlugins", {}))
            self.assertIn("Alfred Dev desinstalado", result.stdout)


if __name__ == "__main__":
    unittest.main()
