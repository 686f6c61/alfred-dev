---
name: api-docs
description: "Usar para documentar API con endpoints, parámetros y ejemplos. Activar ante: documentar API, endpoints, OpenAPI, Swagger, parametros, respuestas de la API"
---

# Documentar API

## Resumen

Este skill genera documentación completa de una API, cubriendo cada endpoint con sus parámetros, respuestas, códigos de error y ejemplos de uso. La documentación de API es el contrato entre el backend y sus consumidores (frontend, servicios externos, desarrolladores de terceros); si está mal documentada, genera confusión, bugs y soporte innecesario.

El formato puede ser Markdown para documentación legible o OpenAPI (Swagger) para documentación interactiva y generación automática de clientes.

## Proceso

1. **Identificar los endpoints a documentar.** Revisar el código del proyecto para listar todas las rutas expuestas. Agruparlas por recurso o dominio funcional.

2. **Para cada endpoint, documentar:**

   - **Método HTTP:** GET, POST, PUT, PATCH, DELETE.
   - **Ruta:** con parámetros de ruta entre llaves (por ejemplo, `/users/{id}`).
   - **Descripción:** qué hace este endpoint en una frase.
   - **Autenticación:** qué tipo de autenticación requiere (Bearer token, API key, ninguna).
   - **Parámetros de ruta:** nombre, tipo, descripción, si es obligatorio.
   - **Parámetros de query:** nombre, tipo, descripción, valor por defecto.
   - **Cuerpo de la petición (body):** esquema JSON con tipos, campos obligatorios y restricciones. Incluir ejemplo.
   - **Respuestas:** para cada código de estado relevante, el esquema de la respuesta y un ejemplo.

3. **Cubrir los códigos de respuesta principales:**

   | Código | Significado | Cuándo se devuelve |
   |--------|------------|-------------------|
   | 200 | OK | Petición exitosa (GET, PUT, PATCH) |
   | 201 | Created | Recurso creado exitosamente (POST) |
   | 204 | No Content | Operación exitosa sin cuerpo de respuesta (DELETE) |
   | 400 | Bad Request | Datos de entrada inválidos |
   | 401 | Unauthorized | Falta autenticación o token inválido |
   | 403 | Forbidden | Autenticado pero sin permisos |
   | 404 | Not Found | Recurso no existe |
   | 409 | Conflict | Conflicto con el estado actual (duplicado, versión desactualizada) |
   | 422 | Unprocessable Entity | Datos válidos pero no procesables por reglas de negocio |
   | 429 | Too Many Requests | Rate limit excedido |
   | 500 | Internal Server Error | Error inesperado del servidor |

4. **Incluir ejemplos con curl.** Para cada endpoint, al menos un ejemplo funcional:

   ```bash
   curl -X POST https://api.ejemplo.com/users \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Ana", "email": "ana@ejemplo.com"}'
   ```

5. **Documentar códigos de error personalizados.** Si la API devuelve errores con códigos propios, listarlos con su significado y la acción recomendada para el consumidor.

6. **Si se usa OpenAPI, generar el fichero de especificación.** Formato YAML o JSON compatible con OpenAPI 3.x. Incluir schemas reutilizables en `components/schemas`.

7. **Verificar la documentación contra el código.** Comprobar que cada endpoint documentado existe en el código y que los parámetros y respuestas coinciden. La documentación desactualizada es peor que no tener documentación.

## Criterios de éxito

- Todos los endpoints públicos están documentados.
- Cada endpoint tiene método, ruta, parámetros, respuestas y al menos un ejemplo.
- Los códigos de error están documentados con su significado.
- Los ejemplos son funcionales (se podrían copiar y pegar para probar).
- La documentación está sincronizada con el código actual.
