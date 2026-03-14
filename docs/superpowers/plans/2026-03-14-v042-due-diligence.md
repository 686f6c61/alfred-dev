# Alfred Dev v0.4.2 — Plan de implementacion

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir bugs, cerrar huecos funcionales y refactorizar el stop-hook tras la auditoria de due diligence de v0.4.0/v0.4.1.

**Architecture:** Python sigue siendo especificacion de referencia; markdown es el motor real. Los cambios corrigen bugs en Python, unifican patrones divergentes, refactorizan el stop-hook en funciones testables, y mejoran las instrucciones markdown para que Claude ejecute correctamente las features.

**Tech Stack:** Python 3.9+, pytest, markdown (comandos de Claude Code plugin)

**Spec:** `docs/superpowers/specs/2026-03-14-v042-due-diligence-design.md`

---

## Chunk 1: Correcciones de bugs en evidence_guard_lib y orchestrator

### Task 1: Corregir falso positivo "0 failures" en FAILURE_PATTERNS

**Files:**
- Modify: `hooks/evidence_guard_lib.py:65,72`
- Test: `tests/test_evidence_guard.py`

- [ ] **Step 1: Escribir el test que falla**

Anadir al final de `TestDetectTestResult` en `tests/test_evidence_guard.py`:

```python
def test_zero_failures_not_detected_as_fail(self):
    """La salida '0 failures' no debe detectarse como fallo."""
    output = "Tests run: 10, 0 failures, 0 errors"
    self.assertEqual(detect_test_result(output), "pass")

def test_zero_failed_not_detected_as_fail(self):
    """La salida '0 failed' no debe detectarse como fallo."""
    output = "10 passed, 0 failed in 1.5s"
    self.assertEqual(detect_test_result(output), "pass")
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py::TestDetectTestResult::test_zero_failures_not_detected_as_fail tests/test_evidence_guard.py::TestDetectTestResult::test_zero_failed_not_detected_as_fail -v`

Expected: FAIL (los patrones actuales matchean "0 failures" y "0 failed")

- [ ] **Step 3: Corregir los patrones en evidence_guard_lib.py**

En `hooks/evidence_guard_lib.py`, cambiar en FAILURE_PATTERNS:

```python
# ANTES:
r"\d+\s+failures?\b",           # "1 failure", "3 failures"
# DESPUES:
r"[1-9]\d*\s+failures?\b",      # "1 failure", "3 failures" (excluye "0 failures")

# ANTES:
r"\d+\s+failed",
# DESPUES:
r"[1-9]\d*\s+failed",           # "1 failed", "3 failed" (excluye "0 failed")
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py -v`

Expected: PASS (todos, incluidos los nuevos y los existentes)

- [ ] **Step 5: Commit**

```bash
git add hooks/evidence_guard_lib.py tests/test_evidence_guard.py
git commit -m "fix: excluir '0 failures/failed' de los patrones de fallo en evidence guard"
```

---

### Task 2: Anadir soporte para go test en SUCCESS_PATTERNS

**Files:**
- Modify: `hooks/evidence_guard_lib.py:77-85`
- Test: `tests/test_evidence_guard.py`

- [ ] **Step 1: Escribir el test que falla**

Anadir al final de `TestDetectTestResult` en `tests/test_evidence_guard.py`:

```python
def test_go_test_detected_as_pass(self):
    """La salida de go test se detecta como pass."""
    # Salida multilinea realista de go test
    output = "=== RUN   TestFoo\n--- PASS: TestFoo (0.00s)\nPASS\nok  \tgithub.com/foo/bar\t0.003s"
    self.assertEqual(detect_test_result(output), "pass")
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py::TestDetectTestResult::test_go_test_detected_as_pass -v`

Expected: FAIL (devuelve "unknown" porque ningun SUCCESS_PATTERN matchea)

- [ ] **Step 3: Anadir patron de go test**

En `hooks/evidence_guard_lib.py`, anadir al final de SUCCESS_PATTERNS:

```python
r"(?m)^ok\s+\S+",               # go test: "ok  github.com/foo/bar 0.003s" (multiline para anclar ^)
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/evidence_guard_lib.py tests/test_evidence_guard.py
git commit -m "fix: anadir patron de exito para go test en evidence guard"
```

---

### Task 3: Corregir gate de arquitectura en orchestrator

**Files:**
- Modify: `core/orchestrator.py:99`
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Escribir el test que falla**

Anadir a la clase `TestFlows` en `tests/test_orchestrator.py`:

```python
def test_architecture_gate_is_usuario_seguridad(self):
    """La fase de arquitectura debe tener gate usuario+seguridad."""
    fase_arq = FLOWS["feature"]["fases"][1]
    self.assertEqual(fase_arq["nombre"], "arquitectura")
    self.assertEqual(fase_arq["gate_tipo"], "usuario+seguridad")
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_orchestrator.py::TestFlows::test_architecture_gate_is_usuario_seguridad -v`

Expected: FAIL ("usuario" != "usuario+seguridad")

