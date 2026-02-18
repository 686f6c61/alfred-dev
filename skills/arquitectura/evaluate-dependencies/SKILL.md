---
name: evaluate-dependencies
description: "Usar para evaluar si una dependencia merece la pena antes de anadirla"
---

# Evaluar dependencias

## Resumen

Este skill analiza una dependencia externa antes de anadirla al proyecto. Cada dependencia es codigo de terceros que se incorpora a la cadena de suministro del software, con sus implicaciones de seguridad, mantenimiento y tamano. La pregunta no es solo "resuelve mi problema" sino "el coste de adoptarla es menor que el coste de implementarla internamente".

El resultado es una recomendacion fundamentada: anadir la dependencia, rechazarla o implementar la funcionalidad internamente.

## Proceso

1. **Identificar la necesidad concreta.** Que problema resuelve la dependencia. Cuanto codigo propio ahorra. Si es una utilidad puntual o una pieza central de la arquitectura.

2. **Evaluar los criterios tecnicos:**

   | Criterio | Que verificar |
   |----------|--------------|
   | Tamano del bundle | Peso en KB/MB. Impacto en tiempos de carga si es frontend. Usar herramientas como `bundlephobia` para npm. |
   | Tree-shaking | Se puede importar solo lo necesario o es todo-o-nada. |
   | Mantenimiento activo | Fecha del ultimo commit, frecuencia de releases, numero de mantenedores. Un solo mantenedor es un riesgo. |
   | Issues y PRs | Ratio de issues abiertas vs cerradas. PRs pendientes sin revisar durante meses. |
   | Vulnerabilidades | Historial de CVEs. Comprobar en bases de datos de vulnerabilidades (Snyk, GitHub Advisory). |
   | Licencia | Compatible con la licencia del proyecto. MIT y Apache 2.0 suelen ser seguras. GPL puede ser problematica en proyectos propietarios. |
   | Dependencias transitivas | Cuantas dependencias arrastra consigo. Cada una es un vector de riesgo adicional. |
   | Documentacion | Calidad de la documentacion y ejemplos. Una libreria mal documentada genera deuda tecnica. |
   | Tests | Cobertura de tests del proyecto. Un proyecto sin tests es un riesgo. |

3. **Buscar alternativas mas ligeras.** Antes de adoptar una dependencia pesada, verificar si existe una alternativa mas pequena que cubra el caso de uso especifico. Por ejemplo: `date-fns` en vez de `moment`, `got` en vez de `axios` si solo se necesita HTTP basico.

4. **Evaluar la opcion de implementacion interna.** Si la funcionalidad necesaria es pequena (menos de 50 lineas de codigo), puede merecer la pena implementarla internamente en vez de anadir una dependencia. Sopesar el coste de mantenimiento propio frente al riesgo de dependencia externa.

5. **Emitir la recomendacion.** Una de tres opciones:

   - **Anadir:** la dependencia pasa todos los criterios y aporta valor significativo.
   - **Rechazar:** no pasa criterios criticos (vulnerabilidades, licencia, abandono).
   - **Implementar internamente:** la funcionalidad es suficientemente simple como para no justificar una dependencia.

6. **Documentar la decision.** Dejar constancia del analisis para que futuras evaluaciones no repitan el trabajo.

## Criterios de exito

- Se han verificado todos los criterios tecnicos de la tabla.
- Se han buscado al menos 2 alternativas (incluida la implementacion interna).
- La licencia es compatible con el proyecto.
- No hay vulnerabilidades criticas conocidas sin parche.
- La recomendacion esta justificada con datos, no con opiniones.
