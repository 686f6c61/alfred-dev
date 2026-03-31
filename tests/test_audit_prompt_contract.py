#!/usr/bin/env python3
"""Tests de contrato para los prompts de audit y SonarQube.

Estos tests protegen comportamiento definido en Markdown. Como los commands y
skills del plugin son prompts ejecutables por Claude Code, sus instrucciones
forman parte de la logica del sistema y se verifican como contrato textual.
"""

import os
import unicodedata
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


class TestAuditCommandContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = _read("commands/audit.md")
        cls.audit_norm = _normalize(cls.audit)

    def test_audit_has_sonarqube_preflight_section(self):
        self.assertIn("## Preflight de SonarQube", self.audit)
        self.assertIn("docker --version", self.audit)
        self.assertIn("docker info", self.audit)

    def test_audit_asks_before_installing_or_starting_docker(self):
        self.assertIn("AskUserQuestion", self.audit)
        self.assertIn("NO intentes instalarlo por tu cuenta", self.audit)
        self.assertIn("NO intentes arrancarlo por tu cuenta", self.audit)

    def test_audit_keeps_permission_prompt_even_in_autopilot(self):
        self.assertIn("incluso si el proyecto esta en modo autopilot", self.audit_norm)
        self.assertIn("requiere confirmacion explicita del usuario", self.audit_norm)

    def test_audit_forbids_silent_sonarqube_skip(self):
        self.assertIn("NUNCA lo omitas sin dejarlo por escrito", self.audit)
        self.assertIn("sonarqube se omitio por decision explicita del usuario", self.audit_norm)

    def test_audit_locates_plugin_files_outside_the_project(self):
        self.assertIn("NO dentro del proyecto auditado", self.audit)
        self.assertIn("~/.claude/plugins/cache/alfred-dev/**/commands/_composicion.md", self.audit)
        self.assertIn("si `${claude_plugin_root}` no esta resuelta", self.audit_norm)


class TestSonarQubeSkillContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = _read("skills/calidad/sonarqube/SKILL.md")
        cls.skill_norm = _normalize(cls.skill)

    def test_skill_requires_explicit_permission_for_docker_changes(self):
        self.assertIn(
            "no instales docker, no abras docker desktop y no arranques el daemon sin aprobacion explicita del usuario.",
            self.skill_norm,
        )
        self.assertIn(
            "si no existe una autorizacion previa, pidela ahora y espera respuesta.",
            self.skill_norm,
        )

    def test_skill_handles_port_conflicts_and_cleanup(self):
        self.assertIn("puerto `9000` ya esta en uso", self.skill_norm)
        self.assertIn("docker rm -f sonarqube-alfred", self.skill)
        self.assertIn("intenta igualmente la limpieza final del contenedor temporal", self.skill_norm)

    def test_skill_mentions_zsh_safe_status_variable(self):
        self.assertIn("no uses la variable `status`", self.skill_norm)
        self.assertIn("usa `sonar_status`", self.skill_norm)


class TestHelpContract(unittest.TestCase):
    def test_help_lists_the_nine_core_agents(self):
        help_md = _read("commands/help.md")
        self.assertIn("project-manager (SonIA)", help_md)


if __name__ == "__main__":
    unittest.main()
