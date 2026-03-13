---
name: deploy-config
description: "Configurar despliegue según hosting. Activar cuando el usuario quiera desplegar en Vercel, Railway, AWS, configurar hosting, preparar para produccion o gestionar variables de entorno de despliegue."
---

# Configurar despliegue

## Resumen

Este skill genera la configuración necesaria para desplegar la aplicación en el proveedor de hosting elegido. Cubre desde la configuración básica (variables de entorno, dominio, SSL) hasta aspectos avanzados como estrategias de despliegue y planes de rollback.

Cada proveedor tiene sus particularidades, pero los principios son universales: despliegue reproducible, configuración externalizada, rollback rápido y cero downtime siempre que sea posible.

## Proceso

1. **Identificar el proveedor de hosting.** Consultar el stack detectado en la configuración de Alfred para adaptar la configuración al lenguaje y framework del proyecto. Detectar la plataforma o preguntar al usuario:

   - **PaaS:** Vercel, Railway, Fly.io, Render, Heroku.
   - **IaaS/Cloud:** AWS (ECS, Lambda, EC2), GCP (Cloud Run, GKE), Azure.
   - **Self-hosted:** VPS con Docker, Kubernetes on-premise.

2. **Configurar variables de entorno.** Separar la configuración del código:

   - Listar todas las variables necesarias (base de datos, APIs externas, secretos).
   - Diferenciar entre variables de build y variables de runtime.
   - Documentar cada variable: nombre, descripción, valor por defecto, si es obligatoria.
   - Verificar que los secretos no tienen valores por defecto en el código.

3. **Configurar dominio y SSL:**

   - Dominio personalizado: DNS, registros A/CNAME.
   - SSL/TLS: certificado automático (Let's Encrypt) o gestionado por el proveedor.
   - Redirección HTTP a HTTPS obligatoria.
   - HSTS habilitado.

4. **Elegir estrategia de despliegue.** Según las necesidades del proyecto:

   | Estrategia | Descripción | Cuándo usarla |
   |------------|-------------|---------------|
   | **Rolling** | Reemplaza instancias progresivamente | Default, bajo riesgo |
   | **Blue-green** | Dos entornos idénticos, cambio instantáneo | Cuando se necesita rollback inmediato |
   | **Canary** | Porcentaje pequeño de tráfico al nuevo deploy | Features de alto riesgo, validación gradual |
   | **Recreate** | Para todo, despliega nuevo | Aceptable solo en entornos de desarrollo |

5. **Definir plan de rollback.** Qué hacer si el despliegue sale mal:

   - Cómo detectar que algo va mal (métricas, alertas, health checks).
   - Cómo volver a la versión anterior (comando concreto o proceso).
   - Tiempo máximo para decidir si hacer rollback.
   - Quién tiene autoridad para ejecutar el rollback.

6. **Configurar health checks.** El proveedor necesita saber si la aplicación está sana:

   - Endpoint de salud (GET /health o similar).
   - Criterios: respuesta 200, tiempo de respuesta < Xms.
   - Período de gracia tras el despliegue (start period).

7. **Generar ficheros de configuración.** Según el proveedor:

   - Vercel: `vercel.json`.
   - Railway: `railway.toml` o Procfile.
   - Fly.io: `fly.toml`.
   - AWS: `task-definition.json`, `appspec.yml`, etc.
   - Docker Compose: `docker-compose.yml` para entornos con múltiples servicios.

8. **Documentar el proceso.** Dejar instrucciones claras de cómo desplegar manualmente si la automatización falla.

## Criterios de éxito

- La configuración del proveedor está generada y lista para usar.
- Las variables de entorno están documentadas y los secretos no tienen valores por defecto.
- El dominio y SSL están configurados con redirección HTTPS.
- Hay una estrategia de despliegue elegida y justificada.
- Existe un plan de rollback documentado.
- Los health checks están configurados.

## Que NO hacer

- No desplegar a producción sin haber verificado el despliegue en un entorno de staging o preview con datos representativos.
- No exponer variables de entorno sensibles en logs, respuestas de API o ficheros de configuración versionados.
- No desplegar sin una estrategia de rollback documentada y probada. Si algo sale mal, el tiempo de recuperación debe medirse en minutos, no en horas.
