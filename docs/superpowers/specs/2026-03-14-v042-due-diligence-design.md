# Spec: Alfred Dev v0.4.2 — Correcciones de due diligence

**Fecha:** 2026-03-14
**Version:** 0.4.2
**Tipo:** parche (bugs + huecos funcionales + refactor del stop-hook)

---

## Contexto

Una auditoria exhaustiva de las cuatro funcionalidades criticas de v0.4.0/v0.4.1
(evidence guard, autopilot, loop iterativo, informes de sesion) revelo 2 problemas
criticos, 8 altos y 10 medios. El modelo arquitectonico del plugin (Python como
especificacion, markdown como motor real) se mantiene. Las correcciones operan
dentro de ese modelo: se corrigen bugs en Python, se unifican patrones divergentes,
se refactoriza el stop-hook para testabilidad, y se mejoran las instrucciones
markdown para cerrar brechas de integracion.

## Decisiones de diseno

| Decision | Opcion elegida | Alternativa descartada |
|----------|---------------|----------------------|
| Modelo arquitectonico | Python = especificacion, markdown = motor | Puente real Python-markdown (v futura) |
| quality-gate.py | Unificar (importa de evidence_guard_lib) | Eliminar (se pierde feedback inmediato) |
| Informes parciales | Generar siempre, stop-hook sigue bloqueando | Generar siempre + no bloquear |
| Ventana de evidencia | `max_age_seconds=None` para informes | Aumentar la ventana global |
| Enfoque de cambios | Refactor parcial (C): stop-hook + correcciones | Quirurgico (A) o maximo alcance sin foco |
| Race condition en evidencia | Fuera de alcance (riesgo bajo en uso real) | Anadir flock (complejidad desproporcionada para el riesgo) |
| Version | 0.4.2 (parche) | 0.5.0 (minor) |

---

## Seccion 1: Correcciones de bugs en Python

### 1.1 Falso positivo "0 failures"

**Fichero:** `hooks/evidence_guard_lib.py`, FAILURE_PATTERNS

**Cambio:** `r"\d+\s+failures?\b"` -> `r"[1-9]\d*\s+failures?\b"` para excluir el cero.
Lo mismo con `r"\d+\s+failed"` -> `r"[1-9]\d*\s+failed"`.

**Razon:** El patron actual detecta "0 failures" como fallo, invirtiendo un resultado
que deberia ser pass. Excluir el cero mantiene la deteccion para 1+ fallos.

### 1.2 Gate de arquitectura mal tipada

**Fichero:** `core/orchestrator.py`, FLOWS["feature"]["fases"][1]

**Cambio:** `gate_tipo: GATE_USUARIO` -> `gate_tipo: GATE_USUARIO_SEGURIDAD`

**Razon:** `feature.md` documenta la gate de arquitectura como `usuario+seguridad`.
La especificacion Python debe coincidir. Con `GATE_USUARIO`, la validacion de
seguridad en esa fase es inoperante.

### 1.3 go test sin cobertura en SUCCESS_PATTERNS

**Fichero:** `hooks/evidence_guard_lib.py`, SUCCESS_PATTERNS

**Cambio:** Anadir `r"^ok\s+\S+"` para cubrir la salida estandar de `go test`
(formato: `ok  github.com/foo/bar 0.003s`).

**Razon:** Hoy todas las ejecuciones de `go test` se registran como `unknown`
porque ningun patron de exito matchea su formato de salida.

### 1.4 Inconsistencia de clave "modo" vs "autopilot"

**Fichero:** `commands/_composicion.md`, paso 2b

**Cambio:** Donde dice `"modo": "autopilot"` en el state, cambiar a `"autopilot": true`.

**Razon:** `run_flow_autopilot()` escribe `session["autopilot"] = True`, no
`session["modo"] = "autopilot"`. El markdown debe buscar la clave real.

---

## Seccion 2: Unificacion de patrones

### 2.1 quality-gate.py consume evidence_guard_lib

**Fichero:** `hooks/quality-gate.py`

**Se elimina:**
- Listas `TEST_RUNNERS` y `FAILURE_PATTERNS` propias (~45 lineas)
- Funciones `is_test_command()` y `has_failures()` propias

