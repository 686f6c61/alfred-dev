---
name: profiling
description: "Perfilar aplicaciones para encontrar cuellos de botella de CPU y memoria. Activar cuando la aplicacion este lenta, haya un cuello de botella, problemas de latencia, se necesite un flamegraph, se detecte alto uso de CPU, un memory leak o se quiera analizar el rendimiento."
---

# Profiling de aplicaciones

## Resumen

Este skill guía el proceso de perfilado de una aplicación para identificar cuellos de botella de rendimiento en CPU y memoria. El profiling es una disciplina empírica: se mide primero, se optimiza después. La intuición sobre dónde está el cuello de botella suele ser incorrecta, por lo que las herramientas de profiling son imprescindibles para tomar decisiones informadas.

El proceso se adapta al runtime de la aplicación (Node.js, Python, frontend) y produce un diagnóstico con los hot paths identificados, las funciones más costosas y las propuestas de corrección.

## Proceso

1. **Consultar el stack del proyecto.** Consultar el stack detectado en la configuración de Alfred para seleccionar las herramientas de profiling adecuadas al runtime (Node.js, Python, navegador, etc.).

2. **Reproducir el escenario lento.** Antes de perfilar, definir exactamente qué operación es lenta y cómo reproducirla de forma consistente:

   - Identificar el endpoint, la acción de usuario o el proceso que se quiere optimizar.
   - Preparar datos de prueba que representen el volumen real de producción.
   - Ejecutar la operación al menos una vez para descartar efectos de arranque en frío.

3. **Capturar el perfil con las herramientas del runtime.** Seleccionar la herramienta según el entorno:

   - **Node.js:** `--inspect` con Chrome DevTools para CPU profiling y heap snapshots. `clinic.js` para diagnóstico automatizado (doctor, flame, bubbleprof). `0x` para generar flamegraphs directamente.
   - **Python:** `cProfile` para perfilado integrado. `py-spy` para perfilado sin instrumentación (sampling profiler, no requiere modificar el código). `memory_profiler` para análisis de memoria línea por línea.
   - **Frontend (navegador):** Chrome DevTools Performance tab para grabar actividad de CPU, layout, paint y scripting. Memory tab para heap snapshots y detección de leaks. Lighthouse para métricas de rendimiento centradas en el usuario (LCP, FID, CLS).

4. **Identificar los hot paths.** Analizar el perfil capturado buscando las funciones y operaciones que consumen más tiempo:

   - En un flamegraph, las barras anchas en la parte superior son las funciones que más tiempo acumulan.
   - En un perfil tabulado, ordenar por "self time" (tiempo propio, no incluyendo llamadas hijas) para encontrar las funciones realmente costosas.
   - En perfiles de memoria, buscar objetos que crecen sin liberarse (memory leaks) o asignaciones excesivas que presionan al garbage collector.

5. **Analizar el call stack de los hot paths.** Una vez identificada la función costosa, entender por qué es costosa:

   - Se llama demasiadas veces (problema de arquitectura o algoritmo)?
   - Cada llamada individual es lenta (operación de I/O, algoritmo ineficiente)?
   - Genera demasiadas asignaciones de memoria (presión sobre el GC)?
   - Bloquea el event loop (en Node.js o navegador)?

6. **Proponer correcciones específicas.** Según el diagnóstico:

   - **CPU bound:** optimizar el algoritmo, usar cachés, mover a un worker thread.
   - **I/O bound:** paralelizar operaciones independientes, implementar batching, usar streaming en lugar de cargar todo en memoria.
   - **Memory leaks:** identificar referencias retenidas, cerrar conexiones y listeners, usar WeakRef donde proceda.
   - **GC pressure:** reducir asignaciones innecesarias, reutilizar objetos, evitar la creación de closures en bucles.
   - **Frontend:** reducir layout thrashing, usar requestAnimationFrame para animaciones, virtualizar listas largas.

7. **Verificar la mejora.** Repetir el profiling tras aplicar los cambios:

   - Comparar los flamegraphs antes y después.
   - Medir la mejora en tiempo de ejecución y uso de memoria.
   - Asegurar que la corrección no ha introducido regresiones funcionales.

## Que NO hacer

- No optimizar sin medir. La optimización prematura basada en intuición suele desperdiciar tiempo y complicar el código sin beneficio real.
- No perfilar en modo desarrollo si se buscan métricas representativas. El hot reloading, los source maps y las comprobaciones de desarrollo distorsionan los resultados.
- No ignorar el garbage collector. Muchos problemas de rendimiento en Node.js y navegador se deben a presión excesiva sobre el GC, no a CPU.
- No perfilar solo una vez. Los resultados pueden variar entre ejecuciones; capturar varias muestras para confirmar los hallazgos.
