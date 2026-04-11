---
name: release
description: "Crear releases con versionado semantico, notas y artefactos"
disable-model-invocation: true
---

# Crear releases con versionado semantico

## Resumen

Este skill gestiona el proceso completo de creacion de una release en GitHub, desde la determinacion de la version correcta segun versionado semantico hasta la publicacion con notas de cambios y artefactos adjuntos.

Una buena release no es solo un tag en el repositorio: es el punto de comunicacion con los usuarios y el equipo sobre que ha cambiado, que se ha corregido y que deben tener en cuenta al actualizar.

## Proceso

1. **Determinar la version siguiente.** Analizar los commits desde la ultima release para decidir el incremento de version segun semver (MAJOR.MINOR.PATCH):

   - **PATCH** (0.1.0 -> 0.1.1): correcciones de bugs que no cambian la API publica.
   - **MINOR** (0.1.1 -> 0.2.0): funcionalidades nuevas compatibles hacia atras.
   - **MAJOR** (0.2.0 -> 1.0.0): cambios que rompen compatibilidad con versiones anteriores.

   En caso de duda, consultar con el usuario. Un cambio que parece menor puede tener implicaciones de compatibilidad.

2. **Generar el changelog.** Revisar los commits y PRs mergeadas desde la ultima release. Clasificar los cambios en las siguientes categorias:

   - **Anadido**: funcionalidades nuevas.
   - **Cambiado**: cambios en funcionalidades existentes.
   - **Corregido**: correcciones de errores.
   - **Seguridad**: correcciones de vulnerabilidades.
   - **Eliminado**: funcionalidades o APIs eliminadas.
   - **Obsoleto**: funcionalidades marcadas para futura eliminacion.

   Cada entrada debe ser comprensible para un usuario final, no solo para desarrolladores. Evitar mensajes tipo "refactorizar modulo X"; en su lugar, explicar el efecto visible.

3. **Actualizar ficheros de version.** Si el proyecto tiene ficheros que contienen la version (package.json, pyproject.toml, Cargo.toml, version.txt), actualizarlos con el nuevo numero.

4. **Crear el tag.** Crear un tag anotado con el formato `vMAJOR.MINOR.PATCH`:

   ```
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

5. **Crear la release en GitHub.** Usar `gh release create` con las notas generadas:

   ```
   gh release create v1.2.0 --title "v1.2.0" --notes-file RELEASE_NOTES.md
   ```

   Si hay artefactos que adjuntar (binarios compilados, paquetes, ficheros de distribucion), incluirlos como assets de la release.

6. **Adjuntar artefactos si procede.** Para proyectos que generan binarios o paquetes distribuibles:

   ```
   gh release upload v1.2.0 dist/app-linux-amd64 dist/app-darwin-arm64
   ```

   Verificar que los artefactos son accesibles y descargables desde la pagina de la release.

7. **Verificar la release.** Comprobar que la release aparece correctamente en GitHub, que las notas se renderizan bien, que los artefactos estan disponibles y que el tag apunta al commit correcto.

## Que NO hacer

- No crear releases sin changelog: el numero de version solo no aporta informacion suficiente.
- No saltar versiones sin justificacion (de 1.0.0 a 1.5.0, por ejemplo).
- No incluir artefactos de depuracion o desarrollo en la release.
- No publicar una release sin verificar que los tests pasan en el commit etiquetado.
