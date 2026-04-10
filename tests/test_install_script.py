#!/usr/bin/env python3
"""Smoke tests del instalador bash sin tocar la instalacion real."""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_VERSION = json.loads(
    (PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
)["version"]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class TestInstallSh(unittest.TestCase):
    def test_install_sh_can_be_invoked_from_repo_path_and_patches_active_runtime_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            fake_bin = home / "bin"
            cache_dir = claude_dir / "plugins" / "cache" / "alfred-dev"
            marketplace_dir = claude_dir / "plugins" / "marketplaces" / "alfred-dev"
            known_marketplaces = claude_dir / "plugins" / "known_marketplaces.json"
            state_file = claude_dir / "fake-claude-state"
            calls_file = claude_dir / "fake-claude-calls.log"

            fake_bin.mkdir(parents=True)
            marketplace_dir.parent.mkdir(parents=True, exist_ok=True)
            cache_dir.mkdir(parents=True, exist_ok=True)
            known_marketplaces.write_text("{}", encoding="utf-8")

            stale_hooks = cache_dir / "alfred-dev" / "0.5.9" / "hooks" / "hooks.json"
            stale_mcp = cache_dir / "alfred-dev" / "0.5.9" / ".claude-plugin" / "mcp.json"
            stale_hooks.parent.mkdir(parents=True, exist_ok=True)
            stale_mcp.parent.mkdir(parents=True, exist_ok=True)
            stale_hooks.write_text(
                textwrap.dedent(
                    """\
                    {
                      "hooks": {
                        "PreToolUse": [
                          {
                            "matcher": "Write|Edit|MultiEdit",
                            "hooks": [
                              {
                                "type": "command",
                                "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/activity-capture.py"
                              }
                            ]
                          }
                        ]
                      }
                    }
                    """
                ),
                encoding="utf-8",
            )
            stale_mcp.write_text(
                textwrap.dedent(
                    """\
                    {
                      "mcpServers": {
                        "alfred-memory": {
                          "command": "python3",
                          "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/memory_server.py"]
                        }
                      }
                    }
                    """
                ),
                encoding="utf-8",
            )
            _write_executable(
                fake_bin / "python3",
                f"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then\n  echo 3.9\n  exit 0\nfi\nexec {sys.executable} \"$@\"\n",
            )
            _write_executable(
                fake_bin / "python3.12",
                f"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then\n  echo 3.12\n  exit 0\nfi\nexec {sys.executable} \"$@\"\n",
            )
            _write_executable(
                fake_bin / "python3.13",
                f"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then\n  echo 3.13\n  exit 0\nfi\nexec {sys.executable} \"$@\"\n",
            )
            _write_executable(
                fake_bin / "claude",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu

                    HOME_DIR="$HOME"
                    CLAUDE_DIR="$HOME_DIR/.claude"
                    STATE_FILE="{state_file}"
                    CALLS_FILE="{calls_file}"
                    MARKETPLACE_DIR="$CLAUDE_DIR/plugins/marketplaces/alfred-dev"
                    KNOWN_MARKETPLACES="$CLAUDE_DIR/plugins/known_marketplaces.json"
                    CACHE_ROOT="$CLAUDE_DIR/plugins/cache/alfred-dev/alfred-dev/{PLUGIN_VERSION}"
                    HOOKS_JSON="$CACHE_ROOT/hooks/hooks.json"
                    MCP_JSON="$CACHE_ROOT/.claude-plugin/mcp.json"

                    installed=0
                    marketplace=0
                    if [ -f "$STATE_FILE" ]; then
                      . "$STATE_FILE"
                    fi

                    mkdir -p "$CLAUDE_DIR"
                    printf '%s\\n' "$*" >> "$CALLS_FILE"

                    if [ "$1" != "plugin" ]; then
                      exit 1
                    fi

                    case "${{2:-}}" in
                      list)
                        if [ "$installed" = 1 ]; then
                          printf 'alfred-dev@alfred-dev\\n'
                        fi
                        ;;
                      uninstall)
                        installed=0
                        ;;
                      install)
                        installed=1
                        mkdir -p "$(dirname "$HOOKS_JSON")" "$(dirname "$MCP_JSON")"
                        cat > "$HOOKS_JSON" <<'EOF'
                    {{
                      "hooks": {{
                        "PreToolUse": [
                          {{
                            "matcher": "Write|Edit|MultiEdit",
                            "hooks": [
                              {{
                                "type": "command",
                                "command": "python3 ${{CLAUDE_PLUGIN_ROOT}}/hooks/activity-capture.py"
                              }}
                            ]
                          }}
                        ]
                      }}
                    }}
                    EOF
                        cat > "$MCP_JSON" <<'EOF'
                    {{
                      "mcpServers": {{
                        "alfred-memory": {{
                          "command": "python3",
                          "args": ["${{CLAUDE_PLUGIN_ROOT}}/mcp/memory_server.py"]
                        }}
                      }}
                    }}
                    EOF
                        ;;
                      marketplace)
                        case "${{3:-}}" in
                          list)
                            if [ "$marketplace" = 1 ]; then
                              printf 'alfred-dev\\n'
                            fi
                            ;;
                          remove)
                            marketplace=0
                            rm -rf "$MARKETPLACE_DIR"
                            printf '{{}}' > "$KNOWN_MARKETPLACES"
                            ;;
                          add)
                            marketplace=1
                            cat > "$KNOWN_MARKETPLACES" <<'EOF'
                    {{
                      "alfred-dev": {{
                        "source": {{
                          "source": "github",
                          "repo": "686f6c61/alfred-dev"
                        }},
                        "installLocation": "{marketplace_dir}",
                        "lastUpdated": "2026-04-10T00:00:00.000Z"
                      }}
                    }}
                    EOF
                            ;;
                          *)
                            exit 1
                            ;;
                        esac
                        ;;
                      *)
                        exit 1
                        ;;
                    esac

                    printf 'installed=%s\\nmarketplace=%s\\n' "$installed" "$marketplace" > "$STATE_FILE"
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["/bin/bash", str(PROJECT_ROOT / "install.sh")],
                cwd=home,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            hooks_json = (
                home
                / ".claude"
                / "plugins"
                / "cache"
                / "alfred-dev"
                / "alfred-dev"
                / PLUGIN_VERSION
                / "hooks"
                / "hooks.json"
            ).read_text(encoding="utf-8")
            mcp_json = (
                home
                / ".claude"
                / "plugins"
                / "cache"
                / "alfred-dev"
                / "alfred-dev"
                / PLUGIN_VERSION
                / ".claude-plugin"
                / "mcp.json"
            ).read_text(encoding="utf-8")
            calls = calls_file.read_text(encoding="utf-8")
            registered = json.loads(known_marketplaces.read_text(encoding="utf-8"))
            stale_hooks_after = stale_hooks.read_text(encoding="utf-8")
            stale_mcp_after = stale_mcp.read_text(encoding="utf-8")

            self.assertIn("plugin marketplace add 686f6c61/alfred-dev", calls)
            self.assertIn("plugin install alfred-dev@alfred-dev", calls)
            self.assertEqual(registered["alfred-dev"]["source"]["source"], "github")
            self.assertEqual(registered["alfred-dev"]["source"]["repo"], "686f6c61/alfred-dev")
            self.assertIn(str(fake_bin / "python3.13"), hooks_json)
            self.assertIn(str(fake_bin / "python3.13"), mcp_json)
            self.assertNotIn(str(fake_bin / "python3.13"), stale_hooks_after)
            self.assertNotIn(str(fake_bin / "python3.13"), stale_mcp_after)
            self.assertIn("Instalacion completada", result.stdout)


if __name__ == "__main__":
    unittest.main()
