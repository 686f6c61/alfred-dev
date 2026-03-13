---
name: choose-stack
description: "Usar para evaluar y elegir tecnologías con matriz de decisión ponderada. Activar cuando el usuario quiera elegir tecnología, comparar frameworks, decidir entre alternativas técnicas, construir una matriz de decisión, evaluar stack, seleccionar base de datos, elegir lenguaje o comparar herramientas."
---

# Elegir stack tecnológico

## Resumen

Este skill evalúa alternativas tecnológicas de forma estructurada mediante una matriz de decisión ponderada. El objetivo es eliminar el sesgo de "lo que ya conozco" o "lo que está de moda" y sustituirlo por una evaluación objetiva basada en criterios relevantes para el proyecto concreto.

La elección de stack es una de las decisiones más costosas de revertir, por lo que merece un análisis riguroso. Este skill produce un documento que justifica la decisión y sirve como referencia futura para el equipo.

## Proceso

1. **Consultar el stack actual del proyecto.** Consultar el stack detectado en la configuración de Alfred (`detect_stack`) como punto de partida. Si no está disponible, detectar manualmente revisando los ficheros de configuración del proyecto (package.json, Cargo.toml, pyproject.toml, etc.). Partir del contexto existente evita proponer tecnologías incompatibles con lo que ya hay.

2. **Recopilar requisitos del proyecto.** Antes de evaluar tecnologías, entender qué se necesita: tipo de aplicación, escala esperada, equipo disponible, restricciones de tiempo, presupuesto y requisitos regulatorios.

2. **Definir los criterios de evaluación y sus pesos.** Los criterios dependen del contexto, pero considerar siempre:

   | Criterio | Peso sugerido | Descripción |
   |----------|--------------|-------------|
   | Rendimiento | Variable | Latencia, throughput, uso de memoria según las necesidades del proyecto. |
   | Ecosistema | Alto | Librerías, frameworks, herramientas disponibles. |
   | Curva de aprendizaje | Variable | Tiempo que necesita el equipo para ser productivo. |
   | Mantenimiento | Alto | Facilidad de actualizar, depurar y evolucionar. |
   | Seguridad | Alto | Historial de vulnerabilidades, prácticas del ecosistema. |
   | Comunidad | Medio | Tamaño, actividad, calidad de documentación. |
   | Coste operativo | Variable | Infraestructura, licencias, herramientas de pago. |
   | Madurez | Medio | Estabilidad de la API, versionado, backwards compatibility. |

   El usuario asigna los pesos finales. Si no lo hace, usar los sugeridos justificando la elección.

3. **Identificar al menos 3 alternativas.** Para cada capa del stack (lenguaje, framework, base de datos, etc.), proponer un mínimo de 3 opciones viables. Incluir siempre al menos una opción "conservadora" (probada y estable) y una "emergente" (más moderna pero con menos recorrido).

4. **Evaluar cada alternativa contra los criterios.** Puntuar de 1 a 5 cada criterio para cada alternativa. Multiplicar por el peso. Documentar la justificación de cada puntuación, no solo el número.

5. **Calcular la puntuación total ponderada.** Sumar los valores ponderados y ordenar las alternativas de mayor a menor.

6. **Analizar los resultados cualitativamente.** La puntuación más alta no siempre es la mejor opción. Considerar factores difíciles de cuantificar: experiencia del equipo, alineación con el ecosistema existente, riesgos de vendor lock-in.

7. **Emitir una recomendación con justificación.** Indicar la opción recomendada, por qué se elige y qué riesgos se asumen. Si la decisión es ajustada, indicarlo explícitamente.

8. **Documentar como ADR.** Si la decisión es significativa, generar un ADR (Architecture Decision Record) con el skill `write-adr` para que quede constancia en el repositorio.

9. **Registrar la elección en la memoria del proyecto** con `memory_log_decision`. Esto permite que futuros skills consulten qué tecnologías se han elegido y por qué, sin necesidad de buscar el documento original.

## Qué NO hacer

- **No recomendar sin datos.** Las preferencias personales no son criterios de evaluación. Toda puntuación debe estar justificada con evidencia verificable.
- **No ignorar el contexto del equipo.** La mejor tecnología del mundo es inútil si el equipo no puede ser productivo con ella en el plazo disponible.
- **No evaluar solo por popularidad.** Las estrellas de GitHub y las tendencias de Twitter no son indicadores fiables de idoneidad para un proyecto concreto.
- **No limitar la comparación a dos opciones.** Siempre evaluar al menos 3 alternativas para evitar el sesgo de confirmación de una decisión ya tomada.
- **No olvidar el coste a largo plazo.** Una tecnología puede ser fácil de adoptar pero cara de mantener. Evaluar todo el ciclo de vida.

## Criterios de éxito

- Se han evaluado al menos 3 alternativas por componente del stack.
- La matriz incluye criterios con pesos justificados.
- Cada puntuación tiene una explicación, no solo un número.
- La recomendación final está argumentada con datos.
- Se han identificado los riesgos de la opción elegida.
