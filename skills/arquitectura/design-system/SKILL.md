---
name: design-system
description: "Usar para disenar la arquitectura de un sistema con diagramas y contratos"
---

# Disenar arquitectura del sistema

## Resumen

Este skill produce el diseno arquitectonico de un sistema o modulo, incluyendo diagramas de componentes, contratos entre modulos y decisiones de diseno fundamentales. El resultado es un documento que permite a cualquier desarrollador del equipo entender como encajan las piezas antes de escribir codigo.

La arquitectura no se disena para impresionar, sino para comunicar. Los diagramas deben ser claros, los contratos precisos y las decisiones justificadas.

## Proceso

1. **Entender los requisitos.** Leer el PRD si existe. Identificar los requisitos funcionales (que hace el sistema) y los no funcionales (rendimiento, escalabilidad, seguridad, disponibilidad). Los requisitos no funcionales suelen ser los que mas condicionan la arquitectura.

2. **Definir los componentes principales.** Identificar los modulos, servicios o capas del sistema. Para cada componente, documentar:

   - Responsabilidad principal (una sola, siguiendo SRP).
   - Inputs que recibe.
   - Outputs que produce.
   - Dependencias externas.

3. **Generar diagrama de componentes con Mermaid:**

   ```mermaid
   graph TD
     A[Cliente] --> B[API Gateway]
     B --> C[Servicio Auth]
     B --> D[Servicio Core]
     D --> E[(Base de datos)]
     D --> F[Cola de mensajes]
   ```

   El diagrama debe mostrar los componentes y sus relaciones, no los detalles internos de cada uno.

4. **Generar diagrama de secuencia para los flujos criticos:**

   ```mermaid
   sequenceDiagram
     participant U as Usuario
     participant A as API
     participant D as DB
     U->>A: POST /recurso
     A->>D: INSERT
     D-->>A: OK
     A-->>U: 201 Created
   ```

   Cubrir al menos el happy path y el principal flujo de error.

5. **Definir contratos entre modulos.** Para cada interfaz entre componentes, especificar:

   - Formato de datos (tipos, esquemas).
   - Protocolo de comunicacion (HTTP, gRPC, eventos, etc.).
   - Manejo de errores (codigos, reintentos, fallbacks).
   - Versionado del contrato.

6. **Aplicar principios SOLID.** Verificar que el diseno respeta:

   - **S**ingle Responsibility: cada componente tiene una razon para cambiar.
   - **O**pen/Closed: extensible sin modificar lo existente.
   - **L**iskov Substitution: las implementaciones son intercambiables.
   - **I**nterface Segregation: interfaces pequenas y especificas.
   - **D**ependency Inversion: depender de abstracciones, no de implementaciones concretas.

7. **Documentar decisiones no obvias.** Si se elige un patron (Event Sourcing, CQRS, Hexagonal, etc.), explicar por que es adecuado para este caso y que alternativas se descartaron.

8. **Revisar con el usuario.** La arquitectura es una decision de equipo. Presentar el diseno, recoger feedback e iterar antes de implementar.

## Criterios de exito

- El diseno incluye al menos un diagrama de componentes y un diagrama de secuencia en Mermaid.
- Cada componente tiene su responsabilidad documentada.
- Los contratos entre modulos estan definidos con tipos y manejo de errores.
- Las decisiones de diseno estan justificadas, no son arbitrarias.
- El usuario ha validado la arquitectura propuesta.