- [ ] **Step 3: Corregir la gate en orchestrator.py**

En `core/orchestrator.py`, en FLOWS["feature"]["fases"][1] (fase "arquitectura"), cambiar:

```python
# ANTES:
"gate_tipo": GATE_USUARIO,
# DESPUES:
"gate_tipo": GATE_USUARIO_SEGURIDAD,
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_orchestrator.py -v`

Expected: PASS (todos, incluido el nuevo). Nota: los tests existentes de `TestGates`
avanzan fases con `advance_phase(session)` sin pasar `security_ok`, que tiene
valor por defecto `True`, asi que no se rompen.

- [ ] **Step 5: Commit**

```bash
git add core/orchestrator.py tests/test_orchestrator.py
git commit -m "fix: gate de arquitectura debe ser usuario+seguridad, no usuario"
```

---

### Task 4: Preservar iteraciones en fase completada

**Files:**
- Modify: `core/orchestrator.py:744-750`
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Escribir el test que falla**

Anadir a la clase `TestLoopIterativo` en `tests/test_orchestrator.py`:

```python
def test_advance_phase_preserves_iterations(self):
    """advance_phase guarda el contador de iteraciones en la fase completada."""
    session = create_session("feature", "Test iteraciones")
    session["iteraciones_fase"] = 3
    session = advance_phase(session, resultado="aprobado")
    fase_completada = session["fases_completadas"][-1]
    self.assertEqual(fase_completada["iteraciones"], 3)
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_orchestrator.py::TestLoopIterativo::test_advance_phase_preserves_iterations -v`

Expected: FAIL (KeyError: 'iteraciones')

- [ ] **Step 3: Anadir iteraciones al dict de fase completada**

En `core/orchestrator.py`, en la funcion `advance_phase()`, modificar la construccion de `fase_completada`:

```python
# ANTES:
fase_completada = {
    "nombre": fases[session["fase_numero"]]["nombre"],
    "resultado": resultado,
    "artefactos": artefactos,
    "completada_en": datetime.now(timezone.utc).isoformat(),
}
# DESPUES:
fase_completada = {
    "nombre": fases[session["fase_numero"]]["nombre"],
    "resultado": resultado,
    "artefactos": artefactos,
    "completada_en": datetime.now(timezone.utc).isoformat(),
    "iteraciones": session.get("iteraciones_fase", 0),
}
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_orchestrator.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: preservar contador de iteraciones en fases completadas"
```

---

### Task 5: Test de documentacion para autopilot con gate usuario+seguridad

**Dependencia:** Requiere que Task 3 este completada (la gate de arquitectura
debe ser GATE_USUARIO_SEGURIDAD para que el test tenga sentido).

**Files:**
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Escribir el test**

Anadir a la clase `TestAutopilot` en `tests/test_orchestrator.py`:

```python
def test_autopilot_usuario_seguridad_auto_approves_user_part(self):
    """En autopilot, GATE_USUARIO_SEGURIDAD aprueba la parte de usuario
    pero evalua la de seguridad. Test de documentacion del comportamiento."""
    session = create_session("feature", "Test autopilot")
    session = advance_phase(session, resultado="aprobado")  # producto -> arquitectura
    # Ahora en fase arquitectura con gate GATE_USUARIO_SEGURIDAD (tras fix de Task 3)
    # Con seguridad OK: debe pasar
    result = is_autopilot_gate_passable(session, security_ok=True)
    self.assertTrue(result["passed"])
    # Con seguridad KO: debe fallar
    result = is_autopilot_gate_passable(session, security_ok=False)
    self.assertFalse(result["passed"])
```

- [ ] **Step 2: Ejecutar test y verificar que pasa**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_orchestrator.py::TestAutopilot::test_autopilot_usuario_seguridad_auto_approves_user_part -v`

Expected: PASS (documenta comportamiento existente, no corrige nada)

- [ ] **Step 3: Commit**

```bash
git add tests/test_orchestrator.py
git commit -m "test: documentar comportamiento de autopilot con gate usuario+seguridad"
```

---

## Chunk 2: Evidencia sin ventana temporal y unificacion de quality-gate

### Task 6: get_evidence con max_age_seconds=None

**Files:**
- Modify: `hooks/evidence_guard_lib.py:230-243`
- Test: `tests/test_evidence_guard.py`

- [ ] **Step 1: Escribir tests que fallan**

Anadir a `TestEvidenceStorage` en `tests/test_evidence_guard.py`:

```python
def test_get_evidence_no_age_filter(self):
    """max_age_seconds=None devuelve todos los registros sin filtrar."""
    # Escribir un registro con timestamp antiguo
    path = os.path.join(self.claude_dir, "alfred-evidence.json")
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    records = [
        {"timestamp": old_ts, "command": "pytest", "result": "pass"},
    ]
    with open(path, "w") as f:
        json.dump(records, f)

    # Con ventana normal: no aparece
    evidence = get_evidence(project_dir=self.tmpdir)
    self.assertFalse(evidence["has_evidence"])

    # Sin ventana: aparece
    evidence = get_evidence(max_age_seconds=None, project_dir=self.tmpdir)
    self.assertTrue(evidence["has_evidence"])
    self.assertEqual(evidence["count"], 1)

