#!/usr/bin/env python3
"""
Orquestador de flujos del plugin Alfred Dev.

Este módulo gestiona el ciclo de vida completo de los flujos de trabajo
(feature, fix, quick, spike, ship, audit). Cada flujo se compone de fases
secuenciales con gates de control que determinan si se puede avanzar
a la siguiente fase.

El orquestador se encarga de:
- Definir los flujos disponibles y sus fases.
- Crear y gestionar sesiones de trabajo.
- Evaluar las gates de cada fase para decidir si se aprueba el avance.
- Persistir y recuperar el estado de las sesiones en disco.
- Gestionar el loop iterativo dentro de cada fase (v0.4.0).
- Soportar el modo autopilot para ejecucion sin interrupcion (v0.4.0).

Arquitectura de gates:
    Las gates actúan como puntos de control entre fases. Su comportamiento
    depende del tipo definido en cada fase: las gates de tipo «usuario»
    requieren aprobación explícita; las «automático» se evalúan contra
    métricas objetivas como tests verdes o pipeline OK; las combinadas
    (ej. «automático+seguridad») acumulan ambas condiciones.

Loop iterativo (v0.4.0):
    Dentro de cada fase, los agentes pueden iterar hasta que los
    entregables esten completos o se alcance el maximo de iteraciones.
    El loop es interno a la fase: no avanza a la siguiente hasta que
    la gate se supere. Esto permite ciclos TDD (rojo-verde-refactor)
    y pasadas de QA repetidas sin intervencion manual.

Modo autopilot (v0.4.0):
    Cuando ``autopilot=True``, el flujo recorre todas las fases sin
    pedir aprobacion al usuario en las gates de tipo «usuario». Las
    gates automaticas y de seguridad siguen evaluandose normalmente.
    Solo se detiene si una gate automatica o de seguridad falla.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.optional_agents import get_optional_agent_names, get_optional_integrations

# --- Constantes de tipos de gate -------------------------------------------
# Se extraen como constantes para evitar la duplicación de literales
# y facilitar la validación centralizada.

GATE_USUARIO = "usuario"
GATE_AUTOMATICO = "automatico"
GATE_LIBRE = "libre"
GATE_USUARIO_SEGURIDAD = "usuario+seguridad"
GATE_AUTOMATICO_SEGURIDAD = "automatico+seguridad"

_KNOWN_GATE_TYPES = {
    GATE_LIBRE, GATE_USUARIO, GATE_AUTOMATICO,
    GATE_USUARIO_SEGURIDAD, GATE_AUTOMATICO_SEGURIDAD,
}

# --- Agentes opcionales conocidos -------------------------------------------
# Lista canónica de agentes opcionales del plugin. Se usa para validar la
# estructura del equipo de sesión en composición dinámica.

_KNOWN_OPTIONAL_AGENTS = frozenset(get_optional_agent_names())
_KNOWN_EQUIPO_SESSION_SOURCES = frozenset({
    "composicion_dinamica",
    "config_persistida",
})

# --- Definición de flujos ---------------------------------------------------
# Cada flujo describe una secuencia de fases que el orquestador recorre.
# Los agentes listados en cada fase son los responsables de ejecutarla.

FLOWS: Dict[str, Dict[str, Any]] = {
        "feature": {
        "nombre": "feature",
        "fases": [
            {
                "nombre": "producto",
                "agentes": ["product-owner"],
                "paralelo": False,
                "gate": "gate_producto",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Análisis de requisitos y definición del alcance "
                    "funcional de la nueva característica."
                ),
            },
            {
                "nombre": "estilo_visual",
                "agentes": ["selina"],
                "paralelo": False,
                "gate": "gate_estilo",
                "gate_tipo": GATE_USUARIO,
                "condicion": "tiene_frontend",
                "descripcion": (
                    "Definicion de la direccion de estilo visual "
                    "del producto con tres propuestas comparativas."
                ),
            },
            {
                "nombre": "arquitectura",
                "agentes": ["architect", "security-officer"],
                "paralelo": True,
                "gate": "gate_arquitectura",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": (
                    "Diseño técnico, elección de patrones y validación "
                    "de la propuesta arquitectónica con threat model."
                ),
            },
            {
                "nombre": "desarrollo",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_desarrollo",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Implementación del código siguiendo TDD estricto "
                    "con ciclos rojo-verde-refactor."
                ),
            },
            {
                "nombre": "calidad",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_calidad",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Revisión de calidad, ejecución de tests y "
                    "auditoría de seguridad en paralelo."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Generación de documentación técnica y de usuario "
                    "para la comunidad."
                ),
            },
            {
                "nombre": "entrega",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_entrega",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": (
                    "Preparación del entregable, changelog y "
                    "validación final antes del merge."
                ),
            },
        ],
    },
    "fix": {
        "nombre": "fix",
        "fases": [
            {
                "nombre": "diagnostico",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_diagnostico",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Identificación de la causa raíz del bug "
                    "mediante análisis de logs, trazas y reproducción."
                ),
            },
            {
                "nombre": "correccion",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_correccion",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Aplicación del fix con test de regresión "
                    "que demuestre que el bug queda resuelto."
                ),
            },
            {
                "nombre": "validacion",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Validación completa: tests de regresión, "
                    "suite existente y revisión de seguridad."
                ),
            },
        ],
    },
    "quick": {
        "nombre": "quick",
        "fases": [
            {
                "nombre": "ejecucion_acotada",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_ejecucion_acotada",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Implementación acotada para cambios pequeños, "
                    "locales y de bajo riesgo, con validación automática."
                ),
            },
            {
                "nombre": "validacion_rapida",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion_rapida",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Validación rápida del cambio sobre la superficie tocada: "
                    "regresión local, tests y revisión de seguridad."
                ),
            },
        ],
    },
    "spike": {
        "nombre": "spike",
        "fases": [
            {
                "nombre": "exploracion",
                "agentes": ["architect", "senior-dev"],
                "paralelo": True,
                "gate": "gate_exploracion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Investigación exploratoria: pruebas de concepto, "
                    "benchmarks y evaluación de alternativas."
                ),
            },
            {
                "nombre": "conclusiones",
                "agentes": ["architect"],
                "paralelo": False,
                "gate": "gate_conclusiones",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Consolidación de hallazgos en un informe "
                    "con recomendaciones accionables."
                ),
            },
        ],
    },
    "ship": {
        "nombre": "ship",
        "fases": [
            {
                "nombre": "auditoria_final",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_auditoria_final",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Auditoría completa de calidad y seguridad "
                    "antes de la release."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion_ship",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Actualización de la documentación de release, "
                    "changelog y guías de migración."
                ),
            },
            {
                "nombre": "empaquetado",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_empaquetado",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Generación del artefacto de release, "
                    "versionado semántico y etiquetado."
                ),
            },
            {
                "nombre": "despliegue",
                "agentes": ["devops-engineer"],
                "paralelo": False,
                "gate": "gate_despliegue",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "autopilot_force_user_confirmation": True,
                "descripcion": (
                    "Despliegue a producción con validación "
                    "post-deploy y rollback preparado."
                ),
            },
        ],
    },
    "audit": {
        "nombre": "audit",
        "fases": [
            {
                "nombre": "auditoria_paralela",
                "agentes": [
                    "qa-engineer",
                    "security-officer",
                    "architect",
                    "tech-writer",
                ],
                "paralelo": True,
                "gate": "gate_auditoria",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Auditoría completa del código en paralelo: "
                    "calidad, seguridad, arquitectura "
                    "y documentación."
                ),
            },
        ],
    },
}


# --- Integracion de agentes opcionales -------------------------------------
# Este mapa define en que fases puede participar cada agente opcional como
# refuerzo de los agentes de nucleo. La posicion indica si se ejecuta en
# paralelo con los de nucleo o de forma secuencial despues de ellos.
#
# El Bibliotecario no participa en flujos activos: es consultivo (via MCP)
# y no necesita integrarse en ninguna fase de ejecucion.

OPTIONAL_INTEGRATIONS: Dict[str, Dict[str, Any]] = get_optional_integrations()

# --- Evaluadores de condiciones de fase ---------------------------------------
# Mapa de condiciones declarativas a funciones evaluadoras.
# Cada condicion recibe el stack del proyecto y devuelve True si la fase debe
# ejecutarse. Se importa de forma perezosa (lazy) dentro de la funcion para
# evitar importaciones circulares con config_loader.

_PHASE_CONDITIONS: Optional[Dict[str, Any]] = None


def _get_phase_conditions() -> Dict[str, Any]:
    """Devuelve el mapa de condiciones, inicializandolo de forma perezosa."""
    global _PHASE_CONDITIONS
    if _PHASE_CONDITIONS is None:
        from core.config_loader import has_frontend  # noqa: PLC0415
        # "tiene_frontend" evalua config_loader.has_frontend(stack) para decidir
        # si la fase estilo_visual debe ejecutarse. La importacion es perezosa para
        # evitar importaciones circulares entre orchestrator y config_loader.
        _PHASE_CONDITIONS = {
            "tiene_frontend": has_frontend,
        }
    return _PHASE_CONDITIONS


def _advance_skipping_phases(
    session: Dict[str, Any],
    fases: List[Dict[str, Any]],
    siguiente: int,
    conditions: Dict[str, Any],
) -> int:
    """Avanza el índice saltando fases con condición no cumplida.

    Registra cada fase saltada en ``session["fases_completadas"]`` con
    resultado ``"saltada"``. Se detiene en la primera fase ejecutable
    (sin condición o condición cumplida) o cuando el stack no está
    disponible para evaluar la condición.

    Args:
        session: estado de la sesión (se muta para registrar fases saltadas).
        fases: lista de fases del flujo.
        siguiente: índice de partida para la búsqueda.
        conditions: mapa de nombre de condición a función evaluadora.

    Returns:
        Índice de la siguiente fase ejecutable.
    """
    stack = session.get("stack")
    while siguiente < len(fases):
        fase_siguiente = fases[siguiente]
        condicion = fase_siguiente.get("condicion")
        if not condicion or condicion not in conditions:
            break
        if stack is None:
            # Sin stack, no se puede evaluar la condición: ejecutar la fase
            break
        if conditions[condicion](stack):
            break
        # Condición no cumplida: registrar fase saltada y continuar
        session["fases_completadas"].append({
            "nombre": fase_siguiente["nombre"],
            "resultado": "saltada",
            "artefactos": [],
            "completada_en": datetime.now(timezone.utc).isoformat(),
            "iteraciones": 0,
        })
        siguiente += 1
    return siguiente


def get_effective_agents(
    phase_name: str,
    active_optionals: Optional[Dict[str, bool]] = None,
) -> Dict[str, List[str]]:
    """Calcula los agentes que participan en una fase, incluyendo opcionales activos.

    Fusiona los agentes de nucleo definidos en FLOWS con los agentes opcionales
    activos que tienen integracion en esa fase. El resultado distingue entre
    agentes en paralelo y secuenciales para que los commands sepan como lanzarlos.

    Args:
        phase_name: nombre de la fase (ej. "arquitectura", "calidad").
        active_optionals: diccionario con los agentes opcionales activos.
            Clave = nombre del agente, valor = True si esta activo.
            Si es None, no se anaden opcionales.

    Returns:
        Diccionario con dos claves:
        - "paralelo": lista de agentes opcionales que se ejecutan en paralelo
          con los de nucleo.
        - "secuencial": lista de agentes opcionales que se ejecutan despues
          de los de nucleo.

    Ejemplo:
        >>> get_effective_agents("calidad", {"ux-reviewer": True, "performance-engineer": True})
        {"paralelo": ["ux-reviewer", "performance-engineer"], "secuencial": []}
    """
    if active_optionals is None:
        return {"paralelo": [], "secuencial": []}

    paralelo: List[str] = []
    secuencial: List[str] = []

    for agent_name, config in OPTIONAL_INTEGRATIONS.items():
        if not active_optionals.get(agent_name, False):
            continue
        if phase_name not in config.get("fases", []):
            continue

        posicion = config.get("posicion", "paralelo")
        if posicion == "secuencial":
            secuencial.append(agent_name)
        elif posicion == "paralelo":
            paralelo.append(agent_name)

    return {"paralelo": paralelo, "secuencial": secuencial}


def _resolve_current_phase(session: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Resuelve y valida la fase actual de una sesión."""
    comando = session.get("comando")
    if comando not in FLOWS:
        return None, f"Flujo '{comando}' no definido en FLOWS."

    fase_actual = session.get("fase_actual")
    if fase_actual == "completado":
        return None, "Sesion completada. No hay gate pendiente."

    fase_numero = session.get("fase_numero")
    if not isinstance(fase_numero, int):
        return None, "El índice de fase no es un entero válido."
    if fase_numero < 0:
        return None, f"El índice de fase no puede ser negativo: {fase_numero}."

    fases = FLOWS[comando]["fases"]
    if fase_numero >= len(fases):
        return None, (
            f"El índice de fase {fase_numero} está fuera de rango para el flujo "
            f"'{comando}' ({len(fases)} fases)."
        )

    fase = fases[fase_numero]
    expected_name = fase["nombre"]
    if fase_actual != expected_name:
        return None, (
            "El estado de sesión es inconsistente: "
            f"fase_actual='{fase_actual}' no coincide con fase_numero={fase_numero} "
            f"('{expected_name}')."
        )

    return fase, ""


