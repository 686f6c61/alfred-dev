---
name: e2e-testing
description: "Configurar y escribir tests end-to-end con Playwright o Cypress. También: validar flujos de usuario completos, testing de integración en navegador, tests E2E en CI, tests de aceptación, smoke tests en producción."
---

# Testing end-to-end

## Resumen

Los tests end-to-end (E2E) validan flujos completos desde la perspectiva del usuario, interactuando con la aplicación tal y como lo haría una persona real: navegando por la interfaz, rellenando formularios, haciendo clic en botones y verificando que el resultado es el esperado. Son el último eslabón de la pirámide de testing y complementan a los tests unitarios y de integración.

Su valor principal reside en detectar problemas de integración entre componentes que los tests unitarios no pueden cubrir: una API que devuelve datos en un formato que el frontend no espera, un flujo de autenticación que falla cuando intervienen cookies y redirecciones, o un proceso de checkout que se rompe al combinar descuentos con impuestos. Son más lentos y más frágiles que los tests unitarios, por lo que deben reservarse para los flujos más críticos del sistema.

## Proceso

### Paso 1: elegir la herramienta

Seleccionar la herramienta de testing E2E según el stack del proyecto. Consultar la configuración de Alfred para detectar el stack automáticamente.

| Herramienta | Cuándo elegirla |
|-------------|-----------------|
| **Playwright** | Opción recomendada por defecto. Soporte multi-navegador (Chromium, Firefox, WebKit), API moderna, buena integración con CI. |
| **Cypress** | Alternativa válida si el equipo ya lo usa o si el proyecto es exclusivamente web con un solo navegador objetivo. |

Si no hay preferencia previa, usar Playwright.

### Paso 2: configurar el entorno

1. Instalar la herramienta y sus dependencias (navegadores incluidos).
2. Crear la configuración base (fichero de config, directorios de tests y fixtures).
3. Configurar el entorno de test: URL base, credenciales de test, datos de seed.
4. Verificar que la aplicación arranca correctamente en el entorno de test.

### Paso 3: identificar los flujos críticos

No todos los flujos necesitan cobertura E2E. Priorizar los que cumplen al menos uno de estos criterios:

- **Alto impacto de fallo:** si se rompe, el usuario no puede completar su objetivo (registro, login, compra, envío de formulario principal).
- **Cruza múltiples componentes:** frontend, backend, base de datos, servicios externos.
- **Historial de bugs:** flujos donde se han detectado regresiones en el pasado.
- **Requisito de negocio:** flujos que el producto owner considera críticos.

Ejemplos típicos: registro de usuario, login/logout, checkout o proceso de pago, creación y edición del recurso principal, flujos de permisos y roles.

### Paso 4: escribir los tests

Seguir el patrón Arrange-Act-Assert en cada test:

1. **Arrange:** preparar el estado inicial (datos de seed, usuario autenticado, página cargada).
2. **Act:** ejecutar las acciones del usuario (navegar, rellenar, hacer clic).
3. **Assert:** verificar el resultado esperado (elemento visible, datos guardados, redirección correcta).

Principios de escritura:

- Un test, un flujo. No encadenar múltiples flujos en un solo test.
- Usar selectores estables (data-testid, roles ARIA), no clases CSS ni XPath frágiles.
- No depender del orden de ejecución. Cada test debe poder ejecutarse de forma independiente.
- Preparar y limpiar los datos de cada test (fixtures, API calls de setup/teardown).

### Paso 5: configurar en CI

Integrar los tests E2E en el pipeline de CI para que se ejecuten automáticamente:

- Configurar el job en GitHub Actions (u otro CI) con los navegadores necesarios.
- Ejecutar los tests contra un entorno de staging o un servidor levantado en el propio CI.
- Configurar reintentos automáticos (1-2 reintentos) para mitigar tests inestables mientras se corrigen.
- Publicar los artefactos de fallo (screenshots, vídeos, traces) para facilitar la depuración.

### Paso 6: ejecutar y verificar

- Ejecutar la suite completa en local antes de integrar en CI.
- Verificar que todos los tests pasan de forma consistente (ejecutar al menos 3 veces para detectar flakiness).
- Revisar los tiempos de ejecución: una suite E2E que tarda más de 10 minutos necesita optimización o paralelización.

## Criterios de éxito

- Los flujos críticos del usuario están cubiertos por al menos un test E2E.
- Los tests son estables: pasan de forma consistente en múltiples ejecuciones consecutivas.
- Los tests corren en CI automáticamente en cada push o pull request.
- Los tests son independientes entre sí: se pueden ejecutar en cualquier orden sin afectarse.
- Los artefactos de fallo (screenshots, vídeos) están disponibles para depuración.
- El tiempo total de la suite es razonable (menos de 10 minutos para proyectos medianos).

## Qué NO hacer

- No intentar cubrir todo con E2E. Reservar los tests E2E para flujos críticos que cruzan múltiples componentes; el resto se cubre mejor con tests unitarios y de integración, que son más rápidos y menos frágiles.
- No depender de datos de producción en los tests. Usar datos de seed controlados que el propio test prepara y limpia.
- No usar sleeps fijos (`sleep(3000)`) para esperar a que algo ocurra. Usar condiciones de espera explícitas (`waitForSelector`, `waitForResponse`, `waitForURL`) que resuelven en cuanto la condición se cumple.
- No hacer tests E2E para lógica de negocio pura. Si una función calcula un descuento, eso es un test unitario. El test E2E verifica que el descuento aparece correctamente en la interfaz.
- No ignorar los tests inestables (flaky). Un test que falla intermitentemente erosiona la confianza en la suite y hace que el equipo deje de prestar atención a los fallos reales. Corregirlos o eliminarlos.
- No ejecutar los tests solo en un navegador si la aplicación soporta varios. Al menos cubrir Chromium y Firefox.