def test_unknown_result_affects_all_passing(self):
    """Un resultado unknown hace que all_passing sea False."""
    record_evidence("pytest -v", "pass", project_dir=self.tmpdir)
    record_evidence("pytest -v", "unknown", project_dir=self.tmpdir)
    evidence = get_evidence(project_dir=self.tmpdir)
    self.assertTrue(evidence["has_evidence"])
    self.assertFalse(evidence["all_passing"])
```

- [ ] **Step 2: Ejecutar tests y verificar que fallan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py::TestEvidenceStorage::test_get_evidence_no_age_filter tests/test_evidence_guard.py::TestEvidenceStorage::test_unknown_result_affects_all_passing -v`

Expected: test_get_evidence_no_age_filter FAIL (TypeError: '<=' not supported between float and NoneType). test_unknown_result_affects_all_passing deberia PASS (el comportamiento ya es correcto).

- [ ] **Step 3: Implementar el guard clause**

En `hooks/evidence_guard_lib.py`, en la funcion `get_evidence()`, reemplazar el bloque de filtrado por antiguedad:

```python
# ANTES (lineas ~238-240):
            age = (now - ts).total_seconds()
            if age <= max_age_seconds:
                recent.append(record)
# DESPUES:
            if max_age_seconds is not None:
                age = (now - ts).total_seconds()
                if age > max_age_seconds:
                    continue
            recent.append(record)
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_evidence_guard.py -v`

Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
git add hooks/evidence_guard_lib.py tests/test_evidence_guard.py
git commit -m "feat: permitir max_age_seconds=None en get_evidence para informes sin ventana temporal"
```

---

### Task 7: Unificar quality-gate.py con evidence_guard_lib

**Files:**
- Modify: `hooks/quality-gate.py`
- Test: `tests/test_quality_gate.py`

- [ ] **Step 1: Escribir test de integracion que verifica la importacion**

Anadir en `tests/test_quality_gate.py` un test que verifica que quality-gate
usa las funciones de evidence_guard_lib (este test fallara con el codigo actual
porque quality-gate tiene sus propias funciones):

```python
def test_quality_gate_uses_evidence_guard_lib_functions(self):
    """quality-gate debe importar is_test_command de evidence_guard_lib."""
    import importlib.util
    hooks_dir = os.path.join(os.path.dirname(__file__), "..", "hooks")
    spec = importlib.util.spec_from_file_location(
        "quality_gate", os.path.join(hooks_dir, "quality-gate.py")
    )
    qg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qg)
    # Debe usar la misma funcion que evidence_guard_lib
    from evidence_guard_lib import is_test_command as lib_fn
    self.assertIs(qg.is_test_command, lib_fn)
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_quality_gate.py::test_quality_gate_uses_evidence_guard_lib_functions -v`

Expected: FAIL (quality-gate tiene su propia is_test_command, no la de la lib)

- [ ] **Step 3: Reescribir quality-gate.py**

Reemplazar el contenido de `hooks/quality-gate.py` con:

```python
#!/usr/bin/env python3
"""
Hook PostToolUse para Bash: quality gate de tests.

Intercepta la salida de comandos Bash para detectar si se han ejecutado
tests y, en caso afirmativo, analizar si han fallado. Cuando detecta
fallos, informa por stderr con la voz de "El Rompe-cosas" (QA).

Delega la deteccion de comandos y resultados a ``evidence_guard_lib``
para mantener una unica fuente de verdad en los patrones.

Solo actua sobre comandos que coincidan con runners de tests conocidos.
El resto de comandos Bash pasan sin inspeccion.
"""

import json
import os
import sys

