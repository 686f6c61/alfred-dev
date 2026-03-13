---
name: bundle-size
description: "Analizar y reducir el tamaño de bundles frontend. Activar cuando el bundle sea grande, se quiera reducir tamaño, aplicar tree shaking, configurar lazy loading, usar webpack analyzer o analizar el peso de la aplicacion."
---

# Análisis y reducción de bundle size

## Resumen

Este skill guía el proceso de analizar y reducir el tamaño de los bundles de una aplicación frontend. Cada kilobyte adicional en el bundle se traduce en mayor tiempo de descarga, más consumo de datos del usuario y mayor tiempo hasta la interactividad. En conexiones lentas o dispositivos modestos, un bundle sobredimensionado puede hacer que la aplicación sea inutilizable.

El proceso parte del análisis visual del bundle actual, identifica las causas del tamaño excesivo y propone soluciones concretas que se validan midiendo antes y después.

## Proceso

1. **Medir el tamaño actual del bundle.** Antes de optimizar, registrar el estado de partida como baseline:

   - Tamaño total del bundle (sin comprimir y con gzip/brotli).
   - Tamaño de cada chunk o archivo generado por el bundler.
   - Tamaño del JavaScript, CSS e imágenes por separado.
   - Tiempo de carga en Lighthouse con throttling de red simulando 3G.

2. **Generar el mapa visual del bundle.** Usar la herramienta correspondiente al bundler del proyecto:

   - **Webpack:** `webpack-bundle-analyzer` genera un treemap interactivo del contenido del bundle.
   - **Vite/Rollup:** `rollup-plugin-visualizer` con formato treemap o sunburst.
   - **Independiente del bundler:** `source-map-explorer` analiza los source maps para mostrar qué ocupa espacio.

   Estas visualizaciones revelan de un vistazo qué dependencias y módulos dominan el tamaño.

3. **Identificar los problemas habituales.** Buscar estos patrones en el mapa visual:

   - **Dependencias duplicadas:** la misma librería aparece varias veces con versiones diferentes (por ejemplo, dos versiones de `lodash` por subdependencias incompatibles).
   - **Imports completos de librerías grandes:** se importa toda la librería cuando solo se usa una función (`import _ from 'lodash'` en lugar de `import groupBy from 'lodash/groupBy'`).
   - **Código muerto:** módulos importados pero nunca referenciados en la ejecución real.
   - **Polyfills innecesarios:** polyfills para navegadores que ya no se soportan.
   - **Assets no optimizados:** imágenes o fuentes incluidas en el bundle en lugar de cargarse como recursos estáticos.
   - **Librerías pesadas con alternativas ligeras:** `moment.js` (300KB+) cuando `date-fns` o `dayjs` cubren el mismo caso de uso.

4. **Aplicar las soluciones.** Para cada problema identificado, actuar con la técnica adecuada:

   - **Tree-shaking:** asegurar que las dependencias usan módulos ES (ESM). Verificar que el bundler no desactiva tree-shaking por configuración incorrecta de `sideEffects` en `package.json`.
   - **Code splitting:** dividir el bundle en chunks que se cargan bajo demanda. Rutas diferentes = chunks diferentes. Componentes pesados que no son visibles inicialmente = lazy loading con `React.lazy()`, `defineAsyncComponent()` o `import()` dinámico.
   - **Lazy loading:** cargar componentes, rutas y módulos solo cuando el usuario los necesita. Implementar `Suspense` o equivalente para gestionar el estado de carga.
   - **Alternativas ligeras:** sustituir dependencias pesadas por alternativas que cubran el caso de uso real:

     | Librería pesada | Alternativa ligera | Reducción aproximada |
     |-----------------|-------------------|---------------------|
     | moment.js | dayjs, date-fns | ~95% |
     | lodash (completo) | lodash-es (cherry-pick) | ~80% |
     | axios | fetch nativo + wrapper | ~100% (elimina dep) |
     | numeral.js | Intl.NumberFormat | ~100% (nativo) |

   - **Externalizar dependencias grandes:** si una librería se usa en todas las páginas (React, Vue), servirla desde CDN o como chunk separado con caché larga.
   - **Comprimir assets:** configurar gzip o brotli en el servidor. Brotli ofrece entre un 15-25% mejor ratio que gzip.

5. **Medir el resultado y comparar.** Repetir las mediciones del paso 1 tras aplicar los cambios:

   - Comparar tamaño total, tamaño por chunk y tiempo de carga.
   - Verificar que la funcionalidad no se ha visto afectada.
   - Generar nuevo mapa visual para confirmar que los problemas se han resuelto.
   - Documentar los cambios realizados y la reducción conseguida.

6. **Establecer presupuesto de bundle.** Para evitar que el tamaño vuelva a crecer sin control:

   - Definir un límite máximo para el bundle principal (por ejemplo, 200KB gzip).
   - Configurar alertas en CI con `bundlesize`, `size-limit` o la funcionalidad de presupuesto del bundler.
   - Revisar el impacto en tamaño antes de añadir nuevas dependencias.

## Que NO hacer

- No optimizar sin medir primero. Una reducción de 2KB en un bundle de 3MB no merece esfuerzo; una de 200KB en un bundle de 400KB es transformadora.
- No sacrificar la experiencia de desarrollo por una optimización marginal. Si una dependencia mejora significativamente la productividad del equipo, su tamaño puede ser aceptable.
- No asumir que el tree-shaking funciona sin verificarlo. Librerías que usan CommonJS, asignaciones a `module.exports` dinámicas o efectos secundarios en la raíz del módulo pueden anular el tree-shaking.
- No cargar todo de forma lazy. El chunk inicial debe contener lo necesario para el primer renderizado; el lazy loading excesivo genera cascadas de peticiones que empeoran la experiencia.
