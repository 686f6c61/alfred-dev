#!/usr/bin/env python3
"""
Cargador de configuración del plugin Alfred Dev.

Este módulo se encarga de leer la configuración del usuario desde un fichero
.local.md con frontmatter YAML, detectar automáticamente el stack tecnológico
del proyecto y fusionar todo con unos valores por defecto sensatos.

El diseño busca funcionar sin dependencias externas: incluye un parser YAML
básico como fallback para entornos donde PyYAML no esté disponible.

Funciones públicas:
    - load_config(path): carga y fusiona configuración desde un fichero .local.md
    - detect_stack(project_dir): detecta runtime, lenguaje, framework y ORM
"""

import json
import os
import re
import copy
import sys
from typing import Any, Dict, List, Optional, Tuple

# Se intenta importar PyYAML; si no está disponible, se usa el parser básico
try:
    import yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# --- Configuración por defecto ---
# Estos valores representan el comportamiento base del plugin cuando el usuario
# no ha definido ninguna preferencia. Cada sección controla un aspecto distinto:
#
# - autonomía: cuánto puede decidir el plugin por su cuenta
# - proyecto: metadatos del proyecto (se rellenan con detect_stack)
# - compliance: reglas de cumplimiento y estilo
# - integraciones: servicios externos habilitados
# - personalidad: tono y nivel de sarcasmo del agente
# - notas: texto libre del usuario con preferencias adicionales

DEFAULT_CONFIG = {
    "autonomia": {
        "producto": "interactivo",
        "seguridad": "autónomo",
        "refactor": "interactivo",
        "docs": "autónomo",
        "tests": "autónomo",
    },
    "proyecto": {
        "runtime": "desconocido",
        "lenguaje": "desconocido",
        "framework": "desconocido",
        "orm": "ninguno",
        "test_runner": "desconocido",
        "bundler": "desconocido",
    },
    "compliance": {
        "estilo": "auto",
        "lint": True,
        "format_on_save": True,
    },
    "integraciones": {
        "git": True,
        "ci": False,
        "deploy": False,
    },
    "personalidad": {
        "nivel_sarcasmo": 3,
        "verbosidad": "normal",
        "idioma": "es",
    },
    # Agentes opcionales: predefinidos que el usuario activa según su proyecto.
    # Todos desactivados por defecto; se activan con /alfred config o por
    # descubrimiento contextual al iniciar el plugin en un proyecto nuevo.
    "agentes_opcionales": {
        "data-engineer": False,
        "ux-reviewer": False,
        "performance-engineer": False,
        "github-manager": False,
        "seo-specialist": False,
        "copywriter": False,
        "librarian": False,
    },
    "notas": "",
}


def load_config(path):
    """
    Carga la configuración del plugin desde un fichero .local.md.

    El fichero utiliza frontmatter YAML (delimitado por ---) para los valores
    de configuración y el cuerpo Markdown para notas en texto libre. Si el
    fichero no existe o no se puede leer, se devuelven los valores por defecto.

    La fusión es recursiva: los valores del fichero sobreescriben solo las
    claves que definen, manteniendo el resto de los defaults intactos.

    Args:
        path: ruta absoluta o relativa al fichero de configuración.

    Returns:
        dict con la configuración fusionada. Siempre contiene todas las claves
        de DEFAULT_CONFIG aunque el fichero no defina ninguna.

    Ejemplo:
        >>> config = load_config("/proyecto/.dev-vago.local.md")
        >>> config["autonomia"]["producto"]
        'interactivo'
    """
    # Se parte siempre de una copia profunda de los defaults para no mutar
    # el diccionario global entre llamadas
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not os.path.isfile(path):
        return config

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer '{path}': {e}. "
            f"Se usarán los valores por defecto.",
            file=sys.stderr,
        )
        return config

    frontmatter, body = _parse_frontmatter(content)

    if frontmatter:
        parsed = _parse_yaml(frontmatter)
        if isinstance(parsed, dict):
            config = _deep_merge(config, parsed)
        elif parsed is not None:
            print(
                f"[Alfred Dev] Aviso: el frontmatter de '{path}' no es un diccionario. "
                f"Se ignorará la configuración del fichero.",
                file=sys.stderr,
            )

    # Se extraen las notas del cuerpo Markdown.
    # Se busca cualquier sección cuyo título contenga "Notas" (h1-h6).
    # Todo el contenido desde esa cabecera hasta la siguiente cabecera
    # del mismo nivel o hasta el final del documento se considera notas.
    notas = _extract_notes(body)
    if notas:
        config["notas"] = notas

    return config


