---
name: architecture-docs
description: "Usar para documentar la arquitectura del sistema. Activar ante: documentar arquitectura, diagrama del sistema, como funciona el proyecto, vision general tecnica"
---

# Documentar arquitectura del sistema

## Resumen

Este skill genera documentación arquitectónica que permite a cualquier desarrollador nuevo entender cómo funciona el sistema sin necesidad de leer todo el código. Cubre la visión general, los componentes principales, los flujos de datos, las dependencias externas y los enlaces a las decisiones arquitectónicas (ADRs) que explican el por qué de cada elección.

La documentación arquitectónica es un mapa del sistema: no necesita cubrir cada detalle, pero debe permitir orientarse y saber dónde buscar.

## Proceso

1. **Redactar la visión general.** En 2-3 párrafos, explicar:

   - Qué es el sistema y qué problema resuelve.
   - A quién va dirigido (usuarios, otros servicios, el equipo interno).
   - Qué principios de diseño guían la arquitectura.

2. **Documentar los componentes principales.** Para cada componente significativo:

   - Nombre y propósito.
   - Responsabilidades (qué hace y qué no hace).
   - Tecnologías que usa.
   - Interfaces públicas (cómo se comunica con otros componentes).
   - Ubicación en el código (directorio o módulo).

3. **Generar diagrama de componentes con Mermaid.** Un diagrama vale más que mil palabras, pero solo si es claro:

   ```mermaid
   graph TD
     subgraph Frontend
       A[SPA React]
     end
     subgraph Backend
       B[API REST]
       C[Worker Jobs]
     end
     subgraph Datos
       D[(PostgreSQL)]
       E[(Redis Cache)]
     end
     A -->|HTTP/JSON| B
     B --> D
     B --> E
     B -->|Encola| C
     C --> D
   ```

   Mantener el diagrama simple. Si es demasiado complejo, dividir en múltiples diagramas por dominio.

4. **Documentar los flujos de datos principales.** Para los 2-3 flujos más importantes del sistema, generar diagramas de secuencia que muestren cómo se mueven los datos entre componentes:

   ```mermaid
   sequenceDiagram
     participant U as Usuario
     participant F as Frontend
     participant A as API
     participant D as DB
     U->>F: Acción del usuario
     F->>A: Request HTTP
     A->>D: Query
     D-->>A: Resultado
     A-->>F: Response JSON
     F-->>U: Actualiza interfaz
   ```

5. **Listar dependencias externas.** Servicios de terceros de los que depende el sistema:

   - Nombre del servicio.
   - Para qué se usa.
   - Qué pasa si no está disponible (fallback, degradación, fallo total).
   - Enlace a su documentación.

6. **Enlazar decisiones arquitectónicas.** Referenciar los ADRs relevantes que explican por qué se tomaron las decisiones de diseño. Si no hay ADRs, considerar crearlos con el skill `write-adr`.

7. **Incluir instrucciones de desarrollo.** Cómo levantar el entorno de desarrollo:

   - Requisitos previos (versiones de lenguaje, herramientas).
   - Pasos para arrancar el proyecto desde cero.
   - Cómo ejecutar tests.
   - Variables de entorno necesarias.

## Criterios de éxito

- La visión general explica qué es el sistema y para qué sirve en 2-3 párrafos.
- Cada componente principal está documentado con propósito, responsabilidades e interfaces.
- Hay al menos un diagrama de componentes y un diagrama de secuencia en Mermaid.
- Las dependencias externas están listadas con su impacto en caso de fallo.
- Las decisiones arquitectónicas están referenciadas o documentadas.
- Las instrucciones de desarrollo permiten a un nuevo miembro del equipo arrancar el proyecto.
