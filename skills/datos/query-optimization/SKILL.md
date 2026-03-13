---
name: query-optimization
description: "Optimizar queries lentas con EXPLAIN, índices y reescritura. Activar cuando el usuario tenga una query lenta, quiera optimizar SQL, usar EXPLAIN, crear indices, resolver problemas N+1 o mejorar el rendimiento de consultas."
---

# Optimización de queries

## Resumen

Este skill guía el proceso de identificar y optimizar queries lentas en bases de datos relacionales. La optimización de queries no consiste en añadir índices a ciegas, sino en entender cómo el motor de base de datos ejecuta una consulta y actuar sobre los cuellos de botella concretos.

El proceso parte de una query lenta identificada (por logs, APM o reporte del usuario), aplica herramientas de análisis como EXPLAIN y propone soluciones que se validan con benchmarks antes y después.

## Proceso

1. **Identificar la query lenta.** Localizar la consulta problemática a partir de fuentes concretas:

   - Slow query log del motor de base de datos (MySQL: `slow_query_log`, PostgreSQL: `log_min_duration_statement`).
   - Herramientas de APM (Datadog, New Relic, Sentry Performance).
   - Reporte del usuario o del equipo de desarrollo.
   - Registrar el tiempo actual de ejecución como baseline para comparar después.

2. **Ejecutar EXPLAIN o EXPLAIN ANALYZE.** Obtener el plan de ejecución de la query:

   - **PostgreSQL:** `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` para ver tiempos reales y acceso a disco.
   - **MySQL:** `EXPLAIN FORMAT=JSON` o `EXPLAIN ANALYZE` (MySQL 8.0+) para detalle adicional.
   - Leer el plan de ejecución de dentro hacia fuera (las operaciones más internas se ejecutan primero).

3. **Identificar los cuellos de botella.** Buscar estos patrones en el plan de ejecución:

   - **Seq Scan / Full Table Scan:** la base de datos recorre toda la tabla porque no hay índice útil.
   - **Nested Loop sin índice:** joins que recorren la tabla interna completa por cada fila de la externa.
   - **Sort sin índice:** ordenaciones que se hacen en memoria o disco en lugar de aprovechar un índice.
   - **Subconsultas correlacionadas:** subconsultas que se ejecutan una vez por cada fila de la consulta externa.
   - **Estimaciones incorrectas:** filas estimadas muy diferentes de las reales, lo que indica estadísticas desactualizadas.

4. **Proponer soluciones según el cuello de botella.** Cada problema tiene soluciones específicas:

   - **Full scan:** crear índice en las columnas del WHERE, o índice compuesto si filtra por varias.
   - **Join sin índice:** asegurar que la columna de join tiene índice en la tabla interna.
   - **Subconsulta correlacionada:** reescribir como JOIN o usar CTE (Common Table Expression).
   - **Ordenación costosa:** crear índice que cubra tanto el filtro como el orden.
   - **Selección de demasiadas columnas:** usar SELECT explícito en lugar de SELECT * y considerar covering indexes.
   - **Estadísticas obsoletas:** ejecutar ANALYZE (PostgreSQL) o ANALYZE TABLE (MySQL).

5. **Evaluar reescrituras de la query.** A veces el problema no es el índice sino la estructura de la query:

   - Sustituir IN con subconsulta por EXISTS o JOIN.
   - Evitar funciones sobre columnas indexadas en el WHERE (rompe el uso del índice).
   - Usar paginación con cursor en lugar de OFFSET para conjuntos grandes.
   - Considerar vistas materializadas para agregaciones costosas que se consultan frecuentemente.

6. **Hacer benchmark antes y después.** Medir el impacto real del cambio:

   - Ejecutar la query original y la optimizada en las mismas condiciones.
   - Comparar tiempo de ejecución, filas examinadas y buffers/páginas leídas.
   - Verificar que la query optimizada devuelve exactamente los mismos resultados.
   - Ejecutar varias iteraciones para descartar variabilidad por caché.

7. **Documentar el cambio.** Registrar la optimización con: query original, plan de ejecución antes, cambio aplicado, plan de ejecución después y métricas de mejora. Este registro es valioso para detectar regresiones futuras.

## Que NO hacer

- No añadir índices sin verificar con EXPLAIN que el motor los utiliza.
- No optimizar queries que se ejecutan pocas veces al día y tardan milisegundos; centrar el esfuerzo en las que generan carga real.
- No sacrificar la legibilidad de la query por una mejora marginal de rendimiento.
- No olvidar que cada índice añadido ralentiza las operaciones de escritura (INSERT, UPDATE, DELETE).
- No confiar en el tiempo de ejecución de una sola iteración como benchmark fiable.
