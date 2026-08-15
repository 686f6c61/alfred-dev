---
description: "Protocolo interno de documentación viva: qué fichero se actualiza en cada gate."
---

# Documentación viva del proyecto

Protocolo compartido. Lo leen `feature`, `fix`, `quick`, `spike`, `audit`, `ship`,
`map-codebase` y `discuss`. No es un slash command.

## Paso 0 -- esqueleto

Antes de la primera fase (o al mapear / discutir), ejecuta:

```bash
python3 .claude/alfred-continuity.py sync-project-docs "$PWD"
```

Eso crea, si faltan:

- `docs/project/README.md` (índice)
- `docs/project/architecture.md`
- `docs/project/compliance.md`
- `docs/project/threat-model.md`
- `docs/project/dependencies.md`
- `docs/adr/`

No rellena prosa. Los esqueletos llevan `<!-- alfred-doc:scaffold -->`.

## Qué se toca en cada momento

Solo actualiza lo que la fase ha cambiado. No reescribas el resto.

| Momento | Quién | Ficheros |
|---------|-------|----------|
| `discuss` | Alfred | índice (existe) + `discovery.md` |
| `map-codebase` | helper + Alfred | índice + esqueleto de arquitectura |
| Producto aprobado | product-owner | PRD; el índice se refresca |
| Arquitectura | architect + security-officer | `architecture.md` (relleno), ADR si hay decisión, `threat-model.md` (relleno) |
| Dependencia nueva | architect o security-officer | `dependencies.md` |
| Desarrollo / quick / fix | tech-writer (sync corto) + senior-dev | índice; cabeceras/docstrings del código tocado; `current.md` |
| Calidad / audit | security-officer | `compliance.md` con evidencia |
| Documentación de cierre / ship | tech-writer | índice, CHANGELOG, release notes |
| Pausa | helper | handoff (sin tocar architecture/compliance) |

## Antes de cerrar una gate

```bash
python3 .claude/alfred-continuity.py check-project-docs "$PWD" --command <comando> --phase <fase>
```

Si el helper sale distinto de 0, la gate no se declara superada. Rellena el
hueco y vuelve a comprobar.

Un documento cuenta como relleno cuando tiene `<!-- alfred-doc:filled -->` o
cuando ya existía con contenido real (sin marcador de esqueleto).

## ADR

Si la fase de arquitectura (o un spike) toma una decisión nueva:

```bash
python3 .claude/alfred-continuity.py next-adr "$PWD" --title "Título corto de la decisión"
```

Luego el architect rellena el fichero con el skill `write-adr`.

## Skills

- `sync-project-docs` -- cómo sincronizar sin inventar prosa
- `write-adr` -- cómo cerrar un ADR
- `evaluate-dependency` -- cómo anotar una dependencia
- `compliance-check` -- cómo rellenar el registro
- `threat-model` -- cómo rellenar el modelo

## El Escriba

Tras cada fase (no solo al final), lanza un sync corto del `tech-writer`:

1. `sync-project-docs`
2. actualizar solo las secciones tocadas
3. `check-project-docs` de la fase actual

En `quick` y `fix` el sync es mínimo: índice + nota en `current.md`. Un ADR
solo si el cambio mueve un límite de arquitectura.
