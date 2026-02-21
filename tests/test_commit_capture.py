#!/usr/bin/env python3
"""Tests para el hook commit-capture.py."""

import importlib.util
import os
import unittest

# Importar el hook usando importlib (el nombre tiene guion)
_hook_path = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "commit-capture.py"
)
_spec = importlib.util.spec_from_file_location("commit_capture", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_git_commit_command = _mod.is_git_commit_command


class TestIsGitCommitCommand(unittest.TestCase):
    """Verifica la deteccion de comandos git commit."""

    def test_simple_git_commit(self):
        """Un git commit simple debe detectarse."""
        self.assertTrue(is_git_commit_command('git commit -m "msg"'))

    def test_git_commit_with_add(self):
        """git commit despues de && debe detectarse."""
        self.assertTrue(is_git_commit_command("git add . && git commit -m 'msg'"))

    def test_git_commit_after_semicolon(self):
        """git commit despues de ; debe detectarse."""
        self.assertTrue(is_git_commit_command('ls; git commit -m "msg"'))

    def test_git_commit_amend(self):
        """git commit --amend debe detectarse."""
        self.assertTrue(is_git_commit_command("git commit --amend"))

    def test_git_commit_after_or(self):
        """git commit despues de || debe detectarse."""
        self.assertTrue(is_git_commit_command("false || git commit -m 'fallback'"))

    def test_not_git_push(self):
        """git push no debe detectarse como commit."""
        self.assertFalse(is_git_commit_command("git push origin main"))

    def test_not_grep_git_commit(self):
        """grep con 'git commit' como argumento no debe detectarse."""
        self.assertFalse(is_git_commit_command("grep 'git commit' log.txt"))


if __name__ == "__main__":
    unittest.main()
