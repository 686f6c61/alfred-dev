---
name: ci-cd-pipeline
description: "Usar para configurar pipeline CI/CD adaptado al proyecto"
---

# Configurar pipeline CI/CD

## Resumen

Este skill genera la configuracion de un pipeline de integracion y despliegue continuo adaptado al stack y la plataforma del proyecto. El pipeline automatiza las verificaciones de calidad (lint, tests, seguridad) y el despliegue, eliminando pasos manuales propensos a error.

Un buen pipeline es rapido (feedback en minutos, no en horas), fiable (no falla aleatoriamente) y seguro (no expone secretos ni permite despliegues sin verificacion).

## Proceso

1. **Detectar la plataforma de CI/CD.** Identificar donde se ejecutara el pipeline:

   - **GitHub Actions:** `.github/workflows/`.
   - **GitLab CI:** `.gitlab-ci.yml`.
   - **Bitbucket Pipelines:** `bitbucket-pipelines.yml`.
   - **CircleCI:** `.circleci/config.yml`.
   - **Jenkins:** `Jenkinsfile`.

   Si no hay preferencia, recomendar GitHub Actions por su ecosistema y facilidad de uso.

2. **Definir los stages del pipeline.** El orden estandar es:

   | Stage | Proposito | Falla si... |
   |-------|-----------|-------------|
   | **Lint** | Verificar estilo y errores estaticos | Hay errores de linter |
   | **Test** | Ejecutar tests unitarios e integracion | Algun test falla |
   | **Build** | Compilar/construir el artefacto | La build falla |
   | **Security** | Escanear vulnerabilidades | Hay CVE criticos o altos |
   | **Deploy** | Desplegar al entorno objetivo | El despliegue falla |

3. **Configurar cache de dependencias.** Evitar descargar las mismas dependencias en cada ejecucion:

   - Node.js: cachear `node_modules` con key basada en `package-lock.json`.
   - Python: cachear el directorio de pip con key basada en `requirements.txt`.
   - Rust: cachear `target/` y el directorio de cargo.

4. **Gestionar secretos.** Los secretos (tokens, contrasenas, API keys) nunca van en el codigo:

   - Usar el sistema de secretos de la plataforma (GitHub Secrets, GitLab Variables, etc.).
   - Referenciar como variables de entorno en el pipeline.
   - Documentar que secretos son necesarios y donde se configuran.

5. **Configurar triggers.** Definir cuando se ejecuta el pipeline:

   - Push a ramas principales (main, develop): pipeline completo.
   - Pull requests: lint + test + build (sin deploy).
   - Tags de version: pipeline completo con deploy a produccion.

6. **Configurar notificaciones de fallo.** El equipo debe enterarse rapidamente cuando algo falla:

   - Notificacion a Slack, email o similar cuando un stage falla.
   - Indicar que stage fallo y enlace al log.

7. **Configurar estrategia de deploy.** Segun el entorno:

   - Staging: deploy automatico en cada merge a develop.
   - Produccion: deploy manual o automatico en cada tag de version, segun la preferencia del equipo.

8. **Documentar el pipeline.** Anadir un comentario en el fichero de configuracion explicando cada stage y como anadir nuevos pasos.

## Criterios de exito

- El pipeline cubre lint, test, build, security y deploy.
- Las dependencias se cachean para acelerar la ejecucion.
- Los secretos se gestionan via variables de entorno de la plataforma, no en el codigo.
- Los triggers estan configurados para PRs, pushes y tags.
- Hay notificaciones de fallo configuradas.
- El fichero de configuracion esta documentado con comentarios.
