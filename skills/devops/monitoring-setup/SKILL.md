---
name: monitoring-setup
description: "Configurar observabilidad del servicio. Activar cuando el usuario quiera configurar logging, integrar Sentry, implementar error tracking, definir metricas, configurar alertas, mejorar la observabilidad o monitorizar un servicio."
---

# Configurar observabilidad

## Resumen

Este skill configura las tres patas de la observabilidad: logging estructurado, error tracking y métricas. Sin observabilidad, operar un servicio en producción es como conducir de noche sin luces: todo va bien hasta que no. El objetivo es poder responder a tres preguntas fundamentales: qué está pasando ahora, qué ha pasado antes y por qué algo falla.

## Proceso

1. **Configurar logging estructurado.** Los logs en texto plano son difíciles de buscar y analizar. Usar JSON como formato estándar:

   ```json
   {
     "timestamp": "2024-03-15T10:30:00Z",
     "level": "error",
     "message": "Fallo al procesar pago",
     "service": "payment-service",
     "requestId": "abc-123",
     "userId": "usr-456",
     "error": {
       "type": "PaymentGatewayError",
       "message": "Timeout after 30s",
       "stack": "..."
     }
   }
   ```

   Principios del logging:

   - Cada entrada tiene timestamp, nivel, mensaje y contexto.
   - Los request IDs permiten trazar un flujo a través de múltiples servicios.
   - Los datos sensibles (contraseñas, tokens, datos personales) NUNCA aparecen en logs.
   - Niveles: `debug` (desarrollo), `info` (flujo normal), `warn` (situación inusual), `error` (algo falló).

2. **Configurar error tracking.** Herramientas como Sentry, Bugsnag o Rollbar proporcionan contexto rico para cada error:

   - Instalación del SDK en la aplicación.
   - Configuración del DSN (endpoint de reporte).
   - Source maps para errores de frontend (si aplica).
   - Agrupación de errores para evitar ruido.
   - Alertas para errores nuevos o con picos de frecuencia.
   - Integración con el sistema de issues (GitHub, Jira) para seguimiento.

3. **Definir métricas de negocio y técnicas.** Las métricas cuentan la historia del sistema en números:

   - **Técnicas:** latencia de requests (p50, p95, p99), tasa de error, uso de CPU/memoria, conexiones a base de datos.
   - **Negocio:** registros por hora, transacciones completadas, tasa de conversión, usuarios activos.

   Las métricas de negocio son las que más interesan al equipo de producto; las técnicas son las que interesan a operaciones.

4. **Configurar alertas.** Las alertas deben ser accionables, no ruidosas:

   - **Crítica:** el servicio está caído o perdiendo datos. Requiere acción inmediata (pagina al ingeniero de guardia).
   - **Alta:** tasa de error elevada o degradación significativa. Requiere atención en la próxima hora.
   - **Media:** tendencia preocupante que no requiere acción inmediata. Revisar en el próximo día laborable.

   Evitar alertas que nadie mira. Si una alerta se ignora sistemáticamente, o se elimina o se ajusta su umbral.

5. **Implementar health endpoints.** La aplicación debe exponer su estado de salud:

   - `GET /health`: responde 200 si la aplicación está corriendo (liveness).
   - `GET /ready`: responde 200 si la aplicación puede procesar requests (readiness). Incluye verificación de dependencias críticas (base de datos, caché).

6. **Documentar la configuración.** Dejar claro dónde se visualizan los logs, cómo se accede al error tracking y qué dashboards están disponibles.

## Criterios de éxito

- Los logs son estructurados (JSON) con timestamp, nivel, mensaje y contexto.
- No hay datos sensibles en los logs.
- El error tracking está integrado y agrupa errores correctamente.
- Las métricas cubren al menos latencia, tasa de error y una métrica de negocio.
- Las alertas son accionables y están clasificadas por severidad.
- Los health endpoints están implementados y responden correctamente.

## Que NO hacer

- No loguear datos personales (PII). Nombres, emails, direcciones IP, tokens de sesión y cualquier dato identificable deben ser redactados o excluidos de los logs para cumplir con GDPR y buenas prácticas de seguridad.
- No configurar alertas sin definir umbrales concretos. Una alerta sin umbral genera ruido y se acaba ignorando. Cada alerta debe tener un criterio numérico que determine cuándo se dispara y cuándo se resuelve.
