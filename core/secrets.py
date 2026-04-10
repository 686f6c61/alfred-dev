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

import os
import re
from typing import List, Optional, Tuple


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
            r"://(?:(?:[^/\s\"':@]+:[^/\s\"'@]+)|(?:[^/\s\"'@]{8,}))@"
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

SECRET_DESCRIPTIONS = {
    "AWS_KEY": "AWS Access Key (patron AKIA...)",
    "ANTHROPIC_KEY": "Anthropic API Key",
    "SK_KEY": "Clave API con prefijo sk- (OpenAI, Stripe u otro)",
    "GITHUB_TOKEN": "GitHub Personal Access Token",
    "SLACK_TOKEN": "Slack Token",
    "GOOGLE_KEY": "Google API Key (patron AIza...)",
    "SENDGRID_KEY": "SendGrid API Key",
    "PRIVATE_KEY": "Clave privada PEM/SSH",
    "JWT": "JWT token hardcodeado",
    "CONNECTION_STRING": "Connection string con credenciales",
    "SLACK_WEBHOOK": "Slack Webhook URL",
    "DISCORD_WEBHOOK": "Discord Webhook URL",
    "HARDCODED_CREDENTIAL": "Credencial hardcodeada en asignacion",
}

_ALLOWED_ENV_SUFFIXES = {
    "local",
    "development",
    "development.local",
    "test",
    "test.local",
    "production",
    "production.local",
    "staging",
    "staging.local",
}

_DISALLOWED_ENV_TOKENS = {
    "example",
    "sample",
    "template",
    "dist",
}


def describe_secret_label(label: str) -> str:
    """Devuelve una descripcion legible para el tipo de secreto."""
    return SECRET_DESCRIPTIONS.get(label, label)


def find_secret_label(text: str) -> Optional[str]:
    """Devuelve la primera etiqueta de secreto encontrada en ``text``."""
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text):
            return label
    return None


def is_secret_storage_path(file_path: str) -> bool:
    """Indica si la ruta es un contenedor legitimo de secretos locales.

    Se permiten los ficheros de entorno reales del proyecto, pero no sus
    variantes de ejemplo o plantilla, que suelen ser versionadas.
    """
    if not file_path:
        return False

    base_name = os.path.basename(file_path).lower()

    if base_name in {".env", "local.env"}:
        return True

    if not base_name.startswith(".env."):
        return False

    suffix = base_name[len(".env."):]
    if not suffix:
        return False

    if suffix in _ALLOWED_ENV_SUFFIXES:
        return True

    parts = [part for part in suffix.split(".") if part]
    return not any(part in _DISALLOWED_ENV_TOKENS for part in parts)


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
