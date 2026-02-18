---
name: explore-codebase
description: "Usar antes de modificar codigo existente para entender el contexto"
---

# Explorar base de codigo

## Resumen

Este skill se ejecuta antes de tocar cualquier linea de codigo existente. Su proposito es entender el contexto: como esta organizado el proyecto, que patrones sigue, que convenciones usa y donde estan los puntos criticos. Modificar codigo sin entender su contexto es la receta para introducir bugs y romper convenciones.

La exploracion no modifica nada. Solo lee, analiza y documenta hallazgos que serviran de guia para los cambios posteriores.

## Proceso

1. **Mapear la estructura del proyecto.** Revisar el arbol de directorios para entender la organizacion general. Identificar:

   - Punto de entrada de la aplicacion (main, index, app).
   - Estructura de capas o modulos (src/, lib/, services/, etc.).
   - Ubicacion de tests (tests/, __tests__/, *.test.*, *.spec.*).
   - Configuracion (package.json, tsconfig, Cargo.toml, pyproject.toml, etc.).
   - Documentacion existente (docs/, README, CONTRIBUTING).

2. **Leer la configuracion del proyecto.** Los ficheros de configuracion revelan decisiones importantes:

   - Dependencias y sus versiones.
   - Scripts disponibles (build, test, lint, format).
   - Configuracion de linter y formatter (estilo de codigo).
   - Configuracion de TypeScript, Babel u otros transpiladores.

3. **Identificar patrones y convenciones.** Leer 3-5 ficheros representativos del codigo para detectar:

   - Estilo de nomenclatura (camelCase, snake_case, PascalCase).
   - Patron de arquitectura (MVC, hexagonal, clean architecture, etc.).
   - Patron de manejo de errores (excepciones, Result types, codigos de error).
   - Patron de inyeccion de dependencias.
   - Formato de imports y exports.

4. **Revisar los tests existentes.** Los tests son la mejor documentacion del comportamiento esperado:

   - Framework de testing utilizado.
   - Estilo de los tests (AAA, Given/When/Then, BDD).
   - Cobertura: que areas tienen tests y cuales no.
   - Fixtures, mocks y utilidades de test.

5. **Mapear dependencias del area a modificar.** Para el modulo o fichero concreto que se va a cambiar:

   - Que otros modulos lo importan (dependientes).
   - Que modulos importa el (dependencias).
   - Interfaces publicas que no se pueden romper sin afectar a dependientes.

6. **Documentar hallazgos.** Resumir en un comentario o mensaje al usuario:

   - Patrones detectados que hay que seguir.
   - Riesgos identificados (areas sin tests, acoplamiento fuerte).
   - Convenciones de naming y formato a respetar.
   - Cualquier "trampa" o peculiaridad del codigo.

## Criterios de exito

- Se ha revisado la estructura general del proyecto.
- Se han identificado patrones y convenciones existentes.
- Se han leido los tests relacionados con el area a modificar.
- Se han mapeado las dependencias del modulo objetivo.
- No se ha modificado ningun fichero durante la exploracion.
- Los hallazgos estan documentados antes de empezar a hacer cambios.