def _validate_equipo_sesion(equipo_sesion: Any) -> bool:
    """Valida la estructura del equipo de sesión generado por composición dinámica.

    Comprueba que el diccionario tenga las claves esperadas en cada nivel y que
    los valores sean del tipo correcto. Si algo falla, imprime un aviso
    descriptivo a stderr y devuelve False. Esto permite que el orquestador
    descarte equipos mal formados sin romper el flujo.

    Las reglas de validación por nivel son:

        - **Primer nivel**: exige exactamente las claves ``"opcionales_activos"``,
          ``"infra"`` y ``"fuente"``. Claves extra o ausentes provocan rechazo.
        - **``opcionales_activos``**: exige como mínimo las claves de
          ``_KNOWN_OPTIONAL_AGENTS``. Acepta
          claves extra con aviso a stderr (tolerancia ante extensiones futuras),
          pero no las valida. Todos los valores deben ser ``bool``.
        - **``infra``**: exige exactamente ``"memoria"``, de tipo ``bool``.
        - **``fuente``**: debe ser una de las fuentes runtime reconocidas
          (actualmente ``"composicion_dinamica"`` o ``"config_persistida"``).

    Args:
        equipo_sesion: valor a validar. Se espera un dict con las claves
            ``"opcionales_activos"``, ``"infra"`` y ``"fuente"``.

    Returns:
        True si la estructura es válida, False en caso contrario.

    Ejemplo:
        >>> _validate_equipo_sesion({"opcionales_activos": {...}, "infra": {...}, "fuente": "composicion_dinamica"})
        True
    """
    # --- 1. Debe ser un dict ---
    if not isinstance(equipo_sesion, dict):
        print(
            "[Alfred Dev] Aviso: equipo_sesion no es un diccionario.",
            file=sys.stderr,
        )
        return False

    # --- 2. Claves de primer nivel ---
    expected_top_keys = {"opcionales_activos", "infra", "fuente"}
    if set(equipo_sesion.keys()) != expected_top_keys:
        print(
            f"[Alfred Dev] Aviso: equipo_sesion tiene claves inesperadas. "
            f"Esperadas: {sorted(expected_top_keys)}, "
            f"recibidas: {sorted(equipo_sesion.keys())}.",
            file=sys.stderr,
        )
        return False

    # --- 3. opcionales_activos: dict con al menos las claves conocidas, valores bool ---
    opcionales = equipo_sesion["opcionales_activos"]
    if not isinstance(opcionales, dict):
        print(
            "[Alfred Dev] Aviso: opcionales_activos no es un diccionario.",
            file=sys.stderr,
        )
        return False

    # Las claves conocidas deben estar presentes. Claves extra se aceptan
    # con aviso (tolerancia ante extensiones futuras).
    missing = _KNOWN_OPTIONAL_AGENTS - set(opcionales.keys())
    if missing:
        print(
            f"[Alfred Dev] Aviso: opcionales_activos no incluye los agentes "
            f"requeridos: {sorted(missing)}.",
            file=sys.stderr,
        )
        return False

    extra = set(opcionales.keys()) - _KNOWN_OPTIONAL_AGENTS
    if extra:
        print(
            f"[Alfred Dev] Aviso: opcionales_activos incluye agentes "
            f"desconocidos que se ignorarán: {sorted(extra)}.",
            file=sys.stderr,
        )

    for agent_name, value in opcionales.items():
        if not isinstance(value, bool):
            print(
                f"[Alfred Dev] Aviso: opcionales_activos['{agent_name}'] no es bool "
                f"(tipo: {type(value).__name__}, valor: {value!r}).",
                file=sys.stderr,
            )
            return False

    # --- 4. infra: dict con exactamente "memoria", valor bool ---
    infra = equipo_sesion["infra"]
    if not isinstance(infra, dict):
        print(
            "[Alfred Dev] Aviso: infra no es un diccionario.",
            file=sys.stderr,
        )
        return False

    expected_infra_keys = {"memoria"}
    actual_keys = set(infra.keys())
    # Aceptar "gui" por compatibilidad con estados de sesiones anteriores
    accepted_keys = actual_keys - {"gui"}
    if accepted_keys != expected_infra_keys:
        print(
            f"[Alfred Dev] Aviso: infra tiene claves inesperadas. "
            f"Esperadas: {sorted(expected_infra_keys)}, "
            f"recibidas: {sorted(infra.keys())}.",
            file=sys.stderr,
        )
        return False

    for infra_key, value in infra.items():
        if infra_key == "gui":
            continue  # Ignorar clave obsoleta
        if not isinstance(value, bool):
            print(
                f"[Alfred Dev] Aviso: infra['{infra_key}'] no es bool "
                f"(tipo: {type(value).__name__}, valor: {value!r}).",
                file=sys.stderr,
            )
            return False

    # --- 5. fuente: debe ser una fuente runtime conocida ---
    if equipo_sesion["fuente"] not in _KNOWN_EQUIPO_SESSION_SOURCES:
        print(
            f"[Alfred Dev] Aviso: fuente debe ser una de "
            f"{sorted(_KNOWN_EQUIPO_SESSION_SOURCES)}, "
            f"recibido: {equipo_sesion['fuente']!r}.",
            file=sys.stderr,
        )
        return False

    return True


