# Contribuir y publicar cambios

Este documento explica cómo mantener Alfred Dev sin romper la superficie pública del plugin. En este repo no basta con que el código funcione: también tienen que quedar alineados prompts, manifiestos, instaladores, documentación, tests de contrato y versión pública.

La regla práctica es esta: cualquier cambio que altere la superficie visible del plugin debe venir acompañado de sus contratos y su documentación correspondiente.

---

## Qué revisar antes de cambiar nada

Según la zona que toques, estas son las superficies que se suelen mover juntas:

| Si cambias... | Revisa también... |
|---|---|
| `commands/*.md` | `.claude-plugin/plugin.json`, `README.md`, `docs/commands.md`, tests de contrato |
| `agents/*.md` | `.claude-plugin/plugin.json`, `docs/agents/`, `docs/personality.md`, tests relacionados |
| `skills/` | `.claude-plugin/plugin.json`, `docs/skills.md`, tests de superficie pública |
| `hooks/` | `hooks/hooks.json`, `docs/hooks.md`, tests del hook |
| `core/memory*` | `docs/memory.md`, `docs/mcp.md`, tests de memoria/UI/MCP |
| instaladores | `docs/installation.md`, `README.md`, tests de instalación |
| versión pública | `README.md`, `.claude-plugin/plugin.json`, marketplace, tests de consistencia |

---

## Cómo validar cambios

La validación mínima del repo pasa por `pytest`:

```bash
python3 -m pytest tests/ -v
```

Si el cambio toca contratos públicos, versión o documentación sensible, conviene prestar atención especial a estas familias de tests:

- `test_public_surface_contract.py`
- `test_version_consistency.py`
- `test_pm_contract.py`
- `test_progress_contract.py`
- `test_memory_ui_contract.py`
- `test_install_script.py`
- `test_uninstall_script.py`

Si el cambio afecta a una zona concreta, ejecuta además su suite específica.

---

## CI actual

La automatización de GitHub vive en `.github/workflows/test.yml`.

Hoy la CI:

- se ejecuta en `push` y `pull_request` sobre `main`;
- job `test`: Python `3.10`–`3.13`, `pytest`, y en `3.12` `release_audit` + cobertura 60%;
- job `plugin`: misma secuencia en Ubuntu, macOS y Windows (`fail-fast: false`); instala Claude CLI, valida, instala 0.7.0 desde el checkout, enseña el inventario y desinstala;
- no instala FastMCP (el servidor local tiene fallback);
- no usa el `curl` de GitHub `main`; instala el checkout de la CI.

Esto convierte la matriz de Python en parte del contrato del repo: si añades una dependencia o sintaxis no compatible con alguno de esos intérpretes, rompes la release.

---

## Versionado y release

El plugin tiene varias superficies donde la versión debe mantenerse coherente:

- `.claude-plugin/plugin.json`
- `README.md`
- instaladores y desinstaladores, cuando proceda
- documentación técnica afectada
- tests de consistencia de versión
- landing, cuando el cambio también la afecta en la rama `Alfred-Astro`

No conviene tratar la versión como un detalle cosmético. En Alfred Dev, la versión es una señal contractual que se cruza desde tests y documentación.

---

## Cambios en prompts

Los prompts de commands y agentes son parte del producto. Aunque no sean “código ejecutable” en el sentido clásico, sí tienen contrato público y pueden romper comportamiento.

Al modificarlos:

1. mantén alineado el manifiesto del plugin;
2. revisa los tests de contrato correspondientes;
3. actualiza la documentación si cambia el comportamiento observable;
4. evita introducir claims que no estén respaldados por el repo.

---

## Cambios en documentación

La documentación en `docs/` debe seguir dos reglas:

- describir el estado real del repo, no planes futuros;
- contener solo documentación estable y útil para el plugin.

Las auditorías, planes temporales o notas de reorganización deben vivir en `internal/`, no en `docs/`.

---

## Publicar sin dejar drift

Antes de cerrar una release o un cambio amplio, revisa explícitamente:

1. si cambió la superficie pública de comandos, agentes o skills;
2. si los contadores públicos siguen siendo correctos;
3. si la documentación aún coincide con el código;
4. si los tests de contrato y consistencia siguen verdes;
5. si la rama `Alfred-Astro` necesita reflejar el cambio en la landing.

Ese paso final evita uno de los problemas más comunes del repo: que el código quede bien pero la narrativa pública se quede una versión atrás.
