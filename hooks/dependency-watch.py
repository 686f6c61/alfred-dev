#!/usr/bin/env python3
"""
Hook PostToolUse para Write/Edit: vigilante de dependencias.

Intercepta las operaciones de escritura sobre ficheros de dependencias
(package.json, Cargo.toml, pyproject.toml, etc.) e informa por stderr
con la voz de "El Paranoico" para que el usuario sea consciente de que
se han modificado las dependencias del proyecto.

No bloquea la operacion (exit 0 siempre), solo avisa. La idea es que
cualquier cambio en dependencias reciba atencion explicita porque cada
nueva dependencia es una superficie de ataque adicional.
"""

import json
import os
import sys

# --- Ficheros de dependencias conocidos ---

# Conjunto de nombres de fichero (sin ruta) que contienen declaraciones
# de dependencias en los ecosistemas mas comunes. Se comprueba el nombre
# base del fichero para ser independiente de la ruta.
DEPENDENCY_FILES = {
    # Node.js / JavaScript / TypeScript
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "bun.lock",
    # Python
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-prod.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    # Rust
    "Cargo.toml",
    "Cargo.lock",
    # Go
    "go.mod",
    "go.sum",
    # Ruby
    "Gemfile",
    "Gemfile.lock",
    # Elixir
    "mix.exs",
    "mix.lock",
    # PHP
    "composer.json",
    "composer.lock",
    # Java / Kotlin / Scala
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    # .NET
    "packages.config",
    # Swift
    "Package.swift",
    "Package.resolved",
}


def is_dependency_file(file_path: str) -> bool:
    """Determina si una ruta corresponde a un fichero de dependencias.

    Comprueba el nombre base del fichero (sin directorio) contra el
    conjunto de nombres conocidos. Tambien detecta ficheros requirements
    con sufijos arbitrarios (requirements-*.txt).

    Args:
        file_path: Ruta absoluta o relativa del fichero.

    Returns:
        True si el fichero es un manifiesto de dependencias conocido.
    """
    basename = os.path.basename(file_path)

    # Comprobacion directa contra nombres conocidos
    if basename in DEPENDENCY_FILES:
        return True

    # Patron flexible para requirements-*.txt (ej: requirements-ci.txt)
    if basename.startswith("requirements") and basename.endswith(".txt"):
        return True

    # Ficheros .csproj y .fsproj de .NET
    if basename.endswith((".csproj", ".fsproj")):
        return True

    return False


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae la ruta del fichero escrito o editado,
    y comprueba si es un fichero de dependencias. Si lo es, emite un
    aviso por stderr con la voz de El Paranoico.
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(
            f"[dependency-watch] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La vigilancia de dependencias esta desactivada para esta operacion.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})

    # Extraer la ruta del fichero segun la herramienta usada
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    # Solo actuar si es un fichero de dependencias
    if not is_dependency_file(file_path):
        sys.exit(0)

    basename = os.path.basename(file_path)

    print(
        f"\n"
        f"[El Paranoico] Cambio en dependencias detectado: {basename}\n"
        f"\n"
        f"Se ha modificado un fichero de dependencias. Cada nueva dependencia\n"
        f"es una superficie de ataque que aceptas de ojos cerrados.\n"
        f"\n"
        f"Antes de seguir, preguntate:\n"
        f"  - Es realmente necesaria esta dependencia?\n"
        f"  - Quien la mantiene? Tiene actividad reciente?\n"
        f"  - Que permisos pide? Cuantas dependencias transitivas arrastra?\n"
        f"\n"
        f"Has pensado en los ataques de supply chain? Porque yo si.\n",
        file=sys.stderr,
    )

    # No bloquear, solo informar
    sys.exit(0)


if __name__ == "__main__":
    main()
