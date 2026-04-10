#!/usr/bin/env python3
"""
Hook PreToolUse para Read: aviso informativo al leer ficheros sensibles.

Intercepta las operaciones de lectura de ficheros y emite un aviso por stderr
si el fichero solicitado coincide con un patron de fichero sensible (claves
privadas, variables de entorno, credenciales, etc.).

A diferencia de secret-guard.sh, este hook NO bloquea la operacion. Su
proposito es informar al agente de que esta accediendo a contenido sensible
para que tenga cuidado de no filtrar ese contenido en respuestas, commits
o artefactos generados.

Politica de seguridad: informativa (exit 0 siempre). Si no se puede parsear
la entrada, se permite la operacion sin aviso.
"""

import json
import os
import sys


def _is_env_file(base_name, _ext):
    return base_name == ".env" or base_name.startswith(".env.")


def _is_private_key(_base_name, ext):
    return ext in (".pem", ".key", ".p12", ".pfx")


def _is_ssh_private_key(base_name, _ext):
    return base_name in ("id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")


def _is_service_credentials_file(base_name, ext):
    lowered = base_name.lower()

    if lowered in {
        "credentials.json",
        "service-account.json",
        "gcloud-credentials.json",
        ".npmrc",
        ".pypirc",
        "terraform.tfstate",
    }:
        return True

    if ext != ".json":
        return False

    return (
        lowered.startswith("service-account")
        or lowered.startswith("firebase-adminsdk")
        or lowered.endswith("-service-account.json")
    )


def _is_htpasswd(base_name, _ext):
    return base_name == ".htpasswd"


def _is_java_keystore(_base_name, ext):
    return ext in (".jks", ".keystore")


# --- Patrones de ficheros sensibles ----------------------------------------
# Cada tupla contiene (condicion_lambda, descripcion).
# Las condiciones se evaluan sobre el nombre base del fichero o la ruta
# completa segun convenga.

_SENSITIVE_PATTERNS = [
    # Variables de entorno
    (_is_env_file, "Fichero de variables de entorno"),
    # Claves privadas
    (_is_private_key, "Clave privada o certificado"),
    # SSH keys
    (_is_ssh_private_key, "Clave SSH privada"),
    # Credenciales de servicios
    (_is_service_credentials_file, "Credenciales de servicio"),
    # htpasswd
    (_is_htpasswd, "Fichero de contrasenas Apache"),
    # Nota: credenciales AWS se detectan por ruta en _PATH_PATTERNS,
    # no por nombre base, porque "credentials" y "config" son demasiado genericos.
    # Keystore
    (_is_java_keystore, "Almacen de claves Java"),
]

# Patrones evaluados sobre la ruta completa (no solo el nombre base)
_PATH_PATTERNS = [
    (".aws/credentials", "Credenciales AWS"),
    (".aws/config", "Configuracion AWS con posibles credenciales"),
    ("/.docker/config.json", "Credenciales Docker"),
    ("/.kube/config", "Configuracion de Kubernetes"),
    ("/.terraform/terraform.tfstate", "Estado Terraform con posibles secretos"),
    (".ssh/", "Directorio SSH (posibles claves privadas)"),
    (".gnupg/", "Directorio GPG (posibles claves privadas)"),
]


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin proporcionado por PreToolUse, extrae la ruta del
    fichero de ``tool_input.file_path`` y la compara contra los patrones
    de ficheros sensibles. Si coincide, emite un aviso informativo.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    normalized_path = file_path.replace("\\", "/")

    # Obtener nombre base y extension para las comparaciones
    base_name = os.path.basename(normalized_path)
    _, ext = os.path.splitext(base_name)

    # Comprobar patrones por nombre base
    warning = None
    for check_fn, description in _SENSITIVE_PATTERNS:
        try:
            if check_fn(base_name, ext):
                warning = description
                break
        except Exception as exc:
            print(
                f"[Alfred Dev] Error evaluando patron de fichero sensible "
                f"'{description}': {exc}",
                file=sys.stderr,
            )
            continue

    # Comprobar patrones por ruta completa
    if warning is None:
        for pattern, description in _PATH_PATTERNS:
            if pattern in normalized_path:
                warning = description
                break

    if warning is not None:
        print(
            f"\n[Alfred Dev] AVISO: lectura de fichero sensible\n\n"
            f"  Fichero: {file_path}\n"
            f"  Tipo:    {warning}\n\n"
            f"  Ten cuidado de no filtrar el contenido de este fichero\n"
            f"  en respuestas, commits, logs o artefactos generados.\n",
            file=sys.stderr,
        )

    # Siempre permitir la lectura (informativo, no bloqueante)
    sys.exit(0)


if __name__ == "__main__":
    main()
