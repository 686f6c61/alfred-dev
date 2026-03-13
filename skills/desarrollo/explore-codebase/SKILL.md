---
name: explore-codebase
description: "Usar antes de modificar código existente para entender el contexto. Activar cuando el usuario quiera entender el código, saber cómo funciona esto, explorar un repositorio, prepararse antes de modificar, analizar la estructura del proyecto o familiarizarse con una base de código nueva."
---

# Explorar base de código

## Resumen

Este skill se ejecuta antes de tocar cualquier línea de código existente. Su propósito es entender el contexto: cómo está organizado el proyecto, qué patrones sigue, qué convenciones usa y dónde están los puntos críticos. Modificar código sin entender su contexto es la receta para introducir bugs y romper convenciones.

La exploración no modifica nada. Solo lee, analiza y documenta hallazgos que servirán de guía para los cambios posteriores.

## Proceso

1. **Mapear la estructura del proyecto.** Revisar el árbol de directorios para entender la organización general. Identificar:

   - Punto de entrada de la aplicación (main, index, app).
   - Estructura de capas o módulos (src/, lib/, services/, etc.).
   - Ubicación de tests (tests/, __tests__/, *.test.*, *.spec.*).
   - Configuración (package.json, tsconfig, Cargo.toml, pyproject.toml, etc.).
   - Documentación existente (docs/, README, CONTRIBUTING).

2. **Leer la configuración del proyecto.** Los ficheros de configuración revelan decisiones importantes:

   - Dependencias y sus versiones.
   - Scripts disponibles (build, test, lint, format).
   - Configuración de linter y formatter (estilo de código).
   - Configuración de TypeScript, Babel u otros transpiladores.

3. **Identificar patrones y convenciones.** Leer 3-5 ficheros representativos del código para detectar:

   - Estilo de nomenclatura (camelCase, snake_case, PascalCase).
   - Patrón de arquitectura (MVC, hexagonal, clean architecture, etc.).
   - Patrón de manejo de errores (excepciones, Result types, códigos de error).
   - Patrón de inyección de dependencias.
   - Formato de imports y exports.

4. **Revisar los tests existentes.** Los tests son la mejor documentación del comportamiento esperado:

   - Framework de testing utilizado.
   - Estilo de los tests (AAA, Given/When/Then, BDD).
   - Cobertura: qué áreas tienen tests y cuáles no.
   - Fixtures, mocks y utilidades de test.

5. **Mapear dependencias del área a modificar.** Para el módulo o fichero concreto que se va a cambiar:

   - Qué otros módulos lo importan (dependientes).
   - Qué módulos importa él (dependencias).
   - Interfaces públicas que no se pueden romper sin afectar a dependientes.

6. **Documentar hallazgos.** Resumir en un comentario o mensaje al usuario:

   - Patrones detectados que hay que seguir.
   - Riesgos identificados (áreas sin tests, acoplamiento fuerte).
   - Convenciones de naming y formato a respetar.
   - Cualquier "trampa" o peculiaridad del código.

## Qué NO hacer

- **No proponer cambios sin haber leído el código existente.** Modificar código que no se entiende es la forma más rápida de introducir bugs y romper convenciones establecidas.
- **No asumir que sabes cómo funciona algo sin verificarlo.** Incluso si el nombre de una función parece obvio, leer la implementación y los tests. El código heredado está lleno de sorpresas.

## Criterios de éxito

- Se ha revisado la estructura general del proyecto.
- Se han identificado patrones y convenciones existentes.
- Se han leído los tests relacionados con el área a modificar.
- Se han mapeado las dependencias del módulo objetivo.
- No se ha modificado ningún fichero durante la exploración.
- Los hallazgos están documentados antes de empezar a hacer cambios.
