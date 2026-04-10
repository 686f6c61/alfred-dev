#!/usr/bin/env python3
"""Tests para la galeria de demos visuales de Selina."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from core.selina_style_demo import (
    STYLE_DEMO_GALLERY_FILENAME,
    render_style_demo_document,
    write_style_demo_gallery,
)


WRITE_STYLE_DEMO_GALLERY_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
    "write-style-demo-gallery.py",
)


class TestSelinaStyleDemo(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="alfred-selina-demo-")
        self.session_dir = os.path.join(self.project_dir, ".alfred-dev", "visual", "session-1")
        self.state_dir = os.path.join(self.session_dir, "state")
        self.content_dir = os.path.join(self.session_dir, "content")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    def test_render_style_demo_document_includes_google_fonts_and_style_name(self):
        html = render_style_demo_document("neo-brutalism")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Neo-brutalismo", html)
        self.assertIn("fonts.googleapis.com/css2", html)
        self.assertIn("Instalar Alfred Dev", html)

    def test_write_style_demo_gallery_creates_gallery_and_demo_pages(self):
        result = write_style_demo_gallery(self.state_dir)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["style_count"], 10)
        self.assertTrue(os.path.isfile(result["gallery_path"]))
        self.assertEqual(
            os.path.basename(result["gallery_path"]),
            STYLE_DEMO_GALLERY_FILENAME,
        )
        self.assertEqual(len(result["demo_paths"]), 10)
        self.assertTrue(all(os.path.isfile(path) for path in result["demo_paths"]))

        with open(result["gallery_path"], "r", encoding="utf-8") as fh:
            gallery = fh.read()
        self.assertIn("Atlas de sistemas de diseño de Selina", gallery)
        self.assertIn("/files/demos/neo-brutalism.html", gallery)
        self.assertIn("Maximalismo &amp; Neo-retro", gallery)

    def test_write_style_demo_gallery_script_outputs_json(self):
        result = subprocess.run(
            [
                "python3",
                WRITE_STYLE_DEMO_GALLERY_SCRIPT,
                "--visual-path",
                self.state_dir,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["style_count"], 10)


if __name__ == "__main__":
    unittest.main()
