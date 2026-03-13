---
name: user-guide
description: "Usar para escribir guías de usuario o desarrollador. Activar ante: guia de usuario, como usar, manual de uso, tutorial, instrucciones para el usuario"
---

# Escribir guía de usuario

## Resumen

Este skill genera guías de usuario o de desarrollador claras y completas. Una buena guía permite al lector ir de "no sé nada de esto" a "lo tengo funcionando y entiendo cómo usarlo" sin necesidad de ayuda externa. El tono es directo, los pasos son verificables y los ejemplos son funcionales.

La guía se adapta al público: si es para usuarios finales, se evita jerga técnica; si es para desarrolladores, se incluyen detalles de configuración e integración.

## Proceso

1. **Identificar al público objetivo.** La guía se escribe de forma distinta según quién la va a leer:

   - **Usuario final:** pasos simples, capturas de pantalla si aplica, lenguaje no técnico.
   - **Desarrollador que integra:** ejemplos de código, documentación de API, configuración.
   - **Desarrollador que contribuye:** setup del entorno, convenios del proyecto, cómo ejecutar tests.

2. **Redactar la sección de instalación.** Paso a paso, sin saltar nada:

   - Requisitos previos (versiones de software, sistema operativo, herramientas necesarias).
   - Comandos de instalación exactos, copiables y pegables.
   - Verificación de que la instalación ha funcionado (comando o página de prueba).
   - Errores comunes de instalación y cómo resolverlos.

3. **Redactar la sección de configuración:**

   - Variables de entorno necesarias, con descripción y ejemplo de valor.
   - Ficheros de configuración, con plantilla y explicación de cada campo.
   - Valores por defecto y cuándo cambiarlos.

4. **Redactar la sección de uso básico.** El caso de uso más simple para que el lector vea resultados rápido:

   - Ejemplo mínimo funcional (de principio a fin).
   - Explicación de qué hace cada paso.
   - Resultado esperado para que el lector pueda verificar.

5. **Redactar la sección de uso avanzado.** Funcionalidades menos obvias pero importantes:

   - Configuraciones avanzadas.
   - Integraciones con otras herramientas.
   - Personalización y extensión.
   - Patrones de uso recomendados.

6. **Redactar la sección de troubleshooting.** Los problemas más comunes y sus soluciones:

   | Problema | Causa probable | Solución |
   |----------|---------------|----------|
   | Error X al arrancar | Falta variable de entorno Y | Añadir Y al fichero .env |
   | La página no carga | Puerto ocupado | Cambiar el puerto en config |

   Esta sección se alimenta de las preguntas reales de los usuarios. Si no hay histórico, anticipar los problemas más probables.

7. **Redactar FAQ.** Preguntas frecuentes que no encajan en las secciones anteriores. Formato pregunta-respuesta, directo y conciso.

8. **Revisar con un lector fresco.** Si es posible, pedir a alguien que no conoce el proyecto que siga la guía y reporte dónde se atasca.

## Criterios de éxito

- La guía cubre instalación, configuración, uso básico, uso avanzado y troubleshooting.
- Los pasos de instalación son reproducibles (se pueden seguir de cero a funcionando).
- Los ejemplos son funcionales y se pueden copiar directamente.
- El lenguaje está adaptado al público objetivo.
- Los problemas comunes tienen soluciones documentadas.
