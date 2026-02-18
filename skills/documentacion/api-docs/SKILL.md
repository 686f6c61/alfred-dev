---
name: api-docs
description: "Usar para documentar API con endpoints, parametros y ejemplos"
---

# Documentar API

## Resumen

Este skill genera documentacion completa de una API, cubriendo cada endpoint con sus parametros, respuestas, codigos de error y ejemplos de uso. La documentacion de API es el contrato entre el backend y sus consumidores (frontend, servicios externos, desarrolladores de terceros); si esta mal documentada, genera confusion, bugs y soporte innecesario.

El formato puede ser Markdown para documentacion legible o OpenAPI (Swagger) para documentacion interactiva y generacion automatica de clientes.

## Proceso

1. **Identificar los endpoints a documentar.** Revisar el codigo del proyecto para listar todas las rutas expuestas. Agruparlas por recurso o dominio funcional.

2. **Para cada endpoint, documentar:**

   - **Metodo HTTP:** GET, POST, PUT, PATCH, DELETE.
   - **Ruta:** con parametros de ruta entre llaves (por ejemplo, `/users/{id}`).
   - **Descripcion:** que hace este endpoint en una frase.
   - **Autenticacion:** que tipo de autenticacion requiere (Bearer token, API key, ninguna).
   - **Parametros de ruta:** nombre, tipo, descripcion, si es obligatorio.
   - **Parametros de query:** nombre, tipo, descripcion, valor por defecto.
   - **Cuerpo de la peticion (body):** esquema JSON con tipos, campos obligatorios y restricciones. Incluir ejemplo.
   - **Respuestas:** para cada codigo de estado relevante, el esquema de la respuesta y un ejemplo.

3. **Cubrir los codigos de respuesta principales:**

   | Codigo | Significado | Cuando se devuelve |
   |--------|------------|-------------------|
   | 200 | OK | Peticion exitosa (GET, PUT, PATCH) |
   | 201 | Created | Recurso creado exitosamente (POST) |
   | 204 | No Content | Operacion exitosa sin cuerpo de respuesta (DELETE) |
   | 400 | Bad Request | Datos de entrada invalidos |
   | 401 | Unauthorized | Falta autenticacion o token invalido |
   | 403 | Forbidden | Autenticado pero sin permisos |
   | 404 | Not Found | Recurso no existe |
   | 409 | Conflict | Conflicto con el estado actual (duplicado, version desactualizada) |
   | 422 | Unprocessable Entity | Datos validos pero no procesables por reglas de negocio |
   | 429 | Too Many Requests | Rate limit excedido |
   | 500 | Internal Server Error | Error inesperado del servidor |

4. **Incluir ejemplos con curl.** Para cada endpoint, al menos un ejemplo funcional:

   ```bash
   curl -X POST https://api.ejemplo.com/users \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Ana", "email": "ana@ejemplo.com"}'
   ```

5. **Documentar codigos de error personalizados.** Si la API devuelve errores con codigos propios, listarlos con su significado y la accion recomendada para el consumidor.

6. **Si se usa OpenAPI, generar el fichero de especificacion.** Formato YAML o JSON compatible con OpenAPI 3.x. Incluir schemas reutilizables en `components/schemas`.

7. **Verificar la documentacion contra el codigo.** Comprobar que cada endpoint documentado existe en el codigo y que los parametros y respuestas coinciden. La documentacion desactualizada es peor que no tener documentacion.

## Criterios de exito

- Todos los endpoints publicos estan documentados.
- Cada endpoint tiene metodo, ruta, parametros, respuestas y al menos un ejemplo.
- Los codigos de error estan documentados con su significado.
- Los ejemplos son funcionales (se podrian copiar y pegar para probar).
- La documentacion esta sincronizada con el codigo actual.
