#!/usr/bin/env python3
"""Tests para el hook dangerous-command-guard.py."""

import importlib.util
import json
import os
import subprocess
import sys
import unittest

# Importar el hook usando importlib (el nombre tiene guion)
_hook_path = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "dangerous-command-guard.py"
)
_spec = importlib.util.spec_from_file_location("dangerous_command_guard", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_DANGEROUS_PATTERNS = _mod._DANGEROUS_PATTERNS
_is_safe_alfred_helper_command = _mod._is_safe_alfred_helper_command
_has_shell_controls_outside_quotes = _mod._has_shell_controls_outside_quotes
_find_dangerous_reason = _mod._find_dangerous_reason


def _is_dangerous(command: str) -> bool:
    """Comprueba si un comando seria bloqueado por el hook real."""
    return _find_dangerous_reason(command) is not None


class TestDangerousCommands(unittest.TestCase):
    """Verifica que los comandos peligrosos se detectan correctamente."""

    # --- Borrado catastrofico ---

    def test_rm_rf_root(self):
        self.assertTrue(_is_dangerous("rm -rf /"))

    def test_rm_rf_root_wildcard(self):
        self.assertTrue(_is_dangerous("rm -rf /*"))

    def test_rm_rf_home(self):
        self.assertTrue(_is_dangerous("rm -rf ~"))

    def test_rm_rf_home_var(self):
        self.assertTrue(_is_dangerous("rm -rf $HOME"))

    def test_rm_rf_etc(self):
        self.assertTrue(_is_dangerous("rm -rf /etc"))

    def test_rm_rf_usr(self):
        self.assertTrue(_is_dangerous("rm -rf /usr"))

    def test_rm_fr_root(self):
        """Verifica que -fr (orden inverso de flags) tambien se detecta."""
        self.assertTrue(_is_dangerous("rm -fr /"))

    def test_sudo_rm_rf_root(self):
        """Verifica que sudo rm -rf / tambien se detecta."""
        self.assertTrue(_is_dangerous("sudo rm -rf /"))

    def test_rm_separated_flags(self):
        """Verifica que flags separadas -r -f tambien se detectan."""
        self.assertTrue(_is_dangerous("rm -r -f /"))

    # --- Comandos seguros de rm ---

    def test_rm_rf_node_modules(self):
        self.assertFalse(_is_dangerous("rm -rf node_modules"))

    def test_rm_rf_dist(self):
        self.assertFalse(_is_dangerous("rm -rf dist/"))

    def test_rm_rf_build(self):
        self.assertFalse(_is_dangerous("rm -rf build/"))

    def test_rm_single_file(self):
        self.assertFalse(_is_dangerous("rm archivo.txt"))

    # --- Force push ---

    def test_git_push_force_main(self):
        self.assertTrue(_is_dangerous("git push --force origin main"))

    def test_git_push_f_master(self):
        self.assertTrue(_is_dangerous("git push -f origin master"))

    # --- Comandos git seguros ---

    def test_git_push_normal(self):
        self.assertFalse(_is_dangerous("git push origin feature/nueva"))

    def test_git_push_u(self):
        self.assertFalse(_is_dangerous("git push -u origin main"))

    # --- SQL destructivo ---

    def test_drop_database(self):
        self.assertTrue(_is_dangerous("DROP DATABASE produccion"))

    def test_drop_table(self):
        self.assertTrue(_is_dangerous("DROP TABLE users"))

    def test_drop_schema(self):
        self.assertTrue(_is_dangerous("DROP SCHEMA public"))

    def test_drop_case_insensitive(self):
        self.assertTrue(_is_dangerous("drop database produccion"))

    # --- Docker prune ---

    def test_docker_system_prune_af(self):
        self.assertTrue(_is_dangerous("docker system prune -af"))

    def test_docker_system_prune_fa(self):
        self.assertTrue(_is_dangerous("docker system prune -f -a"))

    # --- Permisos inseguros ---

    def test_chmod_777_root(self):
        self.assertTrue(_is_dangerous("chmod 777 /"))

    def test_chmod_R_777_root(self):
        self.assertTrue(_is_dangerous("chmod -R 777 /var"))

    # --- Fork bomb ---

    def test_fork_bomb(self):
        self.assertTrue(_is_dangerous(":(){ :|:& };:"))

    # --- Formateo de disco ---

    def test_mkfs_ext4(self):
        self.assertTrue(_is_dangerous("mkfs.ext4 /dev/sda1"))

    def test_dd_to_device(self):
        self.assertTrue(_is_dangerous("dd if=/dev/zero of=/dev/sda"))

    def test_dd_to_nvme(self):
        self.assertTrue(_is_dangerous("dd if=/dev/zero of=/dev/nvme0n1"))

    # --- Redireccion a dispositivo ---

    def test_redirect_to_sda(self):
        self.assertTrue(_is_dangerous("> /dev/sda"))

    # --- git reset --hard ---

    def test_git_reset_hard_origin_main(self):
        self.assertTrue(_is_dangerous("git reset --hard origin/main"))

    def test_git_reset_hard_origin_master(self):
        self.assertTrue(_is_dangerous("git reset --hard origin/master"))

    # --- Comandos seguros generales ---

    def test_ls(self):
        self.assertFalse(_is_dangerous("ls -la"))

    def test_git_status(self):
        self.assertFalse(_is_dangerous("git status"))

    def test_npm_install(self):
        self.assertFalse(_is_dangerous("npm install"))

    def test_python_script(self):
        self.assertFalse(_is_dangerous("python3 script.py"))

    def test_docker_build(self):
        self.assertFalse(_is_dangerous("docker build -t myapp ."))

    def test_cat_file(self):
        self.assertFalse(_is_dangerous("cat /etc/hosts"))

    def test_detects_shell_wrapper_rm_rf(self):
        self.assertTrue(_is_dangerous('sh -c "rm -rf /"'))

    def test_detects_bash_lc_force_push(self):
        self.assertTrue(_is_dangerous('bash -lc "git push --force origin main"'))

    def test_allows_documented_dangerous_text_in_printf(self):
        self.assertFalse(_is_dangerous("printf '%s\\n' 'git push --force origin main'"))

    def test_allows_grep_for_docker_prune_literal(self):
        self.assertFalse(_is_dangerous('grep -R "docker system prune -af" .'))

    def test_allows_python_print_of_dangerous_text(self):
        self.assertFalse(_is_dangerous('python3 -c "print(\\"chmod -R 777 /var\\")"'))

    def test_allows_echo_of_fork_bomb_literal(self):
        self.assertFalse(_is_dangerous('echo ":(){ :|:& };:"'))

    def test_allows_cat_heredoc_with_literal_command(self):
        command = "cat <<'EOF'\nrm -rf /\nEOF"
        self.assertFalse(_is_dangerous(command))


class TestSafeAlfredHelpers(unittest.TestCase):
    """Verifica la autoaprobacion de helpers deterministas de Alfred."""

    def test_safe_consume_prefetch_command(self):
        command = 'python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected map-codebase'
        self.assertTrue(_is_safe_alfred_helper_command(command))

    def test_safe_map_codebase_command(self):
        command = 'python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "login y usuarios"'
        self.assertTrue(_is_safe_alfred_helper_command(command))

    def test_safe_operational_helpers_added_later(self):
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py blocked "$PWD"'
        ))
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py standup "$PWD"'
        ))
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py validate "$PWD"'
        ))
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py search "$PWD" --raw "login usuarios"'
        ))

    def test_safe_helper_with_capture_suffix(self):
        command = 'python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected map-codebase 2>&1'
        self.assertTrue(_is_safe_alfred_helper_command(command))

    def test_allows_quoted_pipe_and_redirect_like_text(self):
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py search "$PWD" --raw "login | signup"'
        ))
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py discuss "$PWD" --raw "funnel A > B"'
        ))
        self.assertTrue(_is_safe_alfred_helper_command(
            'python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "auth; users"'
        ))

    def test_rejects_shell_chaining(self):
        command = 'python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "login"; rm -rf /'
        self.assertFalse(_is_safe_alfred_helper_command(command))

    def test_rejects_real_shell_controls_outside_quotes(self):
        self.assertTrue(_has_shell_controls_outside_quotes('echo hola && whoami'))
        self.assertFalse(_has_shell_controls_outside_quotes('echo "hola && adios"'))
        self.assertFalse(_has_shell_controls_outside_quotes("echo 'a | b ; c > d'"))

    def test_rejects_command_substitution_even_if_quoted(self):
        command = 'python3 .claude/alfred-continuity.py discuss "$PWD" --raw "$(whoami)"'
        self.assertFalse(_is_safe_alfred_helper_command(command))

    def test_hook_emits_permission_allow_for_safe_helper(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": 'python3 .claude/alfred-continuity.py progress "$PWD"',
            },
        }

        result = subprocess.run(
            [sys.executable, _hook_path],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(
            response["hookSpecificOutput"]["permissionDecision"],
            "allow",
        )


if __name__ == "__main__":
    unittest.main()
