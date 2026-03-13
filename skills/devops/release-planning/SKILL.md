---
name: release-planning
description: "Planificar y ejecutar releases: inventario de cambios, versionado semantico, changelog, notas de release y publicacion. Usar antes de cada version nueva."
---

# Planificacion de releases

El usuario quiere preparar una release del proyecto. Este skill guia el proceso completo desde la definicion de la version hasta la publicacion, asegurando que el changelog, las notas de release y la documentacion estan al dia.

> **Nota:** Este skill cubre el proceso completo de release. Para generar solo las entradas de changelog, usar `documentacion/changelog`.

## Resumen

Una release bien planificada no es solo un `git tag`. Requiere revisar que se incluye, comunicar los cambios a los usuarios y garantizar que la version sigue un esquema coherente. Este skill sistematiza ese proceso para que ninguna release salga sin changelog, sin notas o con una version incoherente.

## Proceso

### Fase 1: Inventario de cambios (devops-engineer)

1. Listar todos los commits desde la ultima release (`git log --oneline <last-tag>..HEAD`).
2. Clasificar los cambios por tipo: feat, fix, refactor, docs, test, chore.
3. Identificar breaking changes que requieran bump de version major.
4. Verificar que todos los cambios tienen tests asociados.

**Artefacto:** listado clasificado de cambios.

### Fase 2: Versionado semantico

Determinar la nueva version segun semver (MAJOR.MINOR.PATCH):

| Tipo de cambio | Bump |
|----------------|------|
| Breaking change en API publica | MAJOR |
| Nueva funcionalidad retrocompatible | MINOR |
| Correccion de bug | PATCH |
| Solo docs, tests, refactor interno | PATCH (o ninguno si no hay cambios funcionales) |

Si hay dudas, consultar al usuario antes de decidir.

### Fase 3: Changelog (tech-writer)

Generar o actualizar el fichero CHANGELOG.md con formato Keep a Changelog:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Anadido
- Descripcion del cambio (#PR o commit)

### Cambiado
- Descripcion del cambio

### Corregido
- Descripcion del bug corregido

### Eliminado
- Funcionalidad o API eliminada (si aplica)
```

### Fase 4: Notas de release

Redactar las notas de release para GitHub/GitLab:

1. Titulo: version + nombre descriptivo si procede.
2. Resumen de 2-3 frases con los cambios mas relevantes.
3. Lista detallada de cambios (del changelog).
4. Instrucciones de actualizacion si hay breaking changes.
5. Agradecimientos a contribuidores si los hay.

### Fase 5: Publicacion (devops-engineer)

1. Actualizar la version en los ficheros del proyecto (package.json, plugin.json, etc.).
2. Crear el commit de release.
3. Crear el tag con `git tag vX.Y.Z`.
4. Publicar la release en GitHub con `gh release create`.
5. Verificar que la release aparece correctamente.

**Artefacto:** release publicada con changelog y notas.

## Criterios de exito

- Todos los commits desde la ultima release estan clasificados por tipo.
- La version nueva sigue estrictamente semver, con bump coherente respecto a los cambios incluidos.
- El fichero CHANGELOG.md esta actualizado con la nueva entrada antes de crear el tag.
- Las notas de release estan redactadas y publicadas en la plataforma correspondiente.
- Los ficheros de version del proyecto (package.json, plugin.json, etc.) reflejan la nueva version.
- Los tests pasan antes de crear el tag y publicar la release.

## Que NO hacer

- **No publicar una release sin changelog actualizado.** El changelog es la comunicacion principal con los usuarios del proyecto. Una release sin changelog obliga a los consumidores a leer commits para entender que cambio, lo que genera desconfianza y dificulta las actualizaciones.
- **No hacer bump de version major sin documentar los breaking changes.** Un bump major sin guia de migracion deja a los usuarios sin saber que rompe ni como adaptarse. Los breaking changes deben estar documentados con instrucciones claras de actualizacion.
- **No crear tags sin verificar que los tests pasan.** Un tag apunta a un commit concreto y representa un compromiso de estabilidad. Etiquetar codigo que no pasa los tests es publicar software defectuoso con apariencia de version estable.
