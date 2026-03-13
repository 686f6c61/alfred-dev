---
name: ci-cd-pipeline
description: "Configurar pipeline CI/CD adaptado al proyecto. Activar cuando el usuario quiera configurar CI, crear GitHub Actions, configurar GitLab CI, montar un pipeline de despliegue, automatizar tests o implementar integracion continua."
---

# Configurar pipeline CI/CD

## Resumen

Este skill genera la configuración de un pipeline de integración y despliegue continuo adaptado al stack y la plataforma del proyecto. El pipeline automatiza las verificaciones de calidad (lint, tests, seguridad) y el despliegue, eliminando pasos manuales propensos a error.

Un buen pipeline es rápido (feedback en minutos, no en horas), fiable (no falla aleatoriamente) y seguro (no expone secretos ni permite despliegues sin verificación).

## Proceso

1. **Detectar la plataforma de CI/CD.** Consultar el stack detectado en la configuración de Alfred para adaptar el pipeline al lenguaje, framework y herramientas del proyecto. Identificar dónde se ejecutará el pipeline:

   - **GitHub Actions:** `.github/workflows/`.
   - **GitLab CI:** `.gitlab-ci.yml`.
   - **Bitbucket Pipelines:** `bitbucket-pipelines.yml`.
   - **CircleCI:** `.circleci/config.yml`.
   - **Jenkins:** `Jenkinsfile`.

   Si no hay preferencia, recomendar GitHub Actions por su ecosistema y facilidad de uso.

2. **Definir los stages del pipeline.** El orden estándar es:

   | Stage | Propósito | Falla si... |
   |-------|-----------|-------------|
   | **Lint** | Verificar estilo y errores estáticos | Hay errores de linter |
   | **Test** | Ejecutar tests unitarios e integración | Algún test falla |
   | **Build** | Compilar/construir el artefacto | La build falla |
   | **Security** | Escanear vulnerabilidades | Hay CVE críticos o altos |
   | **Deploy** | Desplegar al entorno objetivo | El despliegue falla |

3. **Configurar caché de dependencias.** Evitar descargar las mismas dependencias en cada ejecución:

   - Node.js: cachear `node_modules` con key basada en `package-lock.json`.
   - Python: cachear el directorio de pip con key basada en `requirements.txt`.
   - Rust: cachear `target/` y el directorio de cargo.

4. **Gestionar secretos.** Los secretos (tokens, contraseñas, API keys) nunca van en el código:

   - Usar el sistema de secretos de la plataforma (GitHub Secrets, GitLab Variables, etc.).
   - Referenciar como variables de entorno en el pipeline.
   - Documentar qué secretos son necesarios y dónde se configuran.

5. **Configurar triggers.** Definir cuándo se ejecuta el pipeline:

   - Push a ramas principales (main, develop): pipeline completo.
   - Pull requests: lint + test + build (sin deploy).
   - Tags de versión: pipeline completo con deploy a producción.

6. **Configurar notificaciones de fallo.** El equipo debe enterarse rápidamente cuando algo falla:

   - Notificación a Slack, email o similar cuando un stage falla.
   - Indicar qué stage falló y enlace al log.

7. **Configurar estrategia de deploy.** Según el entorno:

   - Staging: deploy automático en cada merge a develop.
   - Producción: deploy manual o automático en cada tag de versión, según la preferencia del equipo.

8. **Documentar el pipeline.** Añadir un comentario en el fichero de configuración explicando cada stage y cómo añadir nuevos pasos.

## Criterios de éxito

- El pipeline cubre lint, test, build, security y deploy.
- Las dependencias se cachean para acelerar la ejecución.
- Los secretos se gestionan vía variables de entorno de la plataforma, no en el código.
- Los triggers están configurados para PRs, pushes y tags.
- Hay notificaciones de fallo configuradas.
- El fichero de configuración está documentado con comentarios.

## Que NO hacer

- No crear pipelines sin paso de tests. Un pipeline sin verificación automática no aporta confianza; simplemente automatiza despliegues potencialmente rotos.
- No guardar secretos en el código del pipeline. Los tokens, contraseñas y API keys se gestionan exclusivamente a través del sistema de secretos de la plataforma (GitHub Secrets, GitLab Variables, etc.), nunca en texto plano en el fichero de configuración.
