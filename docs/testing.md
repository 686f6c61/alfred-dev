# Tests

Alfred Dev tiene una arquitectura deliberadamente dividida en dos capas con estrategias de testing muy distintas. La capa core esta escrita en Python puro (orchestrator, config_loader, personality, memory) y se puede testear con pytest de forma convencional, sin dependencias externas ni simulacion de entornos complejos. La segunda capa ---hooks bash, servidor MCP y commands Markdown--- son integraciones directas con Claude Code que solo se pueden verificar en contexto real, ejecutando el plugin dentro de una sesión activa. Esta separación no es casual: se diseño así para que el nucleo de lógica sea testeable de forma aislada, mientras que la capa de integración se valida mediante uso.

Todos los tests usan `unittest` como framework y siguen el patron de clases de test agrupadas por responsabilidad. Cada fichero de test cubre un modulo del core y es independiente del resto, lo que permite ejecutarlos de forma aislada o en conjunto.


## Como ejecutar los tests

El core del plugin solo depende de la biblioteca estandar de Python, por lo que el único requisito para ejecutar los tests es tener `pytest` instalado. No hace falta instalar paquetes adicionales ni configurar entornos virtuales; toda la lógica usa `os`, `json`, `sqlite3`, `tempfile`, `importlib` y otros modulos de la stdlib.

Para ejecutar la suite completa con salida detallada:

```bash
python3 -m pytest tests/ -v
```

Si se necesita medir la cobertura de código (requiere `pytest-cov`):

```bash
python3 -m pytest tests/ -v --cov=core
```

La salida del segundo comando muestra un informe por modulo con el porcentaje de lineas cubiertas, lo que permite identificar rapidamente que partes del core tienen menos cobertura.


## Cobertura por modulo

### test_orchestrator.py

El orquestador es la maquina de estados que gobierna los flujos de trabajo del plugin. Cada tipo de comando (`feature`, `fix`, `spike`, `ship`, `audit`) tiene un flujo definido con fases secuenciales y gates (puntos de verificación) que deben superarse para avanzar. Los tests verifican que la maquina de estados se comporta correctamente en todas las transiciones posibles, incluyendo los casos limite como intentar avanzar mas alla de la última fase o que una gate automática bloquee el avance cuando los tests no pasan.

La suite cubre tanto la definición estática de los flujos (número de fases, flujos esperados) como el comportamiento dinámico de las sesiones (creación, avance, persistencia, gates con condiciones).

| Clase | Métodos de test | Que verifica |
|-------|----------------|--------------|
| `TestFlows` | `test_feature_flow_has_6_phases`, `test_fix_flow_has_3_phases`, `test_all_flows_defined` | Definición correcta de los flujos: número de fases y presencia de todos los tipos (`feature`, `fix`, `spike`, `ship`, `audit`). |
| `TestSession` | `test_create_session`, `test_save_and_load_state` | Creación de sesiones con estado inicial correcto y persistencia a disco (JSON) con carga posterior. |
| `TestGates` | `test_gate_passes_with_correct_result`, `test_gate_fails_with_incorrect_result`, `test_automatic_gate_fails_when_tests_fail`, `test_automatic_gate_passes_when_tests_ok`, `test_security_gate_fails_when_security_fails`, `test_advance_phase_propagates_tests_ok` | Lógica de gates: aprobacion, rechazo, bloqueo automático por tests fallidos, bloqueo por seguridad y propagacion de `tests_ok` al avanzar fase. |
| `TestAdvancePhase` | `test_advance_moves_to_next_phase`, `test_cannot_advance_past_last_phase` | Transiciones correctas entre fases y protección contra avance mas alla de la última fase (estado `completado`). |

### test_config_loader.py

El cargador de configuración gestiona dos responsabilidades: leer las preferencias del usuario desde un fichero `.local.md` con frontmatter YAML, y detectar automáticamente el stack tecnologico del proyecto analizando los ficheros presentes en el directorio de trabajo. Los tests verifican ambas responsabilidades de forma independiente, usando directorios temporales para simular distintos tipos de proyecto sin tocar el sistema de ficheros real.

La tercera responsabilidad cubierta es la sugerencia de agentes opcionales, que analiza el proyecto y recomienda agentes especializados (como `data-engineer` o `seo-specialist`) en función de las dependencias y ficheros detectados. Los tests comprueban que las sugerencias son coherentes con el contenido del proyecto y que no se sugieren agentes ya activados.

