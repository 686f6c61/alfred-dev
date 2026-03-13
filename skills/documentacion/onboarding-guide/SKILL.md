---
name: onboarding-guide
description: "Generar una guía de onboarding para nuevos desarrolladores del proyecto. Activar ante: guia para nuevos, como empezar, setup del proyecto, incorporacion al equipo"
---

# Guía de onboarding para nuevos desarrolladores

## Resumen

Este skill genera una guía paso a paso para que un desarrollador nuevo pueda incorporarse al proyecto con el mínimo de fricciones. La guía cubre desde la instalación del entorno hasta la primera contribución, pasando por la comprensión de la arquitectura y las convenciones del equipo.

Una buena guía de onboarding reduce el tiempo que un nuevo miembro tarda en ser productivo de semanas a días. Es una inversión que se amortiza con cada incorporación.

## Proceso

### Paso 1: analizar el proyecto

- Leer el README, CLAUDE.md y documentación existente.
- Identificar el stack tecnológico y las herramientas necesarias.
- Revisar las convenciones de código, Git y testing.
- Detectar conocimiento implícito que no está documentado en ningún sitio.

### Paso 2: crear docs/onboarding.md

Estructurar la guía en estas secciones:

1. **Bienvenida**: qué hace el proyecto, para quién y por qué existe. Contexto en 3-4 frases.

2. **Requisitos previos**: lista de herramientas con versiones exactas. Comandos para verificar cada una.

3. **Setup del entorno**: paso a paso desde clonar el repo hasta tener la aplicación corriendo en local. Incluir solución de problemas comunes.

4. **Estructura del proyecto**: mapa de directorios con descripción de cada carpeta importante. No listar todo: solo lo que un nuevo developer necesita saber.

5. **Arquitectura**: explicación de alto nivel. Componentes principales, flujo de datos, patrones usados. Enlazar a docs/architecture.md si existe.

6. **Convenciones**: formato de commits, nombrado de ramas, estilo de código, proceso de PR.

7. **Tests**: cómo ejecutar la suite, cómo añadir tests nuevos, qué cobertura se espera.

8. **Primera tarea**: sugerir una tarea pequeña y bien definida para la primera contribución (arreglar un bug menor, mejorar documentación, añadir un test).

### Paso 3: verificar la guía

- Seguir los pasos de la guía en un entorno limpio (mentalmente o con un directorio nuevo).
- Verificar que todos los comandos funcionan y que las rutas son correctas.
- Pedir al usuario que revise si falta algo que un nuevo miembro necesitaría saber.

## Qué NO hacer

- No asumir conocimiento previo sobre el proyecto ni sobre herramientas específicas.
- No escribir instrucciones vagas ("configura la base de datos"). Ser específico ("ejecuta docker compose up -d para levantar PostgreSQL en local").
- No incluir información que cambia frecuentemente sin indicar dónde consultarla actualizada.
