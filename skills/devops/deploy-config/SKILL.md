---
name: deploy-config
description: "Usar para configurar despliegue segun hosting"
---

# Configurar despliegue

## Resumen

Este skill genera la configuracion necesaria para desplegar la aplicacion en el proveedor de hosting elegido. Cubre desde la configuracion basica (variables de entorno, dominio, SSL) hasta aspectos avanzados como estrategias de despliegue y planes de rollback.

Cada proveedor tiene sus particularidades, pero los principios son universales: despliegue reproducible, configuracion externalizada, rollback rapido y cero downtime siempre que sea posible.

## Proceso

1. **Identificar el proveedor de hosting.** Detectar la plataforma o preguntar al usuario:

   - **PaaS:** Vercel, Railway, Fly.io, Render, Heroku.
   - **IaaS/Cloud:** AWS (ECS, Lambda, EC2), GCP (Cloud Run, GKE), Azure.
   - **Self-hosted:** VPS con Docker, Kubernetes on-premise.

2. **Configurar variables de entorno.** Separar la configuracion del codigo:

   - Listar todas las variables necesarias (base de datos, APIs externas, secretos).
   - Diferenciar entre variables de build y variables de runtime.
   - Documentar cada variable: nombre, descripcion, valor por defecto, si es obligatoria.
   - Verificar que los secretos no tienen valores por defecto en el codigo.

3. **Configurar dominio y SSL:**

   - Dominio personalizado: DNS, registros A/CNAME.
   - SSL/TLS: certificado automatico (Let's Encrypt) o gestionado por el proveedor.
   - Redireccion HTTP a HTTPS obligatoria.
   - HSTS habilitado.

4. **Elegir estrategia de despliegue.** Segun las necesidades del proyecto:

   | Estrategia | Descripcion | Cuando usarla |
   |------------|-------------|---------------|
   | **Rolling** | Reemplaza instancias progresivamente | Default, bajo riesgo |
   | **Blue-green** | Dos entornos identicos, cambio instantaneo | Cuando se necesita rollback inmediato |
   | **Canary** | Porcentaje pequeno de trafico al nuevo deploy | Features de alto riesgo, validacion gradual |
   | **Recreate** | Para todo, despliega nuevo | Aceptable solo en entornos de desarrollo |

5. **Definir plan de rollback.** Que hacer si el despliegue sale mal:

   - Como detectar que algo va mal (metricas, alertas, health checks).
   - Como volver a la version anterior (comando concreto o proceso).
   - Tiempo maximo para decidir si hacer rollback.
   - Quien tiene autoridad para ejecutar el rollback.

6. **Configurar health checks.** El proveedor necesita saber si la aplicacion esta sana:

   - Endpoint de salud (GET /health o similar).
   - Criterios: respuesta 200, tiempo de respuesta < Xms.
   - Periodo de gracia tras el despliegue (start period).

7. **Generar ficheros de configuracion.** Segun el proveedor:

   - Vercel: `vercel.json`.
   - Railway: `railway.toml` o Procfile.
   - Fly.io: `fly.toml`.
   - AWS: `task-definition.json`, `appspec.yml`, etc.
   - Docker Compose: `docker-compose.yml` para entornos con multiples servicios.

8. **Documentar el proceso.** Dejar instrucciones claras de como desplegar manualmente si la automatizacion falla.

## Criterios de exito

- La configuracion del proveedor esta generada y lista para usar.
- Las variables de entorno estan documentadas y los secretos no tienen valores por defecto.
- El dominio y SSL estan configurados con redireccion HTTPS.
- Hay una estrategia de despliegue elegida y justificada.
- Existe un plan de rollback documentado.
- Los health checks estan configurados.