**Se anade:**
- Import de `is_test_command` y `detect_test_result` desde `evidence_guard_lib`
- Ajuste del path (insertar `_HOOKS_DIR` en `sys.path`, patron ya usado en `evidence-guard.py`)

**Cambio en la logica:**
- `if has_failures(output):` -> `if detect_test_result(output) == "fail":`
- El mensaje de "El Rompe-cosas" no cambia
- La politica de solo informar (siempre exit 0) no cambia

**Razon:** Las listas duplicadas divergen silenciosamente. `evidence_guard_lib.py`
tiene patrones mas refinados (ej. `FAIL` con lookahead negativo `(?![-_])`).
Fuente unica de verdad elimina la divergencia futura.

---

## Seccion 3: Refactor del stop-hook y funcionalidades nuevas

### 3.1 Extraccion de funciones testables

**Fichero:** `hooks/stop-hook.py`

El `main()` actual se descompone en tres funciones:

```python
def should_block(session, flow) -> bool:
    """Decide si la sesion justifica bloquear la parada de Claude.

    Retorna False si: no hay sesion, sesion completada, flujo no definido,
    fase_numero incoherente.
    Retorna True si hay fase activa con gate pendiente.
    """

def build_block_message(session, fase, gate_tipo) -> str:
    """Construye el mensaje de bloqueo con instrucciones segun el tipo de gate.

    Si session.get("autopilot") es True, adapta el mensaje: no pide
    confirmacion del usuario sino que indica investigar el error.
    """

def handle_session_report(session, project_dir) -> None:
    """Genera informe de sesion (completa o parcial).

    Se llama tanto para sesiones completadas como para activas.
    Pasa project_dir explicitamente a generate_report().
    Para sesiones completadas, llama a clear_evidence() despues.
    """
```

El `main()` queda como orquestador:
1. Cargar estado
2. Si no hay sesion -> exit 0
3. Si sesion completada -> `handle_session_report(completada)` -> exit 0
4. Si sesion activa -> `handle_session_report(parcial)` + `should_block` ->
   si True, emitir `build_block_message` como JSON

### 3.2 Informe parcial

**Fichero:** `core/session_report.py`

- `generate_report()` recibe parametro `completed: bool = True`
- Si `completed=False`, el encabezado cambia a "Sesion interrumpida: {comando}"
- `_section_phases()` ya distingue entre completado y detenido; no necesita cambio

### 3.3 Autopilot en el mensaje de bloqueo

**Fichero:** `hooks/stop-hook.py` (dentro de `build_block_message`)

Si `session.get("autopilot")` es True, los mensajes de gate tipo `usuario`
cambian de "Presenta los resultados y pide confirmacion" a "El flujo esta en
autopilot. Investiga por que se ha detenido y resuelve el problema para continuar."

### 3.4 Evidencia sin ventana temporal para informes

**Fichero:** `hooks/evidence_guard_lib.py`

`get_evidence()` ya acepta `max_age_seconds`. Cambio: si `max_age_seconds is None`,
se salta la comprobacion de antiguedad y se incluyen todos los registros.

**Implementacion concreta:** En el bucle de filtrado (linea ~239), antes de
calcular `age` y comparar con `max_age_seconds`, anadir un guard:

```python
if max_age_seconds is not None:
    age = (now - ts).total_seconds()
    if age > max_age_seconds:
        continue
```

Si `max_age_seconds is None`, se salta el bloque entero y el registro se incluye
directamente en `recent`. Esto evita el `TypeError` que ocurriria al comparar
`float <= None` en Python 3.

**Firma actualizada:** Cambiar el valor por defecto del parametro a
`max_age_seconds: Optional[int] = EVIDENCE_MAX_AGE_SECONDS` (ya es asi, pero
documentar que `None` es un valor valido).

El stop-hook llamara con `max_age_seconds=None` para el informe.
Los consumidores en caliente siguen usando el valor por defecto (600s).

### 3.5 Informacion adicional en el informe

**Fichero:** `core/session_report.py`

Dos secciones nuevas:

- `_section_mode(session)`: indica "Modo: autopilot" o "Modo: interactivo"
  segun `session.get("autopilot", False)`.
