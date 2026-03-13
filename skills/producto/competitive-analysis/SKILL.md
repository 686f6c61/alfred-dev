---
name: competitive-analysis
description: "Investigar cómo resuelven el mismo problema otras herramientas. Activar cuando el usuario quiera hacer un analisis competitivo, saber que hace la competencia, evaluar alternativas existentes o realizar benchmarking de mercado."
---

# Análisis competitivo

## Resumen

Este skill investiga y documenta cómo otras herramientas, productos o proyectos resuelven el mismo problema que el usuario quiere abordar. El resultado es una tabla comparativa objetiva que permite tomar decisiones informadas sobre qué construir, qué copiar deliberadamente y dónde diferenciarse.

No se trata de una lista superficial de competidores, sino de un análisis con criterios definidos que ayude a entender el panorama real del mercado o del ecosistema técnico.

## Proceso

1. **Definir el problema a resolver.** Antes de buscar competidores, acotar con precisión qué problema se está investigando. Un mismo producto puede competir en múltiples dimensiones; aquí interesa la dimensión concreta.

2. **Identificar competidores y alternativas.** Buscar al menos 3 y máximo 6 soluciones que aborden el mismo problema. Incluir:

   - Competidores directos (mismo problema, mismo público).
   - Competidores indirectos (mismo problema, diferente enfoque o público).
   - Alternativas de código abierto si existen.
   - La opción de "no hacer nada" o "hacerlo manualmente" como baseline.

3. **Definir criterios de comparación.** Adaptar según el contexto, pero considerar siempre:

   | Criterio | Descripción |
   |----------|-------------|
   | Funcionalidad | Qué resuelve y qué no. Features principales. |
   | Precio/modelo de negocio | Gratuito, freemium, pago, open source. |
   | Ecosistema/integraciones | Con qué se conecta, plugins, APIs. |
   | Comunidad y soporte | Tamaño de comunidad, documentación, actividad. |
   | Experiencia de uso | Facilidad de setup, curva de aprendizaje. |
   | Limitaciones conocidas | Qué no hace bien, quejas frecuentes de usuarios. |
   | Madurez/estabilidad | Tiempo en el mercado, frecuencia de actualizaciones. |

4. **Investigar cada competidor.** Usar fuentes fiables: documentación oficial, repositorios públicos, reviews de usuarios, changelogs. Evitar opiniones sin fundamentar.

5. **Generar la tabla comparativa.** Formato Markdown con una fila por competidor y una columna por criterio. Incluir puntuaciones o valoraciones cualitativas (bueno/regular/pobre) cuando proceda.

6. **Identificar oportunidades de diferenciación.** Basándose en las limitaciones de los competidores, señalar dónde el proyecto del usuario puede aportar valor único. Esto no es obligatorio si el usuario solo quiere entender el panorama.

7. **Registrar hallazgos en la memoria del proyecto.** Registrar los hallazgos del análisis competitivo en la memoria del proyecto con `memory_log_decision` para que estén disponibles en futuras sesiones de trabajo.

8. **Documentar conclusiones.** Resumir los hallazgos principales en 3-5 puntos clave que orienten la decisión.

## Criterios de éxito

- Se han analizado al menos 3 alternativas con criterios objetivos.
- La tabla comparativa cubre funcionalidad, precio, ecosistema, comunidad y limitaciones como mínimo.
- Las fuentes de información son verificables (documentación oficial, repositorios públicos).
- Las conclusiones son accionables: ayudan a tomar una decisión concreta.
- El análisis distingue entre hechos y opiniones.

## Que NO hacer

- No basar el análisis en opiniones sin fuente verificable. Cada afirmación sobre un competidor debe respaldarse con documentación oficial, repositorios públicos o datos contrastables.
- No limitar el análisis a competidores directos. Las alternativas indirectas y la opción de "no hacer nada" son comparaciones igualmente valiosas para tomar decisiones.
- No presentar el análisis como una recomendación cerrada. El objetivo es informar la decisión del usuario, no tomarla por él.
