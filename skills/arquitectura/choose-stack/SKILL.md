---
name: choose-stack
description: "Usar para evaluar y elegir tecnologias con matriz de decision ponderada"
---

# Elegir stack tecnologico

## Resumen

Este skill evalua alternativas tecnologicas de forma estructurada mediante una matriz de decision ponderada. El objetivo es eliminar el sesgo de "lo que ya conozco" o "lo que esta de moda" y sustituirlo por una evaluacion objetiva basada en criterios relevantes para el proyecto concreto.

La eleccion de stack es una de las decisiones mas costosas de revertir, por lo que merece un analisis riguroso. Este skill produce un documento que justifica la decision y sirve como referencia futura para el equipo.

## Proceso

1. **Recopilar requisitos del proyecto.** Antes de evaluar tecnologias, entender que se necesita: tipo de aplicacion, escala esperada, equipo disponible, restricciones de tiempo, presupuesto y requisitos regulatorios.

2. **Definir los criterios de evaluacion y sus pesos.** Los criterios dependen del contexto, pero considerar siempre:

   | Criterio | Peso sugerido | Descripcion |
   |----------|--------------|-------------|
   | Rendimiento | Variable | Latencia, throughput, uso de memoria segun las necesidades del proyecto. |
   | Ecosistema | Alto | Librerias, frameworks, herramientas disponibles. |
   | Curva de aprendizaje | Variable | Tiempo que necesita el equipo para ser productivo. |
   | Mantenimiento | Alto | Facilidad de actualizar, depurar y evolucionar. |
   | Seguridad | Alto | Historial de vulnerabilidades, practicas del ecosistema. |
   | Comunidad | Medio | Tamano, actividad, calidad de documentacion. |
   | Coste operativo | Variable | Infraestructura, licencias, herramientas de pago. |
   | Madurez | Medio | Estabilidad de la API, versionado, backwards compatibility. |

   El usuario asigna los pesos finales. Si no lo hace, usar los sugeridos justificando la eleccion.

3. **Identificar al menos 3 alternativas.** Para cada capa del stack (lenguaje, framework, base de datos, etc.), proponer un minimo de 3 opciones viables. Incluir siempre al menos una opcion "conservadora" (probada y estable) y una "emergente" (mas moderna pero con menos recorrido).

4. **Evaluar cada alternativa contra los criterios.** Puntuar de 1 a 5 cada criterio para cada alternativa. Multiplicar por el peso. Documentar la justificacion de cada puntuacion, no solo el numero.

5. **Calcular la puntuacion total ponderada.** Sumar los valores ponderados y ordenar las alternativas de mayor a menor.

6. **Analizar los resultados cualitativamente.** La puntuacion mas alta no siempre es la mejor opcion. Considerar factores dificiles de cuantificar: experiencia del equipo, alineacion con el ecosistema existente, riesgos de vendor lock-in.

7. **Emitir una recomendacion con justificacion.** Indicar la opcion recomendada, por que se elige y que riesgos se asumen. Si la decision es ajustada, indicarlo explicitamente.

8. **Documentar como ADR.** Si la decision es significativa, generar un ADR (Architecture Decision Record) con el skill `write-adr` para que quede constancia en el repositorio.

## Criterios de exito

- Se han evaluado al menos 3 alternativas por componente del stack.
- La matriz incluye criterios con pesos justificados.
- Cada puntuacion tiene una explicacion, no solo un numero.
- La recomendacion final esta argumentada con datos.
- Se han identificado los riesgos de la opcion elegida.
