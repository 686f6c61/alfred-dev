#!/usr/bin/env python3
"""
Gestion de git worktrees para aislamiento de trabajo en Alfred Dev.

Proporciona un mecanismo para ejecutar flujos de trabajo (feature, fix)
en worktrees aislados, de modo que los cambios no afecten a la rama
principal hasta que se validen y fusionen explicitamente.

El patron de uso es:
1. ``create_worktree()`` crea un worktree en un directorio temporal
   con una rama nueva derivada de la rama activa.
2. El agente trabaja en el worktree como si fuera el proyecto normal.
3. Al terminar, ``merge_worktree()`` fusiona los cambios de vuelta
   o ``cleanup_worktree()`` descarta el trabajo.

Esto permite que los flujos automatizados (autopilot) operen con red
de seguridad: si algo sale mal, se descarta el worktree sin afectar
al proyecto.
"""

import os
import re
import shutil
import subprocess
import sys
from typing import Optional, Tuple


# --- Constantes ---

# Directorio base para worktrees temporales. Se crea dentro del
# directorio del proyecto para mantener la localidad.
_WORKTREE_DIR = ".alfred-worktrees"

# Prefijo para ramas de worktree.
_BRANCH_PREFIX = "alfred/"


# --- Funciones auxiliares ---

def _run_git(
    args: list,
    cwd: Optional[str] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Ejecuta un comando git con captura de salida.

    Args:
        args: argumentos para git (sin el propio 'git').
        cwd: directorio de trabajo. Si es None, usa cwd.
        check: si True, lanza CalledProcessError en caso de fallo.

    Returns:
        Resultado del proceso.

    Raises:
        subprocess.CalledProcessError: si check=True y el comando falla.
    """
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=30,
    )


def _sanitize_branch_name(name: str) -> str:
    """Convierte un texto libre en un nombre de rama git valido.

    Reemplaza caracteres no permitidos por guiones, elimina guiones
    consecutivos y trunca a 50 caracteres.

    Args:
        name: texto libre para el nombre de rama.

    Returns:
        Nombre de rama sanitizado.
    """
    # Reemplazar espacios y caracteres especiales por guiones
    sanitized = re.sub(r"[^a-zA-Z0-9\-_/]", "-", name.lower())
    # Eliminar guiones consecutivos
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    # Eliminar guiones al inicio y final
    sanitized = sanitized.strip("-")
    # Truncar
    return sanitized[:50] if sanitized else "work"


def is_git_repo(project_dir: Optional[str] = None) -> bool:
    """Comprueba si el directorio es un repositorio git.

    Args:
        project_dir: directorio a comprobar. Si es None, usa cwd.

    Returns:
        True si es un repositorio git.
    """
    cwd = project_dir or os.getcwd()
    try:
        result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd, check=False)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_current_branch(project_dir: Optional[str] = None) -> Optional[str]:
    """Obtiene el nombre de la rama actual.

    Args:
        project_dir: directorio del proyecto.

    Returns:
        Nombre de la rama, o None si no se puede determinar.
    """
    cwd = project_dir or os.getcwd()
    try:
        result = _run_git(["branch", "--show-current"], cwd=cwd, check=False)
        if result.returncode == 0:
            return result.stdout.strip() or None
    except subprocess.TimeoutExpired:
        print(
            "[Alfred Dev] Aviso: git branch --show-current excedio el "
            "timeout. Puede haber un index.lock huerfano.",
            file=sys.stderr,
        )
    except FileNotFoundError:
        pass
    return None


def has_uncommitted_changes(project_dir: Optional[str] = None) -> bool:
    """Comprueba si hay cambios sin commitear en el repositorio.

    Args:
        project_dir: directorio del proyecto.

    Returns:
        True si hay cambios sin commitear (staged o unstaged).
    """
    cwd = project_dir or os.getcwd()
    try:
        result = _run_git(["status", "--porcelain"], cwd=cwd, check=False)
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True  # Asumir que si para evitar perdida de datos


# --- Gestion de worktrees ---

def create_worktree(
    description: str,
    flow_type: str = "feature",
    project_dir: Optional[str] = None,
) -> Tuple[str, str]:
    """Crea un git worktree aislado para trabajo seguro.

    Genera una rama nueva con prefijo ``alfred/`` derivada de la rama
    actual y crea un worktree en un subdirectorio del proyecto.

    Args:
        description: descripcion breve del trabajo (se usa para nombrar
            la rama).
        flow_type: tipo de flujo (feature, fix). Se usa como prefijo
            de la rama junto con ``alfred/``.
        project_dir: directorio del proyecto. Si es None, usa cwd.

    Returns:
        Tupla (worktree_path, branch_name) con la ruta del worktree
        y el nombre de la rama creada.

    Raises:
        RuntimeError: si no es un repositorio git, hay cambios sin
            commitear o no se pudo crear el worktree.
    """
    cwd = project_dir or os.getcwd()

    if not is_git_repo(cwd):
        raise RuntimeError(
            "El directorio actual no es un repositorio git. "
            "Los worktrees requieren un repositorio git inicializado."
        )

    if has_uncommitted_changes(cwd):
        raise RuntimeError(
            "Hay cambios sin commitear en el repositorio. "
            "Haz commit o stash antes de crear un worktree."
        )

    # Generar nombre de rama
    branch_suffix = _sanitize_branch_name(description)
    branch_name = f"{_BRANCH_PREFIX}{flow_type}/{branch_suffix}"

    # Crear directorio de worktrees si no existe
    worktrees_base = os.path.join(cwd, _WORKTREE_DIR)
    os.makedirs(worktrees_base, exist_ok=True)

    # Ruta del worktree
    worktree_dir = os.path.join(worktrees_base, branch_suffix)

    # Limpiar si existe un worktree previo con el mismo nombre
    if os.path.exists(worktree_dir):
        cleanup_worktree(worktree_dir, project_dir=cwd)

    # Crear el worktree con rama nueva
    try:
        _run_git(
            ["worktree", "add", "-b", branch_name, worktree_dir],
            cwd=cwd,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"No se pudo crear el worktree: {e.stderr.strip()}"
        ) from e

    return worktree_dir, branch_name


def merge_worktree(
    worktree_path: str,
    branch_name: str,
    project_dir: Optional[str] = None,
    delete_after: bool = True,
) -> bool:
    """Fusiona los cambios del worktree de vuelta a la rama principal.

    Realiza un merge fast-forward si es posible. Si no, intenta un
    merge normal. Si hay conflictos, aborta el merge y devuelve False.

    Args:
        worktree_path: ruta del worktree a fusionar.
        branch_name: nombre de la rama del worktree.
        project_dir: directorio del proyecto principal.
        delete_after: si True, limpia el worktree despues del merge.

    Returns:
        True si el merge fue exitoso, False si hubo conflictos.
    """
    cwd = project_dir or os.getcwd()

    # Intentar merge
    result = _run_git(
        ["merge", branch_name, "--no-edit"],
        cwd=cwd,
        check=False,
    )

    if result.returncode != 0:
        # Abortar si hay conflictos
        _run_git(["merge", "--abort"], cwd=cwd, check=False)
        return False

    # Limpiar
    if delete_after:
        cleanup_worktree(worktree_path, project_dir=cwd)
        # Eliminar la rama local
        _run_git(
            ["branch", "-d", branch_name],
            cwd=cwd,
            check=False,
        )

    return True


def cleanup_worktree(
    worktree_path: str,
    project_dir: Optional[str] = None,
) -> None:
    """Elimina un worktree y su directorio.

    Primero intenta la eliminacion limpia via ``git worktree remove``.
    Si falla (por ejemplo, por cambios sin commitear), fuerza la
    eliminacion.

    Args:
        worktree_path: ruta del worktree a eliminar.
        project_dir: directorio del proyecto principal.
    """
    cwd = project_dir or os.getcwd()

    # Intentar eliminacion limpia
    result = _run_git(
        ["worktree", "remove", worktree_path],
        cwd=cwd,
        check=False,
    )

    if result.returncode != 0:
        print(
            f"[Alfred Dev] Aviso: eliminacion limpia del worktree fallo "
            f"({result.stderr.strip()}). Intentando forzar...",
            file=sys.stderr,
        )
        result = _run_git(
            ["worktree", "remove", "--force", worktree_path],
            cwd=cwd,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"[Alfred Dev] Aviso: eliminacion forzada del worktree "
                f"tambien fallo: {result.stderr.strip()}",
                file=sys.stderr,
            )

    # Si el directorio sigue existiendo, eliminarlo manualmente
    if os.path.exists(worktree_path):
        try:
            shutil.rmtree(worktree_path)
        except OSError as e:
            print(
                f"[Alfred Dev] Error: no se pudo eliminar el directorio "
                f"del worktree '{worktree_path}': {e}. Puede requerir "
                f"eliminacion manual.",
                file=sys.stderr,
            )

    # Limpiar referencias huerfanas
    _run_git(["worktree", "prune"], cwd=cwd, check=False)


def list_worktrees(project_dir: Optional[str] = None) -> list:
    """Lista los worktrees activos del proyecto.

    Args:
        project_dir: directorio del proyecto.

    Returns:
        Lista de diccionarios con ``path``, ``branch`` y ``commit``
        de cada worktree.
    """
    cwd = project_dir or os.getcwd()

    try:
        result = _run_git(
            ["worktree", "list", "--porcelain"],
            cwd=cwd,
            check=False,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    worktrees = []
    current = {}

    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            if current:
                worktrees.append(current)
                current = {}
            continue

        if line.startswith("worktree "):
            current["path"] = line[9:]
        elif line.startswith("HEAD "):
            current["commit"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[7:]

    if current:
        worktrees.append(current)

    return worktrees
