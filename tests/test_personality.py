#!/usr/bin/env python3
"""Tests para el motor de personalidad."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.personality import get_agent_intro, get_agent_voice, AGENTS


class TestPersonality(unittest.TestCase):
    def test_all_agents_defined(self):
        core = {
            "alfred", "product-owner", "architect", "senior-dev",
            "security-officer", "qa-engineer", "devops-engineer", "tech-writer",
            "selina", "lucius",
        }
        self.assertEqual(set(AGENTS.keys()), core)

    def test_optional_agents_have_flag(self):
        self.assertIn("lucius", AGENTS)

    def test_core_agents_not_optional(self):
        core_names = {
            "alfred", "product-owner", "architect", "senior-dev",
            "security-officer", "qa-engineer", "devops-engineer", "tech-writer",
            "selina",
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
