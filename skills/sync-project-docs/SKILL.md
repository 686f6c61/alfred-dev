---
name: sync-project-docs
description: "Usar para sincronizar la documentación viva del proyecto después de una fase. También: actualizar docs/project, índice, architecture.md, compliance.md, threat-model."
---

# Sincronizar documentación viva

## Resumen

Tras una fase, actualiza solo lo que ha cambiado. El helper crea esqueletos
y comprueba la gate. Tú escribes el contenido.

## Proceso

1. Esqueleto e índice:

   ```bash
   python3 .claude/alfred-continuity.py sync-project-docs "$PWD"
   ```

2. Lee `docs/project/README.md` y el protocolo `commands/_docs_vivas.md`.

3. Actualiza únicamente los ficheros de la fase. Si no hubo API nueva, no
   toques una guía de API. Si no hubo decisión, no inventes un ADR.

4. Cuando un esqueleto tenga contenido real, deja `<!-- alfred-doc:filled -->`
   y quita `<!-- alfred-doc:scaffold -->`.

5. Comprueba la gate:

   ```bash
   python3 .claude/alfred-continuity.py check-project-docs "$PWD" --command <comando> --phase <fase>
   ```

6. Si el helper falla, no declares la fase cerrada.

## En quick y fix

Sync mínimo: índice + `docs/project/current.md`. ADR solo si el cambio mueve
un límite (auth, persistencia, integración).

## Criterios de éxito

- El índice refleja el estado real (`scaffold` o `filled`).
- No hay prosa inventada sobre código que no se ha tocado.
- `check-project-docs` sale 0 antes de cerrar la gate.

## Qué NO hacer

- No reescribas todo `docs/` en cada fase.
- No copies el chat al Markdown.
- No marques `filled` si siguen los `_(pendiente)_`.