| Clase | Métodos de test | Que verifica |
|-------|----------------|--------------|
| `TestLoadConfig` | `test_returns_defaults_when_no_file`, `test_loads_yaml_frontmatter`, `test_extracts_notes_section` | Valores por defecto cuando no existe fichero, carga de configuración desde frontmatter YAML y extraccion de la sección de notas. |
| `TestDetectStack` | `test_detects_node_project`, `test_detects_python_project`, `test_returns_unknown_for_empty_dir` | Detección de stack para proyectos Node.js (con TypeScript), Python y directorios sin marcadores reconocibles. |
| `TestOptionalAgents` | `test_default_config_has_optional_agents`, `test_all_optional_agents_disabled_by_default`, `test_config_loads_optional_agents`, `test_suggest_for_node_project_with_orm`, `test_suggest_for_project_with_html`, `test_suggest_skips_already_active`, `test_suggest_empty_for_minimal_project`, `test_suggest_github_manager_with_remote` | Estructura de agentes opcionales en la configuración por defecto, fusion con configuración del usuario, sugerencias basadas en dependencias del proyecto (ORM, HTML, repositorio Git) y exclusion de agentes ya activos. |

### test_memory.py

El modulo de memoria es el mas extenso del core y, en consecuencia, tiene la suite de tests mas grande. Gestiona una base de datos SQLite con soporte opcional de FTS5 (Full-Text Search) que almacena iteraciones, decisiones, commits y eventos de cada sesión de trabajo. Los tests no solo verifican la API Python, sino que muchos de ellos acceden directamente a la base de datos con consultas SQL para confirmar que la capa de persistencia funciona correctamente. Esta doble verificación (API + SQL) es intencionada: detecta fallos en el mapeo entre la interfaz publica y el almacenamiento real.

La suite incluye tests de sanitizacion de secretos (claves AWS, tokens JWT, claves `sk-`, cabeceras PEM, cadenas de conexión) que verifican que ningun dato sensible se persiste en texto plano. También cubre la reapertura de la base de datos para confirmar que los datos sobreviven entre sesiones.

| Clase | Métodos de test | Que verifica |
|-------|----------------|--------------|
| `TestMemoryDBCreation` | `test_all_tables_exist`, `test_schema_version_registered`, `test_wal_mode_active`, `test_foreign_keys_enabled`, `test_fts5_detection`, `test_fts_enabled_property`, `test_file_permissions_0600`, `test_indices_exist`, `test_created_at_registered`, `test_creates_parent_directory` | Esquema completo de la DB: 6 tablas (`meta`, `iterations`, `decisions`, `commits`, `commit_links`, `events`), 5 índices, modo WAL, foreign keys, detección de FTS5, permisos 0600 y creación automática de directorios padre. |
| `TestIterations` | `test_start_iteration_returns_id`, `test_get_iteration`, `test_get_nonexistent_iteration_returns_none`, `test_complete_iteration`, `test_abandon_iteration`, `test_get_active_iteration`, `test_get_active_iteration_returns_none_when_none_active`, `test_get_active_iteration_after_completion`, `test_latest_active_iteration_wins` | CRUD completo de iteraciones: creación, consulta, finalizacion (completed/abandoned), consulta de la iteracion activa y prioridad de la mas reciente cuando hay multiples activas. |
| `TestDecisions` | `test_log_decision_returns_id`, `test_get_decisions`, `test_decision_auto_links_to_active_iteration`, `test_decision_without_active_iteration`, `test_decision_with_all_fields`, `test_get_decisions_filtered_by_iteration` | CRUD de decisiones: registro con campos opcionales (context, alternatives, rationale, impact, phase), vinculacion automática a la iteracion activa, decisiones huerfanas y filtrado por iteracion. |
| `TestCommits` | `test_log_commit_returns_id`, `test_duplicate_sha_returns_none`, `test_commit_auto_links_to_active_iteration`, `test_log_commit_with_full_metadata`, `test_link_commit_decision`, `test_link_commit_decision_duplicate_ignored` | Registro de commits con idempotencia por SHA, vinculacion automática a iteraciones, metadata completa (author, files_changed, insertions, deletions) y vinculacion de commits con decisiones. |
| `TestSanitization` | `test_none_returns_none`, `test_clean_text_unchanged`, `test_aws_key_redacted`, `test_jwt_redacted`, `test_sk_key_redacted`, `test_private_key_header_redacted`, `test_connection_string_redacted`, `test_multiple_secrets_all_redacted`, `test_sanitization_in_decision` | Sanitizacion de contenido sensible: claves AWS (`AKIA...`), tokens JWT, claves `sk-`, cabeceras PEM, cadenas de conexión con credenciales, multiples secretos simultaneos y verificación de sanitizacion al persistir decisiones. |
| `TestSearch` | `test_search_finds_decision_by_title`, `test_search_finds_commit_by_message`, `test_search_no_results`, `test_search_with_iteration_filter`, `test_search_respects_limit` | Busqueda textual (FTS5 o fallback LIKE): por titulo de decisión, por mensaje de commit, terminos inexistentes, filtrado por iteracion y respeto del parámetro `limit`. |
| `TestEvents` | `test_log_event_returns_id`, `test_log_event_with_payload`, `test_event_auto_links_to_active_iteration`, `test_get_timeline_ordered_chronologically`, `test_get_timeline_empty_for_nonexistent_iteration`, `test_purge_old_events`, `test_purge_does_not_delete_recent_events` | Registro de eventos con payload JSON, vinculacion automática a la iteracion activa, cronología ordenada, purga de eventos antiguos con retención configurable y protección de eventos recientes. |
| `TestStats` | `test_stats_empty_db`, `test_stats_with_data`, `test_stats_includes_metadata`, `test_stats_fts_coherent_with_property` | Estadisticas generales: contadores a cero en DB vacia, contadores correctos tras insertar datos, inclusion de metadatos (schema_version, fts_enabled, created_at) y coherencia del campo FTS con la propiedad del objeto. |
| `TestReopen` | `test_data_persists_after_close_and_reopen`, `test_schema_not_duplicated_on_reopen` | Persistencia entre sesiones: los datos sobreviven tras cerrar y reabrir la DB, y el esquema no se duplica al reabrir. |

