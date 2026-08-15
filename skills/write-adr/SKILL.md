---
name: write-adr
description: "Usar para escribir o cerrar un Architecture Decision Record. También: ADR, docs/adr, decisión de stack, persistencia, autenticación o límites de arquitectura."
---

# Escribir un ADR

## Resumen

Documenta una decisión arquitectónica significativa en `docs/adr/`. Un ADR no
es un diario: solo se escribe si hay una elección real (stack, persistencia,
auth, límites, integración).

## Proceso

1. Crea el esqueleto con el helper. No inventes el número a mano:

   ```bash
   python3 .claude/alfred-continuity.py next-adr "$PWD" --title "Título corto"
   ```

2. Lee `templates/adr.md` si existe y el fichero recién creado.

3. Rellena, con hechos del repo:

   - contexto y restricciones
   - al menos dos opciones reales, con pros y contras
   - decisión y por qué
   - consecuencias y deuda asumida

4. Estado inicial: `propuesto` hasta que el usuario o la gate de arquitectura
   lo acepten. Entonces `aceptado`. Si más tarde cambia, crea un ADR nuevo que
   apunte al anterior; no reescribas el viejo.

5. Sustituye `<!-- alfred-doc:scaffold -->` por `<!-- alfred-doc:filled -->`.

6. Ejecuta `sync-project-docs` para refrescar el índice.

7. Si la decisión es de diseño, regístrala también con `memory_log_decision`.
   La memoria no sustituye al ADR.

## Criterios de éxito

- El fichero está en `docs/adr/ADR-NNN-....md`.
- Hay al menos dos opciones evaluadas.
- La decisión y sus consecuencias se pueden leer sin el chat.
- El marcador es `filled`.

## Qué NO hacer

- No abras un ADR por un rename o un ajuste local de `quick`.
- No dejes `_(pendiente)_` en un ADR que declaras cerrado.
- No copies un ADR genérico que no menciona el repo.
