---
name: changelog
description: "Usar para generar entradas de changelog siguiendo Keep a Changelog"
---

# Generar changelog

## Resumen

Este skill genera entradas de changelog siguiendo el formato Keep a Changelog (keepachangelog.com). El changelog es el documento que los usuarios consultan para saber que ha cambiado entre versiones. Esta escrito para personas, no para maquinas: el lenguaje debe ser claro y orientado al impacto para el usuario, no a los detalles internos de implementacion.

Un buen changelog responde a la pregunta "que ha cambiado que me afecta" sin requerir que el lector entienda el codigo.

## Proceso

1. **Identificar los cambios a documentar.** Revisar el historial de Git desde la ultima version publicada:

   - Commits desde el ultimo tag de version.
   - Pull requests mergeados.
   - Issues cerrados.

   Filtrar los cambios internos (refactoring, actualizacion de CI) que no afectan al usuario, a menos que sean relevantes (como mejoras de rendimiento).

2. **Clasificar cada cambio en su categoria.** Keep a Changelog define seis categorias:

   | Categoria | Descripcion | Ejemplo |
   |-----------|-------------|---------|
   | **Added** | Funcionalidad nueva | "Soporte para autenticacion con Google" |
   | **Changed** | Cambio en funcionalidad existente | "El limite de subida de archivos pasa de 5MB a 20MB" |
   | **Deprecated** | Funcionalidad que se eliminara en una version futura | "El endpoint /v1/users se sustituira por /v2/users en la version 3.0" |
   | **Removed** | Funcionalidad eliminada | "Se elimina el soporte para IE11" |
   | **Fixed** | Correccion de errores | "Corregido error que impedia guardar formularios con campos vacios" |
   | **Security** | Correccion de vulnerabilidades | "Actualizada dependencia X para corregir CVE-YYYY-NNNN" |

3. **Redactar cada entrada.** Reglas de redaccion:

   - Escribir en lenguaje del usuario, no del desarrollador. "Ahora puedes exportar tus datos en CSV" en vez de "Se anade endpoint GET /export?format=csv".
   - Empezar con verbo en infinitivo o participio segun la categoria.
   - Ser concreto: evitar "varias mejoras de rendimiento" sin especificar cuales.
   - Incluir enlace al issue o PR cuando exista, para quien quiera profundizar.

4. **Formato del encabezado de version:**

   ```markdown
   ## [1.2.0] - 2024-03-15

   ### Added
   - Soporte para exportar datos en formato CSV (#42)
   - Nuevo filtro de busqueda por fecha (#38)

   ### Fixed
   - Corregido error al paginar resultados con mas de 1000 registros (#45)

   ### Security
   - Actualizada dependencia lodash a 4.17.21 para corregir CVE-2021-23337 (#47)
   ```

5. **Mantener la seccion [Unreleased].** Los cambios que aun no forman parte de una version se agrupan bajo `[Unreleased]` en la parte superior del changelog. Al publicar una nueva version, estos cambios se mueven bajo el encabezado de la nueva version.

6. **Verificar enlaces.** Si el changelog incluye enlaces a issues o PRs, verificar que los enlaces son correctos y accesibles.

7. **Ubicacion del fichero.** El changelog se guarda como `CHANGELOG.md` en la raiz del proyecto, siguiendo la convencion estandar.

## Criterios de exito

- Los cambios estan clasificados en las categorias correctas de Keep a Changelog.
- El lenguaje esta orientado al usuario, no al desarrollador.
- Cada entrada es concreta y evita generalidades vagas.
- Hay enlaces a issues o PRs cuando estan disponibles.
- El formato de version sigue versionado semantico (MAJOR.MINOR.PATCH).
- La seccion [Unreleased] existe para cambios no publicados.