### test_personality.py

El motor de personalidad define los 17 agentes del plugin (9 del nucleo + 8 opcionales), cada uno con nombre, rol, color, modelo, personalidad y frases caracteristicas. Los tests verifican que el diccionario `AGENTS` es completo y coherente, que los agentes opcionales estan correctamente marcados como tales, que la función `get_agent_intro` respeta el nivel de sarcasmo configurado y que `get_agent_voice` devuelve frases validas para cada agente.

| Clase | Métodos de test | Que verifica |
|-------|----------------|--------------|
| `TestPersonality` | `test_all_agents_defined`, `test_optional_agents_have_flag`, `test_core_agents_not_optional`, `test_intro_respects_sarcasm_level`, `test_voice_returns_phrases`, `test_unknown_agent_raises` | Presencia de los 17 agentes (9 core + 8 opcionales), flag `opcional` correcto en cada agente, intro con diferentes niveles de sarcasmo (1 y 5), frases de voz (mínimo 2 por agente) y error `ValueError` al solicitar un agente inexistente. |

### test_spelling_guard.py

El hook de ortografia analiza ficheros en busca de palabras castellanas escritas sin tilde (por ejemplo, `función` en lugar de `función`). Los tests cubren tres areas: el filtro de ficheros (que determina que extensiones y rutas se inspeccionan), la detección de errores ortograficos y la integridad del diccionario de correcciones. El hook se importa con `importlib` porque su nombre de fichero (`spelling-guard.py`) contiene un guion, lo que impide usar la sentencia `import` directa de Python.

