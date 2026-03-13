#!/usr/bin/env python3
"""Tests para el modulo de gestion de worktrees."""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.worktree import (
    _sanitize_branch_name,
    is_git_repo,
    get_current_branch,
    has_uncommitted_changes,
    create_worktree,
    cleanup_worktree,
    merge_worktree,
    list_worktrees,
)


class TestSanitizeBranchName(unittest.TestCase):
    """Verifica la sanitizacion de nombres de rama."""

    def test_simple_name(self):
        self.assertEqual(_sanitize_branch_name("login-oauth"), "login-oauth")

    def test_spaces(self):
        self.assertEqual(_sanitize_branch_name("login con oauth"), "login-con-oauth")

    def test_special_chars(self):
        result = _sanitize_branch_name("fix: bug #123!")
        self.assertNotIn(":", result)
        self.assertNotIn("#", result)
        self.assertNotIn("!", result)

    def test_consecutive_dashes(self):
        result = _sanitize_branch_name("a---b")
        self.assertNotIn("--", result)

    def test_truncation(self):
        long_name = "a" * 100
        result = _sanitize_branch_name(long_name)
        self.assertLessEqual(len(result), 50)

    def test_empty_string(self):
        self.assertEqual(_sanitize_branch_name(""), "work")

    def test_preserves_slashes(self):
        result = _sanitize_branch_name("feature/auth")
        self.assertIn("/", result)


class TestGitHelpers(unittest.TestCase):
    """Verifica las funciones auxiliares de git."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Inicializar repo git temporal
        subprocess.run(["git", "init"], cwd=self.tmpdir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.tmpdir, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.tmpdir, capture_output=True,
        )
        # Crear commit inicial
        test_file = os.path.join(self.tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=self.tmpdir, capture_output=True,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_git_repo(self):
        self.assertTrue(is_git_repo(self.tmpdir))

    def test_not_git_repo(self):
        tmpdir2 = tempfile.mkdtemp()
        self.assertFalse(is_git_repo(tmpdir2))
        import shutil
        shutil.rmtree(tmpdir2, ignore_errors=True)

    def test_get_current_branch(self):
        branch = get_current_branch(self.tmpdir)
        self.assertIsNotNone(branch)
        self.assertIn(branch, ["main", "master"])

    def test_has_uncommitted_changes_clean(self):
        self.assertFalse(has_uncommitted_changes(self.tmpdir))

    def test_has_uncommitted_changes_dirty(self):
        with open(os.path.join(self.tmpdir, "new.txt"), "w") as f:
            f.write("new")
        self.assertTrue(has_uncommitted_changes(self.tmpdir))


class TestWorktreeOperations(unittest.TestCase):
    """Verifica la creacion y limpieza de worktrees."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self.tmpdir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.tmpdir, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.tmpdir, capture_output=True,
        )
        test_file = os.path.join(self.tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=self.tmpdir, capture_output=True,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_worktree(self):
        wt_path, branch = create_worktree(
            "login oauth",
            flow_type="feature",
            project_dir=self.tmpdir,
        )
        self.assertTrue(os.path.isdir(wt_path))
        self.assertIn("alfred/", branch)
        self.assertIn("feature/", branch)

    def test_create_worktree_no_git(self):
        tmpdir2 = tempfile.mkdtemp()
        with self.assertRaises(RuntimeError):
            create_worktree("test", project_dir=tmpdir2)
        import shutil
        shutil.rmtree(tmpdir2, ignore_errors=True)

    def test_create_worktree_dirty(self):
        with open(os.path.join(self.tmpdir, "dirty.txt"), "w") as f:
            f.write("dirty")
        with self.assertRaises(RuntimeError):
            create_worktree("test", project_dir=self.tmpdir)

    def test_cleanup_worktree(self):
        wt_path, branch = create_worktree(
            "cleanup test",
            project_dir=self.tmpdir,
        )
        self.assertTrue(os.path.isdir(wt_path))
        cleanup_worktree(wt_path, project_dir=self.tmpdir)
        self.assertFalse(os.path.isdir(wt_path))

    def test_merge_worktree(self):
        wt_path, branch = create_worktree(
            "merge test",
            project_dir=self.tmpdir,
        )
        # Hacer un cambio en el worktree
        new_file = os.path.join(wt_path, "feature.txt")
        with open(new_file, "w") as f:
            f.write("new feature")
        subprocess.run(["git", "add", "."], cwd=wt_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "add feature"],
            cwd=wt_path, capture_output=True,
        )

        # Fusionar de vuelta
        success = merge_worktree(
            wt_path, branch,
            project_dir=self.tmpdir,
        )
        self.assertTrue(success)

        # Verificar que el fichero existe en la rama principal
        self.assertTrue(os.path.isfile(os.path.join(self.tmpdir, "feature.txt")))

    def test_list_worktrees(self):
        create_worktree("list test", project_dir=self.tmpdir)
        worktrees = list_worktrees(project_dir=self.tmpdir)
        # Al menos 2: el principal + el nuevo
        self.assertGreaterEqual(len(worktrees), 2)


if __name__ == "__main__":
    unittest.main()
