# Tests

Alfred Dev 0.6.0 usa pruebas por capas. La suite Python cubre la lógica local del plugin; los scripts de auditoría validan la superficie pública que Claude Code carga; los smokes manuales ejecutan Claude CLI con el plugin real; y la revisión humana comprueba la calidad generativa que no se puede reducir a una aserción estable.

Esta página es la guía operativa para desarrollar sin romper la release. Si solo estas tocando una función pequeña, empieza por `python3 -m pytest tests/ -v`. Si estas preparando publicación, usa los gates de release descritos más abajo.

---

## Comandos rápidos

Para ejecutar toda la suite local:

```bash
python3 -m pytest tests/ -v
```

Para medir cobertura del core y los adaptadores Python:

```bash
python3 -m pytest tests/ -v --cov=core --cov=mcp
```

Para validar la superficie publicable del plugin:

```bash
npm run release:audit
npm run release:audit:full
```

Para validar también la web de la rama `Alfred-Astro`:

```bash
python3 scripts/release_audit.py --with-site
npm --prefix site run check
npm --prefix site run build
```

Para comprobar que la autenticación de Claude CLI permite smokes manuales:

```bash
npm run release:audit:manual:preflight
```

---

## Gates de release 0.6.0

La release 0.6.0 no depende de un único comando mágico. Cada gate cubre una frontera distinta y evita que una mejora local rompa la instalación global, el selector de comandos, el MCP de memoria o la documentación pública.

| Gate | Comando | Qué valida |
|------|---------|------------|
| Suite local | `python3 -m pytest tests/ -v` | Core Python, hooks, MCP, instaladores, comandos, contratos de prompts y scripts auxiliares. |
| Auditoría base | `npm run release:audit` | Versionado 0.6.0, manifiestos, inventario publicable, frontmatter soportado, nombres de herramientas, package files y docs de auditoría. |
| Auditoría completa | `npm run release:audit:full` | Auditoría base más checks de continuidad, herramientas MCP y contratos externos sin side effects. |
| Web | `python3 scripts/release_audit.py --with-site` | Coherencia entre plugin, docs y landing Astro; evita claims públicos que no estén cubiertos por evidencia. |
| Claude commands | `npm run release:audit:claude:commands` | Descubrimiento real de comandos con Claude CLI cuando el entorno local lo permite. |
| Preflight manual | `npm run release:audit:manual:preflight` | Autenticación, disponibilidad de Claude CLI y preparación para smokes manuales. |
| Evidencia manual | `npm run release:audit:manual:evidence` | Ejecuta casos smoke contra el worktree y genera evidencia en `docs/manual-smoke-0.6.0.json`. |
| Evidencia instalada | `npm run release:audit:manual:evidence:installed` | Repite smokes contra la caché instalada de usuario para detectar drift entre worktree e instalación. |
| Revisión humana | `npm run release:audit:manual:review` | Bloquea publicación si la plantilla de revisión no esta aprobada, fechada y anotada caso por caso. |

El gate `release:audit:prepublish` encadena la auditoría completa, el preflight de Claude CLI y las revisiones humanas del worktree y de la instalación. Debe fallar si la revisión manual sigue pendiente; no se debe rellenar esa aprobación de forma automática.

---

## Cobertura principal

La suite de `tests/` ya no cubre solo el core. En 0.6.0 incluye contratos para casi todas las superficies que Claude Code consume:

- **Core y memoria**: orquestador, configuración, continuidad, memoria SQLite, compactación, sincronización, UI local y sanitización de secretos.
- **MCP**: servidor `alfred-memory`, forma JSON-RPC, herramientas publicadas y fallback cuando la memoria no esta disponible.
- **Hooks**: captura de actividad, guardas de comandos peligrosos, evidencias, secretos, lecturas sensibles, quality gates, prefetch, session start, stop hook y compactación.
- **Instaladores**: `install.sh`, `install.ps1`, `uninstall.sh` y `uninstall.ps1`, incluyendo instalación global de usuario, alias `/alfred` y limpieza del shim obsoleto en `~/.claude/commands/alfred.md`.
- **Comandos y agentes**: contratos de frontmatter, nombres de herramientas soportadas, ausencia de referencias operativas a `Task`, composición contextual de Alfred y comandos publicados en `plugin.json`.
- **Skills**: inventario de 62 `SKILL.md` en 15 dominios, campos de frontmatter soportados, colisiones de nombres, longitud de listing y skills manuales con `disable-model-invocation: true`.
- **Release y publicación**: scripts de auditoría, evidencia manual, reporte de revisión, freshness de caché instalada y consistencia de versión.
- **Selina y visual**: catálogo de estilos, dirección visual, variantes, helper visual y servidor local de apoyo.

