---
name: lighthouse-audit
description: "Analizar resultados de Lighthouse y proponer mejoras priorizadas. Activar ante: rendimiento web, Core Web Vitals, LCP, CLS, FID, puntuacion Lighthouse, velocidad de carga"
---

# Analizar resultados de Lighthouse

## Resumen

Este skill interpreta los resultados de una auditoria de Lighthouse y genera un plan de mejoras priorizado por impacto. Lighthouse evalua cuatro categorias principales (Performance, Accessibility, Best Practices, SEO) y cada una tiene metricas concretas con umbrales definidos. No se trata de llegar al 100 en todo, sino de identificar los puntos donde una mejora tiene el mayor retorno.

Las metricas de Core Web Vitals merecen atencion especial porque Google las usa directamente como factor de posicionamiento en los resultados de busqueda.

## Proceso

1. **Obtener el informe de Lighthouse.** Si el usuario no proporciona el informe, preguntar si quiere que Alfred lo ejecute directamente. Si acepta, ejecutar `npx lighthouse URL --output json --output-path ./lighthouse-report.json` (npx no requiere instalación global). Si la URL no está disponible o el usuario prefiere hacerlo manualmente, indicar las alternativas: Chrome DevTools (pestaña Lighthouse) o PageSpeed Insights (pagespeed.web.dev). El formato JSON es preferible porque permite análisis programático.

2. **Analizar la categoria Performance.** Es la mas compleja y la que mas impacto tiene en la experiencia del usuario. Centrarse en los Core Web Vitals:

   - **LCP (Largest Contentful Paint)**: mide cuando se renderiza el elemento mas grande visible. Umbral bueno: < 2.5s. Causas comunes de LCP alto: imagenes sin optimizar, carga de fuentes bloqueante, servidor lento (TTFB alto), recursos render-blocking.
   - **INP (Interaction to Next Paint)**: mide la latencia de las interacciones del usuario. Umbral bueno: < 200ms. Causas comunes: JavaScript pesado en el hilo principal, event handlers lentos, layout thrashing.
   - **CLS (Cumulative Layout Shift)**: mide los cambios inesperados de layout. Umbral bueno: < 0.1. Causas comunes: imagenes sin dimensiones explicitas, anuncios inyectados dinamicamente, fuentes web que causan FOIT/FOUT.

   Para cada metrica fuera de umbral, identificar la causa raiz usando las oportunidades y diagnosticos que Lighthouse proporciona.

3. **Analizar la categoria Accessibility.** Cada problema de accesibilidad tiene un impacto real en usuarios con discapacidades. Revisar:

   - Contraste de color insuficiente.
   - Imagenes sin atributo `alt`.
   - Formularios sin labels asociados.
   - Estructura de encabezados incorrecta (saltos de nivel).
   - Elementos interactivos sin nombre accesible.
   - Falta de atributos ARIA donde son necesarios.

4. **Analizar Best Practices.** Verificar:

   - HTTPS en todos los recursos.
   - Ausencia de APIs obsoletas o inseguras.
   - Consola sin errores de JavaScript.
   - Imagenes con resolucion adecuada para la densidad de pantalla.

5. **Analizar la categoria SEO.** Verificar:

   - Meta tags presentes y correctas (delegar en el skill `meta-tags` para un analisis profundo).
   - Documento rastreable (no bloqueado por robots.txt).
   - Enlaces con texto descriptivo.
   - Pagina adaptada a moviles.

6. **Priorizar las mejoras.** Ordenar los hallazgos por impacto estimado. Criterios de priorizacion:

   - Core Web Vitals fuera de umbral: prioridad maxima, afectan al posicionamiento.
   - Problemas de accesibilidad criticos: prioridad alta, afectan a usuarios reales.
   - Best Practices: prioridad media, indican deuda tecnica.
   - Mejoras de SEO menores: prioridad normal.

7. **Generar el plan de accion.** Para cada hallazgo, documentar: la metrica afectada, el valor actual frente al umbral deseado, la causa raiz identificada y la solucion concreta propuesta.

## Que NO hacer

- No obsesionarse con la puntuacion numerica: una pagina con 85 en Performance puede ser perfectamente aceptable si los Core Web Vitals estan en verde.
- No aplicar optimizaciones a ciegas sin medir el impacto real.
- No ignorar los problemas de accesibilidad por considerarlos de menor prioridad que el rendimiento.
