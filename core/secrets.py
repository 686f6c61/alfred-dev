#!/usr/bin/env python3
"""
Fuente unica de verdad para los patrones de deteccion de secretos.

Este modulo centraliza los regex que detectan credenciales, tokens y claves
en texto plano. Los consumidores son:

    - ``core/memory.py``: sanitiza contenido antes de persistir en SQLite.
    - ``hooks/secret-guard.sh``: bloquea escritura de secretos en ficheros.
    - ``hooks/sensitive-read-guard.py``: avisa al leer ficheros sensibles.

Antes de este modulo, los patrones estaban duplicados en 3 sitios con
variantes ligeramente distintas, lo que implicaba que un patron nuevo o
una correccion de regex tenia que replicarse manualmente en los 3 ficheros.
Ahora cualquier cambio se hace aqui y se propaga automaticamente.

Los patrones se ordenan de mas especifico a mas generico para evitar que
un patron amplio consuma un match que deberia capturar uno mas preciso.
"""

import re
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Patrones de secretos en contenido de texto
# ---------------------------------------------------------------------------
# Cada tupla contiene (patron_compilado, etiqueta_para_marcador).
# La etiqueta se usa como [REDACTED:<etiqueta>] en la sanitizacion.

SECRET_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Claves AWS (prefijo AKIA fijo)
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_KEY"),
    # Anthropic API Key (prefijo sk-ant-)
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC_KEY"),
    # Claves con prefijo sk- generico (OpenAI, Stripe, etc.)
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "SK_KEY"),
    # GitHub Personal Access Token (ghp_ o github_pat_)
    (
        re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})"),
        "GITHUB_TOKEN",
    ),
    # Slack Token (xoxb, xoxp, xoxs, xoxa)
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "SLACK_TOKEN"),
    # Google API Key (prefijo AIza)
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "GOOGLE_KEY"),
    # SendGrid API Key
    (
        re.compile(r"SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}"),
        "SENDGRID_KEY",
    ),
    # Claves privadas PEM/SSH
    (
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "PRIVATE_KEY",
    ),
    # JWT tokens hardcodeados (3 segmentos base64url separados por puntos)
    (
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
        "JWT",
    ),
    # Connection strings con credenciales embebidas
    (
        re.compile(
            r"(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|amqp)"
            r"://[^\s\"']{10,}@"
        ),
        "CONNECTION_STRING",
    ),
    # Slack Webhook URL
    (
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"),
        "SLACK_WEBHOOK",
    ),
    # Discord Webhook URL
    (
        re.compile(
            r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"
        ),
        "DISCORD_WEBHOOK",
    ),
    # Asignaciones directas de credenciales en codigo fuente
    (
        re.compile(
            r"(?i)(?:password|passwd|api_key|apikey|api_secret|secret_key"
            r"|auth_token|access_token|private_key)"
            r"""\s*[:=]\s*["'][^"']{8,}["']"""
        ),
        "HARDCODED_CREDENTIAL",
    ),
]


def sanitize_text(text: str) -> str:
    """Reemplaza secretos detectados por marcadores [REDACTED:<tipo>].

    Aplica todos los patrones de ``SECRET_PATTERNS`` sobre el texto y
    sustituye cada coincidencia por su marcador correspondiente.

    Args:
        text: texto a sanitizar.

    Returns:
        Texto con los secretos reemplazados por marcadores.
    """
    for pattern, label in SECRET_PATTERNS:
        text = pattern.sub(f"[REDACTED:{label}]", text)
    return text