# Anadir el directorio de hooks al path para importar la libreria
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from evidence_guard_lib import is_test_command, detect_test_result


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae el comando ejecutado y su salida,
    y determina si hay tests fallidos. Si los hay, emite un aviso
    por stderr con la voz de El Rompe-cosas.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(
            f"[quality-gate] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La monitorizacion de tests esta desactivada para este comando.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    tool_output = data.get("tool_output", {})

    command = tool_input.get("command", "")

    if not command or not is_test_command(command):
        sys.exit(0)

    stdout = tool_output.get("stdout", "")
    stderr_out = tool_output.get("stderr", "")
    output = f"{stdout}\n{stderr_out}"

    if detect_test_result(output) == "fail":
        print(
            "\n"
            "[El Rompe-cosas] He pillado tests rotos\n"
            "\n"
            "Los tests no pasan. Sorpresa: ninguna.\n"
            "No se avanza con tests en rojo. Asi funciona esto.\n"
            "\n"
            "Repasa la salida, corrige los fallos y vuelve a ejecutar.\n"
            "Ese edge case que no contemplaste? Lo encontre.\n",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Adaptar test_quality_gate.py**

Eliminar los tests de patrones propios (ya cubiertos por test_evidence_guard.py).
Mantener los tests de logica del hook existentes. El test de Step 1 ahora
debe pasar porque quality-gate importa de la lib.

- [ ] **Step 5: Ejecutar todos los tests**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_quality_gate.py tests/test_evidence_guard.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add hooks/quality-gate.py tests/test_quality_gate.py
git commit -m "refactor: quality-gate consume patrones de evidence_guard_lib (fuente unica)"
```

---

## Chunk 3: Refactor del stop-hook

### Task 8: Extraer funciones testables del stop-hook

**Files:**
- Modify: `hooks/stop-hook.py`
- Test: `tests/test_stop_hook.py`

- [ ] **Step 1: Escribir tests para should_block**

Reescribir `tests/test_stop_hook.py`. El fichero actual testea indirectamente via
orchestrator. El nuevo testea las funciones extraidas directamente. Nota: el fichero
`stop-hook.py` tiene un guion en el nombre, asi que se importa con importlib.

Anadir al principio del fichero:

```python
import importlib.util

# Importar el modulo stop-hook (tiene guion en el nombre, no es un
# identificador Python valido, asi que usamos spec_from_file_location)
_plugin_root = os.path.join(os.path.dirname(__file__), "..")
_hooks_dir = os.path.join(_plugin_root, "hooks")
sys.path.insert(0, _plugin_root)
sys.path.insert(0, _hooks_dir)

_stop_hook_path = os.path.join(_hooks_dir, "stop-hook.py")
_spec = importlib.util.spec_from_file_location("stop_hook", _stop_hook_path)
stop_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stop_hook)
```

Anadir clase nueva:

```python
class TestShouldBlock(unittest.TestCase):
    """Verifica la funcion should_block."""

    def test_completed_session_does_not_block(self):
        session = create_session("feature", "Test")
        session["fase_actual"] = "completado"
        flow = FLOWS["feature"]
        self.assertFalse(stop_hook.should_block(session, flow))

    def test_active_session_blocks(self):
        session = create_session("feature", "Test")
        flow = FLOWS["feature"]
        self.assertTrue(stop_hook.should_block(session, flow))

    def test_incoherent_fase_numero_does_not_block(self):
        session = create_session("feature", "Test")
        session["fase_numero"] = 999
        flow = FLOWS["feature"]
        self.assertFalse(stop_hook.should_block(session, flow))
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_stop_hook.py::TestShouldBlock -v`

Expected: FAIL (AttributeError: module has no attribute 'should_block')

- [ ] **Step 3: Refactorizar stop-hook.py**

Extraer `should_block`, `build_block_message` y `handle_session_report` de `main()`.
El `main()` queda como orquestador simple que llama a las tres funciones.

```python
def should_block(session, flow):
    """Decide si la sesion justifica bloquear la parada de Claude."""
    fase_actual = session.get("fase_actual", "completado")
    if fase_actual == "completado":
        return False

    fase_numero = session.get("fase_numero", 0)
    fases = flow.get("fases", [])

    if not isinstance(fase_numero, int):
        return False
    if fase_numero >= len(fases):
        return False

    return True


def build_block_message(session, fase, gate_tipo):
    """Construye el mensaje de bloqueo con instrucciones segun el tipo de gate."""
    comando = session.get("comando", "")
    descripcion_fase = fase.get("descripcion", "")
    descripcion_sesion = session.get("descripcion", "Sin descripcion")
    agentes = fase.get("agentes", [])
    agentes_str = ", ".join(agentes) if agentes else "sin agentes asignados"
    nombre_fase = fase.get("nombre", "desconocida")
    is_autopilot = session.get("autopilot", False)

    reason_parts = [
        f"Eh eh eh, para el carro. Aun no hemos terminado. Hay una sesion '{comando}' activa.",
        "",
        f"Fase actual: {nombre_fase}",
        f"Descripcion: {descripcion_fase}",
        f"Agentes asignados: {agentes_str}",
        f"Objetivo de la sesion: {descripcion_sesion}",
        "",
        f"Gate pendiente: {gate_tipo}",
        "",
    ]

    if "automatico" in gate_tipo:
        reason_parts.append(
            "Necesitas que los tests pasen (gate automatica). "
            "Ejecuta los tests y verifica que estan en verde antes de avanzar."
        )
    if "seguridad" in gate_tipo:
        reason_parts.append(
            "Necesitas pasar la auditoria de seguridad. "
            "Revisa las vulnerabilidades pendientes."
        )
    if "usuario" in gate_tipo:
        if is_autopilot:
            reason_parts.append(
                "El flujo esta en autopilot. Investiga por que se ha detenido "
                "y resuelve el problema para continuar."
            )
        else:
            reason_parts.append(
                "Necesitas la aprobacion del usuario para avanzar. "
                "Presenta los resultados y pide confirmacion."
            )
    if gate_tipo == "libre":
        reason_parts.append(
            "La gate es libre, pero aun queda trabajo por hacer en esta fase. "
            "Completa la tarea antes de parar."
        )

    return "\n".join(reason_parts)


def handle_session_report(session, project_dir, completed=True):
    """Genera informe de sesion (completa o parcial)."""
    try:
        evidence = None
        evidence_lib_available = False
        try:
            from evidence_guard_lib import get_evidence, clear_evidence
            evidence_lib_available = True
            evidence = get_evidence(
                max_age_seconds=None,
                project_dir=project_dir,
            )
        except ImportError:
            print(
                "[Alfred Dev] Aviso: no se pudo cargar evidence_guard_lib. "
                "El informe se generara sin evidencia de tests.",
                file=sys.stderr,
            )

        report_path = generate_report(
            session,
            evidence=evidence,
            project_dir=project_dir,
            completed=completed,
        )
        print(
            f"[Alfred Dev] Informe de sesion guardado en: {report_path}",
            file=sys.stderr,
        )

        # Limpiar evidencia solo para sesiones completadas
        if completed and evidence_lib_available:
            try:
                clear_evidence(project_dir=project_dir)
            except OSError as e:
                print(
                    f"[Alfred Dev] Aviso: no se pudo limpiar la evidencia: {e}",
                    file=sys.stderr,
                )
    except (OSError, ValueError, RuntimeError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo generar el informe de sesion: {e}",
            file=sys.stderr,
        )
```

Luego, reescribir `main()` para usar las tres funciones:

```python
def main():
    project_dir = os.getcwd()
    state_path = os.path.join(project_dir, ".claude", "alfred-dev-state.json")

    session = load_state(state_path)
    if session is None:
        sys.exit(0)

    fase_actual = session.get("fase_actual", "completado")

    if fase_actual == "completado":
        handle_session_report(session, project_dir, completed=True)
        sys.exit(0)

    comando = session.get("comando", "")
    if comando not in FLOWS:
        print(
            f"[Alfred Dev] Aviso: la sesion referencia el flujo '{comando}' "
            f"que no esta definido.",
            file=sys.stderr,
        )
        sys.exit(0)

    flow = FLOWS[comando]

    # Generar informe parcial
    handle_session_report(session, project_dir, completed=False)

    if not should_block(session, flow):
        sys.exit(0)

    fase_numero = session.get("fase_numero", 0)
    fase = flow["fases"][fase_numero]
    gate_tipo = fase.get("gate_tipo", "libre")

    reason = build_block_message(session, fase, gate_tipo)

    output = {
        "decision": "block",
        "reason": reason,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)
```

- [ ] **Step 4: Ejecutar todos los tests del stop-hook**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_stop_hook.py -v`

Expected: PASS (tanto los tests existentes como los nuevos)

- [ ] **Step 5: Commit**

```bash
git add hooks/stop-hook.py tests/test_stop_hook.py
git commit -m "refactor: extraer should_block, build_block_message y handle_session_report del stop-hook"
```

---

### Task 9: Tests de build_block_message (interactivo y autopilot)

**Files:**
- Test: `tests/test_stop_hook.py`

- [ ] **Step 1: Escribir tests**

Anadir clase nueva en `tests/test_stop_hook.py`:

```python
class TestBuildBlockMessage(unittest.TestCase):
    """Verifica la construccion del mensaje de bloqueo."""

    def _make_fase(self, gate_tipo="usuario"):
        return {
            "nombre": "producto",
            "agentes": ["product-owner"],
            "descripcion": "Fase de prueba",
            "gate_tipo": gate_tipo,
        }

    def test_interactive_user_gate_asks_for_approval(self):
        """En modo interactivo, la gate de usuario pide confirmacion."""
        session = create_session("feature", "Test")
        fase = self._make_fase("usuario")
        msg = stop_hook.build_block_message(session, fase, "usuario")
        self.assertIn("aprobacion del usuario", msg.lower())
        self.assertNotIn("autopilot", msg.lower())

    def test_autopilot_user_gate_does_not_ask_for_approval(self):
        """En autopilot, la gate de usuario no pide confirmacion."""
        session = create_session("feature", "Test")
        session["autopilot"] = True
        fase = self._make_fase("usuario")
        msg = stop_hook.build_block_message(session, fase, "usuario")
        self.assertIn("autopilot", msg.lower())
        self.assertNotIn("aprobacion del usuario", msg.lower())

    def test_automatic_gate_mentions_tests(self):
        """La gate automatica menciona tests."""
        session = create_session("feature", "Test")
        fase = self._make_fase("automatico")
        msg = stop_hook.build_block_message(session, fase, "automatico")
        self.assertIn("tests", msg.lower())
```

- [ ] **Step 2: Ejecutar tests y verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_stop_hook.py::TestBuildBlockMessage -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_stop_hook.py
git commit -m "test: verificar mensajes de bloqueo en modo interactivo y autopilot"
```

---

### Task 10: Tests de handle_session_report (parcial y completo)

**Files:**
- Test: `tests/test_stop_hook.py`

- [ ] **Step 1: Escribir tests**

Anadir clase nueva en `tests/test_stop_hook.py`:

```python
class TestHandleSessionReport(unittest.TestCase):
    """Verifica la generacion de informes desde el stop-hook."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generates_complete_report(self):
        """Una sesion completada genera informe normal."""
        session = {
            "comando": "feature",
            "descripcion": "Login",
            "fase_actual": "completado",
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
            ],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:30:00+00:00",
        }
        stop_hook.handle_session_report(session, self.tmpdir, completed=True)
        reports = os.listdir(os.path.join(self.tmpdir, "docs", "alfred-reports"))
        self.assertEqual(len(reports), 1)
        with open(os.path.join(self.tmpdir, "docs", "alfred-reports", reports[0])) as f:
            content = f.read()
        self.assertIn("Informe de sesion", content)

    def test_generates_partial_report(self):
        """Una sesion parcial genera informe con 'interrumpida'."""
        session = {
            "comando": "feature",
            "descripcion": "Login",
            "fase_actual": "desarrollo",
            "fase_numero": 2,
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
            ],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:30:00+00:00",
        }
        stop_hook.handle_session_report(session, self.tmpdir, completed=False)
        reports = os.listdir(os.path.join(self.tmpdir, "docs", "alfred-reports"))
        self.assertEqual(len(reports), 1)
        with open(os.path.join(self.tmpdir, "docs", "alfred-reports", reports[0])) as f:
            content = f.read()
        self.assertIn("interrumpida", content.lower())
```

- [ ] **Step 2: Ejecutar tests y verificar que fallan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_stop_hook.py::TestHandleSessionReport -v`

Expected: FAIL (generate_report no acepta parametro `completed` todavia)

- [ ] **Step 3: Commit (tests en rojo, se resuelven en Task 11)**

Estos tests fallan porque `generate_report` no acepta `completed` todavia.
Se commitean como tests pendientes que Task 11 resolvera.

```bash
git add tests/test_stop_hook.py
git commit -m "test: anadir tests de handle_session_report (pendientes de Task 11)"
```

---

## Chunk 4: Mejoras en session_report.py

### Task 11: Informe parcial y secciones nuevas en session_report.py

**Files:**
- Modify: `core/session_report.py`
- Test: `tests/test_session_report.py`

- [ ] **Step 1: Escribir tests para las secciones nuevas**

Anadir en `tests/test_session_report.py`:

```python
from core.session_report import _section_mode, _section_iterations


class TestSectionMode(unittest.TestCase):
    """Verifica la seccion de modo de sesion."""

    def test_autopilot(self):
        session = {"autopilot": True}
        result = _section_mode(session)
        self.assertIn("autopilot", result.lower())

    def test_interactive(self):
        session = {}
        result = _section_mode(session)
        self.assertIn("interactivo", result.lower())


class TestSectionIterations(unittest.TestCase):
    """Verifica la seccion de iteraciones por fase."""

    def test_with_iterations(self):
        session = {
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado", "iteraciones": 0},
                {"nombre": "desarrollo", "resultado": "aprobado", "iteraciones": 3},
            ],
        }
        result = _section_iterations(session)
        self.assertIn("desarrollo", result)
        self.assertIn("3", result)

    def test_without_iterations(self):
        session = {
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado", "iteraciones": 0},
            ],
        }
        result = _section_iterations(session)
        self.assertEqual(result, "")


class TestGenerateReportInterrupted(unittest.TestCase):
    """Verifica informes de sesiones interrumpidas."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dynamic_version_from_plugin_json(self):
        """El informe lee la version de plugin.json."""
        session = {
            "comando": "feature",
            "descripcion": "Test version",
            "fase_actual": "completado",
            "fases_completadas": [],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:05:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir)
        with open(report_path) as f:
            content = f.read()
        # Debe contener la version del plugin, no un literal hardcoded
        self.assertIn("Alfred Dev v", content)
        # No debe contener la version antigua hardcoded
        self.assertNotIn("v0.4.1", content)

    def test_interrupted_report(self):
        session = {
            "comando": "feature",
            "descripcion": "Test interrumpido",
            "fase_actual": "desarrollo",
            "fases_completadas": [],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:15:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir, completed=False)
        with open(report_path) as f:
            content = f.read()
        self.assertIn("interrumpida", content.lower())
```

- [ ] **Step 2: Ejecutar tests y verificar que fallan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_session_report.py::TestSectionMode tests/test_session_report.py::TestSectionIterations tests/test_session_report.py::TestGenerateReportInterrupted -v`

Expected: FAIL (funciones no existen, parametro `completed` no existe)

- [ ] **Step 3: Implementar las secciones y el parametro completed**

En `core/session_report.py`:

**3a.** Anadir `_section_mode`:

```python
def _section_mode(session: Dict[str, Any]) -> str:
    """Genera la seccion de modo de sesion (autopilot o interactivo)."""
    is_autopilot = session.get("autopilot", False)
    modo = "autopilot" if is_autopilot else "interactivo"
    return f"## Modo de sesion\n\nModo: **{modo}**\n"
```

**3b.** Anadir `_section_iterations`:

```python
def _section_iterations(session: Dict[str, Any]) -> str:
    """Genera la seccion de iteraciones por fase si alguna tuvo reintentos."""
    fases = session.get("fases_completadas", [])
    fases_con_iteraciones = [
        f for f in fases if f.get("iteraciones", 0) > 0
    ]
    if not fases_con_iteraciones:
        return ""

    lines = ["## Iteraciones por fase\n"]
    lines.append("| Fase | Iteraciones |")
    lines.append("|------|------------|")
    for fase in fases_con_iteraciones:
        lines.append(f"| {fase['nombre']} | {fase['iteraciones']} |")

    return "\n".join(lines) + "\n"
```

**3c.** Anadir template para sesiones interrumpidas y parametro `completed`:

Anadir un segundo template:

```python
_REPORT_TEMPLATE_INTERRUPTED = """# Sesion interrumpida: {comando}

**Fecha:** {fecha}
**Duracion estimada:** {duracion}
**Descripcion:** {descripcion}

---

{secciones}

---

*Generado automaticamente por Alfred Dev v{version}*
"""
```

**3d.** Anadir funcion `_get_plugin_version`:

```python
def _get_plugin_version() -> str:
    """Lee la version del plugin desde plugin.json. Fallback a hardcoded."""
    try:
        plugin_path = os.path.join(
            os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json"
        )
        with open(plugin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("version", "0.4.2")
    except (OSError, json.JSONDecodeError, KeyError):
        return "0.4.2"
```

**3e.** Modificar `generate_report()` para aceptar `completed` y usar las secciones nuevas:

Anadir `completed: bool = True` al signature. Seleccionar template segun `completed`.
Incluir `_section_mode` y `_section_iterations` en el ensamblaje de secciones.
Usar `_get_plugin_version()` en lugar del literal.

Actualizar el template original para usar `{version}`. El template completo queda:

```python
_REPORT_TEMPLATE = """# Informe de sesion: {comando}

**Fecha:** {fecha}
**Duracion estimada:** {duracion}
**Descripcion:** {descripcion}

---

{secciones}

---

*Generado automaticamente por Alfred Dev v{version}*
"""
```

**IMPORTANTE:** Este cambio del template y la adicion de `version=version` al
`.format()` deben hacerse en el mismo paso. Si solo se cambia uno, los tests
existentes de `TestGenerateReport` romperian con `KeyError`.

Y en `generate_report()`:

```python
template = _REPORT_TEMPLATE if completed else _REPORT_TEMPLATE_INTERRUPTED
version = _get_plugin_version()

report_content = template.format(
    comando=comando,
    fecha=fecha,
    duracion=duracion,
    descripcion=descripcion,
    secciones=secciones_text,
    version=version,
)
```

- [ ] **Step 4: Ejecutar todos los tests**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/test_session_report.py tests/test_stop_hook.py -v`

Expected: PASS (todos, incluidos los de Task 10 que ahora deben pasar)

- [ ] **Step 5: Commit**

```bash
git add core/session_report.py tests/test_session_report.py
git commit -m "feat: informe parcial, secciones de modo/iteraciones, version dinamica"
```

---

## Chunk 5: Instrucciones markdown

### Task 12: Actualizar _composicion.md

**Files:**
- Modify: `commands/_composicion.md`

- [ ] **Step 1: Corregir paso 2b (clave autopilot)**

En `commands/_composicion.md`, paso 2b, cambiar:

```markdown
<!-- ANTES: -->
2. Lee `.claude/alfred-dev-state.json` y comprueba si tiene `"modo": "autopilot"`.

<!-- DESPUES: -->
2. Lee `.claude/alfred-dev-state.json` y comprueba si tiene `"autopilot": true`.
```

- [ ] **Step 2: Anadir paso 2c (verificacion de evidencia)**

Despues del paso 2b, anadir:

```markdown
## Paso 2c -- Verificacion de evidencia antes de gates automaticas

Antes de avanzar una fase con gate automatica o automatica+seguridad, lee
`.claude/alfred-evidence.json` y comprueba que el ultimo registro tiene
`result: "pass"` y un timestamp de los ultimos 10 minutos. Si no hay
evidencia o el ultimo resultado no es `pass`, NO avances. Ejecuta los
tests primero.
```

- [ ] **Step 3: Anadir instruccion de persistencia de iteraciones**

Despues del paso 2c, anadir:

```markdown
## Paso 2d -- Persistencia de estado tras gates

Despues de cada intento de superar una gate (exitoso o no), guarda el estado
actualizado en `.claude/alfred-dev-state.json`. Esto incluye el contador de
iteraciones de la fase actual.
```

- [ ] **Step 4: Commit**

```bash
git add commands/_composicion.md
git commit -m "docs: corregir clave autopilot, anadir verificacion de evidencia y persistencia de iteraciones"
```

---

### Task 13: Anadir loop iterativo y refuerzo de deploy a los comandos

**Files:**
- Modify: `commands/feature.md`
- Modify: `commands/fix.md`
- Modify: `commands/ship.md`

- [ ] **Step 1: Anadir seccion de loop iterativo a feature.md**

Antes de la seccion "HARD-GATES" en `commands/feature.md`, anadir:

```markdown
## Loop iterativo

Si una gate no se supera al primer intento, corrige los problemas y vuelve a intentarlo. Maximo 5 intentos por fase. Si tras 5 intentos la gate sigue sin superarse, informa al usuario y espera instrucciones. En modo autopilot, si agotas los 5 intentos, deten el flujo e informa del problema -- no sigas reintentando indefinidamente.
```

- [ ] **Step 2: Anadir seccion de loop iterativo a fix.md**

Al final de `commands/fix.md`, anadir el mismo bloque.

- [ ] **Step 3: Anadir loop iterativo y refuerzo de deploy a ship.md**

En `commands/ship.md`, anadir el bloque de loop iterativo y ademas:

```markdown
**IMPORTANTE -- Gate de despliegue SIEMPRE interactiva:** Incluso en modo autopilot, la fase 4 (despliegue) requiere confirmacion explicita del usuario con `AskUserQuestion`. NUNCA auto-apruebes un despliegue a produccion.
```

- [ ] **Step 4: Commit**

```bash
git add commands/feature.md commands/fix.md commands/ship.md
git commit -m "docs: anadir loop iterativo a los comandos y reforzar excepcion de deploy"
```

---

## Chunk 6: Version bump, tests finales y cierre

### Task 14: Bump de version a 0.4.2

**Files:**
- Modify: `.claude-plugin/plugin.json:4`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Actualizar version en plugin.json**

Cambiar `"version": "0.4.1"` a `"version": "0.4.2"`.

- [ ] **Step 2: Anadir entrada en CHANGELOG.md**

Anadir antes de la entrada de v0.4.1:

```markdown
## [0.4.2] - 2026-03-14

### Fixed

- **Falso positivo en evidence guard**: el patron `\d+ failures` detectaba "0 failures" como fallo. Corregido para excluir el cero.
- **Gate de arquitectura mal tipada**: la fase de arquitectura del flujo feature tenia gate `usuario` en lugar de `usuario+seguridad`, haciendo inoperante la validacion de seguridad.
- **Patrones divergentes**: `quality-gate.py` tenia patrones de deteccion propios que divergian de `evidence_guard_lib.py`. Unificado para usar una sola fuente de verdad.
- **Clave de autopilot inconsistente**: los comandos markdown buscaban `"modo": "autopilot"` pero el codigo escribia `"autopilot": true`. Corregido.

### Added

- **Soporte para go test**: la salida de `go test` se detecta correctamente como exito en evidence guard.
- **Informe de sesiones parciales**: el stop-hook genera informe cuando una sesion se interrumpe, no solo cuando se completa.
- **Modo autopilot en informes**: los informes de sesion indican si se ejecutaron en modo autopilot o interactivo.
- **Iteraciones por fase en informes**: los informes muestran cuantos reintentos tuvo cada fase.
- **Verificacion de evidencia en markdown**: instruccion explicita para que Claude lea `alfred-evidence.json` antes de avanzar gates automaticas.
- **Loop iterativo documentado**: los comandos feature, fix y ship incluyen instrucciones de loop iterativo (max 5 reintentos por fase).
- **Persistencia de iteraciones**: instruccion para que Claude persista el estado despues de cada intento de gate.
- **Gate de deploy siempre interactiva**: refuerzo explicito de que el deploy nunca se auto-aprueba.

### Changed

- **stop-hook refactorizado**: extraidas funciones `should_block`, `build_block_message` y `handle_session_report` para testabilidad.
- **Mensaje de bloqueo adaptado a autopilot**: en modo autopilot, el stop-hook no pide confirmacion del usuario sino que indica investigar el error.
- **Evidencia sin ventana temporal para informes**: `get_evidence(max_age_seconds=None)` devuelve todos los registros sin filtrar por antiguedad.
- **Version dinamica en informes**: el template lee la version de `plugin.json` en lugar de tenerla hardcoded.
- **Limpieza de evidencia entre sesiones**: al completar una sesion, se limpia el fichero de evidencia para evitar contaminacion cruzada.
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "chore: bump version a 0.4.2"
```

---

### Task 15: Suite completa de tests

- [ ] **Step 1: Ejecutar toda la suite de tests**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python3 -m pytest tests/ -v`

Expected: PASS (todos los tests, incluidos los 18 nuevos)

- [ ] **Step 2: Verificar que no hay regresiones**

Confirmar que los 91 tests originales siguen pasando y que los nuevos suman al total.

- [ ] **Step 3: Commit final si hay cambios pendientes**

Si alguna correccion menor fue necesaria para que los tests pasen, commitear.
