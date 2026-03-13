---
name: migration-guide
description: "Generar guías de migración entre versiones para los usuarios del proyecto. Activar ante: guia de migracion, actualizar version, breaking changes, instrucciones de actualizacion"
---

# Guía de migración entre versiones

## Resumen

Este skill genera una guía de migración cuando el proyecto lanza una versión con cambios que afectan a los usuarios existentes (breaking changes, APIs deprecadas, cambios de configuración). La guía explica exactamente qué cambió, por qué y qué pasos debe seguir el usuario para actualizar sin romperse.

Las migraciones sin guía son la causa principal de que los usuarios se queden en versiones antiguas. Una buena guía de migración facilita la adopción y reduce la carga de soporte.

## Proceso

### Paso 1: identificar los cambios

- Revisar el changelog y los commits desde la última versión estable.
- Clasificar cada cambio: breaking change, deprecación, nuevo comportamiento, eliminación.
- Para cada breaking change, documentar: qué era antes, qué es ahora, por qué se cambió.

### Paso 2: escribir la guía

Crear `docs/migration-vX.Y.md` con la estructura:

1. **Resumen de cambios**: lista breve de lo que cambia en esta versión.

2. **Breaking changes**: para cada uno:
   - Qué hacía antes y qué hace ahora.
   - Código de ejemplo antes/después.
   - Pasos exactos para migrar.

3. **Deprecaciones**: funcionalidades que siguen funcionando pero se eliminarán en una versión futura. Indicar la alternativa recomendada.

4. **Nuevas funcionalidades**: lo que se ha añadido y cómo usarlo.

5. **Pasos de migración**: checklist ordenado que el usuario puede seguir de arriba a abajo.

6. **Problemas conocidos**: si hay limitaciones o bugs conocidos en la nueva versión, mencionarlos con workaround si existe.

### Paso 3: verificar la guía

- Simular la migración siguiendo los pasos de la guía.
- Verificar que los ejemplos de código son correctos y ejecutables.
- Comprobar que no falta ningún breaking change.

## Qué NO hacer

- No omitir breaking changes por pequeños que sean. Si algo deja de funcionar, se documenta.
- No asumir que el usuario lee el changelog. La guía de migración es autosuficiente.
- No mezclar instrucciones de migración con documentación de la nueva versión. Son documentos distintos.