- `_section_iterations(session)`: muestra iteraciones por fase si alguna tiene
  valor > 0. Lee de `fase_completada["iteraciones"]`.

**Fichero:** `core/orchestrator.py`

En `advance_phase()`, antes de `session["iteraciones_fase"] = 0`, guardar el
valor actual en `fase_completada["iteraciones"]`:

```python
fase_completada = {
    "nombre": ...,
    "resultado": ...,
    "artefactos": ...,
    "completada_en": ...,
    "iteraciones": session.get("iteraciones_fase", 0),  # NUEVO
}
```

### 3.6 Version dinamica en template

**Fichero:** `core/session_report.py`

Leer la version de `.claude-plugin/plugin.json` en lugar del literal `v0.4.1`.
Fallback al string hardcoded si no se puede leer.

**Ruta concreta:** `session_report.py` esta en `core/`. La ruta relativa al
plugin.json es `os.path.join(os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json")`.
Si la lectura falla (fichero ausente, JSON invalido, clave `version` ausente),
se usa `"0.4.2"` como fallback hardcoded.

### 3.7 Propagacion de project_dir

**Fichero:** `hooks/stop-hook.py`

`project_dir = os.getcwd()` se calcula una vez en `main()` y se pasa a
`handle_session_report()`, que a su vez lo pasa a `generate_report()` y
`get_evidence()`. Se elimina la dependencia de `os.getcwd()` dentro de
funciones internas.

### 3.8 Limpieza de evidencia entre sesiones

**Fichero:** `hooks/stop-hook.py` (dentro de `handle_session_report`)

Despues de generar el informe de una sesion completada, llamar a
`clear_evidence(project_dir)`. Solo para sesiones completadas, no parciales
(la evidencia parcial puede ser util si se retoma la sesion).

---

## Seccion 4: Mejora de instrucciones markdown

### 4.0 Persistencia de iteraciones en el markdown

**Ficheros:** `commands/_composicion.md`

La funcion `should_retry_phase()` en Python incrementa `iteraciones_fase` en
memoria pero no persiste el estado. Como Python es especificacion (no motor),
la solucion es instruir a Claude para que persista el estado despues de cada
intento de gate. Anadir al bloque de loop iterativo (seccion 4.2):

> Despues de cada intento de superar una gate (exitoso o no), guarda el estado
> actualizado en `.claude/alfred-dev-state.json`. Esto incluye el contador de
> iteraciones de la fase actual.

**Nota:** Este problema se identifico en la auditoria como alto (should_retry_phase
muta sesion sin persistir). En el modelo actual (Python = especificacion), la
persistencia la ejecuta Claude, no Python. La instruccion en markdown cierra
la brecha en la capa que realmente gobierna.

### 4.1 Verificacion de evidencia en _composicion.md

**Fichero:** `commands/_composicion.md`

Nuevo bloque despues del paso 2b:

> **Paso 2c -- Verificacion de evidencia antes de gates automaticas**
>
> Antes de avanzar una fase con gate automatica o automatica+seguridad, lee
> `.claude/alfred-evidence.json` y comprueba que el ultimo registro tiene
> `result: "pass"` y un timestamp de los ultimos 10 minutos. Si no hay
> evidencia o el ultimo resultado no es `pass`, NO avances. Ejecuta los
> tests primero.

### 4.2 Loop iterativo en los comandos

**Ficheros:** `commands/feature.md`, `commands/fix.md`, `commands/ship.md`

Nuevo bloque en cada comando:

> **Loop iterativo**
>
> Si una gate no se supera al primer intento, corrige los problemas y vuelve
> a intentarlo. Maximo 5 intentos por fase. Si tras 5 intentos la gate sigue
> sin superarse, informa al usuario y espera instrucciones. En modo autopilot,
> si agotas los 5 intentos, deten el flujo e informa del problema.

### 4.3 Correccion del paso 2b

Cubierto en seccion 1.4.

### 4.4 Refuerzo de la excepcion del deploy en ship.md

**Fichero:** `commands/ship.md`

Anadir bloque de enfasis:

> **IMPORTANTE -- Gate de despliegue SIEMPRE interactiva:** Incluso en modo
> autopilot, la fase 4 (despliegue) requiere confirmacion explicita del
> usuario con `AskUserQuestion`. NUNCA auto-apruebes un despliegue a produccion.

