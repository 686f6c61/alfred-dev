---
name: project-docs
description: "Documentar el proyecto completo en docs/ para dar contexto absoluto a cualquier desarrollador. Activar ante: documentacion del proyecto, crear docs, organizar documentacion, estructura de docs"
---

# Documentación completa del proyecto

## Resumen

Este skill genera una documentación exhaustiva del proyecto en el directorio `docs/`. El objetivo es que cualquier persona que llegue al proyecto tenga contexto absoluto sin necesidad de preguntar: qué hace el proyecto, cómo funciona, cómo se configura, cómo se contribuye y por qué se tomaron las decisiones que se tomaron.

No se trata de documentar por documentar, sino de crear una referencia viva que reduzca el tiempo de onboarding y evite la pérdida de conocimiento cuando alguien deja el equipo.

## Proceso

### Paso 1: auditar la documentación existente

- Listar los ficheros de documentación actuales (README, docs/, wikis, comentarios de código).
- Identificar qué está documentado, qué falta y qué está desactualizado.
- Comprobar si hay decisiones de arquitectura sin documentar (ADRs pendientes).

### Paso 2: crear la estructura base en docs/

Generar los siguientes documentos si no existen:

```
docs/
  README.md              -- índice de la documentación
  architecture.md        -- visión general de la arquitectura
  getting-started.md     -- guía de inicio rápido
  development.md         -- guía de desarrollo (setup, tests, linting)
  api/                   -- documentación de API (si aplica)
  decisions/             -- ADRs (Architecture Decision Records)
```

### Paso 3: documentar cada sección

Para cada documento:

- **architecture.md**: componentes principales, flujo de datos, dependencias entre módulos, diagramas (Mermaid o texto). No repetir el código, explicar el diseño.
- **getting-started.md**: prerrequisitos, instalación, configuración, primera ejecución. Probarlo desde cero para verificar que funciona.
- **development.md**: cómo ejecutar tests, linting, formateo. Convenciones de código. Flujo de trabajo con Git.
- **API**: endpoints, parámetros, respuestas, códigos de error, ejemplos con curl.
- **decisions/**: un ADR por cada decisión no obvia. Formato: contexto, decisión, consecuencias.

### Paso 4: enlazar desde el README

El README principal debe apuntar a `docs/` para los detalles. El README es la puerta de entrada; la documentación completa está dentro.

## Qué NO hacer

- No duplicar información que ya está en el código (JSDoc, docstrings). Referenciar, no copiar.
- No documentar lo obvio. Documentar lo que no es evidente leyendo el código.
- No crear documentación que nadie va a mantener. Mejor poco y actualizado que mucho y obsoleto.
