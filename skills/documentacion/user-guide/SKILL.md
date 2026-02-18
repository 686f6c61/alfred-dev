---
name: user-guide
description: "Usar para escribir guias de usuario o desarrollador"
---

# Escribir guia de usuario

## Resumen

Este skill genera guias de usuario o de desarrollador claras y completas. Una buena guia permite al lector ir de "no se nada de esto" a "lo tengo funcionando y entiendo como usarlo" sin necesidad de ayuda externa. El tono es directo, los pasos son verificables y los ejemplos son funcionales.

La guia se adapta al publico: si es para usuarios finales, se evita jerga tecnica; si es para desarrolladores, se incluyen detalles de configuracion e integracion.

## Proceso

1. **Identificar al publico objetivo.** La guia se escribe de forma distinta segun quien la va a leer:

   - **Usuario final:** pasos simples, capturas de pantalla si aplica, lenguaje no tecnico.
   - **Desarrollador que integra:** ejemplos de codigo, documentacion de API, configuracion.
   - **Desarrollador que contribuye:** setup del entorno, convenios del proyecto, como ejecutar tests.

2. **Redactar la seccion de instalacion.** Paso a paso, sin saltar nada:

   - Requisitos previos (versiones de software, sistema operativo, herramientas necesarias).
   - Comandos de instalacion exactos, copiables y pegables.
   - Verificacion de que la instalacion ha funcionado (comando o pagina de prueba).
   - Errores comunes de instalacion y como resolverlos.

3. **Redactar la seccion de configuracion:**

   - Variables de entorno necesarias, con descripcion y ejemplo de valor.
   - Ficheros de configuracion, con plantilla y explicacion de cada campo.
   - Valores por defecto y cuando cambiarlos.

4. **Redactar la seccion de uso basico.** El caso de uso mas simple para que el lector vea resultados rapido:

   - Ejemplo minimo funcional (de principio a fin).
   - Explicacion de que hace cada paso.
   - Resultado esperado para que el lector pueda verificar.

5. **Redactar la seccion de uso avanzado.** Funcionalidades menos obvias pero importantes:

   - Configuraciones avanzadas.
   - Integraciones con otras herramientas.
   - Personalizacion y extension.
   - Patrones de uso recomendados.

6. **Redactar la seccion de troubleshooting.** Los problemas mas comunes y sus soluciones:

   | Problema | Causa probable | Solucion |
   |----------|---------------|----------|
   | Error X al arrancar | Falta variable de entorno Y | Anadir Y al fichero .env |
   | La pagina no carga | Puerto ocupado | Cambiar el puerto en config |

   Esta seccion se alimenta de las preguntas reales de los usuarios. Si no hay historico, anticipar los problemas mas probables.

7. **Redactar FAQ.** Preguntas frecuentes que no encajan en las secciones anteriores. Formato pregunta-respuesta, directo y conciso.

8. **Revisar con un lector fresco.** Si es posible, pedir a alguien que no conoce el proyecto que siga la guia y reporte donde se atasca.

## Criterios de exito

- La guia cubre instalacion, configuracion, uso basico, uso avanzado y troubleshooting.
- Los pasos de instalacion son reproducibles (se pueden seguir de cero a funcionando).
- Los ejemplos son funcionales y se pueden copiar directamente.
- El lenguaje esta adaptado al publico objetivo.
- Los problemas comunes tienen soluciones documentadas.