def _load_persisted_equipo_sesion(
    project_dir: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Carga el equipo runtime derivado de la configuración persistida."""
    try:
        from core.config_loader import build_project_equipo_sesion  # noqa: PLC0415

        equipo_sesion = build_project_equipo_sesion(project_dir)
    except Exception as exc:
        print(
            "[Alfred Dev] Aviso: no se pudo cargar el equipo persistido "
            f"del proyecto '{project_dir}': {exc}",
            file=sys.stderr,
        )
        return None, (
            "No se pudo cargar la configuración persistida del proyecto; "
            "la sesión seguirá sin agentes opcionales."
        )

    if equipo_sesion is None:
        return None, None

    if not _validate_equipo_sesion(equipo_sesion):
        print(
            "[Alfred Dev] Aviso: el equipo derivado de la configuración "
            "persistida no pasó la validación y se ignorará.",
            file=sys.stderr,
        )
        return None, (
            "La configuración persistida del proyecto produjo un equipo de "
            "sesión inválido y fue descartada."
        )

    return equipo_sesion, None


def run_flow(
    command: str,
    description: str,
    equipo_sesion: Optional[Dict[str, Any]] = None,
    project_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea una sesión de flujo con composición dinámica de equipo opcional.

    Combina la creación de sesión estándar con la inyección del equipo de
    sesión generado por la composición dinámica. Si el equipo proporcionado
    no pasa la validación, se descarta con aviso a stderr y se registra el
    motivo en ``session["equipo_sesion_error"]`` para que los consumidores
    downstream puedan informar al usuario.

    Este es el punto de entrada principal para iniciar un flujo cuando se
    dispone de información sobre qué agentes opcionales deben participar.

    Args:
        command: identificador del flujo (feature, fix, quick, spike, ship, audit).
        description: descripción en lenguaje natural de la tarea.
        equipo_sesion: diccionario con la composición del equipo generada
            por el módulo de composición dinámica. Si es None, la sesión
            se crea sin equipo. Si es inválido, se descarta con aviso y
            se registra el motivo en "equipo_sesion_error".
        project_dir: ruta al proyecto sobre el que debe detectarse stack y
            cargarse la configuración persistida. Si no se pasa, se usa el
            directorio de trabajo actual.

    Returns:
        Diccionario con el estado de la sesión, incluyendo las claves:
        - "equipo_sesion" (dict válido o None).
        - "equipo_sesion_error" (str o None): motivo del descarte.

    Raises:
        ValueError: si el comando no corresponde a ningún flujo definido.

    Ejemplo:
        >>> session = run_flow("feature", "Login con OAuth", equipo_sesion={...})
        >>> session["equipo_sesion"]["opcionales_activos"]["github-manager"]
        True
    """
    # --- 1. Validar que el comando existe ---
    if command not in FLOWS:
        raise ValueError(
            f"Flujo '{command}' no reconocido. "
            f"Flujos disponibles: {', '.join(FLOWS.keys())}"
        )

    resolved_project_dir = os.path.abspath(project_dir or os.getcwd())

    # --- 2. Validar equipo_sesion si se proporcionó ---
    equipo_error = None
    explicit_team_discarded = False
    if equipo_sesion is not None and not _validate_equipo_sesion(equipo_sesion):
        print(
            "[Alfred Dev] Error: el equipo de sesión no pasó la validación. "
            "La sesión se creará sin agentes opcionales. Revisa la estructura "
            "del diccionario equipo_sesion.",
            file=sys.stderr,
        )
        equipo_error = (
            "El equipo de sesión proporcionado no pasó la validación "
            "y fue descartado."
        )
        equipo_sesion = None
        explicit_team_discarded = True

    if equipo_sesion is None:
        persisted_team, persisted_error = _load_persisted_equipo_sesion(resolved_project_dir)
        if persisted_team is not None:
            equipo_sesion = persisted_team
            if explicit_team_discarded:
                equipo_error = (
                    f"{equipo_error} Se aplicó la configuración persistida de "
                    "agentes opcionales del proyecto."
                )
        elif persisted_error:
            if explicit_team_discarded:
                equipo_error = f"{equipo_error} {persisted_error}"
            else:
                equipo_error = persisted_error

    # --- 3. Detectar stack del proyecto para fases condicionales ---
    stack = None
    try:
        from core.config_loader import detect_stack  # noqa: PLC0415
        stack = detect_stack(resolved_project_dir)
    except Exception as exc:
        print(
            f"[Alfred Dev] Aviso: no se pudo detectar el stack del proyecto: {exc}",
            file=sys.stderr,
        )

    # --- 4. Crear sesión base ---
    session = create_session(command, description, stack=stack)

    # --- 5. Inyectar equipo_sesion y diagnóstico ---
    session["equipo_sesion"] = equipo_sesion
    session["equipo_sesion_error"] = equipo_error

    return session


def create_session(
    command: str,
    description: str,
    stack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Crea una nueva sesión de trabajo para el flujo indicado.

    La sesión contiene todo el estado necesario para que el orquestador
    sepa en qué punto del flujo se encuentra el usuario y qué fases
    se han completado.

    Args:
        command: Identificador del flujo (feature, fix, quick, spike, ship, audit).
        description: Descripción en lenguaje natural de la tarea.
        stack: metadatos detectados del proyecto. Si se proporciona, permite
            evaluar fases condicionales como ``estilo_visual``.

    Returns:
        Diccionario con el estado inicial de la sesión.

    Raises:
        ValueError: Si el comando no corresponde a ningún flujo definido.
    """
    if command not in FLOWS:
        raise ValueError(
            f"Flujo '{command}' no reconocido. "
            f"Flujos disponibles: {', '.join(FLOWS.keys())}"
        )

    flow = FLOWS[command]
    primera_fase = flow["fases"][0]["nombre"]

    session = {
        "comando": command,
        "descripcion": description,
        "fase_actual": primera_fase,
        "fase_numero": 0,
        "fases_completadas": [],
        "artefactos": [],
        "creado_en": datetime.now(timezone.utc).isoformat(),
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }
    if stack is not None:
        session["stack"] = stack
    return session


def check_gate(
    session: Dict[str, Any],
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Evalúa la gate de la fase actual para decidir si se puede avanzar.

    La lógica de evaluación depende del tipo de gate definido en la fase:
    - «usuario»: requiere resultado «aprobado».
    - «automático»: requiere resultado «aprobado» y tests verdes.
    - «usuario+seguridad»: requiere aprobación del usuario y seguridad OK.
    - «automático+seguridad»: requiere tests, seguridad y resultado OK.
    - «libre»: se aprueba siempre que el resultado sea «aprobado».

    Args:
        session: Estado actual de la sesión.
        resultado: Resultado reportado (normalmente «aprobado» o «rechazado»).
        security_ok: Indica si la auditoría de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con las claves «passed» (bool) y «reason» (str).
    """
    comando = session["comando"]
    if comando not in FLOWS:
        return {"passed": False, "reason": f"Flujo '{comando}' no definido en FLOWS."}

    # Sesion completada: no hay gate que evaluar.
    if session.get("fase_actual") == "completado":
        return {"passed": True, "reason": "Sesion completada. No hay gate pendiente."}

    fase, phase_error = _resolve_current_phase(session)
    if fase is None:
        return {"passed": False, "reason": phase_error}

    gate_tipo = fase["gate_tipo"]

    # Se acumulan las condiciones que debe cumplir la gate.
    # El orden de comprobación determina qué error se reporta primero.
    failures = []

    requires_tests = "automatico" in gate_tipo
    requires_security = "seguridad" in gate_tipo
    requires_approval = gate_tipo in (GATE_USUARIO, GATE_USUARIO_SEGURIDAD)
    is_known = gate_tipo in _KNOWN_GATE_TYPES

    if not is_known:
        return {"passed": False, "reason": f"Tipo de gate desconocido: {gate_tipo}"}

    if requires_tests and not tests_ok:
        failures.append("Los tests no pasan.")
    if requires_security and not security_ok:
        failures.append("La auditoría de seguridad no es favorable.")
    if resultado != "aprobado":
        if requires_approval:
            failures.append("Aprobación del usuario requerida.")
        else:
            failures.append("El resultado no es favorable.")

    passed = len(failures) == 0
    reason = failures[0] if failures else ""

    return {"passed": passed, "reason": reason}


def advance_phase(
    session: Dict[str, Any],
    resultado: str = "aprobado",
    artefactos: Optional[List[str]] = None,
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Intenta avanzar la sesión a la siguiente fase del flujo.

    Primero evalúa la gate de la fase actual. Si la gate se supera,
    registra la fase como completada y actualiza el puntero a la
    siguiente. Si ya no quedan fases, marca la sesión como «completado».

    Args:
        session: Estado actual de la sesión.
        resultado: Resultado a evaluar en la gate (por defecto «aprobado»).
        artefactos: Lista opcional de artefactos generados en la fase.
        security_ok: Indica si la auditoría de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con el estado actualizado de la sesión.

    Raises:
        RuntimeError: Si la gate de la fase actual no se supera.
    """
    if artefactos is None:
        artefactos = []

    comando = session["comando"]
    if comando not in FLOWS:
        raise RuntimeError(f"Flujo '{comando}' no definido en FLOWS.")

    flow = FLOWS[comando]
    fases = flow["fases"]

    # Si ya está completado, devolver sin cambios
    if session["fase_actual"] == "completado":
        return session

    # Evaluar la gate de la fase actual propagando todos los parámetros
    gate_result = check_gate(
        session, resultado=resultado, security_ok=security_ok, tests_ok=tests_ok
    )
    if not gate_result["passed"]:
        raise RuntimeError(
            f"No se puede avanzar: {gate_result['reason']}"
        )

    # Registrar la fase completada; se preserva el contador de iteraciones
    # para que los informes de sesión puedan mostrar cuántos ciclos requirió la fase.
    fase_completada = {
        "nombre": fases[session["fase_numero"]]["nombre"],
        "resultado": resultado,
        "artefactos": artefactos,
        "completada_en": datetime.now(timezone.utc).isoformat(),
        "iteraciones": session.get("iteraciones_fase", 0),
    }
    session["fases_completadas"].append(fase_completada)

    # Incorporar artefactos al registro global de la sesión
    session["artefactos"].extend(artefactos)

    # Avanzar al siguiente índice, saltando fases con condicion no cumplida
    siguiente = _advance_skipping_phases(
        session, fases, session["fase_numero"] + 1, _get_phase_conditions()
    )

    if siguiente < len(fases):
        session["fase_numero"] = siguiente
        session["fase_actual"] = fases[siguiente]["nombre"]
    else:
        # No quedan más fases: el flujo está completado
        session["fase_actual"] = "completado"
        session["fase_numero"] = siguiente

    # Reiniciar el contador de iteraciones internas para la nueva fase
    session["iteraciones_fase"] = 0

    session["actualizado_en"] = datetime.now(timezone.utc).isoformat()
    return session


def save_state(session: Dict[str, Any], state_path: str) -> None:
    """
    Persiste el estado de la sesión en un fichero JSON.

    Se utiliza escritura atómica (escritura + renombrado) para evitar
    corrupción si el proceso se interrumpe a mitad de escritura. Si la
    operación falla, se limpia el fichero temporal y se relanza el error
    como RuntimeError para que el llamante sepa que el estado no se guardó.

    Args:
        session: Estado de la sesión a guardar.
        state_path: Ruta absoluta del fichero de destino.

    Raises:
        RuntimeError: Si no se puede guardar el estado por cualquier razón.
    """
    persisted = session
    sync_session_state_to_operational_docs = None
    canonical_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(state_path)))
    is_canonical_state_path = (
        os.path.basename(state_path) == "alfred-dev-state.json"
        and os.path.basename(os.path.dirname(os.path.abspath(state_path))) == ".claude"
    )
    if is_canonical_state_path:
        try:
            from core.continuity import (  # noqa: PLC0415
                sync_session_state_to_kanban,
                sync_session_state_to_operational_docs,
            )
        except Exception:
            sync_session_state_to_kanban = None
            sync_session_state_to_operational_docs = None

        if sync_session_state_to_kanban is not None:
            try:
                persisted = sync_session_state_to_kanban(state_path, session)
            except Exception as exc:  # pragma: no cover - best effort operativa
                print(
                    f"[Alfred Dev] Aviso: no se pudo sincronizar el kanban desde save_state: {exc}",
                    file=sys.stderr,
                )
                persisted = session

    tmp_path = state_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(persisted, f, indent=2, ensure_ascii=False)
        # Renombrado atómico en sistemas POSIX
        os.replace(tmp_path, state_path)
        if is_canonical_state_path and sync_session_state_to_operational_docs is not None:
            try:
                persisted = sync_session_state_to_operational_docs(
                    canonical_project_dir,
                    persisted,
                )
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(persisted, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, state_path)
            except Exception as exc:  # pragma: no cover - best effort operativa
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                print(
                    f"[Alfred Dev] Aviso: no se pudo sincronizar documentación operativa desde save_state: {exc}",
                    file=sys.stderr,
                )
    except (OSError, TypeError) as e:
        # Limpiar el fichero temporal si quedó huérfano
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError as cleanup_err:
                print(
                    f"[Alfred Dev] Aviso: no se pudo limpiar el fichero temporal "
                    f"'{tmp_path}': {cleanup_err}",
                    file=sys.stderr,
                )
        raise RuntimeError(
            f"No se pudo guardar el estado de sesión en '{state_path}': {e}"
        ) from e


# Claves mínimas que debe tener un estado de sesión válido
_REQUIRED_STATE_KEYS = {"comando", "fase_actual", "fase_numero"}


def load_state(state_path: str) -> Optional[Dict[str, Any]]:
    """
    Carga el estado de una sesión desde un fichero JSON.

    Distingue entre tres situaciones:
    - Fichero ausente: devuelve None silenciosamente (caso normal).
    - Fichero corrupto o ilegible: devuelve None pero avisa en stderr.
    - Fichero con estructura inválida: devuelve None y avisa en stderr.

    Args:
        state_path: Ruta absoluta del fichero a leer.

    Returns:
        Diccionario con el estado de la sesión, o None si el fichero
        no existe, está corrupto o tiene estructura inválida.
    """
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(
            f"[Alfred Dev] Error: el fichero de estado '{state_path}' esta corrupto: {e}. "
            f"Para resolver, elimina el fichero manualmente y se creara uno nuevo "
            f"en la proxima sesion.",
            file=sys.stderr,
        )
        return None
    except OSError as e:
        print(
            f"[Alfred Dev] Error al leer el estado de sesión '{state_path}': {e}",
            file=sys.stderr,
        )
        return None

    # Validar estructura mínima: presencia de claves obligatorias
    if not isinstance(data, dict) or not _REQUIRED_STATE_KEYS.issubset(data.keys()):
        print(
            f"[Alfred Dev] Aviso: el fichero de estado '{state_path}' tiene una "
            f"estructura inesperada (faltan claves obligatorias). Se ignorará.",
            file=sys.stderr,
        )
        return None

    # Validar tipos de las claves obligatorias para evitar TypeError
    # en comparaciones posteriores (ej.: fase_numero >= len(fases))
    if not isinstance(data.get("comando"), str):
        print(
            f"[Alfred Dev] Aviso: 'comando' no es un string en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None
    if not isinstance(data.get("fase_actual"), str):
        print(
            f"[Alfred Dev] Aviso: 'fase_actual' no es un string en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None
    if not isinstance(data.get("fase_numero"), int):
        print(
            f"[Alfred Dev] Aviso: 'fase_numero' no es un entero en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None

    command = data["comando"]
    if command not in FLOWS:
        print(
            f"[Alfred Dev] Aviso: 'comando' no corresponde a un flujo conocido en '{state_path}'. "
            f"Se ignorará.",
            file=sys.stderr,
        )
        return None

    phase_index = data["fase_numero"]
    if phase_index < 0:
        print(
            f"[Alfred Dev] Aviso: 'fase_numero' no puede ser negativo en '{state_path}'. "
            f"Se ignorará.",
            file=sys.stderr,
        )
        return None

    fases = FLOWS[command]["fases"]
    phase_name = data["fase_actual"]
    if phase_name == "completado":
        if phase_index != len(fases):
            print(
                f"[Alfred Dev] Aviso: estado completado incoherente en '{state_path}' "
                f"(fase_numero={phase_index}, esperado={len(fases)}). Se ignorará.",
                file=sys.stderr,
            )
            return None
        return data

    if phase_index >= len(fases):
        print(
            f"[Alfred Dev] Aviso: 'fase_numero' está fuera de rango en '{state_path}'. "
            f"Se ignorará.",
            file=sys.stderr,
        )
        return None

    expected_phase_name = fases[phase_index]["nombre"]
    if phase_name != expected_phase_name:
        print(
            f"[Alfred Dev] Aviso: fase_actual y fase_numero no coinciden en '{state_path}' "
            f"('{phase_name}' != '{expected_phase_name}'). Se ignorará.",
            file=sys.stderr,
        )
        return None

    return data


# --- Loop iterativo (v0.4.0) ------------------------------------------------
# Permite que los agentes iteren dentro de una fase hasta que la gate
# se supere o se alcance el maximo de iteraciones. Esto habilita ciclos
# TDD, pasadas de QA repetidas y otros patrones iterativos.

# Maximo de iteraciones internas por fase antes de escalar al usuario.
MAX_PHASE_ITERATIONS = 5


def should_retry_phase(
    session: Dict[str, Any],
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """Determina si la fase actual debe reintentarse o escalar al usuario.

    Evalua la gate de la fase actual. Si no se supera, comprueba si quedan
    iteraciones disponibles. Si las hay, incrementa el contador y devuelve
    instrucciones de reintento. Si se agotaron, devuelve instrucciones de
    escalado al usuario.

    El contador de iteraciones se almacena en ``session["iteraciones_fase"]``.

    Args:
        session: estado actual de la sesion.
        resultado: resultado reportado para la gate.
        security_ok: si la auditoria de seguridad es favorable.
        tests_ok: si los tests pasan.

    Returns:
        Diccionario con:
        - ``"action"``: ``"advance"`` (gate superada), ``"retry"`` (reintentar)
          o ``"escalate"`` (escalar al usuario).
        - ``"reason"``: motivo de la decision.
        - ``"iteration"``: numero de iteracion actual.
        - ``"max_iterations"``: maximo permitido.
    """
    # Validacion defensiva: si la sesion esta completada o el indice
    # esta fuera de rango, no tiene sentido reintentar.
    if session.get("fase_actual") == "completado":
        return {
            "action": "advance",
            "reason": "Sesion completada. No hay gate que evaluar.",
            "iteration": 0,
            "max_iterations": 0,
        }

    _, phase_error = _resolve_current_phase(session)
    if phase_error:
        iteration = session.get("iteraciones_fase", 0)
        max_iter = session.get("max_iteraciones_fase", MAX_PHASE_ITERATIONS)
        return {
            "action": "escalate",
            "reason": f"Estado de sesión inválido: {phase_error}",
            "iteration": iteration,
            "max_iterations": max_iter,
        }

    gate_result = check_gate(
        session,
        resultado=resultado,
        security_ok=security_ok,
        tests_ok=tests_ok,
    )

    iteration = session.get("iteraciones_fase", 0)
    max_iter = session.get("max_iteraciones_fase", MAX_PHASE_ITERATIONS)

    if gate_result["passed"]:
        return {
            "action": "advance",
            "reason": "Gate superada. Se puede avanzar a la siguiente fase.",
            "iteration": iteration,
            "max_iterations": max_iter,
        }

    if iteration < max_iter:
        # Incrementar el contador
        session["iteraciones_fase"] = iteration + 1
        session["actualizado_en"] = datetime.now(timezone.utc).isoformat()

        return {
            "action": "retry",
            "reason": (
                f"Gate no superada: {gate_result['reason']} "
                f"Iteracion {iteration + 1}/{max_iter}. "
                f"Corrige los problemas y vuelve a intentarlo."
            ),
            "iteration": iteration + 1,
            "max_iterations": max_iter,
        }

    return {
        "action": "escalate",
        "reason": (
            f"Se agotaron las {max_iter} iteraciones sin superar la gate: "
            f"{gate_result['reason']} "
            f"Se requiere intervencion del usuario."
        ),
        "iteration": iteration,
        "max_iterations": max_iter,
    }


def reset_phase_iterations(session: Dict[str, Any]) -> None:
    """Reinicia el contador de iteraciones de la fase actual.

    Se llama automaticamente al avanzar a una nueva fase para que
    el contador empiece en 0.

    Args:
        session: estado de la sesion a modificar in-place.
    """
    session["iteraciones_fase"] = 0


# --- Modo autopilot (v0.4.0) ------------------------------------------------
# Permite ejecutar un flujo completo sin interrupcion humana. Las gates
# de tipo «usuario» se aprueban automaticamente; las automaticas y de
# seguridad se evaluan normalmente.

def is_autopilot_gate_passable(
    session: Dict[str, Any],
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """Evalua si una gate puede superarse en modo autopilot.

    En autopilot, las gates de tipo «usuario» se aprueban automaticamente.
    Las de tipo «automatico» y «seguridad» se evaluan con los parametros
    proporcionados.

    Args:
        session: estado de la sesion.
        security_ok: resultado de la auditoria de seguridad.
        tests_ok: resultado de los tests.

    Returns:
        Diccionario con ``"passed"`` (bool) y ``"reason"`` (str).
    """
    comando = session["comando"]
    if comando not in FLOWS:
        return {"passed": False, "reason": f"Flujo '{comando}' no definido."}

    # Sesion completada: no hay gate que evaluar.
    if session.get("fase_actual") == "completado":
        return {"passed": True, "reason": "Sesion completada (autopilot)."}

    fase, phase_error = _resolve_current_phase(session)
    if fase is None:
        return {"passed": False, "reason": phase_error}

    gate_tipo = fase["gate_tipo"]

    if fase.get("autopilot_force_user_confirmation"):
        return {
            "passed": False,
            "reason": (
                "La fase requiere confirmación explícita del usuario incluso en autopilot."
            ),
        }

    # En autopilot, las gates de usuario se aprueban automaticamente
    if gate_tipo == GATE_USUARIO:
        return {"passed": True, "reason": "Aprobacion automatica (autopilot)."}

    # El resto se evalua normalmente con resultado «aprobado»
    return check_gate(
        session,
        resultado="aprobado",
        security_ok=security_ok,
        tests_ok=tests_ok,
    )


def run_flow_autopilot(
    command: str,
    description: str,
    equipo_sesion: Optional[Dict[str, Any]] = None,
    project_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea una sesion de flujo en modo autopilot.

    Identica a ``run_flow()`` pero marca la sesion con ``autopilot=True``
    para que el stop-hook y las gates sepan que deben comportarse de
    forma autonoma.

    Args:
        command: identificador del flujo.
        description: descripcion de la tarea.
        equipo_sesion: composicion del equipo opcional.
        project_dir: ruta del proyecto sobre el que debe resolverse stack y
            configuración persistida.

    Returns:
        Estado de la sesion con ``autopilot=True``.

    Raises:
        ValueError: si el comando no corresponde a ningun flujo definido.
    """
    session = run_flow(
        command,
        description,
        equipo_sesion=equipo_sesion,
        project_dir=project_dir,
    )
    session["autopilot"] = True
    session["iteraciones_fase"] = 0
    session["max_iteraciones_fase"] = MAX_PHASE_ITERATIONS
    return session