def detect_stack(project_dir):
    """
    Detecta el stack tecnológico de un proyecto analizando ficheros clave.

    Examina la presencia de ficheros como package.json, tsconfig.json,
    pyproject.toml, Cargo.toml, go.mod, etc. para inferir el runtime,
    lenguaje, framework y ORM del proyecto.

    La detección de frameworks y ORMs se hace leyendo las dependencias
    declaradas en los manifiestos del proyecto (package.json para Node,
    pyproject.toml para Python, etc.).

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        dict con las claves: runtime, lenguaje, framework, orm, test_runner,
        bundler. Los valores no detectados se devuelven como 'desconocido'
        o 'ninguno' según corresponda.

    Ejemplo:
        >>> stack = detect_stack("/mi-proyecto-next")
        >>> stack["framework"]
        'next'
    """
    stack = {
        "runtime": "desconocido",
        "lenguaje": "desconocido",
        "framework": "desconocido",
        "orm": "ninguno",
        "test_runner": "desconocido",
        "bundler": "desconocido",
    }

    # --- Detección de runtime y lenguaje ---
    # El orden importa: se comprueba primero lo más específico.
    # Si hay package.json es un proyecto Node; la presencia de tsconfig.json
    # lo eleva a TypeScript.

    has_package_json = os.path.isfile(os.path.join(project_dir, "package.json"))
    has_tsconfig = os.path.isfile(os.path.join(project_dir, "tsconfig.json"))
    has_pyproject = os.path.isfile(os.path.join(project_dir, "pyproject.toml"))
    has_setup_py = os.path.isfile(os.path.join(project_dir, "setup.py"))
    has_requirements = os.path.isfile(os.path.join(project_dir, "requirements.txt"))
    has_cargo = os.path.isfile(os.path.join(project_dir, "Cargo.toml"))
    has_go_mod = os.path.isfile(os.path.join(project_dir, "go.mod"))
    has_gemfile = os.path.isfile(os.path.join(project_dir, "Gemfile"))
    has_mix = os.path.isfile(os.path.join(project_dir, "mix.exs"))

    if has_package_json:
        stack["runtime"] = "node"
        stack["lenguaje"] = "typescript" if has_tsconfig else "javascript"
        _detect_node_details(project_dir, stack)
    elif has_pyproject or has_setup_py or has_requirements:
        stack["runtime"] = "python"
        stack["lenguaje"] = "python"
        _detect_python_details(project_dir, stack)
    elif has_cargo:
        stack["runtime"] = "rust"
        stack["lenguaje"] = "rust"
    elif has_go_mod:
        stack["runtime"] = "go"
        stack["lenguaje"] = "go"
    elif has_gemfile:
        stack["runtime"] = "ruby"
        stack["lenguaje"] = "ruby"
    elif has_mix:
        stack["runtime"] = "elixir"
        stack["lenguaje"] = "elixir"

    return stack


# --- Funciones internas ---


def _find_first_match(candidates, deps):
    """
    Busca la primera coincidencia entre una lista de candidatos y un conjunto de dependencias.

    Recorre los candidatos en orden y devuelve el primero que aparezca como
    clave en el diccionario/conjunto de dependencias. Se usa para detectar
    frameworks, ORMs, test runners y bundlers por prioridad.

    Args:
        candidates: lista de nombres de paquetes a buscar, en orden de prioridad.
        deps: diccionario o conjunto de dependencias donde buscar.

    Returns:
        str con el nombre del paquete encontrado, o None si no hay coincidencia.
    """
    for candidate in candidates:
        if candidate in deps:
            return candidate
    return None


def _normalize_scoped_package(name):
    """
    Normaliza un nombre de paquete con scope (@org/paquete) a su forma base.

    Elimina el prefijo '@' y se queda con la parte del scope (sin el nombre
    del sub-paquete). Por ejemplo: '@nestjs/core' -> 'nestjs', '@prisma/client' -> 'prisma'.
    Los paquetes sin scope se devuelven tal cual.

    Args:
        name: nombre del paquete npm.

    Returns:
        str con el nombre normalizado.
    """
    if name.startswith("@"):
        return name.replace("@", "").split("/")[0]
    return name


