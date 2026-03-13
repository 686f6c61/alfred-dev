#!/usr/bin/env python3
"""Tests para el motor de personalidad."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.personality import get_agent_intro, get_agent_voice, AGENTS


class TestPersonality(unittest.TestCase):
    def test_all_agents_defined(self):
        # Núcleo: 9 agentes siempre activos
        core = {
            "alfred", "product-owner", "architect", "senior-dev",
            "security-officer", "qa-engineer", "devops-engineer", "tech-writer",
            "project-manager",
        }
        # Opcionales: 8 agentes predefinidos que el usuario activa
        optional = {
            "data-engineer", "ux-reviewer", "performance-engineer",
            "github-manager", "seo-specialist", "copywriter", "librarian",
            "i18n-specialist",
        }
        self.assertEqual(set(AGENTS.keys()), core | optional)

    def test_optional_agents_have_flag(self):
        """Los agentes opcionales deben tener el campo 'opcional': True."""
        optional_names = {
            "data-engineer", "ux-reviewer", "performance-engineer",
            "github-manager", "seo-specialist", "copywriter", "librarian",
            "i18n-specialist",
        }
        for name in optional_names:
            self.assertTrue(
                AGENTS[name].get("opcional", False),
                f"El agente '{name}' debería tener opcional=True"
            )

    def test_core_agents_not_optional(self):
        """Los agentes del núcleo no deben tener el campo 'opcional'."""
        core_names = {
            "alfred", "product-owner", "architect", "senior-dev",
            "security-officer", "qa-engineer", "devops-engineer", "tech-writer",
            "project-manager",
        }
        for name in core_names:
            self.assertFalse(
                AGENTS[name].get("opcional", False),
                f"El agente '{name}' no debería ser opcional"
            )

    def test_intro_respects_sarcasm_level(self):
        intro_low = get_agent_intro("alfred", nivel_sarcasmo=1)
        intro_high = get_agent_intro("alfred", nivel_sarcasmo=5)
        self.assertIsInstance(intro_low, str)
        self.assertIsInstance(intro_high, str)
        self.assertTrue(len(intro_low) > 0)
        self.assertTrue(len(intro_high) > 0)

    def test_voice_returns_phrases(self):
        for agent_name in AGENTS:
            phrases = get_agent_voice(agent_name)
            self.assertIsInstance(phrases, list)
            self.assertTrue(len(phrases) >= 2, f"{agent_name} necesita al menos 2 frases")

    def test_unknown_agent_raises(self):
        with self.assertRaises(ValueError):
            get_agent_intro("agente-fantasma")


if __name__ == "__main__":
    unittest.main()