---

## Seccion 5: Tests nuevos y adaptados

### 5.1 test_evidence_guard.py

| Test | Proposito |
|------|-----------|
| `test_zero_failures_not_detected_as_fail` | "0 failures" no es fallo |
| `test_go_test_detected_as_pass` | Salida de `go test` devuelve pass |
| `test_unknown_result_affects_all_passing` | `all_passing` es False con unknown |
| `test_get_evidence_no_age_filter` | `max_age_seconds=None` devuelve todo |

### 5.2 test_orchestrator.py

| Test | Proposito |
|------|-----------|
| `test_architecture_gate_is_usuario_seguridad` | Fase 1 de feature tiene gate correcta |
| `test_advance_phase_preserves_iterations` | fase_completada incluye "iteraciones" |
| `test_autopilot_usuario_seguridad_gate` | Documenta comportamiento: `check_gate` con `resultado="aprobado"` satisface la parte de usuario; la de seguridad se evalua con `security_ok`. No es un bug a corregir, es un test de documentacion del comportamiento existente. |

### 5.3 test_stop_hook.py

**Estrategia de importacion:** Las funciones extraidas (`should_block`,
`build_block_message`, `handle_session_report`) se importan directamente del
modulo `hooks.stop_hook` (con guion bajo en lugar de guion, o usando importlib).
El bloque `if __name__ == "__main__"` ya protege la ejecucion del hook al
importar. El fichero de tests anade `HOOKS_DIR` y `PLUGIN_ROOT` a `sys.path`
igual que los tests existentes de otros hooks.

| Test | Proposito |
|------|-----------|
| `test_should_block_active_session` | Devuelve True para sesion activa |
| `test_should_block_completed_session` | Devuelve False para sesion completada |
| `test_build_block_message_autopilot` | Mensaje adaptado sin pedir confirmacion |
| `test_build_block_message_interactive` | Mensaje clasico con confirmacion |
| `test_handle_session_report_partial` | Genera informe con "interrumpido" |
| `test_handle_session_report_complete` | Genera informe normal |

### 5.4 test_session_report.py

| Test | Proposito |
|------|-----------|
| `test_section_mode_autopilot` | Devuelve "Modo: autopilot" |
| `test_section_mode_interactive` | Devuelve "Modo: interactivo" |
| `test_section_iterations` | Genera tabla con iteraciones por fase |
| `test_generate_report_interrupted` | Encabezado dice "interrumpida" |
| `test_dynamic_version` | Lee version de plugin.json |

### 5.5 test_quality_gate.py

- Eliminar tests de patrones propios (cubiertos por test_evidence_guard.py)
- Mantener/crear tests de logica del hook: lectura de stdin, decision de emitir
  mensaje, formato del aviso de "El Rompe-cosas"

---

## Ficheros afectados (resumen)

| Fichero | Tipo de cambio |
|---------|---------------|
| `hooks/evidence_guard_lib.py` | Correccion de patrones, `max_age_seconds=None` |
| `hooks/quality-gate.py` | Unificacion (eliminar patrones, importar de lib) |
| `hooks/stop-hook.py` | Refactor en funciones, informe parcial, autopilot, project_dir, limpieza |
| `core/orchestrator.py` | Gate de arquitectura, iteraciones en fase_completada |
| `core/session_report.py` | Informe parcial, secciones modo/iteraciones, version dinamica |
| `commands/_composicion.md` | Paso 2b corregido, paso 2c nuevo (evidencia), persistencia de iteraciones |
| `commands/feature.md` | Seccion loop iterativo |
| `commands/fix.md` | Seccion loop iterativo |
| `commands/ship.md` | Seccion loop iterativo, refuerzo excepcion deploy |
| `tests/test_evidence_guard.py` | 4 tests nuevos |
| `tests/test_orchestrator.py` | 3 tests nuevos |
| `tests/test_stop_hook.py` | 6 tests nuevos |
| `tests/test_session_report.py` | 5 tests nuevos |
| `tests/test_quality_gate.py` | Adaptacion |

**Total:** 14 ficheros, 18 tests nuevos, 0 ficheros nuevos.