Los tests siguen usando `unittest` como estilo interno y `pytest` como runner. Cada fichero se puede ejecutar de forma aislada cuando quieres iterar rápido:

```bash
python3 -m pytest tests/test_release_audit.py -q
python3 -m pytest tests/test_install_script.py -q
python3 -m pytest tests/test_memory_server.py -q
```

---

## Patrones de testing usados

Los tests que necesitan disco usan `tempfile.NamedTemporaryFile` o `tempfile.TemporaryDirectory` y limpian en `tearDown()` o `try/finally`. Ningun test debe escribir estado permanente en el repositorio, en `~/.claude/` ni en una base de datos real salvo que el propio test lo aísle en un directorio temporal.

Los modulos del core se importan añadiendo la raiz del proyecto a `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

Los ficheros con guion, como `hooks/spelling-guard.py`, se cargan con `importlib.util.spec_from_file_location` porque no se pueden importar con sintaxis Python normal.

Los tests de memoria verifican a dos niveles: usan la API pública de `MemoryDB` y, cuando hace falta, abren SQLite directamente para comprobar tablas, índices, permisos, WAL y relaciones persistidas.

Los tests de sanitización construyen patrones sensibles en runtime para no dejar secretos falsos completos en el código fuente:

```python
fake_key = "AKIA" + "TESTMEMORYDB1234"
fake_sk = "sk-" + "a" * 25
```

---

## Integraciones externas

Algunos checks viven detrás de flags porque pueden necesitar credenciales, red, Docker, GitHub CLI o servicios externos:

```bash
npm run release:audit:external
npm run release:audit:external:preflight
```

Estos comandos no deben ejecutarse como parte silenciosa de una suite local si el entorno no esta preparado. Su función es probar contratos externos de forma explícita: GitHub, Codex CLI, SonarQube/Docker y otras integraciones que pueden tener side effects o depender de autenticación.

---

## Límites honestos de cobertura

### Calidad generativa

Los prompts de comandos, agentes y skills se pueden auditar por estructura, herramientas, referencias y coherencia, pero no se puede garantizar con un test determinista que Claude produzca siempre una respuesta excelente. Por eso 0.6.0 añade `scripts/manual_smoke.py`, plantillas de revisión humana y un gate que exige aprobación explícita caso por caso antes de publicar.

### Sesiones reales de Claude Code

La suite simula hooks, MCP y discovery hasta donde es razonable, pero la carga final depende de Claude Code, su caché de plugins, el estado de autenticación y el selector interactivo. La evidencia de release debe incluir smokes en worktree e instalación global de usuario, especialmente para `/alfred`, `/alfred-dev:*` y `claude -p`.

### Servicios con side effects

GitHub, SonarQube, Docker y cualquier herramienta externa con credenciales se prueban con preflights y contratos. Los tests no deben crear issues, releases, contenedores persistentes ni cambios remotos sin una bandera explícita y documentación de evidencia.

### Plataformas no presentes

Los instaladores de Bash y PowerShell tienen tests de contrato, pero una release pública debe revisarse en macOS/Linux y, cuando sea posible, en Windows real o PowerShell disponible. Si solo se ha probado una plataforma, esa limitación debe quedar reflejada en `docs/release-readiness-0.6.0.md`.

---

## Como añadir un nuevo test

1. Crea un fichero `tests/test_<modulo>.py` con clases `unittest.TestCase` y nombres de test descriptivos.
2. Usa directorios temporales para cualquier escritura.
3. Evita depender de una instalación real en `~/.claude/` salvo que el test cree un `HOME` temporal.
4. Si el cambio afecta comandos, agentes, skills, hooks, MCP, instaladores o package files, añade también un contrato en `scripts/release_audit.py` o en una suite existente.
5. Ejecuta el test nuevo, la suite relacionada y al menos `npm run release:audit` antes de cerrar el cambio.

Ejemplo mínimo:

```python
#!/usr/bin/env python3
"""Tests para mi_modulo."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.mi_modulo import funcion_a_testear


class TestMiModulo(unittest.TestCase):
    def test_comportamiento_esperado(self):
        self.assertEqual(funcion_a_testear("entrada"), "salida")


if __name__ == "__main__":
    unittest.main()
```