| Clase | Métodos de test | Que verifica |
|-------|----------------|--------------|
| `TestShouldInspect` | `test_inspects_markdown`, `test_inspects_python`, `test_inspects_html`, `test_inspects_typescript`, `test_ignores_json`, `test_ignores_lockfiles`, `test_ignores_node_modules`, `test_ignores_git`, `test_ignores_dist`, `test_ignores_empty_path`, `test_ignores_no_extension` | Filtro de ficheros: extensiones inspeccionadas (.md, .py, .html, .ts), extensiones ignoradas (.json), directorios excluidos (node_modules, .git, dist), rutas vacias y ficheros sin extensión. |
| `TestFindAccentErrors` | `test_detects_single_word`, `test_detects_multiple_words`, `test_no_duplicates`, `test_case_insensitive`, `test_no_errors_in_correct_text`, `test_empty_text`, `test_none_text`, `test_word_boundaries`, `test_technical_context` | Detección de palabras sin tilde: una palabra, multiples palabras, deduplicacion de errores repetidos, insensibilidad a mayusculas, texto correcto sin falsos positivos, texto vacio, texto nulo, limites de palabra y contextos técnicos habituales (método, autenticacion, validación, parámetro). |
| `TestAccentDictionary` | `test_no_self_referencing_entries`, `test_all_corrections_have_accents`, `test_minimum_dictionary_size` | Integridad del diccionario `ACCENT_WORDS`: ninguna entrada se corrige a si misma, todas las correcciones contienen al menos un carácter acentuado y el diccionario tiene un mínimo de 50 entradas. |


## Patrones de testing usados

### Ficheros temporales con cleanup

Los tests que necesitan escribir en disco ---bases de datos SQLite, ficheros de configuración, directorios de proyecto--- usan `tempfile.NamedTemporaryFile` o `tempfile.TemporaryDirectory` para crear recursos desechables. La limpieza se realiza en `tearDown()` o en bloques `try/finally`. Esto garantiza que los tests nunca escriben en el directorio del proyecto ni dejan residuos en el sistema de ficheros, lo que permite ejecutarlos en cualquier entorno sin efectos secundarios.

En el caso concreto de SQLite, la limpieza incluye los ficheros auxiliares del modo WAL (`-wal` y `-shm`) además del fichero principal `.db`, ya que SQLite puede crear estos ficheros complementarios durante la operación normal.

### Imports por ruta con sys.path

Los modulos del core no forman un paquete Python instalable (no hay `setup.py` ni `pyproject.toml` con sección de build). Para que los tests puedan importarlos, cada fichero de test inserta la raiz del proyecto en `sys.path` con la linea:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

A partir de ahi, se importan los modulos directamente:

```python
from core.memory import MemoryDB, sanitize_content
```

Este patron es deliberado: mantiene el plugin ligero (sin infraestructura de empaquetado) a cambio de una linea extra en cada fichero de test.

### importlib para ficheros con guion

El hook `spelling-guard.py` tiene un guion en el nombre, lo que es coherente con la convencion de nombres de hooks de Alfred Dev pero incompatible con la sentencia `import` de Python (que solo acepta identificadores validos). Para cargarlo como modulo se usa `importlib.util.spec_from_file_location`:

```python
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "spelling-guard.py")
_spec = importlib.util.spec_from_file_location("spelling_guard", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

find_accent_errors = _mod.find_accent_errors
```

Las funciones importadas se asignan a variables de nivel de modulo para que las clases de test las usen con la misma sintaxis que cualquier import normal.

### SQL directo para verificación

Los tests de `test_memory.py` no se limitan a verificar los datos a traves de la API publica de `MemoryDB`. Varios tests abren una conexión SQLite independiente y ejecutan consultas directas contra la base de datos para confirmar que los datos se han persistido correctamente. Por ejemplo, `test_commit_auto_links_to_active_iteration` verifica la vinculacion consultando directamente la tabla `commits`:

```python
conn = sqlite3.connect(self._db_path)
row = conn.execute(
    "SELECT iteration_id FROM commits WHERE id = ?", (commit_id,)
).fetchone()
conn.close()
self.assertEqual(row[0], iter_id)
```

Esta doble verificación detecta errores que la API podria enmascarar, como caches en memoria, transformaciones incorrectas al leer o escrituras que no llegan al disco.

### Construccion de secretos en runtime

Los tests de sanitizacion necesitan crear cadenas que contengan patrones de secretos (claves AWS, tokens JWT, etc.), pero el propio hook de seguridad del plugin (`secret-guard.sh`) podria detectar esos patrones en el código fuente de los tests. Para evitar falsos positivos, los valores de test se construyen concatenando fragmentos en tiempo de ejecución:

```python
fake_key = "AKIA" + "TESTMEMORYDB1234"
fake_jwt = f"{header}.{payload}.{signature}"
fake_sk = "sk-" + "a" * 25
```

De este modo, ningun patron completo aparece como literal en el código fuente, pero en ejecución se genera el valor completo para verificar que la sanitizacion funciona.


