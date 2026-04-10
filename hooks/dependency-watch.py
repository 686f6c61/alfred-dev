#!/usr/bin/env python3
"""
Hook PostToolUse para Write/Edit: vigilante de dependencias.

Intercepta las operaciones de escritura sobre ficheros de dependencias
(package.json, Cargo.toml, pyproject.toml, etc.) e informa por stderr
con la voz de "El Paranoico" para que el usuario sea consciente de que
se han modificado las dependencias del proyecto.

No bloquea la operación (exit 0 siempre), solo avisa. La idea es que
cualquier cambio en dependencias reciba atención explícita porque cada
nueva dependencia es una superficie de ataque adicional.
"""

import json
import os
import re
import sys

# --- Ficheros de dependencias conocidos ---

# Conjunto de nombres de fichero (sin ruta) que contienen declaraciones
# de dependencias en los ecosistemas más comunes. Se comprueba el nombre
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
    "requirements.in",
    "requirements-dev.txt",
    "requirements-prod.txt",
    "constraints.txt",
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
    "packages.lock.json",
    "Directory.Packages.props",
    # Swift
    "Package.swift",
    "Package.resolved",
    # Workspaces / monorepos
    "pnpm-workspace.yaml",
}

_EDIT_GATED_MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Cargo.toml",
    "mix.exs",
    "composer.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Package.swift",
    "Directory.Packages.props",
}

_DEPENDENCY_SECTION_PATTERNS = {
    "package.json": (
        r'"(?:dependencies|devDependencies|peerDependencies|optionalDependencies|bundledDependencies)"\s*:',
        r'"(?:overrides|resolutions|packageExtensions|patchedDependencies)"\s*:',
    ),
    "pyproject.toml": (
        r"(?im)^\s*dependencies\s*=",
        r"(?im)^\s*\[project\.optional-dependencies\]",
        r"(?im)^\s*\[tool\.poetry(?:\.group\.[^.]+)?\.dependencies\]",
        r"(?im)^\s*\[dependency-groups\]",
    ),
    "setup.py": (r"\binstall_requires\b", r"\bextras_require\b"),
    "setup.cfg": (r"(?im)^\s*install_requires\s*=", r"(?im)^\s*\[options\.extras_require\]"),
    "Cargo.toml": (
        r"(?im)^\s*\[(?:workspace\.)?(?:dev-|build-)?dependencies(?:\.[^\]]+)?\]",
    ),
    "mix.exs": (r"\bdeps\s+do\b", r"\{:[^,]+,\s*\""),
    "composer.json": (r'"(?:require|require-dev|conflict|replace|provide)"\s*:',),
    "pom.xml": (r"<dependency>", r"<dependencies>"),
    "build.gradle": (r"\b(?:implementation|api|compileOnly|runtimeOnly|testImplementation|classpath)\b",),
    "build.gradle.kts": (r"\b(?:implementation|api|compileOnly|runtimeOnly|testImplementation|classpath)\b",),
    "Package.swift": (r"\.package\s*\(", r"dependencies\s*:\s*\["),
    "Directory.Packages.props": (r"<Package(?:Reference|Version)\b",),
}

_ALWAYS_DEPENDENCY_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "bun.lock",
    "requirements.txt",
    "requirements.in",
    "requirements-dev.txt",
    "requirements-prod.txt",
    "constraints.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "Gemfile.lock",
    "mix.lock",
    "composer.lock",
    "packages.config",
    "packages.lock.json",
    "Package.resolved",
    "pnpm-workspace.yaml",
}


def is_dependency_file(file_path: str) -> bool:
    """Determina si una ruta corresponde a un fichero de dependencias.

    Comprueba el nombre base del fichero (sin directorio) contra el
    conjunto de nombres conocidos. También detecta ficheros requirements
    con sufijos arbitrarios (requirements-*.txt).

    Args:
        file_path: Ruta absoluta o relativa del fichero.

    Returns:
        True si el fichero es un manifiesto de dependencias conocido.
    """
    basename = os.path.basename(file_path)

    # Comprobación directa contra nombres conocidos
    if basename in DEPENDENCY_FILES:
        return True

    # Patrón flexible para requirements-*.txt (ej.: requirements-ci.txt)
    if basename.startswith("requirements") and basename.endswith(".txt"):
        return True

    # constraints-*.txt en Python
    if basename.startswith("constraints") and basename.endswith(".txt"):
        return True

    # Ficheros de proyecto .NET
    if basename.endswith((".csproj", ".fsproj", ".vbproj")):
        return True

    return False


def has_dependency_signal(file_path: str, tool_input: dict) -> bool:
    """Determina si la escritura toca dependencias y no solo metadata lateral."""
    basename = os.path.basename(file_path)

    if basename.startswith("requirements") and basename.endswith(".txt"):
        return True
    if basename.startswith("constraints") and basename.endswith(".txt"):
        return True
    if basename.endswith((".csproj", ".fsproj", ".vbproj")):
        text = "\n".join(
            part for part in (
                tool_input.get("old_string", ""),
                tool_input.get("new_string", ""),
                tool_input.get("content", ""),
            ) if part
        )
        return bool(re.search(r"<PackageReference\b|<PackageVersion\b", text))

    if basename in _ALWAYS_DEPENDENCY_FILES:
        return True

    if basename not in _EDIT_GATED_MANIFESTS:
        return True

    text = "\n".join(
        part for part in (
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
        ) if part
    )
    if not text:
        text = tool_input.get("content", "")

    if not text:
        return True

    patterns = _DEPENDENCY_SECTION_PATTERNS.get(basename, ())
    return any(re.search(pattern, text) for pattern in patterns)


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae la ruta del fichero escrito o editado,
    y comprueba si es un fichero de dependencias. Si lo es, emite un
    aviso por stderr con la voz de El Paranoico.
    """
    try:
        data = json.load(sys.stdin)
    except ValueError as e:
        print(
            f"[dependency-watch] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La vigilancia de dependencias está desactivada para esta operación.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})

    # Extraer la ruta del fichero según la herramienta usada
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    # Solo actuar si es un fichero de dependencias
    if not is_dependency_file(file_path):
        sys.exit(0)

    # En manifiestos mixtos intentamos reducir ruido cuando el cambio solo
    # toca metadata o scripts y no las secciones de dependencias.
    if not has_dependency_signal(file_path, tool_input):
        sys.exit(0)

    basename = os.path.basename(file_path)

    print(
        f"\n"
        f"[El Paranoico] Cambio en dependencias detectado: {basename}\n"
        f"\n"
        f"Se ha modificado un manifiesto o lockfile de dependencias. Cada nueva\n"
        f"dependencia es una superficie de ataque que aceptas de ojos cerrados.\n"
        f"\n"
        f"Antes de seguir, pregúntate:\n"
        f"  - Es realmente necesaria esta dependencia?\n"
        f"  - Quién la mantiene? Tiene actividad reciente?\n"
        f"  - Qué permisos pide? Cuántas dependencias transitivas arrastra?\n"
        f"\n"
        f"Has pensado en los ataques de supply chain? Porque yo sí.\n",
        file=sys.stderr,
    )

    # No bloquear, solo informar
    sys.exit(0)


if __name__ == "__main__":
    main()
