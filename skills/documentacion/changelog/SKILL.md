---
name: changelog
description: "Usar para generar entradas de changelog siguiendo Keep a Changelog. Activar ante: generar changelog, documentar cambios, Keep a Changelog, notas de version, que ha cambiado"
---

# Generar changelog

## Resumen

Este skill genera entradas de changelog siguiendo el formato Keep a Changelog (keepachangelog.com). El changelog es el documento que los usuarios consultan para saber qué ha cambiado entre versiones. Está escrito para personas, no para máquinas: el lenguaje debe ser claro y orientado al impacto para el usuario, no a los detalles internos de implementación.

Un buen changelog responde a la pregunta "qué ha cambiado que me afecta" sin requerir que el lector entienda el código.

> **Nota:** este skill genera entradas de changelog individuales. Para el proceso completo de publicación de una release (versionado, changelog, notas, publicación), usar el protocolo release-planning.

## Proceso

1. **Identificar los cambios a documentar.** Revisar el historial de Git desde la última versión publicada:

   - Commits desde el último tag de versión.
   - Pull requests mergeados.
   - Issues cerrados.

   Filtrar los cambios internos (refactoring, actualización de CI) que no afectan al usuario, a menos que sean relevantes (como mejoras de rendimiento).

2. **Clasificar cada cambio en su categoría.** Keep a Changelog define seis categorías:

   | Categoría | Descripción | Ejemplo |
   |-----------|-------------|---------|
   | **Added** | Funcionalidad nueva | "Soporte para autenticación con Google" |
   | **Changed** | Cambio en funcionalidad existente | "El límite de subida de archivos pasa de 5MB a 20MB" |
   | **Deprecated** | Funcionalidad que se eliminará en una versión futura | "El endpoint /v1/users se sustituirá por /v2/users en la versión 3.0" |
   | **Removed** | Funcionalidad eliminada | "Se elimina el soporte para IE11" |
   | **Fixed** | Corrección de errores | "Corregido error que impedía guardar formularios con campos vacíos" |
   | **Security** | Corrección de vulnerabilidades | "Actualizada dependencia X para corregir CVE-YYYY-NNNN" |

3. **Redactar cada entrada.** Reglas de redacción:

   - Escribir en lenguaje del usuario, no del desarrollador. "Ahora puedes exportar tus datos en CSV" en vez de "Se añade endpoint GET /export?format=csv".
   - Empezar con verbo en infinitivo o participio según la categoría.
   - Ser concreto: evitar "varias mejoras de rendimiento" sin especificar cuáles.
   - Incluir enlace al issue o PR cuando exista, para quien quiera profundizar.

4. **Formato del encabezado de versión:**

   ```markdown
   ## [1.2.0] - 2024-03-15

   ### Added
   - Soporte para exportar datos en formato CSV (#42)
   - Nuevo filtro de búsqueda por fecha (#38)

   ### Fixed
   - Corregido error al paginar resultados con más de 1000 registros (#45)

   ### Security
   - Actualizada dependencia lodash a 4.17.21 para corregir CVE-2021-23337 (#47)
   ```

5. **Mantener la sección [Unreleased].** Los cambios que aún no forman parte de una versión se agrupan bajo `[Unreleased]` en la parte superior del changelog. Al publicar una nueva versión, estos cambios se mueven bajo el encabezado de la nueva versión.

6. **Verificar enlaces.** Si el changelog incluye enlaces a issues o PRs, verificar que los enlaces son correctos y accesibles.

7. **Ubicación del fichero.** El changelog se guarda como `CHANGELOG.md` en la raíz del proyecto, siguiendo la convención estándar.

## Criterios de éxito

- Los cambios están clasificados en las categorías correctas de Keep a Changelog.
- El lenguaje está orientado al usuario, no al desarrollador.
- Cada entrada es concreta y evita generalidades vagas.
- Hay enlaces a issues o PRs cuando están disponibles.
- El formato de versión sigue versionado semántico (MAJOR.MINOR.PATCH).
- La sección [Unreleased] existe para cambios no publicados.
