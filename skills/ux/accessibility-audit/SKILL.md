---
name: accessibility-audit
description: "Auditar accesibilidad WCAG 2.1 nivel AA con checklist y correcciones. Activar ante: accesibilidad web, WCAG, lector de pantalla, contraste, navegacion por teclado, a11y"
---

# Auditoría de accesibilidad WCAG 2.1 AA

## Resumen

Este skill ejecuta una auditoría de accesibilidad basada en las pautas WCAG 2.1 nivel AA. La accesibilidad no es un complemento opcional sino un requisito que garantiza que todas las personas, independientemente de sus capacidades, puedan usar el producto. Además, en muchas jurisdicciones es una obligación legal.

La auditoría se organiza en torno a los cuatro principios WCAG (Perceptible, Operable, Comprensible, Robusto) y produce un informe con los criterios evaluados, los problemas encontrados y las correcciones propuestas con ejemplos de código.

> **Nota de versión:** basado en WCAG 2.1 nivel AA (2018). WCAG 2.2 (octubre 2023) añade criterios adicionales. Verificar si el proyecto requiere conformidad con la versión más reciente.

## Proceso

1. **Verificar el principio Perceptible.** El contenido debe ser presentado de formas que todos los usuarios puedan percibir:

   - **Alternativas textuales:** todas las imágenes tienen `alt` descriptivo. Las imágenes decorativas usan `alt=""` o `role="presentation"`. Los iconos informativos tienen `aria-label`.
   - **Contenido multimedia:** los vídeos tienen subtítulos y los audios tienen transcripción.
   - **Adaptabilidad:** la estructura semántica es correcta (headings ordenados, landmarks, listas). La información no depende solo del color o la forma.
   - **Distinguible:** el contraste de color cumple el ratio mínimo 4.5:1 para texto normal y 3:1 para texto grande. El texto se puede redimensionar al 200% sin pérdida de contenido.

2. **Verificar el principio Operable.** La interfaz debe ser navegable y utilizable con diferentes dispositivos de entrada:

   - **Teclado:** todos los elementos interactivos son accesibles con teclado (Tab, Enter, Escape, flechas). No hay trampas de foco. El orden de tabulación es lógico.
   - **Tiempo suficiente:** si hay temporizadores, el usuario puede pausarlos, extenderlos o desactivarlos.
   - **Navegación:** hay mecanismos para saltar bloques de contenido repetido (skip links). Los títulos de página son descriptivos. Los enlaces tienen texto significativo (no "pincha aquí").
   - **Modalidades de entrada:** los gestos complejos (deslizar, pellizcar) tienen alternativas de un solo punto. Las funciones activadas por movimiento tienen alternativas convencionales.

3. **Verificar el principio Comprensible.** El contenido y la interfaz deben ser entendibles:

   - **Legibilidad:** el atributo `lang` está presente en el HTML y es correcto. El lenguaje es claro y los términos técnicos se explican.
   - **Predecibilidad:** la navegación es consistente en todas las páginas. Los cambios de contexto no ocurren sin aviso al usuario.
   - **Asistencia de entrada:** los campos de formulario tienen `label` asociado. Los errores se identifican claramente y se ofrecen sugerencias de corrección. Los mensajes de error están vinculados al campo correspondiente con `aria-describedby`.

4. **Verificar el principio Robusto.** El contenido debe ser interpretable por tecnologías de asistencia:

   - **Parsing:** el HTML es válido, sin IDs duplicados ni atributos ARIA incorrectos.
   - **Compatibilidad:** los componentes personalizados tienen roles, estados y propiedades ARIA correctos. Los cambios dinámicos se anuncian con `aria-live`. Los widgets complejos siguen los patrones WAI-ARIA Authoring Practices.

5. **Ejecutar herramientas automatizadas.** Complementar la revisión manual con herramientas:

   - axe-core o axe DevTools para detección automática.
   - Lighthouse (sección Accessibility) para puntuación general.
   - WAVE para visualización de problemas.
   - Navegación real con lector de pantalla (VoiceOver, NVDA) para validar la experiencia.

6. **Documentar hallazgos.** Cada problema detectado debe incluir:

   - Criterio WCAG violado (por ejemplo: 1.1.1 Non-text Content).
   - Ubicación en el código (componente, línea).
   - Descripción del problema y su impacto en el usuario.
   - Ejemplo de código incorrecto y código corregido.
   - Severidad: crítico (bloquea el acceso), grave (dificulta significativamente), moderado (inconveniente) o leve (mejora deseable).

## Que NO hacer

- No considerar que la accesibilidad se resuelve solo con herramientas automatizadas. Estas detectan como máximo el 30-40% de los problemas.
- No usar ARIA para compensar HTML mal estructurado. La primera regla de ARIA es "no uses ARIA si puedes usar HTML nativo".
- No esconder contenido con `display: none` o `visibility: hidden` pensando que los lectores de pantalla lo ignorarán selectivamente; lo ignoran completamente.
- No testar únicamente con ratón. Si el sitio no se puede usar solo con teclado, no es accesible.
