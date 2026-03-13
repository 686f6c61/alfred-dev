---
name: evaluate-dependencies
description: "Usar para evaluar si una dependencia merece la pena antes de añadirla. Activar cuando el usuario quiera añadir una librería, saber si merece la pena esta dependencia, evaluar un paquete antes de instalarlo, hacer npm install o pip install de algo nuevo, buscar alternativas a una librería o decidir si implementar algo internamente."
---

# Evaluar dependencias

## Resumen

Este skill analiza una dependencia externa antes de añadirla al proyecto. Cada dependencia es código de terceros que se incorpora a la cadena de suministro del software, con sus implicaciones de seguridad, mantenimiento y tamaño. La pregunta no es solo "resuelve mi problema" sino "el coste de adoptarla es menor que el coste de implementarla internamente".

El resultado es una recomendación fundamentada: añadir la dependencia, rechazarla o implementar la funcionalidad internamente.

## Proceso

1. **Identificar la necesidad concreta.** Qué problema resuelve la dependencia. Cuánto código propio ahorra. Si es una utilidad puntual o una pieza central de la arquitectura.

2. **Evaluar los criterios técnicos:**

   | Criterio | Qué verificar |
   |----------|--------------|
   | Tamaño del bundle | Peso en KB/MB. Impacto en tiempos de carga si es frontend. Usar herramientas como `bundlephobia` para npm. |
   | Tree-shaking | Se puede importar solo lo necesario o es todo-o-nada. |
   | Mantenimiento activo | Fecha del último commit, frecuencia de releases, número de mantenedores. Un solo mantenedor es un riesgo. |
   | Issues y PRs | Ratio de issues abiertas vs cerradas. PRs pendientes sin revisar durante meses. |
   | Vulnerabilidades | Historial de CVEs. Comprobar en bases de datos de vulnerabilidades (Snyk, GitHub Advisory). |
   | Licencia | Compatible con la licencia del proyecto. MIT y Apache 2.0 suelen ser seguras. GPL puede ser problemática en proyectos propietarios. |
   | Dependencias transitivas | Cuántas dependencias arrastra consigo. Cada una es un vector de riesgo adicional. |
   | Documentación | Calidad de la documentación y ejemplos. Una librería mal documentada genera deuda técnica. |
   | Tests | Cobertura de tests del proyecto. Un proyecto sin tests es un riesgo. |

3. **Buscar alternativas más ligeras.** Antes de adoptar una dependencia pesada, verificar si existe una alternativa más pequeña que cubra el caso de uso específico. Por ejemplo: `date-fns` en vez de `moment`, `got` en vez de `axios` si solo se necesita HTTP básico.

4. **Evaluar la opción de implementación interna.** Si la funcionalidad necesaria es pequeña (menos de 50 líneas de código), puede merecer la pena implementarla internamente en vez de añadir una dependencia. Sopesar el coste de mantenimiento propio frente al riesgo de dependencia externa.

5. **Emitir la recomendación.** Una de tres opciones:

   - **Añadir:** la dependencia pasa todos los criterios y aporta valor significativo.
   - **Rechazar:** no pasa criterios críticos (vulnerabilidades, licencia, abandono).
   - **Implementar internamente:** la funcionalidad es suficientemente simple como para no justificar una dependencia.

6. **Documentar la decisión.** Dejar constancia del análisis para que futuras evaluaciones no repitan el trabajo.

## Qué NO hacer

- **No añadir dependencias para funcionalidad trivial** que se resuelve en 20 líneas de código. El coste de gestionar una dependencia (actualizaciones, vulnerabilidades, compatibilidad) supera al beneficio cuando la funcionalidad es simple.
- **No evaluar solo por popularidad.** Las estrellas de GitHub no son garantía de calidad, seguridad ni mantenimiento a largo plazo. Un proyecto con 50.000 estrellas y un solo mantenedor inactivo es más arriesgado que uno con 500 estrellas y un equipo activo.
- **No ignorar las dependencias transitivas.** Instalar una librería con 200 subdependencias amplía enormemente la superficie de ataque y el riesgo de rotura.

## Relación con otros skills

Este skill evalúa una dependencia concreta antes de añadirla. Para auditar las dependencias existentes del proyecto, usar `dependency-audit`.

## Criterios de éxito

- Se han verificado todos los criterios técnicos de la tabla.
- Se han buscado al menos 2 alternativas (incluida la implementación interna).
- La licencia es compatible con el proyecto.
- No hay vulnerabilidades críticas conocidas sin parche.
- La recomendación está justificada con datos, no con opiniones.