def _parse_frontmatter(content):
    """
    Extrae el frontmatter YAML y el cuerpo Markdown de un texto.

    El frontmatter debe estar delimitado por líneas que contengan
    exactamente '---'. El primer delimitador debe ser la primera línea
    no vacía del documento.

    Args:
        content: texto completo del fichero.

    Returns:
        tupla (frontmatter_str, body_str). Si no hay frontmatter,
        frontmatter_str será una cadena vacía.
    """
    # Se busca el patrón ---\n...\n--- al principio del contenido.
    # El grupo central usa .*? (lazy) para detenerse en el primer cierre ---.
    match = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)", content, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return "", content


def _deep_merge(base, override):
    """
    Fusiona dos diccionarios de forma recursiva.

    Los valores del diccionario 'override' sobreescriben los de 'base'.
    Cuando ambos valores son diccionarios, se fusionan recursivamente
    en lugar de reemplazar el diccionario completo. Esto permite que el
    usuario defina solo las claves que quiere cambiar sin perder los
    valores por defecto del resto.

    Args:
        base: diccionario base (se copia, no se muta).
        override: diccionario con los valores que sobreescriben.

    Returns:
        dict nuevo con la fusión de ambos.

    Ejemplo:
        >>> _deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"x": 99}})
        {'a': {'x': 99, 'y': 2}}
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _parse_yaml(text):
    """
    Parsea un texto YAML y devuelve un diccionario.

    Intenta usar PyYAML si está disponible. En caso contrario, recurre
    a un parser básico que soporta el subconjunto de YAML necesario
    para la configuración del plugin: diccionarios anidados con valores
    escalares (strings, números, booleanos).

    El parser básico no soporta listas, anclas, aliases ni otros
    constructos avanzados de YAML. Para configuraciones complejas
    se recomienda instalar PyYAML.

    Args:
        text: cadena con contenido YAML.

    Returns:
        dict con los valores parseados, o dict vacío si el parseo falla.
    """
    if _HAS_YAML:
        try:
            result = yaml.safe_load(text)
            if not isinstance(result, dict):
                print(
                    "[Alfred Dev] Aviso: el frontmatter YAML no es un diccionario. "
                    "Se ignorará la configuración del fichero.",
                    file=sys.stderr,
                )
                return {}
            return result
        except yaml.YAMLError as e:
            print(
                f"[Alfred Dev] Error de sintaxis en el frontmatter YAML: {e}. "
                f"Se ignorará la configuración del fichero.",
                file=sys.stderr,
            )
            return {}

    return _basic_yaml_parse(text)


def _basic_yaml_parse(text):
    """
    Parser YAML minimalista sin dependencias externas.

    Soporta el subconjunto necesario para la configuración del plugin:
    - Pares clave: valor
    - Anidamiento por indentación (espacios)
    - Valores escalares: strings, enteros, floats, booleanos, null

    No soporta listas, strings multilínea, anclas ni aliases. Esto es
    un fallback para entornos sin PyYAML; en producción se recomienda
    tener PyYAML instalado.

    Args:
        text: cadena con contenido YAML básico.

    Returns:
        dict con los valores parseados.
    """
    result = {}
    # Pila para rastrear el nivel de anidamiento actual.
    # Cada elemento es (indent_level, dict_referencia)
    stack = [(0, result)]

    for line in text.split("\n"):
        # Se ignoran líneas vacías y comentarios
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Se calcula la indentación para determinar el nivel
        indent = len(line) - len(line.lstrip())

        # Se busca el patrón clave: valor
        match = re.match(r"^(\w[\w\-]*):\s*(.*)", stripped)
        if not match:
            continue

        key = match.group(1)
        raw_value = match.group(2).strip()

        # Se retrocede en la pila hasta encontrar el padre correcto
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        parent = stack[-1][1]

        if raw_value:
            # Es un par clave: valor escalar
            parent[key] = _coerce_yaml_value(raw_value)
        else:
            # Es una clave que abre un diccionario anidado
            new_dict = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))

    return result


def _coerce_yaml_value(value):
    """
    Convierte un valor YAML en cadena al tipo Python correspondiente.

    Reglas de conversión:
    - 'true'/'false' (case insensitive) -> bool
    - 'null'/'~' -> None
    - Números enteros -> int
    - Números decimales -> float
    - Strings entre comillas -> string sin comillas
    - Todo lo demás -> string tal cual

    Args:
        value: cadena con el valor YAML crudo.

    Returns:
        valor Python convertido al tipo apropiado.
    """
    # Booleanos
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Null
    if value.lower() in ("null", "~"):
        return None

    # Strings entrecomillados: se eliminan las comillas externas
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    # Enteros
    try:
        return int(value)
    except ValueError:
        pass

    # Floats
    try:
        return float(value)
    except ValueError:
        pass

    return value


def _extract_notes(body):
    """
    Extrae el contenido de la sección de notas del cuerpo Markdown.

    Busca una cabecera (h1-h6) cuyo texto contenga 'Notas' y extrae
    todo el contenido hasta la siguiente cabecera del mismo nivel o
    hasta el final del documento.

    Args:
        body: texto Markdown (sin frontmatter).

    Returns:
        str con el contenido de la sección de notas, o cadena vacía
        si no se encuentra ninguna sección con ese título.
    """
    # Se busca una línea que empiece con # y contenga "Notas".
    # Se usa [^\n]*? (lazy) para evitar backtracking excesivo en líneas largas.
    pattern = re.compile(r"^(#{1,6})\s+[^\n]*?[Nn]otas[^\n]*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""

    header_level = len(match.group(1))
    start = match.end()

    # Se busca la siguiente cabecera del mismo nivel o superior
    next_header = re.compile(
        r"^#{1," + str(header_level) + r"}\s+", re.MULTILINE
    )
    next_match = next_header.search(body, start)

    if next_match:
        notes_text = body[start : next_match.start()]
    else:
        notes_text = body[start:]

    return notes_text.strip()


def _detect_node_details(project_dir, stack):
    """
    Detecta framework, ORM, test runner y bundler en un proyecto Node.

    Lee el package.json y analiza tanto 'dependencies' como
    'devDependencies' para identificar las herramientas del proyecto.

    Args:
        project_dir: ruta al directorio del proyecto.
        stack: diccionario de stack que se modifica in-place.
    """
    pkg_path = os.path.join(project_dir, "package.json")
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, IOError, json.JSONDecodeError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer '{pkg_path}': {e}. "
            f"La detección de framework será incompleta.",
            file=sys.stderr,
        )
        return

    # Se unifican todas las dependencias para buscar en un solo paso
    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }

    # Frameworks: se comprueba del más específico al más genérico.
    # El orden determina la prioridad cuando hay varios presentes.
    frameworks = [
        "next", "nuxt", "astro", "remix", "gatsby", "svelte",
        "solid-js", "qwik", "hono", "express", "fastify", "koa",
        "nest", "@nestjs/core", "vue", "react", "angular", "@angular/core",
    ]

    found = _find_first_match(frameworks, all_deps)
    if found:
        stack["framework"] = _normalize_scoped_package(found)

    # ORMs y query builders
    orms = [
        "drizzle-orm", "prisma", "@prisma/client", "typeorm",
        "sequelize", "knex", "mongoose", "mikro-orm", "@mikro-orm/core",
    ]

    found = _find_first_match(orms, all_deps)
    if found:
        # Se simplifica: @prisma/client -> prisma, drizzle-orm -> drizzle
        name = _normalize_scoped_package(found)
        stack["orm"] = name.replace("-orm", "").replace("-client", "")

    # Test runners
    test_runners = [
        "vitest", "jest", "mocha", "ava", "tap", "playwright", "cypress",
    ]

    found = _find_first_match(test_runners, all_deps)
    if found:
        stack["test_runner"] = found

    # Bundlers
    bundlers = [
        "vite", "webpack", "esbuild", "rollup",
        "parcel", "turbopack", "tsup", "unbuild",
    ]

    found = _find_first_match(bundlers, all_deps)
    if found:
        stack["bundler"] = found


def _detect_python_details(project_dir, stack):
    """
    Detecta framework, ORM y test runner en un proyecto Python.

    Lee pyproject.toml (de forma básica, sin parser TOML completo)
    y requirements.txt para identificar las dependencias.

    Args:
        project_dir: ruta al directorio del proyecto.
        stack: diccionario de stack que se modifica in-place.
    """
    deps_text = ""

    # Se intenta leer pyproject.toml para extraer dependencias
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    if os.path.isfile(pyproject_path):
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                deps_text += f.read()
        except (OSError, IOError) as e:
            print(
                f"[Alfred Dev] Aviso: no se pudo leer '{pyproject_path}': {e}. "
                f"La detección de framework será incompleta.",
                file=sys.stderr,
            )

    # Se complementa con requirements.txt si existe
    reqs_path = os.path.join(project_dir, "requirements.txt")
    if os.path.isfile(reqs_path):
        try:
            with open(reqs_path, "r", encoding="utf-8") as f:
                deps_text += "\n" + f.read()
        except (OSError, IOError) as e:
            print(
                f"[Alfred Dev] Aviso: no se pudo leer '{reqs_path}': {e}. "
                f"La detección de framework será incompleta.",
                file=sys.stderr,
            )

    deps_lower = deps_text.lower()

    # Frameworks Python (orden = prioridad)
    py_frameworks = [
        "fastapi", "django", "flask", "starlette",
        "litestar", "sanic", "tornado", "aiohttp",
    ]

    found = _find_first_match(py_frameworks, deps_lower)
    if found:
        stack["framework"] = found

    # ORMs Python: se usan tuplas solo cuando la clave de busqueda
    # difiere del nombre que se asigna (django -> django-orm)
    py_orms = [
        ("sqlalchemy", "sqlalchemy"),
        ("sqlmodel", "sqlmodel"),
        ("django", "django-orm"),
        ("tortoise", "tortoise"),
        ("peewee", "peewee"),
        ("pony", "pony"),
    ]

    for dep_name, orm_name in py_orms:
        if dep_name in deps_lower:
            stack["orm"] = orm_name
            break

    # Test runners Python
    py_test_runners = ["pytest", "unittest", "nose"]

    found = _find_first_match(py_test_runners, deps_lower)
    if found:
        stack["test_runner"] = found


# --- Descubrimiento contextual de agentes opcionales ----------------------

# Frameworks que implican una interfaz de usuario visible para el visitante.
# Se usa para sugerir ux-reviewer y seo-specialist.
_FRONTEND_FRAMEWORKS = {
    "next", "nuxt", "astro", "remix", "gatsby", "svelte",
    "solid-js", "qwik", "vue", "react", "angular",
}

# Palabras clave que vinculan tareas del usuario con agentes opcionales.
# Cada agente tiene una lista de keywords (se buscan con \b word boundary
# en la descripción de la tarea) y un peso_base que determina la puntuación
# mínima cuando hay al menos una coincidencia. Esta tabla es el corazón de
# la composición dinámica de equipo: permite que Alfred sugiera agentes sin
# que el usuario tenga que conocerlos de antemano.
TASK_KEYWORDS: Dict[str, Dict[str, Any]] = {
    "data-engineer": {
        "keywords": [
            "bd", "base de datos", "database", "migracion", "migración",
            "esquema", "orm", "prisma", "sql", "mysql", "postgres",
            "postgresql", "mongodb", "redis", "pagos", "pago",
            "facturacion", "facturación", "stripe", "tabla", "tablas",
            "modelo de datos", "relacion", "relación",
        ],
        "peso_base": 0.6,
    },
    "ux-reviewer": {
        "keywords": [
            "interfaz", "ui", "ux", "formulario", "form", "accesibilidad",
            "responsive", "onboarding", "flujo de usuario", "checkout",
            "navegacion", "navegación", "componente", "componentes",
            "pantalla", "vista", "layout", "diseño", "experiencia",
        ],
        "peso_base": 0.6,
    },
    "performance-engineer": {
        "keywords": [
            "rendimiento", "lento", "lentitud", "optimizar", "optimización",
            "cache", "caché", "latencia", "benchmark", "bundle", "profiling",
            "memoria", "cpu", "carga", "escalabilidad", "throughput",
        ],
        "peso_base": 0.7,
    },
    "github-manager": {
        "keywords": [
            "release", "pr", "pull request", "deploy", "desplegar",
            "publicar", "tag", "version", "versión", "changelog",
            "rama", "branch", "merge", "ci", "cd", "pipeline",
        ],
        "peso_base": 0.5,
    },
    "seo-specialist": {
        "keywords": [
            "seo", "meta tags", "lighthouse", "posicionamiento", "sitemap",
            "json-ld", "schema", "indexacion", "indexación", "crawl",
            "landing", "organico", "orgánico", "buscador", "google",
        ],
        "peso_base": 0.7,
    },
    "copywriter": {
        "keywords": [
            "textos", "copy", "landing", "cta", "tono", "redaccion",
            "redacción", "marketing", "contenido", "mensaje", "comunicacion",
            "comunicación", "email", "newsletter", "blog", "articulo",
        ],
        "peso_base": 0.6,
    },
    "librarian": {
        "keywords": [
            "historial", "decision", "decisión", "por que", "por qué",
            "antecedente", "contexto historico", "contexto histórico",
            "arquitectura anterior", "que se decidio", "qué se decidió",
        ],
        "peso_base": 0.5,
    },
}


def _has_git_remote(project_dir):
    """Comprueba si el proyecto tiene un remote Git configurado.

    Lee directamente el fichero .git/config para evitar dependencias de
    subprocesos. Busca la presencia de cualquier sección [remote "..."].

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si hay al menos un remote configurado, False en caso contrario.
    """
    git_config = os.path.join(project_dir, ".git", "config")
    if not os.path.isfile(git_config):
        return False
    try:
        with open(git_config, "r", encoding="utf-8") as f:
            return '[remote "' in f.read()
    except (OSError, IOError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer .git/config: {e}",
            file=sys.stderr,
        )
        return False


def _has_public_html(project_dir):
    """Detecta si el proyecto tiene contenido web público.

    Busca indicadores comunes de sitios web estáticos o landing pages:
    ficheros HTML en la raíz o en directorios típicos (public/, site/, dist/).

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si se detectan ficheros HTML públicos, False en caso contrario.
    """
    # Ficheros HTML directos en la raíz
    for name in ("index.html", "index.htm"):
        if os.path.isfile(os.path.join(project_dir, name)):
            return True

    # Directorios típicos de contenido público
    for dirname in ("public", "site", "dist", "docs"):
        dirpath = os.path.join(project_dir, dirname)
        if os.path.isdir(dirpath):
            for entry in os.listdir(dirpath):
                if entry.endswith((".html", ".htm")):
                    return True

    return False


def _count_source_files(project_dir):
    """Cuenta ficheros de código fuente en el proyecto (no recursivo profundo).

    Recorre hasta 2 niveles de profundidad para evitar latencia excesiva
    en proyectos con node_modules o directorios de dependencias grandes.
    Ignora directorios de dependencias y artefactos conocidos.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        int con el número de ficheros de código fuente encontrados.
    """
    source_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go",
        ".rb", ".ex", ".exs", ".java", ".kt", ".swift", ".cs",
        ".vue", ".svelte", ".astro", ".php", ".c", ".cpp", ".h",
    }
    skip_dirs = {
        "node_modules", ".git", "dist", "build", ".next", "__pycache__",
        ".venv", "venv", "vendor", "target", ".cargo",
    }
    count = 0
    scan_errors = []
    try:
        for entry in os.scandir(project_dir):
            if entry.is_file() and os.path.splitext(entry.name)[1] in source_extensions:
                count += 1
            elif entry.is_dir() and entry.name not in skip_dirs:
                try:
                    for sub in os.scandir(entry.path):
                        if sub.is_file() and os.path.splitext(sub.name)[1] in source_extensions:
                            count += 1
                        elif sub.is_dir() and sub.name not in skip_dirs:
                            try:
                                for deep in os.scandir(sub.path):
                                    if deep.is_file() and os.path.splitext(deep.name)[1] in source_extensions:
                                        count += 1
                            except (OSError, PermissionError) as e:
                                scan_errors.append(str(e))
                except (OSError, PermissionError) as e:
                    scan_errors.append(str(e))
    except (OSError, PermissionError) as e:
        scan_errors.append(str(e))
    if scan_errors:
        print(
            f"[Alfred Dev] Aviso: no se pudieron escanear {len(scan_errors)} "
            f"directorios. El conteo de ficheros puede ser parcial.",
            file=sys.stderr,
        )
    return count


def _is_memory_enabled(project_dir):
    """Comprueba si la memoria persistente está habilitada en la configuración local.

    Busca el fichero ``alfred-dev.local.md`` en el directorio ``.claude``
    del proyecto y verifica que contenga la sección ``memoria:`` con
    ``enabled: true``. El patrón es el mismo que usa ``hooks/memory-capture.py``.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si la memoria está habilitada, False en caso contrario.
    """
    config_path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, FileNotFoundError):
        return False

    pattern = r"memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true"
    return bool(re.search(pattern, content))


def suggest_optional_agents(project_dir, current_config=None):
    """Analiza el proyecto y sugiere agentes opcionales relevantes.

    Examina el stack tecnológico, la presencia de base de datos, frontend,
    contenido web público, remote Git y tamaño del proyecto para recomendar
    qué agentes opcionales podrían ser útiles.

    Solo sugiere agentes que no estén ya activados en la configuración actual.

    Args:
        project_dir: ruta al directorio raíz del proyecto.
        current_config: diccionario de configuración actual (opcional).
            Si se proporciona, se filtran los agentes ya activos.

    Returns:
        Lista de tuplas (nombre_agente, razon) con las sugerencias.
        Cada tupla contiene el identificador del agente y una cadena
        explicando por qué se sugiere.

    Ejemplo:
        >>> suggestions = suggest_optional_agents("/mi-proyecto-next")
        >>> suggestions
        [('ux-reviewer', 'Proyecto con frontend Next.js'),
         ('github-manager', 'Repositorio con remote en GitHub')]
    """
    if current_config is None:
        current_config = copy.deepcopy(DEFAULT_CONFIG)

    active = current_config.get("agentes_opcionales", {})
    stack = detect_stack(project_dir)
    suggestions = []

    # Base de datos / ORM → data-engineer
    if not active.get("data-engineer") and stack.get("orm", "ninguno") != "ninguno":
        suggestions.append((
            "data-engineer",
            f"Usas {stack['orm']} como ORM: te ayuda con esquemas, migraciones y queries"
        ))

    # Frontend → ux-reviewer
    framework = stack.get("framework", "desconocido")
    if not active.get("ux-reviewer") and framework in _FRONTEND_FRAMEWORKS:
        suggestions.append((
            "ux-reviewer",
            f"Proyecto con {framework}: revisa accesibilidad, usabilidad y flujos de usuario"
        ))

    # Contenido web público → seo-specialist, copywriter
    if _has_public_html(project_dir):
        if not active.get("seo-specialist"):
            suggestions.append((
                "seo-specialist",
                "Contenido web público detectado: optimiza SEO, meta tags y datos estructurados"
            ))
        if not active.get("copywriter"):
            suggestions.append((
                "copywriter",
                "Textos públicos detectados: mejora copys, CTAs y tono de comunicación"
            ))

    # Remote Git → github-manager
    if not active.get("github-manager") and _has_git_remote(project_dir):
        suggestions.append((
            "github-manager",
            "Repositorio con remote: gestiona PRs, releases, issues y configuración de repo"
        ))

    # Proyecto grande → performance-engineer
    if not active.get("performance-engineer") and _count_source_files(project_dir) > 50:
        suggestions.append((
            "performance-engineer",
            "Proyecto con más de 50 ficheros fuente: ayuda con profiling, benchmarks y optimización"
        ))

    # Memoria activa → librarian
    if not active.get("librarian") and _is_memory_enabled(project_dir):
        suggestions.append((
            "librarian",
            "Memoria persistente activa: consulta decisiones, historial y cronología del proyecto"
        ))

    return suggestions


# Límite de seguridad para la descripción de tarea. Las descripciones más
# largas se truncan con un aviso a stderr para evitar consumo excesivo de
# memoria durante el matching de keywords.
_MAX_TASK_DESCRIPTION_LENGTH = 10_000


def match_task_keywords(
    task_description: str,
    project_suggestions: Optional[List[Tuple[str, str]]] = None,
    active_config: Optional[Dict[str, bool]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Puntúa agentes opcionales según la descripción de una tarea del usuario.

    Analiza el texto libre de la tarea buscando keywords asociadas a cada
    agente opcional. Combina esa señal textual con el contexto del proyecto
    (sugerencias de ``suggest_optional_agents``) y la configuración activa
    para producir una puntuación compuesta que determina si el agente debe
    sugerirse al equipo dinámico.

    El algoritmo de puntuación funciona así:
        - **peso_base** se suma si al menos una keyword coincide.
        - **+0.1** adicional si coinciden 2 o más keywords.
        - **+0.4** si el agente aparece en ``project_suggestions``.
        - **+0.3** si el agente está activado en ``active_config``.
        - Un agente se marca como ``sugerido=True`` si su score >= 0.5.

    Args:
        task_description: texto libre que describe la tarea. Se acepta None
            (se trata como cadena vacía). Tipos no-str se convierten a cadena
            vacía con aviso a stderr. Se trunca a 10 000 caracteres con aviso.
        project_suggestions: lista de tuplas ``(nombre_agente, razon)``
            generada por ``suggest_optional_agents``. Opcional.
        active_config: diccionario ``{nombre_agente: bool}`` con los agentes
            ya activados en la configuración del usuario. Opcional.

    Returns:
        Diccionario con una entrada por cada agente de ``TASK_KEYWORDS``.
        Cada valor es un dict con las claves:
            - ``score`` (float): puntuación compuesta.
            - ``sugerido`` (bool): True si score >= 0.5.
            - ``razones`` (list[str]): explicaciones en castellano de cada
              componente que contribuyó a la puntuación.

    Ejemplo:
        >>> result = match_task_keywords("Hay que migrar la base de datos a Postgres")
        >>> result["data-engineer"]["sugerido"]
        True
        >>> result["data-engineer"]["score"]
        0.7
    """
    # --- Normalización de la entrada ---
    # Se acepta None explícitamente (caso de uso documentado). Tipos no-str
    # se tratan como cadena vacía pero emitiendo un aviso para facilitar
    # la depuración de bugs en el código llamante.
    if task_description is None:
        task_description = ""
    elif not isinstance(task_description, str):
        print(
            f"[Alfred Dev] Aviso: match_task_keywords recibió task_description "
            f"de tipo {type(task_description).__name__} en lugar de str. "
            f"Se tratará como cadena vacía.",
            file=sys.stderr,
        )
        task_description = ""

    # Truncar con aviso si supera el límite de seguridad.
    if len(task_description) > _MAX_TASK_DESCRIPTION_LENGTH:
        print(
            f"[Alfred Dev] Aviso: la descripción de la tarea tiene "
            f"{len(task_description)} caracteres y se truncará a "
            f"{_MAX_TASK_DESCRIPTION_LENGTH}. Las keywords al final del "
            f"texto no se analizarán.",
            file=sys.stderr,
        )
        task_description = task_description[:_MAX_TASK_DESCRIPTION_LENGTH]

    task_description = task_description.lower()

    # Se convierten las sugerencias de proyecto a un set para búsqueda O(1)
    project_agent_names = set()
    if project_suggestions:
        project_agent_names = {name for name, _reason in project_suggestions}

    if active_config is None:
        active_config = {}

    result: Dict[str, Dict[str, Any]] = {}

    for agent_name, agent_data in TASK_KEYWORDS.items():
        score = 0.0
        razones: List[str] = []

        # --- Señal textual: keywords encontradas ---
        keywords = agent_data["keywords"]
        peso_base = agent_data["peso_base"]

        matched_keywords = [
            kw for kw in keywords
            if re.search(r'\b' + re.escape(kw) + r'\b', task_description)
        ]
        match_count = len(matched_keywords)

        if match_count >= 1:
            score += peso_base
            razones.append(
                f"Keyword detectada en la tarea: {', '.join(matched_keywords[:3])}"
            )

        if match_count >= 2:
            score += 0.1
            razones.append("Coincidencia múltiple de keywords (+0.1)")

        # --- Señal de proyecto: suggest_optional_agents lo recomienda ---
        if agent_name in project_agent_names:
            score += 0.4
            razones.append("Sugerido por el análisis del proyecto (+0.4)")

        # --- Señal de configuración: ya activado por el usuario ---
        if active_config.get(agent_name):
            score += 0.3
            razones.append("Activado en la configuración del usuario (+0.3)")

        # Se redondea para evitar artefactos de coma flotante (0.6+0.1=0.7000...01)
        score = round(score, 2)

        result[agent_name] = {
            "score": score,
            "sugerido": score >= 0.5,
            "razones": razones,
        }

    return result
