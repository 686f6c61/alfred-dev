---
name: benchmark
description: "Crear y ejecutar benchmarks para medir impacto de cambios. Activar cuando el usuario quiera medir rendimiento, comparar antes y despues, evaluar velocidad, throughput o ejecutar un benchmark de codigo."
---

# Benchmarks de rendimiento

## Resumen

Este skill establece un proceso para crear y ejecutar benchmarks fiables que midan el impacto real de los cambios en el rendimiento de una aplicación. Un benchmark mal diseñado es peor que no tener benchmark, porque puede llevar a conclusiones erróneas y optimizaciones contraproducentes.

El resultado es un informe cuantitativo con métricas estadísticas (media, percentiles) que permite tomar decisiones informadas sobre si un cambio mejora, empeora o no afecta al rendimiento.

## Proceso

1. **Consultar el stack del proyecto.** Consultar el stack detectado en la configuración de Alfred para seleccionar la herramienta de benchmarking adecuada al runtime y al tipo de aplicación.

2. **Definir qué se mide y por qué.** Antes de escribir código de benchmark, establecer con claridad:

   - Qué operación se está midiendo (renderizado de un componente, respuesta de un endpoint, procesado de un fichero).
   - Qué métrica importa: latencia, throughput, uso de memoria, tamaño de bundle.
   - Cuál es el criterio de éxito (mejora del 20%, no empeorar más de un 5%, mantenerse por debajo de 100ms en p95).

3. **Preparar condiciones controladas.** Un benchmark solo es fiable si las condiciones son reproducibles:

   - Ejecutar en un entorno consistente (misma máquina, misma carga, mismos datos).
   - Cerrar procesos que puedan interferir (otras aplicaciones, servicios en background).
   - Usar datos de prueba representativos del volumen real.
   - Fijar las versiones de todas las dependencias para evitar variabilidad por actualizaciones.

4. **Implementar el benchmark con la herramienta adecuada.** Seleccionar según el runtime:

   - **Node.js:** `vitest bench`, `tinybench` o `benchmark.js` para microbenchmarks. `autocannon` o `k6` para benchmarks HTTP.
   - **Python:** `pytest-benchmark` para microbenchmarks. `locust` o `k6` para carga HTTP.
   - **Frontend:** `lighthouse ci` para métricas web. Web Vitals API para métricas reales en navegador. `react-render-tracker` o React Profiler API para componentes.
   - **General:** `hyperfine` para benchmarks de línea de comandos.

5. **Ejecutar con warmup e iteraciones suficientes.** Los JIT compilers y las cachés hacen que las primeras ejecuciones sean atípicas:

   - Incluir fase de warmup (al menos 5-10 iteraciones) que no se contabilice.
   - Ejecutar un mínimo de 100 iteraciones para operaciones rápidas, 30 para operaciones lentas.
   - Si la herramienta lo permite, ejecutar hasta que la desviación estándar sea estable.

6. **Recopilar estadísticas, no solo la media.** La media oculta la distribución real del rendimiento:

   - **Media:** referencia general, pero sensible a outliers.
   - **Mediana (p50):** el caso típico. Más robusta que la media.
   - **p95:** el 95% de las ejecuciones son más rápidas que este valor. Representa la experiencia de la mayoría.
   - **p99:** detecta colas largas. Importante para sistemas con muchos usuarios.
   - **Min/Max:** útiles para detectar anomalías, pero no para comparar.
   - **Desviación estándar:** mide la variabilidad. Si es alta, los resultados no son fiables.

7. **Comparar antes y después con formato estandarizado.** Presentar los resultados en tabla:

   | Metrica | Antes | Después | Diferencia | Cambio |
   |---------|-------|---------|------------|--------|
   | Media | 120ms | 85ms | -35ms | -29.2% |
   | p50 | 115ms | 82ms | -33ms | -28.7% |
   | p95 | 180ms | 105ms | -75ms | -41.7% |
   | p99 | 250ms | 130ms | -120ms | -48.0% |

   Incluir el número de iteraciones y la desviación estándar para evaluar la confianza en los resultados.

8. **Interpretar y documentar.** No basta con números; contextualizar los resultados:

   - La mejora es estadísticamente significativa o está dentro del margen de error?
   - La mejora justifica la complejidad adicional del cambio?
   - Hay regresiones en algún percentil aunque la media mejore?
   - Guardar los resultados en el repositorio para seguimiento histórico.

## Que NO hacer

- No comparar benchmarks ejecutados en máquinas o condiciones diferentes.
- No usar una sola iteración como resultado. Un solo dato no es un benchmark, es una anécdota.
- No ignorar los percentiles altos (p95, p99). La media puede mejorar mientras la cola empeora.
- No optimizar para el benchmark en lugar de para el caso de uso real. El benchmark debe representar el uso real, no un escenario artificial.
- No omitir la fase de warmup. Las primeras ejecuciones son sistemáticamente más lentas por compilación JIT y llenado de cachés.