## Que no esta cubierto

### Hooks bash (session-start.sh, secret-guard.sh)

Los hooks bash son scripts que reciben eventos de Claude Code por stdin en formato JSON y escriben respuestas por stdout/stderr. Su funcionamiento depende del protocolo de hooks de Claude Code, que incluye variables de entorno específicas, una estructura de datos concreta para los eventos y un flujo de ejecución gestionado por el runtime del plugin. Probarlos con tests unitarios requeriria simular todo ese protocolo ---entorno, stdin, formato de eventos, ciclo de vida--- lo que equivaldria a construir un mock completo de Claude Code. El coste de mantenimiento de esos mocks superaria al beneficio, así que se validan en uso real.

### Servidor MCP (memory_server.py)

El servidor MCP expone las operaciones de memoria como herramientas JSON-RPC sobre stdio. Probarlo requiere simular la comunicación bidireccional del protocolo MCP (peticion JSON-RPC por stdin, respuesta por stdout, gestion del ciclo de vida). Los tests de `test_memory.py` ya cubren exhaustivamente la capa de datos subyacente (`MemoryDB`), que es donde reside la lógica de negocio. El servidor MCP es esencialmente un adaptador de protocolo, y su correcta integración se verifica ejecutando el plugin dentro de Claude Code.

### Commands (*.md)

Los commands son ficheros Markdown que Claude Code interpreta como system prompts. No contienen lógica ejecutable: son instrucciones en lenguaje natural que guian el comportamiento del modelo. No existe una forma significativa de testearlos con assertions automáticas; su calidad se valida observando que Claude sigue las instrucciones correctamente durante el uso real del plugin.

### Agentes (*.md)

Los agentes siguen la misma lógica que los commands: son ficheros Markdown que definen la personalidad y las instrucciones de cada agente especializado. El motor de personalidad (`core/personality.py`) esta cubierto por tests, pero el contenido de las instrucciones Markdown es texto para el modelo, no código ejecutable. La validación es empirica, no automatizable.


## Como añadir un nuevo test

Si quieres contribuir con tests al plugin, esta es la guia practica para hacerlo de forma coherente con la suite existente.

### 1. Crear el fichero

Los tests van en el directorio `tests/` con el prefijo `test_`. Si el modulo a testear se llama `core/mi_modulo.py`, el fichero de test debe llamarse `tests/test_mi_modulo.py`.

### 2. Estructura básica

Cada fichero de test sigue esta estructura:

```python
#!/usr/bin/env python3
"""Tests para [descripción del modulo]."""

import os
import sys
import unittest

# Insertar la raiz del proyecto en sys.path para poder importar core/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.mi_modulo import funcion_a_testear


class TestNombreDescriptivo(unittest.TestCase):
    """Describe que grupo de funcionalidad cubre esta clase."""

    def setUp(self):
        """Preparar recursos compartidos entre tests."""
        pass

    def tearDown(self):
        """Limpiar recursos creados en setUp."""
        pass

    def test_comportamiento_esperado(self):
        """Descripción clara de que verifica este test."""
        resultado = funcion_a_testear("entrada")
        self.assertEqual(resultado, "salida_esperada")


if __name__ == "__main__":
    unittest.main()
```

### 3. Importar modulos con guion en el nombre

Si el fichero a testear tiene un guion en el nombre (como `hooks/spelling-guard.py`), usa `importlib`:

```python
import importlib.util

_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "mi-hook.py")
_spec = importlib.util.spec_from_file_location("mi_hook", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

mi_funcion = _mod.mi_funcion
```

### 4. Usar ficheros temporales

Cuando el test necesite escribir ficheros en disco, usa siempre directorios temporales. Nunca escribas en el directorio del proyecto:

```python
import tempfile

class TestConFicheros(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_algo(self):
        ruta = os.path.join(self._tmpdir, "fichero.txt")
        with open(ruta, "w") as f:
            f.write("contenido de prueba")
        # ... assertions ...
```

### 5. Verificar que pasa

Tras escribir el test, ejecuta la suite completa para confirmar que no hay conflictos con los tests existentes:

```bash
python3 -m pytest tests/ -v
```

Si el test falla, revisa los mensajes de error antes de asumir que hay un bug en el código: es comun equivocarse en las rutas de import o en la limpieza de ficheros temporales.
